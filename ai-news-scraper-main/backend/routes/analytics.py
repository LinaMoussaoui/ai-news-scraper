"""Analytics endpoints (Gold layer)"""
from datetime import datetime
import logging

from fastapi import APIRouter, Query

from backend.utils.api_errors import structured_http_exception, require_callable
from backend.utils.schemas import ArticlePayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/generate")
async def generate_analytics_api(articles: list[ArticlePayload], days: int = Query(default=7, ge=1, le=30)):
    """Generate analytics from recent articles."""
    if not articles:
        raise structured_http_exception(
            422,
            "EMPTY_ARTICLE_LIST",
            "No articles were provided for analytics generation",
            "Send a non-empty list of cleaned/silver articles.",
        )
    try:
        from backend.services.analytics.trends import AnalyticsService
        from backend.utils.postgres_client import PostgresClient
        
        generate_full_analytics = require_callable(
            AnalyticsService,
            "generate_full_analytics",
            "MISSING_ANALYTICS_METHOD",
            "Implement AnalyticsService.generate_full_analytics or remove the /analytics/generate route.",
        )

        # Best-effort persistence so test payloads and ad-hoc analytics inputs
        # can appear on refresh in the dashboard.
        postgres_client = PostgresClient()
        persisted_count = 0
        if postgres_client.connect():
            insert_articles_batch = require_callable(
                postgres_client,
                "insert_articles_batch",
                "MISSING_INGESTION_METHOD",
                "Implement PostgresClient.insert_articles_batch or remove the persistence step from /analytics/generate.",
            )
            persisted_count = insert_articles_batch([article.model_dump() for article in articles])
            postgres_client.disconnect()

        analytics = generate_full_analytics([article.model_dump() for article in articles], days=days)
        return {
            "status": "success",
            "persisted_articles": persisted_count,
            "analytics": analytics,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Analytics generation failed: {e}")
        raise structured_http_exception(
            500,
            "ANALYTICS_GENERATION_FAILED",
            "Analytics generation failed",
            "Check the AnalyticsService implementation and the input article payloads.",
            details={"exception": e.__class__.__name__},
        )

@router.get("/trends")
async def get_trends(days: int = Query(default=7, ge=1, le=30)):
    """Get current trends from PostgreSQL."""
    try:
        from backend.utils.postgres_client import PostgresClient
        
        postgres_client = PostgresClient()
        if not postgres_client.connect():
            raise structured_http_exception(
                503,
                "POSTGRES_UNAVAILABLE",
                "PostgreSQL connection failed",
                "Ensure the Postgres container is running and the credentials match the environment settings.",
            )
        
        get_articles_per_day = require_callable(
            postgres_client,
            "get_articles_per_day",
            "MISSING_ANALYTICS_METHOD",
            "Implement PostgresClient.get_articles_per_day or remove the /analytics/trends route.",
        )
        get_articles_per_source = require_callable(
            postgres_client,
            "get_articles_per_source",
            "MISSING_ANALYTICS_METHOD",
            "Implement PostgresClient.get_articles_per_source or remove the /analytics/trends route.",
        )
        get_articles_per_category = require_callable(
            postgres_client,
            "get_articles_per_category",
            "MISSING_ANALYTICS_METHOD",
            "Implement PostgresClient.get_articles_per_category or remove the /analytics/trends route.",
        )
        get_keyword_trends = require_callable(
            postgres_client,
            "get_keyword_trends",
            "MISSING_ANALYTICS_METHOD",
            "Implement PostgresClient.get_keyword_trends or remove the /analytics/trends route.",
        )

        trends = get_articles_per_day(days=days)
        sources = get_articles_per_source(days=days)
        categories = get_articles_per_category(days=days)
        keywords = get_keyword_trends(limit=15, days=days)
        postgres_client.disconnect()

        return {
            "status": "success",
            "window_days": days,
            "trends": trends,
            "sources": sources,
            "categories": categories,
            "keywords": keywords,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error fetching analytics: {e}")
        raise structured_http_exception(
            500,
            "ANALYTICS_QUERY_FAILED",
            "Unable to fetch analytics from PostgreSQL",
            "Check the Postgres connection and verify all analytics methods exist on PostgresClient.",
            details={"exception": e.__class__.__name__},
        )

@router.get("/articles")
async def get_recent_articles(limit: int = Query(default=200, ge=1, le=1000), days: int | None = Query(default=None, ge=1, le=30)):
    """Get most recent articles from Gold layer, optionally filtered by days."""
    try:
        from backend.utils.postgres_client import PostgresClient
        
        postgres_client = PostgresClient()
        if not postgres_client.connect():
            raise structured_http_exception(
                503,
                "POSTGRES_UNAVAILABLE",
                "PostgreSQL connection failed",
                "Ensure the Postgres container is running and the credentials match the environment settings.",
            )
        
        get_recent_articles = require_callable(
            postgres_client,
            "get_recent_articles",
            "MISSING_ANALYTICS_METHOD",
            "Implement PostgresClient.get_recent_articles or remove the /analytics/articles route.",
        )
        articles = get_recent_articles(limit=limit, days=days)
        postgres_client.disconnect()
        
        return {
            "status": "success",
            "count": len(articles),
            "articles": articles,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Error fetching recent articles: {e}")
        raise structured_http_exception(
            500,
            "RECENT_ARTICLES_QUERY_FAILED",
            "Unable to fetch recent analytics articles",
            "Check the Postgres connection and verify PostgresClient.get_recent_articles exists.",
            details={"exception": e.__class__.__name__},
        )
