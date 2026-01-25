/**
 * CostEstimate - Shows estimated and actual AI costs
 * Used before and after AI operations for transparency
 */

import { useState, useEffect } from 'react';

interface CostEstimateProps {
  /** Estimated cost before the operation */
  estimatedCost?: number;
  /** Actual cost after the operation */
  actualCost?: number;
  /** Type of AI operation */
  operationType?: 'recap' | 'coach' | 'brainstorm' | 'analysis' | 'generic';
  /** Show in compact mode */
  compact?: boolean;
  /** Show tooltip on hover */
  showTooltip?: boolean;
  /** Custom class name */
  className?: string;
}

const OPERATION_LABELS: Record<string, string> = {
  recap: 'Chapter Recap',
  coach: 'Writing Suggestion',
  brainstorm: 'Brainstorm Ideas',
  analysis: 'AI Analysis',
  generic: 'AI Request',
};

const TYPICAL_COSTS: Record<string, { min: number; max: number }> = {
  recap: { min: 0.005, max: 0.02 },
  coach: { min: 0.0005, max: 0.002 },
  brainstorm: { min: 0.003, max: 0.01 },
  analysis: { min: 0.002, max: 0.008 },
  generic: { min: 0.001, max: 0.01 },
};

export default function CostEstimate({
  estimatedCost,
  actualCost,
  operationType = 'generic',
  compact = false,
  showTooltip = true,
  className = '',
}: CostEstimateProps) {
  const [showDetails, setShowDetails] = useState(false);

  // Get typical cost range for this operation
  const typicalRange = TYPICAL_COSTS[operationType];
  const label = OPERATION_LABELS[operationType];

  // Determine which cost to display
  const displayCost = actualCost ?? estimatedCost;
  const isEstimate = actualCost === undefined && estimatedCost !== undefined;

  if (!displayCost && !typicalRange) {
    return null;
  }

  // Format cost for display
  const formatCost = (cost: number) => {
    if (cost < 0.01) {
      return `$${cost.toFixed(4)}`;
    }
    return `$${cost.toFixed(3)}`;
  };

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1 text-xs font-sans ${className}`}
        title={showTooltip ? `${isEstimate ? 'Estimated' : 'Actual'} cost: ${formatCost(displayCost || 0)}` : undefined}
      >
        <span className="text-faded-ink">
          {isEstimate ? '~' : ''}
          {formatCost(displayCost || typicalRange?.min || 0)}
        </span>
      </span>
    );
  }

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => showTooltip && setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      <div className="flex items-center gap-2 px-2 py-1 bg-bronze/5 border border-bronze/20 rounded text-xs font-sans">
        <svg
          className="w-3 h-3 text-bronze"
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
        <span className="text-midnight">
          {isEstimate ? 'Est: ' : 'Cost: '}
          <span className="font-medium text-bronze">
            {displayCost ? formatCost(displayCost) : `${formatCost(typicalRange?.min || 0)} - ${formatCost(typicalRange?.max || 0)}`}
          </span>
        </span>
      </div>

      {/* Tooltip with details */}
      {showDetails && (
        <div className="absolute bottom-full left-0 mb-2 p-3 bg-white border border-slate-ui rounded-lg shadow-lg z-50 w-48">
          <p className="text-xs font-semibold text-midnight mb-2">{label}</p>
          {displayCost ? (
            <>
              <p className="text-xs text-faded-ink">
                {isEstimate ? 'Estimated' : 'Actual'} cost: <span className="font-medium text-bronze">{formatCost(displayCost)}</span>
              </p>
              <p className="text-xs text-faded-ink mt-1">
                Typical range: {formatCost(typicalRange?.min || 0)} - {formatCost(typicalRange?.max || 0)}
              </p>
            </>
          ) : (
            <p className="text-xs text-faded-ink">
              Typical cost: {formatCost(typicalRange?.min || 0)} - {formatCost(typicalRange?.max || 0)}
            </p>
          )}
          <p className="text-xs text-bronze/70 mt-2">
            Powered by OpenRouter
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Hook to track AI usage costs
 */
export function useAICostTracking() {
  const [totalCost, setTotalCost] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);

  // Load saved stats
  useEffect(() => {
    const saved = localStorage.getItem('ai_usage_stats');
    if (saved) {
      try {
        const stats = JSON.parse(saved);
        setTotalCost(stats.cost || 0);
        setTotalTokens(stats.tokens || 0);
      } catch (e) {
        console.error('Failed to load AI usage stats');
      }
    }
  }, []);

  // Track a new AI operation
  const trackUsage = (cost: number, tokens: number) => {
    const newCost = totalCost + cost;
    const newTokens = totalTokens + tokens;

    setTotalCost(newCost);
    setTotalTokens(newTokens);

    // Save to localStorage
    localStorage.setItem('ai_usage_stats', JSON.stringify({
      cost: newCost,
      tokens: newTokens,
      lastUpdated: new Date().toISOString(),
    }));
  };

  // Reset stats
  const resetStats = () => {
    setTotalCost(0);
    setTotalTokens(0);
    localStorage.removeItem('ai_usage_stats');
  };

  return {
    totalCost,
    totalTokens,
    trackUsage,
    resetStats,
  };
}
