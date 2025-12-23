/**
 * InconsistencyList - Display timeline inconsistencies and allow resolution
 */

import { useState, useEffect } from 'react';
import { Severity, getSeverityColor, getSeverityIcon } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';

interface InconsistencyListProps {
  manuscriptId: string;
}

export default function InconsistencyList({ manuscriptId }: InconsistencyListProps) {
  const { inconsistencies, setInconsistencies, removeInconsistency } = useTimelineStore();
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<Severity | 'ALL'>('ALL');

  useEffect(() => {
    loadInconsistencies();
  }, [manuscriptId]);

  const loadInconsistencies = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await timelineApi.listInconsistencies(manuscriptId);
      setInconsistencies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load inconsistencies');
    } finally {
      setLoading(false);
    }
  };

  const handleDetect = async () => {
    try {
      setDetecting(true);
      setError(null);
      const result = await timelineApi.detectInconsistencies(manuscriptId);
      setInconsistencies(result.data);
    } catch (err) {
      setError('Failed to detect inconsistencies: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setDetecting(false);
    }
  };

  const handleResolve = async (inconsistencyId: string) => {
    if (!confirm('Mark this inconsistency as resolved?')) {
      return;
    }

    try {
      await timelineApi.resolveInconsistency(inconsistencyId);
      removeInconsistency(inconsistencyId);
    } catch (err) {
      alert('Failed to resolve inconsistency: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const filteredInconsistencies = inconsistencies.filter((inc) => {
    return filterSeverity === 'ALL' || inc.severity === filterSeverity;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading inconsistencies...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui">
        <button
          onClick={handleDetect}
          disabled={detecting}
          className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 flex items-center justify-center gap-2"
          style={{ borderRadius: '2px' }}
        >
          {detecting && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
          {detecting ? 'Detecting...' : '🔍 Detect Inconsistencies'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-redline/10 border-b border-redline">
          <p className="text-sm font-sans text-redline">{error}</p>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-ui bg-white">
        {['ALL', ...Object.values(Severity)].map((severity) => (
          <button
            key={severity}
            onClick={() => setFilterSeverity(severity as Severity | 'ALL')}
            className={`
              px-4 py-2 text-sm font-sans whitespace-nowrap transition-colors flex items-center gap-1
              ${filterSeverity === severity
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            {severity !== 'ALL' && getSeverityIcon(severity as Severity)}
            <span>{severity}</span>
            <span className="ml-1 text-xs">
              ({severity === 'ALL' ? inconsistencies.length : inconsistencies.filter((i) => i.severity === severity).length})
            </span>
          </button>
        ))}
      </div>

      {/* Inconsistency List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredInconsistencies.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="text-4xl mb-3">✅</div>
            <p className="text-midnight font-garamond font-semibold mb-2">
              {inconsistencies.length === 0
                ? 'No inconsistencies detected'
                : `No ${filterSeverity.toLowerCase()} severity issues`}
            </p>
            <p className="text-sm text-faded-ink font-sans max-w-xs">
              {inconsistencies.length === 0
                ? 'Your timeline is consistent! Click "Detect Inconsistencies" to check again.'
                : 'Try a different severity filter.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredInconsistencies.map((inc) => (
              <div
                key={inc.id}
                className="border border-slate-ui bg-white p-4"
                style={{ borderRadius: '2px' }}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getSeverityIcon(inc.severity)}</span>
                    <span
                      className="text-xs font-sans px-2 py-0.5 text-white"
                      style={{
                        backgroundColor: getSeverityColor(inc.severity),
                        borderRadius: '2px',
                      }}
                    >
                      {inc.severity}
                    </span>
                    <span className="text-xs font-sans text-faded-ink uppercase">
                      {inc.inconsistency_type.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <button
                    onClick={() => handleResolve(inc.id)}
                    className="text-sm font-sans text-bronze hover:underline"
                  >
                    Resolve
                  </button>
                </div>

                {/* Description */}
                <p className="text-sm font-serif text-midnight">
                  {inc.description}
                </p>

                {/* Metadata */}
                <div className="mt-2 pt-2 border-t border-slate-ui">
                  <p className="text-xs text-faded-ink font-sans">
                    Detected: {new Date(inc.created_at).toLocaleString()}
                  </p>
                  {inc.affected_event_ids.length > 0 && (
                    <p className="text-xs text-faded-ink font-sans">
                      Affects {inc.affected_event_ids.length} event{inc.affected_event_ids.length > 1 ? 's' : ''}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
