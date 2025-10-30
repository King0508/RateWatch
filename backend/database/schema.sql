-- RateWatch Local Database Schema
-- Self-contained DuckDB schema for sentiment and market data

-- News articles with sentiment analysis
CREATE SEQUENCE IF NOT EXISTS seq_news_sentiment;
CREATE TABLE IF NOT EXISTS news_sentiment (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_news_sentiment'),
    title TEXT NOT NULL,
    summary TEXT,
    source TEXT NOT NULL,
    url TEXT,
    timestamp TIMESTAMP NOT NULL,
    
    -- ML Sentiment Analysis
    sentiment_score DOUBLE,  -- -1 to 1 (negative to positive)
    sentiment_label TEXT,     -- 'bullish', 'bearish', 'neutral'
    confidence DOUBLE,        -- 0 to 1
    
    -- Entity Extraction
    fed_officials TEXT[],
    economic_indicators TEXT[],
    treasury_instruments TEXT[],
    
    -- Metadata
    is_high_impact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hourly sentiment aggregates for time series
CREATE SEQUENCE IF NOT EXISTS seq_sentiment_aggregates;
CREATE TABLE IF NOT EXISTS sentiment_aggregates (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_sentiment_aggregates'),
    hour_timestamp TIMESTAMP NOT NULL UNIQUE,
    
    -- Aggregate metrics
    avg_sentiment DOUBLE,
    sentiment_count INTEGER,
    risk_on_count INTEGER,
    risk_off_count INTEGER,
    neutral_count INTEGER,
    
    -- High impact count
    high_impact_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treasury yield data
CREATE SEQUENCE IF NOT EXISTS seq_treasury_yields;
CREATE TABLE IF NOT EXISTS treasury_yields (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_treasury_yields'),
    timestamp TIMESTAMP NOT NULL,
    
    -- Yield rates (in percentage)
    us_2y DOUBLE,
    us_5y DOUBLE,
    us_10y DOUBLE,
    us_30y DOUBLE,
    
    -- Metadata
    source TEXT DEFAULT 'FRED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETF price data
CREATE SEQUENCE IF NOT EXISTS seq_etf_prices;
CREATE TABLE IF NOT EXISTS etf_prices (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_etf_prices'),
    timestamp TIMESTAMP NOT NULL,
    ticker TEXT NOT NULL,
    
    -- Price data
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Correlation analysis results (cached)
CREATE SEQUENCE IF NOT EXISTS seq_correlation_results;
CREATE TABLE IF NOT EXISTS correlation_results (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_correlation_results'),
    analysis_date TIMESTAMP NOT NULL,
    
    -- Parameters
    lookback_days INTEGER,
    lag_hours INTEGER,
    instrument TEXT,
    
    -- Results
    correlation DOUBLE,
    p_value DOUBLE,
    sample_size INTEGER,
    
    -- Statistical metadata
    is_significant BOOLEAN,
    confidence_level DOUBLE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_sentiment(timestamp);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_label ON news_sentiment(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_sentiment_agg_timestamp ON sentiment_aggregates(hour_timestamp);
CREATE INDEX IF NOT EXISTS idx_treasury_timestamp ON treasury_yields(timestamp);
CREATE INDEX IF NOT EXISTS idx_etf_timestamp ON etf_prices(timestamp);
CREATE INDEX IF NOT EXISTS idx_etf_ticker ON etf_prices(ticker);

