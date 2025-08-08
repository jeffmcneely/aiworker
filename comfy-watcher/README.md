# ComfyUI Watcher

ComfyUI Watcher is a containerized service that monitors AWS SQS queues for image generation requests and processes them using ComfyUI. It handles workflow execution, image uploads to S3, and job completion tracking.

## Features

- Container-based deployment for easy scaling and management
- Configurable ComfyUI host and port via environment variables
- Adjustable polling intervals for optimal performance
- AWS S3 integration for image storage and metadata
- AWS SQS integration for job queue management
- Comprehensive logging and monitoring
- Health checks for container orchestration

## Security

### Docker Secrets (Recommended)
The application supports Docker secrets for secure credential management:

- **Secrets are stored in separate files** outside the container image
- **File permissions are automatically secured** (600)
- **Secrets are excluded from Git** via .dockerignore
- **Environment variables are used as fallback** for development

### Environment Variable Prefixing
All AWS-related environment variables now use the `COMFY_` prefix to:
- **Avoid conflicts** with system AWS credentials
- **Provide clear separation** of application-specific config
- **Enable easy identification** of comfy-watcher variables

### Backward Compatibility
The application maintains backward compatibility with standard AWS environment variables:
- `AWS_ACCESS_KEY_ID` → `COMFY_AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` → `COMFY_AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` → `COMFY_AWS_DEFAULT_REGION`
- `AWS_S3_BUCKET` → `COMFY_AWS_S3_BUCKET`
- `AWS_SQS_NAME` → `COMFY_AWS_SQS_NAME`

## Configuration

### Environment Variables

#### Required AWS Configuration (COMFY_ prefixed)
- **COMFY_AWS_ACCESS_KEY_ID**: AWS access key (or use Docker secrets)
- **COMFY_AWS_SECRET_ACCESS_KEY**: AWS secret key (or use Docker secrets)
- **COMFY_AWS_DEFAULT_REGION**: AWS region (default: us-west-2)
- **COMFY_AWS_S3_BUCKET**: S3 bucket name for storing images and metadata
- **COMFY_AWS_SQS_NAME**: SQS queue name for job processing

#### Docker Secrets (Recommended for production)
- **COMFY_AWS_ACCESS_KEY_ID_FILE**: Path to file containing AWS access key
- **COMFY_AWS_SECRET_ACCESS_KEY_FILE**: Path to file containing AWS secret key

#### ComfyUI Configuration
- **COMFY_HOST**: ComfyUI hostname (default: comfyui)
- **COMFY_PORT**: ComfyUI port (default: 8188)

#### Application Configuration
- **LOG_LEVEL**: Logging level (default: INFO)
- **POLL_INTERVAL**: Polling interval in seconds (default: 2)
- **OUTPUT_FOLDER**: Local output directory (default: /app/output)

## Docker Usage

### Using Docker Compose (Recommended)

1. **Set up secrets:**
   ```sh
   ./setup-secrets.sh
   ```

2. **Edit the secret files:**
   ```sh
   # Edit with your actual AWS credentials
   vi secrets/aws_access_key_id.txt
   vi secrets/aws_secret_access_key.txt
   ```

3. **Copy the environment template:**
   ```sh
   cp .env.example .env
   ```

4. **Edit `.env` with your configuration:**
   ```sh
   # AWS Configuration (using COMFY_ prefix)
   COMFY_AWS_DEFAULT_REGION=us-west-2
   COMFY_AWS_S3_BUCKET=your-s3-bucket-name
   COMFY_AWS_SQS_NAME=your-sqs-queue-name
   
   # ComfyUI Configuration
   COMFY_HOST=comfyui
   COMFY_PORT=8188
   
   # Application Configuration
   LOG_LEVEL=INFO
   POLL_INTERVAL=2
   ```

5. **Start the services:**
   ```sh
   docker-compose up -d
   ```

6. **Check logs:**
   ```sh
   docker-compose logs -f comfy-watcher
   ```

### Using Docker Only

1. Build the image:
   ```sh
   docker build -t comfy-watcher .
   ```

2. Run the container:
   ```sh
   docker run -d \
     --name comfy-watcher \
     -e COMFY_AWS_ACCESS_KEY_ID=your_key \
     -e COMFY_AWS_SECRET_ACCESS_KEY=your_secret \
     -e COMFY_AWS_S3_BUCKET=your-bucket \
     -e COMFY_AWS_SQS_NAME=your-queue \
     -e COMFY_HOST=your-comfyui-host \
     -e COMFY_PORT=8188 \
     -e LOG_LEVEL=INFO \
     -e POLL_INTERVAL=2 \
     comfy-watcher
   ```

## Kubernetes Deployment

For production Kubernetes deployments, comprehensive manifests are provided in the `k8s/` directory.

### Quick Kubernetes Setup

1. Configure your environment:
   ```sh
   cd k8s
   # Edit configuration files
   vi configs/production.env
   vi secrets/aws.env
   ```

2. Deploy to cluster:
   ```sh
   chmod +x deploy.sh
   ./deploy.sh deploy
   ```

3. Check status:
   ```sh
   ./deploy.sh status
   ```

### Kubernetes Features

- **Auto-scaling**: HPA configured for 1-5 replicas based on CPU/memory
- **Storage**: Persistent volumes for models and output
- **Security**: Network policies, RBAC, and secret management
- **Monitoring**: Health checks and resource limits
- **Production-ready**: Kustomize overlays for different environments

See `k8s/README.md` for detailed Kubernetes deployment instructions.

## Local Development

1. Set up a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set environment variables and run:
   ```sh
   export COMFY_AWS_S3_BUCKET=your-bucket
   export COMFY_AWS_SQS_NAME=your-queue
   export COMFY_AWS_ACCESS_KEY_ID=your-access-key
   export COMFY_AWS_SECRET_ACCESS_KEY=your-secret-key
   export COMFY_HOST=localhost
   export COMFY_PORT=8188
   python3 comfy-watcher.py
   ```

## Systemd Integration


1. Edit `comfy-watcher.service` and set the correct paths, user, group, and environment variables (including S3, SQS, and AWS credentials).
2. Copy the service file:
   ```sh
   sudo cp comfy-watcher.service /etc/systemd/system/
   ```
3. Reload systemd and start the service:
   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable comfy-watcher
   sudo systemctl start comfy-watcher
   ```
4. Check status:
   ```sh
   sudo systemctl status comfy-watcher
   ```

## AWS: Create a User with S3 Read/Write Access to One Bucket


To create an AWS IAM user with S3 and SQS access to a single bucket and queue, use the following steps (replace names as needed):


```sh
# 1. Copy `s3-sample.json` and `sqs-sample.json` to `s3-policy.json` and `sqs-policy.json` respectively.
cp s3-sample.json s3-policy.json
cp sqs-sample.json sqs-policy.json
```

2. Edit s3-policy.json and sqs-policy.json to include your bucket and queue ARNs.

3. Run the following commands in your terminal:

```sh
# 1. Create the user
aws iam create-user --user-name comfy-watcher

# 2. Attach the S3 policy to the user
aws iam put-user-policy --user-name comfy-watcher --policy-name S3RWAccess --policy-document file://s3-policy.json

# 3. Attach the SQS policy to the user
aws iam put-user-policy --user-name comfy-watcher --policy-name SQSAccess --policy-document file://sqs-policy.json

# 4. (Optional) Create access keys for the user
aws iam create-access-key --user-name comfy-watcher
```

## Notes

- The service runs as the user/group specified in the service file.
- Ensure AWS credentials are available (via environment, config file, or IAM role).
- For SQS FIFO queues, always use the .fifo suffix and set MessageGroupId when sending messages.