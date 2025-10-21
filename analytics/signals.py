"""
Trading signal generation and backtesting based on sentiment analysis.
Generates signals from sentiment data and tests their performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals from sentiment and market data.
    """

    def __init__(self, db_manager):
        """
        Initialize signal generator.
        
        Args:
            db_manager: DatabaseManager or WarehouseIntegration instance
        """
        self.db = db_manager

    def generate_sentiment_signals(
        self,
        start_date: datetime,
        end_date: datetime,
        instrument: str = 'TLT',
        sentiment_threshold: float = 0.3,
        aggregation_hours: int = 4
    ) -> pd.DataFrame:
        """
        Generate trading signals based on aggregated sentiment.
        
        Strategy: Strong positive sentiment → Buy TLT (yields down)
                 Strong negative sentiment → Sell TLT (yields up)
        
        Args:
            start_date: Start date for signal generation
            end_date: End date for signal generation
            instrument: Trading instrument (default TLT)
            sentiment_threshold: Threshold for signal generation
            aggregation_hours: Hours to aggregate sentiment
            
        Returns:
            DataFrame with signals
        """
        try:
            # Get sentiment aggregates
            query = """
            SELECT 
                hour_timestamp as timestamp,
                avg_sentiment,
                sentiment_count,
                has_fomc,
                has_cpi,
                has_nfp
            FROM sentiment_aggregates
            WHERE hour_timestamp >= ? AND hour_timestamp <= ?
            ORDER BY hour_timestamp
            """
            
            results = self.db.execute_query(query, [start_date, end_date])
            
            if not results:
                logger.warning("No sentiment data found")
                return pd.DataFrame()

            df = pd.DataFrame(results, columns=[
                'timestamp', 'avg_sentiment', 'sentiment_count',
                'has_fomc', 'has_cpi', 'has_nfp'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Aggregate sentiment over specified hours
            if aggregation_hours > 1:
                df = df.set_index('timestamp')
                df = df.resample(f'{aggregation_hours}H').agg({
                    'avg_sentiment': 'mean',
                    'sentiment_count': 'sum',
                    'has_fomc': 'max',
                    'has_cpi': 'max',
                    'has_nfp': 'max'
                })
                df = df.reset_index()
            
            # Generate signals
            df['signal_type'] = 'NEUTRAL'
            df['signal_strength'] = 0.0
            
            # Strong risk-on → Buy TLT (expect yields to fall)
            mask_buy = df['avg_sentiment'] > sentiment_threshold
            df.loc[mask_buy, 'signal_type'] = 'BUY_TLT'
            df.loc[mask_buy, 'signal_strength'] = df.loc[mask_buy, 'avg_sentiment']
            
            # Strong risk-off → Sell TLT (expect yields to rise)
            mask_sell = df['avg_sentiment'] < -sentiment_threshold
            df.loc[mask_sell, 'signal_type'] = 'SELL_TLT'
            df.loc[mask_sell, 'signal_strength'] = abs(df.loc[mask_sell, 'avg_sentiment'])
            
            # Boost signal strength for major events
            df.loc[df['has_fomc'] | df['has_cpi'] | df['has_nfp'], 'signal_strength'] *= 1.5
            
            # Only keep non-neutral signals
            signals_df = df[df['signal_type'] != 'NEUTRAL'].copy()
            
            logger.info(f"Generated {len(signals_df)} signals from sentiment")
            return signals_df

        except Exception as e:
            logger.error(f"Failed to generate signals: {e}")
            return pd.DataFrame()

    def store_signals_to_db(self, signals_df: pd.DataFrame):
        """
        Store generated signals to database.
        
        Args:
            signals_df: DataFrame with signals from generate_sentiment_signals
        """
        try:
            for idx, signal in signals_df.iterrows():
                self.db.conn.execute("""
                    INSERT INTO sentiment_signals (
                        signal_timestamp, signal_type, signal_strength,
                        sentiment_input
                    ) VALUES (?, ?, ?, ?)
                """, [
                    signal['timestamp'],
                    signal['signal_type'],
                    signal['signal_strength'],
                    signal['avg_sentiment']
                ])
            
            logger.info(f"Stored {len(signals_df)} signals to database")
        except Exception as e:
            logger.error(f"Failed to store signals: {e}")


class Backtester:
    """
    Backtests trading signals against historical market data.
    """

    def __init__(self, db_manager):
        """
        Initialize backtester.
        
        Args:
            db_manager: DatabaseManager or WarehouseIntegration instance
        """
        self.db = db_manager

    def get_market_prices(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get market prices for backtesting.
        
        Args:
            instrument: Trading instrument
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with prices
        """
        try:
            query = """
            SELECT timestamp, price, yield, volume
            FROM market_data
            WHERE instrument = ?
                AND timestamp >= ?
                AND timestamp <= ?
            ORDER BY timestamp
            """
            
            results = self.db.execute_query(query, [instrument, start_date, end_date])
            
            if not results:
                logger.warning(f"No market data found for {instrument}")
                return pd.DataFrame()

            df = pd.DataFrame(results, columns=['timestamp', 'price', 'yield', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = df['yield'] if instrument.startswith('US') else df['price']
            
            return df

        except Exception as e:
            logger.error(f"Failed to get market prices: {e}")
            return pd.DataFrame()

    def backtest_signals(
        self,
        signals_df: pd.DataFrame,
        prices_df: pd.DataFrame,
        holding_hours: int = 24,
        transaction_cost_pct: float = 0.1
    ) -> pd.DataFrame:
        """
        Backtest trading signals against historical prices.
        
        Args:
            signals_df: Signals from SignalGenerator
            prices_df: Market prices from get_market_prices
            holding_hours: How long to hold each position
            transaction_cost_pct: Transaction cost as percentage
            
        Returns:
            DataFrame with backtest results
        """
        results = []
        
        for idx, signal in signals_df.iterrows():
            signal_time = signal['timestamp']
            signal_type = signal['signal_type']
            
            # Find entry price
            entry_mask = prices_df['timestamp'] >= signal_time
            if not entry_mask.any():
                continue
                
            entry_idx = prices_df[entry_mask].index[0]
            entry_price = prices_df.loc[entry_idx, 'value']
            entry_time = prices_df.loc[entry_idx, 'timestamp']
            
            # Find exit price
            exit_time = entry_time + timedelta(hours=holding_hours)
            exit_mask = prices_df['timestamp'] >= exit_time
            
            if not exit_mask.any():
                continue
                
            exit_idx = prices_df[exit_mask].index[0]
            exit_price = prices_df.loc[exit_idx, 'value']
            actual_exit_time = prices_df.loc[exit_idx, 'timestamp']
            
            # Calculate returns
            if signal_type == 'BUY_TLT':
                # Long position: profit if price goes up
                raw_return = (exit_price - entry_price) / entry_price
            elif signal_type == 'SELL_TLT':
                # Short position: profit if price goes down
                raw_return = (entry_price - exit_price) / entry_price
            else:
                raw_return = 0
            
            # Apply transaction costs
            net_return = raw_return - (transaction_cost_pct / 100)
            pnl = net_return * entry_price  # Assuming 1 unit position
            
            # Hold time
            hold_hours = (actual_exit_time - entry_time).total_seconds() / 3600
            
            results.append({
                'signal_timestamp': signal_time,
                'entry_timestamp': entry_time,
                'exit_timestamp': actual_exit_time,
                'signal_type': signal_type,
                'signal_strength': signal['signal_strength'],
                'sentiment_input': signal['avg_sentiment'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': net_return * 100,
                'pnl': pnl,
                'hold_hours': hold_hours,
            })

        results_df = pd.DataFrame(results)
        logger.info(f"Backtested {len(results_df)} signals")
        
        return results_df

    def calculate_performance_metrics(
        self,
        backtest_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate performance metrics from backtest results.
        
        Args:
            backtest_df: Results from backtest_signals
            
        Returns:
            Dictionary with performance metrics
        """
        if backtest_df.empty:
            return {}

        total_trades = len(backtest_df)
        winning_trades = (backtest_df['return_pct'] > 0).sum()
        losing_trades = (backtest_df['return_pct'] < 0).sum()
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_return = backtest_df['return_pct'].mean()
        total_pnl = backtest_df['pnl'].sum()
        
        # Sharpe ratio (annualized, assuming daily returns)
        returns_std = backtest_df['return_pct'].std()
        sharpe_ratio = (avg_return / returns_std * np.sqrt(252)) if returns_std != 0 else 0
        
        # Max drawdown
        cumulative_returns = (1 + backtest_df['return_pct'] / 100).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Profit factor
        gross_profit = backtest_df[backtest_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(backtest_df[backtest_df['pnl'] < 0]['pnl'].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'avg_return_pct': avg_return,
            'total_pnl': total_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'profit_factor': profit_factor,
            'avg_hold_hours': backtest_df['hold_hours'].mean(),
            'best_trade_pct': backtest_df['return_pct'].max(),
            'worst_trade_pct': backtest_df['return_pct'].min(),
        }

    def run_full_backtest(
        self,
        lookback_days: int = 90,
        instrument: str = 'TLT',
        sentiment_threshold: float = 0.3,
        holding_hours: int = 24
    ) -> Dict[str, any]:
        """
        Run complete backtest pipeline.
        
        Args:
            lookback_days: Days to backtest
            instrument: Trading instrument
            sentiment_threshold: Signal generation threshold
            holding_hours: Position holding period
            
        Returns:
            Complete backtest results
        """
        logger.info(f"Starting backtest for {instrument}")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        
        # Generate signals
        signal_gen = SignalGenerator(self.db)
        signals_df = signal_gen.generate_sentiment_signals(
            start_date,
            end_date,
            instrument,
            sentiment_threshold
        )
        
        if signals_df.empty:
            return {"error": "No signals generated"}

        # Get market prices
        prices_df = self.get_market_prices(instrument, start_date, end_date)
        
        if prices_df.empty:
            return {"error": "No market data available"}

        # Run backtest
        backtest_df = self.backtest_signals(
            signals_df,
            prices_df,
            holding_hours
        )
        
        if backtest_df.empty:
            return {"error": "Backtest produced no results"}

        # Calculate metrics
        metrics = self.calculate_performance_metrics(backtest_df)
        
        # Performance by signal type
        by_type = {}
        for signal_type in backtest_df['signal_type'].unique():
            subset = backtest_df[backtest_df['signal_type'] == signal_type]
            by_type[signal_type] = {
                'trades': len(subset),
                'win_rate_pct': (subset['return_pct'] > 0).sum() / len(subset) * 100,
                'avg_return_pct': subset['return_pct'].mean(),
                'total_pnl': subset['pnl'].sum(),
            }
        
        return {
            'instrument': instrument,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': lookback_days
            },
            'parameters': {
                'sentiment_threshold': sentiment_threshold,
                'holding_hours': holding_hours
            },
            'overall_performance': metrics,
            'by_signal_type': by_type,
            'trades': backtest_df.to_dict('records') if len(backtest_df) <= 100 else []
        }

