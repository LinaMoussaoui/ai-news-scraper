"""
FastAPI Application Entry Point
RESTful API for the AI News Scraper system
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os

# Configure logging
from backend.utils.logger import setup_logging, get_logger
setup_logging("INFO")
logger = get_logger(__name__)

# Import route routers
from backend.routes import health, scraping, ingestion, transformation, analytics, datalake, realtime
from backend.utils.event_broadcaster import get_broadcaster
from backend.utils.api_errors import ApiErrorPayload

# Create FastAPI app
app = FastAPI(
    title="AI News Scraper API",
    description="RESTful API for web scraping, data ingestion, and analytics with real-time events",
    version="1.0.0"
)


def _structured_error(status_code: int, error_code: str, message: str, suggested_fix: str, details=None):
    return JSONResponse(
        status_code=status_code,
        content=ApiErrorPayload(
            error_code=error_code,
            error_message=message,
            suggested_fix=suggested_fix,
            details=details,
        ).to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _structured_error(
        422,
        "REQUEST_VALIDATION_FAILED",
        "Request payload is malformed or missing required fields",
        "Check the request body and query parameters against the endpoint schema in /docs.",
        details={"errors": exc.errors(), "path": str(request.url.path)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and {"error_code", "error_message", "suggested_fix"}.issubset(exc.detail):
        payload = dict(exc.detail)
        payload.setdefault("details", {"path": str(request.url.path)})
        return JSONResponse(status_code=exc.status_code, content=payload)
    return _structured_error(
        exc.status_code,
        "HTTP_ERROR",
        str(exc.detail),
        "Inspect the endpoint input and backend logs for the failure point.",
        details={"path": str(request.url.path)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return _structured_error(
        500,
        "UNHANDLED_SERVER_ERROR",
        "An unexpected server error occurred",
        "Check the server logs and fix the failing backend method or dependency.",
        details={"path": str(request.url.path), "exception": exc.__class__.__name__},
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event broadcaster startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize event broadcaster on startup"""
    try:
        broadcaster = await get_broadcaster()
        logger.info("✅ Event broadcaster initialized on startup")
    except Exception as e:
        logger.error(f"❌ Failed to initialize event broadcaster: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup event broadcaster on shutdown"""
    try:
        broadcaster = await get_broadcaster()
        await broadcaster.disconnect()
        logger.info("Event broadcaster disconnected")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Include routers
app.include_router(health.router)
app.include_router(scraping.router)
app.include_router(ingestion.router)
app.include_router(transformation.router)
app.include_router(analytics.router)
app.include_router(datalake.router)
app.include_router(realtime.router)

# Serve static files (dashboard)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Dashboard endpoint
@app.get("/dashboard")
async def dashboard():
    """Serve real-time dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {"error": "Dashboard not found"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "AI News Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/dashboard (GET - HTML)",
            "health": "/health",
            "scraping": "/scrape (POST)",
            "ingestion": "/ingest (POST)",
            "transformation": "/transform/clean (POST), /transform/filter-language (POST)",
            "analytics": "/analytics/generate (POST), /analytics/trends (GET)",
            "datalake": "/datalake/bronze/count, /datalake/silver/count, /datalake/gold/count",
            "realtime": "/realtime/ws/events (WebSocket), /realtime/ws/bronze, /realtime/ws/silver, /realtime/ws/gold"
        },
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

