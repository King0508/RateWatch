"""
Fixed Income Sentiment Analytics Dashboard
Interactive Streamlit dashboard with TradingView/Koyfin aesthetic
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import warehouse integration
try:
    from squawk.warehouse_integration import get_warehouse
    from analytics.correlations import CorrelationAnalyzer
    from analytics.event_studies import EventStudyAnalyzer
    from analytics.signals import SignalGenerator, Backtester
    DIRECT_DB_ACCESS = True
except ImportError:
    DIRECT_DB_ACCESS = False

# Page configuration
st.set_page_config(
    page_title="Fixed Income Sentiment Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme (TradingView/Koyfin style)
st.markdown("""
<style>
    .reportview-container {
        background: #1E1E1E;
        color: #FFFFFF;
    }
    .sidebar .sidebar-content {
        background: #262626;
    }
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    .stMetric {
        background-color: #2D2D2D;
        padding: 15px;
        border-radius: 8px;
    }
    .risk-on {
        color: #00C853;
        font-weight: bold;
    }
    .risk-off {
        color: #FF1744;
        font-weight: bold;
    }
    .neutral {
        color: #FFB300;
    }
</style>
""", unsafe_allow_html=True)

# Initialize warehouse connection
@st.cache_resource
def init_warehouse():
    """Initialize warehouse connection."""
    if DIRECT_DB_ACCESS:
        try:
            warehouse_path = Path(__file__).parent.parent.parent / "quant-sql-warehouse" / "warehouse.duckdb"
            warehouse = get_warehouse(str(warehouse_path))
            return warehouse
        except Exception as e:
            st.error(f"Failed to connect to warehouse: {e}")
            return None
    return None

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Live Feed", "Analytics", "Event Studies", "Backtest Results", "Settings"]
)

# Initialize warehouse
warehouse = init_warehouse()

# Helper functions
def get_sentiment_color(label):
    """Get color for sentiment label."""
    colors = {
        'risk-on': '#00C853',
        'risk-off': '#FF1744',
        'neutral': '#FFB300'
    }
    return colors.get(label, '#FFFFFF')

def format_sentiment_label(label):
    """Format sentiment label with HTML styling."""
    color = get_sentiment_color(label)
    return f'<span style="color: {color}; font-weight: bold;">{label.upper()}</span>'


# PAGE 1: LIVE FEED
if page == "Live Feed":
    st.title("📰 Live Sentiment Feed")
    st.markdown("Real-time fixed-income news with ML-based sentiment analysis")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        hours_back = st.selectbox("Time Range", [6, 12, 24, 48, 72], index=2)
    with col2:
        high_impact_only = st.checkbox("High-Impact Only", value=False)
    with col3:
        limit = st.selectbox("Max Items", [25, 50, 100, 200], index=1)
    
    if warehouse and DIRECT_DB_ACCESS:
        try:
            # Get recent news
            news_data = warehouse.get_recent_news(hours=hours_back, limit=limit)
            
            if high_impact_only:
                news_data = [n for n in news_data if n.get('is_high_impact', False)]
            
            if news_data:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total = len(news_data)
                risk_on = sum(1 for n in news_data if n['sentiment_label'] == 'risk-on')
                risk_off = sum(1 for n in news_data if n['sentiment_label'] == 'risk-off')
                avg_sentiment = sum(n['sentiment_score'] for n in news_data) / total
                
                col1.metric("Total Articles", total)
                col2.metric("Risk-On", risk_on, delta=None, delta_color="normal")
                col3.metric("Risk-Off", risk_off, delta=None, delta_color="inverse")
                col4.metric("Avg Sentiment", f"{avg_sentiment:.3f}")
                
                st.markdown("---")
                
                # Display news items
                for item in news_data:
                    with st.container():
                        cols = st.columns([3, 1, 1])
                        
                        # Title and details
                        cols[0].markdown(f"### {item['title']}")
                        cols[0].caption(f"**{item['source']}** | {item['timestamp']}")
                        
                        # Sentiment
                        sentiment_html = format_sentiment_label(item['sentiment_label'])
                        cols[1].markdown(sentiment_html, unsafe_allow_html=True)
                        cols[1].caption(f"Score: {item['sentiment_score']:.3f}")
                        
                        # Confidence
                        conf_pct = item.get('confidence', 0) * 100
                        cols[2].metric("Confidence", f"{conf_pct:.1f}%")
                        
                        # Summary and entities
                        if item.get('summary'):
                            st.write(item['summary'][:300] + "..." if len(item['summary']) > 300 else item['summary'])
                        
                        # Entities
                        entities = []
                        if item.get('economic_indicators'):
                            entities.extend([f"📊 {ind}" for ind in item['economic_indicators']])
                        if item.get('fed_officials'):
                            entities.extend([f"👤 {off}" for off in item['fed_officials']])
                        if item.get('treasury_instruments'):
                            entities.extend([f"💹 {inst}" for inst in item['treasury_instruments']])
                        
                        if entities:
                            st.caption(" | ".join(entities[:5]))
                        
                        st.markdown("---")
            else:
                st.info("No news articles found for the selected time range.")
                
        except Exception as e:
            st.error(f"Error loading news: {e}")
    else:
        st.warning("Database connection not available. Please ensure the warehouse is initialized.")


# PAGE 2: ANALYTICS
elif page == "Analytics":
    st.title("📈 Sentiment Analytics")
    st.markdown("Correlation analysis and market impact")
    
    if warehouse and DIRECT_DB_ACCESS:
        try:
            # Get sentiment timeseries
            hours_back = st.sidebar.slider("Analysis Period (hours)", 24, 720, 168)
            timeseries = warehouse.get_sentiment_timeseries(hours=hours_back)
            
            if timeseries:
                df = pd.DataFrame(timeseries)
                df['hour_timestamp'] = pd.to_datetime(df['hour_timestamp'])
                
                # Sentiment trend chart
                st.subheader("Sentiment Trend Over Time")
                
                fig = go.Figure()
                
                # Add sentiment line
                fig.add_trace(go.Scatter(
                    x=df['hour_timestamp'],
                    y=df['avg_sentiment'],
                    mode='lines',
                    name='Avg Sentiment',
                    line=dict(color='#00BCD4', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 188, 212, 0.1)'
                ))
                
                # Add zero line
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                
                fig.update_layout(
                    template='plotly_dark',
                    height=400,
                    xaxis_title="Time",
                    yaxis_title="Sentiment Score",
                    hovermode='x unified',
                    plot_bgcolor='#1E1E1E',
                    paper_bgcolor='#1E1E1E',
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sentiment distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Sentiment Distribution")
                    
                    fig_dist = go.Figure()
                    fig_dist.add_trace(go.Histogram(
                        x=df['avg_sentiment'],
                        nbinsx=30,
                        marker_color='#00BCD4',
                        opacity=0.75
                    ))
                    
                    fig_dist.update_layout(
                        template='plotly_dark',
                        height=300,
                        xaxis_title="Sentiment Score",
                        yaxis_title="Frequency",
                        plot_bgcolor='#1E1E1E',
                        paper_bgcolor='#1E1E1E',
                    )
                    
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                with col2:
                    st.subheader("Sentiment Breakdown")
                    
                    # Calculate totals
                    total_risk_on = df['risk_on_count'].sum()
                    total_risk_off = df['risk_off_count'].sum()
                    total_neutral = df['neutral_count'].sum()
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['Risk-On', 'Risk-Off', 'Neutral'],
                        values=[total_risk_on, total_risk_off, total_neutral],
                        marker=dict(colors=['#00C853', '#FF1744', '#FFB300']),
                        hole=0.4
                    )])
                    
                    fig_pie.update_layout(
                        template='plotly_dark',
                        height=300,
                        plot_bgcolor='#1E1E1E',
                        paper_bgcolor='#1E1E1E',
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Statistics
                st.subheader("Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Avg Sentiment", f"{df['avg_sentiment'].mean():.3f}")
                col2.metric("Std Dev", f"{df['avg_sentiment'].std():.3f}")
                col3.metric("Max", f"{df['avg_sentiment'].max():.3f}")
                col4.metric("Min", f"{df['avg_sentiment'].min():.3f}")
                
            else:
                st.info("No aggregated sentiment data available.")
                
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
            st.exception(e)
    else:
        st.warning("Database connection not available.")


# PAGE 3: EVENT STUDIES
elif page == "Event Studies":
    st.title("🎯 Event Impact Analysis")
    st.markdown("Market impact of high-sentiment news events")
    
    if warehouse and DIRECT_DB_ACCESS:
        st.info("Event studies require sufficient historical data. Run the ETL pipeline to populate the database.")
        
        if st.button("Run Event Study Analysis"):
            with st.spinner("Analyzing events..."):
                try:
                    analyzer = EventStudyAnalyzer(warehouse)
                    results = analyzer.run_full_event_study(lookback_days=30, instrument='US10Y')
                    
                    if 'error' not in results:
                        st.success(f"Analysis complete! Found {results['summary']['total_events']} events.")
                        
                        # Display summary
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Events", results['summary']['total_events'])
                        col2.metric("Avg Impact", f"{results['summary']['avg_percent_impact']:.2f}%")
                        col3.metric("Max Impact", f"{results['summary']['max_impact']:.2f}")
                        col4.metric("Positive/Negative", f"{results['summary']['positive_impacts']}/{results['summary']['negative_impacts']}")
                        
                        # By sentiment type
                        if results['by_sentiment']:
                            st.subheader("Impact by Sentiment Type")
                            
                            sentiment_data = []
                            for label, data in results['by_sentiment'].items():
                                sentiment_data.append({
                                    'Sentiment': label.title(),
                                    'Events': data['count'],
                                    'Avg % Change': f"{data['avg_percent_change']:.2f}%",
                                    'Direction Consistency': f"{data['consistent_direction']:.1f}%"
                                })
                            
                            st.table(pd.DataFrame(sentiment_data))
                        
                        # Statistical significance
                        if results.get('significance_tests'):
                            st.subheader("Statistical Significance")
                            sig = results['significance_tests']
                            
                            if sig['significant_at_5pct']:
                                st.success("✅ Market impact is statistically significant at 5% level")
                            else:
                                st.warning("⚠️ Market impact is not statistically significant")
                            
                            st.caption(f"p-value: {sig['t_test_p_value']:.4f}")
                    else:
                        st.warning(results['error'])
                        
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.exception(e)
    else:
        st.warning("Database connection not available.")


# PAGE 4: BACKTEST RESULTS
elif page == "Backtest Results":
    st.title("💰 Signal Backtesting")
    st.markdown("Performance of sentiment-based trading signals")
    
    if warehouse and DIRECT_DB_ACCESS:
        st.info("Backtesting requires market data. Ensure Treasury/ETF data has been loaded.")
        
        # Parameters
        col1, col2, col3 = st.columns(3)
        with col1:
            lookback_days = st.number_input("Lookback Days", 30, 180, 60)
        with col2:
            sentiment_threshold = st.slider("Sentiment Threshold", 0.1, 0.9, 0.3)
        with col3:
            holding_hours = st.number_input("Holding Period (hours)", 1, 72, 24)
        
        if st.button("Run Backtest"):
            with st.spinner("Running backtest..."):
                try:
                    backtester = Backtester(warehouse)
                    results = backtester.run_full_backtest(
                        lookback_days=lookback_days,
                        instrument='TLT',
                        sentiment_threshold=sentiment_threshold,
                        holding_hours=holding_hours
                    )
                    
                    if 'error' not in results:
                        st.success("Backtest complete!")
                        
                        # Performance metrics
                        st.subheader("Overall Performance")
                        perf = results['overall_performance']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Trades", perf['total_trades'])
                        col2.metric("Win Rate", f"{perf['win_rate_pct']:.1f}%")
                        col3.metric("Avg Return", f"{perf['avg_return_pct']:.2f}%")
                        col4.metric("Total P&L", f"${perf['total_pnl']:.2f}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Sharpe Ratio", f"{perf['sharpe_ratio']:.2f}")
                        col2.metric("Max Drawdown", f"{perf['max_drawdown_pct']:.2f}%")
                        col3.metric("Profit Factor", f"{perf['profit_factor']:.2f}")
                        col4.metric("Avg Hold", f"{perf['avg_hold_hours']:.1f}h")
                        
                        # By signal type
                        if results.get('by_signal_type'):
                            st.subheader("Performance by Signal Type")
                            
                            signal_data = []
                            for signal_type, data in results['by_signal_type'].items():
                                signal_data.append({
                                    'Signal': signal_type,
                                    'Trades': data['trades'],
                                    'Win Rate': f"{data['win_rate_pct']:.1f}%",
                                    'Avg Return': f"{data['avg_return_pct']:.2f}%",
                                    'Total P&L': f"${data['total_pnl']:.2f}"
                                })
                            
                            st.table(pd.DataFrame(signal_data))
                        
                        # Trade history
                        if results.get('trades'):
                            st.subheader("Recent Trades")
                            trades_df = pd.DataFrame(results['trades'][:20])
                            st.dataframe(trades_df[['signal_timestamp', 'signal_type', 'return_pct', 'pnl', 'hold_hours']])
                        
                    else:
                        st.warning(results['error'])
                        
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                    st.exception(e)
    else:
        st.warning("Database connection not available.")


# PAGE 5: SETTINGS
elif page == "Settings":
    st.title("⚙️ Settings")
    st.markdown("Configuration and data management")
    
    st.subheader("Database Connection")
    if warehouse:
        st.success("✅ Connected to quant-sql-warehouse")
        
        # Database stats
        stats = warehouse.get_stats()
        if stats:
            col1, col2, col3 = st.columns(3)
            col1.metric("News Articles", stats.get('news_count', 0))
            col2.metric("High-Impact", stats.get('high_impact_count', 0))
            
            if stats.get('news_date_range'):
                date_range = stats['news_date_range']
                col3.metric("Date Range", f"{date_range['min']} to {date_range['max']}")
    else:
        st.warning("❌ Not connected to warehouse")
        st.info("Ensure warehouse.duckdb exists in quant-sql-warehouse directory")
    
    st.markdown("---")
    
    st.subheader("Data Collection")
    st.info("Run the news summarizer to collect and process fixed-income news")
    
    st.code("python -m squawk.main --hours 24 --top 50", language="bash")
    
    st.markdown("---")
    
    st.subheader("About")
    st.markdown("""
    **Fixed Income Sentiment Analytics Platform**
    
    Combines ML-based sentiment analysis with market data to provide actionable insights for fixed-income markets.
    
    - 🤖 FinBERT sentiment analysis
    - 📊 Real-time news monitoring
    - 📈 Market impact analysis
    - 💹 Trading signal generation
    - 🎯 Backtesting framework
    
    Integrated with **quant-sql-warehouse** for unified data management.
    """)


# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Fixed Income Sentiment Analytics v2.0")
if warehouse:
    st.sidebar.caption("🟢 Connected to Warehouse")
else:
    st.sidebar.caption("🔴 Warehouse Offline")

