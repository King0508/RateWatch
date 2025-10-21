# Quick Start Guide

Get the Fixed Income Sentiment Analytics Platform running in 15 minutes.

## Prerequisites

- Python 3.9 or higher
- Git
- 2GB free disk space (for ML models)

## Step 1: Setup Projects

```bash
# Create projects directory
mkdir quantfinance-projects
cd quantfinance-projects

# Clone both projects (if not already cloned)
# Replace with your actual repo URLs
git clone <fixed-income-news-summarizer-url>
git clone <quant-sql-warehouse-url>

# Or if you have them, ensure they're in the same parent directory:
# quantfinance-projects/
#   ├── fixed-income-news-summarizer/
#   └── quant-sql-warehouse/
```

## Step 2: Install Dependencies

### For Fixed Income News Summarizer:

```bash
cd fixed-income-news-summarizer
pip install -r requirements.txt

# Optional but recommended for best performance
pip install torch  # CPU version is fine for inference
```

### For Quant Warehouse:

```bash
cd ../quant-sql-warehouse
pip install -r requirements.txt
```

## Step 3: Initialize Database

```bash
# Stay in quant-sql-warehouse directory
cd quant-sql-warehouse

# Create sample market data (optional but recommended)
python etl/generate_data.py
python etl/load_data.py

# Add sentiment tables
python -c "import duckdb; conn = duckdb.connect('warehouse.duckdb'); conn.execute(open('sql/sentiment_schema.sql').read()); conn.close()"

# Verify database
python -c "import duckdb; conn = duckdb.connect('warehouse.duckdb'); print('Tables:', conn.execute('SHOW TABLES').fetchall()); conn.close()"
```

## Step 4: Collect News Data

```bash
cd ../fixed-income-news-summarizer

# First run: Downloads FinBERT model (~500MB)
# This may take a few minutes
python -m squawk.main --hours 24 --top 20

# You should see:
# - News fetching from RSS feeds
# - ML sentiment analysis (FinBERT)
# - Entity extraction
# - Storage in warehouse
# - Formatted output
```

**Expected Output:**

```
[info] Fetching feeds...
[info] Pulled 147 items
[info] Within last 24h: 132 items
[info] After keyword filter: 45 items
[info] Processing items with FinBERT and entity extraction...
[info] ML processing complete
[info] Storing items in warehouse...
[info] Stored 45 items in warehouse
[info] Computed 24 sentiment aggregates
[info] Warehouse stats: {'news_count': 45, 'high_impact_count': 8...}

# Fixed-Income Squawk — 2025-10-21 16:30 EDT
**Desk Mood:** risk-off (avg score: -0.23)
**Counts:** risk-on 12, neutral 18, risk-off 15
...
```

## Step 5: Launch Dashboard

```bash
# Still in fixed-income-news-summarizer directory
streamlit run dashboard/app.py

# Dashboard will open at http://localhost:8501
```

**Dashboard Pages:**

- **Live Feed**: Recent news with sentiment
- **Analytics**: Sentiment trends and distributions
- **Event Studies**: Market impact analysis
- **Backtest Results**: Trading signal performance
- **Settings**: Database stats and configuration

## Step 6: Start API (Optional)

```bash
# In a new terminal
cd quant-sql-warehouse
python -m api.main

# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

**Test API Endpoints:**

```bash
# Get recent sentiment
curl http://localhost:8000/sentiment/recent?hours=24

# Get sentiment stats
curl http://localhost:8000/sentiment/stats

# Get signal performance
curl http://localhost:8000/sentiment/signals/performance
```

## Common Commands

### Collect News Regularly

```bash
# Every 6 hours
python -m squawk.main --hours 6 --top 30

# Or use cron/Task Scheduler:
# 0 */6 * * * cd /path/to/project && python -m squawk.main --hours 6
```

### Check Database Stats

```bash
python -c "from squawk.warehouse_integration import get_warehouse; print(get_warehouse().get_stats())"
```

### Recompute Aggregates

```bash
python -c "from squawk.warehouse_integration import get_warehouse; w = get_warehouse(); print(f'Computed {w.compute_sentiment_aggregates(168)} aggregates')"
```

### Run Analytics

```python
from squawk.warehouse_integration import get_warehouse
from analytics.correlations import CorrelationAnalyzer

warehouse = get_warehouse()
analyzer = CorrelationAnalyzer(warehouse)
results = analyzer.run_full_analysis(lookback_days=30)
print(results['summary'])
```

## Troubleshooting

### "No module named 'transformers'"

```bash
pip install transformers torch
```

### "Database not found"

Ensure both projects are siblings:

```
parent-directory/
├── fixed-income-news-summarizer/
└── quant-sql-warehouse/
    └── warehouse.duckdb  ← Must exist here
```

### "No sentiment data in dashboard"

```bash
# Run news collection first
python -m squawk.main --hours 24

# Then launch dashboard
streamlit run dashboard/app.py
```

### FinBERT download fails

Check internet connection. Model downloads from HuggingFace on first run.

### API returns 404 for /sentiment

```bash
# Ensure sentiment schema is loaded
cd quant-sql-warehouse
python -c "import duckdb; conn = duckdb.connect('warehouse.duckdb'); conn.execute(open('sql/sentiment_schema.sql').read())"
```

## Next Steps

### For Production Use

1. **Schedule news collection** (cron/Task Scheduler)
2. **Set up FRED API key** for Treasury data:
   ```bash
   export FRED_API_KEY=your_key_here
   ```
3. **Configure Slack webhook** (optional):
   ```bash
   export SLACK_WEBHOOK_URL=your_webhook_url
   python -m squawk.main --hours 6 --push slack
   ```

### For Development

1. Read `README.md` for detailed documentation
2. Check `SENTIMENT_INTEGRATION.md` in quant-warehouse
3. Explore API at `http://localhost:8000/docs`
4. Customize dashboard in `dashboard/app.py`

### For Data Science Portfolio

1. Run backtests with different parameters
2. Generate correlation analysis reports
3. Create visualizations from analytics
4. Document findings in notebooks

## Performance Optimization

### First Run (with model download)

- ~5-10 minutes

### Subsequent Runs (50 news items)

- News fetching: ~10 seconds
- ML processing: ~30 seconds
- Database storage: ~2 seconds
- Total: ~45 seconds

### Dashboard Load

- Initial: ~3 seconds
- Page navigation: <1 second

## Data Volumes

After 1 week of hourly collection:

- News items: ~3,000
- Sentiment aggregates: ~168
- Database size: ~50MB

After 1 month:

- News items: ~12,000
- Database size: ~200MB

## Support

- Check `README.md` for full documentation
- Review `examples/` directory for code samples
- Open issues on GitHub

## Success Checklist

- [ ] Both projects cloned and installed
- [ ] Database initialized with sentiment schema
- [ ] News collection runs successfully
- [ ] Dashboard loads and shows data
- [ ] API endpoints respond correctly
- [ ] Can run analytics (correlations, backtests)

If all checked, you're ready to use the platform! 🎉
