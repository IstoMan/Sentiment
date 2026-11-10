#!/usr/bin/env bash
# Setup Podman secret for database password
set -euo pipefail

SECRET_NAME="db_password"
DEFAULT_PASSWORD="changeme_secure_password_$(date +%s)"

echo "Setting up Podman secret for database password..."

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

if [ -f .env ]; then
    if grep -q "^POSTGRESQL_PASSWORD=" .env; then
        PASSWORD=$(grep "^POSTGRESQL_PASSWORD=" .env | cut -d= -f2)
        echo "Using password from .env file"
    else
        PASSWORD="$DEFAULT_PASSWORD"
        echo "POSTGRESQL_PASSWORD not found in .env, using generated password"
    fi
else
    PASSWORD="$DEFAULT_PASSWORD"
    echo "No .env file found, using generated password: $PASSWORD"
    echo "POSTGRESQL_PASSWORD=$PASSWORD" >> .env
    echo "Password saved to .env file"
fi

echo "$PASSWORD" | podman secret create "$SECRET_NAME" -

echo "✓ Secret '$SECRET_NAME' created successfully"
