"""
Integration layer for pushing sentiment data to quant-sql-warehouse DuckDB.
Connects the fixed-income news summarizer with the centralized data warehouse.
"""

import duckdb
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WarehouseIntegration:
    """
    Manages data flow from fixed-income news summarizer to quant-sql-warehouse.
    """

    def __init__(self, warehouse_path: str = None):
        """
        Initialize connection to quant warehouse.

        Args:
            warehouse_path: Path to warehouse.duckdb file
        """
        if warehouse_path is None:
            # Default to sibling directory structure
            # From fixed-income-news-summarizer/squawk/warehouse_integration.py
            # Go up to fixed-income-news-summarizer/, then to downloads/, then to quant-sql-warehouse/
            default_path = (
                Path(__file__).parent.parent
                / ".."
                / "quant-sql-warehouse"
                / "warehouse.duckdb"
            )
            warehouse_path = default_path.resolve()

        self.warehouse_path = Path(warehouse_path)
        self.conn = None

        if not self.warehouse_path.exists():
            logger.warning(f"Warehouse database not found at {self.warehouse_path}")
            logger.info("Will create new database when inserting data")

        self._connect()
        self._ensure_schema()

    def _connect(self):
        """Establish connection to warehouse database."""
        try:
            self.conn = duckdb.connect(str(self.warehouse_path))
            logger.info(f"Connected to quant warehouse: {self.warehouse_path}")
        except Exception as e:
            logger.error(f"Failed to connect to warehouse: {e}")
            raise

    def _ensure_schema(self):
        """Ensure sentiment tables exist in warehouse (skip if already exist)."""
        try:
            # Check if key tables exist
            result = self.conn.execute(
                """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name IN ('news_sentiment', 'sentiment_aggregates', 'market_events', 'sentiment_signals')
                AND table_schema = 'main'
            """
            ).fetchone()

            if result and result[0] >= 4:
                logger.info("Sentiment schema already exists in warehouse")
                return

            logger.info("Sentiment tables not found, will need manual initialization")
            logger.info("Run: cd quant-sql-warehouse && python init_sentiment.py")

        except Exception as e:
            logger.error(f"Failed to check schema: {e}")

    def close(self):
        """Close warehouse connection."""
        if self.conn:
            self.conn.close()
            logger.info("Warehouse connection closed")

    # === News Sentiment Operations ===

    def insert_news_item(self, item: Dict[str, Any]) -> int:
        """
        Insert a news item with sentiment into warehouse.

        Args:
            item: Dictionary containing:
                - timestamp, source, title, summary, link
                - sentiment_score, sentiment_label, confidence
                - entities (dict)

        Returns:
            news_id of inserted row
        """
        try:
            entities = item.get("entities", {})

            # Check if high-impact
            is_high_impact = self._is_high_impact(entities)

            result = self.conn.execute(
                """
                INSERT INTO news_sentiment (
                    timestamp, source, title, summary, link,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    credit_terms, yields, basis_points, is_high_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING news_id
            """,
                [
                    item.get("timestamp", datetime.now(timezone.utc)),
                    item["source"],
                    item["title"],
                    item.get("summary", ""),
                    item.get("link", ""),
                    item["sentiment_score"],
                    item["sentiment_label"],
                    item.get("confidence", 0.0),
                    entities.get("fed_officials", []),
                    entities.get("economic_indicators", []),
                    entities.get("treasury_instruments", []),
                    entities.get("credit_terms", []),
                    entities.get("yields", []),
                    entities.get("basis_points", []),
                    is_high_impact,
                ],
            ).fetchone()

            logger.debug(f"Inserted news item: {item['title'][:50]}...")
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to insert news item: {e}")
            raise

    def bulk_insert_news(self, items: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple news items.

        Args:
            items: List of news item dictionaries

        Returns:
            Number of items inserted
        """
        if not items:
            return 0

        try:
            data = []
            for item in items:
                entities = item.get("entities", {})
                is_high_impact = self._is_high_impact(entities)

                data.append(
                    [
                        item.get("timestamp", datetime.now(timezone.utc)),
                        item["source"],
                        item["title"],
                        item.get("summary", ""),
                        item.get("link", ""),
                        item["sentiment_score"],
                        item["sentiment_label"],
                        item.get("confidence", 0.0),
                        entities.get("fed_officials", []),
                        entities.get("economic_indicators", []),
                        entities.get("treasury_instruments", []),
                        entities.get("credit_terms", []),
                        entities.get("yields", []),
                        entities.get("basis_points", []),
                        is_high_impact,
                    ]
                )

            self.conn.executemany(
                """
                INSERT INTO news_sentiment (
                    timestamp, source, title, summary, link,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, treasury_instruments,
                    credit_terms, yields, basis_points, is_high_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

            logger.info(f"Bulk inserted {len(items)} news items to warehouse")
            return len(items)

        except Exception as e:
            logger.error(f"Failed to bulk insert news: {e}")
            raise

    def _is_high_impact(self, entities: Dict[str, List[str]]) -> bool:
        """Determine if news is high-impact based on entities."""
        high_impact_indicators = {"FOMC", "CPI", "NFP", "PCE"}
        high_impact_officials = {"Jerome Powell", "Powell", "Chair Powell"}

        has_indicator = any(
            ind in entities.get("economic_indicators", [])
            for ind in high_impact_indicators
        )
        has_official = any(
            off in entities.get("fed_officials", []) for off in high_impact_officials
        )

        return has_indicator or has_official

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
            # Use string formatting for INTERVAL since parameterized queries don't work well with it
            query = f"""
                INSERT INTO sentiment_aggregates (
                    hour_timestamp, avg_sentiment, sentiment_count,
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
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours_back}' HOUR
                    AND NOT EXISTS (
                        SELECT 1 FROM sentiment_aggregates sa 
                        WHERE sa.hour_timestamp = date_trunc('hour', news_sentiment.timestamp)
                    )
                GROUP BY hour
            """

            result = self.conn.execute(query)
            # DuckDB doesn't have changes(), so we count the aggregates we just created
            count_result = self.conn.execute(
                """
                SELECT COUNT(*) FROM sentiment_aggregates
            """
            ).fetchone()
            count = count_result[0] if count_result else 0
            logger.info(f"Computed sentiment aggregates (total: {count})")
            return count

        except Exception as e:
            logger.error(f"Failed to compute aggregates: {e}")
            return 0

    # === Query Helpers ===

    def get_recent_news(
        self, hours: int = 24, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent news from warehouse."""
        try:
            query = f"""
                SELECT 
                    news_id, timestamp, source, title, summary,
                    sentiment_score, sentiment_label, confidence,
                    fed_officials, economic_indicators, is_high_impact
                FROM news_sentiment
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours}' HOUR
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            result = self.conn.execute(query).fetchdf()

            return result.to_dict("records")
        except Exception as e:
            logger.error(f"Failed to retrieve recent news: {e}")
            return []

    def get_sentiment_timeseries(self, hours: int = 168) -> List[Dict[str, Any]]:
        """Get hourly sentiment aggregates."""
        try:
            query = f"""
                SELECT 
                    hour_timestamp,
                    avg_sentiment,
                    sentiment_count,
                    risk_on_count,
                    risk_off_count,
                    neutral_count
                FROM sentiment_aggregates
                WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours}' HOUR
                ORDER BY hour_timestamp DESC
            """
            result = self.conn.execute(query).fetchdf()

            return result.to_dict("records")
        except Exception as e:
            logger.error(f"Failed to retrieve sentiment timeseries: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get warehouse statistics."""
        try:
            stats = {}

            # News count
            result = self.conn.execute("SELECT COUNT(*) FROM news_sentiment").fetchone()
            stats["news_count"] = result[0] if result else 0

            # Date range
            result = self.conn.execute(
                """
                SELECT MIN(timestamp), MAX(timestamp) FROM news_sentiment
            """
            ).fetchone()
            if result and result[0]:
                stats["news_date_range"] = {"min": result[0], "max": result[1]}

            # High-impact count
            result = self.conn.execute(
                """
                SELECT COUNT(*) FROM news_sentiment WHERE is_high_impact = TRUE
            """
            ).fetchone()
            stats["high_impact_count"] = result[0] if result else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Global warehouse integration instance
_warehouse: Optional[WarehouseIntegration] = None


def get_warehouse(warehouse_path: str = None) -> WarehouseIntegration:
    """
    Get or create the global warehouse integration instance.

    Args:
        warehouse_path: Optional path to warehouse.duckdb

    Returns:
        WarehouseIntegration instance
    """
    global _warehouse
    if _warehouse is None:
        _warehouse = WarehouseIntegration(warehouse_path)
    return _warehouse
