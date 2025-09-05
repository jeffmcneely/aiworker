import os
import boto3
import paramiko
import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Step 3: Connect to EC2 and create directories"""
    try:
        # Send start notification
        send_discord_message(
            "🔄 Connecting to EC2 and creating directories...",
            title="Step 3: Create Directories",
            color=3447003  # Blue
        )
        
        # Get stack name from previous step
        stack_name = event.get('stack_name', 'ComfyVPCStack')
        
        # Get EC2 instance IP from CloudFormation stack
        cf_client = boto3.client('cloudformation')
        stack_resources = cf_client.describe_stack_resources(StackName=stack_name)
        
        # Find EC2 instance resource
        instance_id = None
        for resource in stack_resources['StackResources']:
            if resource['ResourceType'] == 'AWS::EC2::Instance':
                instance_id = resource['PhysicalResourceId']
                break
        
        if not instance_id:
            raise Exception("No EC2 instance found in stack")
        
        # Get instance details
        ec2_client = boto3.client('ec2')
        instances = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        public_ip = instance['PublicIpAddress']
        availability_zone = instance['Placement']['AvailabilityZone']
        
        # Get SSH key from secrets
        secrets_client = boto3.client('secretsmanager')
        ssh_secret = secrets_client.get_secret_value(SecretId='/ai/ssh')['SecretString']
        ssh_data = json.loads(ssh_secret)
        
        # Use EC2 Instance Connect to send public key
        eic_client = boto3.client('ec2-instance-connect')
        eic_client.send_ssh_public_key(
            InstanceId=instance_id,
            InstanceOSUser='ec2-user',
            SSHPublicKey=ssh_data['public_key'],
            AvailabilityZone=availability_zone
        )
        
        # Connect via SSH and create directories
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Create private key file for connection
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_file:
            key_file.write(ssh_data['private_key'])
            key_path = key_file.name
        os.chmod(key_path, 0o600)
        
        ssh.connect(public_ip, username='ec2-user', key_filename=key_path)
        
        # Create directories
        commands = [
            'sudo mkdir -p /opt/comfyui/ComfyUI',
            'sudo chown -R ec2-user:ec2-user /opt/comfyui/ComfyUI',
            'mkdir -p /home/ec2-user/comfyui',
            'mkdir -p /home/ec2-user/comfy-watcher'
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()  # Wait for command to complete
            
        ssh.close()
        
        # Clean up temporary key file
        os.unlink(key_path)
        
        # Send success notification
        send_discord_message(
            f"✅ Directories created on EC2 instance: {public_ip}",
            title="Step 3: Create Directories Complete",
            color=65280  # Green
        )
        
        return {
            'statusCode': 200,
            'status': 'success',
            'instance_id': instance_id,
            'public_ip': public_ip,
            'message': 'Directories created successfully'
        }
        
    except Exception as e:
        # Send error notification
        send_discord_message(
            f"❌ Directory creation failed: {str(e)}",
            title="Step 3: Create Directories Failed",
            color=16711680  # Red
        )
        
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
