#!/usr/bin/env bash
# Manual Podman setup script - demonstrates all concepts without compose
set -euo pipefail

PROJECT_NAME="sentiment"

# Array to track containers created by this run
CREATED_CONTAINERS=()

# Cleanup function - removes only containers created by this run
cleanup_on_error() {
    local exit_code=$?
    trap - EXIT  # Clear trap to avoid recursion
    
    if [ $exit_code -ne 0 ] && [ ${#CREATED_CONTAINERS[@]} -gt 0 ]; then
        echo ""
        echo "⚠ Setup failed. Removing containers created by this run: ${CREATED_CONTAINERS[*]}"
        # Remove in reverse order
        for ((i=${#CREATED_CONTAINERS[@]}-1; i>=0; i--)); do
            podman rm -f "${CREATED_CONTAINERS[i]}" 2>/dev/null || true
        done
        echo "✓ Cleanup complete"
    fi
    exit $exit_code
}

# Set trap to cleanup on error or interrupt
trap cleanup_on_error EXIT
trap 'exit 130' INT TERM  # Ctrl-C should trigger cleanup

# Pre-flight check: fail early if target containers already exist
for container_name in "${PROJECT_NAME}-db" "${PROJECT_NAME}-api" "${PROJECT_NAME}-proxy"; do
    if podman container exists "$container_name" 2>/dev/null; then
        echo "Error: Container '$container_name' already exists."
        echo "Stop and remove it first, or use a different project name."
        echo ""
        echo "To clean up: ./scripts/manual-stop.sh"
        exit 1
    fi
done
VERSION="${VERSION:-1.0.0}"
IMAGE_NAME="localhost/${PROJECT_NAME}-analyzer:${VERSION}"
DB_SECRET_NAME="db_password"

NETWORK_FRONTEND="${PROJECT_NAME}_frontend"
NETWORK_BACKEND="${PROJECT_NAME}_backend"
VOLUME_DATA="${PROJECT_NAME}_db-data"

DB_USER="${DB_USER:-sentiment_user}"
DB_NAME="${DB_NAME:-sentiment_db}"

echo "=== Sentiment Analyzer Manual Podman Setup ==="
echo "Version: $VERSION"
echo "Image: $IMAGE_NAME"
echo ""

if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy .env.example to .env first."
    exit 1
fi

source .env

if ! podman secret exists "$DB_SECRET_NAME" 2>/dev/null; then
    echo "Error: Secret '$DB_SECRET_NAME' not found. Run ./scripts/setup-secret.sh first."
    exit 1
fi

echo "Step 1: Creating networks with isolation..."
podman network exists "$NETWORK_FRONTEND" 2>/dev/null || \
    podman network create --opt isolate=true "$NETWORK_FRONTEND"
podman network exists "$NETWORK_BACKEND" 2>/dev/null || \
    podman network create --internal --opt isolate=true "$NETWORK_BACKEND"
echo "✓ Networks created: $NETWORK_FRONTEND (isolated), $NETWORK_BACKEND (internal + isolated)"

echo ""
echo "Step 2: Creating volume..."
podman volume exists "$VOLUME_DATA" 2>/dev/null || podman volume create "$VOLUME_DATA"
echo "✓ Volume created: $VOLUME_DATA"

echo ""
echo "Step 3: Starting PostgreSQL database..."
CREATED_CONTAINERS+=("${PROJECT_NAME}-db")
podman run -d \
    --name "${PROJECT_NAME}-db" \
    --network "$NETWORK_BACKEND" \
    -e POSTGRESQL_USER="$DB_USER" \
    -e POSTGRESQL_DATABASE="$DB_NAME" \
    --secret "$DB_SECRET_NAME",type=env,target=POSTGRESQL_PASSWORD \
    -v "$VOLUME_DATA:/var/lib/pgsql/data:Z" \
    -v "./db/00-init.sh:/opt/app-root/src/postgresql-start/00-init.sh:Z,ro" \
    --restart unless-stopped \
    --health-cmd "pg_isready -U $DB_USER -d $DB_NAME" \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 5 \
    quay.io/sclorg/postgresql-16-c9s:20261104

echo "Waiting for database to be healthy..."
COUNTER=0
until [ "$(podman inspect --format='{{.State.Health.Status}}' ${PROJECT_NAME}-db 2>/dev/null)" = "healthy" ]; do
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
    if [ $COUNTER -ge 60 ]; then
        echo ""
        echo "✗ Database failed to become healthy after 120s"
        podman logs --tail 50 "${PROJECT_NAME}-db"
        exit 1
    fi
done
echo ""
echo "✓ Database is healthy"

echo ""
echo "Step 4: Building application image..."
podman build \
    -t "$IMAGE_NAME" \
    --build-arg APP_VERSION="$VERSION" \
    --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -f Containerfile \
    .
echo "✓ Image built: $IMAGE_NAME"

echo ""
echo "Step 5: Starting application..."
CREATED_CONTAINERS+=("${PROJECT_NAME}-api")
podman run -d \
    --name "${PROJECT_NAME}-api" \
    --network "$NETWORK_FRONTEND":alias=api \
    --network "$NETWORK_BACKEND" \
    -e DB_HOST="${PROJECT_NAME}-db" \
    -e DB_PORT=5432 \
    -e DB_NAME="$DB_NAME" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD_FILE="/run/secrets/db_password" \
    -e PORT=8080 \
    -e WAIT_FOR_DB=1 \
    --secret "$DB_SECRET_NAME" \
    --restart unless-stopped \
    --health-cmd 'curl -fsS http://localhost:8080/health || exit 1' \
    --health-interval 10s \
    "$IMAGE_NAME"

echo "Waiting for application to be ready..."
for i in {1..30}; do
    if [ "$(podman inspect -f '{{.State.Health.Status}}' "${PROJECT_NAME}-api" 2>/dev/null)" = "healthy" ]; then
        echo "✓ Application is healthy"
        break
    fi
    echo -n "."
    sleep 2
done
if [ "$(podman inspect -f '{{.State.Health.Status}}' "${PROJECT_NAME}-api" 2>/dev/null)" != "healthy" ]; then
    echo ""
    echo "✗ API not healthy after 60s"
    podman logs --tail 50 "${PROJECT_NAME}-api"
    exit 1
fi
echo ""

echo ""
echo "Step 6: Building and starting proxy..."
podman build -t "localhost/${PROJECT_NAME}-proxy:${VERSION}" proxy/

CREATED_CONTAINERS+=("${PROJECT_NAME}-proxy")
podman run -d \
    --name "${PROJECT_NAME}-proxy" \
    --network "$NETWORK_FRONTEND" \
    -p "127.0.0.1:8000:8080" \
    --restart unless-stopped \
    "localhost/${PROJECT_NAME}-proxy:${VERSION}"

echo "✓ Proxy started"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Application is now running at: http://127.0.0.1:8000"

# Clear trap on successful completion
trap - EXIT INT TERM

echo ""
echo "Useful commands:"
echo "  podman ps                                    # List running containers"
echo "  podman logs -f ${PROJECT_NAME}-api          # Follow application logs"
echo "  podman exec -it ${PROJECT_NAME}-db bash     # Access database container"
echo "  podman port ${PROJECT_NAME}-proxy           # Show port mappings"
echo ""
