"""
DuckDB database manager for Fixed Income Analytics Platform.
Handles all database operations, ETL, and data persistence.
"""

import duckdb
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages DuckDB database operations for news sentiment and market data.
    """

    def __init__(self, db_path: str = "database/fixed_income.duckdb"):
        """
        Initialize database connection and ensure schema exists.
        
        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self.conn = None
        self._ensure_db_directory()
        self._connect()
        self._initialize_schema()

    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _initialize_schema(self):
        """Initialize database schema from SQL file."""
        schema_path = Path("database/schema.sql")
        
        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return

        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema - split by semicolons for multiple statements
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    self.conn.execute(statement)
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    # === News Sentiment Operations ===

    def insert_news_item(self, item: Dict[str, Any]) -> int:
        """
        Insert a news item with sentiment and entities into the database.
        
        Args:
            item: Dictionary containing news data with keys:
                - timestamp, source, title, summary, link
                - sentiment_score, sentiment_label, confidence
                - entities (dict with fed_officials, economic_indicators, etc.)
                
        Returns:
            ID of inserted row
        """
        try:
            entities = item.get('entities', {})
            
            result = self.conn.execute("""
                INSERT INTO news_sentiment (
                    timestamp, source, title, summary, link,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    credit_terms, yields, basis_points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, [
                item.get('timestamp', datetime.now(timezone.utc)),
                item['source'],
                item['title'],
                item.get('summary', ''),
                item.get('link', ''),
                item['sentiment_score'],
                item['sentiment_label'],
                item.get('confidence', 0.0),
                entities.get('fed_officials', []),
                entities.get('economic_indicators', []),
                entities.get('treasury_instruments', []),
                entities.get('credit_terms', []),
                entities.get('yields', []),
                entities.get('basis_points', []),
            ]).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to insert news item: {e}")
            raise

    def bulk_insert_news(self, items: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple news items for efficiency.
        
        Args:
            items: List of news item dictionaries
            
        Returns:
            Number of items inserted
        """
        if not items:
            return 0

        try:
            # Prepare data for bulk insert
            data = []
            for item in items:
                entities = item.get('entities', {})
                data.append([
                    item.get('timestamp', datetime.now(timezone.utc)),
                    item['source'],
                    item['title'],
                    item.get('summary', ''),
                    item.get('link', ''),
                    item['sentiment_score'],
                    item['sentiment_label'],
                    item.get('confidence', 0.0),
                    entities.get('fed_officials', []),
                    entities.get('economic_indicators', []),
                    entities.get('treasury_instruments', []),
                    entities.get('credit_terms', []),
                    entities.get('yields', []),
                    entities.get('basis_points', []),
                ])

            self.conn.executemany("""
                INSERT INTO news_sentiment (
                    timestamp, source, title, summary, link,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    credit_terms, yields, basis_points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            logger.info(f"Bulk inserted {len(items)} news items")
            return len(items)

        except Exception as e:
            logger.error(f"Failed to bulk insert news items: {e}")
            raise

    def get_recent_news(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent news items from database.
        
        Args:
            hours: Look back window in hours
            limit: Maximum number of items to return
            
        Returns:
            List of news item dictionaries
        """
        try:
            result = self.conn.execute("""
                SELECT 
                    id, timestamp, source, title, summary, link,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    credit_terms, yields, basis_points
                FROM news_sentiment
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ? HOUR
                ORDER BY timestamp DESC
                LIMIT ?
            """, [hours, limit]).fetchall()

            # Convert to list of dictionaries
            columns = ['id', 'timestamp', 'source', 'title', 'summary', 'link',
                      'sentiment_score', 'sentiment_label', 'confidence',
                      'fed_officials', 'economic_indicators', 'treasury_instruments',
                      'credit_terms', 'yields', 'basis_points']
            
            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Failed to retrieve recent news: {e}")
            return []

    # === Market Data Operations ===

    def insert_market_data(self, data: Dict[str, Any]) -> int:
        """
        Insert market data point (yield, ETF price, etc.).
        
        Args:
            data: Dictionary containing:
                - timestamp, instrument, instrument_type
                - price, yield, volume
                - change_1h, change_4h, change_1d
                
        Returns:
            ID of inserted row
        """
        try:
            result = self.conn.execute("""
                INSERT INTO market_data (
                    timestamp, instrument, instrument_type,
                    price, yield, volume,
                    change_1h, change_4h, change_1d
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, [
                data.get('timestamp', datetime.now(timezone.utc)),
                data['instrument'],
                data['instrument_type'],
                data.get('price'),
                data.get('yield'),
                data.get('volume'),
                data.get('change_1h'),
                data.get('change_4h'),
                data.get('change_1d'),
            ]).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to insert market data: {e}")
            raise

    def bulk_insert_market_data(self, data_points: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple market data points.
        
        Args:
            data_points: List of market data dictionaries
            
        Returns:
            Number of data points inserted
        """
        if not data_points:
            return 0

        try:
            data = []
            for point in data_points:
                data.append([
                    point.get('timestamp', datetime.now(timezone.utc)),
                    point['instrument'],
                    point['instrument_type'],
                    point.get('price'),
                    point.get('yield'),
                    point.get('volume'),
                    point.get('change_1h'),
                    point.get('change_4h'),
                    point.get('change_1d'),
                ])

            self.conn.executemany("""
                INSERT INTO market_data (
                    timestamp, instrument, instrument_type,
                    price, yield, volume,
                    change_1h, change_4h, change_1d
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            logger.info(f"Bulk inserted {len(data_points)} market data points")
            return len(data_points)

        except Exception as e:
            logger.error(f"Failed to bulk insert market data: {e}")
            raise

    def get_latest_market_data(self, instrument: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get latest market data for instrument(s).
        
        Args:
            instrument: Specific instrument code, or None for all
            
        Returns:
            List of market data dictionaries
        """
        try:
            if instrument:
                result = self.conn.execute("""
                    SELECT 
                        id, timestamp, instrument, instrument_type,
                        price, yield, volume, change_1h, change_4h, change_1d
                    FROM market_data
                    WHERE instrument = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, [instrument]).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT ON (instrument)
                        id, timestamp, instrument, instrument_type,
                        price, yield, volume, change_1h, change_4h, change_1d
                    FROM market_data
                    ORDER BY instrument, timestamp DESC
                """).fetchall()

            columns = ['id', 'timestamp', 'instrument', 'instrument_type',
                      'price', 'yield', 'volume', 'change_1h', 'change_4h', 'change_1d']
            
            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Failed to retrieve market data: {e}")
            return []

    # === Sentiment Aggregation ===

    def compute_sentiment_aggregates(self, hours_back: int = 24) -> int:
        """
        Compute hourly sentiment aggregates from raw news data.
        
        Args:
            hours_back: How far back to aggregate
            
        Returns:
            Number of aggregate rows created
        """
        try:
            self.conn.execute("""
                INSERT INTO sentiment_aggregates (
                    timestamp, avg_sentiment, sentiment_count,
                    risk_on_count, risk_off_count, neutral_count,
                    has_fomc, has_cpi, has_nfp, has_fed_speaker
                )
                SELECT 
                    date_trunc('hour', timestamp) as hour,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as sentiment_count,
                    SUM(CASE WHEN sentiment_label = 'risk-on' THEN 1 ELSE 0 END) as risk_on_count,
                    SUM(CASE WHEN sentiment_label = 'risk-off' THEN 1 ELSE 0 END) as risk_off_count,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                    MAX(CASE WHEN 'FOMC' = ANY(economic_indicators) THEN 1 ELSE 0 END)::BOOLEAN as has_fomc,
                    MAX(CASE WHEN 'CPI' = ANY(economic_indicators) THEN 1 ELSE 0 END)::BOOLEAN as has_cpi,
                    MAX(CASE WHEN 'NFP' = ANY(economic_indicators) THEN 1 ELSE 0 END)::BOOLEAN as has_nfp,
                    MAX(CASE WHEN array_length(fed_officials) > 0 THEN 1 ELSE 0 END)::BOOLEAN as has_fed_speaker
                FROM news_sentiment
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ? HOUR
                    AND NOT EXISTS (
                        SELECT 1 FROM sentiment_aggregates sa 
                        WHERE sa.timestamp = date_trunc('hour', news_sentiment.timestamp)
                    )
                GROUP BY hour
            """, [hours_back])

            count = self.conn.execute("SELECT changes()").fetchone()[0]
            logger.info(f"Computed {count} sentiment aggregates")
            return count

        except Exception as e:
            logger.error(f"Failed to compute sentiment aggregates: {e}")
            return 0

    # === Query Helpers ===

    def execute_query(self, query: str, params: Optional[List] = None) -> List[tuple]:
        """
        Execute arbitrary SQL query and return results.
        
        Args:
            query: SQL query string
            params: Optional parameters for parameterized query
            
        Returns:
            List of result tuples
        """
        try:
            if params:
                return self.conn.execute(query, params).fetchall()
            else:
                return self.conn.execute(query).fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with table counts and date ranges
        """
        try:
            stats = {}
            
            # News count
            stats['news_count'] = self.conn.execute(
                "SELECT COUNT(*) FROM news_sentiment"
            ).fetchone()[0]
            
            # Market data count
            stats['market_data_count'] = self.conn.execute(
                "SELECT COUNT(*) FROM market_data"
            ).fetchone()[0]
            
            # Date ranges
            news_range = self.conn.execute("""
                SELECT MIN(timestamp), MAX(timestamp) FROM news_sentiment
            """).fetchone()
            stats['news_date_range'] = {
                'min': news_range[0],
                'max': news_range[1]
            } if news_range[0] else None
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: str = "database/fixed_income.duckdb") -> DatabaseManager:
    """
    Get or create the global database manager instance.
    
    Args:
        db_path: Path to DuckDB database file
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager

