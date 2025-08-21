# ComfyUI Watcher Setup Guide

This guide helps you set up and run the ComfyUI watcher with proper AWS credentials.

## Quick Start (Environment Variables)

This is the easiest way to get started during development:

1. **Copy the environment template:**
   ```bash
   cd comfy-watcher
   cp .env.example .env
   ```

2. **Edit the .env file with your AWS credentials:**
   ```bash
   # Required AWS credentials
   AWS_ACCESS_KEY_ID=your_actual_access_key_id
   AWS_SECRET_ACCESS_KEY=your_actual_secret_access_key
   AWS_DEFAULT_REGION=us-east-1
   
   # Queue names (will auto-discover URLs)
   FAST_QUEUE_NAME=FAST_QUEUE
   SLOW_QUEUE_NAME=SLOW_QUEUE
   ```

3. **Run the containers:**
   ```bash
   docker-compose up -d
   ```

## Production Setup (External Docker Secrets)

For production deployment, use external Docker secrets for better security:

1. **Create external Docker secrets:**
   ```bash
   # Create secrets in Docker
   echo "your_actual_access_key_id" | docker secret create aws_access_key_id -
   echo "your_actual_secret_access_key" | docker secret create aws_secret_access_key -
   
   # Verify secrets are created
   docker secret ls
   ```

2. **Run with external secrets:**
   ```bash
   docker-compose up -d
   ```

   The secrets will be automatically mounted at `/run/secrets/` in the container.

## Troubleshooting

### Missing Secret Files Warning
If you see: `WARNING Secret file not found: /run/secrets/aws_access_key_id`

This means you haven't set up either method above. The watcher will try:
1. External Docker secrets first (production): `/run/secrets/aws_access_key_id` and `/run/secrets/aws_secret_access_key`
2. Environment variables as fallback (development)
3. Warn if neither is available

To create external Docker secrets:
```bash
echo "your_access_key" | docker secret create aws_access_key_id -
echo "your_secret_key" | docker secret create aws_secret_access_key -
```

### AWS Permissions
Your AWS credentials need these permissions:
- `sqs:ReceiveMessage` on FAST_QUEUE and SLOW_QUEUE
- `sqs:DeleteMessage` on both queues
- `sqs:GetQueueUrl` to discover queue URLs
- `lambda:InvokeFunction` for Trello integration
- `sts:AssumeRole` if using role-based access

### Queue Discovery
The watcher automatically discovers SQS queue URLs using the queue names. If discovery fails, you can manually set:
```bash
FAST_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/FAST_QUEUE
SLOW_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/SLOW_QUEUE
```

## Configuration Options

All configuration can be set in the `.env` file:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# SQS Queues
FAST_QUEUE_NAME=FAST_QUEUE
SLOW_QUEUE_NAME=SLOW_QUEUE

# ComfyUI
COMFYUI_URL=http://comfyui:8188

# Polling intervals (seconds)
FAST_QUEUE_POLL_INTERVAL=5
SLOW_QUEUE_POLL_INTERVAL=10

# Logging
LOG_LEVEL=INFO  # or DEBUG for verbose output
```

## Checking Status

View container logs:
```bash
docker-compose logs -f comfy-watcher
```

Check if queues are being monitored:
```bash
docker-compose logs comfy-watcher | grep "Monitoring"
```
