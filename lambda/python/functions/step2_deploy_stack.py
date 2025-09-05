import os
import boto3
import json
from discord import send_discord_message

def lambda_handler(event, context):
    """Step 2: Deploy CloudFormation stack"""
    try:
        # Send start notification
        send_discord_message(
            "🔄 Starting CloudFormation stack deployment...",
            title="Step 2: Deploy Stack",
            color=3447003  # Blue
        )
        
        # Get template content and stack name from previous step
        template_content = event.get('template_content')
        stack_name = event.get('stack_name')
        
        if not template_content:
            raise ValueError("template_content not provided from previous step")
        if not stack_name:
            raise ValueError("stack_name not provided from previous step")
        
        # Deploy CloudFormation stack
        cf_client = boto3.client('cloudformation')
        
        # Check if stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            # Stack exists, update it
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_content,
                Parameters=[
                    {
                        'ParameterKey': 'SSHKeyPair',
                        'ParameterValue': 'airender'
                    }
                ]
            )
            operation = 'update'
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                # Stack doesn't exist, create it
                response = cf_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_content,
                    Parameters=[
                        {
                            'ParameterKey': 'SSHKeyPair',
                            'ParameterValue': 'airender'
                        }
                    ]
                )
                operation = 'create'
            else:
                raise e
        
        # Wait for stack operation to complete
        if operation == 'create':
            waiter = cf_client.get_waiter('stack_create_complete')
        else:
            waiter = cf_client.get_waiter('stack_update_complete')
        
        waiter.wait(StackName=stack_name)
        
        # Send success notification
        send_discord_message(
            f"✅ CloudFormation stack {operation} completed: {stack_name}",
            title="Step 2: Deploy Stack Complete",
            color=65280  # Green
        )
        
        return {
            'statusCode': 200,
            'status': 'success',
            'stack_name': stack_name,
            'operation': operation,
            'execution_id': event.get('execution_id'),
            'message': f'CloudFormation stack {operation} completed successfully'
        }
        
    except Exception as e:
        # Send error notification
        send_discord_message(
            f"❌ CloudFormation deployment failed: {str(e)}",
            title="Step 2: Deploy Stack Failed",
            color=16711680  # Red
        )
        
        return {
            'statusCode': 500,
            'status': 'error',
            'error': str(e)
        }
