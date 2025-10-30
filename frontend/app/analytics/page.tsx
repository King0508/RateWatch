'use client'

import { useEffect, useState } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { api } from '@/lib/api'
import type { CorrelationResult } from '@/lib/api'
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'

export default function AnalyticsPage() {
  const [correlation, setCorrelation] = useState<CorrelationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [lookbackDays, setLookbackDays] = useState(30)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const result = await api.getCorrelation({
          lookback_days: lookbackDays,
          lag_hours: 0,
          instrument: 'us_10y'
        })
        setCorrelation(result)
      } catch (error) {
        console.error('Failed to fetch correlation:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [lookbackDays])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">
          Correlation Analytics
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Analyze the relationship between sentiment and market movements
        </p>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        {[7, 14, 30, 60, 90].map(days => (
          <button
            key={days}
            onClick={() => setLookbackDays(days)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              lookbackDays === days
                ? 'bg-primary-500 text-white'
                : 'bg-card border border-border hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {days}D
          </button>
        ))}
      </div>

      {/* Correlation Result */}
      {loading ? (
        <div className="bg-card rounded-lg border border-border p-12 text-center">
          <div className="animate-pulse text-gray-500">Calculating correlation...</div>
        </div>
      ) : correlation ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card rounded-lg border border-border p-6 card-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Correlation</span>
              {correlation.correlation > 0 ? (
                <TrendingUp className="h-5 w-5 text-bullish" />
              ) : (
                <TrendingDown className="h-5 w-5 text-bearish" />
              )}
            </div>
            <div className="text-3xl font-bold mb-1">
              {correlation.correlation.toFixed(3)}
            </div>
            <div className="text-xs text-gray-500">
              {correlation.is_significant ? '✓ Significant' : '✗ Not significant'}
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-6 card-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">P-Value</span>
              <BarChart3 className="h-5 w-5 text-primary-500" />
            </div>
            <div className="text-3xl font-bold mb-1">
              {correlation.p_value.toFixed(4)}
            </div>
            <div className="text-xs text-gray-500">
              {correlation.p_value < 0.05 ? 'p < 0.05' : 'p ≥ 0.05'}
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-6 card-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Sample Size</span>
              <BarChart3 className="h-5 w-5 text-purple-500" />
            </div>
            <div className="text-3xl font-bold mb-1">
              {correlation.sample_size}
            </div>
            <div className="text-xs text-gray-500">
              Data points
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-card rounded-lg border border-border p-12 text-center text-gray-500">
          No correlation data available
        </div>
      )}

      {/* Explanation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          Understanding the Correlation
        </h3>
        <p className="text-sm text-blue-800 dark:text-blue-200">
          This analysis shows the Pearson correlation between news sentiment scores and 10-year Treasury yield changes.
          A positive correlation means bullish sentiment tends to coincide with yield increases, while negative correlation
          suggests sentiment and yields move in opposite directions. Statistical significance (p &lt; 0.05) indicates
          the relationship is unlikely to be due to chance.
        </p>
      </div>
    </div>
  )
}

