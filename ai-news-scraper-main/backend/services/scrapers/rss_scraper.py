"""
RSS Scraper Module
Scrapes articles from RSS feeds (structured feeds with title, link, summary, date)
"""
import feedparser
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

RSS_SOURCES = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
}

class RSSScraper:
    """Scrapes articles from RSS feeds and returns Bronze-layer article objects"""
    
    def __init__(self):
        self.sources = RSS_SOURCES
        logger.info(f"RSSScraper initialized with {len(self.sources)} sources")

    def _parse_entry_datetime(self, entry) -> datetime:
        """Parse feed entry datetime and fall back to now when unavailable."""
        for field in ("published_parsed", "updated_parsed"):
            parsed = entry.get(field)
            if parsed:
                return datetime(*parsed[:6], tzinfo=timezone.utc)

        for field in ("published", "updated"):
            value = entry.get(field)
            if value:
                try:
                    cleaned = value.replace("Z", "+00:00")
                    parsed = datetime.fromisoformat(cleaned)
                    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                except Exception:
                    continue

        return datetime.now(timezone.utc)
    
    def fetch_articles(self, source_name: str, feed_url: str, limit: int = 5) -> List[Dict]:
        """
        Fetch articles from an RSS feed.
        
        Args:
            source_name: Friendly name of the RSS source
            feed_url: Full URL to the RSS feed
            limit: Maximum articles to fetch from this source
        
        Returns:
            List of Bronze-layer article dictionaries
        """
        logger.info(f"📰 Scraping RSS: {source_name}...")
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            sorted_entries = sorted(
                feed.entries,
                key=self._parse_entry_datetime,
                reverse=True
            )
            
            for entry in sorted_entries[:limit]:
                article_id = hashlib.md5(entry.link.encode()).hexdigest()
                published_datetime = self._parse_entry_datetime(entry)
                article = {
                    "article_id": article_id,
                    "title": entry.get("title", "No title"),
                    "content": entry.get("summary", ""),
                    "url": entry.link,
                    "source": source_name,
                    "source_type": "rss",
                    "author": entry.get("author", "Unknown"),
                    "published_date": published_datetime.isoformat().replace("+00:00", "Z"),
                    "description": entry.get("summary", "")[:500],
                    "keywords": "",
                    "raw_html": False,
                    "scraped_at": datetime.utcnow().isoformat() + "Z"
                }
                articles.append(article)
            
            logger.info(f"   ✅ {len(articles)} articles fetched from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"   ❌ Error scraping {source_name}: {e}")
            return []
    
    def scrape_all(self, limit_per_source: int = 5) -> List[Dict]:
        """
        Scrape all configured RSS sources.
        
        Args:
            limit_per_source: Max articles per source
        
        Returns:
            List of all Bronze articles from all RSS sources
        """
        logger.info("\n" + "="*60)
        logger.info("🚀 RSS SCRAPING STARTED")
        logger.info("="*60)
        
        all_articles = []
        
        for source_name, feed_url in self.sources.items():
            articles = self.fetch_articles(source_name, feed_url, limit_per_source)
            all_articles.extend(articles)
        
        logger.info(f"\n🏁 RSS SCRAPING COMPLETE: {len(all_articles)} articles total")
        logger.info("="*60 + "\n")
        
        return all_articles
