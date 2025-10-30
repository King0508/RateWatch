'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'
import type { SentimentAggregate } from '@/lib/types'
import { format } from 'date-fns'

interface TimeSeriesChartProps {
  hours?: number
}

export function TimeSeriesChart({ hours = 168 }: TimeSeriesChartProps) {
  const [data, setData] = useState<SentimentAggregate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getSentimentTimeSeries(hours)
        setData(response.data)
      } catch (error) {
        console.error('Failed to fetch timeseries:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [hours])

  if (loading) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Loading chart...</div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-500">
        No data available for the selected period
      </div>
    )
  }

  const chartData = data.map(item => ({
    timestamp: format(new Date(item.timestamp), 'MMM d HH:mm'),
    sentiment: parseFloat(item.avg_sentiment.toFixed(3)),
    articles: item.count,
  }))

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickMargin={10}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            domain={[-1, 1]}
            tickCount={9}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#fff'
            }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="sentiment"
            stroke="#0ea5e9"
            strokeWidth={2}
            dot={{ fill: '#0ea5e9', r: 3 }}
            activeDot={{ r: 5 }}
            name="Avg Sentiment"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

