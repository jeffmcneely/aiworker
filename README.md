# AWS SQS Python Application


This project is a Python-based automation and workflow system for AI image generation and processing, integrating AWS S3, SQS, Lambda, and ComfyUI. It includes:

- A watcher service that monitors local directories for new files and uploads them to S3.
- SQS FIFO queue integration for reliable message passing and workflow triggers.
- Lambda functions for API endpoints and queue processing.
- ComfyUI workflow automation, including EXIF metadata insertion and prompt handling.

The system is designed for scalable, event-driven AI workflows, with best practices for AWS SDK usage and Python scripting.

## Features

- Monitor directories and upload new files to S3
- Send and receive messages using AWS SQS FIFO queues
- Trigger and process AI workflows via Lambda and ComfyUI
- Insert custom EXIF metadata (seed, uuid) into images

## Requirements

- Python 3.7+
- AWS credentials configured (via environment variables or AWS CLI)
- boto3, watchdog, requests, pillow, piexif

## Setup

1. Install dependencies:
   ```bash
   pip install boto3 watchdog requests pillow piexif
   ```
2. Configure your AWS credentials:
   - Run `aws configure` or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as environment variables.

## Usage

- Edit environment variables for S3 bucket, SQS queue, and watched directories.
- Run the watcher or Lambda/API scripts as needed.

## License
MIT
