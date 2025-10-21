# Fixed Income Sentiment Analytics Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade analytics platform combining **ML-based sentiment analysis** of fixed-income news with **quantitative market data** to generate actionable trading insights. Integrated with a DuckDB data warehouse for scalable analytics.

## 🌟 Key Features

### ML/NLP Capabilities
- **FinBERT Sentiment Analysis**: State-of-the-art transformer model fine-tuned for financial text
- **Named Entity Recognition**: Extracts Fed officials, economic indicators, Treasury instruments
- **Confidence Scoring**: ML model confidence for each prediction
- **High-Impact Detection**: Automated flagging of market-moving news

### Data Engineering
- **DuckDB Integration**: Fast analytical queries on combined news + market data
- **ETL Pipeline**: Automated news fetching, processing, and warehouse storage
- **Market Data Fetching**: Treasury yields (FRED API) and ETFs (Yahoo Finance)
- **Time-Series Aggregation**: Hourly sentiment metrics for trend analysis

### Quantitative Analytics
- **Lead-Lag Correlations**: How sentiment predicts yield movements (1h, 4h, 24h lags)
- **Event Studies**: Measure abnormal market moves around high-sentiment news
- **Trading Signals**: Sentiment-based signals for TLT (Treasury Bond ETF)
- **Backtesting Framework**: Sharpe ratio, win rate, max drawdown, profit factor

### Visualization & API
- **Streamlit Dashboard**: Interactive TradingView/Koyfin-style interface
- **FastAPI Backend**: RESTful endpoints for all analytics
- **Real-Time Feed**: Live sentiment monitoring with entity tags
- **Performance Metrics**: Comprehensive backtest visualization

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.9 or higher
python --version

# Optional: FRED API key for Treasury data
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
```

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fixed-income-news-summarizer

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional, for enhanced NER)
python -m spacy download en_core_web_sm
```

### Configuration

Create a `.env` file or set environment variables:
```bash
# Optional: For Treasury yield data
FRED_API_KEY=your_fred_api_key_here

# Warehouse location (defaults to ../quant-sql-warehouse/warehouse.duckdb)
WAREHOUSE_DB_PATH=path/to/warehouse.duckdb
```

### Run News Collection & Analysis

```bash
# Collect and analyze news (last 24 hours)
python -m squawk.main --hours 24 --top 50

# Output to console with sentiment analysis
# Data automatically stored in warehouse
```

### Launch Dashboard

```bash
# Start the interactive dashboard
streamlit run dashboard/app.py

# Opens at http://localhost:8501
```

### Start API Server

```bash
# Navigate to quant-sql-warehouse and start API
cd ../quant-sql-warehouse
python -m api.main

# API docs at http://localhost:8000/docs
# Includes both market data AND sentiment endpoints
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources                                  │
│  Reuters │ Fed  │ BLS │ Treasury │ FRED API │ Yahoo Finance     │
└────┬──────────────────────────────────────────────────────┬─────┘
     │                                                        │
     ▼                                                        ▼
┌─────────────────────┐                        ┌─────────────────────┐
│  News Summarizer    │                        │  Market Data        │
│  ├─ RSS Fetching    │                        │  Fetcher            │
│  ├─ FinBERT ML      │                        │  ├─ Treasury Yields │
│  ├─ Entity Extract  │                        │  └─ ETF Prices      │
│  └─ Sentiment Score │                        └──────────┬──────────┘
└──────────┬──────────┘                                   │
           │                                              │
           └──────────────┬───────────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  DuckDB Warehouse     │
              │  (quant-sql-warehouse)│
              │  ├─ news_sentiment    │
              │  ├─ market_data       │
              │  ├─ sentiment_aggs    │
              │  └─ signals           │
              └──────────┬────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐  ┌──────────┐  ┌────────────────┐
│   Analytics    │  │ FastAPI  │  │   Dashboard    │
│ ├─Correlations │  │ REST API │  │   (Streamlit)  │
│ ├─Event Studies│  │          │  │                │
│ └─Backtesting  │  │ /sentiment│  │ ├─ Live Feed   │
└────────────────┘  │ /analytics│  │ ├─ Analytics   │
                    └──────────┘  │ ├─ Events       │
                                  │ └─ Backtest     │
                                  └────────────────┘
```

## 📁 Project Structure

```
fixed-income-news-summarizer/
├── squawk/                      # Core news analysis
│   ├── main.py                  # CLI entry point
│   ├── summarizer.py            # RSS fetching & filtering
│   ├── ml_sentiment.py          # FinBERT sentiment analysis
│   ├── entity_extraction.py    # NER for financial entities
│   ├── market_data.py           # FRED/Yahoo data fetching
│   └── warehouse_integration.py # DuckDB connection layer
│
├── analytics/                   # Quantitative analysis
│   ├── correlations.py          # Lead-lag correlation analysis
│   ├── event_studies.py         # Event impact measurement
│   └── signals.py               # Signal generation & backtesting
│
├── dashboard/                   # Streamlit UI
│   └── app.py                   # Interactive dashboard
│
├── database/                    # Local schema (deprecated, moved to warehouse)
│   └── schema.sql               # Original standalone schema
│
├── config.yaml                  # News sources & keywords
└── requirements.txt             # Python dependencies

../quant-sql-warehouse/          # Integrated data warehouse
├── sql/
│   ├── schema.sql               # Market data tables
│   └── sentiment_schema.sql     # Sentiment extension tables
├── api/
│   ├── main.py                  # Extended with sentiment routes
│   └── sentiment_api.py         # Sentiment endpoints
└── warehouse.duckdb             # Unified database
```

## 💡 Usage Examples

### 1. Collect News with ML Sentiment

```python
from squawk.summarizer import fetch_items, filter_keywords
from squawk.ml_sentiment import sentiment_score_ml
from squawk.entity_extraction import extract_entities
from squawk.warehouse_integration import get_warehouse

# Fetch news
items = fetch_items(['https://www.reuters.com/markets/rss'])

# Analyze sentiment
for item in items:
    score, label, confidence = sentiment_score_ml(f"{item['title']} {item['summary']}")
    item['sentiment_score'] = score
    item['sentiment_label'] = label
    item['confidence'] = confidence
    item['entities'] = extract_entities(f"{item['title']} {item['summary']}")

# Store in warehouse
warehouse = get_warehouse()
warehouse.bulk_insert_news(items)
warehouse.compute_sentiment_aggregates(hours_back=24)
```

### 2. Run Correlation Analysis

```python
from analytics.correlations import CorrelationAnalyzer
from squawk.warehouse_integration import get_warehouse

warehouse = get_warehouse()
analyzer = CorrelationAnalyzer(warehouse)

# Analyze sentiment vs 10Y yields
results = analyzer.run_full_analysis(
    instrument='US10Y',
    lookback_days=90
)

print(f"Best lag: {results['summary']['best_lag']}")
# Example output: "4h lag shows correlation of 0.245 (p=0.0023)"
```

### 3. Backtest Trading Signals

```python
from analytics.signals import Backtester
from squawk.warehouse_integration import get_warehouse

warehouse = get_warehouse()
backtester = Backtester(warehouse)

results = backtester.run_full_backtest(
    lookback_days=60,
    instrument='TLT',
    sentiment_threshold=0.3,
    holding_hours=24
)

print(f"Win Rate: {results['overall_performance']['win_rate_pct']:.1f}%")
print(f"Sharpe Ratio: {results['overall_performance']['sharpe_ratio']:.2f}")
print(f"Total P&L: ${results['overall_performance']['total_pnl']:.2f}")
```

### 4. Query via API

```bash
# Get recent high-impact news
curl http://localhost:8000/sentiment/recent?high_impact_only=true&limit=10

# Get sentiment time series
curl http://localhost:8000/sentiment/timeseries?hours=168

# Get signal performance
curl http://localhost:8000/sentiment/signals/performance

# Search news by keyword
curl "http://localhost:8000/sentiment/search?keyword=powell&days=30"
```

## 📈 Key Findings (Example)

Based on 90-day analysis (results will vary with your data):

- **Sentiment-Yield Correlation**: 4-hour lag shows ~0.24 correlation (p<0.05)
- **Event Impact**: High-impact news causes avg 8.5bps yield movement
- **Trading Signals**: 58% win rate, 1.3 Sharpe ratio on TLT signals
- **Best Strategy**: Aggregate 4h sentiment → 24h hold → 2.4% avg return

## 🔧 Advanced Configuration

### config.yaml

```yaml
feeds:
  - https://www.reuters.com/markets/rss
  - https://www.federalreserve.gov/feeds/press_all.xml
  - https://www.bls.gov/feed/news.rss
  - https://www.treasury.gov/resource-center/presscenter/press-releases/Pages/rss.aspx

keywords:
  must_have_any:
    - treasury
    - yield
    - fed
    - inflation
    - cpi
    # ... more keywords

stop_words:
  - celebrity
  - sports
  - entertainment
```

### Dashboard Customization

Edit `dashboard/app.py` to customize:
- Color scheme (TradingView dark theme by default)
- Refresh intervals
- Chart types
- Metric displays

## 🧪 Testing & Development

```bash
# Run basic functionality test
python -m squawk.main --hours 1 --top 5

# Test warehouse integration
python -c "from squawk.warehouse_integration import get_warehouse; print(get_warehouse().get_stats())"

# Test API endpoints
# (Start API first, then)
curl http://localhost:8000/sentiment/stats
```

## 📦 Integration with Quant-SQL-Warehouse

This project extends [quant-sql-warehouse](../quant-sql-warehouse) with sentiment analytics:

1. **Shared Database**: Both projects use the same DuckDB warehouse
2. **Extended API**: Sentiment endpoints added to existing market data API
3. **Unified Analytics**: Correlate sentiment with technical indicators (RSI, VWAP)
4. **Single Dashboard**: View news sentiment + market data in one interface

To integrate:
```bash
# Ensure both projects are siblings
/projects/
  ├── fixed-income-news-summarizer/
  └── quant-sql-warehouse/

# Initialize warehouse schema
cd quant-sql-warehouse
python etl/load_data.py

# Add sentiment tables
sqlite3 warehouse.duckdb < sql/sentiment_schema.sql

# Run news collection
cd ../fixed-income-news-summarizer
python -m squawk.main --hours 24

# Start integrated API
cd ../quant-sql-warehouse
python -m api.main
```

## 🎯 Use Cases for Data Science Internships

This project demonstrates:

1. **ML/NLP Pipeline**: FinBERT implementation, entity extraction, confidence scoring
2. **Data Engineering**: ETL design, DuckDB integration, API development
3. **Statistical Analysis**: Correlation testing, hypothesis testing, event studies
4. **Quantitative Finance**: Signal generation, backtesting, risk metrics
5. **Full-Stack Skills**: Backend API + interactive frontend dashboard
6. **Production Thinking**: Error handling, logging, modular design
7. **Clear Value Proposition**: "Sentiment predicts X% of yield moves" is measurable

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

## 🤝 Contributing

Contributions welcome! This is a portfolio project demonstrating data science + quant finance skills.

## 📧 Contact

Built for data science internship applications - showcasing ML, data engineering, and financial analytics.

---

**Note**: This project is for educational and demonstration purposes. Not financial advice. Past performance doesn't guarantee future results.
