#!/usr/bin/env bash
# Export database volume as tarball
set -euo pipefail

PROJECT_NAME="sentiment"
VOLUME_NAME="${PROJECT_NAME}_db-data"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_FILE="${BACKUP_DIR}/volume_${TIMESTAMP}.tar"

mkdir -p "$BACKUP_DIR"

if ! podman volume exists "$VOLUME_NAME" 2>/dev/null; then
    echo "Error: Volume $VOLUME_NAME does not exist"
    exit 1
fi

echo "Exporting volume $VOLUME_NAME..."

podman volume export "$VOLUME_NAME" -o "$EXPORT_FILE"

echo "✓ Volume exported to $EXPORT_FILE"
echo "Export size: $(du -h "$EXPORT_FILE" | cut -f1)"

gzip "$EXPORT_FILE"
echo "✓ Compressed to ${EXPORT_FILE}.gz"
