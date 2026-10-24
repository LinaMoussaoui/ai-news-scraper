"""
PostgreSQL Client Utility
Handles all PostgreSQL database operations for the data warehouse (Gold layer)
"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PostgresClient:
    """PostgreSQL data warehouse client for Gold layer storage and analytics"""
    
    def __init__(self, host: str = None, port: int = None, 
                 user: str = None, password: str = None, 
                 database: str = None):
        """
        Initialize PostgreSQL client.
        
        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            user: Database user
            password: Database password
            database: Database name
        """
        # Load from settings if not provided
        if host is None or port is None or user is None or password is None or database is None:
            from backend.config.settings import (
                POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DATABASE
            )
            host = host or POSTGRES_HOST
            port = port or POSTGRES_PORT
            user = user or POSTGRES_USER
            password = password or POSTGRES_PASSWORD
            database = database or POSTGRES_DATABASE
        
        self.connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }
        self.conn = None
        self.host = host
        self.port = port
        logger.info(f"PostgresClient configured: {host}:{port}/{database}")
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info(f"✅ Connected to PostgreSQL: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from PostgreSQL")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            
            logger.info(f"✅ PostgreSQL connection test passed: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection test failed: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create required database tables for Gold layer"""
        try:
            with self.conn.cursor() as cur:
                # Articles table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        article_id VARCHAR(255) UNIQUE NOT NULL,
                        title VARCHAR(500) NOT NULL,
                        content TEXT,
                        url VARCHAR(1000),
                        source VARCHAR(255),
                        source_type VARCHAR(50),
                        author VARCHAR(255),
                        published_date TIMESTAMP,
                        description TEXT,
                        keywords VARCHAR(500),
                        category VARCHAR(100),
                        language VARCHAR(10),
                        word_count INT,
                        is_valid BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Analytics: articles per day
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles_per_day (
                        date DATE PRIMARY KEY,
                        count INT,
                        sources JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Analytics: articles per source
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles_per_source (
                        source VARCHAR(255) PRIMARY KEY,
                        count INT,
                        last_article TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Analytics: articles per category
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles_per_category (
                        category VARCHAR(100) PRIMARY KEY,
                        count INT,
                        top_keywords VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Analytics: keyword trends
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS keyword_trends (
                        keyword VARCHAR(255) PRIMARY KEY,
                        count INT,
                        last_seen TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.conn.commit()
                logger.info("✅ All tables created successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def insert_article(self, article: Dict) -> Optional[int]:
        """
        Insert an article into the database.
        
        Args:
            article: Article dictionary
        
        Returns:
            Article ID if successful, None otherwise
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO articles (
                        article_id, title, content, url, source, source_type,
                        author, published_date, description, keywords, category, language, word_count, is_valid
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (article_id) DO NOTHING
                    RETURNING id
                """, (
                    article.get('article_id'),
                    article.get('title'),
                    article.get('clean_content', article.get('content')),
                    article.get('url'),
                    article.get('source'),
                    article.get('source_type'),
                    article.get('author'),
                    article.get('published_date'),
                    article.get('description'),
                    article.get('keywords'),
                    article.get('category'),
                    article.get('detected_language'),
                    article.get('word_count', 0),
                    article.get('is_valid', True)
                ))
                
                result = cur.fetchone()
                self.conn.commit()
                
                if result:
                    logger.info(f"   ✅ Article inserted: {article.get('title')[:50]}...")
                    return result[0]
                else:
                    logger.info(f"   ℹ️ Article already exists: {article.get('article_id')}")
                    return None
                    
        except Exception as e:
            logger.error(f"   ❌ Error inserting article: {e}")
            self.conn.rollback()
            return None
    
    def insert_articles_batch(self, articles: List[Dict]) -> int:
        """
        Insert multiple articles into the database.
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Number of articles inserted
        """
        inserted = 0
        for article in articles:
            result = self.insert_article(article)
            if result:
                inserted += 1
        
        logger.info(f"📊 {inserted}/{len(articles)} articles inserted into database")
        return inserted
    
    def get_articles_per_day(self, days: int = 7) -> List[Dict]:
        """Get article counts by day"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        DATE(published_date) as date,
                        COUNT(*) as count,
                        COUNT(DISTINCT source) as unique_sources
                    FROM articles
                    WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'
                    GROUP BY DATE(published_date)
                    ORDER BY date DESC
                """, (days,))
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching articles per day: {e}")
            return []
    
    def get_articles_per_source(self, days: int = None) -> List[Dict]:
        """Get article counts by source. Optionally limit to recent `days`."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if days:
                    cur.execute("""
                        SELECT 
                            source,
                            COUNT(*) as count,
                            MAX(published_date) as last_article
                        FROM articles
                        WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY source
                        ORDER BY count DESC
                    """, (days,))
                else:
                    cur.execute("""
                        SELECT 
                            source,
                            COUNT(*) as count,
                            MAX(published_date) as last_article
                        FROM articles
                        GROUP BY source
                        ORDER BY count DESC
                    """)
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching articles per source: {e}")
            return []
    
    def get_articles_per_category(self, days: int = None) -> List[Dict]:
        """Get article counts by category. Optionally limit to recent `days`."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if days:
                    cur.execute("""
                        SELECT 
                            category,
                            COUNT(*) as count
                        FROM articles
                        WHERE category IS NOT NULL AND published_date >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY category
                        ORDER BY count DESC
                    """, (days,))
                else:
                    cur.execute("""
                        SELECT 
                            category,
                            COUNT(*) as count
                        FROM articles
                        WHERE category IS NOT NULL
                        GROUP BY category
                        ORDER BY count DESC
                    """)
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching articles per category: {e}")
            return []

    def get_top_tools(self, days: int = None, limit: int = 10) -> List[Dict]:
        """Detect top mentioned tools within recent articles using AnalyticsService."""
        try:
            # Import locally to avoid top-level dependency cycles
            from backend.services.analytics.trends import AnalyticsService

            # Fetch recent articles' content and title
            params = ()
            query = "SELECT clean_content, title, published_date FROM articles"
            if days:
                query += " WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'"
                params = (days,)
            query += " ORDER BY published_date DESC LIMIT %s"
            params = params + (500,)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # First, count how many articles are in the requested window.
                count_query = "SELECT COUNT(*) FROM articles"
                count_params = ()
                if days:
                    count_query += " WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'"
                    count_params = (days,)
                cur.execute(count_query, count_params)
                total_in_window = cur.fetchone().get('count', 0)

                # If there are fewer than 200 articles in the window, skip tool detection.
                if total_in_window < 200:
                    logger.info(f"🔕 Skipping tool detection: only {total_in_window} articles (<200) in window")
                    return []

                cur.execute(query, params)
                rows = cur.fetchall()

            # Convert to expected silver article shape
            silver_articles = []
            for r in rows:
                silver_articles.append({
                    "title": r.get("title"),
                    "clean_content": r.get("clean_content") or "",
                    "published_date": r.get("published_date")
                })

            top_tools = AnalyticsService.compute_top_tools(silver_articles, top_n=limit)
            return top_tools
        except Exception as e:
            logger.error(f"❌ Error fetching top tools: {e}")
            return []

    def get_recent_articles(self, limit: int = 50, days: int = None) -> List[Dict]:
        """Get the most recent articles from the database, optionally filtered by days"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if days:
                    cur.execute("""
                        SELECT * FROM articles
                        WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'
                        ORDER BY published_date DESC, created_at DESC
                        LIMIT %s
                    """, (days, limit))
                else:
                    cur.execute("""
                        SELECT * FROM articles
                        ORDER BY published_date DESC, created_at DESC
                        LIMIT %s
                    """, (limit,))
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching recent articles: {e}")
            return []

    def get_keyword_trends(self, limit: int = 10, days: int | None = None) -> List[Dict]:
        """Get top keyword trends from the database, optionally limited to recent days."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if days:
                    # Combine recent mentions from articles with historical counts
                    # from keyword_trends so the list never goes empty when the
                    # latest batch has no new keyword hits.
                    cur.execute("""
                        WITH recent AS (
                            SELECT
                                lower(trim(kw)) AS keyword,
                                COUNT(*) AS recent_count,
                                MAX(published_date) AS recent_last_seen
                            FROM (
                                SELECT
                                    unnest(string_to_array(keywords, ',')) AS kw,
                                    published_date
                                FROM articles
                                WHERE keywords IS NOT NULL
                                  AND published_date >= CURRENT_DATE - INTERVAL '%s days'
                            ) s
                            WHERE trim(kw) <> ''
                            GROUP BY lower(trim(kw))
                        )
                        SELECT
                            COALESCE(r.keyword, kt.keyword) AS keyword,
                            COALESCE(r.recent_count, kt.count, 0) AS count,
                            COALESCE(r.recent_count, 0) AS recent_count,
                            COALESCE(kt.count, 0) AS historical_count,
                            COALESCE(r.recent_last_seen, kt.last_seen) AS last_seen,
                            (
                                COALESCE(r.recent_count, 0) * 20.0 +
                                COALESCE(kt.count, 0) * 0.5 +
                                CASE
                                    WHEN COALESCE(r.recent_last_seen, kt.last_seen) IS NULL THEN 0
                                    ELSE GREATEST(
                                        0,
                                        100.0 - (
                                            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - COALESCE(r.recent_last_seen, kt.last_seen))) / 3600.0
                                        ) * 4.0
                                    )
                                END
                            ) AS score
                        FROM recent r
                        FULL OUTER JOIN keyword_trends kt
                          ON kt.keyword = r.keyword
                        WHERE COALESCE(r.keyword, kt.keyword) IS NOT NULL
                        ORDER BY score DESC, historical_count DESC, last_seen DESC NULLS LAST, keyword ASC
                        LIMIT %s
                    """, (days, limit))
                else:
                    cur.execute("""
                        SELECT keyword, count, last_seen
                        FROM keyword_trends
                        ORDER BY count DESC
                        LIMIT %s
                    """, (limit,))

                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching keyword trends: {e}")
            return []
    
    def insert_articles_per_day(self, trends: Dict) -> int:
        """Insert articles per day analytics"""
        try:
            inserted = 0
            articles_per_day = trends.get("articles_per_day", {})
            
            with self.conn.cursor() as cur:
                for date_str, count in articles_per_day.items():
                    cur.execute("""
                        INSERT INTO articles_per_day (date, count, sources)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (date) DO UPDATE SET count = EXCLUDED.count
                    """, (date_str, count, '{}'))
                    inserted += 1
                
                self.conn.commit()
                logger.info(f"✅ Inserted {inserted} articles_per_day records")
            return inserted
        except Exception as e:
            logger.error(f"❌ Error inserting articles_per_day: {e}")
            self.conn.rollback()
            return 0
    
    def insert_articles_per_source(self, source_distribution: List[Dict]) -> int:
        """Insert articles per source analytics"""
        try:
            inserted = 0
            
            with self.conn.cursor() as cur:
                for source_data in source_distribution:
                    source = source_data.get("source", "Unknown")
                    count = source_data.get("count", 0)
                    
                    cur.execute("""
                        INSERT INTO articles_per_source (source, count, last_article)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (source) DO UPDATE SET count = EXCLUDED.count, updated_at = CURRENT_TIMESTAMP
                    """, (source, count))
                    inserted += 1
                
                self.conn.commit()
                logger.info(f"✅ Inserted {inserted} articles_per_source records")
            return inserted
        except Exception as e:
            logger.error(f"❌ Error inserting articles_per_source: {e}")
            self.conn.rollback()
            return 0
    
    def insert_articles_per_category(self, top_subjects: List[Dict]) -> int:
        """Insert articles per category analytics"""
        try:
            inserted = 0
            
            with self.conn.cursor() as cur:
                for subject_data in top_subjects:
                    category = subject_data.get("subject", subject_data.get("category", "General"))
                    count = subject_data.get("count", 0)
                    
                    cur.execute("""
                        INSERT INTO articles_per_category (category, count, top_keywords)
                        VALUES (%s, %s, '')
                        ON CONFLICT (category) DO UPDATE SET count = EXCLUDED.count, updated_at = CURRENT_TIMESTAMP
                    """, (category, count))
                    inserted += 1
                
                self.conn.commit()
                logger.info(f"✅ Inserted {inserted} articles_per_category records")
            return inserted
        except Exception as e:
            logger.error(f"❌ Error inserting articles_per_category: {e}")
            self.conn.rollback()
            return 0
    
    def insert_keyword_trends(self, top_keywords: List[Dict]) -> int:
        """Insert keyword trends analytics"""
        try:
            inserted = 0
            
            with self.conn.cursor() as cur:
                for keyword_data in top_keywords:
                    keyword = keyword_data.get("keyword", "")
                    count = keyword_data.get("count", 0)
                    
                    if keyword:  # Only insert non-empty keywords
                        # On conflict, increment the stored count to reflect
                        # repeated appearances across analytics runs and update
                        # the last_seen timestamp so recency can be evaluated.
                        cur.execute("""
                            INSERT INTO keyword_trends (keyword, count, last_seen)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (keyword) DO UPDATE
                            SET count = keyword_trends.count + EXCLUDED.count,
                                last_seen = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                        """, (keyword, count))
                        inserted += 1
                
                self.conn.commit()
                logger.info(f"✅ Inserted {inserted} keyword_trends records")
            return inserted
        except Exception as e:
            logger.error(f"❌ Error inserting keyword_trends: {e}")
            self.conn.rollback()
            return 0
