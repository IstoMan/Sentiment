#!/usr/bin/env bash
# Generate Kubernetes YAML from running containers
set -euo pipefail

PROJECT_NAME="sentiment"
OUTPUT_DIR="./kubernetes"

mkdir -p "$OUTPUT_DIR"

echo "Generating Kubernetes manifests..."

# With podman-compose 1.6+, containers are in a pod
# Check if pod exists and generate from that
if podman pod exists pod_sentiment 2>/dev/null; then
    echo "Generating from pod pod_sentiment (podman-compose 1.6+ mode)..."
    podman kube generate pod_sentiment > "${OUTPUT_DIR}/sentiment-pod.yaml"
    echo "✓ Generated ${OUTPUT_DIR}/sentiment-pod.yaml"
else
    echo "Generating per-container manifests..."
    podman generate kube "${PROJECT_NAME}-db" > "${OUTPUT_DIR}/db-deployment.yaml"
    podman generate kube "${PROJECT_NAME}-api" > "${OUTPUT_DIR}/api-deployment.yaml"
    podman generate kube "${PROJECT_NAME}-proxy" > "${OUTPUT_DIR}/proxy-deployment.yaml"
    echo "✓ Generated individual manifests in ${OUTPUT_DIR}/"
fi

ls -lh "$OUTPUT_DIR"
