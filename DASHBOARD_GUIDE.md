# 🚀 Dashboard Quick Start Guide

## ✅ Dashboard is Now Running!

Your Streamlit dashboard has been started in the background.

### 📍 Access the Dashboard

**URL**: http://localhost:8501

Open this in your web browser (Chrome, Edge, Firefox, etc.)

---

## 🎯 What You'll See in Each Tab

### **1. Live Feed Tab** 📰

**What to expect:**
- 2 Federal Reserve news articles
- Each article shows:
  - Title and source
  - Sentiment label (risk-on/risk-off/neutral)
  - Sentiment score (-1 to +1)
  - Confidence percentage
  - Extracted entities (Fed officials, indicators, instruments)

**Summary metrics at top:**
- Total Articles: 2
- Risk-On: 0
- Risk-Off: 0  
- Avg Sentiment: 0.00

**What you see:**
- "Federal Reserve Board denies application by Canandaigua National Corporation"
- "Federal Reserve Board announces approval of application by HPB Holdings, Inc."

---

### **2. Analytics Tab** 📊

**What to expect:**
- **Sentiment Trend Chart**: Line graph showing sentiment over time
- **Sentiment Distribution**: Histogram of sentiment scores
- **Sentiment Breakdown**: Pie chart (risk-on/risk-off/neutral counts)
- **Summary Statistics**: Mean, Std Dev, Max, Min sentiment

**With 2 articles:**
- You'll see 2 data points on the timeline
- Both neutral (score ~0.00)
- Useful for demonstrating the visualization capabilities

---

### **3. Event Studies Tab** 🎯

**What to expect:**
- Button to "Run Event Study Analysis"
- When clicked, analyzes correlation between:
  - News sentiment 
  - Treasury yield movements (1,033 events available!)

**How it works:**
- Takes sentiment from news_sentiment (2 articles)
- Correlates with market_events (1,033 yield movements)
- Shows statistical significance (t-tests, p-values)

**What you'll see:**
- Total events analyzed
- Average market impact
- Impact by sentiment type
- Statistical significance metrics

---

### **4. Backtest Results Tab** 💰

**What to expect:**
- Button to "Run Backtest"
- Parameters to adjust:
  - Lookback period (days)
  - Sentiment threshold
  - Holding period (hours)

**Current status:**
- No signals yet (need high-impact news)
- Shows: "Backtest requires market data"
- **Why**: Current 2 articles are neutral and not high-impact

**To populate:**
- Collect more news with strong sentiment
- Look for FOMC, CPI, NFP announcements
- These generate trading signals

---

### **5. Settings Tab** ⚙️

**What to expect:**
- Database connection status: ✅ Connected
- **Database stats:**
  - News Articles: 2
  - High-Impact: 0
  - Date Range displayed

**Instructions shown:**
- How to collect more data
- Command to run news collector
- About section with project info

---

## 🎨 Dashboard Features

### Dark Theme
- TradingView/Koyfin inspired design
- Dark background with colored accents
- Professional financial dashboard look

### Interactive Charts
- Hover over data points for details
- Zoom and pan on time series
- Responsive to window size

### Real-time Updates
- Refresh browser (F5) to update with new data
- Sidebar shows connection status (green = connected)

---

## 🔄 How to Refresh Data

### 1. Collect More News
```bash
cd C:\Users\kings\Downloads\fixed-income-news-summarizer
.\.venv\Scripts\python.exe -m squawk.main --hours 720 --top 100 --no-ml
```

### 2. Rebuild Analytics
```bash
cd C:\Users\kings\Downloads\quant-sql-warehouse
python etl\build_analytics.py
```

### 3. Refresh Dashboard
- Press **F5** in your browser
- Or click the "Refresh" button in Streamlit (top-right corner)

---

## 🐛 Troubleshooting

### Dashboard won't open
- Check the terminal for errors
- Make sure port 8501 is not in use
- Try: http://127.0.0.1:8501

### "Connection error" message
- Warehouse database path issue
- Check Settings tab for connection status
- Verify: `C:\Users\kings\Downloads\quant-sql-warehouse\warehouse.duckdb` exists

### No data showing
1. Check Settings tab - should show 2 articles
2. Run readiness check: `python test_dashboard_ready.py`
3. Refresh browser (F5)

### "Module not found" errors
- Install dashboard dependencies:
  ```bash
  .\.venv\Scripts\python.exe -m pip install streamlit plotly
  ```

---

## 🎬 Demo Flow (For Showing to Others)

### 1. Start at Settings Tab
- Show database connection: ✅
- Point out data stats: 2 articles, 1,033 market events

### 2. Move to Live Feed
- "This pulls fixed-income news from multiple RSS feeds"
- "Each article gets sentiment analysis"
- Show entity extraction: Fed officials, indicators

### 3. Show Analytics
- "Hourly aggregated sentiment metrics"
- "Interactive visualizations with Plotly"
- Point out the charts update with new data

### 4. Event Studies
- "Correlates news sentiment with actual Treasury yield movements"
- "1,033 market events from Treasury data"
- Click "Run Event Study Analysis" to show it works

### 5. Explain Backtest Tab
- "This would show trading signal performance"
- "Needs high-impact news to generate signals"
- "Demonstrates quantitative finance skills"

---

## 📈 Making It More Impressive

### Add More Data Sources
Edit `config.yaml` and add:
```yaml
feeds:
  - https://www.cnbc.com/id/10000664/device/rss/rss.html
  - https://www.marketwatch.com/rss/topstories
  - https://www.bloomberg.com/feeds/markets/news.rss
```

### Enable ML Sentiment
Remove `--no-ml` flag for FinBERT (more accurate):
```bash
.\.venv\Scripts\python.exe -m squawk.main --hours 720 --top 100
```

### Run Daily Collection
Set up a scheduled task:
- Windows Task Scheduler
- Run news collector every 6 hours
- Automatically rebuild analytics

---

## 🎓 For Resume/Interviews

**Key points to mention:**

1. **Data Engineering**
   - "Built ETL pipeline connecting news sentiment to data warehouse"
   - "DuckDB for columnar analytics performance"

2. **Machine Learning**
   - "Implemented FinBERT for domain-specific sentiment analysis"
   - "Named entity recognition for financial entities"

3. **Quantitative Finance**
   - "Event study methodology to measure market impact"
   - "Backtesting framework with standard performance metrics"

4. **Full-Stack Skills**
   - "FastAPI backend, Streamlit dashboard"
   - "Real-time data ingestion from multiple sources"

5. **Integration**
   - "Connected two separate projects into unified platform"
   - "Sentiment as alternative data source for trading signals"

---

## 🛑 How to Stop the Dashboard

Press **Ctrl+C** in the terminal where dashboard is running

Or close the terminal window

---

**Your dashboard is live and ready to showcase!** 🎉

Visit: **http://localhost:8501**

