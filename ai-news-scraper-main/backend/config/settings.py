"""
Configuration Settings
Central configuration for all backend services
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "ai-news-warehouse")

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "airy")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airypass123")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "ai_news_warehouse")

# Scraping Configuration
RSS_LIMIT_PER_SOURCE = int(os.getenv("RSS_LIMIT_PER_SOURCE", "5"))
HTML_LIMIT_PER_SOURCE = int(os.getenv("HTML_LIMIT_PER_SOURCE", "3"))

# Transformation Configuration
MIN_WORD_COUNT = int(os.getenv("MIN_WORD_COUNT", "50"))
TARGET_LANGUAGES = os.getenv("TARGET_LANGUAGES", "en,fr").split(",")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Airflow Configuration
AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/root/airflow")
AIRFLOW_DAGS_FOLDER = os.getenv("AIRFLOW_DAGS_FOLDER", f"{AIRFLOW_HOME}/dags")

# Batch Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "1"))
TRANSFORM_INTERVAL_HOURS = int(os.getenv("TRANSFORM_INTERVAL_HOURS", "2"))
ANALYTICS_INTERVAL_HOURS = int(os.getenv("ANALYTICS_INTERVAL_HOURS", "24"))

# Data quality thresholds
MAX_TITLE_LENGTH = int(os.getenv("MAX_TITLE_LENGTH", "500"))
MIN_TITLE_LENGTH = int(os.getenv("MIN_TITLE_LENGTH", "3"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "100000"))
