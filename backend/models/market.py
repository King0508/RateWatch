"""Market data models."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TreasuryYields(BaseModel):
    """Treasury yield rates."""
    timestamp: datetime
    us_2y: Optional[float] = None
    us_5y: Optional[float] = None
    us_10y: Optional[float] = None
    us_30y: Optional[float] = None


class ETFPrice(BaseModel):
    """ETF price data."""
    timestamp: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketData(BaseModel):
    """Combined market data response."""
    treasury_yields: List[TreasuryYields]
    etf_prices: Optional[List[ETFPrice]] = None
    period_days: int

