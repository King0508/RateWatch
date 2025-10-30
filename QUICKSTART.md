# RateWatch Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

### Backend
```bash
pip install -r backend/requirements.txt
```

### Frontend
```bash
cd frontend
npm install
cd ..
```

## Step 2: Start the Services

### Terminal 1 - Backend
```bash
python -m backend.main
```
Backend will start on http://localhost:8000

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```
Frontend will start on http://localhost:3000

## Step 3: Use the Application

1. Open your browser to **http://localhost:3000**
2. Click **"Refresh Data"** button to fetch news
3. Wait 2-3 minutes for ML processing (first time only - downloads model)
4. Explore the dashboard!

## What You'll See

### Dashboard
- Recent news with sentiment analysis (bullish/bearish/neutral)
- Sentiment trend chart
- Key metrics

### Analytics
- Correlation between sentiment and Treasury yields
- Statistical significance testing
- Multiple time periods

### Market Data
- Treasury yield curves
- Historical data visualization

## Troubleshooting

### Backend won't start
- Make sure you're in the project root directory
- Check Python version: `python --version` (need 3.9+)
- Install dependencies again: `pip install -r backend/requirements.txt`

### Frontend won't start
- Navigate to frontend directory: `cd frontend`
- Install dependencies: `npm install`
- Try: `npm run dev`

### No data showing
- Click "Refresh Data" button on dashboard
- Wait 2-3 minutes for first run (ML model download)
- Check backend terminal for errors

### CORS errors
- Make sure backend is running on port 8000
- Make sure frontend is running on port 3000
- Restart both services

## Optional: Configure FRED API

For Treasury yield data:

1. Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html
2. Create `.env` file in project root:
```bash
FRED_API_KEY=your_key_here
```
3. Restart backend

## Need Help?

Check the full README.md for detailed documentation, architecture, and advanced features.

**Happy analyzing! 📈**
