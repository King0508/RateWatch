'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api, type TreasuryYields } from '@/lib/api'
import { format } from 'date-fns'

export default function MarketDataPage() {
  const [yields, setYields] = useState<TreasuryYields[]>([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const data = await api.getTreasuryYields(days)
        setYields(data)
      } catch (error) {
        console.error('Failed to fetch yields:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [days])

  const chartData = yields.map(item => ({
    date: format(new Date(item.timestamp), 'MMM d'),
    '2Y': item.us_2y,
    '5Y': item.us_5y,
    '10Y': item.us_10y,
    '30Y': item.us_30y,
  }))

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">
          Market Data
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Treasury yield curves and ETF prices
        </p>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        {[7, 14, 30, 60, 90].map(d => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              days === d
                ? 'bg-primary-500 text-white'
                : 'bg-card border border-border hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {d}D
          </button>
        ))}
      </div>

      {/* Treasury Yields Chart */}
      <div className="bg-card rounded-lg border border-border p-6 card-shadow">
        <h2 className="text-2xl font-semibold mb-4">Treasury Yield Curve</h2>
        {loading ? (
          <div className="h-96 flex items-center justify-center">
            <div className="animate-pulse text-gray-500">Loading chart...</div>
          </div>
        ) : yields.length === 0 ? (
          <div className="h-96 flex items-center justify-center text-gray-500">
            No market data available. Please refresh data from the dashboard.
          </div>
        ) : (
          <div className="w-full h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                />
                <YAxis
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  domain={['auto', 'auto']}
                  label={{ value: 'Yield (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="2Y" stroke="#10b981" strokeWidth={2} name="2-Year" />
                <Line type="monotone" dataKey="5Y" stroke="#0ea5e9" strokeWidth={2} name="5-Year" />
                <Line type="monotone" dataKey="10Y" stroke="#8b5cf6" strokeWidth={2} name="10-Year" />
                <Line type="monotone" dataKey="30Y" stroke="#f59e0b" strokeWidth={2} name="30-Year" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Latest Yields */}
      {yields.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: '2-Year', value: yields[yields.length - 1]?.us_2y, color: 'text-green-500' },
            { label: '5-Year', value: yields[yields.length - 1]?.us_5y, color: 'text-blue-500' },
            { label: '10-Year', value: yields[yields.length - 1]?.us_10y, color: 'text-purple-500' },
            { label: '30-Year', value: yields[yields.length - 1]?.us_30y, color: 'text-orange-500' },
          ].map(item => (
            <div key={item.label} className="bg-card rounded-lg border border-border p-4 card-shadow">
              <div className="text-sm text-gray-500 mb-1">{item.label}</div>
              <div className={`text-2xl font-bold ${item.color}`}>
                {item.value ? `${item.value.toFixed(2)}%` : 'N/A'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

