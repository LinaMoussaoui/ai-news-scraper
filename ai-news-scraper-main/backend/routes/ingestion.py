"""Ingestion endpoints"""
from datetime import datetime
import logging

from fastapi import APIRouter

from backend.utils.api_errors import structured_http_exception, require_callable
from backend.utils.schemas import IngestRequest, ArticlePayload
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

@router.post("")
async def ingest_articles_api(request: IngestRequest):
    """
    Ingest articles into MinIO Bronze layer.
    
    Args:
        articles: List of article dictionaries
        source_type: Type of articles
    
    Returns:
        Ingestion statistics
    """
    logger.info(f"🔄 Ingestion request: {len(request.articles)} articles")
    
    try:
        from backend.utils.minio_client import MinIOClient
        from backend.services.ingestion import IngestionService
        
        minio_client = MinIOClient()
        ingestion_service = IngestionService(minio_client)
        ingest_batch = require_callable(
            ingestion_service,
            "ingest_batch",
            "MISSING_INGESTION_METHOD",
            "Implement IngestionService.ingest_batch or remove the /ingest route call path.",
        )
        stats = ingest_batch([article.model_dump() for article in request.articles], request.source_type)
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise structured_http_exception(
            500,
            "INGESTION_FAILED",
            "Ingestion request failed",
            "Check MinIO connectivity and ensure the request contains valid articles.",
            details={"exception": e.__class__.__name__},
        )

@router.get("/status")
async def get_ingestion_status():
    """Get current ingestion status"""
    try:
        from backend.utils.minio_client import MinIOClient
        from backend.services.ingestion import IngestionService
        
        minio_client = MinIOClient()
        ingestion_service = IngestionService(minio_client)
        status = ingestion_service.get_ingestion_status()
        
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error getting ingestion status: {e}")
        raise structured_http_exception(
            500,
            "INGESTION_STATUS_FAILED",
            "Unable to fetch ingestion status",
            "Check MinIO connectivity and the ingestion service implementation.",
            details={"exception": e.__class__.__name__},
        )
