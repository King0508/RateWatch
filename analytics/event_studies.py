"""
Event study analysis for measuring market impact of high-sentiment news.
Analyzes abnormal yield movements around major economic events.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class EventStudyAnalyzer:
    """
    Conducts event studies to measure market impact of high-sentiment news events.
    """

    def __init__(self, db_manager):
        """
        Initialize event study analyzer.

        Args:
            db_manager: DatabaseManager or WarehouseIntegration instance
        """
        self.db = db_manager

    def identify_high_impact_events(
        self,
        start_date: datetime,
        end_date: datetime,
        min_sentiment_threshold: float = 0.5,
    ) -> pd.DataFrame:
        """
        Identify high-impact news events for analysis.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            min_sentiment_threshold: Minimum abs(sentiment) to be considered impactful

        Returns:
            DataFrame of high-impact events
        """
        try:
            query = """
            SELECT 
                news_id,
                timestamp,
                title,
                sentiment_score,
                sentiment_label,
                confidence,
                economic_indicators,
                fed_officials,
                is_high_impact
            FROM news_sentiment
            WHERE timestamp >= ? 
                AND timestamp <= ?
                AND (ABS(sentiment_score) >= ? OR is_high_impact = TRUE)
            ORDER BY timestamp
            """

            results = self.db.execute_query(
                query, [start_date, end_date, min_sentiment_threshold]
            )

            if not results:
                logger.warning("No high-impact events found")
                return pd.DataFrame()

            df = pd.DataFrame(
                results,
                columns=[
                    "news_id",
                    "timestamp",
                    "title",
                    "sentiment_score",
                    "sentiment_label",
                    "confidence",
                    "economic_indicators",
                    "fed_officials",
                    "is_high_impact",
                ],
            )

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

        except Exception as e:
            logger.error(f"Failed to identify high-impact events: {e}")
            return pd.DataFrame()

    def measure_market_impact(
        self,
        event_timestamp: datetime,
        instrument: str = "US10Y",
        window_hours: int = 24,
    ) -> Dict[str, float]:
        """
        Measure market impact around a specific event.

        Args:
            event_timestamp: Time of the news event
            instrument: Market instrument to analyze
            window_hours: Hours before/after to analyze

        Returns:
            Dictionary with impact metrics
        """
        try:
            # Get market data around event
            start_time = event_timestamp - timedelta(hours=window_hours)
            end_time = event_timestamp + timedelta(hours=window_hours)

            query = """
            SELECT timestamp, yield, price
            FROM market_data
            WHERE instrument = ?
                AND timestamp >= ?
                AND timestamp <= ?
            ORDER BY timestamp
            """

            results = self.db.execute_query(query, [instrument, start_time, end_time])

            if not results or len(results) < 4:
                logger.warning(f"Insufficient market data around {event_timestamp}")
                return {}

            df = pd.DataFrame(results, columns=["timestamp", "yield", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["value"] = df["yield"] if instrument.startswith("US") else df["price"]

            # Find data points closest to event
            df["time_diff"] = abs(
                (df["timestamp"] - event_timestamp).dt.total_seconds()
            )
            event_idx = df["time_diff"].idxmin()

            if event_idx == 0 or event_idx == len(df) - 1:
                logger.warning("Event at boundary of data")
                return {}

            # Calculate pre and post event values
            pre_event = df[df.index < event_idx]["value"].mean()
            post_event = df[df.index > event_idx]["value"].mean()
            event_value = df.loc[event_idx, "value"]

            # Calculate changes
            abs_change = post_event - pre_event
            pct_change = (abs_change / pre_event) * 100 if pre_event != 0 else 0

            # Calculate volatility
            pre_volatility = df[df.index < event_idx]["value"].std()
            post_volatility = df[df.index > event_idx]["value"].std()

            return {
                "pre_event_value": pre_event,
                "event_value": event_value,
                "post_event_value": post_event,
                "absolute_change": abs_change,
                "percent_change": pct_change,
                "pre_volatility": pre_volatility,
                "post_volatility": post_volatility,
                "volatility_ratio": (
                    post_volatility / pre_volatility if pre_volatility != 0 else 1.0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to measure market impact: {e}")
            return {}

    def conduct_event_study(
        self,
        start_date: datetime,
        end_date: datetime,
        instrument: str = "US10Y",
        window_hours: int = 12,
        min_sentiment: float = 0.5,
    ) -> pd.DataFrame:
        """
        Conduct comprehensive event study across multiple events.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            instrument: Market instrument to analyze
            window_hours: Hours before/after event to analyze
            min_sentiment: Minimum sentiment threshold

        Returns:
            DataFrame with event study results
        """
        logger.info(f"Conducting event study from {start_date} to {end_date}")

        # Identify events
        events_df = self.identify_high_impact_events(
            start_date, end_date, min_sentiment
        )

        if events_df.empty:
            logger.warning("No events to analyze")
            return pd.DataFrame()

        results = []

        for idx, event in events_df.iterrows():
            impact = self.measure_market_impact(
                event["timestamp"], instrument, window_hours
            )

            if impact:
                results.append(
                    {
                        "news_id": event["news_id"],
                        "timestamp": event["timestamp"],
                        "title": event["title"],
                        "sentiment_score": event["sentiment_score"],
                        "sentiment_label": event["sentiment_label"],
                        "confidence": event["confidence"],
                        "is_high_impact": event["is_high_impact"],
                        **impact,
                    }
                )

        if not results:
            logger.warning("No successful impact measurements")
            return pd.DataFrame()

        results_df = pd.DataFrame(results)
        logger.info(f"Completed event study with {len(results)} events")

        return results_df

    def aggregate_impact_by_sentiment(
        self, event_study_df: pd.DataFrame
    ) -> Dict[str, Dict]:
        """
        Aggregate event study results by sentiment direction.

        Args:
            event_study_df: Results from conduct_event_study

        Returns:
            Dictionary with aggregated statistics by sentiment label
        """
        if event_study_df.empty:
            return {}

        results = {}

        for label in ["risk-on", "risk-off", "neutral"]:
            subset = event_study_df[event_study_df["sentiment_label"] == label]

            if len(subset) == 0:
                continue

            results[label] = {
                "count": len(subset),
                "avg_absolute_change": subset["absolute_change"].mean(),
                "avg_percent_change": subset["percent_change"].mean(),
                "median_percent_change": subset["percent_change"].median(),
                "avg_volatility_ratio": subset["volatility_ratio"].mean(),
                "consistent_direction": (
                    (subset["absolute_change"] > 0).sum() / len(subset) * 100
                    if label == "risk-on"
                    else (
                        (subset["absolute_change"] < 0).sum() / len(subset) * 100
                        if label == "risk-off"
                        else 50.0
                    )
                ),
            }

        return results

    def test_significance(self, event_study_df: pd.DataFrame) -> Dict[str, any]:
        """
        Test statistical significance of event impacts.

        Args:
            event_study_df: Results from conduct_event_study

        Returns:
            Dictionary with statistical test results
        """
        if event_study_df.empty or len(event_study_df) < 3:
            return {}

        try:
            # T-test: is average change significantly different from 0?
            t_stat, p_value = stats.ttest_1samp(event_study_df["percent_change"], 0)

            # ANOVA: do different sentiment labels have different impacts?
            groups = [
                event_study_df[event_study_df["sentiment_label"] == label][
                    "percent_change"
                ].values
                for label in ["risk-on", "risk-off", "neutral"]
                if len(event_study_df[event_study_df["sentiment_label"] == label]) > 0
            ]

            if len(groups) >= 2:
                f_stat, anova_p = stats.f_oneway(*groups)
            else:
                f_stat, anova_p = None, None

            return {
                "sample_size": len(event_study_df),
                "t_statistic": t_stat,
                "t_test_p_value": p_value,
                "significant_at_5pct": p_value < 0.05,
                "f_statistic": f_stat,
                "anova_p_value": anova_p,
                "sentiment_labels_differ": (
                    anova_p < 0.05 if anova_p is not None else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to test significance: {e}")
            return {}

    def run_full_event_study(
        self, lookback_days: int = 90, instrument: str = "US10Y"
    ) -> Dict[str, any]:
        """
        Run comprehensive event study analysis.

        Args:
            lookback_days: Days to analyze
            instrument: Market instrument

        Returns:
            Complete event study results
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)

        # Conduct event study
        event_study_df = self.conduct_event_study(
            start_date, end_date, instrument, window_hours=12, min_sentiment=0.4
        )

        if event_study_df.empty:
            return {"error": "No events found for analysis"}

        # Aggregate by sentiment
        aggregated = self.aggregate_impact_by_sentiment(event_study_df)

        # Statistical significance
        significance = self.test_significance(event_study_df)

        # Summary statistics
        summary = {
            "total_events": len(event_study_df),
            "avg_absolute_impact": event_study_df["absolute_change"].mean(),
            "avg_percent_impact": event_study_df["percent_change"].mean(),
            "max_impact": event_study_df["absolute_change"].abs().max(),
            "positive_impacts": (event_study_df["absolute_change"] > 0).sum(),
            "negative_impacts": (event_study_df["absolute_change"] < 0).sum(),
        }

        return {
            "instrument": instrument,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": lookback_days,
            },
            "summary": summary,
            "by_sentiment": aggregated,
            "significance_tests": significance,
            "events": (
                event_study_df.to_dict("records") if len(event_study_df) <= 100 else []
            ),
        }
