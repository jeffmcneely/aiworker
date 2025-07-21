import boto3
import os

# Set your SQS queue URL here
QUEUE_URL = os.getenv('AWS_SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/my-queue')

sqs = boto3.client('sqs')

def send_message(message_body):
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=message_body
    )
    print('Message sent:', response['MessageId'])

def receive_messages():
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1
    )
    messages = response.get('Messages', [])
    for msg in messages:
        print('Received:', msg['Body'])
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg['ReceiptHandle']
        )
        print('Message deleted')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'send':
        send_message(' '.join(sys.argv[2:]) or 'Hello from SQS!')
    else:
        receive_messages()
