#!/usr/bin/env bash
# Push image to container registry (requires podman login first)
set -euo pipefail

VERSION="${VERSION:-1.0.0}"
LOCAL_IMAGE="localhost/sentiment-analyzer:${VERSION}"

echo "=== Push Container Image ==="
echo ""
echo "Before pushing, you need to:"
echo "1. Login to your registry:"
echo "   For Quay.io:        podman login quay.io"
echo "   For Docker Hub:     podman login docker.io"
echo ""
echo "2. Tag the image with your registry:"
echo "   For Quay.io:        podman tag $LOCAL_IMAGE quay.io/<username>/sentiment-analyzer:${VERSION}"
echo "   For Docker Hub:     podman tag $LOCAL_IMAGE docker.io/<username>/sentiment-analyzer:${VERSION}"
echo ""
echo "3. Push the tagged image:"
echo "   For Quay.io:        podman push quay.io/<username>/sentiment-analyzer:${VERSION}"
echo "   For Docker Hub:     podman push docker.io/<username>/sentiment-analyzer:${VERSION}"
echo ""
echo "Note: Always use fully qualified tags (no 'latest')"
echo "      Recommended: Use semantic versioning (e.g., 1.0.0, 1.0.1, etc.)"
