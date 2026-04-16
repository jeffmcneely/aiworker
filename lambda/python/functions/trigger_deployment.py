import boto3
import json
import uuid
from discord import send_discord_message

def lambda_handler(event, context):
    """Trigger Lambda to start the AI deployment Step Functions workflow"""
    try:
        # Send Discord notification that workflow is being triggered
        send_discord_message(
            message="Starting new AI deployment workflow execution",
            title="🚀 AI Deployment Workflow Triggered",
            color=0x3498db,  # Blue
            fields=[
                {"name": "Execution ID", "value": str(uuid.uuid4())[:8], "inline": True},
                {"name": "Triggered By", "value": context.invoked_function_arn.split(':')[-1], "inline": True}
            ]
        )
        
        # Initialize Step Functions client
        stepfunctions_client = boto3.client('stepfunctions')
        
        # Get state machine ARN from environment variable or event
        import os
        state_machine_arn = (
            event.get('state_machine_arn') or 
            os.environ.get('STATE_MACHINE_ARN')
        )
        
        if not state_machine_arn:
            # Fallback: construct Step Functions ARN from Lambda function ARN
            # Lambda ARN: arn:aws:lambda:region:account:function:function-name
            # Step Functions ARN: arn:aws:states:region:account:stateMachine:state-machine-name
            arn_parts = context.invoked_function_arn.split(':')
            region = arn_parts[3]
            account_id = arn_parts[4]
            state_machine_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:ai-deployment-workflow"
        
        print(f"Using state machine ARN: {state_machine_arn}")  # Debug logging
        
        # Prepare input for the state machine with default values
        execution_input = {
            'repo_url': 'https://github.com/jeffmcneely/aws_cloudformation.git',
            'stack_name': 'ComfyVPCStack',
            'execution_id': str(uuid.uuid4())
        }
        
        # Start execution
        execution_name = f"ai-deployment-{execution_input['execution_id'][:8]}"
        
        response = stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(execution_input)
        )
        
        # Send Discord notification that workflow started successfully
        send_discord_message(
            message="Step Functions workflow execution has begun",
            title="✅ AI Deployment Workflow Started",
            color=0x2ecc71,  # Green
            fields=[
                {"name": "Execution ARN", "value": response['executionArn'][-50:], "inline": False},
                {"name": "Execution Name", "value": execution_name, "inline": True},
                {"name": "Repository", "value": execution_input['repo_url'], "inline": True},
                {"name": "Stack Name", "value": execution_input['stack_name'], "inline": True}
            ]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'execution_arn': response['executionArn'],
                'execution_name': execution_name,
                'message': 'AI deployment workflow started successfully'
            })
        }
        
    except Exception as e:
        # Send Discord notification about the error
        send_discord_message(
            message="Failed to start the AI deployment workflow",
            title="❌ AI Deployment Workflow Trigger Failed",
            color=0xe74c3c,  # Red
            fields=[
                {"name": "Error", "value": str(e)[:1000], "inline": False},
                {"name": "Function", "value": context.function_name, "inline": True},
                {"name": "Request ID", "value": context.aws_request_id, "inline": True}
            ]
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e)
            })
        }
