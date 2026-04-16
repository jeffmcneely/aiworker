import os
import boto3
import paramiko
import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Step 4: Clone S3 bucket contents to EC2"""
    try:
        # Send start notification
        send_discord_message(
            "🔄 Syncing S3 bucket contents to EC2...",
            title="Step 4: Clone S3 Contents",
            color=3447003  # Blue
        )
        
        # Get instance details from previous step
        instance_id = event.get('instance_id')
        public_ip = event.get('public_ip')
        
        if not instance_id or not public_ip:
            raise Exception("Missing instance_id or public_ip from previous step")
        
        # Get bucket name from environment variable
        bucket_name = os.environ['DNDBucketProgramParameter']
        
        # Get SSH key from secrets
        secrets_client = boto3.client('secretsmanager')
        ssh_secret = secrets_client.get_secret_value(SecretId='/ai/ssh')['SecretString']
        ssh_data = json.loads(ssh_secret)
        
        # Connect via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Create private key file for connection
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
            key_file.write(ssh_data['private_key'])
            key_path = key_file.name
        os.chmod(key_path, 0o600)
        
        ssh.connect(public_ip, username='ec2-user', key_filename=key_path)
        
        # Sync S3 bucket contents
        commands = [
            f'aws s3 sync s3://{bucket_name}/opt /opt/comfyui/ComfyUI',
            f'aws s3 sync s3://{bucket_name}/comfyui /home/ec2-user/comfyui',
            f'aws s3 sync s3://{bucket_name}/comfy-watcher /home/ec2-user/comfy-watcher',
            'sudo chown -R ec2-user:ec2-user /home/ec2-user/comfyui',
            'sudo chown -R ec2-user:ec2-user /home/ec2-user/comfy-watcher'
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()  # Wait for command to complete
            
        ssh.close()
        
        # Clean up temporary key file
        os.unlink(key_path)
        
        # Send success notification
        send_discord_message(
            f"✅ S3 bucket contents synced successfully from {bucket_name}",
            title="Step 4: Clone S3 Contents Complete",
            color=65280  # Green
        )
        
        return {
            'statusCode': 200,
            'status': 'success',
            'instance_id': instance_id,
            'public_ip': public_ip,
            'bucket_synced': bucket_name,
            'message': 'S3 bucket contents cloned successfully'
        }
        
    except Exception as e:
        # Send error notification
        send_discord_message(
            f"❌ S3 sync failed: {str(e)}",
            title="Step 4: Clone S3 Contents Failed",
            color=16711680  # Red
        )
        
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
