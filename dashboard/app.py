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
    initial_sidebar_state="expanded",
)

# Premium CSS - TradingView/Koyfin Inspired Professional Design
st.markdown(
    """
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Global Styles - Dark Professional Theme */
    .stApp {
        background: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main content wrapper */
    .main {
        background: linear-gradient(180deg, rgba(13, 17, 23, 0.95) 0%, rgba(22, 27, 34, 0.98) 100%);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #131722 0%, #1C1F2B 100%);
        border-right: 1px solid #2A2E39;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Remove empty blocks in sidebar */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
    
    /* Compact sidebar spacing */
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Main Content Area */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1600px;
    }
    
    /* Headers with Gradient Accent */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.75rem !important;
        background: linear-gradient(135deg, #58a6ff 0%, #8957e5 50%, #bc4c91 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem !important;
        letter-spacing: -0.03em;
        line-height: 1.2 !important;
        padding-top: 1rem !important;
    }
    
    /* Add subtle glow to h1 */
    h1::after {
        content: '';
        display: block;
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, #58a6ff 0%, #8957e5 100%);
        margin-top: 1rem;
        border-radius: 2px;
        box-shadow: 0 0 20px rgba(88, 166, 255, 0.5);
    }
    
    h2 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.75rem !important;
        color: #FFFFFF;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        border-bottom: 2px solid #2A2E39;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 1.25rem !important;
        color: #B8B8B8;
        margin-bottom: 1rem !important;
    }
    
    /* Premium Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
        font-family: 'Roboto Mono', monospace;
        color: #FFFFFF !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #8E8E93 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E2433 0%, #252B3B 100%);
        border: 1px solid #2A2E39;
        border-radius: 12px;
        padding: 1.5rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
        border-color: #667EEA;
    }
    
    /* Enhanced Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #58a6ff 0%, #8957e5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.875rem 2.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6cb6ff 0%, #9d6ff2 100%);
        box-shadow: 0 8px 24px rgba(88, 166, 255, 0.6), 0 4px 8px rgba(0, 0, 0, 0.4);
        transform: translateY(-3px) scale(1.02);
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
        box-shadow: 0 2px 8px rgba(88, 166, 255, 0.4);
    }
    
    /* Checkbox Styling */
    .stCheckbox {
        color: #c9d1d9 !important;
    }
    
    .stCheckbox > label {
        color: #c9d1d9 !important;
        font-weight: 500 !important;
    }
    
    .stCheckbox > label > div {
        background-color: #161b22 !important;
        border: 1.5px solid #30363d !important;
        border-radius: 6px !important;
    }
    
    .stCheckbox > label > div[data-checked="true"] {
        background-color: #58a6ff !important;
        border-color: #58a6ff !important;
    }
    
    /* Radio Buttons - Sidebar Navigation */
    .stRadio > label {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
        margin-bottom: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-size: 0.85rem !important;
        display: none !important; /* Hide default label since we're using custom markdown */
    }
    
    .stRadio > div {
        gap: 0.25rem !important;
    }
    
    .stRadio > div > label {
        background: transparent !important;
        border-radius: 8px !important;
        padding: 0.65rem 0.85rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
        font-size: 0.9rem !important;
        white-space: nowrap !important;
    }
    
    .stRadio > div > label:hover {
        background: rgba(88, 166, 255, 0.1) !important;
        border-color: rgba(88, 166, 255, 0.3) !important;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.15) 0%, rgba(137, 87, 229, 0.15) 100%) !important;
        border: 1px solid rgba(88, 166, 255, 0.5) !important;
        box-shadow: 0 2px 8px rgba(88, 166, 255, 0.3) !important;
    }
    
    [data-testid="stMarkdownContainer"] label {
        color: #c9d1d9 !important;
    }
    
    /* Premium Card Containers */
    [data-testid="stVerticalBlock"] > div {
        background: rgba(30, 36, 51, 0.5);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2A2E39;
        backdrop-filter: blur(10px);
    }
    
    /* Data Tables */
    .dataframe {
        background-color: #1E2433 !important;
        border: 1px solid #2A2E39 !important;
        border-radius: 8px;
        color: #E0E0E0 !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #252B3B 0%, #1E2433 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        padding: 1rem !important;
        border-bottom: 2px solid #667EEA !important;
    }
    
    .dataframe td {
        border-color: #2A2E39 !important;
        padding: 0.75rem !important;
        color: #E0E0E0 !important;
    }
    
    /* Sentiment Color Classes */
    .risk-on {
        color: #00E676 !important;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(0, 230, 118, 0.5);
    }
    
    .risk-off {
        color: #FF5252 !important;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(255, 82, 82, 0.5);
    }
    
    .neutral {
        color: #FFD740 !important;
        font-weight: 600;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%) !important;
        border: 1.5px solid #30363d !important;
        border-radius: 10px !important;
        color: #c9d1d9 !important;
        padding: 0.875rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stSelectbox > div > div {
        padding: 0 !important;
    }
    
    .stSelectbox select {
        background: transparent !important;
        padding: 0.875rem 1rem !important;
        color: #c9d1d9 !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > div > div > input:hover,
    .stSelectbox > div > div:hover,
    .stNumberInput > div > div > input:hover {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 1px rgba(88, 166, 255, 0.3) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25) !important;
        background: #1c2128 !important;
    }
    
    /* Input labels */
    .stTextInput > label,
    .stSelectbox > label,
    .stNumberInput > label {
        color: #8b949e !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Info/Warning/Error Boxes */
    .stAlert {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.08) 0%, rgba(137, 87, 229, 0.08) 100%) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 12px !important;
        color: #c9d1d9 !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    /* Specific alert types */
    .stAlert[data-baseweb="notification"] {
        font-size: 1rem !important;
    }
    
    /* Info alerts */
    div[data-baseweb="notification"] > div {
        background: transparent !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1E2433 0%, #252B3B 100%) !important;
        border: 1px solid #2A2E39 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-weight: 500;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #667EEA !important;
    }
    
    /* Divider */
    hr {
        border-color: #2A2E39 !important;
        margin: 2rem 0 !important;
    }
    
    /* Code Blocks */
    code {
        background-color: #1E2433 !important;
        color: #00E676 !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 4px !important;
        font-family: 'Roboto Mono', monospace !important;
        font-size: 0.9rem !important;
    }
    
    pre {
        background-color: #131722 !important;
        border: 1px solid #2A2E39 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #131722;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764BA2 0%, #667EEA 100%);
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #667EEA !important;
    }
    
    /* Caption Text */
    .css-1kyxreq {
        color: #8E8E93 !important;
        font-size: 0.85rem !important;
    }
    
    /* Badge/Pill Style for Tags */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
    }
    
    /* Chart Container */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* News Card Styling */
    .news-card {
        background: linear-gradient(135deg, #1E2433 0%, #252B3B 100%);
        border: 1px solid #2A2E39;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .news-card:hover {
        border-color: #667EEA;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        transform: translateX(5px);
    }
    
    /* Status Indicators */
    .status-online {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #00E676;
        border-radius: 50%;
        margin-right: 0.5rem;
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.6);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .status-offline {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: #FF5252;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    /* Glassmorphism Effect for Special Cards */
    .glass-card {
        background: rgba(30, 36, 51, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize warehouse connection
@st.cache_resource
def init_warehouse():
    """Initialize warehouse connection."""
    if DIRECT_DB_ACCESS:
        try:
            # Resolve path to sibling quant-sql-warehouse directory
            # From dashboard/app.py -> fixed-income-news-summarizer/ -> downloads/ -> quant-sql-warehouse/
            warehouse_path = (
                Path(__file__).parent.parent
                / ".."
                / "quant-sql-warehouse"
                / "warehouse.duckdb"
            ).resolve()
            warehouse = get_warehouse(str(warehouse_path))
            return warehouse
        except Exception as e:
            st.error(f"Failed to connect to warehouse: {e}")
            return None
    return None


# Sidebar navigation with premium branding
st.sidebar.markdown(
    """
<div style="text-align: center; padding: 1.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid #30363d;">
    <h1 style="
        font-size: 1.6rem; 
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff 0%, #8957e5 50%, #bc4c91 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.01em;
        margin-bottom: 0.5rem;
    ">FIXED INCOME</h1>
    <p style="
        color: #8b949e;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin: 0;
        font-weight: 500;
    ">Sentiment Analytics Platform</p>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
<h2 style="
    color: #c9d1d9;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    margin-top: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.85rem;
">📊 Navigation</h2>
""",
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Select Page",
    ["Live Feed", "Analytics", "Event Studies", "Backtest Results", "Settings"],
    label_visibility="collapsed",
)

# Initialize warehouse
warehouse = init_warehouse()

# Sidebar status indicator
st.sidebar.markdown("---")
if warehouse:
    st.sidebar.markdown(
        """
    <div style="display: flex; align-items: center; padding: 0.75rem; background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(0, 230, 118, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.3);">
        <span class="status-online"></span>
        <div>
            <div style="font-weight: 600; color: #00E676; font-size: 0.9rem;">System Online</div>
            <div style="font-size: 0.75rem; color: #8E8E93;">Warehouse Connected</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        """
    <div style="display: flex; align-items: center; padding: 0.75rem; background: linear-gradient(135deg, rgba(255, 82, 82, 0.1) 0%, rgba(255, 82, 82, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(255, 82, 82, 0.3);">
        <span class="status-offline"></span>
        <div>
            <div style="font-weight: 600; color: #FF5252; font-size: 0.9rem;">System Offline</div>
            <div style="font-size: 0.75rem; color: #8E8E93;">Warehouse Disconnected</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Helper functions
def get_sentiment_color(label):
    """Get color for sentiment label - Premium TradingView Colors."""
    colors = {
        "risk-on": "#00E676",  # Brighter green with glow
        "risk-off": "#FF5252",  # Vibrant red
        "neutral": "#FFD740",  # Golden yellow
    }
    return colors.get(label, "#FFFFFF")


def format_sentiment_label(label):
    """Format sentiment label with HTML styling."""
    color = get_sentiment_color(label)
    return f'<span class="{label}" style="color: {color}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">{label}</span>'


def get_premium_chart_layout():
    """Get premium dark theme layout for Plotly charts - Modern GitHub Style."""
    return dict(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=13,
            color="#c9d1d9",
        ),
        title_font=dict(
            family="Inter, sans-serif", size=18, color="#f0f6fc", weight=600
        ),
        xaxis=dict(
            gridcolor="#21262d",
            linecolor="#30363d",
            zerolinecolor="#30363d",
            tickfont=dict(color="#8b949e", size=11),
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            gridcolor="#21262d",
            linecolor="#30363d",
            zerolinecolor="#30363d",
            tickfont=dict(color="#8b949e", size=11),
            showgrid=True,
            gridwidth=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#161b22",
            font_size=13,
            font_family="Inter, sans-serif",
            bordercolor="#58a6ff",
            font_color="#f0f6fc",
        ),
        margin=dict(l=70, r=40, t=70, b=60),
        legend=dict(
            bgcolor="rgba(22, 27, 34, 0.95)",
            bordercolor="#30363d",
            borderwidth=1,
            font=dict(color="#c9d1d9", size=12),
        ),
    )


# PAGE 1: LIVE FEED
if page == "Live Feed":
    st.title("📰 Live Sentiment Feed")
    st.markdown(
        """
    <p style="
        font-size: 1.05rem;
        color: #8b949e;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
        font-weight: 400;
    ">Real-time fixed-income news with ML-based sentiment analysis</p>
    """,
        unsafe_allow_html=True,
    )

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
                news_data = [n for n in news_data if n.get("is_high_impact", False)]

            if news_data:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)

                total = len(news_data)
                risk_on = sum(1 for n in news_data if n["sentiment_label"] == "risk-on")
                risk_off = sum(
                    1 for n in news_data if n["sentiment_label"] == "risk-off"
                )
                avg_sentiment = sum(n["sentiment_score"] for n in news_data) / total

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
                        sentiment_html = format_sentiment_label(item["sentiment_label"])
                        cols[1].markdown(sentiment_html, unsafe_allow_html=True)
                        cols[1].caption(f"Score: {item['sentiment_score']:.3f}")

                        # Confidence
                        conf_pct = item.get("confidence", 0) * 100
                        cols[2].metric("Confidence", f"{conf_pct:.1f}%")

                        # Summary and entities
                        if item.get("summary"):
                            st.write(
                                item["summary"][:300] + "..."
                                if len(item["summary"]) > 300
                                else item["summary"]
                            )

                        # Entities
                        entities = []
                        if item.get("economic_indicators"):
                            entities.extend(
                                [f"📊 {ind}" for ind in item["economic_indicators"]]
                            )
                        if item.get("fed_officials"):
                            entities.extend(
                                [f"👤 {off}" for off in item["fed_officials"]]
                            )
                        if item.get("treasury_instruments"):
                            entities.extend(
                                [f"💹 {inst}" for inst in item["treasury_instruments"]]
                            )

                        if entities:
                            st.caption(" | ".join(entities[:5]))

                        st.markdown("---")
            else:
                st.info("No news articles found for the selected time range.")

        except Exception as e:
            st.error(f"Error loading news: {e}")
    else:
        st.warning(
            "Database connection not available. Please ensure the warehouse is initialized."
        )


# PAGE 2: ANALYTICS
elif page == "Analytics":
    st.title("📈 Sentiment Analytics")
    st.markdown(
        """
    <p style="
        font-size: 1.05rem;
        color: #8b949e;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
        font-weight: 400;
    ">Advanced correlation analysis and market impact metrics</p>
    """,
        unsafe_allow_html=True,
    )

    if warehouse and DIRECT_DB_ACCESS:
        try:
            # Get sentiment timeseries
            hours_back = st.sidebar.slider("Analysis Period (hours)", 24, 720, 168)
            timeseries = warehouse.get_sentiment_timeseries(hours=hours_back)

            if timeseries:
                df = pd.DataFrame(timeseries)
                df["hour_timestamp"] = pd.to_datetime(df["hour_timestamp"])

                # Sentiment trend chart
                st.subheader("Sentiment Trend Over Time")

                fig = go.Figure()

                # Add sentiment line with premium styling
                fig.add_trace(
                    go.Scatter(
                        x=df["hour_timestamp"],
                        y=df["avg_sentiment"],
                        mode="lines+markers",
                        name="Avg Sentiment",
                        line=dict(
                            color="#58a6ff", width=3, shape="spline"  # Smooth curves
                        ),
                        marker=dict(
                            color="#58a6ff", size=8, line=dict(color="#0d1117", width=2)
                        ),
                        fill="tozeroy",
                        fillcolor="rgba(88, 166, 255, 0.12)",
                        hovertemplate="<b>%{x|%Y-%m-%d %H:%M}</b><br>Sentiment: %{y:.3f}<extra></extra>",
                    )
                )

                # Add zero line
                fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="#8E8E93",
                    opacity=0.3,
                    annotation_text="Neutral",
                    annotation_font_size=10,
                    annotation_font_color="#8E8E93",
                )

                # Apply premium layout
                layout = get_premium_chart_layout()
                layout.update(
                    height=450,
                    xaxis_title="Time",
                    yaxis_title="Sentiment Score",
                    title=dict(
                        text="", font=dict(size=0)
                    ),  # Using Streamlit's subheader instead
                )
                fig.update_layout(**layout)

                st.plotly_chart(fig, use_container_width=True)

                # Sentiment distribution
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Sentiment Distribution")

                    fig_dist = go.Figure()
                    fig_dist.add_trace(
                        go.Histogram(
                            x=df["avg_sentiment"],
                            nbinsx=30,
                            marker=dict(
                                color="#58a6ff",
                                line=dict(color="#8957e5", width=1.5),
                                opacity=0.9,
                            ),
                            hovertemplate="Sentiment: %{x:.3f}<br>Count: %{y}<extra></extra>",
                        )
                    )

                    # Apply premium layout
                    layout = get_premium_chart_layout()
                    layout.update(
                        height=350,
                        xaxis_title="Sentiment Score",
                        yaxis_title="Frequency",
                        showlegend=False,
                    )
                    fig_dist.update_layout(**layout)

                    st.plotly_chart(fig_dist, use_container_width=True)

                with col2:
                    st.subheader("Sentiment Breakdown")

                    # Calculate totals
                    total_risk_on = df["risk_on_count"].sum()
                    total_risk_off = df["risk_off_count"].sum()
                    total_neutral = df["neutral_count"].sum()

                    fig_pie = go.Figure(
                        data=[
                            go.Pie(
                                labels=["Risk-On", "Risk-Off", "Neutral"],
                                values=[total_risk_on, total_risk_off, total_neutral],
                                marker=dict(
                                    colors=["#00E676", "#FF5252", "#FFD740"],
                                    line=dict(color="#131722", width=2),
                                ),
                                hole=0.5,
                                textposition="outside",
                                textinfo="label+percent",
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
                            )
                        ]
                    )

                    # Apply premium layout
                    layout = get_premium_chart_layout()
                    layout.update(
                        height=350,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                        ),
                    )
                    fig_pie.update_layout(**layout)

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
        st.info(
            "Event studies require sufficient historical data. Run the ETL pipeline to populate the database."
        )

        if st.button("Run Event Study Analysis"):
            with st.spinner("Analyzing events..."):
                try:
                    analyzer = EventStudyAnalyzer(warehouse)
                    results = analyzer.run_full_event_study(
                        lookback_days=30, instrument="US10Y"
                    )

                    if "error" not in results:
                        st.success(
                            f"Analysis complete! Found {results['summary']['total_events']} events."
                        )

                        # Display summary
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Events", results["summary"]["total_events"])
                        col2.metric(
                            "Avg Impact",
                            f"{results['summary']['avg_percent_impact']:.2f}%",
                        )
                        col3.metric(
                            "Max Impact", f"{results['summary']['max_impact']:.2f}"
                        )
                        col4.metric(
                            "Positive/Negative",
                            f"{results['summary']['positive_impacts']}/{results['summary']['negative_impacts']}",
                        )

                        # By sentiment type
                        if results["by_sentiment"]:
                            st.subheader("Impact by Sentiment Type")

                            sentiment_data = []
                            for label, data in results["by_sentiment"].items():
                                sentiment_data.append(
                                    {
                                        "Sentiment": label.title(),
                                        "Events": data["count"],
                                        "Avg % Change": f"{data['avg_percent_change']:.2f}%",
                                        "Direction Consistency": f"{data['consistent_direction']:.1f}%",
                                    }
                                )

                            st.table(pd.DataFrame(sentiment_data))

                        # Statistical significance
                        if results.get("significance_tests"):
                            st.subheader("Statistical Significance")
                            sig = results["significance_tests"]

                            if sig["significant_at_5pct"]:
                                st.success(
                                    "✅ Market impact is statistically significant at 5% level"
                                )
                            else:
                                st.warning(
                                    "⚠️ Market impact is not statistically significant"
                                )

                            st.caption(f"p-value: {sig['t_test_p_value']:.4f}")
                    else:
                        st.warning(results["error"])

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
        st.info(
            "Backtesting requires market data. Ensure Treasury/ETF data has been loaded."
        )

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
                        instrument="TLT",
                        sentiment_threshold=sentiment_threshold,
                        holding_hours=holding_hours,
                    )

                    if "error" not in results:
                        st.success("Backtest complete!")

                        # Performance metrics
                        st.subheader("Overall Performance")
                        perf = results["overall_performance"]

                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Trades", perf["total_trades"])
                        col2.metric("Win Rate", f"{perf['win_rate_pct']:.1f}%")
                        col3.metric("Avg Return", f"{perf['avg_return_pct']:.2f}%")
                        col4.metric("Total P&L", f"${perf['total_pnl']:.2f}")

                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Sharpe Ratio", f"{perf['sharpe_ratio']:.2f}")
                        col2.metric("Max Drawdown", f"{perf['max_drawdown_pct']:.2f}%")
                        col3.metric("Profit Factor", f"{perf['profit_factor']:.2f}")
                        col4.metric("Avg Hold", f"{perf['avg_hold_hours']:.1f}h")

                        # By signal type
                        if results.get("by_signal_type"):
                            st.subheader("Performance by Signal Type")

                            signal_data = []
                            for signal_type, data in results["by_signal_type"].items():
                                signal_data.append(
                                    {
                                        "Signal": signal_type,
                                        "Trades": data["trades"],
                                        "Win Rate": f"{data['win_rate_pct']:.1f}%",
                                        "Avg Return": f"{data['avg_return_pct']:.2f}%",
                                        "Total P&L": f"${data['total_pnl']:.2f}",
                                    }
                                )

                            st.table(pd.DataFrame(signal_data))

                        # Trade history
                        if results.get("trades"):
                            st.subheader("Recent Trades")
                            trades_df = pd.DataFrame(results["trades"][:20])
                            st.dataframe(
                                trades_df[
                                    [
                                        "signal_timestamp",
                                        "signal_type",
                                        "return_pct",
                                        "pnl",
                                        "hold_hours",
                                    ]
                                ]
                            )

                    else:
                        st.warning(results["error"])

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
            col1.metric("News Articles", stats.get("news_count", 0))
            col2.metric("High-Impact", stats.get("high_impact_count", 0))

            if stats.get("news_date_range"):
                date_range = stats["news_date_range"]
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
    st.markdown(
        """
    **Fixed Income Sentiment Analytics Platform**
    
    Combines ML-based sentiment analysis with market data to provide actionable insights for fixed-income markets.
    
    - 🤖 FinBERT sentiment analysis
    - 📊 Real-time news monitoring
    - 📈 Market impact analysis
    - 💹 Trading signal generation
    - 🎯 Backtesting framework
    
    Integrated with **quant-sql-warehouse** for unified data management.
    """
    )


# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Fixed Income Sentiment Analytics v2.0")
