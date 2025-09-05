import os
import boto3
import paramiko
import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Step 5: Launch ComfyUI and comfy-watcher daemons"""
    try:
        # Send start notification
        send_discord_message(
            "🔄 Launching ComfyUI and comfy-watcher daemons...",
            title="Step 5: Launch Daemons",
            color=3447003  # Blue
        )
        
        # Get instance details from previous step
        instance_id = event.get('instance_id')
        public_ip = event.get('public_ip')
        
        if not instance_id or not public_ip:
            raise Exception("Missing instance_id or public_ip from previous step")
        
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
        
        # Launch daemons
        commands = [
            # Make scripts executable
            'chmod +x /home/ec2-user/comfyui/ComfyUI/main.py',
            'chmod +x /home/ec2-user/comfy-watcher/comfy-watcher.py',
            
            # Create virtual environments if they don't exist
            'cd /home/ec2-user/comfyui/ComfyUI && python3 -m venv venv || true',
            'cd /home/ec2-user/comfy-watcher && python3 -m venv venv || true',
            
            # Install dependencies
            '/home/ec2-user/comfyui/ComfyUI/venv/bin/pip install -r /home/ec2-user/comfyui/ComfyUI/requirements.txt',
            '/home/ec2-user/comfy-watcher/venv/bin/pip install -r /home/ec2-user/comfy-watcher/requirements.txt',
            
            # Launch ComfyUI daemon
            'cd /home/ec2-user/comfyui/ComfyUI && nohup /home/ec2-user/comfyui/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --disable-smart-memory > /tmp/comfyui.log 2>&1 &',
            
            # Wait a moment for ComfyUI to start
            'sleep 5',
            
            # Launch comfy-watcher daemon
            'cd /home/ec2-user/comfy-watcher && nohup /home/ec2-user/comfy-watcher/venv/bin/python3 /home/ec2-user/comfy-watcher/comfy-watcher.py > /tmp/comfy-watcher.log 2>&1 &'
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()  # Wait for command to complete
            
        # Verify services are running
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "(main.py|comfy-watcher.py)" | grep -v grep')
        running_processes = stdout.read().decode()
        
        ssh.close()
        
        # Clean up temporary key file
        os.unlink(key_path)
        
        comfyui_url = f'http://{public_ip}:8188'
        
        # Send success notification
        send_discord_message(
            f"✅ Daemons launched successfully! ComfyUI available at: {comfyui_url}",
            title="Step 5: Launch Daemons Complete",
            color=65280,  # Green
            fields=[
                {
                    "name": "ComfyUI URL",
                    "value": comfyui_url,
                    "inline": False
                },
                {
                    "name": "Running Processes",
                    "value": running_processes[:500] + "..." if len(running_processes) > 500 else running_processes,
                    "inline": False
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'status': 'success',
            'instance_id': instance_id,
            'public_ip': public_ip,
            'running_processes': running_processes,
            'message': 'Daemons launched successfully',
            'comfyui_url': comfyui_url,
            'final_result': {
                'comfyui_url': comfyui_url,
                'public_ip': public_ip,
                'instance_id': instance_id
            }
        }
        
    except Exception as e:
        # Send error notification
        send_discord_message(
            f"❌ Daemon launch failed: {str(e)}",
            title="Step 5: Launch Daemons Failed",
            color=16711680  # Red
        )
        
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
