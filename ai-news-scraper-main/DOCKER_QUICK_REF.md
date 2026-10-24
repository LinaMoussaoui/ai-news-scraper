# Docker Quick Reference

## Files Created/Updated

| File                     | Purpose                                         |
| ------------------------ | ----------------------------------------------- |
| `Dockerfile`             | Multi-stage build for backend (Python 3.11)     |
| `docker-compose.yml`     | Production setup (MinIO + PostgreSQL + Backend) |
| `docker-compose.dev.yml` | Development override (hot reload)               |
| `.dockerignore`          | Excludes unnecessary files from Docker build    |
| `DOCKER.md`              | Detailed Docker documentation                   |

## One-Line Commands

```bash
# Production: Start all services (MinIO, PostgreSQL, Backend)
docker-compose up -d

# Development: Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down

# Rebuild backend image
docker-compose build --no-cache backend

# Initialize database
docker-compose exec backend python -c "from backend.utils.postgres_client import PostgresClient; c = PostgresClient(); c.connect(); c.create_tables(); c.disconnect()"

# Run tests
docker-compose exec backend pytest backend/tests/ -v

# Access backend shell
docker-compose exec backend /bin/bash
```

## Service Status

Once running, check:

```bash
# All containers
docker-compose ps

# Backend API
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Interactive docs

# MinIO
http://localhost:9006  # Console (minioadmin / minioadmin123)

# PostgreSQL
psql -h localhost -p 5433 -U airy -d ai_news_warehouse
```

## Architecture

```
docker-compose.yml
├── minio:9000         (S3-compatible storage)
├── postgres:5432      (Data warehouse)
└── backend:8000       (FastAPI app - depends on above)
    ├── Exposes        → localhost:8000
    ├── Logs           → ./logs/
    ├── Code           → ./backend/
    └── Connects to    → minio:9000, postgres:5432 (internal DNS)
```

## Key Points

✅ **Internal Networking**: Services use Docker hostnames (`minio`, `postgres`), not `localhost:9005`
✅ **Hot Reload**: Use `docker-compose.dev.yml` to rebuild on code changes
✅ **Health Checks**: Auto-restart unhealthy containers
✅ **Dependencies**: Backend waits for PostgreSQL health check before starting
✅ **Persistent Storage**: Data in `./data/minio/` and `./data/postgres/`
✅ **Logs**: Accessible in `./logs/app.log` and via `docker-compose logs`

See `DOCKER.md` for full documentation.
