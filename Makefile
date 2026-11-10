.PHONY: help setup build up down clean test test-cov logs backup save-image

PROJECT_NAME = sentiment
VERSION ?= 1.0.0
IMAGE_NAME = localhost/$(PROJECT_NAME)-analyzer:$(VERSION)

help:
	@echo "Sentiment Analyzer - Makefile Commands"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make setup          - Create .env file and Podman secret"
	@echo "  make build          - Build container image"
	@echo ""
	@echo "Compose Operations:"
	@echo "  make up             - Start all services with podman-compose"
	@echo "  make down           - Stop all services"
	@echo "  make clean          - Stop services and remove volumes (DELETES DATA)"
	@echo "  make logs           - Follow application logs"
	@echo "  make ps             - Show running containers"
	@echo ""
	@echo "Manual Podman Operations:"
	@echo "  make manual-setup   - Start services manually (no compose)"
	@echo "  make manual-stop    - Stop manually started services"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo ""
	@echo "Backup & Export:"
	@echo "  make backup         - Backup database with pg_dump"
	@echo "  make backup-volume  - Export database volume"
	@echo "  make save-image     - Save image as tarball"
	@echo "  make generate-kube  - Generate Kubernetes manifests"
	@echo ""
	@echo "Inspection:"
	@echo "  make inspect-api    - Inspect application container"
	@echo "  make inspect-db     - Inspect database container"
	@echo "  make events         - Watch Podman events"

setup:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env; \
		echo "Please edit .env and set your configuration"; \
	fi
	@chmod +x scripts/*.sh
	@./scripts/setup-secret.sh

build:
	podman build \
		-t $(IMAGE_NAME) \
		--build-arg APP_VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$$(date -u +%Y-%m-%dT%H:%M:%SZ) \
		-f Containerfile .
	@echo "✓ Built: $(IMAGE_NAME)"

up:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from example"; fi
	@./scripts/setup-secret.sh
	podman-compose up -d
	@echo "✓ Services started. Access at http://127.0.0.1:8000"

down:
	podman-compose down

clean:
	podman-compose down -v
	@echo "⚠ Volumes removed - all data deleted"

logs:
	podman-compose logs -f

ps:
	podman-compose ps

manual-setup:
	@chmod +x scripts/manual-setup.sh
	@./scripts/manual-setup.sh

manual-stop:
	@chmod +x scripts/manual-stop.sh
	@./scripts/manual-stop.sh

test:
	python3 -m pytest tests/ -v

docs-check:
	python3 scripts/check-doc-refs.py

test-cov:
	python3 -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-integration:
	@echo "Building test image..."
	@podman build --target test -t localhost/sentiment-analyzer-test:$(VERSION) . >/dev/null
	@echo "Running integration tests inside backend network..."
	podman run --rm \
	  --network sentiment_backend \
	  --secret db_password \
	  -e DB_HOST=db \
	  -e DB_NAME=sentiment_db \
	  -e DB_USER=sentiment_user \
	  -e DB_PASSWORD_FILE=/run/secrets/db_password \
	  -e SKIP_INTEGRATION_TESTS=false \
	  -e TESTING=0 \
	  localhost/sentiment-analyzer-test:$(VERSION) \
	  /opt/app-venv/bin/python -m pytest tests/test_integration.py -m integration -v

backup:
	@chmod +x scripts/backup-db.sh
	@./scripts/backup-db.sh

backup-volume:
	@chmod +x scripts/export-volume.sh
	@./scripts/export-volume.sh

save-image: build
	@chmod +x scripts/save-image.sh
	@VERSION=$(VERSION) ./scripts/save-image.sh

generate-kube:
	@chmod +x scripts/generate-kube.sh
	@./scripts/generate-kube.sh

inspect-api:
	podman inspect --format='{{json .State}}' sentiment-api | python3 -m json.tool
	@echo ""
	podman inspect --format='{{json .NetworkSettings}}' sentiment-api | python3 -m json.tool

inspect-db:
	podman inspect --format='{{json .State}}' sentiment-db | python3 -m json.tool
	@echo ""
	podman inspect --format='{{json .Mounts}}' sentiment-db | python3 -m json.tool

events:
	podman events --filter container=sentiment-api --filter container=sentiment-db --filter container=sentiment-proxy

shell-api:
	podman exec -it sentiment-api /bin/bash

shell-db:
	podman exec -it sentiment-db /bin/bash

port-check:
	@echo "Checking ports..."
	@podman port sentiment-proxy || echo "Proxy not running"
	@echo ""
	@echo "Checking listening ports in API container:"
	@podman exec sentiment-api ss -pant || echo "API not running"
