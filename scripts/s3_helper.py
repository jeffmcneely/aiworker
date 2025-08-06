#!/usr/bin/env python3
"""
Helper script to build S3 Express One Zone URLs and manage environment variables
"""

import os
import sys


def extract_region_from_bucket(bucket_name: str) -> str:
    """Extract region from S3 Express One Zone bucket name"""
    # S3 Express buckets have format: name--azid--x-s3
    if '--usw2-az1--' in bucket_name:
        return 'us-west-2'
    elif '--use1-az1--' in bucket_name:
        return 'us-east-1'
    elif '--euw1-az1--' in bucket_name:
        return 'eu-west-1'
    elif '--euc1-az1--' in bucket_name:
        return 'eu-central-1'
    elif '--aps1-az1--' in bucket_name:
        return 'ap-south-1'
    elif '--apne1-az1--' in bucket_name:
        return 'ap-northeast-1'
    else:
        print(f"Warning: Could not determine region from bucket name: {bucket_name}")
        return 'us-west-2'  # Default fallback


def build_s3_express_url(bucket_name: str, object_key: str, region: str) -> str:
    """Build S3 Express One Zone URL from bucket name and object key"""
    return f"https://{bucket_name}.s3express-{region}.amazonaws.com/{object_key}"


def get_env_config(bucket_name=None):
    """Get current environment configuration"""
    # Use provided bucket name or get from environment
    bucket = bucket_name or os.environ.get('AWS_S3_BUCKET')
    region = os.environ.get('AWS_REGION')
    object_key = os.environ.get('METRICS_OBJECT_KEY', 'metrics.json')
    
    if not bucket:
        print("❌ No bucket name provided!")
        print("Usage: provide bucket name as argument or set AWS_S3_BUCKET environment variable")
        return None
    
    if not region:
        region = extract_region_from_bucket(bucket)
        print(f"ℹ️  Detected region from bucket name: {region}")
    
    base_url = f"https://{bucket}.s3express-{region}.amazonaws.com"
    metrics_url = f"{base_url}/{object_key}"
    list_url = f"{base_url}/list.json"
    
    return {
        'bucket': bucket,
        'region': region,
        'object_key': object_key,
        'base_url': base_url,
        'metrics_url': metrics_url,
        'list_url': list_url
    }


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python s3_helper.py <command> [bucket-name]")
        print("Commands:")
        print("  show-config [bucket]    - Show configuration for bucket (from arg or env)")
        print("  build-url [bucket]      - Build base URL for bucket (from arg or env)")
        print("  check-env [bucket]      - Check configuration for bucket (from arg or env)")
        return 1
    
    command = sys.argv[1]
    bucket_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    if bucket_name:
        print(f"Using bucket name from command line: {bucket_name}")
    
    if command == "show-config":
        config = get_env_config(bucket_name)
        if config:
            print("🔧 Current Configuration:")
            print(f"   Bucket: {config['bucket']}")
            print(f"   Region: {config['region']}")
            print(f"   Object: {config['object_key']}")
            print(f"   Base URL: {config['base_url']}")
            print(f"   List URL: {config['list_url']}")
            print(f"   Metrics URL: {config['metrics_url']}")
        return 0 if config else 1
    
    elif command == "build-url":
        config = get_env_config(bucket_name)
        if config:
            print(config['base_url'])
        return 0 if config else 1
    
    elif command == "check-env":
        config = get_env_config(bucket_name)
        if config:
            print("✅ All environment variables are properly configured")
            
            # Check if METRICS_BUCKET_BASE matches
            base_url = os.environ.get('METRICS_BUCKET_BASE')
            if base_url == config['base_url']:
                print("✅ METRICS_BUCKET_BASE matches computed URL")
            else:
                print("⚠️  METRICS_BUCKET_BASE doesn't match computed URL")
                print(f"   Current: {base_url}")
                print(f"   Expected: {config['base_url']}")
        
        return 0 if config else 1
    
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    exit(main())
