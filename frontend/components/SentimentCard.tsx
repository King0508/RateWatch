'use client'

import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { NewsItem } from '@/lib/types'
import { formatRelativeTime, getSentimentBgColor, cn } from '@/lib/utils'

interface SentimentCardProps {
  item: NewsItem
}

export function SentimentCard({ item }: SentimentCardProps) {
  const SentimentIcon = item.sentiment_label === 'bullish' 
    ? TrendingUp 
    : item.sentiment_label === 'bearish' 
    ? TrendingDown 
    : Minus

  return (
    <div className="bg-card rounded-lg border border-border p-5 hover:shadow-lg transition-all duration-200 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg leading-tight mb-2 line-clamp-2">
            {item.title}
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="font-medium">{item.source}</span>
            <span>•</span>
            <span>{formatRelativeTime(item.timestamp)}</span>
          </div>
        </div>
        {item.is_high_impact && (
          <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-xs font-semibold rounded flex-shrink-0">
            HIGH IMPACT
          </span>
        )}
      </div>

      {/* Summary */}
      {item.summary && (
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 line-clamp-2">
          {item.summary}
        </p>
      )}

      {/* Sentiment Badge */}
      <div className="flex items-center gap-4 mb-4">
        <div className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md border font-medium text-sm',
          getSentimentBgColor(item.sentiment_label)
        )}>
          <SentimentIcon className="h-4 w-4" />
          <span className="capitalize">{item.sentiment_label}</span>
          <span className="ml-1 opacity-75">
            {item.sentiment_score >= 0 ? '+' : ''}{item.sentiment_score.toFixed(2)}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          Confidence: <span className="font-medium">{(item.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Entities */}
      {(item.entities.fed_officials.length > 0 || 
        item.entities.economic_indicators.length > 0 || 
        item.entities.treasury_instruments.length > 0) && (
        <div className="flex flex-wrap gap-2 mb-4">
          {item.entities.fed_officials.slice(0, 2).map((entity) => (
            <span key={entity} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded">
              👤 {entity}
            </span>
          ))}
          {item.entities.economic_indicators.slice(0, 3).map((entity) => (
            <span key={entity} className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded">
              📊 {entity}
            </span>
          ))}
          {item.entities.treasury_instruments.slice(0, 2).map((entity) => (
            <span key={entity} className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs rounded">
              💹 {entity}
            </span>
          ))}
        </div>
      )}

      {/* Link */}
      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-primary-500 hover:text-primary-600 transition-colors"
        >
          Read full article
          <ExternalLink className="h-3 w-3" />
        </a>
      )}
    </div>
  )
}

