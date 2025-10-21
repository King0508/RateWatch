"""
Analytics package for Fixed Income Analytics Platform.
Provides correlation analysis, event studies, and signal generation.
"""

from .correlations import CorrelationAnalyzer
from .event_studies import EventStudyAnalyzer
from .signals import SignalGenerator, Backtester

__all__ = [
    "CorrelationAnalyzer",
    "EventStudyAnalyzer",
    "SignalGenerator",
    "Backtester",
]
