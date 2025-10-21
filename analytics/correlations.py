"""
Lead-lag correlation analysis between news sentiment and Treasury yields.
Analyzes how sentiment predicts future yield movements.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes correlations between sentiment scores and yield changes.
    Supports lead-lag analysis to identify predictive relationships.
    """

    def __init__(self, db_manager):
        """
        Initialize correlation analyzer.

        Args:
            db_manager: DatabaseManager instance for data queries
        """
        self.db = db_manager

    def get_sentiment_timeseries(
        self, start_date: datetime, end_date: datetime, freq: str = "1H"
    ) -> pd.DataFrame:
        """
        Get sentiment time series data from database.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            freq: Frequency for resampling ('1H', '4H', '1D')

        Returns:
            DataFrame with timestamp and avg_sentiment columns
        """
        try:
            # Query sentiment aggregates
            query = """
                SELECT timestamp, avg_sentiment, sentiment_count
                FROM sentiment_aggregates
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """

            results = self.db.execute_query(query, [start_date, end_date])

            if not results:
                logger.warning("No sentiment data found for specified period")
                return pd.DataFrame(columns=["timestamp", "avg_sentiment"])

            df = pd.DataFrame(
                results, columns=["timestamp", "avg_sentiment", "sentiment_count"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")

            # Resample if needed
            if freq != "1H":
                df = df.resample(freq).agg(
                    {"avg_sentiment": "mean", "sentiment_count": "sum"}
                )

            return df.reset_index()

        except Exception as e:
            logger.error(f"Failed to get sentiment timeseries: {e}")
            return pd.DataFrame()

    def get_yield_timeseries(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        freq: str = "1H",
    ) -> pd.DataFrame:
        """
        Get yield/price time series data from database.

        Args:
            instrument: Instrument code (e.g., 'US10Y', 'TLT')
            start_date: Start of analysis period
            end_date: End of analysis period
            freq: Frequency for resampling

        Returns:
            DataFrame with timestamp and value columns
        """
        try:
            query = """
                SELECT timestamp, yield, price
                FROM market_data
                WHERE instrument = ?
                    AND timestamp >= ?
                    AND timestamp <= ?
                ORDER BY timestamp
            """

            results = self.db.execute_query(query, [instrument, start_date, end_date])

            if not results:
                logger.warning(f"No market data found for {instrument}")
                return pd.DataFrame(columns=["timestamp", "value"])

            df = pd.DataFrame(results, columns=["timestamp", "yield", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Use yield for Treasury instruments, price for ETFs
            df["value"] = df["yield"] if instrument.startswith("US") else df["price"]
            df = df[["timestamp", "value"]].dropna()
            df = df.set_index("timestamp")

            # Resample and forward-fill
            if freq != "1H":
                df = df.resample(freq).mean().ffill()

            return df.reset_index()

        except Exception as e:
            logger.error(f"Failed to get yield timeseries: {e}")
            return pd.DataFrame()

    def calculate_lead_lag_correlation(
        self,
        sentiment_df: pd.DataFrame,
        yield_df: pd.DataFrame,
        lag_hours: List[int] = [1, 4, 24],
    ) -> List[Dict[str, any]]:
        """
        Calculate correlations with various time lags.
        Tests if sentiment at time t correlates with yield change at t+lag.

        Args:
            sentiment_df: Sentiment time series
            yield_df: Yield/price time series
            lag_hours: List of lag periods to test (in hours)

        Returns:
            List of correlation results with statistics
        """
        results = []

        # Merge datasets on timestamp
        merged = pd.merge(
            sentiment_df,
            yield_df,
            on="timestamp",
            how="inner",
            suffixes=("_sentiment", "_yield"),
        )

        if len(merged) < 10:
            logger.warning("Insufficient data for correlation analysis")
            return results

        # Calculate yield changes for each lag
        for lag in lag_hours:
            try:
                # Shift yield values forward by lag periods
                merged[f"yield_change_{lag}h"] = (
                    merged["value"].shift(-lag) - merged["value"]
                )

                # Remove rows with NaN
                analysis_df = merged[["avg_sentiment", f"yield_change_{lag}h"]].dropna()

                if len(analysis_df) < 10:
                    logger.warning(f"Insufficient data for {lag}h lag")
                    continue

                # Calculate Pearson correlation
                corr, p_value = stats.pearsonr(
                    analysis_df["avg_sentiment"], analysis_df[f"yield_change_{lag}h"]
                )

                # Calculate Spearman (rank) correlation for robustness
                spearman_corr, spearman_p = stats.spearmanr(
                    analysis_df["avg_sentiment"], analysis_df[f"yield_change_{lag}h"]
                )

                results.append(
                    {
                        "lag_hours": lag,
                        "correlation": corr,
                        "p_value": p_value,
                        "spearman_correlation": spearman_corr,
                        "spearman_p_value": spearman_p,
                        "sample_size": len(analysis_df),
                        "significant": p_value < 0.05,
                    }
                )

                logger.info(
                    f"Lag {lag}h: corr={corr:.3f}, p={p_value:.4f}, "
                    f"n={len(analysis_df)}, significant={p_value < 0.05}"
                )

            except Exception as e:
                logger.error(f"Error calculating correlation for {lag}h lag: {e}")
                continue

        return results

    def rolling_correlation(
        self,
        instrument: str,
        window_days: int = 30,
        lag_hours: int = 4,
        lookback_days: int = 180,
    ) -> pd.DataFrame:
        """
        Calculate rolling correlation over time to see relationship stability.

        Args:
            instrument: Market instrument to analyze
            window_days: Rolling window size
            lag_hours: Lag to use for correlation
            lookback_days: Total period to analyze

        Returns:
            DataFrame with timestamp and rolling_correlation columns
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=lookback_days)

            # Get data
            sentiment_df = self.get_sentiment_timeseries(
                start_date, end_date, freq="4H"
            )
            yield_df = self.get_yield_timeseries(
                instrument, start_date, end_date, freq="4H"
            )

            # Merge
            merged = pd.merge(sentiment_df, yield_df, on="timestamp", how="inner")
            merged["yield_change"] = (
                merged["value"].shift(-lag_hours // 4) - merged["value"]
            )

            merged = merged.dropna()
            merged = merged.set_index("timestamp")

            # Calculate rolling correlation
            window_periods = window_days * 6  # 6 periods per day at 4H frequency

            rolling_corr = (
                merged["avg_sentiment"]
                .rolling(window=window_periods, min_periods=window_periods // 2)
                .corr(merged["yield_change"])
            )

            result_df = pd.DataFrame(
                {
                    "timestamp": rolling_corr.index,
                    "rolling_correlation": rolling_corr.values,
                }
            )

            return result_df.dropna()

        except Exception as e:
            logger.error(f"Failed to calculate rolling correlation: {e}")
            return pd.DataFrame()

    def correlation_by_sentiment_strength(
        self, instrument: str, lag_hours: int = 4, lookback_days: int = 90
    ) -> Dict[str, Dict]:
        """
        Analyze if correlation is stronger for high-confidence or extreme sentiment.

        Args:
            instrument: Market instrument
            lag_hours: Prediction lag
            lookback_days: Analysis period

        Returns:
            Dictionary with correlation stats for different sentiment buckets
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=lookback_days)

            sentiment_df = self.get_sentiment_timeseries(start_date, end_date)
            yield_df = self.get_yield_timeseries(instrument, start_date, end_date)

            merged = pd.merge(sentiment_df, yield_df, on="timestamp", how="inner")
            merged["yield_change"] = merged["value"].shift(-lag_hours) - merged["value"]
            merged = merged.dropna()

            # Define sentiment buckets
            results = {}

            # All data
            corr, p_val = stats.pearsonr(
                merged["avg_sentiment"], merged["yield_change"]
            )
            results["all"] = {
                "correlation": corr,
                "p_value": p_val,
                "sample_size": len(merged),
            }

            # Strong positive sentiment (top 25%)
            threshold_high = merged["avg_sentiment"].quantile(0.75)
            strong_positive = merged[merged["avg_sentiment"] >= threshold_high]
            if len(strong_positive) >= 10:
                corr, p_val = stats.pearsonr(
                    strong_positive["avg_sentiment"], strong_positive["yield_change"]
                )
                results["strong_positive"] = {
                    "correlation": corr,
                    "p_value": p_val,
                    "sample_size": len(strong_positive),
                }

            # Strong negative sentiment (bottom 25%)
            threshold_low = merged["avg_sentiment"].quantile(0.25)
            strong_negative = merged[merged["avg_sentiment"] <= threshold_low]
            if len(strong_negative) >= 10:
                corr, p_val = stats.pearsonr(
                    strong_negative["avg_sentiment"], strong_negative["yield_change"]
                )
                results["strong_negative"] = {
                    "correlation": corr,
                    "p_value": p_val,
                    "sample_size": len(strong_negative),
                }

            # Extreme sentiment (top and bottom 10%)
            extreme = merged[
                (merged["avg_sentiment"] >= merged["avg_sentiment"].quantile(0.9))
                | (merged["avg_sentiment"] <= merged["avg_sentiment"].quantile(0.1))
            ]
            if len(extreme) >= 10:
                corr, p_val = stats.pearsonr(
                    extreme["avg_sentiment"], extreme["yield_change"]
                )
                results["extreme"] = {
                    "correlation": corr,
                    "p_value": p_val,
                    "sample_size": len(extreme),
                }

            return results

        except Exception as e:
            logger.error(f"Failed to analyze correlation by sentiment strength: {e}")
            return {}

    def run_full_analysis(
        self, instrument: str = "US10Y", lookback_days: int = 90
    ) -> Dict[str, any]:
        """
        Run comprehensive correlation analysis.

        Args:
            instrument: Market instrument to analyze
            lookback_days: Analysis period

        Returns:
            Dictionary containing all analysis results
        """
        logger.info(f"Starting full correlation analysis for {instrument}")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)

        # Get data
        sentiment_df = self.get_sentiment_timeseries(start_date, end_date, freq="1H")
        yield_df = self.get_yield_timeseries(
            instrument, start_date, end_date, freq="1H"
        )

        if sentiment_df.empty or yield_df.empty:
            logger.error("Insufficient data for analysis")
            return {}

        # Lead-lag correlations
        lead_lag = self.calculate_lead_lag_correlation(
            sentiment_df, yield_df, lag_hours=[1, 4, 8, 24, 48]
        )

        # Rolling correlation
        rolling = self.rolling_correlation(instrument, window_days=30, lag_hours=4)

        # Sentiment strength analysis
        by_strength = self.correlation_by_sentiment_strength(instrument, lag_hours=4)

        results = {
            "instrument": instrument,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": lookback_days,
            },
            "lead_lag_correlations": lead_lag,
            "rolling_correlation": (
                rolling.to_dict("records") if not rolling.empty else []
            ),
            "by_sentiment_strength": by_strength,
            "summary": self._generate_summary(lead_lag, by_strength),
        }

        logger.info("Correlation analysis complete")
        return results

    def _generate_summary(
        self, lead_lag: List[Dict], by_strength: Dict
    ) -> Dict[str, str]:
        """Generate human-readable summary of findings."""
        summary = {}

        # Find strongest correlation
        if lead_lag:
            best_lag = max(lead_lag, key=lambda x: abs(x["correlation"]))
            summary["best_lag"] = (
                f"{best_lag['lag_hours']}h lag shows correlation of {best_lag['correlation']:.3f} "
                f"(p={best_lag['p_value']:.4f})"
            )

        # Sentiment strength effect
        if "all" in by_strength and "extreme" in by_strength:
            all_corr = by_strength["all"]["correlation"]
            extreme_corr = by_strength["extreme"]["correlation"]
            if abs(extreme_corr) > abs(all_corr):
                summary["strength_effect"] = (
                    f"Extreme sentiment shows stronger correlation ({extreme_corr:.3f}) "
                    f"vs all data ({all_corr:.3f})"
                )

        return summary
