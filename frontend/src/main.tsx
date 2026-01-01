import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './styles/index.css'
import { initSentry, ErrorBoundary } from './lib/sentry'
import { initAnalytics } from './lib/analytics'

// Initialize error tracking and analytics
initSentry()
initAnalytics()

// Create TanStack Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Fallback UI for errors
const ErrorFallback = () => (
  <div className="min-h-screen bg-vellum flex items-center justify-center p-4">
    <div className="max-w-md text-center">
      <h1 className="font-garamond text-4xl font-bold text-midnight mb-4">
        Oops! Something went wrong
      </h1>
      <p className="font-sans text-faded-ink mb-6">
        We've been notified and are looking into it. Try refreshing the page.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="px-6 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 transition-colors"
      >
        Refresh Page
      </button>
    </div>
  </div>
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary fallback={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
