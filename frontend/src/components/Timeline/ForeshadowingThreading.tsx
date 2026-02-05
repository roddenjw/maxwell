/**
 * ForeshadowingThreading - Visual threading UI for foreshadowing connections
 *
 * Shows setup/payoff pairs as connected threads across the story timeline,
 * with auto-detection capabilities and visual connection lines.
 */

import { useState, useEffect, useMemo } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { foreshadowingApi } from '@/lib/api';
import type { ForeshadowingPair, ForeshadowingType } from '@/types/foreshadowing';
import {
  FORESHADOWING_TYPE_LABELS,
  FORESHADOWING_TYPE_ICONS,
} from '@/types/foreshadowing';

interface ForeshadowingThreadingProps {
  manuscriptId: string;
}

interface DetectedSetup {
  text: string;
  chapter_id: string;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  setup_type: string;
  confidence: number;
  context: string;
  keywords: string[];
  suggestion: string;
}

interface DetectedPayoff {
  text: string;
  chapter_id: string;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  setup_reference: string;
  confidence: number;
  context: string;
}

interface DetectedMatch {
  setup: DetectedSetup;
  payoff: DetectedPayoff;
  similarity_score: number;
  match_type: string;
}

interface DetectionResults {
  setups: DetectedSetup[];
  payoffs: DetectedPayoff[];
  matches: DetectedMatch[];
  suggestions: Array<{
    type: string;
    title: string;
    message: string;
    count: number;
  }>;
  stats: {
    total_setups: number;
    total_payoffs: number;
    matched_pairs: number;
    unmatched_setups: number;
  };
}

// Thread colors by type
const THREAD_COLORS: Record<string, { main: string; light: string }> = {
  CHEKHOV_GUN: { main: '#ef4444', light: 'rgba(239, 68, 68, 0.2)' },
  PROPHECY: { main: '#8b5cf6', light: 'rgba(139, 92, 246, 0.2)' },
  SYMBOL: { main: '#10b981', light: 'rgba(16, 185, 129, 0.2)' },
  HINT: { main: '#f59e0b', light: 'rgba(245, 158, 11, 0.2)' },
  PARALLEL: { main: '#3b82f6', light: 'rgba(59, 130, 246, 0.2)' },
};

export default function ForeshadowingThreading({ manuscriptId }: ForeshadowingThreadingProps) {
  const { events } = useTimelineStore();
  const [pairs, setPairs] = useState<ForeshadowingPair[]>([]);
  const [detectionResults, setDetectionResults] = useState<DetectionResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [selectedSetup, setSelectedSetup] = useState<DetectedSetup | null>(null);
  const [showDetected, setShowDetected] = useState(false);
  const [filterType, setFilterType] = useState<string | null>(null);

  // Load existing pairs
  useEffect(() => {
    loadPairs();
  }, [manuscriptId]);

  const loadPairs = async () => {
    setLoading(true);
    try {
      const data = await foreshadowingApi.getPairs(manuscriptId);
      setPairs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load foreshadowing pairs:', err);
      setPairs([]);
    } finally {
      setLoading(false);
    }
  };

  // Run auto-detection
  const runDetection = async () => {
    setDetecting(true);
    try {
      const response = await fetch(`/api/foreshadowing/detect/${manuscriptId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ min_confidence: 0.5 }),
      });
      const result = await response.json();
      if (result.success) {
        setDetectionResults(result.data);
        setShowDetected(true);
      }
    } catch (err) {
      console.error('Detection failed:', err);
    } finally {
      setDetecting(false);
    }
  };

  // Confirm a detected pair
  const confirmDetection = async (setup: DetectedSetup, payoff?: DetectedPayoff) => {
    try {
      const response = await fetch(`/api/foreshadowing/detect/${manuscriptId}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ setup, payoff }),
      });
      const result = await response.json();
      if (result.success) {
        setPairs([result.data, ...pairs]);
        // Remove from detection results
        if (detectionResults) {
          setDetectionResults({
            ...detectionResults,
            setups: detectionResults.setups.filter(s => s.text !== setup.text),
            matches: detectionResults.matches.filter(m => m.setup.text !== setup.text),
          });
        }
      }
    } catch (err) {
      console.error('Failed to confirm detection:', err);
    }
  };

  // Filter pairs by type
  const filteredPairs = useMemo(() => {
    if (!filterType) return pairs;
    return pairs.filter(p => p.foreshadowing_type === filterType);
  }, [pairs, filterType]);

  // Group pairs by resolution status
  const { resolved, unresolved } = useMemo(() => {
    const resolved = filteredPairs.filter(p => p.is_resolved);
    const unresolved = filteredPairs.filter(p => !p.is_resolved);
    return { resolved, unresolved };
  }, [filteredPairs]);

  // Calculate thread positions for visualization
  const maxOrder = events.length > 0 ? Math.max(...events.map(e => e.order_index)) : 10;

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 border-2 border-bronze border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-faded-ink font-sans">Loading foreshadowing data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="font-garamond text-lg text-midnight">
              Foreshadowing Threading
            </h3>
            <p className="text-sm font-sans text-faded-ink">
              Visualize narrative threads connecting setups to payoffs
            </p>
          </div>
          <button
            onClick={runDetection}
            disabled={detecting}
            className={`
              px-4 py-2 text-sm font-sans transition-colors
              ${detecting
                ? 'bg-slate-ui text-faded-ink cursor-wait'
                : 'bg-bronze text-white hover:bg-opacity-90'
              }
            `}
            style={{ borderRadius: '2px' }}
          >
            {detecting ? 'Detecting...' : '🔍 Auto-Detect'}
          </button>
        </div>

        {/* Type filters */}
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setFilterType(null)}
            className={`px-3 py-1 text-xs font-sans transition-colors ${
              !filterType ? 'bg-bronze text-white' : 'bg-vellum text-midnight hover:bg-bronze/10'
            }`}
            style={{ borderRadius: '2px' }}
          >
            All
          </button>
          {Object.entries(FORESHADOWING_TYPE_LABELS).map(([type, label]) => (
            <button
              key={type}
              onClick={() => setFilterType(filterType === type ? null : type)}
              className={`px-3 py-1 text-xs font-sans transition-colors flex items-center gap-1 ${
                filterType === type ? 'bg-bronze text-white' : 'bg-vellum text-midnight hover:bg-bronze/10'
              }`}
              style={{ borderRadius: '2px' }}
            >
              <span>{FORESHADOWING_TYPE_ICONS[type as ForeshadowingType]}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats bar */}
      <div className="p-3 border-b border-slate-ui bg-vellum flex items-center gap-6">
        <div className="text-center">
          <p className="text-lg font-garamond text-midnight font-semibold">{pairs.length}</p>
          <p className="text-xs font-sans text-faded-ink">Total Pairs</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-garamond text-sage font-semibold">{resolved.length}</p>
          <p className="text-xs font-sans text-faded-ink">Resolved</p>
        </div>
        <div className="text-center">
          <p className={`text-lg font-garamond font-semibold ${unresolved.length > 0 ? 'text-bronze' : 'text-midnight'}`}>
            {unresolved.length}
          </p>
          <p className="text-xs font-sans text-faded-ink">Unresolved</p>
        </div>
        {detectionResults && (
          <div className="ml-auto text-center">
            <p className="text-lg font-garamond text-purple-600 font-semibold">
              {detectionResults.stats.total_setups}
            </p>
            <p className="text-xs font-sans text-faded-ink">Detected</p>
          </div>
        )}
      </div>

      {/* Main visualization area */}
      <div className="flex-1 overflow-auto">
        {/* Detection results panel */}
        {showDetected && detectionResults && (
          <div className="p-4 border-b border-slate-ui bg-purple-50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-garamond text-lg text-midnight">
                Auto-Detected Foreshadowing
              </h4>
              <button
                onClick={() => setShowDetected(false)}
                className="text-faded-ink hover:text-midnight text-sm font-sans"
              >
                Hide
              </button>
            </div>

            {/* Suggestions */}
            {detectionResults.suggestions.length > 0 && (
              <div className="mb-4 space-y-2">
                {detectionResults.suggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded text-sm font-sans ${
                      suggestion.type === 'warning'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : suggestion.type === 'success'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'bg-blue-100 text-blue-800 border border-blue-200'
                    }`}
                  >
                    <strong>{suggestion.title}:</strong> {suggestion.message}
                  </div>
                ))}
              </div>
            )}

            {/* Detected setups */}
            <div className="space-y-3">
              <p className="text-xs font-sans text-faded-ink uppercase">
                Detected Setups ({detectionResults.setups.length})
              </p>
              <div className="grid gap-3 max-h-64 overflow-auto">
                {detectionResults.setups.slice(0, 10).map((setup, idx) => {
                  const colors = THREAD_COLORS[setup.setup_type] || THREAD_COLORS.HINT;
                  const matchedPayoff = detectionResults.matches.find(
                    m => m.setup.text === setup.text
                  )?.payoff;

                  return (
                    <div
                      key={idx}
                      className="p-3 bg-white border transition-all hover:shadow-md cursor-pointer"
                      style={{
                        borderRadius: '2px',
                        borderColor: colors.main,
                        borderLeftWidth: '4px',
                      }}
                      onClick={() => setSelectedSetup(selectedSetup?.text === setup.text ? null : setup)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span>{FORESHADOWING_TYPE_ICONS[setup.setup_type as ForeshadowingType] || '💡'}</span>
                          <span className="text-xs font-sans text-faded-ink">
                            {FORESHADOWING_TYPE_LABELS[setup.setup_type as ForeshadowingType] || setup.setup_type}
                          </span>
                          <span
                            className="text-xs font-sans px-1.5 py-0.5"
                            style={{
                              backgroundColor: colors.light,
                              color: colors.main,
                              borderRadius: '2px',
                            }}
                          >
                            {(setup.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <span className="text-xs font-sans text-faded-ink">
                          {setup.chapter_title}
                        </span>
                      </div>

                      <p className="text-sm font-serif text-midnight mb-2 line-clamp-2">
                        "{setup.text}"
                      </p>

                      {selectedSetup?.text === setup.text && (
                        <div className="mt-3 pt-3 border-t border-slate-ui">
                          <p className="text-xs font-sans text-faded-ink mb-2">{setup.suggestion}</p>
                          {matchedPayoff && (
                            <div className="p-2 bg-green-50 border border-green-200 rounded mb-2">
                              <p className="text-xs font-sans text-green-800 mb-1">
                                <strong>Potential payoff found:</strong>
                              </p>
                              <p className="text-sm font-serif text-green-900">
                                "{matchedPayoff.text}"
                              </p>
                            </div>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              confirmDetection(setup, matchedPayoff);
                            }}
                            className="px-3 py-1.5 bg-bronze text-white text-xs font-sans hover:bg-opacity-90"
                            style={{ borderRadius: '2px' }}
                          >
                            Confirm & Track
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {detectionResults.setups.length > 10 && (
                <p className="text-xs font-sans text-faded-ink text-center">
                  + {detectionResults.setups.length - 10} more detected setups
                </p>
              )}
            </div>
          </div>
        )}

        {/* Thread visualization */}
        <div className="p-4">
          <h4 className="text-xs font-sans text-faded-ink uppercase mb-4">
            Narrative Threads
          </h4>

          {filteredPairs.length === 0 ? (
            <div className="text-center py-12">
              <span className="text-5xl mb-4 block">🧵</span>
              <p className="text-midnight font-garamond text-lg font-semibold mb-2">
                No foreshadowing threads yet
              </p>
              <p className="text-sm font-sans text-faded-ink max-w-sm mx-auto">
                Click "Auto-Detect" to find potential setups, or manually add them in the Foreshadowing Tracker.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Unresolved threads (Chekhov violations) */}
              {unresolved.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-amber-500">⚠️</span>
                    <span className="text-sm font-sans font-semibold text-amber-700">
                      Unresolved Setups ({unresolved.length})
                    </span>
                  </div>
                  <div className="space-y-2">
                    {unresolved.map(pair => (
                      <ThreadCard key={pair.id} pair={pair} maxOrder={maxOrder} events={events} />
                    ))}
                  </div>
                </div>
              )}

              {/* Resolved threads */}
              {resolved.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-green-500">✓</span>
                    <span className="text-sm font-sans font-semibold text-green-700">
                      Resolved Threads ({resolved.length})
                    </span>
                  </div>
                  <div className="space-y-2">
                    {resolved.map(pair => (
                      <ThreadCard key={pair.id} pair={pair} maxOrder={maxOrder} events={events} resolved />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Thread card component
interface ThreadCardProps {
  pair: ForeshadowingPair;
  maxOrder: number;
  events: Array<{ id: string; order_index: number }>;
  resolved?: boolean;
}

function ThreadCard({ pair, maxOrder, events, resolved }: ThreadCardProps) {
  const colors = THREAD_COLORS[pair.foreshadowing_type] || THREAD_COLORS.HINT;

  // Find event positions
  const setupEvent = events.find(e => e.id === pair.foreshadowing_event_id);
  const payoffEvent = pair.payoff_event_id
    ? events.find(e => e.id === pair.payoff_event_id)
    : null;

  const setupPos = setupEvent ? (setupEvent.order_index / maxOrder) * 100 : 0;
  const payoffPos = payoffEvent ? (payoffEvent.order_index / maxOrder) * 100 : 100;

  return (
    <div
      className="p-3 border bg-white transition-all hover:shadow-sm"
      style={{
        borderRadius: '2px',
        borderColor: resolved ? colors.main : '#f59e0b',
        borderLeftWidth: '4px',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span>{FORESHADOWING_TYPE_ICONS[pair.foreshadowing_type as ForeshadowingType] || '💡'}</span>
        <span className="text-xs font-sans text-faded-ink">
          {FORESHADOWING_TYPE_LABELS[pair.foreshadowing_type as ForeshadowingType] || pair.foreshadowing_type}
        </span>
        {!resolved && (
          <span className="text-xs font-sans px-2 py-0.5 bg-amber-100 text-amber-700 rounded">
            Needs payoff
          </span>
        )}
      </div>

      {/* Thread visualization */}
      <div className="relative h-8 bg-slate-100 rounded my-3">
        {/* Setup marker */}
        <div
          className="absolute w-4 h-4 rounded-full transform -translate-x-1/2 top-1/2 -translate-y-1/2 border-2 border-white z-10"
          style={{ left: `${setupPos}%`, backgroundColor: colors.main }}
          title="Setup"
        />

        {/* Thread line */}
        {resolved && payoffEvent && (
          <>
            <div
              className="absolute h-1 top-1/2 -translate-y-1/2"
              style={{
                left: `${setupPos}%`,
                width: `${payoffPos - setupPos}%`,
                backgroundColor: colors.main,
                opacity: 0.5,
              }}
            />
            {/* Payoff marker */}
            <div
              className="absolute w-4 h-4 rounded-full transform -translate-x-1/2 top-1/2 -translate-y-1/2 border-2 border-white z-10"
              style={{ left: `${payoffPos}%`, backgroundColor: colors.main }}
              title="Payoff"
            />
          </>
        )}

        {/* Dangling thread for unresolved */}
        {!resolved && (
          <div
            className="absolute h-1 top-1/2 -translate-y-1/2"
            style={{
              left: `${setupPos}%`,
              width: `${100 - setupPos}%`,
              background: `linear-gradient(to right, ${colors.main}, transparent)`,
              opacity: 0.3,
            }}
          />
        )}
      </div>

      {/* Text content */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-xs font-sans text-faded-ink uppercase mb-1">Setup</p>
          <p className="font-serif text-midnight line-clamp-2">"{pair.foreshadowing_text}"</p>
        </div>
        {resolved && pair.payoff_text && (
          <div>
            <p className="text-xs font-sans text-faded-ink uppercase mb-1">Payoff</p>
            <p className="font-serif text-midnight line-clamp-2">"{pair.payoff_text}"</p>
          </div>
        )}
      </div>
    </div>
  );
}
