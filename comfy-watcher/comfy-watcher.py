
# Poll ComfyUI history endpoint for prompt results
import time
import os
import sys
import time
import json
import boto3
import requests
import secrets
from PIL import Image
import piexif


# S3 Watcher config
S3_BUCKET = os.environ.get("AWS_S3_BUCKET")

# SQS config
QUEUE_NAME = os.getenv("AWS_SQS_NAME", "")

s3 = boto3.client("s3")
sqs = boto3.client("sqs")


def send_sqs_message(queue_name, message_body):
    queue_url = get_sqs_url_by_name(queue_name)
    if not queue_url:
        print(f"Queue URL not found for '{queue_name}'.")
        return
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
    print("SQS message sent:", response["MessageId"])


def receive_sqs_messages(queue_name):
    queue_url = get_sqs_url_by_name(queue_name)
    if not queue_url:
        print(f"Queue URL not found for '{queue_name}'.")
        return

    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    messages = response.get("Messages", [])
    for msg in messages:
        print("SQS received:", msg["Body"])
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
            print(
                f"Workflow file not found at {workflow_path}. Please ensure it exists."
            )
            return

        # workflow variable is loaded and available here
        print("SQS message deleted")
        random_64bit = secrets.randbits(64)
        workflow["16"]["inputs"]["text"] = sqs_body["prompt"]
        workflow["53"]["inputs"]["height"] = sqs_body["height"]
        workflow["53"]["inputs"]["width"] = sqs_body["width"]
        workflow["3"]["inputs"]["steps"] = sqs_body["steps"]
        workflow["3"]["inputs"]["seed"] = random_64bit
        prompt = {"prompt": workflow}
        data = json.dumps(prompt).encode("utf-8")
        response = requests.post(
            "http://localhost:8188/prompt",
            headers={"Content-Type": "application/json"},
            data=data,
        )
        poll_response = poll_comfyui_history(response.json().get("prompt_id"))

# Response: {'prompt_id': 'a3bf9763-4cf8-4aef-9d70-36d89d9d03d5', 'number': 0, 'node_errors': {}}


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "send":
            send_sqs_message(" ".join(sys.argv[2:]) or "Hello from SQS!")
            return
        elif sys.argv[1] in ("recv", "receive"):
            receive_sqs_messages(QUEUE_NAME)
            return


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

# Utility to look up SQS URL by queue name
def get_sqs_url_by_name(queue_name):
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        url = response['QueueUrl']
        print(f"SQS URL for '{queue_name}': {url}")
        return url
    except Exception as e:
        print(f"Error getting SQS URL for '{queue_name}': {e}")
        return None


# Insert seed and uuid into EXIF metadata of an image
def insert_seed_uuid_exif(image_path, seed, uuid, output_path=None):
    """
    Inserts the seed and uuid into the ImageDescription EXIF tag of the image.
    If output_path is not provided, overwrites the original image.
    """
    if output_path is None:
        output_path = image_path
    img = Image.open(image_path)
    exif_dict = piexif.load(img.info.get('exif', b""))
    desc = f"seed:{seed};uuid:{uuid}"
    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = desc.encode('utf-8')
    exif_bytes = piexif.dump(exif_dict)
    img.save(output_path, exif=exif_bytes)
    print(f"Inserted seed and uuid into EXIF: {output_path}")


def poll_comfyui_history(prompt_id, base_url="http://127.0.0.1:8188/history/") -> dict:
    url = base_url + str(prompt_id)
    for i in range(600):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    data = None
                if data and data.json() != {}:
                    retval = data.json()[prompt_id]["outputs"]
                    print(f"History for {prompt_id} received after {i+1} seconds.")
                    return retval
            else:
                print(f"Non-200 response: {resp.status_code}")
        except Exception as e:
            print(f"Error polling history: {e}")
        time.sleep(1)
    print(f"Timeout: No history for {prompt_id} after 600 seconds.")
    return None


if __name__ == "__main__":
    main()
