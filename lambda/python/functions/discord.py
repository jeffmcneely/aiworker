import boto3
import json
import requests
from datetime import datetime

def send_discord_message(message, title=None, color=None, fields=None):
    """
    Send a message to Discord using webhook URL from AWS Secrets Manager
    
    Args:
        message (str): Main message content
        title (str, optional): Embed title
        color (int, optional): Embed color (decimal)
        fields (list, optional): List of field dictionaries with 'name' and 'value'
    
    Returns:
        dict: Response with status and message
    """
    try:
        # Get Discord webhook URL from secrets
        secrets_client = boto3.client('secretsmanager')
        discord_secret = secrets_client.get_secret_value(SecretId='/ai/discord_url')['SecretString']
        discord_data = json.loads(discord_secret)
        webhook_url = discord_data['webhook_url']
        
        # Prepare the payload
        payload = {
            "content": message if not title else None,
            "embeds": []
        }
        
        # If title is provided, create an embed
        if title:
            embed = {
                "title": title,
                "description": message,
                "timestamp": datetime.utcnow().isoformat(),
                "color": color or 3447003  # Default blue color
            }
            
            # Add fields if provided
            if fields:
                embed["fields"] = fields
                
            payload["embeds"] = [embed]
        
        # Send the message
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:  # Discord returns 204 for successful webhook
            return {
                'status': 'success',
                'message': 'Discord message sent successfully'
            }
        else:
            return {
                'status': 'error',
                'message': f'Discord API error: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to send Discord message: {str(e)}'
        }
