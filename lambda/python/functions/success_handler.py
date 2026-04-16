import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Success handler for Step Functions workflow"""
    try:
        # Extract relevant information from the event
        execution_name = event.get('execution_name', 'Unknown')
        final_result = event.get('final_result', {})
        
        # Prepare success message
        title = "🎉 AI Deployment Successful"
        message = f"Deployment workflow completed successfully!"
        
        fields = [
            {
                "name": "Execution",
                "value": execution_name,
                "inline": True
            }
        ]
        
        # Add ComfyUI URL if available
        if 'comfyui_url' in final_result:
            fields.append({
                "name": "ComfyUI URL",
                "value": final_result['comfyui_url'],
                "inline": False
            })
        
        # Add instance details if available
        if 'public_ip' in final_result:
            fields.append({
                "name": "EC2 Instance",
                "value": final_result['public_ip'],
                "inline": True
            })
        
        # Send Discord notification
        discord_result = send_discord_message(
            message=message,
            title=title,
            color=65280,  # Green color
            fields=fields
        )
        
        return {
            'statusCode': 200,
            'status': 'success',
            'discord_result': discord_result,
            'message': 'Success notification sent'
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
