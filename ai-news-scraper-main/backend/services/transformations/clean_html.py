"""
Text Cleaning and Normalization Service (Silver Layer)
Transforms Bronze articles into cleaned Silver articles
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, Tuple, Optional
import html
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """Cleans and normalizes article content from Bronze to Silver layer"""
    
    def __init__(self, min_word_count: int = 20):
        """
        Initialize text cleaner.
        
        Args:
            min_word_count: Minimum words required for valid article
        """
        self.min_word_count = min_word_count
        logger.info(f"TextCleaner initialized (min_words: {min_word_count})")
    
    def clean_html(self, raw_html: str) -> str:
        """Remove all HTML tags and extract text"""
        if not raw_html:
            return ""
        
        # Check if it's actually HTML
        if not raw_html.strip().startswith("<"):
            return raw_html
        
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                tag.decompose()
            
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"Error parsing HTML: {e}")
            # Fallback: regex-based cleaning
            text = re.sub(r'<[^>]+>', ' ', raw_html)
            text = html.unescape(text)
            return re.sub(r'\s+', ' ', text).strip()
    
    def normalize_text(self, text: str) -> str:
        """Normalize text: remove special chars, normalize whitespace"""
        if not text:
            return ""
        
        # Remove special characters (keep alphanumeric, spaces, punctuation)
        text = re.sub(r'[^\w\s\.\,\!\?\-\'\"]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate text (newsletters, cookie policies, etc.)"""
        patterns = [
            r'subscribe to our newsletter',
            r'click here to subscribe',
            r'cookie policy',
            r'privacy policy',
            r'terms of service',
            r'all rights reserved',
            r'© 20\d{2}'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_article_text(self, html_content: str) -> str:
        """Intelligently extract main article content from HTML"""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", 
                         "iframe", "noscript", "meta", "link", "button", "form"]):
            tag.decompose()
        
        # Try common content selectors
        content_selectors = [
            "article", ".post-content", ".entry-content", ".article-content",
            ".post-body", ".content", "main", ".blog-post", ".post"
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Find the div with the most text
            candidates = soup.find_all(["div", "section"])
            best = None
            best_len = 0
            
            for candidate in candidates:
                text = candidate.get_text(strip=True)
                if 300 < len(text) < 50000 and len(text) > best_len:
                    best = candidate
                    best_len = len(text)
            
            main_content = best if best else soup
        
        return str(main_content)
    
    def extract_metadata(self, text: str) -> Dict:
        """Extract metadata from text"""
        words = text.split()
        word_count = len(words)
        
        return {
            "word_count": word_count,
            "char_count": len(text),
            "is_valid": word_count >= self.min_word_count
        }
    
    def process_article(self, bronze_article: Dict) -> Dict:
        """
        Transform a Bronze article into a Silver article.
        
        Args:
            bronze_article: Raw article from Bronze layer
        
        Returns:
            Cleaned Silver article
        """
        raw_content = bronze_article.get("content", "")
        
        # Extract content intelligently if it's raw HTML
        if bronze_article.get("raw_html", False):
            content_html = self.extract_article_text(raw_content)
        else:
            content_html = raw_content
        
        # Clean HTML and normalize text
        clean_text = self.clean_html(content_html)
        clean_text = self.normalize_text(clean_text)
        clean_text = self.remove_boilerplate(clean_text)
        
        # Extract metadata
        metadata = self.extract_metadata(clean_text)
        
        silver_article = {
            "article_id": bronze_article.get("article_id", ""),
            "title": self.normalize_text(bronze_article.get("title", "")),
            "clean_content": clean_text,
            "url": bronze_article.get("url", ""),
            "source": bronze_article.get("source", ""),
            "source_type": bronze_article.get("source_type", "unknown"),
            "author": bronze_article.get("author", "Unknown"),
            "published_date": bronze_article.get("published_date", ""),
            "description": bronze_article.get("description", ""),
            "keywords": bronze_article.get("keywords", ""),
            "category": bronze_article.get("category", "General"),
            "word_count": metadata["word_count"],
            "is_valid": metadata["is_valid"],
            "processed_at": self._get_timestamp()
        }
        
        return silver_article
    
    def validate_silver(self, silver_article: Dict) -> Tuple[bool, str]:
        """
        Validate a Silver article.
        
        Args:
            silver_article: Article to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not silver_article.get("clean_content"):
            return False, "Empty content"
        
        if not silver_article["is_valid"]:
            return False, f"Too short ({silver_article['word_count']} words)"
        
        if not silver_article.get("title"):
            return False, "Missing title"
        
        if len(silver_article["title"]) < 3:
            return False, "Title too short"
        
        return True, "Valid"
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

