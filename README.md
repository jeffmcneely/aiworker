# AWS SQS Python Application

This is a simple Python application that demonstrates sending and receiving messages using AWS SQS.

## Features
- Send messages to an SQS queue
- Receive messages from an SQS queue

## Requirements
- Python 3.7+
- AWS credentials configured (via environment variables or AWS CLI)
- boto3 library

## Setup
1. Install dependencies:
   ```bash
   pip install boto3
   ```
2. Configure your AWS credentials:
   - Run `aws configure` or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as environment variables.

## Usage
- Edit `sqs_app.py` to set your queue URL.
- Run the script:
   ```bash
   python sqs_app.py
   ```

## License
MIT
