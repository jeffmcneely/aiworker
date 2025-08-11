from fileinput import filename
import logging


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

# Function to read Docker secrets
def read_secret(secret_path):
    """Read secret from file path, fallback to environment variable"""
    logger.debug(f"Attempting to read secret from: {secret_path}")
    try:
        with open(secret_path, 'r') as f:
            value = f.read().strip()
            # Log only the first 6 and last 2 characters for safety
            if value:
                safe_value = value[:6] + ("..." if len(value) > 8 else "") + value[-2:]
            else:
                safe_value = "<empty>"
            logger.debug(f"Successfully read secret from {secret_path}: {safe_value}")
            return value
    except FileNotFoundError:
        logger.warning(f"Secret file not found: {secret_path}")
        return None

# AWS Configuration - support both secrets and env vars
def get_aws_credentials():
    # Try to read from Docker secrets first
    logger.debug("Getting AWS credentials...")
    access_key_file = os.getenv("COMFY_AWS_ACCESS_KEY_ID_FILE")
    secret_key_file = os.getenv("COMFY_AWS_SECRET_ACCESS_KEY_FILE")
    logger.debug(f"COMFY_AWS_ACCESS_KEY_ID_FILE: {access_key_file}")
    logger.debug(f"COMFY_AWS_SECRET_ACCESS_KEY_FILE: {secret_key_file}")
    if access_key_file and secret_key_file:
        access_key = read_secret(access_key_file)
        secret_key = read_secret(secret_key_file)
        logger.debug(f"Read access_key: {'set' if access_key else 'not set'}, secret_key: {'set' if secret_key else 'not set'} from secrets")
        if access_key and secret_key:
            return access_key, secret_key
    # Fallback to environment variables
    access_key = os.getenv("COMFY_AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("COMFY_AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    logger.debug(f"Read access_key: {'set' if access_key else 'not set'}, secret_key: {'set' if secret_key else 'not set'} from environment")
    return access_key, secret_key

# Get AWS credentials
aws_access_key_id, aws_secret_access_key = get_aws_credentials()

# Function to get S3 bucket (support secrets and env vars)
def get_s3_bucket():
    logger.debug("Getting S3 bucket name...")
    bucket_file = os.getenv("COMFY_AWS_S3_BUCKET_FILE")
    logger.debug(f"COMFY_AWS_S3_BUCKET_FILE: {bucket_file}")
    if bucket_file:
        bucket = read_secret(bucket_file)
        logger.debug(f"Read S3 bucket from secret: {bucket if bucket else 'not set'}")
        if bucket:
            return bucket
    bucket = os.getenv("COMFY_AWS_S3_BUCKET") or os.getenv("AWS_S3_BUCKET")
    logger.debug(f"Read S3 bucket from environment: {bucket if bucket else 'not set'}")
    return bucket

# Function to get SQS queue name (support secrets and env vars)
def get_sqs_queue_name():
    logger.debug("Getting SQS queue name...")
    queue_file = os.getenv("COMFY_AWS_SQS_NAME_FILE")
    logger.debug(f"COMFY_AWS_SQS_NAME_FILE: {queue_file}")
    if queue_file:
        queue = read_secret(queue_file)
        logger.debug(f"Read SQS queue name from secret: {queue if queue else 'not set'}")
        if queue:
            return queue
    queue = os.getenv("COMFY_AWS_SQS_NAME") or os.getenv("AWS_SQS_NAME", "")
    logger.debug(f"Read SQS queue name from environment: {queue if queue else 'not set'}")
    return queue

# S3 Watcher config
S3_BUCKET = get_s3_bucket()

# SQS config
QUEUE_NAME = get_sqs_queue_name()
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")

# ComfyUI config
COMFY_HOST = os.getenv("COMFY_HOST", "127.0.0.1")
COMFY_PORT = os.getenv("COMFY_PORT", "8188")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))

# AWS Region
AWS_REGION = os.getenv("COMFY_AWS_DEFAULT_REGION") or os.getenv("AWS_DEFAULT_REGION", "us-west-2")

# Initialize AWS clients with explicit credentials
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=AWS_REGION
)
sqs = boto3.client(
    "sqs",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=AWS_REGION
)


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


def receive_sqs_messages(queue_name):
    queue_url = get_sqs_url_by_name(queue_name)
    if not queue_url:
        logger.debug(f"Queue URL not found for '{queue_name}'.")
        return

    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    messages = response.get("Messages", [])
    for msg in messages:
        logger.debug(f"SQS received: {msg['Body']}")
        sqs_body_dict = json.loads(msg["Body"])
        tti_input = TTI_input(sqs_body_dict)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
        # Load workflow from hidream.json
        try:
            workflow_path = os.path.join(
                os.path.dirname(__file__),
                "workflows",
                tti_input.model + ".json",
            )
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
        except FileNotFoundError:
            logger.debug(
                f"Workflow file not found at {workflow_path}. Please ensure it exists."
            )
            return

        # workflow variable is loaded and available here
        logger.debug("SQS message deleted")
        # Use seed from the TTI_input instead of generating a new one
        seed = tti_input.seed if tti_input.seed != 0 else secrets.randbits(64)  # Use provided seed or generate random if 0
        match tti_input.model:
            case "hidream":
                workflow["16"]["inputs"]["text"] = tti_input.prompt
                workflow["53"]["inputs"]["height"] = tti_input.height
                workflow["53"]["inputs"]["width"] = tti_input.width
                workflow["3"]["inputs"]["steps"] = tti_input.steps
                workflow["3"]["inputs"]["seed"] = seed
                workflow["40"]["inputs"]["text"] = tti_input.negativePrompt
                workflow["3"]["inputs"]["cfg"] = tti_input.cfg
            case "flux":
                workflow["41"]["inputs"]["clip_l"] = tti_input.prompt
                workflow["41"]["inputs"]["t5xxl"] = tti_input.prompt
                workflow["31"]["inputs"]["seed"] = seed
                workflow["27"]["inputs"]["height"] = tti_input.height
                workflow["27"]["inputs"]["width"] = tti_input.width
            case "omnigen":
                workflow["6"]["inputs"]["text"] = tti_input.prompt
                workflow["11"]["inputs"]["height"] = tti_input.height
                workflow["11"]["inputs"]["width"] = tti_input.width
                #workflow["23"]["inputs"]["steps"] = tti_input.steps
                workflow["21"]["inputs"]["noise_seed"] = seed
                workflow["7"]["inputs"]["text"] = tti_input.negativePrompt
            case "sd3.5":
                workflow["16"]["inputs"]["text"] = tti_input.prompt
                workflow["40"]["inputs"]["text"] = tti_input.negativePrompt
                workflow["53"]["inputs"]["width"] = tti_input.width
                workflow["53"]["inputs"]["height"] = tti_input.height
                workflow["53"]["inputs"]["batch_size"] = 1
                workflow["3"]["inputs"]["seed"] = seed
                workflow["3"]["inputs"]["steps"] = tti_input.steps
                workflow["3"]["inputs"]["cfg"] = tti_input.cfg
                if "negative_prompt" in workflow.get("71", {}).get("inputs", {}):
                    workflow["71"]["inputs"]["text"] = tti_input.negativePrompt
        prompt = {"prompt": workflow}
        data = json.dumps(prompt).encode("utf-8")
        logger.info(f"using prompt: {tti_input.prompt}")
        logger.debug(f"Sending workflow to ComfyUI: {data}")
        comfy_url = f"http://{COMFY_HOST}:{COMFY_PORT}/prompt"
        response = requests.post(
            comfy_url,
            headers={"Content-Type": "application/json"},
            data=data,
        )
        
        # Measure time for polling ComfyUI history
        poll_start_time = time.time()
        poll_response = poll_comfyui_history(response.json().get("prompt_id"))
        poll_elapsed = time.time() - poll_start_time
        logger.debug(f"Poll response: {poll_response}")
        logger.info(f"ComfyUI polling completed in {poll_elapsed:.2f} seconds")
        
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
        
        # insert_seed_uuid_exif(
        #     os.path.join(OUTPUT_FOLDER, poll_response["9"]["images"][0]["filename"]),
        #     seed,
        #     tti_input.id,
        # )
#        logger.info("Inserted seed and uuid into EXIF metadata.")
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


# Response: {'prompt_id': 'a3bf9763-4cf8-4aef-9d70-36d89d9d03d5', 'number': 0, 'node_errors': {}}


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "send":
            send_sqs_message(" ".join(sys.argv[2:]) or "Hello from SQS!")
            return
        elif sys.argv[1] in ("recv", "receive"):
            receive_sqs_messages(QUEUE_NAME)
            return
    else:
        while True:
            receive_sqs_messages(QUEUE_NAME)
            time.sleep(POLL_INTERVAL)


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
    main()
