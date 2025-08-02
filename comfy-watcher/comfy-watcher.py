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

# S3 Watcher config
S3_BUCKET = os.environ.get("AWS_S3_BUCKET")

# SQS config
QUEUE_NAME = os.getenv("AWS_SQS_NAME", "")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")
s3 = boto3.client("s3")
sqs = boto3.client("sqs")


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
        sqs_body = json.loads(msg["Body"])
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
        # Load workflow from hidream.json
        try:
            workflow_path = os.path.join(
                os.path.dirname(__file__),
                "workflows",
                sqs_body.get("model", "hidream") + ".json",
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
        random_64bit = secrets.randbits(64)
        match sqs_body.get("model", "hidream"):
            case "hidream":
                workflow["16"]["inputs"]["text"] = sqs_body["prompt"]
                workflow["53"]["inputs"]["height"] = sqs_body["height"]
                workflow["53"]["inputs"]["width"] = sqs_body["width"]
                workflow["3"]["inputs"]["steps"] = sqs_body["steps"]
                workflow["3"]["inputs"]["seed"] = random_64bit
            case "flux":
                workflow["41"]["inputs"]["clip_l"] = sqs_body["prompt"]
                workflow["41"]["inputs"]["t5xxl"] = sqs_body["prompt"]
                workflow["31"]["inputs"]["seed"] = random_64bit
                workflow["27"]["inputs"]["height"] = sqs_body["height"]
                workflow["27"]["inputs"]["width"] = sqs_body["width"]

        prompt = {"prompt": workflow}
        data = json.dumps(prompt).encode("utf-8")
        logger.info(f"using prompt: {sqs_body['prompt']}")
        logger.debug(f"Sending workflow to ComfyUI: {data}")
        response = requests.post(
            "http://localhost:8188/prompt",
            headers={"Content-Type": "application/json"},
            data=data,
        )
        poll_response = poll_comfyui_history(response.json().get("prompt_id"))
        logger.debug(f"Poll response: {poll_response}")
        
        # Upload poll_response to S3 as JSON
        output_json_key = f"{random_64bit}_output.json"
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
        #     random_64bit,
        #     sqs_body.get("id"),
        # )
#        logger.info("Inserted seed and uuid into EXIF metadata.")
        # Upload generated image to S3
        image_filename = poll_response["9"]["images"][0]["filename"]
        ext = os.path.splitext(image_filename)[1][1:]
        image_path = os.path.join(OUTPUT_FOLDER, image_filename)
        s3_key = sqs_body["id"] + '.' + ext
        try:
            s3.upload_file(image_path, S3_BUCKET, s3_key)
            logger.debug(f"Uploaded {image_path} to s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload {image_path} to S3: {e}")


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
            time.sleep(1)


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


def poll_comfyui_history(prompt_id, base_url="http://127.0.0.1:8188/history/") -> dict:
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
