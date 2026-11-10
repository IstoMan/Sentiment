# Fresh Verification - Sentiment Analyzer

## Complete Clean Run from Scratch

### 1. Clean State
```bash
podman-compose down -v
podman volume prune -f
podman secret rm db_password
```

### 2. Setup
```bash
cp .env.example .env
./scripts/setup-secret.sh  # Auto-generates secure password
```

### 3. Start Stack
```bash
podman-compose up -d
```

**Result**: All containers start cleanly, DB initializes automatically, API connects after 2 retry attempts.

### 4. Verify Through Proxy (127.0.0.1:8000)

Health check:
```bash
curl http://127.0.0.1:8000/health
{"status": "healthy", "database": "healthy", "analyzer": "loaded"}
```

Analyze positive review:
```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Amazing product!"}'
{"id": 1, "sentiment": "positive", "compound": 0.6239, ...}
```

Stats:
```bash
curl http://127.0.0.1:8000/api/stats
{"positive_percentage": 60.0, "negative_percentage": 40.0, ...}
```

Web UI: http://127.0.0.1:8000/ ✓ Works

### 5. Network Isolation Verified
- Proxy (sentiment-proxy): workspace_frontend ONLY ✓
- API (sentiment-api): workspace_frontend AND workspace_backend ✓  
- DB (sentiment-db): workspace_backend ONLY ✓

### 6. Secret Verification
- DB: POSTGRESQL_PASSWORD set via secret type=env ✓
- API: Password read from /run/secrets/db_password ✓
- No plaintext in .env or compose.yaml ✓

### 7. Database Init
- Table created automatically via postgresql-start hook ✓
- Idempotent (safe to restart) ✓

## All Caveats FIXED ✓
