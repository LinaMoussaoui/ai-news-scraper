# AI News Scraper - Enterprise Data Pipeline

A modular, production-ready news scraping and analytics platform using Python, MinIO, PostgreSQL, Apache Airflow, and FastAPI.

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

- MinIO (port 9005, console 9006)
- PostgreSQL (port 5433)

## Quick Start

There are two main ways to run the project locally: (A) using Docker Compose to start the full stack (recommended for development), or (B) running services individually for faster iteration (backend + frontend). Follow the steps below.

### Option A — Start full stack with Docker Compose (recommended)

1. Copy the environment template and review settings:

```bash
cp .env.example .env
# Edit .env if you need custom ports/credentials
```

2. Start services (MinIO, Postgres, Redis, Airflow, Backend):

```bash
docker-compose up -d --build
```

3. Verify services:

```bash
docker-compose ps
```

Key URLs after compose:

- Backend API: http://localhost:8000
- Backend OpenAPI: http://localhost:8000/docs
- MinIO Console: http://localhost:9006
- Postgres (pgAdmin): http://localhost:5050 (or psql on port 5433)
- Airflow UI: http://localhost:8080

### Option B — Run backend + frontend locally (fast iteration)

Use this if you prefer to iterate on the API or frontend without rebuilding containers.

1. Prepare Python environment and install backend deps:

```bash
### Data Flow

```

RSS Feeds & HTML Pages
↓
Scrapers (RSS + HTML)
↓

2. Start Postgres and MinIO (recommended via docker-compose while running backend locally):

````bash
    Bronze Layer (MinIO) - Raw articles
        ↓
    Ingestion Service (Batch/Streaming)

3. Run the backend API locally:

```bash
        ↓
    Silver Layer (MinIO) - Clean & validated
        ↓

API will be available at `http://localhost:8000` and the OpenAPI docs at `/docs`.

### Frontend (Next.js) — Run the dashboard locally

We provide a Next.js frontend in `frontend/` (not committed by default). To scaffold and run a local prototype:

```bash
    Transformations (Clean HTML, Language Filter)
        ↓
    Gold Layer (PostgreSQL) - Analytics & insights
        ↓
    FastAPI REST API & Reports
````

## Project Structure

Notes:

- The frontend expects the backend API at `http://localhost:8000`. You can change `NEXT_PUBLIC_API_URL` in `.env.local` inside `frontend/`.
- The dashboard page is served on `http://localhost:3000` by default.

### Airflow (optional)

If you want to run Airflow via Docker Compose the compose file includes services and initialization. To run Airflow only:

```bash

```

Airflow UI: http://localhost:8080
ai-news-scraper/
├── backend/ # All backend code
│ ├── main.py # FastAPI entry point
│ ├── services/
│ │ ├── scrapers/
│ │ │ ├── rss_scraper.py # RSS feed scraping
│ │ │ └── html_scraper.py # HTML page scraping
│ │ ├── ingestion.py # Bronze layer ingestion
│ │ ├── transformations/
│ │ │ ├── clean_html.py # HTML cleaning & normalization
│ │ │ └── detect_language.py # Language filtering
│ │ ├── analytics/
│ │ │ └── trends.py # Gold layer analytics
│ │ └── orchestration/
│ │ ├── bronze_ingestion_dag.py # Hourly scraping
│ │ ├── silver_transformation_dag.py # Daily cleaning
│ │ └── gold_analytics_dag.py # Daily analytics
│ ├── utils/
│ │ ├── minio_client.py # MinIO operations
│ │ ├── postgres_client.py # PostgreSQL operations
│ │ └── logger.py # Logging
│ ├── config/
│ │ └── settings.py # Configuration
│ └── tests/ # Unit & integration tests
├── docs/ # Documentation
├── docker-compose.yml # MinIO + PostgreSQL
├── requirements.txt # Python dependencies
├── .env.example # Environment template
├── README.md # This file
└── ARCHITECTURE.md # Detailed architecture guide

````

## Key Features

✅ **Modular Architecture** - Clean separation of concerns
✅ **Medallion Data Architecture** - Bronze → Silver → Gold layering
✅ **Batch & Streaming** - Hourly batch scraping, streaming-ready framework
✅ **Data Quality** - Validation, cleansing, language filtering
✅ **Analytics** - Automated trend analysis and insights
✅ **Scalable** - MinIO for distributed storage, PostgreSQL for analytics
✅ **REST API** - FastAPI with OpenAPI documentation
✅ **Orchestration** - Apache Airflow for workflow management
✅ **Logging** - Centralized logging with rotation

## Usage Examples

### API Endpoints

**Health Checks**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/minio
curl http://localhost:8000/health/postgres
````

**Scrape Articles**

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"scraper_type": "both", "limit_per_source": 5}'
```

**Ingest to Bronze**

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"articles": [...], "source_type": "mixed"}'
```

**Clean Articles**

```bash
curl -X POST "http://localhost:8000/transform/clean" \
  -H "Content-Type: application/json" \
  -d '[{...article...}]'
```

**Filter by Language**

```bash
curl -X POST "http://localhost:8000/transform/filter-language" \
  -H "Content-Type: application/json" \
  -d '[{...article...}]'
```

**Generate Analytics**

```bash
curl -X POST "http://localhost:8000/analytics/generate" \
  -H "Content-Type: application/json" \
  -d '[{...article...}]'
```

**Get Trends from Database**

```bash
curl http://localhost:8000/analytics/trends
```

### Python Usage

```python
from backend.services.scrapers.rss_scraper import RSSScraper
from backend.services.scrapers.html_scraper import HTMLScraper
from backend.services.ingestion import IngestionService
from backend.services.transformations.clean_html import TextCleaner
from backend.services.transformations.detect_language import LanguageDetector
from backend.services.analytics.trends import AnalyticsService

# Scrape
rss_articles = RSSScraper().scrape_all(limit_per_source=5)
html_articles = HTMLScraper().scrape_all(limit_per_source=3)

# Ingest
ingestion = IngestionService()
ingestion.ingest_batch(rss_articles + html_articles)

# Clean
cleaner = TextCleaner()
silver = [cleaner.process_article(a) for a in (rss_articles + html_articles)]

# Filter by language
detector = LanguageDetector(['en', 'fr'])
kept, rejected = detector.filter_batch(silver)

# Generate analytics
analytics = AnalyticsService.generate_full_analytics(kept)
```

## Scraped Data Sources

### RSS Feeds

- TechCrunch AI
- OpenAI Blog

### HTML Pages

- BAIR Blog (Berkeley AI Research)
- Distill Pub

_Note: Add more sources in `backend/services/scrapers/rss_scraper.py` and `backend/services/scrapers/html_scraper.py`_

## Configuration

Create/edit `.env` file (template at `.env.example`):

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

# Scraping
RSS_LIMIT_PER_SOURCE=5
HTML_LIMIT_PER_SOURCE=3

# Filtering
TARGET_LANGUAGES=en,fr
MIN_WORD_COUNT=50
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture, data flow, and advanced setup
- **[docs/tasks.txt](docs/tasks.txt)** - Original project requirements
- **API Docs** - http://localhost:8000/docs (interactive Swagger UI)

## Testing

```bash
pytest backend/tests/
pytest backend/tests/test_scrapers.py -v
pytest backend/tests/test_transformations.py -v
pytest backend/tests/test_analytics.py -v
```

## Monitoring

- **Logs**: `logs/app.log` (rotating, 10MB max)
- **MinIO Console**: http://localhost:9006
- **API Documentation**: http://localhost:8000/docs
- **Airflow Dashboard**: http://localhost:8080 (if running)

## Troubleshooting

**MinIO Connection Failed**

```bash
# Check MinIO status
docker-compose ps

# Restart MinIO
docker-compose restart minio
```

**PostgreSQL Connection Failed**

```bash
# Check PostgreSQL status
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres
```

**Import Errors**

```bash
# Ensure you're in the project root
cd c:\Users\jnane\OneDrive\Desktop\ai-news-scraper

# Add to PYTHONPATH (PowerShell)
$env:PYTHONPATH += ";$(Get-Location)"

# Or (Bash)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Next Steps

1. ✅ Data collection (scrapers working)
2. ✅ Data lake (MinIO Bronze/Silver/Gold)
3. ✅ Batch ingestion (Airflow DAGs)
4. ⏳ Dashboard (Streamlit - future)
5. ⏳ Advanced analytics (ML, NLP - future)

## Contributing

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed development guide.

## License

MIT License - See LICENSE file for details
