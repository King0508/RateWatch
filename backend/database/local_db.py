"""
Local DuckDB database integration for RateWatch.
Self-contained database manager without external dependencies.
"""

import duckdb
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalDatabase:
    """
    Manages local DuckDB database for RateWatch.
    Self-contained, no external warehouse dependencies.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize local database connection.
        
        Args:
            db_path: Path to DuckDB file (defaults to data/ratewatch.db)
        """
        if db_path is None:
            # Default to data directory in project root
            db_path = Path(__file__).parent.parent.parent / "data" / "ratewatch.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Establish connection to database."""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to local database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _initialize_schema(self):
        """Initialize database schema if not exists."""
        try:
            schema_path = Path(__file__).parent / "schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                self.conn.execute(schema_sql)
                logger.info("Database schema initialized")
            else:
                logger.warning(f"Schema file not found: {schema_path}")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    # ============= NEWS & SENTIMENT OPERATIONS =============
    
    def insert_news(self, news_item: Dict[str, Any]) -> int:
        """
        Insert a single news item with sentiment.
        
        Args:
            news_item: Dictionary with news data and sentiment
            
        Returns:
            ID of inserted record
        """
        try:
            query = """
                INSERT INTO news_sentiment (
                    title, summary, source, url, timestamp,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    is_high_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """
            
            entities = news_item.get('entities', {})
            
            result = self.conn.execute(query, [
                news_item.get('title'),
                news_item.get('summary'),
                news_item.get('source'),
                news_item.get('url'),
                news_item.get('timestamp'),
                news_item.get('sentiment_score'),
                news_item.get('sentiment_label'),
                news_item.get('confidence'),
                entities.get('fed_officials', []),
                entities.get('economic_indicators', []),
                entities.get('treasury_instruments', []),
                news_item.get('is_high_impact', False)
            ]).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to insert news: {e}")
            raise
    
    def bulk_insert_news(self, news_items: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple news items.
        
        Args:
            news_items: List of news item dictionaries
            
        Returns:
            Number of items inserted
        """
        count = 0
        for item in news_items:
            try:
                self.insert_news(item)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert item: {e}")
                continue
        
        logger.info(f"Inserted {count}/{len(news_items)} news items")
        return count
    
    def get_recent_news_count(
        self,
        hours: int = 24,
        high_impact_only: bool = False
    ) -> int:
        """
        Get the total count of recent news articles matching criteria.
        
        Args:
            hours: Hours to look back
            high_impact_only: Only count high-impact news
            
        Returns:
            Total count of matching news items
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = """
                SELECT COUNT(*)
                FROM news_sentiment
                WHERE timestamp >= ?
            """
            
            if high_impact_only:
                query += " AND is_high_impact = TRUE"
            
            result = self.conn.execute(query, [cutoff]).fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to get news count: {e}")
            return 0
    
    def get_recent_news(
        self, 
        hours: int = 24, 
        limit: int = 50,
        offset: int = 0,
        high_impact_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent news articles with sentiment.
        
        Args:
            hours: Hours to look back
            limit: Maximum number of results
            offset: Number of items to skip (for pagination)
            high_impact_only: Only return high-impact news
            
        Returns:
            List of news items
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = """
                SELECT 
                    id, title, summary, source, url, timestamp,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    is_high_impact
                FROM news_sentiment
                WHERE timestamp >= ?
            """
            
            if high_impact_only:
                query += " AND is_high_impact = TRUE"
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            
            results = self.conn.execute(query, [cutoff, limit, offset]).fetchall()
            
            return [
                {
                    'id': r[0], 'title': r[1], 'summary': r[2], 
                    'source': r[3], 'url': r[4], 'timestamp': r[5],
                    'sentiment_score': r[6], 'sentiment_label': r[7], 
                    'confidence': r[8],
                    'entities': {
                        'fed_officials': r[9],
                        'economic_indicators': r[10],
                        'treasury_instruments': r[11]
                    },
                    'is_high_impact': r[12]
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recent news: {e}")
            return []
    
    def compute_sentiment_aggregates(self, hours_back: int = 24) -> int:
        """
        Compute hourly sentiment aggregates.
        
        Args:
            hours_back: Hours to compute aggregates for
            
        Returns:
            Number of aggregates computed
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            query = """
                INSERT INTO sentiment_aggregates (
                    hour_timestamp, avg_sentiment, sentiment_count,
                    risk_on_count, risk_off_count, neutral_count,
                    high_impact_count
                )
                SELECT 
                    date_trunc('hour', timestamp) as hour,
                    AVG(sentiment_score) as avg_sent,
                    COUNT(*) as cnt,
                    SUM(CASE WHEN sentiment_label = 'bullish' THEN 1 ELSE 0 END) as risk_on,
                    SUM(CASE WHEN sentiment_label = 'bearish' THEN 1 ELSE 0 END) as risk_off,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral,
                    SUM(CASE WHEN is_high_impact THEN 1 ELSE 0 END) as high_impact
                FROM news_sentiment
                WHERE timestamp >= ?
                GROUP BY date_trunc('hour', timestamp)
                ON CONFLICT (hour_timestamp) DO UPDATE SET
                    avg_sentiment = EXCLUDED.avg_sentiment,
                    sentiment_count = EXCLUDED.sentiment_count,
                    risk_on_count = EXCLUDED.risk_on_count,
                    risk_off_count = EXCLUDED.risk_off_count,
                    neutral_count = EXCLUDED.neutral_count,
                    high_impact_count = EXCLUDED.high_impact_count
            """
            
            self.conn.execute(query, [cutoff])
            
            # Get count of affected rows
            count_query = """
                SELECT COUNT(*) FROM sentiment_aggregates 
                WHERE hour_timestamp >= ?
            """
            result = self.conn.execute(count_query, [cutoff]).fetchone()
            count = result[0] if result else 0
            
            logger.info(f"Computed {count} sentiment aggregates")
            return count
            
        except Exception as e:
            logger.error(f"Failed to compute aggregates: {e}")
            return 0
    
    def get_sentiment_timeseries(self, hours: int = 168) -> List[Dict[str, Any]]:
        """
        Get sentiment time series data.
        
        Args:
            hours: Hours to look back (default 7 days)
            
        Returns:
            List of hourly sentiment aggregates
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = """
                SELECT 
                    hour_timestamp, avg_sentiment, sentiment_count,
                    risk_on_count, risk_off_count, neutral_count,
                    high_impact_count
                FROM sentiment_aggregates
                WHERE hour_timestamp >= ?
                ORDER BY hour_timestamp ASC
            """
            
            results = self.conn.execute(query, [cutoff]).fetchall()
            
            return [
                {
                    'timestamp': r[0],
                    'avg_sentiment': r[1],
                    'count': r[2],
                    'risk_on': r[3],
                    'risk_off': r[4],
                    'neutral': r[5],
                    'high_impact': r[6]
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get sentiment timeseries: {e}")
            return []
    
    # ============= MARKET DATA OPERATIONS =============
    
    def insert_treasury_yields(self, yields_data: Dict[str, Any]) -> int:
        """Insert Treasury yield data."""
        try:
            query = """
                INSERT INTO treasury_yields (
                    timestamp, us_2y, us_5y, us_10y, us_30y, source
                ) VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
            """
            
            result = self.conn.execute(query, [
                yields_data.get('timestamp'),
                yields_data.get('us_2y'),
                yields_data.get('us_5y'),
                yields_data.get('us_10y'),
                yields_data.get('us_30y'),
                yields_data.get('source', 'FRED')
            ]).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to insert treasury yields: {e}")
            raise
    
    def insert_etf_prices(self, etf_data: Dict[str, Any]) -> int:
        """Insert ETF price data."""
        try:
            query = """
                INSERT INTO etf_prices (
                    timestamp, ticker, open, high, low, close, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """
            
            result = self.conn.execute(query, [
                etf_data.get('timestamp'),
                etf_data.get('ticker'),
                etf_data.get('open'),
                etf_data.get('high'),
                etf_data.get('low'),
                etf_data.get('close'),
                etf_data.get('volume')
            ]).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to insert ETF prices: {e}")
            raise
    
    def get_treasury_yields(
        self, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent Treasury yield data."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = """
                SELECT 
                    timestamp, us_2y, us_5y, us_10y, us_30y
                FROM treasury_yields
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            results = self.conn.execute(query, [cutoff]).fetchall()
            
            return [
                {
                    'timestamp': r[0],
                    'us_2y': r[1],
                    'us_5y': r[2],
                    'us_10y': r[3],
                    'us_30y': r[4]
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get treasury yields: {e}")
            return []
    
    def get_etf_prices(
        self, 
        ticker: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get ETF price history."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = """
                SELECT 
                    timestamp, ticker, open, high, low, close, volume
                FROM etf_prices
                WHERE ticker = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            results = self.conn.execute(query, [ticker, cutoff]).fetchall()
            
            return [
                {
                    'timestamp': r[0],
                    'ticker': r[1],
                    'open': r[2],
                    'high': r[3],
                    'low': r[4],
                    'close': r[5],
                    'volume': r[6]
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get ETF prices: {e}")
            return []
    
    # ============= STATISTICS & UTILITIES =============
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats = {}
            
            # News count
            result = self.conn.execute(
                "SELECT COUNT(*) FROM news_sentiment"
            ).fetchone()
            stats['news_count'] = result[0] if result else 0
            
            # High impact count
            result = self.conn.execute(
                "SELECT COUNT(*) FROM news_sentiment WHERE is_high_impact = TRUE"
            ).fetchone()
            stats['high_impact_count'] = result[0] if result else 0
            
            # Date range
            result = self.conn.execute(
                """
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM news_sentiment
                """
            ).fetchone()
            if result and result[0]:
                stats['date_range'] = {
                    'min': result[0],
                    'max': result[1]
                }
            
            # Average sentiment
            result = self.conn.execute(
                "SELECT AVG(sentiment_score) FROM news_sentiment"
            ).fetchone()
            stats['avg_sentiment'] = result[0] if result and result[0] else 0.0
            
            # Treasury data points
            result = self.conn.execute(
                "SELECT COUNT(*) FROM treasury_yields"
            ).fetchone()
            stats['treasury_count'] = result[0] if result else 0
            
            # ETF data points
            result = self.conn.execute(
                "SELECT COUNT(DISTINCT ticker) FROM etf_prices"
            ).fetchone()
            stats['etf_tickers'] = result[0] if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Global database instance
_db_instance = None


def get_database(db_path: str = None) -> LocalDatabase:
    """
    Get or create global database instance.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        LocalDatabase instance
    """
    global _db_instance
    
    if _db_instance is None:
        _db_instance = LocalDatabase(db_path)
    
    return _db_instance

