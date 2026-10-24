"""
HTML Scraper Module
Scrapes articles from websites that don't expose RSS or require full HTML parsing
"""
import requests
from bs4 import BeautifulSoup
import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import logging
import re
import time

STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was', 'were',
    'have', 'has', 'had', 'into', 'your', 'about', 'after', 'before', 'over',
    'under', 'with', 'the', 'a', 'an', 'to', 'of', 'in', 'on', 'by', 'or', 'as'
}

logger = logging.getLogger(__name__)

HTML_SOURCES = {
    "BAIR Blog": {
        "base_url": "https://bair.berkeley.edu",
        "articles_list": "https://bair.berkeley.edu/blog/",
        "article_selector": ".post",
        "title_selector": "h1",
        "content_selector": ".post-content",
        "link_selector": "a[href*='/blog/']"
    },
    "Distill Pub": {
        "base_url": "https://distill.pub",
        "articles_list": "https://distill.pub/",
        "article_selector": "article",
        "title_selector": "h1",
        "content_selector": ".content",
        "link_selector": "a[href*='/']"
    }
}

class HTMLScraper:
    """Scrapes articles from HTML pages and returns Bronze-layer article objects"""
    
    def __init__(self, output_dir: str = "data/bronze/html"):
        self.sources = HTML_SOURCES
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        logger.info(f"HTMLScraper initialized with {len(self.sources)} sources")

    def _parse_datetime(self, value: str) -> datetime:
        """Parse a published date into UTC for sorting."""
        if not value:
            return datetime.now(timezone.utc)

        try:
            cleaned = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)
    
    def get_article_links(self, source_name: str, config: dict, limit: int = 5) -> List[str]:
        """Extract article URLs from listing page"""
        logger.info(f"🔍 Extracting links from {source_name}...")
        
        try:
            response = self.session.get(config["articles_list"], timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            links = []
            link_selector = config.get("link_selector", "a")
            
            for a in soup.select(link_selector):
                href = a.get("href", "")
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                
                full_url = urljoin(config["base_url"], href)
                
                if self._is_article_link(full_url, source_name) and full_url not in links:
                    links.append(full_url)
                
                if len(links) >= limit * 2:
                    break
            
            unique_links = [l for l in links if not self._is_homepage(l, config["base_url"])][:limit]
            logger.info(f"   ✅ {len(unique_links)} links found")
            return unique_links
            
        except Exception as e:
            logger.error(f"   ❌ Error extracting links: {e}")
            return []
    
    def _is_article_link(self, url: str, source_name: str) -> bool:
        """Determine if URL is an article (not category/tag/etc)"""
        exclude = ["category", "tag", "author", "page", "search", "feed", "rss", "xml", "json", "wp-", "admin", "login", "signup", "contact", "about", "privacy"]
        url_lower = url.lower()
        
        if any(p in url_lower for p in exclude):
            return False
        
        include = ["blog", "post", "article", "news", "story"]
        return any(p in url_lower for p in include) or len(url.split("/")) > 4
    
    def _is_homepage(self, url: str, base_url: str) -> bool:
        """Check if URL is homepage"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        return parsed_url.path in ["", "/", "/index.html", "/index.php"]
    
    def extract_main_content(self, soup: BeautifulSoup, config: dict) -> str:
        """Intelligently extract main article content"""
        content_selector = config.get("content_selector", "article, .post, .content, main")
        content_tag = soup.select_one(content_selector)
        
        if content_tag:
            return str(content_tag)
        
        # Fallback: find largest text div
        candidates = soup.find_all(["div", "article", "section", "main"])
        best_candidate = None
        best_text_len = 0
        
        for candidate in candidates:
            text = candidate.get_text(strip=True)
            text_len = len(text)
            if 500 < text_len < 50000 and text_len > best_text_len and not self._is_boilerplate(candidate):
                best_candidate = candidate
                best_text_len = text_len
        
        if best_candidate:
            return str(best_candidate)
        
        body = soup.find("body")
        return str(body) if body else str(soup)
    
    def _is_boilerplate(self, tag) -> bool:
        """Detect if tag is nav/footer/header (non-content)"""
        boilerplate_classes = ["nav", "menu", "sidebar", "footer", "header", "navigation", "navbar", "breadcrumb"]
        classes = tag.get("class", [])
        return any(any(bp in cls.lower() for bp in boilerplate_classes) for cls in classes)
    
    def _extract_title(self, soup: BeautifulSoup, config: dict) -> str:
        """Extract article title"""
        title_tag = soup.select_one(config.get("title_selector", "h1"))
        if title_tag:
            text = title_tag.get_text(strip=True)
            if 3 < len(text) < 500:
                return text
        
        for selector in ["h1.entry-title", ".post-title", ".article-title", "title"]:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                if 3 < len(text) < 500:
                    return text
        
        return "No title found"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        selectors = ['[rel="author"]', '.author', '.byline', '.writer', '.post-author', '.article-author']
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                return elem.get_text(strip=True)
        return "Unknown"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        selectors = ['time', '[datetime]', '.published', '.date', '.post-date', '.article-date']
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                if elem.get("datetime"):
                    return elem["datetime"]
                text = elem.get_text(strip=True)
                if text:
                    return text
        return datetime.utcnow().isoformat() + "Z"
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"][:500]
        meta = soup.find("meta", attrs={"property": "og:description"})
        if meta and meta.get("content"):
            return meta["content"][:500]
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta = soup.find("meta", attrs={"name": "keywords"})
        if meta and meta.get("content"):
            return meta["content"]
        return ""
    
    def _detect_category(self, text: str) -> str:
        """Derive a data-driven topic label from article text."""
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", text or "")
        normalized = [token.lower() for token in tokens if token.lower() not in STOPWORDS]

        if not normalized:
            return "Uncategorized"

        # Prefer the most common meaningful token, preserving the original surface form when possible.
        counts = Counter(normalized)
        top_token, _ = counts.most_common(1)[0]
        if top_token:
            return top_token.replace("-", " ").title()
        return "Uncategorized"
    
    def scrape_article(self, url: str, source_name: str, config: dict) -> Optional[Dict]:
        """Scrape and parse a single article"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove unwanted elements
            for unwanted in soup.select("script, style, nav, footer, header, .nav, .sidebar, .menu, iframe, .advertisement"):
                unwanted.decompose()
            
            title = self._extract_title(soup, config)
            raw_html = self.extract_main_content(soup, config)
            author = self._extract_author(soup)
            published_date = self._extract_date(soup)
            description = self._extract_meta_description(soup)
            keywords = self._extract_keywords(soup)
            
            article_id = hashlib.md5(url.encode()).hexdigest()
            article = {
                "article_id": article_id,
                "title": title,
                "content": raw_html,
                "raw_html": True,
                "url": url,
                "source": source_name,
                "source_type": "html",
                "author": author,
                "published_date": published_date,
                "description": description,
                "keywords": keywords,
                "category": self._detect_category(" ".join([title, description, keywords])),
                "scraped_at": datetime.utcnow().isoformat() + "Z"
            }
            return article
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error scraping {url[:60]}...: {e}")
            return None
    
    def scrape_source(self, source_name: str, config: dict, limit: int = 3) -> List[Dict]:
        """Scrape all articles from a single HTML source"""
        logger.info(f"\n📌 Source: {source_name}")
        
        links = self.get_article_links(source_name, config, limit)
        articles = []
        
        for idx, url in enumerate(links):
            logger.info(f"   📄 [{idx+1}/{len(links)}] Scraping...")
            article = self.scrape_article(url, source_name, config)
            
            if article:
                logger.info(f"      ✅ {article['title'][:50]}...")
                articles.append(article)
            else:
                logger.warning(f"      ❌ Failed to scrape")
            
            time.sleep(1)  # Respectful delay

        articles.sort(
            key=lambda article: self._parse_datetime(article.get("published_date", "")),
            reverse=True
        )
        
        return articles
    
    def scrape_all(self, limit_per_source: int = 3) -> List[Dict]:
        """
        Scrape all configured HTML sources.
        
        Args:
            limit_per_source: Max articles per source
        
        Returns:
            List of all Bronze articles from all HTML sources
        """
        logger.info("\n" + "="*60)
        logger.info("🌐 HTML SCRAPING STARTED")
        logger.info("="*60)
        
        all_articles = []
        
        for source_name, config in self.sources.items():
            articles = self.scrape_source(source_name, config, limit_per_source)
            all_articles.extend(articles)
        
        logger.info(f"\n🏁 HTML SCRAPING COMPLETE: {len(all_articles)} articles total")
        logger.info("="*60 + "\n")
        
        return all_articles
