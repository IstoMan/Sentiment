#!/usr/bin/env bash
# Generate Kubernetes YAML from running containers
set -euo pipefail

PROJECT_NAME="sentiment"
OUTPUT_DIR="./kubernetes"

mkdir -p "$OUTPUT_DIR"

echo "Generating Kubernetes manifests..."

echo "Generating DB manifest..."
podman generate kube "${PROJECT_NAME}-db" > "${OUTPUT_DIR}/db-deployment.yaml"

echo "Generating API manifest..."
podman generate kube "${PROJECT_NAME}-api" > "${OUTPUT_DIR}/api-deployment.yaml"

echo "Generating proxy manifest..."
podman generate kube "${PROJECT_NAME}-proxy" > "${OUTPUT_DIR}/proxy-deployment.yaml"

echo "✓ Kubernetes manifests generated in $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR"
