/**
 * Utility functions
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return format(d, 'MMM d, yyyy HH:mm')
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return formatDistanceToNow(d, { addSuffix: true })
}

export function formatSentimentScore(score: number): string {
  return score >= 0 ? `+${score.toFixed(3)}` : score.toFixed(3)
}

export function getSentimentColor(label: 'bullish' | 'bearish' | 'neutral'): string {
  switch (label) {
    case 'bullish':
      return 'text-bullish'
    case 'bearish':
      return 'text-bearish'
    case 'neutral':
      return 'text-neutral'
  }
}

export function getSentimentBgColor(label: 'bullish' | 'bearish' | 'neutral'): string {
  switch (label) {
    case 'bullish':
      return 'bg-bullish/10 text-bullish border-bullish/30'
    case 'bearish':
      return 'bg-bearish/10 text-bearish border-bearish/30'
    case 'neutral':
      return 'bg-neutral/10 text-neutral border-neutral/30'
  }
}

