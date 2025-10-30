'use client'

import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { Navbar } from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>RateWatch - Sentiment-Market Analytics</title>
        <meta name="description" content="Real-time correlation between financial news sentiment and Treasury market movements" />
      </head>
      <body className={inter.className}>
        <ThemeProvider>
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1">
              {children}
            </main>
            <footer className="border-t border-gray-200 dark:border-gray-800 py-4 px-6">
              <div className="max-w-7xl mx-auto text-center text-sm text-gray-500 dark:text-gray-400">
                RateWatch - Sentiment-Market Correlation Analytics
              </div>
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}

