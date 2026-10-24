"""
Language Detection and Filtering Service (Silver Layer)
Detects article language and filters by target languages
"""
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Detects language and filters articles by target languages"""
    
    def __init__(self, target_languages: List[str] = None):
        """
        Initialize language detector.
        
        Args:
            target_languages: List of target language codes (e.g., ['en', 'fr'])
        """
        self.target_languages = target_languages or ['en', 'fr']
        logger.info(f"LanguageDetector initialized (targets: {self.target_languages})")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not text or len(text.strip()) < 20:
            return "unknown", 0.0
        
        try:
            sample = text[:500]
            lang = detect(sample)
            # Confidence is higher with more text
            confidence = 0.95 if len(sample) > 200 else 0.7 if len(sample) > 100 else 0.5
            return lang, confidence
        except LangDetectException:
            return "unknown", 0.0
        except Exception as e:
            logger.warning(f"Error detecting language: {e}")
            return "unknown", 0.0
    
    def is_target_language(self, text: str) -> Tuple[bool, str]:
        """
        Check if text is in a target language.
        
        Args:
            text: Text to check
        
        Returns:
            Tuple of (is_target, detected_language)
        """
        lang, confidence = self.detect_language(text)
        is_accepted = lang in self.target_languages and confidence > 0.5
        return is_accepted, lang
    
    def filter_article(self, silver_article: Dict) -> Tuple[bool, Dict]:
        """
        Filter article by language.
        
        Args:
            silver_article: Silver article to check
        
        Returns:
            Tuple of (is_accepted, enriched_article)
        """
        text_to_analyze = silver_article.get("title", "") + " " + silver_article.get("clean_content", "")
        is_accepted, detected_lang = self.is_target_language(text_to_analyze)
        
        # Add language info to article
        silver_article["detected_language"] = detected_lang
        silver_article["language_accepted"] = is_accepted
        
        return is_accepted, silver_article
    
    def filter_batch(self, silver_articles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter batch of articles by language.
        
        Args:
            silver_articles: List of Silver articles
        
        Returns:
            Tuple of (kept_articles, rejected_articles)
        """
        kept = []
        rejected = []
        
        for article in silver_articles:
            is_accepted, enriched = self.filter_article(article)
            if is_accepted:
                kept.append(enriched)
            else:
                rejected.append(enriched)
        
        logger.info(f"🌍 Language filtering: {len(kept)} kept, {len(rejected)} rejected")
        return kept, rejected

