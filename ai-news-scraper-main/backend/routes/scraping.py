"""Scraping endpoints"""
from datetime import datetime
import logging

from fastapi import APIRouter

from backend.utils.api_errors import structured_http_exception, require_callable
from backend.utils.schemas import ScrapingRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scraping"])

@router.post("")
async def scrape_articles(request: ScrapingRequest):
    """
    Scrape articles from configured sources.
    
    Args:
        scraper_type: 'rss', 'html', or 'both'
        limit_per_source: Max articles per source
    
    Returns:
        Scraping results with article count
    """
    logger.info(f"📡 Scraping request: {request.scraper_type} (limit: {request.limit_per_source})")
    
    try:
        from backend.services.scrapers.rss_scraper import RSSScraper
        from backend.services.scrapers.html_scraper import HTMLScraper
        from backend.services.ingestion import IngestionService
        from backend.utils.minio_client import MinIOClient
        from backend.utils.postgres_client import PostgresClient
        
        articles = []
        
        if request.scraper_type in ['rss', 'both']:
            rss_scraper = RSSScraper()
            scrape_all = require_callable(
                rss_scraper,
                "scrape_all",
                "MISSING_SCRAPER_METHOD",
                "Implement RSSScraper.scrape_all or remove the /scrape route call path.",
            )
            rss_articles = scrape_all(limit_per_source=request.limit_per_source)
            articles.extend(rss_articles)
        
        if request.scraper_type in ['html', 'both']:
            html_scraper = HTMLScraper()
            scrape_all = require_callable(
                html_scraper,
                "scrape_all",
                "MISSING_SCRAPER_METHOD",
                "Implement HTMLScraper.scrape_all or remove the /scrape route call path.",
            )
            html_articles = scrape_all(limit_per_source=request.limit_per_source)
            articles.extend(html_articles)

        # Best-effort persistence so freshly scraped stories show up immediately
        # in the dashboard instead of waiting for a separate warehouse job.
        bronze_saved_articles = 0
        persisted_articles = 0

        if articles:
            minio_client = MinIOClient()
            ingestion_service = IngestionService(minio_client)
            ingest_batch = require_callable(
                ingestion_service,
                "ingest_batch",
                "MISSING_INGESTION_METHOD",
                "Implement IngestionService.ingest_batch or remove the persistence step from /scrape.",
            )
            ingest_stats = ingest_batch(articles, request.scraper_type)
            bronze_saved_articles = ingest_stats.get("saved_articles", 0)

            postgres_client = PostgresClient()
            if postgres_client.connect():
                insert_articles_batch = require_callable(
                    postgres_client,
                    "insert_articles_batch",
                    "MISSING_INGESTION_METHOD",
                    "Implement PostgresClient.insert_articles_batch or remove the persistence step from /scrape.",
                )
                persisted_articles = insert_articles_batch(articles)
                postgres_client.disconnect()
        
        return {
            "status": "success",
            "scraper_type": request.scraper_type,
            "total_articles": len(articles),
            "bronze_saved_articles": bronze_saved_articles,
            "persisted_articles": persisted_articles,
            "articles": articles,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise structured_http_exception(
            500,
            "SCRAPING_FAILED",
            "Scraping request failed",
            "Check scraper configuration, network access, and source URLs.",
            details={"exception": e.__class__.__name__},
        )
