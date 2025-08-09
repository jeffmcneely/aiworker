#!/bin/bash

# Setup script for ComfyUI Watcher secrets

set -e

SECRETS_DIR="./secrets"

echo "Setting up ComfyUI Watcher secrets..."
echo ""

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

# Function to create secret file
create_secret() {
    local secret_name=$1
    local secret_file=$2
    local example_file="${secret_file}.example"
    
    if [ -f "$secret_file" ]; then
        echo "✓ $secret_name already exists"
        return
    fi
    
    echo "Setting up $secret_name..."
    
    if [ -f "$example_file" ]; then
        cp "$example_file" "$secret_file"
        echo "📝 Created $secret_file from example"
        echo "   Please edit this file with your actual credentials"
    else
        echo "your-$secret_name-here" > "$secret_file"
        echo "📝 Created $secret_file"
        echo "   Please edit this file with your actual credentials"
    fi
    
    # Set secure permissions
    chmod 600 "$secret_file"
    echo "🔒 Set secure permissions (600) on $secret_file"
}

# Create secret files
create_secret "aws-access-key-id" "$SECRETS_DIR/aws_access_key_id.txt"
create_secret "aws-secret-access-key" "$SECRETS_DIR/aws_secret_access_key.txt"
create_secret "aws-s3-bucket" "$SECRETS_DIR/aws_s3_bucket.txt"
create_secret "aws-sqs-name" "$SECRETS_DIR/aws_sqs_name.txt"

echo ""
echo "✅ Secret files created!"
echo ""
echo "Next steps:"
echo "1. Edit the secret files with your actual AWS credentials and configuration:"
echo "   - $SECRETS_DIR/aws_access_key_id.txt"
echo "   - $SECRETS_DIR/aws_secret_access_key.txt"
echo "   - $SECRETS_DIR/aws_s3_bucket.txt"
echo "   - $SECRETS_DIR/aws_sqs_name.txt"
echo ""
echo "2. Update your .env file with the COMFY_ prefixed variables"
echo ""
echo "3. Run: docker-compose up -d"
echo ""
echo "⚠️  Security Note:"
echo "   - Secret files are excluded from Git via .dockerignore"
echo "   - Keep these files secure and never commit them to version control"
