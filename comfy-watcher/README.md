# S3Watcher


S3Watcher monitors local directories for new files and uploads them to an S3 bucket. It can also send and receive messages from an AWS SQS FIFO queue for workflow automation with ComfyUI.

## Configuration


Set the following environment variables (in your shell or systemd service file):

- **S3_BUCKET**: Name of the S3 bucket to upload files to.
- **WATCH_DIRS**: Colon-separated list of directories to monitor (e.g., `/dir1:/dir2`).
- **AWS_SQS_NAME**: Name of the SQS FIFO queue (e.g., `aiworker-queue.fifo`).
- **AWS_REGION**: AWS region (e.g., `us-west-2`).
- **AWS credentials**: Ensure AWS credentials are available (via environment, config file, or IAM role).

## Usage

1. Set up a virtual environment and install dependencies:
   ```sh
   mkdir ~/comfy-watcher
   cd ~/comfy-watcher
   python3 -m venv venv
   source venv/bin/activate
   pip install boto3 watchdog requests pillow piexif
   ```

2. Set environment variables and run:
   ```sh
   export S3_BUCKET=your-bucket
   export WATCH_DIRS=/path/to/dir1:/path/to/dir2
   export AWS_SQS_NAME=aiworker-queue.fifo
   export AWS_REGION=us-west-2
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