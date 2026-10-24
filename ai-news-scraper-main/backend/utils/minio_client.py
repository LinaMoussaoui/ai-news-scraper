"""
MinIO Client Utility
Handles all MinIO (S3-compatible) object storage operations for the data lake
"""
from minio import Minio
from minio.error import S3Error
import json
import io
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MinIOClient:
    """MinIO data lake client for Bronze, Silver, and Gold storage"""
    
    def __init__(self, endpoint: str = None, access_key: str = None, 
                 secret_key: str = None, secure: bool = None):
        """
        Initialize MinIO client.
        
        Args:
            endpoint: MinIO endpoint (host:port)
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Use HTTPS
        """
        # Load from settings if not provided
        if endpoint is None or access_key is None or secret_key is None or secure is None:
            from backend.config.settings import (
                MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
            )
            endpoint = endpoint or MINIO_ENDPOINT
            access_key = access_key or MINIO_ACCESS_KEY
            secret_key = secret_key or MINIO_SECRET_KEY
            secure = secure if secure is not None else MINIO_SECURE
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.endpoint = endpoint
        logger.info(f"MinIOClient initialized: {endpoint}")
    
    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"✅ Bucket '{bucket_name}' created")
            else:
                logger.info(f"📦 Bucket '{bucket_name}' already exists")
            return True
        except S3Error as e:
            logger.error(f"❌ Error creating bucket '{bucket_name}': {e}")
            return False
    
    def save_article(self, bucket_name: str, article: Dict, layer: str = "bronze") -> Optional[str]:
        """
        Save a single article to MinIO.
        
        Args:
            bucket_name: MinIO bucket name
            article: Article dictionary
            layer: Data layer (bronze, silver, gold)
        
        Returns:
            Object path if successful, None otherwise
        """
        try:
            date_str = datetime.utcnow().strftime("%Y/%m/%d")
            source_type = article.get("source_type", "unknown")
            object_path = f"{layer}/{source_type}/{date_str}/{article['article_id']}.json"
            
            json_data = json.dumps(article, ensure_ascii=False, indent=2)
            json_bytes = io.BytesIO(json_data.encode('utf-8'))
            
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_path,
                data=json_bytes,
                length=len(json_data.encode('utf-8')),
                content_type="application/json"
            )
            
            logger.info(f"   💾 MinIO: {object_path}")
            return object_path
            
        except S3Error as e:
            logger.error(f"   ❌ Error saving article: {e}")
            return None
    
    def save_articles_batch(self, bucket_name: str, articles: List[Dict], layer: str = "bronze") -> List[str]:
        """
        Save multiple articles to MinIO.
        
        Args:
            bucket_name: MinIO bucket name
            articles: List of article dictionaries
            layer: Data layer (bronze, silver, gold)
        
        Returns:
            List of saved object paths
        """
        saved_paths = []
        for article in articles:
            path = self.save_article(bucket_name, article, layer)
            if path:
                saved_paths.append(path)
        
        logger.info(f"📦 {len(saved_paths)} articles saved to '{layer}' layer")
        return saved_paths
    
    def list_articles(self, bucket_name: str, layer: str = "bronze", 
                     source_type: str = None, limit: int = 100) -> List[Dict]:
        """
        List articles in a bucket/layer.
        
        Args:
            bucket_name: MinIO bucket name
            layer: Data layer (bronze, silver, gold)
            source_type: Filter by source type (rss, html, etc.)
            limit: Max results
        
        Returns:
            List of object metadata
        """
        try:
            prefix = f"{layer}/"
            if source_type:
                prefix += f"{source_type}/"
            
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            articles = []
            
            for obj in objects:
                articles.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified
                })
            
            # Sort by last_modified descending (latest first)
            articles.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return articles[:limit]
            
        except S3Error as e:
            logger.error(f"❌ Error listing articles: {e}")
            return []
    
    def get_article(self, bucket_name: str, object_path: str) -> Optional[Dict]:
        """
        Retrieve a single article from MinIO.
        
        Args:
            bucket_name: MinIO bucket name
            object_path: Full path to object
        
        Returns:
            Parsed article dictionary or None
        """
        try:
            response = self.client.get_object(bucket_name, object_path)
            data = response.read()
            response.close()
            response.release_conn()
            return json.loads(data.decode('utf-8'))
            
        except S3Error as e:
            logger.error(f"❌ Error retrieving article: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test MinIO connection"""
        try:
            self.client.list_buckets()
            logger.info(f"✅ MinIO connection successful: {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"❌ MinIO connection failed: {e}")
            return False
