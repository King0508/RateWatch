"""News and sentiment related models."""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class NewsEntities(BaseModel):
    """Extracted entities from news."""
    fed_officials: List[str] = []
    economic_indicators: List[str] = []
    treasury_instruments: List[str] = []


class NewsItem(BaseModel):
    """Single news article with sentiment analysis."""
    id: Optional[int] = None
    title: str
    summary: Optional[str] = None
    source: str
    url: Optional[str] = None
    timestamp: datetime
    
    # Sentiment
    sentiment_score: float  # -1 to 1
    sentiment_label: str    # 'bullish', 'bearish', 'neutral'
    confidence: float       # 0 to 1
    
    # Entities
    entities: NewsEntities = NewsEntities()
    
    # Metadata
    is_high_impact: bool = False


class NewsResponse(BaseModel):
    """Response containing multiple news items."""
    items: List[NewsItem]
    total: int
    page: int = 1
    page_size: int = 50


class SentimentAggregate(BaseModel):
    """Hourly sentiment aggregate."""
    timestamp: datetime
    avg_sentiment: float
    count: int
    risk_on: int
    risk_off: int
    neutral: int
    high_impact: int


class SentimentTimeSeries(BaseModel):
    """Time series of sentiment aggregates."""
    data: List[SentimentAggregate]
    period_hours: int
    summary: Dict[str, float]

