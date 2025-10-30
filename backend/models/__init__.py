"""Data models for RateWatch API."""

from .news import NewsItem, NewsResponse, SentimentTimeSeries
from .market import TreasuryYields, ETFPrice, MarketData
from .analytics import CorrelationResult, AnalyticsResponse
from .common import StatusResponse, StatsResponse

__all__ = [
    'NewsItem',
    'NewsResponse',
    'SentimentTimeSeries',
    'TreasuryYields',
    'ETFPrice',
    'MarketData',
    'CorrelationResult',
    'AnalyticsResponse',
    'StatusResponse',
    'StatsResponse'
]

