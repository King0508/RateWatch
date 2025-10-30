/**
 * Type definitions for RateWatch frontend
 */

export interface NewsItem {
  id: number
  title: string
  summary: string | null
  source: string
  url: string | null
  timestamp: string
  sentiment_score: number
  sentiment_label: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  entities: {
    fed_officials: string[]
    economic_indicators: string[]
    treasury_instruments: string[]
  }
  is_high_impact: boolean
}

export interface Stats {
  news_count: number
  high_impact_count: number
  avg_sentiment: number
  treasury_count: number
  etf_tickers: number
  date_range?: {
    min: string
    max: string
  }
}

export interface SentimentAggregate {
  timestamp: string
  avg_sentiment: number
  count: number
  risk_on: number
  risk_off: number
  neutral: number
  high_impact: number
}

export type SentimentLabel = 'bullish' | 'bearish' | 'neutral'

