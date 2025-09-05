import os
import boto3
import subprocess
import tempfile
import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Step 1: Git pull the repository"""
    import requests
    try:
        # Send start notification
        send_discord_message(
            "🔄 Starting download of vpc-template.yaml...",
            title="Step 1: Git Pull",
            color=3447003  # Blue
        )
        # Read secrets
        secrets_client = boto3.client('secretsmanager')
        git_secret = secrets_client.get_secret_value(SecretId='/ai/github')['SecretString']
        git_data = json.loads(git_secret)
        github_pat = git_data.get('github_pat')
        # Get repository URL and file path from state machine input
        repo_url = event.get('repo_url')
        stack_name = event.get('stack_name')
        if not repo_url:
            raise ValueError("repo_url not provided in state machine input")
        if not stack_name:
            raise ValueError("stack_name not provided in state machine input")
        
        file_path = 'vpc-template.yaml'
        # Construct raw file URL for GitHub
        parts = repo_url.rstrip('.git').split('/')
        owner = parts[-2]
        repo = parts[-1]
        branch = event.get('branch', 'main')
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        # Download the file using the GitHub PAT for authentication
        headers = {'Authorization': f'token {github_pat}'}
        response = requests.get(raw_url, headers=headers)
        response.raise_for_status()
        # Save the file to /tmp and read content for passing to next step
        temp_file_path = os.path.join('/tmp', file_path)
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        
        # Read the file content to pass through state machine
        with open(temp_file_path, 'r') as f:
            template_content = f.read()
        # Send success notification
        send_discord_message(
            f"✅ vpc-template.yaml downloaded successfully from {repo_url}",
            title="Step 1: Git Pull Complete",
            color=65280  # Green
        )
        return {
            'statusCode': 200,
            'status': 'success',
            'template_content': template_content,
            'repo_url': repo_url,
            'stack_name': stack_name,
            'execution_id': event.get('execution_id'),
            'message': 'vpc-template.yaml downloaded successfully'
        }
    except Exception as e:
        # Send error notification
        send_discord_message(
            f"❌ Download failed: {str(e)}",
            title="Step 1: Git Pull Failed",
            color=16711680  # Red
        )
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
