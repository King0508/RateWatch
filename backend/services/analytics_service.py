"""
Analytics service for sentiment-market correlation analysis.
Simplified version focused on core correlation metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

from backend.database.local_db import get_database

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analyzes correlations between sentiment scores and market movements.
    """
    
    def __init__(self):
        self.db = get_database()
    
    def get_sentiment_yield_correlation(
        self, 
        lookback_days: int = 30,
        lag_hours: int = 0,
        instrument: str = 'us_10y'
    ) -> Dict[str, any]:
        """
        Calculate correlation between sentiment and yield changes.
        
        Args:
            lookback_days: Number of days to analyze
            lag_hours: Hours to lag sentiment (positive = sentiment leads yields)
            instrument: Which yield to analyze (us_2y, us_5y, us_10y, us_30y)
            
        Returns:
            Dictionary with correlation results
        """
        try:
            # Get sentiment data
            cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            sentiment_data = self.db.get_sentiment_timeseries(hours=lookback_days * 24)
            
            if not sentiment_data:
                return {
                    'error': 'No sentiment data available',
                    'correlation': 0.0,
                    'p_value': 1.0,
                    'sample_size': 0
                }
            
            # Get yield data
            yield_data = self.db.get_treasury_yields(days=lookback_days)
            
            if not yield_data:
                return {
                    'error': 'No yield data available',
                    'correlation': 0.0,
                    'p_value': 1.0,
                    'sample_size': 0
                }
            
            # Convert to DataFrames
            sentiment_df = pd.DataFrame(sentiment_data)
            sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
            sentiment_df = sentiment_df.set_index('timestamp').sort_index()
            
            yield_df = pd.DataFrame(yield_data)
            yield_df['timestamp'] = pd.to_datetime(yield_df['timestamp'])
            yield_df = yield_df.set_index('timestamp').sort_index()
            
            # Resample to daily frequency for stability
            sentiment_daily = sentiment_df['avg_sentiment'].resample('D').mean()
            yield_daily = yield_df[instrument].resample('D').mean()
            
            # Calculate yield changes
            yield_changes = yield_daily.diff()
            
            # Apply lag if specified
            if lag_hours != 0:
                lag_days = lag_hours / 24
                if lag_days > 0:
                    # Sentiment leads: shift sentiment back
                    sentiment_daily = sentiment_daily.shift(-int(lag_days))
                else:
                    # Yields lead: shift yields back
                    yield_changes = yield_changes.shift(int(abs(lag_days)))
            
            # Align data
            combined = pd.DataFrame({
                'sentiment': sentiment_daily,
                'yield_change': yield_changes
            }).dropna()
            
            if len(combined) < 3:
                return {
                    'error': 'Insufficient overlapping data points',
                    'correlation': 0.0,
                    'p_value': 1.0,
                    'sample_size': len(combined)
                }
            
            # Calculate correlation
            correlation, p_value = stats.pearsonr(
                combined['sentiment'], 
                combined['yield_change']
            )
            
            is_significant = p_value < 0.05
            
            return {
                'correlation': float(correlation),
                'p_value': float(p_value),
                'sample_size': len(combined),
                'is_significant': is_significant,
                'lag_hours': lag_hours,
                'instrument': instrument,
                'lookback_days': lookback_days,
                'date_range': {
                    'start': combined.index.min().isoformat(),
                    'end': combined.index.max().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Correlation calculation failed: {e}")
            return {
                'error': str(e),
                'correlation': 0.0,
                'p_value': 1.0,
                'sample_size': 0
            }
    
    def get_rolling_correlation(
        self,
        lookback_days: int = 90,
        window_days: int = 30,
        instrument: str = 'us_10y'
    ) -> List[Dict[str, any]]:
        """
        Calculate rolling correlation over time.
        
        Args:
            lookback_days: Total period to analyze
            window_days: Rolling window size
            instrument: Which yield to analyze
            
        Returns:
            List of rolling correlation data points
        """
        try:
            # Get data
            sentiment_data = self.db.get_sentiment_timeseries(hours=lookback_days * 24)
            yield_data = self.db.get_treasury_yields(days=lookback_days)
            
            if not sentiment_data or not yield_data:
                return []
            
            # Convert to DataFrames
            sentiment_df = pd.DataFrame(sentiment_data)
            sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
            sentiment_df = sentiment_df.set_index('timestamp').sort_index()
            
            yield_df = pd.DataFrame(yield_data)
            yield_df['timestamp'] = pd.to_datetime(yield_df['timestamp'])
            yield_df = yield_df.set_index('timestamp').sort_index()
            
            # Resample to daily
            sentiment_daily = sentiment_df['avg_sentiment'].resample('D').mean()
            yield_daily = yield_df[instrument].resample('D').mean()
            yield_changes = yield_daily.diff()
            
            # Combine
            combined = pd.DataFrame({
                'sentiment': sentiment_daily,
                'yield_change': yield_changes
            }).dropna()
            
            if len(combined) < window_days:
                return []
            
            # Calculate rolling correlation
            rolling_corr = combined['sentiment'].rolling(window=window_days).corr(
                combined['yield_change']
            )
            
            # Convert to list of dicts
            results = []
            for timestamp, corr in rolling_corr.dropna().items():
                results.append({
                    'timestamp': timestamp.isoformat(),
                    'correlation': float(corr),
                    'window_days': window_days
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Rolling correlation failed: {e}")
            return []
    
    def get_correlation_data_points(
        self,
        lookback_days: int = 30,
        instrument: str = 'us_10y'
    ) -> List[Dict[str, any]]:
        """
        Get individual data points for scatter plot visualization.
        
        Args:
            lookback_days: Number of days to retrieve
            instrument: Which yield to analyze
            
        Returns:
            List of data points with sentiment and yield changes
        """
        try:
            sentiment_data = self.db.get_sentiment_timeseries(hours=lookback_days * 24)
            yield_data = self.db.get_treasury_yields(days=lookback_days)
            
            if not sentiment_data or not yield_data:
                return []
            
            # Convert to DataFrames
            sentiment_df = pd.DataFrame(sentiment_data)
            sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
            sentiment_df = sentiment_df.set_index('timestamp').sort_index()
            
            yield_df = pd.DataFrame(yield_data)
            yield_df['timestamp'] = pd.to_datetime(yield_df['timestamp'])
            yield_df = yield_df.set_index('timestamp').sort_index()
            
            # Resample to daily
            sentiment_daily = sentiment_df['avg_sentiment'].resample('D').mean()
            yield_daily = yield_df[instrument].resample('D').mean()
            yield_changes = yield_daily.diff()
            
            # Combine
            combined = pd.DataFrame({
                'sentiment': sentiment_daily,
                'yield_change': yield_changes,
                'yield_level': yield_daily
            }).dropna()
            
            # Convert to list
            results = []
            for timestamp, row in combined.iterrows():
                results.append({
                    'timestamp': timestamp.isoformat(),
                    'sentiment': float(row['sentiment']),
                    'yield_change': float(row['yield_change']),
                    'yield_level': float(row['yield_level'])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get data points: {e}")
            return []
    
    def get_analytics_summary(
        self,
        lookback_days: int = 30
    ) -> Dict[str, any]:
        """
        Get comprehensive analytics summary.
        
        Args:
            lookback_days: Number of days to analyze
            
        Returns:
            Summary statistics and correlations
        """
        try:
            # Get base correlation
            base_corr = self.get_sentiment_yield_correlation(
                lookback_days=lookback_days,
                lag_hours=0,
                instrument='us_10y'
            )
            
            # Get correlations with different lags
            lag_correlations = []
            for lag in [1, 4, 24]:  # 1h, 4h, 24h lags
                corr = self.get_sentiment_yield_correlation(
                    lookback_days=lookback_days,
                    lag_hours=lag,
                    instrument='us_10y'
                )
                lag_correlations.append({
                    'lag_hours': lag,
                    'correlation': corr.get('correlation', 0.0),
                    'is_significant': corr.get('is_significant', False)
                })
            
            # Find best lag
            best_lag = max(lag_correlations, key=lambda x: abs(x['correlation']))
            
            # Get database stats
            db_stats = self.db.get_stats()
            
            return {
                'base_correlation': base_corr,
                'lag_analysis': lag_correlations,
                'best_lag': best_lag,
                'data_stats': db_stats,
                'analysis_period': lookback_days
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {
                'error': str(e)
            }


# Global analytics service instance
_analytics_service = None


def get_analytics_service() -> AnalyticsService:
    """Get or create global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

