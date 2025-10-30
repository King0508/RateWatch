"""Analytics and correlation models."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class CorrelationPoint(BaseModel):
    """Single correlation data point."""
    timestamp: datetime
    sentiment: float
    yield_change: Optional[float] = None
    price_change: Optional[float] = None


class CorrelationResult(BaseModel):
    """Correlation analysis result."""
    correlation: float
    p_value: float
    sample_size: int
    is_significant: bool
    lag_hours: int = 0
    instrument: str
    lookback_days: int


class RollingCorrelation(BaseModel):
    """Rolling correlation data."""
    timestamp: datetime
    correlation: float
    window_days: int


class AnalyticsResponse(BaseModel):
    """Complete analytics response."""
    correlation: CorrelationResult
    rolling_correlations: Optional[List[RollingCorrelation]] = None
    data_points: Optional[List[CorrelationPoint]] = None
    summary: Dict[str, Any]

