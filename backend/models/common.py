"""Common models used across the API."""

from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    """Database statistics response."""
    news_count: int
    high_impact_count: int
    avg_sentiment: float
    treasury_count: int
    etf_tickers: int
    date_range: Optional[Dict[str, datetime]] = None

