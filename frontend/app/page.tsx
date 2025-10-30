'use client'

import { useEffect, useState } from 'react'
import { MetricsPanel } from '@/components/MetricsPanel'
import { SentimentFeed } from '@/components/SentimentFeed'
import { TimeSeriesChart } from '@/components/TimeSeriesChart'
import { RefreshButton } from '@/components/RefreshButton'
import { api } from '@/lib/api'
import type { NewsItem, Stats } from '@/lib/types'

export default function Dashboard() {
  const [news, setNews] = useState<NewsItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [newsData, statsData] = await Promise.all([
        api.getRecentNews({ hours: 24, limit: 20 }),
        api.getStats(),
      ])
      setNews(newsData.items)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            RateWatch Dashboard
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Real-time sentiment analysis and market correlations
          </p>
        </div>
        <RefreshButton onRefresh={fetchData} />
      </div>

      {/* Metrics */}
      {stats && <MetricsPanel stats={stats} />}

      {/* Time Series Chart */}
      <div className="bg-card rounded-lg border border-border p-6 card-shadow">
        <h2 className="text-2xl font-semibold mb-4">Sentiment Trends</h2>
        <TimeSeriesChart hours={168} />
      </div>

      {/* News Feed */}
      <div className="bg-card rounded-lg border border-border p-6 card-shadow">
        <h2 className="text-2xl font-semibold mb-4">Recent News</h2>
        <SentimentFeed news={news} loading={loading} />
      </div>
    </div>
  )
}

