#!/usr/bin/env bash
# Save container image as tarball for distribution
set -euo pipefail

VERSION="${VERSION:-1.0.0}"
IMAGE_NAME="localhost/sentiment-analyzer:${VERSION}"
OUTPUT_DIR="./dist"
OUTPUT_FILE="${OUTPUT_DIR}/sentiment-analyzer-${VERSION}.tar"

mkdir -p "$OUTPUT_DIR"

echo "Saving image $IMAGE_NAME to $OUTPUT_FILE..."

podman save -o "$OUTPUT_FILE" "$IMAGE_NAME"

echo "✓ Image saved successfully"
echo "Archive size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "To load on another system:"
echo "  podman load -i $OUTPUT_FILE"
