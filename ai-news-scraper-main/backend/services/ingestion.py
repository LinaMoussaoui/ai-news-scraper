"""
Data Ingestion Service
Handles batch and streaming ingestion of scraped articles into MinIO (Bronze layer)
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging
from backend.utils.minio_client import MinIOClient

logger = logging.getLogger(__name__)


def _schedule_realtime_event(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)

class IngestionService:
    """
    Handles data ingestion from scrapers into the data lake (Bronze layer)
    Supports both batch and streaming ingestion
    """
    
    def __init__(self, minio_client: Optional[MinIOClient] = None, 
                 bucket_name: str = "ai-news-warehouse"):
        """
        Initialize ingestion service.
        
        Args:
            minio_client: MinIO client instance (creates default if None)
            bucket_name: MinIO bucket for storing bronze data
        """
        self.minio_client = minio_client or MinIOClient()
        self.bucket_name = bucket_name
        self.minio_client.create_bucket_if_not_exists(bucket_name)
        logger.info(f"IngestionService initialized with bucket: {bucket_name}")
    
    def ingest_batch(self, articles: List[Dict], source_type: str = "mixed") -> Dict:
        """
        Batch ingestion: store multiple articles in MinIO Bronze layer.
        This is the primary ingestion method for scheduled scraping jobs.
        
        Args:
            articles: List of article dictionaries from scrapers
            source_type: Type of articles (rss, html, mixed)
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 BATCH INGESTION STARTED - {len(articles)} articles")
        logger.info(f"{'='*60}")
        
        ingestion_start = datetime.utcnow()
        
        # Validate articles before ingestion
        valid_articles = []
        invalid_articles = []
        
        for article in articles:
            if self._validate_article(article):
                valid_articles.append(article)
            else:
                invalid_articles.append(article)
                logger.warning(f"   ⚠️ Invalid article skipped: {article.get('article_id')}")
        
        logger.info(f"✅ {len(valid_articles)} valid articles, ❌ {len(invalid_articles)} invalid")
        
        # Save to MinIO Bronze
        saved_paths = self.minio_client.save_articles_batch(
            self.bucket_name,
            valid_articles,
            layer="bronze"
        )
        
        ingestion_end = datetime.utcnow()
        duration = (ingestion_end - ingestion_start).total_seconds()
        
        stats = {
            "total_articles": len(articles),
            "valid_articles": len(valid_articles),
            "invalid_articles": len(invalid_articles),
            "saved_articles": len(saved_paths),
            "saved_paths": saved_paths,
            "ingestion_time_seconds": duration,
            "articles_per_second": len(saved_paths) / max(duration, 0.1),
            "bucket": self.bucket_name,
            "layer": "bronze",
            "timestamp": ingestion_end.isoformat() + "Z"
        }

        try:
            from backend.utils.event_broadcaster import EVENT_ARTICLES_BATCH, broadcast_bronze_event

            _schedule_realtime_event(
                broadcast_bronze_event(
                    EVENT_ARTICLES_BATCH,
                    valid_articles,
                )
            )
        except Exception as e:
            logger.debug(f"Realtime bronze event skipped: {e}")
        
        logger.info(f"\n📊 INGESTION STATISTICS:")
        logger.info(f"   Total: {stats['total_articles']} | Valid: {stats['valid_articles']} | Saved: {stats['saved_articles']}")
        logger.info(f"   Time: {duration:.2f}s | Rate: {stats['articles_per_second']:.2f} articles/sec")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def ingest_streaming(self, article: Dict) -> Optional[str]:
        """
        Streaming ingestion: store a single article immediately (as event arrives).
        This is for real-time article ingestion (future enhancement with Kafka/Pub-Sub).
        
        Args:
            article: Single article dictionary from scraper
        
        Returns:
            Saved object path if successful, None otherwise
        """
        logger.info(f"📤 STREAMING: Ingesting article '{article.get('title')[:50]}...'")
        
        if not self._validate_article(article):
            logger.warning(f"   ⚠️ Invalid article rejected: {article.get('article_id')}")
            return None
        
        path = self.minio_client.save_article(
            self.bucket_name,
            article,
            layer="bronze"
        )

        try:
            from backend.utils.event_broadcaster import EVENT_ARTICLE_ADDED, broadcast_bronze_event

            _schedule_realtime_event(
                broadcast_bronze_event(
                    EVENT_ARTICLE_ADDED,
                    {"article": article, "path": path},
                )
            )
        except Exception as e:
            logger.debug(f"Realtime bronze event skipped: {e}")
        
        return path
    
    def _validate_article(self, article: Dict) -> bool:
        """
        Validate article before ingestion.
        
        Args:
            article: Article dictionary
        
        Returns:
            True if valid, False otherwise
        """
        # Required fields
        required_fields = ["article_id", "title", "url", "source", "source_type"]
        if not all(article.get(field) for field in required_fields):
            return False
        
        # Title length
        if len(article.get("title", "")) < 3 or len(article.get("title", "")) > 500:
            return False
        
        # Content/summary exists
        if not article.get("content") and not article.get("description"):
            return False
        
        return True
    
    def get_ingestion_status(self) -> Dict:
        """Get current ingestion status and statistics"""
        try:
            bronze_articles = self.minio_client.list_articles(
                self.bucket_name,
                layer="bronze",
                limit=1000
            )
            
            rss_articles = self.minio_client.list_articles(
                self.bucket_name,
                layer="bronze",
                source_type="rss",
                limit=1000
            )
            
            html_articles = self.minio_client.list_articles(
                self.bucket_name,
                layer="bronze",
                source_type="html",
                limit=1000
            )
            
            return {
                "bucket": self.bucket_name,
                "total_bronze_articles": len(bronze_articles),
                "rss_articles": len(rss_articles),
                "html_articles": len(html_articles),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"Error getting ingestion status: {e}")
            return {}

