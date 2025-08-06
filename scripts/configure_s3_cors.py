import boto3
import json
import logging
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class S3CorsConfigurator:
    """Configure CORS settings for S3 Express One Zone buckets"""

    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize S3 client with proper error handling

        Args:
            region_name: AWS region name (defaults to session region)
        """
        try:
            self.s3_client = boto3.client("s3", region_name=region_name)
            logger.info(f"Initialized S3 client for region: {region_name or 'default'}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def create_cors_configuration(self, allowed_origins: List[str]) -> Dict:
        """
        Create CORS configuration for metrics widget

        Args:
            allowed_origins: List of allowed origins for CORS

        Returns:
            CORS configuration dictionary
        """
        cors_configuration = {
            "CORSRules": [
                {
                    "ID": "MetricsWidgetCORS",
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedOrigins": allowed_origins,
                    "ExposeHeaders": ["ETag", "x-amz-meta-*"],
                    "MaxAgeSeconds": 3600,
                }
            ]
        }

        logger.info(f"Created CORS configuration with origins: {allowed_origins}")
        return cors_configuration

    def is_express_one_zone_bucket(self, bucket_name: str) -> bool:
        """
        Check if bucket is S3 Express One Zone
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            True if bucket is S3 Express One Zone
        """
        return '--x-s3' in bucket_name
    
    def apply_cors_configuration(self, bucket_name: str, cors_config: Dict) -> bool:
        """
        Apply CORS configuration to S3 bucket

        Args:
            bucket_name: Name of the S3 bucket
            cors_config: CORS configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        
        # Check if this is an S3 Express One Zone bucket
        if self.is_express_one_zone_bucket(bucket_name):
            logger.warning("⚠️  S3 Express One Zone buckets do not support CORS configuration")
            logger.info("For S3 Express One Zone, you need to handle CORS at the application level")
            logger.info("Consider using a CloudFront distribution or API Gateway as a proxy")
            logger.info("Alternatively, ensure your application handles preflight requests properly")
            return False
        
        try:
            self.s3_client.put_bucket_cors(
                Bucket=bucket_name, CORSConfiguration=cors_config
            )
            logger.info(
                f"Successfully applied CORS configuration to bucket: {bucket_name}"
            )
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code == "NoSuchBucket":
                logger.error(f"Bucket '{bucket_name}' does not exist")
            elif error_code == "AccessDenied":
                logger.error(
                    f"Access denied to bucket '{bucket_name}'. Check IAM permissions."
                )
            else:
                logger.error(
                    f"Failed to apply CORS configuration: {error_code} - {error_message}"
                )

            return False

        except Exception as e:
            logger.error(f"Unexpected error applying CORS configuration: {e}")
            return False

    def get_cors_configuration(self, bucket_name: str) -> Optional[Dict]:
        """
        Retrieve current CORS configuration from S3 bucket

        Args:
            bucket_name: Name of the S3 bucket

        Returns:
            CORS configuration dictionary or None if not found
        """
        
        # Check if this is an S3 Express One Zone bucket
        if self.is_express_one_zone_bucket(bucket_name):
            logger.info("S3 Express One Zone buckets do not support CORS configuration")
            return None
        
        try:
            response = self.s3_client.get_bucket_cors(Bucket=bucket_name)
            logger.info(f"Retrieved CORS configuration for bucket: {bucket_name}")
            return response.get("CORSConfiguration")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "NoSuchCORSConfiguration":
                logger.info(f"No CORS configuration found for bucket: {bucket_name}")
                return None
            else:
                logger.error(f"Failed to retrieve CORS configuration: {error_code}")
                return None

        except Exception as e:
            logger.error(f"Unexpected error retrieving CORS configuration: {e}")
            return None

    def configure_metrics_bucket_cors(
        self, bucket_name: str, website_domains: List[str]
    ) -> bool:
        """
        Configure CORS for metrics bucket with website domains

        Args:
            bucket_name: Name of the S3 bucket containing metrics
            website_domains: List of website domains that need access

        Returns:
            True if configuration was successful
        """
    def configure_metrics_bucket_cors(
        self, bucket_name: str, website_domains: List[str]
    ) -> bool:
        """
        Configure CORS for metrics bucket with website domains

        Args:
            bucket_name: Name of the S3 bucket containing metrics
            website_domains: List of website domains that need access

        Returns:
            True if configuration was successful
        """
        logger.info(f"Configuring CORS for metrics bucket: {bucket_name}")

        # Check if this is an S3 Express One Zone bucket
        if self.is_express_one_zone_bucket(bucket_name):
            logger.warning("🚨 S3 Express One Zone buckets do not support CORS!")
            logger.info("")
            logger.info("💡 Alternative solutions:")
            logger.info("1. Use CloudFront distribution with custom origin")
            logger.info("2. Use API Gateway as a proxy to S3")
            logger.info("3. Configure your web application to handle CORS at the server level")
            logger.info("4. Use a regular S3 bucket instead of S3 Express One Zone")
            logger.info("")
            logger.info("🔗 For web widget access, consider creating a CloudFront distribution")
            logger.info("   that points to your S3 Express bucket with appropriate headers.")
            return False

        # Add localhost for development
        allowed_origins = website_domains 
        # Create CORS configuration
        cors_config = self.create_cors_configuration(allowed_origins)

        # Show current configuration
        current_config = self.get_cors_configuration(bucket_name)
        if current_config:
            logger.info("Current CORS configuration:")
            logger.info(json.dumps(current_config, indent=2))

        # Apply new configuration
        success = self.apply_cors_configuration(bucket_name, cors_config)

        if success:
            # Verify configuration was applied
            new_config = self.get_cors_configuration(bucket_name)
            if new_config:
                logger.info("New CORS configuration applied successfully:")
                logger.info(json.dumps(new_config, indent=2))

        return success


def main():
    """Main function to configure CORS for metrics bucket"""
    import sys

    # Load bucket name from command line argument or environment variable
    if len(sys.argv) > 1:
        BUCKET_NAME = sys.argv[1]
        logger.info(f"Using bucket name from command line: {BUCKET_NAME}")
    else:
        BUCKET_NAME = os.environ.get("AWS_S3_BUCKET")
        if not BUCKET_NAME:
            logger.error("❌ No bucket name provided!")
            logger.error("Usage: python configure_s3_cors.py <bucket-name>")
            logger.error("Or set AWS_S3_BUCKET environment variable")
            logger.error(
                "Example: python configure_s3_cors.py my-metrics-bucket--usw2-az1--x-s3"
            )
            return 1
        logger.info(f"Using bucket name from environment: {BUCKET_NAME}")

    WEBSITE_DOMAINS = ["*"]  # Wildcard for subdomains

    # Load AWS region from environment or use default
    REGION = os.environ.get("AWS_REGION", "us-west-2")

    logger.info(f"Using bucket: {BUCKET_NAME}")
    logger.info(f"Using region: {REGION}")
    logger.info(f"Allowed domains: {WEBSITE_DOMAINS}")

    try:
        # Initialize CORS configurator
        cors_configurator = S3CorsConfigurator(region_name=REGION)

        # Configure CORS for metrics bucket
        success = cors_configurator.configure_metrics_bucket_cors(
            bucket_name=BUCKET_NAME, website_domains=WEBSITE_DOMAINS
        )

        if success:
            logger.info("✅ CORS configuration completed successfully!")
            logger.info("Your metrics widget should now be able to fetch data from S3.")
        else:
            logger.error("❌ CORS configuration failed!")
            logger.error("Please check the logs above for specific error details.")

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
