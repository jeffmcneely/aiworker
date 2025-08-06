import boto3
import requests
import logging
import os
from botocore.exceptions import ClientError
from typing import Optional
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class S3CorseTester:
    """Test CORS configuration for S3 Express One Zone buckets"""
    
    def __init__(self, region_name: Optional[str] = None):
        self.s3_client = boto3.client('s3', region_name=region_name)
        
    def test_cors_preflight(self, bucket_url: str, origin: str) -> bool:
        """
        Test CORS preflight request
        
        Args:
            bucket_url: Full URL to the S3 object
            origin: Origin header to test with
            
        Returns:
            True if CORS preflight passes
        """
        headers = {
            'Origin': origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        try:
            response = requests.options(bucket_url, headers=headers, timeout=10)
            
            logger.info(f"Preflight response status: {response.status_code}")
            logger.info(f"Preflight response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                cors_headers = {
                    'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                    'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                    'access-control-allow-headers': response.headers.get('access-control-allow-headers')
                }
                
                logger.info(f"CORS headers: {cors_headers}")
                
                if cors_headers['access-control-allow-origin']:
                    logger.info("✅ CORS preflight successful!")
                    return True
                else:
                    logger.warning("⚠️ CORS preflight response missing required headers")
                    return False
            else:
                logger.error(f"❌ CORS preflight failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ CORS preflight test failed: {e}")
            return False
    
    def test_actual_request(self, bucket_url: str, origin: str) -> bool:
        """
        Test actual GET request with CORS
        
        Args:
            bucket_url: Full URL to the S3 object
            origin: Origin header to test with
            
        Returns:
            True if request succeeds
        """
        headers = {
            'Origin': origin
        }
        
        try:
            response = requests.get(bucket_url, headers=headers, timeout=10)
            
            logger.info(f"GET response status: {response.status_code}")
            logger.info(f"GET response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info("✅ GET request successful!")
                
                # Try to parse as JSON if it's metrics data
                try:
                    data = response.json()
                    logger.info(f"Response data keys: {list(data.keys())}")
                except:
                    logger.info(f"Response length: {len(response.text)} characters")
                
                return True
            else:
                logger.error(f"❌ GET request failed with status: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ GET request test failed: {e}")
            return False


def build_s3_express_url(bucket_name: str, object_key: str, region: str) -> str:
    """Build S3 Express One Zone URL from bucket name and object key"""
    return f"https://{bucket_name}.s3express-{region}.amazonaws.com/{object_key}"


def extract_region_from_bucket(bucket_name: str) -> str:
    """Extract region from S3 Express One Zone bucket name"""
    # S3 Express buckets have format: name--azid--x-s3
    # We need to map azid to region
    if '--usw2-az1--' in bucket_name:
        return 'us-west-2'
    elif '--use1-az1--' in bucket_name:
        return 'us-east-1'
    elif '--euw1-az1--' in bucket_name:
        return 'eu-west-1'
    else:
        # Default fallback
        return 'us-west-2'


def is_express_one_zone_bucket(bucket_name: str) -> bool:
    """Check if bucket is S3 Express One Zone"""
    return '--x-s3' in bucket_name


def main():
    """Test CORS configuration"""
    import sys
    
    # Load bucket name from command line argument or environment variable
    if len(sys.argv) > 1:
        BUCKET_NAME = sys.argv[1]
        logger.info(f"Using bucket name from command line: {BUCKET_NAME}")
    else:
        BUCKET_NAME = os.environ.get('AWS_S3_BUCKET')
        if not BUCKET_NAME:
            logger.error("❌ No bucket name provided!")
            logger.error("Usage: python test_s3_cors.py <bucket-name>")
            logger.error("Or set AWS_S3_BUCKET environment variable")
            logger.error("Example: python test_s3_cors.py my-metrics-bucket--usw2-az1--x-s3")
            return 1
        logger.info(f"Using bucket name from environment: {BUCKET_NAME}")
    
    # Try to get region from environment, or extract from bucket name
    REGION = os.environ.get('AWS_REGION')
    if not REGION:
        REGION = extract_region_from_bucket(BUCKET_NAME)
        logger.info(f"Detected region from bucket name: {REGION}")
    
    OBJECT_KEY = os.environ.get('METRICS_OBJECT_KEY', 'metrics.json')
    
    # Build the metrics URL
    METRICS_URL = build_s3_express_url(BUCKET_NAME, OBJECT_KEY, REGION)
    
    TEST_ORIGINS = [
        "https://ai.mcneely.io",
        "https://test.ai.mcneely.io", 
        "http://localhost:3000"
    ]
    
    logger.info(f"Testing CORS for bucket: {BUCKET_NAME}")
    logger.info(f"Testing URL: {METRICS_URL}")
    logger.info(f"Using region: {REGION}")
    
    # Check if this is an S3 Express One Zone bucket
    if is_express_one_zone_bucket(BUCKET_NAME):
        logger.warning("🚨 S3 Express One Zone buckets do not support CORS!")
        logger.info("This test will fail as expected because Express buckets can't have CORS configuration.")
        logger.info("The requests will be blocked by browser CORS policy.")
        logger.info("")
        logger.info("💡 To access Express bucket data from web browsers:")
        logger.info("1. Use CloudFront distribution with custom headers")
        logger.info("2. Use API Gateway as a proxy")
        logger.info("3. Use server-side fetching instead of client-side")
        logger.info("")
    
    tester = S3CorseTester(region_name=REGION)
    
    all_tests_passed = True
    
    for origin in TEST_ORIGINS:
        logger.info(f"\n🧪 Testing with origin: {origin}")
        
        # Test preflight
        preflight_success = tester.test_cors_preflight(METRICS_URL, origin)
        
        # Test actual request
        request_success = tester.test_actual_request(METRICS_URL, origin)
        
        if not (preflight_success and request_success):
            all_tests_passed = False
            logger.error(f"❌ Tests failed for origin: {origin}")
        else:
            logger.info(f"✅ All tests passed for origin: {origin}")
    
    if all_tests_passed:
        logger.info("\n🎉 All CORS tests passed! Your metrics widget should work correctly.")
        logger.info(f"You can now set NEXT_PUBLIC_METRICS_URL={METRICS_URL}")
    else:
        if is_express_one_zone_bucket(BUCKET_NAME):
            logger.error("\n💥 CORS tests failed as expected for S3 Express One Zone bucket.")
            logger.error("Express buckets don't support CORS - this is a limitation of the service.")
            logger.error("Consider using CloudFront or switching to a regular S3 bucket.")
        else:
            logger.error("\n💥 Some CORS tests failed. Please check your bucket CORS configuration.")
            logger.error("Try running: python scripts/configure_s3_cors.py")
    
    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    exit(main())