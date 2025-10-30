'use client'

import { SentimentCard } from './SentimentCard'
import type { NewsItem } from '@/lib/types'

interface SentimentFeedProps {
  news: NewsItem[]
  loading?: boolean
}

export function SentimentFeed({ news, loading }: SentimentFeedProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-card rounded-lg border border-border p-5 animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-3"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          </div>
        ))}
      </div>
    )
  }

  if (news.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No news articles found. Try refreshing the data.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {news.map((item) => (
        <SentimentCard key={item.id} item={item} />
      ))}
    </div>
  )
}

