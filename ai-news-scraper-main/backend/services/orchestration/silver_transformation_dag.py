"""
Apache Airflow DAG: Silver Layer Transformation
Orchestrates cleaning, normalization, and language filtering (Bronze -> Silver)
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging
import json

try:
    from backend.utils.minio_client import MinIOClient
    from backend.services.transformations.clean_html import TextCleaner
    from backend.services.transformations.detect_language import LanguageDetector
except ImportError:
    logging.warning("Could not import services - DAG may be in test mode")

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
    'email_on_failure': False,
}

dag = DAG(
    'silver_transformation_dag',
    default_args=default_args,
    description='Transform Bronze articles to Silver (clean, normalize, detect language)',
    schedule_interval=None,
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=['silver', 'transformation', 'cleaning']
)

def read_bronze_articles(**context):
    """Read articles from Bronze layer in MinIO"""
    logger.info("📖 Reading Bronze articles from MinIO...")
    try:
        minio_client = MinIOClient()
        articles_meta = minio_client.list_articles(
            bucket_name="ai-news-warehouse",
            layer="bronze",
            limit=1000
        )
        logger.info(f"✅ Found {len(articles_meta)} Bronze articles")
        return articles_meta
    except Exception as e:
        logger.error(f"❌ Error reading Bronze articles: {e}")
        raise

def clean_and_normalize(**context):
    """Clean HTML and normalize text"""
    logger.info("🧹 Cleaning and normalizing articles...")
    try:
        # Get article metadata from previous task
        articles_meta = context['task_instance'].xcom_pull(task_ids='read_bronze') or []
        
        cleaner = TextCleaner()
        minio_client = MinIOClient()
        cleaned_articles = []
        
        for article_meta in articles_meta:
            try:
                # Get full article from MinIO
                article = minio_client.get_article("ai-news-warehouse", article_meta['name'])
                if article:
                    # Clean article
                    cleaned = cleaner.process_article(article)
                    is_valid, msg = cleaner.validate_silver(cleaned)
                    if is_valid:
                        cleaned_articles.append(cleaned)
            except Exception as e:
                logger.warning(f"Skipping article {article_meta['name']}: {e}")
        
        logger.info(f"✅ Cleaned {len(cleaned_articles)} articles")
        return cleaned_articles
    except Exception as e:
        logger.error(f"❌ Cleaning failed: {e}")
        raise

def filter_language(**context):
    """Filter articles by language"""
    logger.info("🌍 Filtering by language...")
    try:
        # Get cleaned articles from previous task
        cleaned_articles = context['task_instance'].xcom_pull(task_ids='clean_and_normalize') or []
        
        detector = LanguageDetector(target_languages=['en', 'fr'])
        kept, rejected = detector.filter_batch(cleaned_articles)
        
        logger.info(f"✅ Language filtering: {len(kept)} kept, {len(rejected)} rejected")
        return kept
    except Exception as e:
        logger.error(f"❌ Language filtering failed: {e}")
        raise

def save_silver_articles(**context):
    """Save Silver articles to MinIO"""
    logger.info("💾 Saving Silver articles to MinIO...")
    try:
        # Get filtered articles from previous task
        silver_articles = context['task_instance'].xcom_pull(task_ids='filter_language') or []
        
        minio_client = MinIOClient()
        saved_paths = minio_client.save_articles_batch(
            bucket_name="ai-news-warehouse",
            articles=silver_articles,
            layer="silver"
        )
        
        logger.info(f"✅ Saved {len(saved_paths)} Silver articles")
        return saved_paths
    except Exception as e:
        logger.error(f"❌ Saving Silver articles failed: {e}")
        raise

# Define tasks
task_read = PythonOperator(
    task_id='read_bronze',
    python_callable=read_bronze_articles,
    dag=dag,
)

task_clean = PythonOperator(
    task_id='clean_and_normalize',
    python_callable=clean_and_normalize,
    dag=dag,
)

task_filter = PythonOperator(
    task_id='filter_language',
    python_callable=filter_language,
    dag=dag,
)

task_save = PythonOperator(
    task_id='save_silver',
    python_callable=save_silver_articles,
    dag=dag,
)

task_trigger_gold = TriggerDagRunOperator(
    task_id='trigger_gold_analytics_dag',
    trigger_dag_id='gold_analytics_dag',
    wait_for_completion=False,
    reset_dag_run=True,
    dag=dag,
)

# Define dependencies
task_read >> task_clean >> task_filter >> task_save >> task_trigger_gold
