'use client'

import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

interface RefreshButtonProps {
  onRefresh?: () => void
}

export function RefreshButton({ onRefresh }: RefreshButtonProps) {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<string>('')

  const handleRefresh = async () => {
    setLoading(true)
    setStatus('Fetching data...')
    
    try {
      await api.refreshData({ hours: 24, limit: 100 })
      setStatus('Data refresh initiated')
      
      // Wait a bit for data to be processed
      setTimeout(() => {
        onRefresh?.()
        setStatus('')
      }, 3000)
    } catch (error) {
      setStatus('Failed to refresh data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      {status && (
        <span className="text-sm text-gray-500">{status}</span>
      )}
      <button
        onClick={handleRefresh}
        disabled={loading}
        className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        Refresh Data
      </button>
    </div>
  )
}

