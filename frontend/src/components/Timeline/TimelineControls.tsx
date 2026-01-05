/**
 * TimelineControls - Filter controls and validation button for Timeline Orchestrator
 */

import { useState } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';

interface TimelineControlsProps {
  manuscriptId: string;
  onValidate?: () => void;
  showTeachingToggle?: boolean;
}

export default function TimelineControls({
  manuscriptId,
  onValidate,
  showTeachingToggle = false,
}: TimelineControlsProps) {
  const {
    filterByResolved,
    setFilterByResolved,
    showTeachingMoments,
    toggleTeachingMoments,
    runValidation,
  } = useTimelineStore();

  const [validating, setValidating] = useState(false);

  const handleRunValidation = async () => {
    try {
      setValidating(true);
      await runValidation(manuscriptId);
      onValidate?.();
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Failed to run validation: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="p-4 border-b border-slate-ui bg-white space-y-3">
      {/* Run Validation Button */}
      <button
        onClick={handleRunValidation}
        disabled={validating}
        className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
        style={{ borderRadius: '2px' }}
      >
        {validating && (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        )}
        {validating ? 'Validating Timeline...' : '🔍 Run Validation'}
      </button>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Resolution Filter */}
        <div className="flex items-center gap-1 flex-1">
          <span className="text-xs font-sans text-faded-ink whitespace-nowrap">Show:</span>
          <div className="flex border border-slate-ui overflow-hidden" style={{ borderRadius: '2px' }}>
            <button
              onClick={() => setFilterByResolved('all')}
              className={`px-3 py-1 text-xs font-sans transition-colors ${
                filterByResolved === 'all'
                  ? 'bg-bronze text-white'
                  : 'bg-white text-faded-ink hover:bg-vellum'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterByResolved('pending')}
              className={`px-3 py-1 text-xs font-sans border-l border-slate-ui transition-colors ${
                filterByResolved === 'pending'
                  ? 'bg-bronze text-white'
                  : 'bg-white text-faded-ink hover:bg-vellum'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setFilterByResolved('resolved')}
              className={`px-3 py-1 text-xs font-sans border-l border-slate-ui transition-colors ${
                filterByResolved === 'resolved'
                  ? 'bg-bronze text-white'
                  : 'bg-white text-faded-ink hover:bg-vellum'
              }`}
            >
              Resolved
            </button>
          </div>
        </div>

        {/* Teaching Moments Toggle */}
        {showTeachingToggle && (
          <button
            onClick={toggleTeachingMoments}
            className={`px-3 py-1 text-xs font-sans border border-slate-ui transition-colors ${
              showTeachingMoments
                ? 'bg-bronze text-white border-bronze'
                : 'bg-white text-faded-ink hover:bg-vellum'
            }`}
            style={{ borderRadius: '2px' }}
            title="Toggle teaching points visibility"
          >
            📚 Teaching
          </button>
        )}
      </div>
    </div>
  );
}
