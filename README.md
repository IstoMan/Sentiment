# Sentiment Analyzer for Reviews

A containerized Python web application for sentiment analysis of product and movie reviews, built as a Red Hat DO188/EX188 course project demonstrating Podman and container technologies.

## Overview

This application provides a web interface and REST API for analyzing the sentiment of text reviews using the VADER (Valence Aware Dictionary and sEntiment Reasoner) lexicon-based sentiment analysis tool. Results are stored in PostgreSQL and statistics are displayed showing positive/negative/neutral percentages.

### Features

- 🎯 Simple, clean web UI for submitting and analyzing reviews
- 🔌 REST API for programmatic access
- 📊 Real-time sentiment statistics (positive/negative/neutral percentages)
- 💾 PostgreSQL database for persistent storage
- 🐋 Fully containerized with Podman
- 🔒 Security-focused (rootless, non-root user, secrets management)
- 📦 Multi-stage builds with Red Hat Universal Base Images (UBI)

## Architecture

```mermaid
graph TB
    User[User Browser/API Client]
    Proxy[Nginx Proxy<br/>ubi9/nginx-122<br/>Port 127.0.0.1:8000]
    API[Flask API<br/>sentiment-api<br/>Port 8080]
    DB[(PostgreSQL<br/>postgresql-16-c9s<br/>No exposed port)]
    
    User -->|HTTP| Proxy
    Proxy -->|frontend network| API
    API -->|backend network| DB
    
    DB -.->|named volume<br/>:Z mount| DataVol[db-data volume]
    DB -.->|:Z mount| InitSQL[init.sql]
    
    style Proxy fill:#e1f5ff
    style API fill:#fff4e6
    style DB fill:#f3e5f5
    style DataVol fill:#f1f8e9
```

### Network Topology

The application uses **two separate networks** to implement defense-in-depth:

- **frontend network**: Connects proxy ↔ API
- **backend network**: Connects API ↔ database

The proxy (and thus external users) cannot reach the database directly - all database access must go through the API tier.

## Quick Start

### Prerequisites

- Podman 4.9+ (rootless mode recommended)
- podman-compose 1.6+
- Python 3.11+ (for local testing)

### Option 1: Using podman-compose (Recommended)

```bash
# 1. Clone and setup
git clone https://github.com/IstoMan/Sentiment.git
cd Sentiment
make setup

# 2. Edit .env file with your configuration (optional)
vi .env

# 3. Start all services
make up

# 4. Access the application
# Web UI: http://127.0.0.1:8000
# API: http://127.0.0.1:8000/api
```

### Option 2: Manual Podman Commands

```bash
# 1. Setup environment and secret
cp .env.example .env
./scripts/setup-secret.sh

# 2. Run manual setup script
./scripts/manual-setup.sh

# 3. Access the application
# Web UI: http://127.0.0.1:8000
```

## API Usage

### Analyze a Review

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing! I love it!"}'
```

Response:
```json
{
  "id": 1,
  "text": "This product is amazing! I love it!",
  "preprocessed": "This product is amazing! I love it!",
  "sentiment": "positive",
  "compound": 0.8516,
  "positive": 0.576,
  "negative": 0.0,
  "neutral": 0.424
}
```

### Get Reviews

```bash
# Get recent reviews (paginated)
curl http://127.0.0.1:8000/api/reviews?limit=10&offset=0
```

### Get Statistics

```bash
# Get sentiment statistics
curl http://127.0.0.1:8000/api/stats
```

Response:
```json
{
  "total_reviews": 42,
  "positive_count": 28,
  "negative_count": 10,
  "neutral_count": 4,
  "positive_percentage": 66.67,
  "negative_percentage": 23.81,
  "neutral_percentage": 9.52,
  "average_compound": 0.3421
}
```

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

## DO188/EX188 Course Concepts Demonstrated

This project demonstrates all required concepts from Red Hat DO188 chapters 3-7:

| Concept | Location | Description |
|---------|----------|-------------|
| **Multi-stage Containerfile** | `Containerfile:1-18, 20-63` | Builder stage (Python 3.11) + runtime stage (UBI minimal) |
| **UBI Base Images** | `Containerfile:4, 20` | Uses `ubi9/python-311` for builder and `ubi-minimal` for runtime |
| **Non-root USER** | `Containerfile:53-57, 62` | Application runs as UID 1001 (appuser) |
| **ARG + ENV with defaults** | `Containerfile:6-7, 22-29` | `${APP_VERSION:-1.0.0}`, `${PORT:-8080}` |
| **EXPOSE** | `Containerfile:64` | Port 8080 (>1024 for rootless) |
| **LABEL** | `Containerfile:31-39` | Metadata: name, version, description, maintainer, build-date |
| **Exec-form ENTRYPOINT/CMD** | `Containerfile:69-70` | JSON array format: `["gunicorn"]`, `["--bind", ...]` |
| **Layer caching optimization** | `Containerfile:13-16` | Copy requirements.txt before app code |
| **COPY --from=builder** | `Containerfile:47` | Copy venv from builder stage |
| **Podman secret (file)** | `compose.yaml:11-13, 33-35` | DB password via `/run/secrets/db_password` |
| **Secret consumption in code** | `app/main.py:23-28` | Reads from `DB_PASSWORD_FILE` |
| **Named volume** | `compose.yaml:17, 76-77` | `db-data` for PostgreSQL persistence |
| **Bind mount with :Z** | `compose.yaml:18, 52` | SELinux label for init.sql and nginx.conf |
| **Two networks (isolation)** | `compose.yaml:49-51, 67, 72-75` | frontend + backend: proxy cannot reach DB |
| **User-created network** | `scripts/manual-setup.sh:29-31` | Networks with DNS for name resolution |
| **depends_on** | `compose.yaml:54-55, 68-69` | Service startup ordering with health checks |
| **container_name** | `compose.yaml:8, 28, 60` | Named containers for easy reference |
| **env_file** | `compose.yaml:14, 36, 63` | Load variables from `.env` file |
| **ports (127.0.0.1)** | `compose.yaml:61` | Rootless-friendly binding to loopback |
| **PostgreSQL UBI image** | `compose.yaml:5` | `quay.io/sclorg/postgresql-16-c9s` |
| **No published DB port** | `compose.yaml:5-20` | Database not exposed to host |
| **Fully qualified tags** | `Makefile:4, compose.yaml:30` | `localhost/sentiment-analyzer:1.0.0` (no `latest`) |
| **podman build** | `Makefile:27-32, scripts/manual-setup.sh:44-50` | Build with args |
| **podman run manual** | `scripts/manual-setup.sh:35-48, 52-64, 68-76` | All run parameters explicitly shown |
| **podman network create** | `scripts/manual-setup.sh:29-31` | Manual network setup |
| **podman secret create** | `scripts/setup-secret.sh:31` | Create secret from stdin |
| **podman volume create** | `scripts/manual-setup.sh:34-36` | Named volume creation |
| **podman save/load** | `scripts/save-image.sh:14` | Image distribution as tarball |
| **podman generate kube** | `scripts/generate-kube.sh:12-18` | Export to Kubernetes YAML |
| **pg_dump backup** | `scripts/backup-db.sh:15` | Database logical backup |
| **podman volume export** | `scripts/export-volume.sh:21` | Volume backup as tarball |
| **podman inspect --format** | `Makefile:95-99` | Extract specific JSON fields |
| **podman events** | `Makefile:101-102` | Monitor container events |
| **podman logs -f** | `Makefile:46, README` | Follow container logs |
| **podman port** | `Makefile:110-111` | Show port mappings |
| **podman exec** | `scripts/backup-db.sh:15, Makefile:107-110` | Execute commands in containers |
| **restart policies** | `compose.yaml:23, 58, 71` | `unless-stopped` for automatic restart |
| **healthcheck** | `Containerfile:66-67, compose.yaml:24-29, 56-62` | Container health monitoring |
| **HEALTHCHECK in Containerfile** | `Containerfile:66-67` | Native container health check |

### Additional Concepts Demonstrated

| Concept | Location | Description |
|---------|----------|-------------|
| **registries.conf concepts** | `scripts/push-image.sh` | Fully qualified registry names (quay.io, docker.io) |
| **UBI variants** | `Containerfile:4, 20` | `ubi9/python-311` (full) → `ubi-minimal` (runtime) |
| **Rootless subuid** | Implicit | All commands run rootless (no sudo) |
| **Copy-on-write layers** | `Containerfile` | Optimized layer order for caching |
| **DB env vars on empty volume** | `README:182-188` | Init only applies to new volumes |
| **Default network DNS issue** | `README:201-204` | User-created networks required for DNS |
| **App binding (0.0.0.0)** | `app/main.py:174, Containerfile:70` | Listen on all interfaces in container |
| **compose up -d/down** | `Makefile:41, 44` | Detached mode and cleanup |
| **podman ps** | `Makefile:48` | List containers |
| **podman image prune** | Not scripted | Manual cleanup (mentioned in docs) |

## Verification & Troubleshooting

### Verify Everything is Running

```bash
# Check container status
podman ps

# Should show 3 containers: sentiment-proxy, sentiment-api, sentiment-db
# All should have STATUS "Up" and HEALTH "healthy"
```

### Check Logs

```bash
# Follow all logs
make logs

# Or individual services
podman logs -f sentiment-api
podman logs -f sentiment-db
podman logs -f sentiment-proxy
```

### Check Port Mappings

```bash
# Show published ports
podman port sentiment-proxy

# Expected output:
# 8080/tcp -> 127.0.0.1:8000
```

### Check Network Connectivity

```bash
# Check what ports are listening in API container
podman exec sentiment-api ss -tuln

# You should see port 8080 listening
```

### Inspect Containers

```bash
# View full container state
podman inspect sentiment-api

# Extract specific fields
podman inspect --format='{{.State.Status}}' sentiment-api
podman inspect --format='{{.State.Health.Status}}' sentiment-db
podman inspect --format='{{json .NetworkSettings.Networks}}' sentiment-api | python3 -m json.tool
```

### Watch Container Events

```bash
# Monitor real-time container events
make events

# Or directly
podman events --filter container=sentiment-api
```

### Test Database Connection

```bash
# Access database shell
podman exec -it sentiment-db psql -U sentiment_user -d sentiment_db

# Run test query
\dt  # List tables
SELECT COUNT(*) FROM reviews;
\q   # Quit
```

## Common Issues and Solutions

### Issue: Database not initializing

**Symptom**: API can't connect to database, or init.sql not executed

**Cause**: Database environment variables only apply to an empty volume. If you've started the DB before with different credentials, the old data persists.

**Solution**:
```bash
# Stop and remove containers and volumes
make clean

# Or manually
podman-compose down -v

# Then restart
make up
```

### Issue: `podman-compose` can't find services

**Symptom**: `Error: no such container`

**Cause**: Default Podman network doesn't have DNS

**Solution**: The compose.yaml creates user-defined networks (`frontend` and `backend`) which have built-in DNS. Ensure you're using those networks, not the default.

### Issue: Can't connect to http://localhost:8000

**Symptom**: Connection refused when accessing application

**Cause**: Rootless Podman on some systems doesn't handle IPv6 localhost well

**Solution**: Use `http://127.0.0.1:8000` instead of `http://localhost:8000`

### Issue: :Z mount flag causes errors on non-SELinux systems

**Symptom**: Warnings about SELinux labels on Arch Linux or other non-RHEL systems

**Solution**: The `:Z` flag is a no-op on non-SELinux systems and is safe to keep. It's shown here because it's required practice for the DO188 exam. You can remove `:Z` if it causes issues, but it shouldn't.

### Issue: Permission denied in containers

**Symptom**: Application can't write logs or database can't initialize

**Cause**: Files created on host may have restrictive permissions

**Solution**:
```bash
# Fix permissions for bind mounts
chmod 644 db/init.sql
chmod 644 proxy/nginx.conf

# Database volumes should use named volumes (already configured)
```

### Issue: Port already in use

**Symptom**: `Error: address already in use`

**Solution**:
```bash
# Check what's using port 8000
ss -tuln | grep 8000

# Either stop the conflicting service or change the port in compose.yaml:
# ports:
#   - "127.0.0.1:8001:8080"
```

### Issue: Image build fails to download packages

**Symptom**: Network errors during `podman build`

**Solution**:
```bash
# Check network connectivity
curl -I https://registry.access.redhat.com/v2/

# Try with fresh cache
podman build --no-cache -t localhost/sentiment-analyzer:1.0.0 .
```

## Testing

### Run Unit Tests

```bash
# Install test dependencies
pip3 install -r requirements.txt -r requirements-test.txt

# Run all tests
make test

# Run with coverage
make test-cov

# Open coverage report
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS
```

### Run Integration Tests (requires running database)

```bash
# Start database
make up

# Run integration tests
SKIP_INTEGRATION_TESTS=false pytest tests/test_integration.py -v
```

## Backup and Distribution

### Backup Database

```bash
# Using pg_dump (logical backup)
make backup

# Or export entire volume (physical backup)
make backup-volume

# Backups are stored in ./backups/ directory
```

### Save and Distribute Image

```bash
# Save image as tarball
make save-image

# Copy dist/sentiment-analyzer-1.0.0.tar to target system

# Load on target system
podman load -i sentiment-analyzer-1.0.0.tar
```

### Push to Container Registry

```bash
# Login to registry
podman login quay.io
# or
podman login docker.io

# Tag image with registry
podman tag localhost/sentiment-analyzer:1.0.0 quay.io/yourusername/sentiment-analyzer:1.0.0

# Push
podman push quay.io/yourusername/sentiment-analyzer:1.0.0

# See scripts/push-image.sh for detailed instructions
```

### Generate Kubernetes Manifests

```bash
# Generate from running containers
make generate-kube

# Output in kubernetes/ directory
```

## Development

### Live Development with Volume Mount

Edit `compose.yaml` to add a bind mount for live code reloading:

```yaml
api:
  # ... existing config ...
  volumes:
    - ./app:/app/app:Z
  environment:
    - FLASK_ENV=development
    - FLASK_DEBUG=1
```

### Manual Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt -r requirements-test.txt

# Run locally (requires PostgreSQL running)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=sentiment_db
export DB_USER=sentiment_user
export DB_PASSWORD=yourpassword

flask --app app run --host 0.0.0.0 --port 8080
```

## Cleanup

### Stop Services (Keep Data)

```bash
make down
# or
./scripts/manual-stop.sh
```

### Remove Everything Including Data

```bash
make clean
```

### Remove Images

```bash
# Remove application image
podman rmi localhost/sentiment-analyzer:1.0.0

# Remove all unused images
podman image prune -a
```

## Project Structure

```
.
├── app/
│   ├── __init__.py           # Application package
│   ├── main.py               # Flask app and API routes
│   ├── sentiment.py          # VADER sentiment analysis
│   └── templates/
│       └── index.html        # Web UI
├── db/
│   └── init.sql              # Database initialization script
├── proxy/
│   └── nginx.conf            # Nginx reverse proxy configuration
├── scripts/
│   ├── setup-secret.sh       # Create Podman secret
│   ├── manual-setup.sh       # Manual Podman setup
│   ├── manual-stop.sh        # Stop manual setup
│   ├── backup-db.sh          # Backup with pg_dump
│   ├── export-volume.sh      # Export volume as tarball
│   ├── save-image.sh         # Save image as tarball
│   ├── generate-kube.sh      # Generate Kubernetes YAML
│   └── push-image.sh         # Push to registry instructions
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── test_sentiment.py     # Sentiment analysis tests
│   ├── test_api.py           # API endpoint tests
│   └── test_integration.py   # Integration tests
├── Containerfile             # Multi-stage container build
├── compose.yaml              # Podman Compose configuration
├── Makefile                  # Convenient command shortcuts
├── requirements.txt          # Python dependencies
├── requirements-test.txt     # Test dependencies
├── pytest.ini                # Pytest configuration
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Technology Stack

- **Language**: Python 3.11
- **Web Framework**: Flask 3.1
- **Sentiment Analysis**: VADER (vaderSentiment)
- **Database**: PostgreSQL 16 (CentOS Stream 9 image)
- **Container Runtime**: Podman 4.9+
- **Base Images**: Red Hat UBI 9
- **Web Server**: Gunicorn
- **Reverse Proxy**: Nginx (UBI 9)
- **Testing**: pytest, pytest-cov

## License

MIT License - See LICENSE file for details

## Course Context

This project is designed for Red Hat DO188 4.18 (Introduction to Containers, Kubernetes, and Red Hat OpenShift) and EX188 exam preparation. It demonstrates practical container skills including:

- Building multi-stage Containerfiles with UBI
- Implementing rootless, non-root container security
- Managing secrets with Podman
- Configuring multi-network architectures
- Using health checks and restart policies
- Backing up and distributing containers
- Troubleshooting containerized applications

## Screenshots

![Sentiment Analyzer Web UI](docs/screenshots/main-ui.png)
*Main web interface for sentiment analysis*

![API Response Example](docs/screenshots/api-response.png)
*JSON API response with sentiment scores*

## Contributing

This is a course project and not actively maintained, but suggestions for improvements are welcome via issues or pull requests.

## Author

DO188 Course Project - Red Hat Container Technologies

## Screenshots

### Main Application Interface
![Main Page](docs/screenshots/01-main-page.png)
*Clean, modern UI for sentiment analysis*

### Review Input
![Review Input](docs/screenshots/02-review-input.png)
*Submit product or movie reviews for analysis*

### Analysis Results
![Positive Result](docs/screenshots/03-positive-result.png)
*Real-time sentiment classification with detailed scores*

### Statistics Dashboard  
![Statistics](docs/screenshots/04-statistics.png)
*Positive/negative percentages and analytics*

### Recent Reviews
![Recent Reviews](docs/screenshots/05-recent-reviews.png)
*History of analyzed reviews with sentiment labels*

