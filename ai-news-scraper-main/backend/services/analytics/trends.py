"""
Gold Layer Analytics Services
Computes trends, top subjects, and analytics from Silver articles
"""
from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime, timedelta, timezone
import logging
import re

# Minimal stopword set to filter obvious non-tool tokens
STOPWORDS = set([
    'the','and','for','with','that','this','from','are','was','were','have','has','had',
    'will','can','use','using','used','new','usecase','model','models','training','data'
])

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Generates analytics from Silver articles for Gold layer"""

    @staticmethod
    def _parse_article_datetime(value: str) -> datetime:
        """Parse an article datetime string and fall back to the epoch."""
        if not value:
            return datetime.min.replace(tzinfo=timezone.utc)

        try:
            cleaned = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    @staticmethod
    def _filter_recent_articles(silver_articles: List[Dict], days: int) -> List[Dict]:
        """Keep only articles inside the requested recent window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent_articles = []

        for article in silver_articles:
            published_date = article.get("published_date") or article.get("scraped_at")
            article_datetime = AnalyticsService._parse_article_datetime(published_date)
            if article_datetime >= cutoff:
                recent_articles.append(article)

        recent_articles.sort(
            key=lambda article: AnalyticsService._parse_article_datetime(
                article.get("published_date") or article.get("scraped_at")
            ),
            reverse=True
        )
        return recent_articles
    
    @staticmethod
    def compute_trends(silver_articles: List[Dict], days: int = 7) -> Dict:
        """
        Compute news trends from articles.
        
        Args:
            silver_articles: List of Silver articles
            days: Number of days to analyze
        
        Returns:
            Dictionary with trend statistics
        """
        logger.info("📈 Computing news trends...")

        recent_articles = AnalyticsService._filter_recent_articles(silver_articles, days)
        
        trends = {
            "articles_per_day": {},
            "articles_per_source": {},
            "articles_per_category": {},
            "total_articles": len(recent_articles),
            "date_range_days": days
        }
        
        # Count by day
        for article in recent_articles:
            pub_date = article.get("published_date", "")
            if pub_date:
                date_only = pub_date.split("T")[0]
                trends["articles_per_day"][date_only] = trends["articles_per_day"].get(date_only, 0) + 1

        source_counts = Counter(article.get("source", "Unknown") for article in recent_articles)
        category_counts = Counter(article.get("category", "General") for article in recent_articles)

        trends["articles_per_source"] = [
            {"source": source, "count": count}
            for source, count in source_counts.most_common()
        ]
        trends["articles_per_category"] = [
            {"category": category, "count": count}
            for category, count in category_counts.most_common()
        ]
        
        logger.info(f"   ✅ Trends computed: {len(trends['articles_per_day'])} days tracked")
        return trends
    
    @staticmethod
    def compute_top_subjects(silver_articles: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Find top subjects/categories from articles.
        
        Args:
            silver_articles: List of Silver articles
            top_n: Number of top subjects to return
        
        Returns:
            List of top subjects with counts
        """
        logger.info("🎯 Computing top subjects...")
        
        categories = [article.get("category", "General") for article in silver_articles]
        category_counts = Counter(categories)
        
        top_subjects = [
            {"subject": category, "count": count}
            for category, count in category_counts.most_common(top_n)
        ]
        
        logger.info(f"   ✅ Top {len(top_subjects)} subjects identified")
        return top_subjects
    
    @staticmethod
    def compute_source_counts(silver_articles: List[Dict]) -> List[Dict]:
        """
        Count articles by source.
        
        Args:
            silver_articles: List of Silver articles
        
        Returns:
            List of source counts
        """
        logger.info("📊 Computing source counts...")
        
        sources = [article.get("source", "Unknown") for article in silver_articles]
        source_counts = Counter(sources)
        
        source_stats = [
            {"source": source, "count": count}
            for source, count in source_counts.most_common()
        ]
        
        logger.info(f"   ✅ {len(source_stats)} sources identified")
        return source_stats
    
    @staticmethod
    def compute_keyword_frequency(silver_articles: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        Extract and count most frequent keywords.
        
        Args:
            silver_articles: List of Silver articles
            top_n: Number of top keywords to return
        
        Returns:
            List of keywords with frequencies
        """
        logger.info("🔤 Computing keyword frequencies...")
        
        all_keywords = []
        
        for article in silver_articles:
            keywords = article.get("keywords", "")
            if keywords:
                # Split by comma and clean
                kw_list = [k.strip().lower() for k in keywords.split(",")]
                all_keywords.extend(kw_list)
        
        keyword_counts = Counter(all_keywords)
        top_keywords = [
            {"keyword": keyword, "count": count}
            for keyword, count in keyword_counts.most_common(top_n)
        ]
        
        logger.info(f"   ✅ {len(top_keywords)} top keywords identified")
        return top_keywords
    
    @staticmethod
    def compute_author_stats(silver_articles: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Get most prolific authors.
        
        Args:
            silver_articles: List of Silver articles
            top_n: Number of top authors to return
        
        Returns:
            List of authors with article counts
        """
        logger.info("✍️  Computing author statistics...")
        
        authors = [article.get("author", "Unknown") for article in silver_articles]
        author_counts = Counter(authors)
        
        top_authors = [
            {"author": author, "count": count}
            for author, count in author_counts.most_common(top_n)
        ]
        
        logger.info(f"   ✅ {len(top_authors)} top authors identified")
        return top_authors
    
    @staticmethod
    def compute_top_tools(silver_articles: List[Dict], top_n: int = 10, tools_keywords: Optional[Dict[str, List[str]]] = None) -> List[Dict]:
        """
        Detect and count mentioned AI tools in articles.

        If `tools_keywords` mapping is provided, use it (mapping of display name -> keyword list).
        Otherwise perform lightweight dynamic extraction from titles and content to avoid hardcoding.
        """
        logger.info("🛠️  Detecting mentioned tools...")

        tool_mentions = Counter()

        if tools_keywords:
            # Use provided mapping (backwards-compatible)
            for article in silver_articles:
                content = (article.get("clean_content", "") + " " + article.get("title", "")).lower()
                for tool, keywords in tools_keywords.items():
                    if any(kw in content for kw in keywords):
                        tool_mentions[tool] += 1
        else:
            # Dynamic extraction: look for CamelCase / ProperName tokens and API/GPT-like tokens
            name_pattern = re.compile(r"\b[A-Z][A-Za-z0-9+#\.\-]{2,}\b")
            api_pattern = re.compile(r"\b([A-Za-z0-9\-]{2,}?(?:api|API|Api|GPT|gpt|gpt-\d|gpt-\d\.\d|claude|gemini)\b)")

            for article in silver_articles:
                text = (article.get("clean_content", "") or "") + " " + (article.get("title", "") or "")
                # Find CamelCase/Proper nouns
                for match in name_pattern.findall(text):
                    token = match.strip()
                    if token.lower() in STOPWORDS:
                        continue
                    # ignore very short/obvious words
                    if len(token) < 3:
                        continue
                    tool_mentions[token] += 1

                # Find api/gpt-like tokens
                for match in api_pattern.findall(text):
                    token = match[0] if isinstance(match, tuple) else match
                    token = token.strip()
                    if token and token.lower() not in STOPWORDS:
                        tool_mentions[token] += 1

        # Normalize and return top N
        top_tools = [ {"name": name, "mentions": count} for name, count in tool_mentions.most_common(top_n) ]
        logger.info(f"   ✅ {len(top_tools)} tools identified")
        return top_tools

    @staticmethod
    def generate_full_analytics(silver_articles: List[Dict], days: int = 7) -> Dict:
        """
        Generate comprehensive analytics report.
        
        Args:
            silver_articles: List of Silver articles
        
        Returns:
            Dictionary with all analytics
        """
        logger.info("\n" + "="*60)
        logger.info("📊 GENERATING COMPREHENSIVE ANALYTICS")
        logger.info("="*60)
        
        recent_articles = AnalyticsService._filter_recent_articles(silver_articles, days)

        analytics = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_articles": len(recent_articles),
            "window_days": days,
            "trends": AnalyticsService.compute_trends(recent_articles, days=days),
            "top_subjects": AnalyticsService.compute_top_subjects(recent_articles),
            "source_distribution": AnalyticsService.compute_source_counts(recent_articles),
            "top_keywords": AnalyticsService.compute_keyword_frequency(recent_articles),
            "top_authors": AnalyticsService.compute_author_stats(recent_articles),
            # Tools/frameworks section removed — keep payload smaller
            "language_distribution": AnalyticsService.compute_language_distribution(recent_articles)
        }
        
        logger.info(f"\n✅ Analytics generated for {len(recent_articles)} recent articles")
        logger.info("="*60 + "\n")
        
        return analytics
    
    @staticmethod
    def compute_language_distribution(silver_articles: List[Dict]) -> List[Dict]:
        """Count articles by language"""
        languages = [article.get("detected_language", "unknown") for article in silver_articles]
        lang_counts = Counter(languages)
        
        return [
            {"language": lang, "count": count}
            for lang, count in lang_counts.most_common()
        ]
