# Deployment Guide

This project now runs as a production Docker Compose stack with a FastAPI backend, a Next.js frontend, PostgreSQL, Redis, MinIO, and Airflow.

## What You Need

- Docker Desktop or Docker Engine with Compose
- A `.env` file at the repository root
- Optional: a public domain if you are deploying beyond localhost

## Step 1: Create and edit `.env`

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set real values for:

- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `POSTGRES_PASSWORD`
- `AIRFLOW_POSTGRES_PASSWORD`
- `AIRFLOW_WEBSERVER_SECRET_KEY`
- `PGADMIN_DEFAULT_PASSWORD`

If you are deploying to a public domain or reverse proxy, also set:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`

For a single-machine Docker deployment, the defaults in `.env.example` are already aligned with `localhost`.

## Step 2: Build and start the stack

Run this from the repository root:

```powershell
docker compose up -d --build
```

This starts:

- `frontend` on port `3000`
- `backend` on port `8000`
- `postgres` on port `5433`
- `minio` on ports `9005` and `9006`
- `redis` on port `6379`
- `pgadmin` on port `5050`
- `airflow-webserver` on port `8080`

## Step 3: Verify the services

Check container status:

```powershell
docker compose ps
```

Check the backend health endpoint:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Check analytics trends:

```powershell
curl.exe "http://127.0.0.1:8000/analytics/trends?days=7"
```

Open the app in your browser:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/docs`
- Airflow: `http://localhost:8080`
- MinIO console: `http://localhost:9006`
- PgAdmin: `http://localhost:5050`

## Step 4: Keep the deployment updated

When code changes, rebuild and restart:

```powershell
docker compose up -d --build
```

If you change only container data or config, you can restart a single service:

```powershell
docker compose restart backend
```

## Production Notes

- The frontend builds with `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` at image build time.
- If your frontend and backend are on different public domains, set those variables before rebuilding.
- `.env` is ignored by git, so it is safe to keep secrets there locally.
- Do not commit real passwords or keys to GitHub.
