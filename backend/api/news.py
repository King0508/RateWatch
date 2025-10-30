"""
News and sentiment API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from backend.database.local_db import get_database
from backend.models.news import NewsItem, NewsResponse, SentimentTimeSeries, SentimentAggregate, NewsEntities

router = APIRouter()


@router.get("/recent", response_model=NewsResponse)
async def get_recent_news(
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Maximum number of items"),
    high_impact_only: bool = Query(False, description="Only show high-impact news"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    Get recent news articles with sentiment analysis.
    """
    try:
        db = get_database()
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get total count of matching items
        total_count = db.get_recent_news_count(
            hours=hours,
            high_impact_only=high_impact_only
        )
        
        # Get paginated news data
        news_data = db.get_recent_news(
            hours=hours,
            limit=limit,
            offset=offset,
            high_impact_only=high_impact_only
        )
        
        # Convert to NewsItem models
        items = []
        for item in news_data:
            news_item = NewsItem(
                id=item['id'],
                title=item['title'],
                summary=item['summary'],
                source=item['source'],
                url=item['url'],
                timestamp=item['timestamp'],
                sentiment_score=item['sentiment_score'],
                sentiment_label=item['sentiment_label'],
                confidence=item['confidence'],
                entities=NewsEntities(**item['entities']),
                is_high_impact=item['is_high_impact']
            )
            items.append(news_item)
        
        return NewsResponse(
            items=items,
            total=total_count,
            page=page,
            page_size=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")


@router.get("/timeseries", response_model=SentimentTimeSeries)
async def get_sentiment_timeseries(
    hours: int = Query(168, description="Hours to look back (default 7 days)")
):
    """
    Get sentiment time series (hourly aggregates).
    """
    try:
        db = get_database()
        timeseries_data = db.get_sentiment_timeseries(hours=hours)
        
        # Convert to SentimentAggregate models
        aggregates = []
        for item in timeseries_data:
            agg = SentimentAggregate(
                timestamp=item['timestamp'],
                avg_sentiment=item['avg_sentiment'],
                count=item['count'],
                risk_on=item['risk_on'],
                risk_off=item['risk_off'],
                neutral=item['neutral'],
                high_impact=item['high_impact']
            )
            aggregates.append(agg)
        
        # Calculate summary statistics
        if aggregates:
            avg_sentiment = sum(a.avg_sentiment for a in aggregates) / len(aggregates)
            total_count = sum(a.count for a in aggregates)
            total_high_impact = sum(a.high_impact for a in aggregates)
        else:
            avg_sentiment = 0.0
            total_count = 0
            total_high_impact = 0
        
        summary = {
            'avg_sentiment': avg_sentiment,
            'total_articles': total_count,
            'high_impact_articles': total_high_impact,
            'period_hours': hours
        }
        
        return SentimentTimeSeries(
            data=aggregates,
            period_hours=hours,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch timeseries: {str(e)}")


@router.get("/search")
async def search_news(
    keyword: str = Query(..., description="Keyword to search for"),
    days: int = Query(30, description="Days to search back")
):
    """
    Search news by keyword (placeholder for future implementation).
    """
    # This would require full-text search in the database
    # For now, return a simple response
    return {
        "message": "Search functionality coming soon",
        "keyword": keyword,
        "days": days
    }

