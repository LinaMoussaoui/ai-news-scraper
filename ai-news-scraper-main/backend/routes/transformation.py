"""Transformation endpoints (Silver layer)"""
from datetime import datetime
import logging

from fastapi import APIRouter

from backend.utils.api_errors import structured_http_exception, require_callable
from backend.utils.schemas import ArticlePayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transform", tags=["transformation"])

@router.post("/clean")
async def clean_articles(articles: list[ArticlePayload]):
    """Clean Bronze articles to Silver"""
    if not articles:
        raise structured_http_exception(
            422,
            "EMPTY_ARTICLE_LIST",
            "No articles were provided for cleaning",
            "Send a non-empty list of Bronze articles with the required fields.",
        )
    try:
        from backend.services.transformations.clean_html import TextCleaner
        
        cleaner = TextCleaner()
        cleaned = []
        
        process_article = require_callable(
            cleaner,
            "process_article",
            "MISSING_TRANSFORMATION_METHOD",
            "Implement TextCleaner.process_article or remove the /transform/clean route.",
        )
        validate_silver = require_callable(
            cleaner,
            "validate_silver",
            "MISSING_TRANSFORMATION_METHOD",
            "Implement TextCleaner.validate_silver or remove the /transform/clean route.",
        )

        for article in articles:
            silver = process_article(article.model_dump())
            is_valid, _ = validate_silver(silver)
            if is_valid:
                cleaned.append(silver)
        
        return {
            "status": "success",
            "input_count": len(articles),
            "output_count": len(cleaned),
            "articles": cleaned,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Cleaning failed: {e}")
        raise structured_http_exception(
            500,
            "TRANSFORMATION_CLEAN_FAILED",
            "Cleaning request failed",
            "Check the input article schema and the TextCleaner implementation.",
            details={"exception": e.__class__.__name__},
        )

@router.post("/filter-language")
async def filter_language_articles(articles: list[ArticlePayload], target_languages: list[str] = ['en']):
    """Filter articles by language"""
    if not articles:
        raise structured_http_exception(
            422,
            "EMPTY_ARTICLE_LIST",
            "No articles were provided for language filtering",
            "Send a non-empty list of cleaned articles with detected_language or text fields.",
        )
    try:
        from backend.services.transformations.detect_language import LanguageDetector
        
        detector = LanguageDetector(target_languages)
        filter_batch = require_callable(
            detector,
            "filter_batch",
            "MISSING_TRANSFORMATION_METHOD",
            "Implement LanguageDetector.filter_batch or remove the /transform/filter-language route.",
        )
        kept, rejected = filter_batch([article.model_dump() for article in articles])
        
        return {
            "status": "success",
            "kept_count": len(kept),
            "rejected_count": len(rejected),
            "kept_articles": kept,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"❌ Language filtering failed: {e}")
        raise structured_http_exception(
            500,
            "TRANSFORMATION_FILTER_FAILED",
            "Language filtering request failed",
            "Check the LanguageDetector implementation and the article payload fields.",
            details={"exception": e.__class__.__name__},
        )
