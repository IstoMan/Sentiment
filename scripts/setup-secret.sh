#!/usr/bin/env bash
# Setup Podman secret for database password
set -euo pipefail

SECRET_NAME="db_password"
DEFAULT_PASSWORD="secure_$(openssl rand -hex 16 2>/dev/null || date +%s)"

echo "Setting up Podman secret for database password..."
echo "NOTE: Password is stored in Podman secret, NOT in .env file"
echo ""

if podman secret exists "$SECRET_NAME" 2>/dev/null; then
    echo "Secret '$SECRET_NAME' already exists."
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman secret rm "$SECRET_NAME"
    else
        echo "Keeping existing secret."
        exit 0
    fi
fi

# Check if password provided as argument
if [ $# -gt 0 ]; then
    PASSWORD="$1"
    echo "Using provided password"
elif [ -t 0 ]; then
    # Interactive mode
    read -sp "Enter database password (or press Enter to generate): " PASSWORD
    echo
    if [ -z "$PASSWORD" ]; then
        PASSWORD="$DEFAULT_PASSWORD"
        echo "Generated secure password"
    fi
else
    # Non-interactive mode
    PASSWORD="$DEFAULT_PASSWORD"
    echo "Generated secure password: $PASSWORD"
fi

echo "$PASSWORD" | podman secret create "$SECRET_NAME" -

echo "✓ Secret '$SECRET_NAME' created successfully"
echo ""
echo "To view or update the secret:"
echo "  podman secret rm $SECRET_NAME"
echo "  echo 'new_password' | podman secret create $SECRET_NAME -"
