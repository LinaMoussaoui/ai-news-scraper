# AI News Scraper - Refactored Architecture

A modular, enterprise-grade news scraping and analytics platform using Python, MinIO, PostgreSQL, Apache Airflow, and FastAPI.

## Project Structure

```
backend/
├── main.py                           # FastAPI entry point
├── services/
│   ├── scrapers/
│   │   ├── rss_scraper.py           # RSS feed scraping
│   │   └── html_scraper.py          # HTML page scraping
│   ├── ingestion.py                 # Bronze layer ingestion
│   ├── transformations/
│   │   ├── clean_html.py            # HTML cleaning & normalization
│   │   └── detect_language.py       # Language filtering
│   ├── analytics/
│   │   └── trends.py                # Gold layer analytics
│   └── orchestration/
│       ├── bronze_ingestion_dag.py  # Hourly scraping & ingestion
│       ├── silver_transformation_dag.py  # Daily cleaning & filtering
│       └── gold_analytics_dag.py    # Daily analytics & warehouse load
├── utils/
│   ├── minio_client.py              # MinIO operations
│   ├── postgres_client.py           # PostgreSQL operations
│   └── logger.py                    # Logging configuration
├── config/
│   └── settings.py                  # Centralized configuration
└── tests/
    ├── test_scrapers.py
    ├── test_ingestion.py
    ├── test_transformations.py
    └── test_analytics.py
```

## Architecture: Medallion Data Architecture

### Bronze Layer (Raw Data)

- **Source**: RSS feeds and HTML pages
- **Storage**: MinIO object storage
- **Process**: Scraped articles stored as-is
- **Trigger**: Hourly via Airflow DAG
- **Components**: `RSSScraper`, `HTMLScraper`, `IngestionService`

### Silver Layer (Cleaned Data)

- **Source**: Bronze articles
- **Storage**: MinIO object storage
- **Process**:
  - HTML tag removal
  - Text normalization
  - Language detection & filtering
  - Data validation
- **Trigger**: Daily via Airflow DAG (2 AM)
- **Components**: `TextCleaner`, `LanguageDetector`

### Gold Layer (Analytics & Warehouse)

- **Source**: Silver articles
- **Storage**: PostgreSQL database + MinIO analytics artifacts
- **Process**:
  - Article loading to database
  - Trend analysis
  - Top subjects/keywords identification
  - Source distribution statistics
  - Author statistics
- **Trigger**: Daily via Airflow DAG (3 AM)
- **Components**: `AnalyticsService`, `PostgresClient`

## Components & Services

### Scrapers

- **RSSScraper**: Parses RSS feeds (structured, fast)
  - TechCrunch AI
  - OpenAI Blog
- **HTMLScraper**: Parses HTML pages (flexible, more robust)
  - BAIR Blog
  - Distill Pub

### Data Ingestion

- **Batch Ingestion**: Scheduled scraping every hour
- **Streaming Ingestion**: Real-time article submission (future: Kafka/Pub-Sub)
- **Fallback**: Batch catches missed streaming articles
- Validation before storage

### Transformations (Silver Layer)

- **HTML Cleaning**: Remove scripts, styles, boilerplate
- **Text Normalization**: Standardize whitespace, remove special chars
- **Language Detection**: Identify language using `langdetect`
- **Filtering**: Keep only target languages (EN, FR)
- **Validation**: Word count, title length checks

### Analytics (Gold Layer)

- **Trends**: Articles per day
- **Top Subjects**: Most common categories
- **Source Distribution**: Article count by source
- **Keyword Frequency**: Most mentioned keywords
- **Author Statistics**: Most prolific authors
- **Language Distribution**: Articles by language

### Orchestration

**Apache Airflow DAGs**:

1. `bronze_ingestion_dag`: Hourly (00:00) → Scrape + Ingest
2. `silver_transformation_dag`: Daily (02:00) → Clean + Filter + Validate
3. `gold_analytics_dag`: Daily (03:00) → Load DB + Generate Analytics

### API (FastAPI)

RESTful endpoints for all operations:

**Health Checks**

- `GET /health` - API status
- `GET /health/minio` - MinIO connection
- `GET /health/postgres` - PostgreSQL connection

**Scraping**

- `POST /scrape` - Scrape articles (RSS, HTML, or both)

**Ingestion**

- `POST /ingest` - Ingest articles into Bronze
- `GET /ingest/status` - Current ingestion status

**Transformation**

- `POST /transform/clean` - Clean articles
- `POST /transform/filter-language` - Filter by language

**Analytics**

- `POST /analytics/generate` - Generate analytics from articles
- `GET /analytics/trends` - Get trends from database

**Data Lake**

- `GET /datalake/bronze/count` - Bronze article count
- `GET /datalake/silver/count` - Silver article count
- `GET /datalake/gold/count` - Gold article count

## Setup & Installation

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- MinIO running (port 9005)
- PostgreSQL running (port 5433)

### 1. Docker Setup

```bash
cd ai-news-scraper
docker-compose up -d
```

This starts:

- MinIO (http://localhost:9006 for UI)
- PostgreSQL (localhost:5433)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Initialize Database

```bash
python -c "from backend.utils.postgres_client import PostgresClient; client = PostgresClient(); client.connect(); client.create_tables(); client.disconnect()"
```

### 5. Start FastAPI Server

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 6. Start Airflow (Optional)

```bash
# Initialize Airflow database
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com

# Copy DAGs to Airflow folder
cp backend/services/orchestration/*_dag.py $AIRFLOW_HOME/dags/

# Start scheduler and webserver
airflow scheduler &
airflow webserver --port 8080 &
```

Airflow UI: http://localhost:8080

## Usage Examples

### 1. Scrape & Ingest Articles

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"scraper_type": "both", "limit_per_source": 5}'

# Returns articles, then ingest:
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"articles": [...], "source_type": "mixed"}'
```

### 2. Clean Articles

```bash
curl -X POST "http://localhost:8000/transform/clean" \
  -H "Content-Type: application/json" \
  -d '[{...bronze article...}]'
```

### 3. Filter by Language

```bash
curl -X POST "http://localhost:8000/transform/filter-language" \
  -H "Content-Type: application/json" \
  -d '[{...silver article...}]'
```

### 4. Generate Analytics

```bash
curl -X POST "http://localhost:8000/analytics/generate" \
  -H "Content-Type: application/json" \
  -d '[{...silver article...}]'

# Or fetch from database
curl "http://localhost:8000/analytics/trends"
```

### 5. Run Python Pipeline Directly

```bash
from backend.services.scrapers.rss_scraper import RSSScraper
from backend.services.scrapers.html_scraper import HTMLScraper
from backend.services.ingestion import IngestionService
from backend.services.transformations.clean_html import TextCleaner
from backend.services.transformations.detect_language import LanguageDetector
from backend.services.analytics.trends import AnalyticsService

# Scrape
rss_articles = RSSScraper().scrape_all(limit_per_source=5)
html_articles = HTMLScraper().scrape_all(limit_per_source=3)
all_articles = rss_articles + html_articles

# Ingest
ingestion = IngestionService()
ingestion.ingest_batch(all_articles)

# Clean
cleaner = TextCleaner()
silver_articles = [cleaner.process_article(a) for a in all_articles]

# Filter
detector = LanguageDetector(['en', 'fr'])
kept, rejected = detector.filter_batch(silver_articles)

# Analyze
analytics = AnalyticsService.generate_full_analytics(kept)
```

## Configuration

Edit `backend/config/settings.py` or `.env` file:

```bash
# MinIO
MINIO_ENDPOINT=localhost:9005
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=airy
POSTGRES_PASSWORD=airypass123
POSTGRES_DATABASE=ai_news_warehouse

# Scraping limits
RSS_LIMIT_PER_SOURCE=5
HTML_LIMIT_PER_SOURCE=3

# Target languages
TARGET_LANGUAGES=en,fr

# Quality thresholds
MIN_WORD_COUNT=50
```

## Monitoring & Logs

- **Logs directory**: `logs/app.log` (rotating, max 10MB)
- **Airflow logs**: `airflow/logs/`
- **MinIO console**: http://localhost:9006
- **API docs**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080

## Testing

```bash
pytest backend/tests/
pytest backend/tests/test_scrapers.py -v
pytest backend/tests/test_transformations.py -v
pytest backend/tests/test_analytics.py -v
```

## Key Features

✅ **Modular Architecture**: Separation of concerns (scrapers, ingestion, transformation, analytics)
✅ **Medallion Data Architecture**: Bronze → Silver → Gold layering
✅ **Batch Ingestion**: Hourly scheduled scraping via Airflow
✅ **Streaming Ready**: Framework for real-time ingestion (Kafka/Pub-Sub)
✅ **Data Quality**: Validation, cleansing, language filtering
✅ **Analytics**: Automated trend analysis and insights
✅ **Scalable**: MinIO for distributed storage, PostgreSQL for analytics
✅ **RESTful API**: FastAPI with OpenAPI documentation
✅ **Orchestration**: Apache Airflow for workflow management
✅ **Logging**: Centralized logging with rotation

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RSS Feeds  ─┐                                                 │
│              ├──► Scrapers ──► Bronze ──► Silver ──► Gold      │
│  HTML Pages ─┘                (MinIO)    (MinIO)    (PostgreSQL)│
│                                  ▲                       ▲      │
│                                  │                       │      │
│                            Ingestion Service      Analytics     │
│                           (Batch/Streaming)     & Warehouse     │
│                                                                 │
│  ┌────────────────────── Airflow DAGs ──────────────────────┐  │
│  │                                                            │  │
│  │ • bronze_ingestion_dag: Every hour (00:00)               │  │
│  │ • silver_transformation_dag: Daily (02:00)               │  │
│  │ • gold_analytics_dag: Daily (03:00)                      │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────────── FastAPI REST API ─────────────────────┐   │
│  │                                                            │   │
│  │ /scrape /ingest /transform/clean /transform/filter-lang  │   │
│  │ /analytics/generate /analytics/trends /datalake/* /health │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Future Enhancements

- [ ] Real-time streaming ingestion (Kafka/Redis)
- [ ] Advanced NLP (entity recognition, sentiment analysis)
- [ ] Streamlit dashboard
- [ ] Email notifications & alerts
- [ ] Data governance & lineage tracking
- [ ] ML-based content recommendation
- [ ] GraphQL API layer
- [ ] Distributed processing (Spark integration)

## Contributing

1. Create feature branch: `git checkout -b feature/xyz`
2. Commit changes: `git commit -m "Add feature xyz"`
3. Push to branch: `git push origin feature/xyz`
4. Create Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on the project repository.
