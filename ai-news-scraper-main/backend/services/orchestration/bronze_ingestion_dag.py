"""
Apache Airflow DAG: Bronze Layer Ingestion
Orchestrates scraping (RSS + HTML) and ingestion into MinIO every hour
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging

# Assuming imports work with proper PYTHONPATH
try:
    from backend.services.scrapers.rss_scraper import RSSScraper
    from backend.services.scrapers.html_scraper import HTMLScraper
    from backend.services.ingestion import IngestionService
except ImportError:
    logging.warning("Could not import services - DAG may be in test mode")

logger = logging.getLogger(__name__)

# DAG configuration
default_args = {
    'owner': 'data-engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG(
    'bronze_ingestion_dag',
    default_args=default_args,
    description='Scrape news articles (RSS + HTML) and ingest into MinIO Bronze layer',
    schedule_interval='*/5 * * * *',  # Every 5 minutes for near real-time polling
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=['bronze', 'ingestion', 'scraping']
)

def scrape_rss(**context):
    """Scrape RSS feeds and return articles"""
    logger.info("🔄 Starting RSS scraping task...")
    try:
        scraper = RSSScraper()
        articles = scraper.scrape_all(limit_per_source=5)
        logger.info(f"✅ RSS scraping complete: {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"❌ RSS scraping failed: {e}")
        raise

def scrape_html(**context):
    """Scrape HTML pages and return articles"""
    logger.info("🔄 Starting HTML scraping task...")
    try:
        scraper = HTMLScraper()
        articles = scraper.scrape_all(limit_per_source=3)
        logger.info(f"✅ HTML scraping complete: {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"❌ HTML scraping failed: {e}")
        raise

def ingest_articles(**context):
    """Ingest scraped articles into MinIO"""
    logger.info("🔄 Starting ingestion task...")
    try:
        # Get articles from upstream tasks
        rss_articles = context['task_instance'].xcom_pull(task_ids='scrape_rss') or []
        html_articles = context['task_instance'].xcom_pull(task_ids='scrape_html') or []
        
        # Combine articles
        all_articles = rss_articles + html_articles
        logger.info(f"Total articles to ingest: {len(all_articles)}")
        
        # Ingest to MinIO
        ingestion_service = IngestionService()
        stats = ingestion_service.ingest_batch(all_articles, source_type="mixed")
        
        logger.info(f"✅ Ingestion complete: {stats['saved_articles']} articles saved")
        return stats
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise

# Define tasks
task_scrape_rss = PythonOperator(
    task_id='scrape_rss',
    python_callable=scrape_rss,
    dag=dag,
)

task_scrape_html = PythonOperator(
    task_id='scrape_html',
    python_callable=scrape_html,
    dag=dag,
)

task_ingest = PythonOperator(
    task_id='ingest_articles',
    python_callable=ingest_articles,
    dag=dag,
)

task_trigger_silver = TriggerDagRunOperator(
    task_id='trigger_silver_transformation_dag',
    trigger_dag_id='silver_transformation_dag',
    wait_for_completion=False,
    reset_dag_run=True,
    dag=dag,
)

# Define dependencies
[task_scrape_rss, task_scrape_html] >> task_ingest >> task_trigger_silver
