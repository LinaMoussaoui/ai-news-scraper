"""Shared request/response schemas for backend routes."""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class ArticlePayload(BaseModel):
    article_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    published_date: str = Field(min_length=1)
    content: Optional[str] = None
    clean_content: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    detected_language: Optional[str] = None
    read_count: int = 0


class ScrapingRequest(BaseModel):
    scraper_type: Literal["rss", "html", "both"]
    limit_per_source: int = Field(default=5, ge=1, le=100)


class IngestRequest(BaseModel):
    articles: List[ArticlePayload] = Field(min_length=1)
    source_type: str = Field(default="mixed", min_length=1)