"""Data lake endpoints"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datalake", tags=["data-lake"])

@router.get("/bronze/count")
async def count_bronze_articles():
    """Count articles in Bronze layer"""
    try:
        from backend.utils.minio_client import MinIOClient
        
        minio_client = MinIOClient()
        articles = minio_client.list_articles("ai-news-warehouse", layer="bronze", limit=10000)
        return {
            "layer": "bronze",
            "count": len(articles),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error counting Bronze articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/silver/count")
async def count_silver_articles():
    """Count articles in Silver layer"""
    try:
        from backend.utils.minio_client import MinIOClient
        
        minio_client = MinIOClient()
        articles = minio_client.list_articles("ai-news-warehouse", layer="silver", limit=10000)
        return {
            "layer": "silver",
            "count": len(articles),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error counting Silver articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gold/count")
async def count_gold_articles():
    """Count articles in Gold layer"""
    try:
        from backend.utils.minio_client import MinIOClient
        
        minio_client = MinIOClient()
        articles = minio_client.list_articles("ai-news-warehouse", layer="gold", limit=10000)
        return {
            "layer": "gold",
            "count": len(articles),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error counting Gold articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
