#!/bin/bash

# Kubernetes deployment script for ComfyUI Watcher

set -e

NAMESPACE="comfy-watcher"
CONTEXT=${KUBECTL_CONTEXT:-$(kubectl config current-context)}

echo "Deploying ComfyUI Watcher to Kubernetes cluster: $CONTEXT"
echo "Namespace: $NAMESPACE"
echo ""

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "Error: kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Function to check if kustomize is available
check_kustomize() {
    if ! command -v kustomize &> /dev/null; then
        echo "Warning: kustomize is not installed. Using kubectl apply instead."
        USE_KUSTOMIZE=false
    else
        USE_KUSTOMIZE=true
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    
    echo "Waiting for deployment $deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/$deployment -n $namespace
}

# Main deployment function
deploy() {
    echo "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    echo "Applying configuration..."
    if [ "$USE_KUSTOMIZE" = true ]; then
        kustomize build . | kubectl apply -f -
    else
        kubectl apply -f .
    fi
    
    echo "Waiting for ComfyUI to be ready..."
    wait_for_deployment "comfyui" "$NAMESPACE"
    
    echo "Waiting for ComfyUI Watcher to be ready..."
    wait_for_deployment "comfy-watcher" "$NAMESPACE"
    
    echo ""
    echo "Deployment completed successfully!"
    echo ""
    echo "To check the status:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo ""
    echo "To view logs:"
    echo "  kubectl logs -f deployment/comfy-watcher -n $NAMESPACE"
    echo "  kubectl logs -f deployment/comfyui -n $NAMESPACE"
    echo ""
    echo "To port-forward ComfyUI (optional):"
    echo "  kubectl port-forward service/comfyui-service 8188:8188 -n $NAMESPACE"
}

# Function to undeploy
undeploy() {
    echo "Removing ComfyUI Watcher from cluster..."
    
    if [ "$USE_KUSTOMIZE" = true ]; then
        kustomize build . | kubectl delete -f - --ignore-not-found=true
    else
        kubectl delete -f . --ignore-not-found=true
    fi
    
    echo "Undeployment completed!"
}

# Main script logic
check_kubectl
check_kustomize

case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "undeploy"|"delete"|"remove")
        undeploy
        ;;
    "status")
        kubectl get all -n $NAMESPACE
        ;;
    "logs")
        kubectl logs -f deployment/comfy-watcher -n $NAMESPACE
        ;;
    "logs-comfyui")
        kubectl logs -f deployment/comfyui -n $NAMESPACE
        ;;
    *)
        echo "Usage: $0 [deploy|undeploy|status|logs|logs-comfyui]"
        echo ""
        echo "Commands:"
        echo "  deploy        Deploy ComfyUI Watcher to Kubernetes (default)"
        echo "  undeploy      Remove ComfyUI Watcher from Kubernetes"
        echo "  status        Show deployment status"
        echo "  logs          Show ComfyUI Watcher logs"
        echo "  logs-comfyui  Show ComfyUI logs"
        exit 1
        ;;
esac
