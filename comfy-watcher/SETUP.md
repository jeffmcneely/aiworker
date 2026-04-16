# ComfyUI Watcher Setup

Minimal setup for running the watcher in this repository.

## Required Configuration

Create `.env` from the template:

```bash
cd comfy-watcher
cp .env.example .env
```

Set these values in `.env` (or your runtime environment):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `AWS_ROLE_NAME`
- `COMFYUI_URL`
- `POLL_INTERVAL`
- `LOG_LEVEL`

Use [comfy-watcher/.env.example](comfy-watcher/.env.example) as the source of truth for defaults and optional keys.

Notes:
- The watcher assumes `AWS_ROLE_NAME` and then reads queue/bucket names from SSM (`/ai/sqs-fast`, `/ai/sqs-slow`, `/ai/bucket`).
- For production, credentials can be mounted as Docker secrets at `/run/secrets/aws_access_key_id` and `/run/secrets/aws_secret_access_key`.

## Run Locally (Python)

```bash
cd comfy-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 comfy-watcher.py
```

## Run In Docker

```bash
cd comfy-watcher
docker build -t comfy-watcher .
docker run --rm --env-file .env comfy-watcher
```

## Run In Kubernetes (Helm)

```bash
cd comfy-watcher
helm upgrade --install comfy-watcher . -n aiworker --create-namespace -f values.yaml
kubectl get pods -n aiworker
```

To remove it:

```bash
helm uninstall comfy-watcher -n aiworker
```
