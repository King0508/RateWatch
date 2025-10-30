"""
RateWatch FastAPI Backend
Modern, self-contained sentiment-market analytics API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.database.local_db import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RateWatch API...")
    
    # Initialize database
    try:
        db = get_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RateWatch API...")
    try:
        db.close()
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


# Create FastAPI app
app = FastAPI(
    title="RateWatch API",
    description="Sentiment-Market Correlation Analytics for Fixed Income",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RateWatch API",
        "version": "1.0.0",
        "description": "Sentiment-Market Correlation Analytics",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db = get_database()
        stats = db.get_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "news_count": stats.get('news_count', 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Import and include routers
from backend.api import news, market, analytics, data

app.include_router(news.router, prefix="/api/news", tags=["News & Sentiment"])
app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(data.router, prefix="/api/data", tags=["Data Management"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

