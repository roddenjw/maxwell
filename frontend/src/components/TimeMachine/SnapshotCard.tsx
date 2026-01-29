/**
 * Snapshot Card - Individual snapshot display in sidebar
 */

import { type Snapshot } from '../../lib/api';

interface SnapshotCardProps {
  snapshot: Snapshot;
  isSelected: boolean;
  onSelect: () => void;
  onShowDiff: () => void;
  onRestore: () => void;
}

export default function SnapshotCard({
  snapshot,
  isSelected,
  onSelect,
  onShowDiff,
  onRestore,
}: SnapshotCardProps) {
  return (
    <div
      className={`
        bg-white rounded border transition-all cursor-pointer
        ${isSelected
          ? 'border-bronze shadow-md'
          : 'border-slate-ui hover:border-bronze/50'
        }
      `}
      onClick={onSelect}
    >
      <div className="p-3">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <h4 className={`font-garamond text-sm font-medium ${isSelected ? 'text-bronze' : 'text-midnight'}`}>
            {snapshot.label || 'Untitled'}
          </h4>
          <span className={`
            text-xs px-1.5 py-0.5 rounded font-sans
            ${getTriggerTypeStyle(snapshot.trigger_type)}
          `}>
            {getTriggerTypeLabel(snapshot.trigger_type)}
          </span>
        </div>

        {/* Auto-generated summary */}
        {snapshot.auto_summary && (
          <p className="text-xs text-midnight/70 font-sans italic mb-2 line-clamp-2">
            {snapshot.auto_summary.split('\n')[0]}
          </p>
        )}

        {/* Metadata */}
        <p className="text-xs text-faded-ink font-sans mb-1">
          {new Date(snapshot.created_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
          })}
        </p>

        <p className="text-xs text-faded-ink font-sans">
          {snapshot.word_count.toLocaleString()} words
        </p>

        {/* Actions */}
        {isSelected && (
          <div className="mt-3 pt-3 border-t border-slate-ui flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onShowDiff();
              }}
              className="flex-1 text-xs font-sans text-bronze hover:text-bronze/80 transition-colors"
            >
              View Changes
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRestore();
              }}
              className="flex-1 text-xs font-sans bg-bronze text-white px-2 py-1 rounded hover:bg-bronze/90 transition-colors"
            >
              Restore
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Get trigger type display label
 */
function getTriggerTypeLabel(triggerType: string): string {
  const labels: Record<string, string> = {
    MANUAL: 'Manual',
    AUTO: 'Auto',
    CHAPTER_COMPLETE: 'Chapter',
    PRE_GENERATION: 'Pre-AI',
    SESSION_END: 'Session',
  };
  return labels[triggerType] || triggerType;
}

/**
 * Get Tailwind classes for trigger type badge
 */
function getTriggerTypeStyle(triggerType: string): string {
  const styles: Record<string, string> = {
    MANUAL: 'bg-bronze/20 text-bronze',
    AUTO: 'bg-slate-ui text-faded-ink',
    CHAPTER_COMPLETE: 'bg-green-100 text-green-700',
    PRE_GENERATION: 'bg-blue-100 text-blue-700',
    SESSION_END: 'bg-purple-100 text-purple-700',
  };
  return styles[triggerType] || 'bg-slate-ui text-faded-ink';
}
