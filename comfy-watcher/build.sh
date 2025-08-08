#!/bin/bash

# Build script for ComfyUI Watcher

set -e

echo "Building ComfyUI Watcher container..."

# Build the Docker image
docker build -t comfy-watcher:latest .

echo "Build completed successfully!"
echo ""
echo "To run with docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "To run with docker only:"
echo "  docker run -d --name comfy-watcher \\"
echo "    -e AWS_ACCESS_KEY_ID=your_key \\"
echo "    -e AWS_SECRET_ACCESS_KEY=your_secret \\"
echo "    -e AWS_S3_BUCKET=your-bucket \\"
echo "    -e AWS_SQS_NAME=your-queue \\"
echo "    -e COMFY_HOST=your-comfyui-host \\"
echo "    comfy-watcher:latest"
