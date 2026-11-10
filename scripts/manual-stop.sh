#!/usr/bin/env bash
# Stop and remove all containers, networks (keep volumes and images)
set -euo pipefail

PROJECT_NAME="sentiment"

echo "Stopping containers..."
podman stop -t 10 "${PROJECT_NAME}-proxy" "${PROJECT_NAME}-api" "${PROJECT_NAME}-db" 2>/dev/null || true

echo "Removing containers..."
podman rm "${PROJECT_NAME}-proxy" "${PROJECT_NAME}-api" "${PROJECT_NAME}-db" 2>/dev/null || true

echo "Removing networks..."
podman network rm "${PROJECT_NAME}_frontend" "${PROJECT_NAME}_backend" 2>/dev/null || true

echo "✓ Cleanup complete (volumes and images preserved)"
echo ""
echo "To also remove volumes (THIS DELETES DATA):"
echo "  podman volume rm ${PROJECT_NAME}_db-data"
echo ""
echo "To also remove images:"
echo "  podman rmi localhost/${PROJECT_NAME}-analyzer:1.0.0"
