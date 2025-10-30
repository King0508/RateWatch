"""
Analytics API endpoints for correlation analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from backend.services.analytics_service import get_analytics_service
from backend.models.analytics import CorrelationResult, RollingCorrelation, AnalyticsResponse, CorrelationPoint

router = APIRouter()


@router.get("/correlation", response_model=CorrelationResult)
async def get_correlation(
    lookback_days: int = Query(30, description="Days to analyze"),
    lag_hours: int = Query(0, description="Lag in hours (positive = sentiment leads)"),
    instrument: str = Query("us_10y", description="Yield instrument to analyze")
):
    """
    Calculate correlation between sentiment and yield changes.
    """
    try:
        analytics = get_analytics_service()
        result = analytics.get_sentiment_yield_correlation(
            lookback_days=lookback_days,
            lag_hours=lag_hours,
            instrument=instrument
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return CorrelationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


@router.get("/rolling-correlation", response_model=List[RollingCorrelation])
async def get_rolling_correlation(
    lookback_days: int = Query(90, description="Total period to analyze"),
    window_days: int = Query(30, description="Rolling window size"),
    instrument: str = Query("us_10y", description="Yield instrument")
):
    """
    Get rolling correlation over time.
    """
    try:
        analytics = get_analytics_service()
        results = analytics.get_rolling_correlation(
            lookback_days=lookback_days,
            window_days=window_days,
            instrument=instrument
        )
        
        return [RollingCorrelation(**item) for item in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rolling correlation failed: {str(e)}")


@router.get("/data-points", response_model=List[CorrelationPoint])
async def get_correlation_data_points(
    lookback_days: int = Query(30, description="Days to retrieve"),
    instrument: str = Query("us_10y", description="Yield instrument")
):
    """
    Get individual data points for scatter plot visualization.
    """
    try:
        analytics = get_analytics_service()
        results = analytics.get_correlation_data_points(
            lookback_days=lookback_days,
            instrument=instrument
        )
        
        return [CorrelationPoint(**item) for item in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data points: {str(e)}")


@router.get("/summary")
async def get_analytics_summary(
    lookback_days: int = Query(30, description="Days to analyze")
) -> Dict[str, Any]:
    """
    Get comprehensive analytics summary.
    """
    try:
        analytics = get_analytics_service()
        summary = analytics.get_analytics_summary(lookback_days=lookback_days)
        
        if 'error' in summary:
            raise HTTPException(status_code=400, detail=summary['error'])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

