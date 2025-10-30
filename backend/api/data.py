"""
Data collection and management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, Any

from backend.services.news_processor import get_processor
from backend.services.market_data import MarketDataFetcher
from backend.database.local_db import get_database
from backend.models.common import StatusResponse, StatsResponse

router = APIRouter()


@router.post("/refresh", response_model=StatusResponse)
async def refresh_data(
    background_tasks: BackgroundTasks,
    hours: int = Query(24, description="Hours of news to collect"),
    limit: int = Query(100, description="Maximum news items to process"),
    include_market_data: bool = Query(False, description="Also fetch market data")
):
    """
    Trigger data collection (news + optional market data).
    Runs in background to avoid timeout.
    """
    def collect_data():
        """Background task to collect data."""
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Background task started: collecting {hours} hours, limit {limit}")
            # Collect news
            processor = get_processor()
            logger.info("Processor obtained, starting collection...")
            result = processor.collect_and_process(hours=hours, limit=limit)
            logger.info(f"Data collection complete: {result}")
            
            # Optionally collect market data
            if include_market_data:
                try:
                    fetcher = MarketDataFetcher()
                    # This would fetch fresh market data
                    # Implementation depends on FRED API key availability
                    pass
                except Exception as e:
                    logger.error(f"Market data fetch failed: {e}")
            
            print(f"[SUCCESS] Data collection complete: {result}")
            
        except Exception as e:
            error_msg = f"Data collection failed: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
    
    # Add task to background
    background_tasks.add_task(collect_data)
    
    return StatusResponse(
        status="initiated",
        message=f"Data collection started for last {hours} hours",
        data={
            "hours": hours,
            "limit": limit,
            "include_market_data": include_market_data
        }
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics.
    """
    try:
        db = get_database()
        stats = db.get_stats()
        
        return StatsResponse(
            news_count=stats.get('news_count', 0),
            high_impact_count=stats.get('high_impact_count', 0),
            avg_sentiment=stats.get('avg_sentiment', 0.0),
            treasury_count=stats.get('treasury_count', 0),
            etf_tickers=stats.get('etf_tickers', 0),
            date_range=stats.get('date_range')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/compute-aggregates")
async def compute_aggregates(
    hours_back: int = Query(24, description="Hours to compute aggregates for")
) -> Dict[str, Any]:
    """
    Manually trigger sentiment aggregate computation.
    """
    try:
        db = get_database()
        count = db.compute_sentiment_aggregates(hours_back=hours_back)
        
        return {
            "status": "success",
            "aggregates_computed": count,
            "hours_back": hours_back
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute aggregates: {str(e)}")


@router.post("/refresh-sync")
async def refresh_data_sync(
    hours: int = Query(24, description="Hours of news to collect"),
    limit: int = Query(10, description="Maximum news items to process")
) -> Dict[str, Any]:
    """
    Synchronous data collection for testing (shows errors immediately).
    Limited to 10 items to avoid timeout.
    """
    try:
        processor = get_processor()
        result = processor.collect_and_process(hours=hours, limit=limit)
        return result
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
