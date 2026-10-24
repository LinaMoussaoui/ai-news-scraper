"""Health check endpoints"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Check API health"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }

@router.get("/health/minio")
async def health_minio():
    """Check MinIO connection"""
    from backend.utils.minio_client import MinIOClient
    minio_client = MinIOClient()
    is_healthy = minio_client.test_connection()
    return {
        "service": "MinIO",
        "status": "healthy" if is_healthy else "unhealthy",
        "endpoint": minio_client.endpoint
    }

@router.get("/health/postgres")
async def health_postgres():
    """Check PostgreSQL connection"""
    from backend.utils.postgres_client import PostgresClient
    postgres_client = PostgresClient()
    is_healthy = postgres_client.test_connection()
    return {
        "service": "PostgreSQL",
        "status": "healthy" if is_healthy else "unhealthy",
        "host": postgres_client.host,
        "port": postgres_client.port
    }
