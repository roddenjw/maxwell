/**
 * BalanceWidget - Shows OpenRouter balance in header
 * Provides quick access to AI settings and warns on low balance
 */

import { useState, useEffect, useCallback } from 'react';

interface BalanceWidgetProps {
  onOpenSettings?: () => void;
  className?: string;
}

interface BalanceData {
  balance: number | null;
  limit: number | null;
  loading: boolean;
  error: boolean;
  lastFetched: Date | null;
}

// Rate limit: fetch balance at most once per 5 minutes
const FETCH_INTERVAL = 5 * 60 * 1000;

export default function BalanceWidget({ onOpenSettings, className = '' }: BalanceWidgetProps) {
  const [data, setData] = useState<BalanceData>({
    balance: null,
    limit: null,
    loading: false,
    error: false,
    lastFetched: null,
  });

  const hasApiKey = !!localStorage.getItem('openrouter_api_key');

  const fetchBalance = useCallback(async () => {
    const apiKey = localStorage.getItem('openrouter_api_key');
    if (!apiKey) {
      setData(prev => ({ ...prev, balance: null, limit: null, error: false }));
      return;
    }

    // Rate limiting
    if (data.lastFetched && Date.now() - data.lastFetched.getTime() < FETCH_INTERVAL) {
      return;
    }

    setData(prev => ({ ...prev, loading: true }));

    try {
      const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        // OpenRouter returns limit_remaining and limit
        const balance = result.data?.limit_remaining ?? result.data?.usage ?? null;
        const limit = result.data?.limit ?? null;

        setData({
          balance,
          limit,
          loading: false,
          error: false,
          lastFetched: new Date(),
        });
      } else {
        setData(prev => ({ ...prev, loading: false, error: true }));
      }
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      setData(prev => ({ ...prev, loading: false, error: true }));
    }
  }, [data.lastFetched]);

  // Fetch on mount and when API key changes
  useEffect(() => {
    if (hasApiKey) {
      fetchBalance();
    }

    // Set up periodic refresh
    const interval = setInterval(() => {
      if (hasApiKey) {
        fetchBalance();
      }
    }, FETCH_INTERVAL);

    return () => clearInterval(interval);
  }, [hasApiKey, fetchBalance]);

  // Listen for storage changes (API key updates)
  useEffect(() => {
    const handleStorage = () => {
      fetchBalance();
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [fetchBalance]);

  // Don't show if no API key
  if (!hasApiKey) {
    return (
      <button
        onClick={onOpenSettings}
        className={`flex items-center gap-2 px-3 py-1.5 text-sm font-sans text-bronze hover:bg-bronze/10 rounded transition-colors ${className}`}
        title="Enable AI features"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span>Enable AI</span>
      </button>
    );
  }

  // Determine balance status
  const isLowBalance = data.balance !== null && data.balance < 1;
  const isCriticalBalance = data.balance !== null && data.balance < 0.1;

  return (
    <button
      onClick={onOpenSettings}
      className={`flex items-center gap-2 px-3 py-1.5 text-sm font-sans rounded transition-colors ${
        isCriticalBalance
          ? 'bg-red-100 text-red-700 hover:bg-red-200'
          : isLowBalance
          ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
          : 'text-faded-ink hover:bg-vellum'
      } ${className}`}
      title={data.error ? 'Failed to fetch balance' : 'AI balance (click for settings)'}
    >
      {/* Icon */}
      <svg
        className={`w-4 h-4 ${isCriticalBalance ? 'text-red-500' : isLowBalance ? 'text-yellow-500' : 'text-bronze'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>

      {/* Balance display */}
      {data.loading ? (
        <span className="text-faded-ink">...</span>
      ) : data.error ? (
        <span className="text-red-500">!</span>
      ) : data.balance !== null ? (
        <span className={isCriticalBalance ? 'text-red-700 font-semibold' : isLowBalance ? 'text-yellow-700' : ''}>
          ${data.balance.toFixed(2)}
        </span>
      ) : (
        <span className="text-faded-ink">AI</span>
      )}

      {/* Low balance warning indicator */}
      {isCriticalBalance && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
        </span>
      )}
    </button>
  );
}
