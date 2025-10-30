/**
 * API client for RateWatch backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

export interface NewsResponse {
  items: NewsItem[]
  total: number
  page: number
  page_size: number
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

export interface SentimentTimeSeries {
  data: SentimentAggregate[]
  period_hours: number
  summary: {
    avg_sentiment: number
    total_articles: number
    high_impact_articles: number
    period_hours: number
  }
}

export interface TreasuryYields {
  timestamp: string
  us_2y: number | null
  us_5y: number | null
  us_10y: number | null
  us_30y: number | null
}

export interface CorrelationResult {
  correlation: number
  p_value: number
  sample_size: number
  is_significant: boolean
  lag_hours: number
  instrument: string
  lookback_days: number
  date_range?: {
    start: string
    end: string
  }
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

class APIClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API Error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  // News endpoints
  async getRecentNews(params: {
    hours?: number
    limit?: number
    high_impact_only?: boolean
    page?: number
  }): Promise<NewsResponse> {
    const query = new URLSearchParams()
    if (params.hours) query.append('hours', params.hours.toString())
    if (params.limit) query.append('limit', params.limit.toString())
    if (params.high_impact_only) query.append('high_impact_only', 'true')
    if (params.page) query.append('page', params.page.toString())

    return this.fetch<NewsResponse>(`/api/news/recent?${query}`)
  }

  async getSentimentTimeSeries(hours: number = 168): Promise<SentimentTimeSeries> {
    return this.fetch<SentimentTimeSeries>(`/api/news/timeseries?hours=${hours}`)
  }

  // Market endpoints
  async getTreasuryYields(days: number = 30): Promise<TreasuryYields[]> {
    return this.fetch<TreasuryYields[]>(`/api/market/yields?days=${days}`)
  }

  // Analytics endpoints
  async getCorrelation(params: {
    lookback_days?: number
    lag_hours?: number
    instrument?: string
  }): Promise<CorrelationResult> {
    const query = new URLSearchParams()
    if (params.lookback_days) query.append('lookback_days', params.lookback_days.toString())
    if (params.lag_hours) query.append('lag_hours', params.lag_hours.toString())
    if (params.instrument) query.append('instrument', params.instrument)

    return this.fetch<CorrelationResult>(`/api/analytics/correlation?${query}`)
  }

  async getAnalyticsSummary(lookback_days: number = 30): Promise<any> {
    return this.fetch(`/api/analytics/summary?lookback_days=${lookback_days}`)
  }

  // Data management endpoints
  async refreshData(params: {
    hours?: number
    limit?: number
    include_market_data?: boolean
  }): Promise<{ status: string; message: string }> {
    const query = new URLSearchParams()
    if (params.hours) query.append('hours', params.hours.toString())
    if (params.limit) query.append('limit', params.limit.toString())
    if (params.include_market_data) query.append('include_market_data', 'true')

    return this.fetch(`/api/data/refresh?${query}`, { method: 'POST' })
  }

  async getStats(): Promise<Stats> {
    return this.fetch<Stats>('/api/data/stats')
  }
}

export const api = new APIClient(API_BASE_URL)

