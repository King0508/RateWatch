-- Fixed Income Analytics Platform - Database Schema
-- DuckDB schema for news sentiment, market data, and events

-- News sentiment data with ML-based analysis
CREATE TABLE IF NOT EXISTS news_sentiment (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    summary TEXT,
    link VARCHAR,
    
    -- Sentiment analysis
    sentiment_score DOUBLE NOT NULL,  -- -1 (bearish) to 1 (bullish)
    sentiment_label VARCHAR NOT NULL,  -- 'risk-on', 'risk-off', 'neutral'
    confidence DOUBLE,  -- Model confidence 0-1
    
    -- Entity extraction
    fed_officials VARCHAR[],
    economic_indicators VARCHAR[],
    treasury_instruments VARCHAR[],
    credit_terms VARCHAR[],
    yields VARCHAR[],
    basis_points VARCHAR[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    INDEX idx_timestamp (timestamp),
    INDEX idx_sentiment_label (sentiment_label),
    INDEX idx_source (source)
);

-- Market data for Treasury yields and ETFs
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    instrument VARCHAR NOT NULL,  -- e.g., 'US2Y', 'US10Y', 'TLT', 'IEF'
    instrument_type VARCHAR NOT NULL,  -- 'yield', 'etf', 'spread'
    
    -- Price/Yield data
    price DOUBLE,  -- For ETFs
    yield DOUBLE,  -- For Treasury yields (in %)
    volume BIGINT,  -- Trading volume
    
    -- Calculated fields
    change_1h DOUBLE,
    change_4h DOUBLE,
    change_1d DOUBLE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_instrument_time (instrument, timestamp),
    INDEX idx_timestamp_market (timestamp)
);

-- Major economic events and announcements
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR NOT NULL,  -- 'FOMC', 'CPI', 'NFP', 'AUCTION', etc.
    description TEXT NOT NULL,
    
    -- Market impact
    market_impact VARCHAR,  -- 'high', 'medium', 'low'
    pre_event_sentiment DOUBLE,  -- Avg sentiment 24h before
    post_event_sentiment DOUBLE,  -- Avg sentiment 24h after
    
    -- Yield changes around event (in bps)
    yield_change_2y DOUBLE,
    yield_change_10y DOUBLE,
    yield_change_30y DOUBLE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_event_type (event_type),
    INDEX idx_event_time (timestamp)
);

-- Sentiment aggregations (materialized view for performance)
CREATE TABLE IF NOT EXISTS sentiment_aggregates (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,  -- Hourly aggregation
    
    -- Aggregate metrics
    avg_sentiment DOUBLE,
    sentiment_count INTEGER,
    risk_on_count INTEGER,
    risk_off_count INTEGER,
    neutral_count INTEGER,
    
    -- High-impact news flags
    has_fomc BOOLEAN,
    has_cpi BOOLEAN,
    has_nfp BOOLEAN,
    has_fed_speaker BOOLEAN,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_agg_timestamp (timestamp)
);

-- Correlation analysis results (cached computations)
CREATE TABLE IF NOT EXISTS correlation_cache (
    id INTEGER PRIMARY KEY,
    calculation_date DATE NOT NULL,
    
    -- Correlation parameters
    sentiment_instrument VARCHAR NOT NULL,  -- Which sentiment metric
    market_instrument VARCHAR NOT NULL,  -- Which market instrument
    lag_hours INTEGER NOT NULL,  -- Time lag for correlation
    window_days INTEGER NOT NULL,  -- Rolling window size
    
    -- Results
    correlation DOUBLE NOT NULL,
    p_value DOUBLE,
    sample_size INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_corr_instruments (sentiment_instrument, market_instrument)
);

-- Trading signals and backtest results
CREATE TABLE IF NOT EXISTS trading_signals (
    id INTEGER PRIMARY KEY,
    signal_timestamp TIMESTAMP NOT NULL,
    
    -- Signal details
    signal_type VARCHAR NOT NULL,  -- 'BUY_TLT', 'SELL_TLT', 'NEUTRAL'
    signal_strength DOUBLE,  -- 0-1, strength of signal
    sentiment_input DOUBLE,  -- Sentiment that triggered signal
    
    -- Position tracking
    entry_price DOUBLE,
    exit_price DOUBLE,
    exit_timestamp TIMESTAMP,
    
    -- Performance
    pnl DOUBLE,
    return_pct DOUBLE,
    hold_hours DOUBLE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_signal_time (signal_timestamp),
    INDEX idx_signal_type (signal_type)
);

-- Create views for common queries

-- Recent high-impact news
CREATE VIEW IF NOT EXISTS v_recent_high_impact AS
SELECT 
    timestamp,
    source,
    title,
    sentiment_score,
    sentiment_label,
    confidence,
    fed_officials,
    economic_indicators
FROM news_sentiment
WHERE 
    timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
    AND (
        array_length(fed_officials) > 0 
        OR 'FOMC' = ANY(economic_indicators)
        OR 'CPI' = ANY(economic_indicators)
        OR 'NFP' = ANY(economic_indicators)
    )
ORDER BY timestamp DESC;

-- Latest market snapshot
CREATE VIEW IF NOT EXISTS v_latest_market AS
SELECT DISTINCT ON (instrument)
    instrument,
    timestamp,
    price,
    yield,
    change_1h,
    change_1d
FROM market_data
ORDER BY instrument, timestamp DESC;

-- Sentiment vs yield changes (for correlation analysis)
CREATE VIEW IF NOT EXISTS v_sentiment_yield_pairs AS
SELECT 
    sa.timestamp,
    sa.avg_sentiment,
    sa.sentiment_count,
    md.instrument,
    md.yield,
    md.change_1h,
    md.change_1d
FROM sentiment_aggregates sa
JOIN market_data md ON 
    md.timestamp BETWEEN sa.timestamp - INTERVAL '5 minutes' 
    AND sa.timestamp + INTERVAL '5 minutes'
WHERE md.instrument_type = 'yield'
ORDER BY sa.timestamp DESC;

