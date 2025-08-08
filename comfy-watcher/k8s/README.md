# Kubernetes Deployment for ComfyUI Watcher

This directory contains Kubernetes manifests for deploying the ComfyUI Watcher application in a Kubernetes cluster.

## Quick Start

1. **Configure your environment:**
   ```bash
   # Edit the configuration files
   vi k8s/configs/production.env
   vi k8s/secrets/aws.env
   ```

2. **Deploy to Kubernetes:**
   ```bash
   cd k8s
   chmod +x deploy.sh
   ./deploy.sh deploy
   ```

3. **Check deployment status:**
   ```bash
   ./deploy.sh status
   ```

## Files Structure

```
k8s/
├── namespace.yaml           # Namespace definition
├── configmap.yaml          # Application configuration
├── storage.yaml            # Persistent volume claims
├── rbac.yaml              # Service account and permissions
├── comfyui.yaml           # ComfyUI deployment and service
├── comfy-watcher.yaml     # ComfyUI Watcher deployment
├── hpa.yaml               # Horizontal Pod Autoscaler
├── network-policy.yaml    # Network security policies
├── kustomization.yaml     # Kustomize configuration
├── deploy.sh              # Deployment script
├── configs/
│   └── production.env     # Production environment config
├── secrets/
│   └── aws.env           # AWS credentials
└── patches/
    └── production.yaml   # Production-specific patches
```

## Configuration

### 1. AWS Credentials
Edit `secrets/aws.env`:
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 2. Application Configuration
Edit `configs/production.env`:
```bash
AWS_DEFAULT_REGION=us-west-2
AWS_S3_BUCKET=your-s3-bucket
AWS_SQS_NAME=your-sqs-queue
COMFY_HOST=comfyui-service
COMFY_PORT=8188
LOG_LEVEL=INFO
POLL_INTERVAL=2
```

### 3. Resource Requirements
Modify `patches/production.yaml` for your resource needs:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Deployment Options

### Option 1: Using the deployment script (Recommended)
```bash
./deploy.sh deploy
```

### Option 2: Using kubectl directly
```bash
kubectl apply -f .
```

### Option 3: Using Kustomize
```bash
kustomize build . | kubectl apply -f -
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment comfy-watcher --replicas=3 -n comfy-watcher
```

### Auto Scaling
The HPA (Horizontal Pod Autoscaler) is configured to scale between 1-5 replicas based on CPU and memory usage.

## Monitoring

### Check Pod Status
```bash
kubectl get pods -n comfy-watcher
```

### View Logs
```bash
# ComfyUI Watcher logs
kubectl logs -f deployment/comfy-watcher -n comfy-watcher

# ComfyUI logs
kubectl logs -f deployment/comfyui -n comfy-watcher
```

### Port Forward (for debugging)
```bash
kubectl port-forward service/comfyui-service 8188:8188 -n comfy-watcher
```

## Storage

The deployment uses PersistentVolumeClaims for:
- **comfy-models-pvc**: Stores ComfyUI models (50Gi)
- **comfy-output-pvc**: Shared output directory (10Gi)

Adjust storage sizes in `storage.yaml` based on your needs.

## Security

### Network Policies
Network policies are configured to:
- Allow comfy-watcher to communicate with ComfyUI
- Allow both services to access AWS APIs
- Restrict unnecessary traffic

### RBAC
Service accounts with minimal required permissions are configured.

### Secrets Management
AWS credentials are stored as Kubernetes secrets.

## Troubleshooting

### Common Issues

1. **Pod not starting:**
   ```bash
   kubectl describe pod <pod-name> -n comfy-watcher
   ```

2. **Image pull errors:**
   Ensure the comfy-watcher image is built and available:
   ```bash
   docker build -t comfy-watcher:latest ../
   # Push to your registry if using remote cluster
   ```

3. **AWS connectivity issues:**
   Check AWS credentials and permissions:
   ```bash
   kubectl logs deployment/comfy-watcher -n comfy-watcher
   ```

4. **ComfyUI connection issues:**
   Verify ComfyUI service is running:
   ```bash
   kubectl get svc comfyui-service -n comfy-watcher
   kubectl logs deployment/comfyui -n comfy-watcher
   ```

### Clean Up
```bash
./deploy.sh undeploy
```

## Production Considerations

1. **Image Registry**: Push your comfy-watcher image to a container registry
2. **Storage Classes**: Use appropriate storage classes for your cloud provider
3. **Resource Limits**: Adjust CPU/Memory based on workload
4. **Monitoring**: Integrate with Prometheus/Grafana for monitoring
5. **Logging**: Configure centralized logging (ELK, Loki, etc.)
6. **Backup**: Implement backup strategies for persistent data
