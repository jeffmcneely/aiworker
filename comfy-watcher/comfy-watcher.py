from fileinput import filename
import logging
import threading
import datetime


# Poll ComfyUI history endpoint for prompt results
import time
import os
import sys
import time
import json
import boto3
import requests
import secrets
from exif import Image

# Set logging level based on LOG_LEVEL env var
log_level = logging.DEBUG if os.environ.get("LOG_LEVEL") == "DEBUG" else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Global variables for AWS clients and configuration
aws_session = None
s3 = None
sqs = None
ssm = None
lambda_client = None
S3_BUCKET = None
FAST_QUEUE = None
SLOW_QUEUE = None
role_refresh_timer = None
iteration_counter = 0

# AWS Region
AWS_REGION = os.getenv("COMFY_AWS_DEFAULT_REGION") or os.getenv("AWS_DEFAULT_REGION", "us-west-2")

# AWS Role to assume
AWS_ROLE_NAME = os.getenv("AWS_ROLE_NAME", "comfyrole")

# Function to read Docker secrets
def read_secret(secret_file_path):
    if not secret_file_path:
        return None
    try:
        if os.path.exists(secret_file_path):
            with open(secret_file_path, 'r') as f:
                value = f.read().strip()
                return value if value else None
        else:
            logger.debug(f"Secret file not found: {secret_file_path}")
            return None
    except Exception as e:
        logger.debug(f"Error reading secret from {secret_file_path}: {e}")
        return None

# AWS Configuration - support both secrets and env vars for initial credentials
def get_initial_aws_credentials():
    # Try to read from Docker secrets first (hardcoded paths)
    logger.debug("Getting initial AWS credentials...")
    
    access_key = None
    secret_key = None
    
    # Try Docker secrets at standard paths
    access_key = read_secret("/run/secrets/aws_access_key_id")
    secret_key = read_secret("/run/secrets/aws_secret_access_key")
    logger.debug(f"Read access_key: {'set' if access_key else 'not set'}, secret_key: {'set' if secret_key else 'not set'} from Docker secrets")
    
    if access_key and secret_key:
        return access_key, secret_key
    
    # Fallback to environment variables
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    logger.debug(f"Read access_key: {'set' if access_key else 'not set'}, secret_key: {'set' if secret_key else 'not set'} from environment")
    
    if not access_key or not secret_key:
        logger.warning("No AWS credentials found in Docker secrets or environment variables")
        logger.info("To use Docker secrets, ensure they are created externally and mounted at /run/secrets/")
        logger.info("To use environment variables, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
    
    return access_key, secret_key

def assume_dnd_role():
    """Assume the configured AWS role and return session with temporary credentials"""
    global aws_session, s3, sqs, ssm, lambda_client, S3_BUCKET, FAST_QUEUE, SLOW_QUEUE
    
    logger.info(f"Assuming {AWS_ROLE_NAME}...")
    
    # Get initial credentials for assuming role
    initial_access_key, initial_secret_key = get_initial_aws_credentials()
    
    # Create initial STS client
    sts_client = boto3.client(
        'sts',
        aws_access_key_id=initial_access_key,
        aws_secret_access_key=initial_secret_key,
        region_name=AWS_REGION
    )
    
    try:
        # Get caller identity to determine account ID
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity['Account']
        logger.debug(f"Current account ID: {account_id}")
        
        # Assume the configured role
        role_arn = f'arn:aws:iam::{account_id}:role/{AWS_ROLE_NAME}'
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='comfy-watcher-session'
        )
        
        credentials = response['Credentials']
        logger.info(f"Successfully assumed {AWS_ROLE_NAME}. Session expires at: {credentials['Expiration']}")
        
        # Create session with temporary credentials
        aws_session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=AWS_REGION
        )
        
        # Initialize AWS clients with the assumed role session
        s3 = aws_session.client('s3')
        sqs = aws_session.client('sqs')
        ssm = aws_session.client('ssm')
        lambda_client = aws_session.client('lambda')
        
        # Get S3 bucket and SQS queue names from SSM
        S3_BUCKET = get_ssm_parameter('/ai/bucket')
        FAST_QUEUE = get_ssm_parameter('/ai/sqs-fast')
        SLOW_QUEUE = get_ssm_parameter('/ai/sqs-slow')
        
        if not S3_BUCKET or not FAST_QUEUE or not SLOW_QUEUE:
            logger.error(f"Failed to retrieve required SSM parameters. S3_BUCKET: {S3_BUCKET}, FAST_QUEUE: {FAST_QUEUE}, SLOW_QUEUE: {SLOW_QUEUE}")
            return False
        
        logger.info(f"Retrieved S3 bucket: {S3_BUCKET}")
        logger.info(f"Retrieved fast SQS queue: {FAST_QUEUE}")
        logger.info(f"Retrieved slow SQS queue: {SLOW_QUEUE}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to assume {AWS_ROLE_NAME}: {e}")
        return False

def get_ssm_parameter(parameter_name):
    """Get parameter value from AWS SSM Parameter Store"""
    try:
        response = ssm.get_parameter(Name=parameter_name)
        value = response['Parameter']['Value']
        logger.debug(f"Retrieved SSM parameter {parameter_name}: {value}")
        return value
    except Exception as e:
        logger.error(f"Failed to get SSM parameter {parameter_name}: {e}")
        return None

def invoke_trello_lambda():
    """Invoke the Trello to SQS Lambda function"""
    try:
        logger.info("Invoking Trello to SQS Lambda function...")
        response = lambda_client.invoke(
            FunctionName='ai-trello-to-sqs',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'httpMethod': 'POST',
                'headers': {},
                'body': '{}'
            })
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        if response.get('StatusCode') == 200:
            if 'body' in payload:
                body = json.loads(payload['body'])
                logger.info(f"Trello Lambda executed successfully: {body.get('message', 'Unknown result')}")
                if 'cardsProcessed' in body:
                    logger.info(f"Cards processed: {body['cardsProcessed']}")
            else:
                logger.info("Trello Lambda executed successfully")
        else:
            logger.error(f"Trello Lambda execution failed with status: {response.get('StatusCode')}")
            if 'errorMessage' in payload:
                logger.error(f"Error message: {payload['errorMessage']}")
    except Exception as e:
        logger.error(f"Failed to invoke Trello Lambda function: {e}")

def refresh_role():
    """Refresh the assumed role credentials"""
    logger.info(f"Refreshing {AWS_ROLE_NAME} credentials...")
    success = assume_dnd_role()
    if success:
        # Schedule next refresh in 59 minutes
        schedule_role_refresh()
    else:
        logger.error("Failed to refresh role, retrying in 5 minutes...")
        # Retry in 5 minutes if failed
        global role_refresh_timer
        role_refresh_timer = threading.Timer(300, refresh_role)  # 5 minutes
        role_refresh_timer.daemon = True
        role_refresh_timer.start()

def schedule_role_refresh():
    """Schedule role refresh in 59 minutes"""
    global role_refresh_timer
    # Cancel existing timer if any
    if role_refresh_timer:
        role_refresh_timer.cancel()
    
    # Schedule refresh in 59 minutes (3540 seconds)
    role_refresh_timer = threading.Timer(3540, refresh_role)
    role_refresh_timer.daemon = True
    role_refresh_timer.start()
    logger.debug("Scheduled role refresh in 59 minutes")

# ComfyUI and other configuration
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")
COMFY_HOST = os.getenv("COMFY_HOST", "127.0.0.1")
COMFY_PORT = os.getenv("COMFY_PORT", "8188")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
ORIGINAL_POLL_INTERVAL = POLL_INTERVAL  # Store original value for reset
current_poll_interval = POLL_INTERVAL  # Current poll interval (may change with backoff)


def apply_backoff():
    """Apply binary backoff to poll interval, max 30 seconds"""
    global current_poll_interval
    current_poll_interval = min(current_poll_interval * 2, 30)
    logger.info(f"ComfyUI failure detected, increasing poll interval to {current_poll_interval} seconds")


def reset_poll_interval():
    """Reset poll interval to original value after successful ComfyUI call"""
    global current_poll_interval
    if current_poll_interval != ORIGINAL_POLL_INTERVAL:
        current_poll_interval = ORIGINAL_POLL_INTERVAL
        logger.info(f"ComfyUI success detected, resetting poll interval to {current_poll_interval} seconds")


class TTI_input:
    """Text-To-Image input parameters class"""
    
    def __init__(self, sqs_body_dict=None):
        if sqs_body_dict is None:
            sqs_body_dict = {}
        
        self.id = sqs_body_dict.get("id", "")
        self.prompt = sqs_body_dict.get("prompt", "cat in a hat")
        self.height = sqs_body_dict.get("height", 512)
        self.width = sqs_body_dict.get("width", 512)
        self.steps = sqs_body_dict.get("steps", 50)
        self.seed = sqs_body_dict.get("seed", 0)
        self.cfg = sqs_body_dict.get("cfg", 5.0)
        self.negativePrompt = sqs_body_dict.get("negativePrompt", "blurry, low quality, distorted, ugly, bad anatomy, deformed, poorly drawn")
        self.model = sqs_body_dict.get("model", "hidream")


def send_sqs_message(queue_name, message_body):
    queue_url = get_sqs_url_by_name(queue_name)
    if not queue_url:
        logger.debug(f"Queue URL not found for '{queue_name}'.")
        return
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
    logger.debug(f"SQS message sent: {response['MessageId']}")


def apply_workflow_mapping(workflow, tti_input, mapping):
    """Apply TTI input parameters to workflow using mapping configuration"""
    # Use seed from the TTI_input instead of generating a new one
    seed = tti_input.seed if tti_input.seed != 0 else secrets.randbits(64)
    
    # Create a mapping of TTI_input attributes to their values
    input_values = {
        'prompt': tti_input.prompt,
        'negativePrompt': tti_input.negativePrompt,
        'height': tti_input.height,
        'width': tti_input.width,
        'steps': tti_input.steps,
        'seed': seed,
        'cfg': tti_input.cfg,
        'batch_size': 1  # Default value
    }
    
    for param, value in input_values.items():
        if param in mapping:
            mapping_config = mapping[param]
            
            # Handle both single mappings and arrays of mappings
            if isinstance(mapping_config, list):
                for config in mapping_config:
                    apply_single_mapping(workflow, config, value)
            else:
                apply_single_mapping(workflow, mapping_config, value)
    
    return seed

def apply_single_mapping(workflow, config, value):
    """Apply a single parameter mapping to the workflow"""
    node_id = config["node"]
    input_name = config["input"]
    is_optional = config.get("optional", False)
    default_value = config.get("default")
    
    # Use default value if provided and current value is None
    if value is None and default_value is not None:
        value = default_value
    
    # Skip if value is None and mapping is optional
    if value is None and is_optional:
        return
    
    # Check if the node and input exist before setting
    if node_id in workflow:
        if "inputs" in workflow[node_id]:
            if not is_optional or input_name in workflow[node_id]["inputs"]:
                workflow[node_id]["inputs"][input_name] = value
                logger.debug(f"Set {node_id}.inputs.{input_name} = {value}")
        else:
            logger.warning(f"Node {node_id} has no inputs section")
    else:
        logger.warning(f"Node {node_id} not found in workflow")


def receive_sqs_messages(queue_name):
    queue_url = get_sqs_url_by_name(queue_name)
    if not queue_url:
        logger.debug(f"Queue URL not found for '{queue_name}'.")
        return

    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    messages = response.get("Messages", [])
    comfy_success = False  # Track if ComfyUI processing was successful
    
    for msg in messages:
        logger.debug(f"SQS received: {msg['Body']}")
        sqs_body_dict = json.loads(msg["Body"])
        tti_input = TTI_input(sqs_body_dict)
        receipt_handle = msg["ReceiptHandle"]  # Store receipt handle for later deletion
        # Load workflow from model.json
        try:
            workflow_path = os.path.join(
                os.path.dirname(__file__),
                "workflows",
                tti_input.model + ".json",
            )
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
        except FileNotFoundError:
            logger.error(
                f"Workflow file not found at {workflow_path}. Please ensure it exists."
            )
            # Don't delete message on error, let it retry
            continue

        # Load mapping configuration for this model
        try:
            mapping_path = os.path.join(
                os.path.dirname(__file__),
                "workflows",
                tti_input.model + ".mapping.json",
            )
            with open(mapping_path, "r") as f:
                mapping = json.load(f)
        except FileNotFoundError:
            logger.error(
                f"Mapping file not found at {mapping_path}. Please ensure it exists."
            )
            # Don't delete message on error, let it retry
            continue

        try:
            # Apply TTI input parameters to workflow using mapping
            logger.debug("Applying workflow mapping...")
            seed = apply_workflow_mapping(workflow, tti_input, mapping)
            prompt = {"prompt": workflow}
            data = json.dumps(prompt).encode("utf-8")
            logger.info(f"using prompt: {tti_input.prompt}")
            logger.debug(f"Sending workflow to ComfyUI: {data}")
            comfy_url = f"http://{COMFY_HOST}:{COMFY_PORT}/prompt"
            response = requests.post(
                comfy_url,
                headers={"Content-Type": "application/json"},
                data=data,
                timeout=30  # Add timeout for ComfyUI request
            )
            
            # Check if ComfyUI request was successful
            if response.status_code != 200:
                logger.error(f"ComfyUI request failed with status {response.status_code}: {response.text}")
                # Don't delete message on error, let it retry
                apply_backoff()
                continue
            
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                logger.error("ComfyUI response missing prompt_id")
                # Don't delete message on error, let it retry
                apply_backoff()
                continue
            
            # Measure time for polling ComfyUI history
            poll_start_time = time.time()
            poll_response = poll_comfyui_history(prompt_id)
            poll_elapsed = time.time() - poll_start_time
            
            # Check if polling was successful
            if poll_response is None:
                logger.error(f"Failed to get ComfyUI history for prompt_id: {prompt_id}")
                # Don't delete message on error, let it retry
                apply_backoff()
                continue
            
            logger.debug(f"Poll response: {poll_response}")
            logger.info(f"ComfyUI polling completed in {poll_elapsed:.2f} seconds")
            
            # Check if expected output exists
            if "9" not in poll_response or "images" not in poll_response["9"] or not poll_response["9"]["images"]:
                logger.error("ComfyUI output missing expected image data")
                # Don't delete message on error, let it retry
                apply_backoff()
                continue
        
            # Upload poll_response to S3 as JSON using the message ID
            output_json_key = f"{tti_input.id}_output.json"
            try:
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=output_json_key,
                    Body=json.dumps(poll_response),
                    ContentType='application/json'
                )
                logger.debug(f"Uploaded poll_response to s3://{S3_BUCKET}/{output_json_key}")
            except Exception as e:
                logger.error(f"Failed to upload poll_response to S3: {e}")
                # Don't delete message on S3 error, let it retry
                continue
            
            # Upload generated image to S3
            image_filename = poll_response["9"]["images"][0]["filename"]
            ext = os.path.splitext(image_filename)[1][1:]
            image_path = os.path.join(OUTPUT_FOLDER, image_filename)
            s3_key = tti_input.id + '.' + ext
            try:
                s3.upload_file(image_path, S3_BUCKET, s3_key)
                logger.debug(f"Uploaded {image_path} to s3://{S3_BUCKET}/{s3_key}")
            except Exception as e:
                logger.error(f"Failed to upload {image_path} to S3: {e}")
                # Don't delete message on S3 error, let it retry
                continue

            # Upload output JSON to S3 with final metadata
            output_json = {
                "prompt": tti_input.prompt,
                "width": tti_input.width,
                "height": tti_input.height,
                "seed": seed,
                "s3_key": s3_key,
                "cfg": tti_input.cfg,
                "steps": tti_input.steps,
                "model": tti_input.model,
                "negativePrompt": tti_input.negativePrompt,
                "filename": tti_input.id + "." + ext,
                "status": "completed",
                "timestamp": int(time.time()),
                "elapsed": round(poll_elapsed, 2)
            }
            
            final_json_key = f"{tti_input.id}_final.json"
            try:
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=final_json_key,
                    Body=json.dumps(output_json),
                    ContentType='application/json'
                )
                logger.debug(f"Uploaded final metadata to s3://{S3_BUCKET}/{final_json_key}")
            except Exception as e:
                logger.error(f"Failed to upload final metadata to S3: {e}")
                # Don't delete message on S3 error, let it retry
                continue
            
            # Update the original request JSON with the actual seed used
            if tti_input.seed == 0:
                try:
                    original_json_key = f"{tti_input.id}.json"
                    # Read the original JSON
                    original_response = s3.get_object(Bucket=S3_BUCKET, Key=original_json_key)
                    original_data = json.loads(original_response['Body'].read())
                    # Update with actual seed
                    original_data['seed'] = seed
                    # Write back to S3
                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=original_json_key,
                        Body=json.dumps(original_data),
                        ContentType='application/json'
                    )
                    logger.debug(f"Updated original request JSON with actual seed: {seed}")
                except Exception as e:
                    logger.error(f"Failed to update original request JSON with seed: {e}")
                    # This is non-critical, don't fail the whole process
            
            # Only delete the SQS message after successful processing
            logger.info(f"Successfully processed message {tti_input.id}, deleting from SQS queue")
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            comfy_success = True  # Mark ComfyUI processing as successful
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error communicating with ComfyUI: {e}")
            # Don't delete message on network error, let it retry
            apply_backoff()
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing message {tti_input.id}: {e}")
            # Don't delete message on unexpected error, let it retry
            apply_backoff()
            continue
    
    # Reset poll interval if ComfyUI processing was successful
    if comfy_success:
        reset_poll_interval()


# Response: {'prompt_id': 'a3bf9763-4cf8-4aef-9d70-36d89d9d03d5', 'number': 0, 'node_errors': {}}


def main():
    # Initialize AWS role assumption
    logger.info("Starting comfy-watcher...")
    if not assume_dnd_role():
        logger.error(f"Failed to assume {AWS_ROLE_NAME}. Exiting.")
        sys.exit(1)
    
    # Schedule periodic role refresh
    schedule_role_refresh()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "send":
            send_sqs_message(" ".join(sys.argv[2:]) or "Hello from SQS!")
            return
        elif sys.argv[1] in ("recv", "receive"):
            # Check both queues when receiving
            receive_sqs_messages(FAST_QUEUE)
            receive_sqs_messages(SLOW_QUEUE)
            return
    else:
        while True:
            global iteration_counter
            iteration_counter += 1
            
            # Check both queues in the main loop
            receive_sqs_messages(FAST_QUEUE)
            receive_sqs_messages(SLOW_QUEUE)
            
            # Every 10 iterations, invoke the Trello Lambda function
            if iteration_counter % 10 == 0:
                invoke_trello_lambda()
                logger.debug(f"Completed iteration {iteration_counter}, invoked Trello Lambda")
            
            time.sleep(current_poll_interval)


# Utility to look up SQS URL by queue name
def get_sqs_url_by_name(queue_name):
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        url = response["QueueUrl"]
        logger.debug(f"SQS URL for '{queue_name}': {url}")
        return url
    except Exception as e:
        logger.debug(f"Error getting SQS URL for '{queue_name}': {e}")
        return None


# Insert seed and uuid into EXIF metadata of an image
def insert_seed_uuid_exif(image_path, seed, uuid):
    with open(image_path, "rb") as f:
        img = Image(f)

    # Check if the image has EXIF data and ImageDescription tag
    if img.has_exif and hasattr(img, 'image_description'):
        # Get the current description (optional)
        logger.debug(f"Current ImageDescription: {img.image_description}")

        # Set the new ImageDescription
        img.image_description = f"seed:{seed};uuid:{uuid}"

        # Save the updated image
        with open("modified_image_exif.jpg", "wb") as new_f:
            new_f.write(img.bytes)
        logger.debug("ImageDescription updated successfully using exif library.")
    elif img.has_exif:
        # If the tag doesn't exist, you can add it
        img.image_description = f"seed:{seed};uuid:{uuid}"
        with open("modified_image_exif.jpg", "wb") as new_f:
            new_f.write(img.bytes)
        logger.debug("ImageDescription added successfully using exif library.")
    else:
        logger.info("Image does not contain EXIF data or ImageDescription tag.")


def poll_comfyui_history(prompt_id, base_url=None) -> dict:
    if base_url is None:
        base_url = f"http://{COMFY_HOST}:{COMFY_PORT}/history/"
    url = base_url + str(prompt_id)
    delay = 1
    for i in range(600):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text
                    logger.debug(f"Error parsing JSON response: {data}")
                if data != {}:
                    retval = data[prompt_id]["outputs"]
                    logger.debug(
                        f"History for {prompt_id} received after {i+1} seconds."
                    )
                    return retval
            else:
                logger.debug(f"Non-200 response: {resp.status_code}")
        except Exception as e:
            logger.debug(f"Error polling history: {e}")
        time.sleep(delay)
        delay = min(delay * 2, 10)  # Exponential backoff, max 10 seconds
    logger.debug(f"Timeout: No history for {prompt_id} after 600 seconds.")
    return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        # Cancel the role refresh timer
        if role_refresh_timer:
            role_refresh_timer.cancel()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Cancel the role refresh timer
        if role_refresh_timer:
            role_refresh_timer.cancel()
        sys.exit(1)
