import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Failure handler for Step Functions workflow"""
    try:
        # Extract error information from the event
        execution_name = event.get('execution_name', 'Unknown')
        error_info = event.get('Error', {})
        cause = event.get('Cause', 'Unknown error occurred')
        
        # Try to parse the cause if it's JSON
        try:
            cause_data = json.loads(cause)
            error_message = cause_data.get('errorMessage', cause)
            error_type = cause_data.get('errorType', 'Unknown')
        except (json.JSONDecodeError, AttributeError):
            error_message = str(cause)
            error_type = error_info.get('Error', 'Unknown')
        
        # Prepare failure message
        title = "❌ AI Deployment Failed"
        message = f"Deployment workflow failed during execution."
        
        fields = [
            {
                "name": "Execution",
                "value": execution_name,
                "inline": True
            },
            {
                "name": "Error Type",
                "value": error_type,
                "inline": True
            },
            {
                "name": "Error Details",
                "value": error_message[:1000] + "..." if len(error_message) > 1000 else error_message,
                "inline": False
            }
        ]
        
        # Send Discord notification
        discord_result = send_discord_message(
            message=message,
            title=title,
            color=16711680,  # Red color
            fields=fields
        )
        
        return {
            'statusCode': 200,
            'status': 'failure_notified',
            'discord_result': discord_result,
            'message': 'Failure notification sent'
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
