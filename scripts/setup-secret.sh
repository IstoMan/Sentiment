#!/usr/bin/env bash
# Setup Podman secret for database password
set -euo pipefail

SECRET_NAME="db_password"
DEFAULT_PASSWORD="secure_$(openssl rand -hex 16 2>/dev/null || date +%s)"

echo "Setting up Podman secret for database password..."
echo "NOTE: Password is stored in Podman secret, NOT in .env file"
echo ""

# Check if --force flag is provided
FORCE=false
if [ "${1:-}" = "--force" ]; then
    FORCE=true
fi

if podman secret exists "$SECRET_NAME" 2>/dev/null; then
    if [ "$FORCE" = false ]; then
        echo "✓ Secret '$SECRET_NAME' already exists (use --force to recreate)"
        exit 0
    fi
    echo "Recreating secret (--force specified)..."
    podman secret rm "$SECRET_NAME"
fi

# Check if password provided as argument (skip --force)
if [ $# -gt 0 ] && [ "${1:-}" != "--force" ]; then
    PASSWORD="$1"
    echo "Using provided password"
elif [ $# -gt 1 ] && [ "${1:-}" = "--force" ]; then
    PASSWORD="$2"
    echo "Using provided password"
elif [ -t 0 ] && [ "$FORCE" = false ]; then
    # Interactive mode only if not forced
    read -sp "Enter database password (or press Enter to generate): " PASSWORD
    echo
    if [ -z "$PASSWORD" ]; then
        PASSWORD="$DEFAULT_PASSWORD"
        echo "Generated and stored a secure random password"
    fi
else
    # Non-interactive mode or force mode
    PASSWORD="$DEFAULT_PASSWORD"
    echo "Generated and stored a secure random password"
fi

printf "%s" "$PASSWORD" | podman secret create "$SECRET_NAME" -

echo "✓ Secret '$SECRET_NAME' created successfully"
echo ""
echo "To view or update the secret:"
echo "  podman secret rm $SECRET_NAME"
echo "  echo 'new_password' | podman secret create $SECRET_NAME -"
