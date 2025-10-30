'use client'

import { TrendingUp, TrendingDown, Activity, AlertTriangle } from 'lucide-react'
import type { Stats } from '@/lib/types'
import { cn } from '@/lib/utils'

interface MetricsPanelProps {
  stats: Stats
}

export function MetricsPanel({ stats }: MetricsPanelProps) {
  const sentimentMood = stats.avg_sentiment > 0.1 ? 'bullish' : stats.avg_sentiment < -0.1 ? 'bearish' : 'neutral'

  const metrics = [
    {
      label: 'Total Articles',
      value: stats.news_count.toLocaleString(),
      icon: Activity,
      color: 'text-blue-500',
    },
    {
      label: 'High Impact',
      value: stats.high_impact_count.toLocaleString(),
      icon: AlertTriangle,
      color: 'text-orange-500',
    },
    {
      label: 'Avg Sentiment',
      value: stats.avg_sentiment.toFixed(3),
      icon: stats.avg_sentiment > 0 ? TrendingUp : TrendingDown,
      color: sentimentMood === 'bullish' ? 'text-bullish' : sentimentMood === 'bearish' ? 'text-bearish' : 'text-neutral',
      badge: sentimentMood,
    },
    {
      label: 'Treasury Data Points',
      value: stats.treasury_count.toLocaleString(),
      icon: Activity,
      color: 'text-purple-500',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="bg-card rounded-lg border border-border p-6 card-shadow hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {metric.label}
            </span>
            <metric.icon className={cn('h-5 w-5', metric.color)} />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-3xl font-bold">{metric.value}</span>
            {metric.badge && (
              <span
                className={cn(
                  'text-xs font-semibold px-2 py-1 rounded capitalize',
                  metric.badge === 'bullish' && 'bg-bullish/10 text-bullish',
                  metric.badge === 'bearish' && 'bg-bearish/10 text-bearish',
                  metric.badge === 'neutral' && 'bg-neutral/10 text-neutral'
                )}
              >
                {metric.badge}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

