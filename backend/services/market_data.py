"""
Market data fetching for Treasury yields and fixed-income ETFs.
Supports FRED API for official Treasury yields and Yahoo Finance for ETFs.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import requests
import time

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from fredapi import Fred
except ImportError:
    Fred = None

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetches Treasury yields and fixed-income ETF data from various sources.
    """

    # FRED series IDs for Treasury yields
    FRED_SERIES = {
        "US2Y": "DGS2",  # 2-Year Treasury
        "US5Y": "DGS5",  # 5-Year Treasury
        "US10Y": "DGS10",  # 10-Year Treasury
        "US30Y": "DGS30",  # 30-Year Treasury
    }

    # Fixed-income ETFs to track
    ETF_TICKERS = {
        "TLT": "20+ Year Treasury Bond ETF",
        "IEF": "7-10 Year Treasury Bond ETF",
        "SHY": "1-3 Year Treasury Bond ETF",
        "LQD": "Investment Grade Corporate Bond ETF",
        "HYG": "High Yield Corporate Bond ETF",
    }

    def __init__(self, fred_api_key: Optional[str] = None):
        """
        Initialize market data fetcher.

        Args:
            fred_api_key: FRED API key (or uses FRED_API_KEY env var)
        """
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self.fred_client = None

        if self.fred_api_key and Fred is not None:
            try:
                self.fred_client = Fred(api_key=self.fred_api_key)
                logger.info("FRED API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize FRED client: {e}")
        else:
            logger.warning(
                "FRED API not available. Set FRED_API_KEY environment variable."
            )

    def fetch_treasury_yields(self) -> List[Dict[str, Any]]:
        """
        Fetch current Treasury yields from FRED.

        Returns:
            List of dictionaries with yield data for each maturity
        """
        if not self.fred_client:
            logger.warning("FRED client not available, cannot fetch Treasury yields")
            return []

        results = []
        timestamp = datetime.now(timezone.utc)

        for instrument, series_id in self.FRED_SERIES.items():
            try:
                # Get most recent data point
                series = self.fred_client.get_series(series_id, limit=10)

                if series.empty:
                    logger.warning(f"No data available for {instrument}")
                    continue

                # Get the most recent non-null value
                latest_yield = None
                for idx in range(len(series) - 1, -1, -1):
                    if not pd.isna(series.iloc[idx]):
                        latest_yield = float(series.iloc[idx])
                        break

                if latest_yield is None:
                    logger.warning(f"No valid data for {instrument}")
                    continue

                # Calculate changes (fetch historical data)
                try:
                    hist = self.fred_client.get_series(
                        series_id, observation_start=datetime.now() - timedelta(days=7)
                    )

                    change_1d = None
                    if len(hist) >= 2:
                        prev_yield = (
                            float(hist.iloc[-2]) if not pd.isna(hist.iloc[-2]) else None
                        )
                        if prev_yield:
                            change_1d = latest_yield - prev_yield
                except Exception as e:
                    logger.warning(f"Could not calculate changes for {instrument}: {e}")
                    change_1d = None

                results.append(
                    {
                        "timestamp": timestamp,
                        "instrument": instrument,
                        "instrument_type": "yield",
                        "yield": latest_yield,
                        "price": None,
                        "volume": None,
                        "change_1h": None,  # FRED data is daily, no intraday
                        "change_4h": None,
                        "change_1d": change_1d,
                    }
                )

                logger.info(f"Fetched {instrument}: {latest_yield}%")

            except Exception as e:
                logger.error(f"Failed to fetch {instrument} from FRED: {e}")
                continue

            # Rate limit
            time.sleep(0.1)

        return results

    def fetch_etf_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fixed-income ETF data from Yahoo Finance.

        Returns:
            List of dictionaries with ETF price and volume data
        """
        if yf is None:
            logger.warning("yfinance not available, cannot fetch ETF data")
            return []

        results = []
        timestamp = datetime.now(timezone.utc)

        for ticker, description in self.ETF_TICKERS.items():
            try:
                etf = yf.Ticker(ticker)

                # Get current price and recent history
                hist = etf.history(period="5d", interval="1d")

                if hist.empty:
                    logger.warning(f"No data available for {ticker}")
                    continue

                latest = hist.iloc[-1]
                price = float(latest["Close"])
                volume = int(latest["Volume"])

                # Calculate changes
                change_1d = None
                if len(hist) >= 2:
                    prev_price = float(hist.iloc[-2]["Close"])
                    change_1d = (
                        (price - prev_price) / prev_price
                    ) * 100  # Percent change

                # Get intraday data for hourly changes if available
                change_1h = None
                change_4h = None
                try:
                    intraday = etf.history(period="1d", interval="1h")
                    if not intraday.empty and len(intraday) >= 2:
                        hour_ago_price = float(intraday.iloc[-2]["Close"])
                        change_1h = ((price - hour_ago_price) / hour_ago_price) * 100

                        if len(intraday) >= 5:
                            four_hours_ago_price = float(intraday.iloc[-5]["Close"])
                            change_4h = (
                                (price - four_hours_ago_price) / four_hours_ago_price
                            ) * 100
                except Exception as e:
                    logger.debug(f"Could not get intraday data for {ticker}: {e}")

                results.append(
                    {
                        "timestamp": timestamp,
                        "instrument": ticker,
                        "instrument_type": "etf",
                        "price": price,
                        "yield": None,
                        "volume": volume,
                        "change_1h": change_1h,
                        "change_4h": change_4h,
                        "change_1d": change_1d,
                    }
                )

                logger.info(f"Fetched {ticker}: ${price:.2f}, volume {volume:,}")

            except Exception as e:
                logger.error(f"Failed to fetch {ticker} from Yahoo Finance: {e}")
                continue

            # Rate limit
            time.sleep(0.2)

        return results

    def fetch_all(self) -> List[Dict[str, Any]]:
        """
        Fetch all market data (Treasury yields + ETFs).

        Returns:
            Combined list of all market data points
        """
        all_data = []

        # Fetch Treasury yields
        yields = self.fetch_treasury_yields()
        all_data.extend(yields)

        # Fetch ETF data
        etfs = self.fetch_etf_data()
        all_data.extend(etfs)

        logger.info(f"Fetched total {len(all_data)} market data points")
        return all_data

    def fetch_historical(
        self, instrument: str, days_back: int = 30, instrument_type: str = "yield"
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical data for backtesting and analysis.

        Args:
            instrument: Instrument code (e.g., 'US10Y', 'TLT')
            days_back: Number of days of history to fetch
            instrument_type: 'yield' or 'etf'

        Returns:
            List of historical data points
        """
        results = []

        if instrument_type == "yield" and self.fred_client:
            try:
                series_id = self.FRED_SERIES.get(instrument)
                if not series_id:
                    logger.error(f"Unknown yield instrument: {instrument}")
                    return []

                start_date = datetime.now() - timedelta(days=days_back)
                series = self.fred_client.get_series(
                    series_id, observation_start=start_date
                )

                for date, value in series.items():
                    if pd.isna(value):
                        continue

                    results.append(
                        {
                            "timestamp": datetime.combine(
                                date, datetime.min.time()
                            ).replace(tzinfo=timezone.utc),
                            "instrument": instrument,
                            "instrument_type": "yield",
                            "yield": float(value),
                            "price": None,
                            "volume": None,
                            "change_1h": None,
                            "change_4h": None,
                            "change_1d": None,
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to fetch historical yields for {instrument}: {e}")

        elif instrument_type == "etf" and yf is not None:
            try:
                if instrument not in self.ETF_TICKERS:
                    logger.error(f"Unknown ETF: {instrument}")
                    return []

                etf = yf.Ticker(instrument)
                hist = etf.history(period=f"{days_back}d", interval="1d")

                for date, row in hist.iterrows():
                    results.append(
                        {
                            "timestamp": date.to_pydatetime().replace(
                                tzinfo=timezone.utc
                            ),
                            "instrument": instrument,
                            "instrument_type": "etf",
                            "price": float(row["Close"]),
                            "yield": None,
                            "volume": int(row["Volume"]),
                            "change_1h": None,
                            "change_4h": None,
                            "change_1d": None,
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Failed to fetch historical ETF data for {instrument}: {e}"
                )

        logger.info(f"Fetched {len(results)} historical data points for {instrument}")
        return results


# Import pandas for FRED data handling
try:
    import pandas as pd
except ImportError:
    pd = None
    logger.warning("pandas not available, some market data functions may not work")


# Global fetcher instance
_fetcher: Optional[MarketDataFetcher] = None


def get_fetcher(fred_api_key: Optional[str] = None) -> MarketDataFetcher:
    """
    Get or create the global market data fetcher instance.

    Args:
        fred_api_key: Optional FRED API key

    Returns:
        MarketDataFetcher instance
    """
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher(fred_api_key)
    return _fetcher


def fetch_market_data(fred_api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch all current market data.

    Args:
        fred_api_key: Optional FRED API key

    Returns:
        List of market data dictionaries
    """
    fetcher = get_fetcher(fred_api_key)
    return fetcher.fetch_all()
