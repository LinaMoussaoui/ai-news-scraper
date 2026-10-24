# Docker Setup Guide

## Files Overview

- **Dockerfile** - Multi-stage build for the FastAPI backend
- **docker-compose.yml** - Production setup (MinIO + PostgreSQL + Backend)
- **docker-compose.dev.yml** - Development override (hot reload enabled)
- **.dockerignore** - Optimization (excludes unnecessary files)

## Quick Start

### Production Setup (All Services)

```bash
# Build and start all containers (MinIO, PostgreSQL, Backend)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f minio
```

Services will be available at:

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9006
- **PostgreSQL**: localhost:5433 (psql -h localhost -p 5433 -U airy -d ai_news_warehouse)

### Development Setup (With Hot Reload)

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Backend code changes will auto-reload
# Logs with DEBUG level
docker-compose logs -f backend
```

### Database Setup

```bash
# Initialize PostgreSQL tables
docker-compose exec backend python -c "from backend.utils.postgres_client import PostgresClient; c = PostgresClient(); c.connect(); c.create_tables(); c.disconnect()"

# Or run manually
docker-compose exec postgres psql -U airy -d ai_news_warehouse -c "CREATE TABLE IF NOT EXISTS articles (...);"
```

## Container Details

### Backend Container (`backend`)

- **Image**: Local build from Dockerfile
- **Port**: 8000
- **Health Check**: HTTP request to `/health` every 30s
- **Depends On**: MinIO, PostgreSQL
- **Volumes**:
  - `./backend:/app/backend` - Application code
  - `./logs:/app/logs` - Application logs
- **Environment**: Configured for MinIO and PostgreSQL

### MinIO Container (`minio`)

- **Image**: minio/minio:latest
- **Ports**: 9000 (API), 9006 (Console)
- **Volumes**: `./data/minio:/data` - Persistent storage

### PostgreSQL Container (`postgres`)

- **Image**: postgres:15
- **Port**: 5433 (mapped from 5432)
- **Health Check**: pg_isready every 10s
- **Volumes**: `./data/postgres:/var/lib/postgresql/data` - Persistent storage

## Building the Backend Image

### Build Locally

```bash
docker build -t ai-news-backend:latest .
```

### Build with Custom Name

```bash
docker build -t myrepo/ai-news-backend:v1.0 .
```

### Multi-stage Build Benefits

- **Stage 1 (builder)**: Installs dependencies (larger)
- **Stage 2 (final)**: Only includes runtime dependencies (smaller image ~400MB vs 1.2GB)

## Running Backend Standalone

```bash
# Run backend container only (requires MinIO and PostgreSQL already running)
docker run -p 8000:8000 \
  -e MINIO_ENDPOINT=localhost:9005 \
  -e POSTGRES_HOST=localhost \
  -v ./logs:/app/logs \
  ai-news-backend:latest
```

## Environment Variables

Set in `docker-compose.yml` for containers:

```yaml
environment:
  MINIO_ENDPOINT: minio:9000 # Docker network hostname
  MINIO_ACCESS_KEY: minioadmin
  MINIO_SECRET_KEY: minioadmin123
  POSTGRES_HOST: postgres # Docker network hostname
  POSTGRES_PORT: 5432
  POSTGRES_USER: airy
  POSTGRES_PASSWORD: airypass123
  LOG_LEVEL: INFO
  API_HOST: 0.0.0.0
  API_PORT: 8000
```

**Note**: Internal Docker hostnames (`minio`, `postgres`) are used for inter-container communication, not localhost:9005 or localhost:5433.

## Stopping Services

```bash
# Stop all containers
docker-compose down

# Stop and remove all data
docker-compose down -v

# Stop specific service
docker-compose down backend
```

## Troubleshooting

### Backend can't connect to MinIO

- Check container logs: `docker-compose logs backend`
- Verify MinIO is running: `docker-compose ps`
- Check hostname: Backend should use `minio:9000` (not `localhost:9005`)
- Test MinIO: `curl http://minio:9000`

### Backend can't connect to PostgreSQL

- Check PostgreSQL is healthy: `docker-compose ps` (status should be "Up")
- Verify hostname: Backend should use `postgres:5432` (not `localhost:5433`)
- Test connection: `docker-compose exec backend python -c "from backend.utils.postgres_client import PostgresClient; c = PostgresClient(); c.test_connection()"`

### Health checks failing

```bash
# Check backend health directly
docker-compose exec backend curl http://localhost:8000/health

# View health check details
docker inspect backend-ai-news | grep -A 10 Healthcheck
```

### Image too large

- Multi-stage build already optimizes (~400MB)
- To further reduce: remove test dependencies, compress more aggressively
- Use `.dockerignore` to exclude unnecessary files

### Hot reload not working in development

- Ensure you're using `docker-compose.dev.yml` override
- File changes on host should be reflected in container
- If not: rebuild and restart `docker-compose down && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

## Advanced Usage

### Push to Registry

```bash
# Tag image
docker tag ai-news-backend:latest myregistry.azurecr.io/ai-news-backend:v1.0

# Push
docker push myregistry.azurecr.io/ai-news-backend:v1.0
```

### Run Tests in Container

```bash
docker-compose exec backend pytest backend/tests/ -v
```

### Access Container Shell

```bash
docker-compose exec backend /bin/bash
```

### Scale Backend (Multiple Instances)

```bash
# Note: Not recommended with same data sources
# For load balancing, use reverse proxy (Nginx)
docker-compose up -d --scale backend=3
```

## Performance Optimization

- **Multi-stage build**: Reduces image size
- **Health checks**: Automatically restart unhealthy containers
- **Depends on**: Ensures correct startup order
- **Volumes**: Mounts for logs and code (avoid copying large files)
- **Python optimization**: PYTHONUNBUFFERED, PYTHONDONTWRITEBYTECODE

## Production Considerations

For production deployment:

1. **Use environment file**: Create `.env` with secrets (not in docker-compose.yml)
2. **Set restart policy**: `restart: unless-stopped`
3. **Enable health checks**: Already configured
4. **Use external PostgreSQL/MinIO**: Don't run in containers for production
5. **Use Kubernetes**: For orchestration at scale
6. **Setup monitoring**: Prometheus, Grafana
7. **Log aggregation**: ELK stack, Splunk

Example production docker-compose.yml:

```yaml
services:
  backend:
    image: myregistry.com/ai-news-backend:v1.0
    environment:
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      POSTGRES_HOST: ${POSTGRES_HOST}
    env_file: .env.production
    restart: unless-stopped
    # ... other configs
```

## Dockerfile Explanation

```dockerfile
# Multi-stage approach
FROM python:3.11-slim as builder
  # Install build dependencies
  # Install Python packages

FROM python:3.11-slim
  # Copy only runtime packages from builder
  # Copy application code
  # Set environment
  # Health check
  # Run command
```

This approach:

- ✅ Reduces final image size (no build tools)
- ✅ Faster startup
- ✅ Smaller downloads for deployments
- ✅ Better security (fewer tools)

## See Also

- [README.md](README.md) - Quick start guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture
- [docker-compose.yml](docker-compose.yml) - Service definitions
