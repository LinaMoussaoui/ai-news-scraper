"""
Apache Airflow DAG: Gold Layer Analytics
Orchestrates analytics generation and loading to PostgreSQL (Silver -> Gold)
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging
import json

try:
    from backend.utils.minio_client import MinIOClient
    from backend.utils.postgres_client import PostgresClient
    from backend.services.analytics.trends import AnalyticsService
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
    'gold_analytics_dag',
    default_args=default_args,
    description='Generate analytics from Silver articles and load to PostgreSQL (Gold)',
    schedule_interval=None,
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=['gold', 'analytics', 'warehouse']
)

def read_silver_articles(**context):
    """Read articles from Silver layer in MinIO"""
    logger.info("📖 Reading Silver articles from MinIO...")
    try:
        minio_client = MinIOClient()
        articles_meta = minio_client.list_articles(
            bucket_name="ai-news-warehouse",
            layer="silver",
            limit=1000
        )
        logger.info(f"✅ Found {len(articles_meta)} Silver articles")
        
        # Get full articles
        silver_articles = []
        for meta in articles_meta:
            try:
                article = minio_client.get_article("ai-news-warehouse", meta['name'])
                if article:
                    silver_articles.append(article)
            except Exception as e:
                logger.warning(f"Could not read article {meta['name']}: {e}")
        
        logger.info(f"✅ Read {len(silver_articles)} full Silver articles")
        return silver_articles
    except Exception as e:
        logger.error(f"❌ Error reading Silver articles: {e}")
        raise

def generate_analytics(**context):
    """Generate analytics from Silver articles"""
    logger.info("📊 Generating analytics...")
    try:
        # Get Silver articles from previous task
        silver_articles = context['task_instance'].xcom_pull(task_ids='read_silver') or []
        
        # Generate comprehensive analytics
        analytics = AnalyticsService.generate_full_analytics(silver_articles)
        
        logger.info(f"✅ Analytics generated")
        return analytics
    except Exception as e:
        logger.error(f"❌ Analytics generation failed: {e}")
        raise

def load_to_postgres(**context):
    """Load articles and analytics to PostgreSQL"""
    logger.info("🗄️  Loading to PostgreSQL...")
    try:
        # Get Silver articles and analytics
        silver_articles = context['task_instance'].xcom_pull(task_ids='read_silver') or []
        analytics = context['task_instance'].xcom_pull(task_ids='generate_analytics') or {}
        
        # Connect to PostgreSQL
        pg_client = PostgresClient()
        if not pg_client.connect():
            raise Exception("Could not connect to PostgreSQL")
        
        # Create tables if they don't exist
        pg_client.create_tables()
        
        # Load articles
        inserted = pg_client.insert_articles_batch(silver_articles)
        logger.info(f"✅ Inserted {inserted} articles into PostgreSQL")
        
        # Load analytics data into analytics tables
        if analytics:
            # Insert articles per day
            trends = analytics.get("trends", {})
            pg_client.insert_articles_per_day(trends)
            
            # Insert articles per source
            source_dist = analytics.get("source_distribution", [])
            pg_client.insert_articles_per_source(source_dist)
            
            # Insert articles per category
            top_subjects = analytics.get("top_subjects", [])
            pg_client.insert_articles_per_category(top_subjects)
            
            # Insert keyword trends
            top_keywords = analytics.get("top_keywords", [])
            pg_client.insert_keyword_trends(top_keywords)
            
            logger.info(f"✅ Analytics loaded: trends, sources, categories, keywords")
        
        pg_client.disconnect()
        return {"articles_inserted": inserted, "analytics_loaded": True}
    except Exception as e:
        logger.error(f"❌ PostgreSQL loading failed: {e}")
        raise

def save_gold_analytics(**context):
    """Save analytics to MinIO Gold layer"""
    logger.info("💾 Saving analytics to Gold layer...")
    try:
        # Get analytics from previous task
        analytics = context['task_instance'].xcom_pull(task_ids='generate_analytics') or {}
        
        # Save as Gold layer artifact
        minio_client = MinIOClient()
        import io
        
        gold_article = {
            "article_id": f"analytics_{__import__('datetime').datetime.utcnow().isoformat()}",
            "title": "Daily Analytics Report",
            "content": json.dumps(analytics, indent=2),
            "url": "internal://analytics",
            "source": "analytics-engine",
            "source_type": "analytics",
            "author": "System",
            "published_date": __import__('datetime').datetime.utcnow().isoformat() + "Z",
            "description": "Automated analytics report",
            "keywords": "analytics, trends, dashboard",
            "category": "Analytics",
            "word_count": len(str(analytics).split()),
            "is_valid": True,
            "processed_at": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }
        
        path = minio_client.save_article(
            bucket_name="ai-news-warehouse",
            article=gold_article,
            layer="gold"
        )
        
        logger.info(f"✅ Analytics saved to Gold layer: {path}")
        return path
    except Exception as e:
        logger.error(f"❌ Saving Gold analytics failed: {e}")
        raise

# Define tasks
task_read = PythonOperator(
    task_id='read_silver',
    python_callable=read_silver_articles,
    dag=dag,
)

task_analytics = PythonOperator(
    task_id='generate_analytics',
    python_callable=generate_analytics,
    dag=dag,
)

task_postgres = PythonOperator(
    task_id='load_to_postgres',
    python_callable=load_to_postgres,
    dag=dag,
)

task_gold = PythonOperator(
    task_id='save_gold_analytics',
    python_callable=save_gold_analytics,
    dag=dag,
)

# Define dependencies
task_read >> task_analytics >> [task_postgres, task_gold]
