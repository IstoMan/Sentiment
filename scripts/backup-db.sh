#!/usr/bin/env bash
# Backup database using pg_dump
set -euo pipefail

PROJECT_NAME="sentiment"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sentiment_db_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "Backing up database to $BACKUP_FILE..."

podman exec "${PROJECT_NAME}-db" pg_dump -U sentiment_user sentiment_db --clean --if-exists > "$BACKUP_FILE"

echo "✓ Database backed up successfully"
echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

gzip "$BACKUP_FILE"
echo "✓ Compressed to ${BACKUP_FILE}.gz"
