/**
 * History Slider - Visual timeline of snapshots
 * Shows snapshots in chronological order with visual timeline
 */

import { type Snapshot } from '../../lib/api';

interface HistorySliderProps {
  snapshots: Snapshot[];
  onSelect: (snapshot: Snapshot) => void;
}

export default function HistorySlider({ snapshots, onSelect }: HistorySliderProps) {
  if (snapshots.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-faded-ink font-sans">
          <svg
            className="w-24 h-24 mx-auto mb-4 text-slate-ui"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-lg">No version history yet</p>
          <p className="text-sm mt-2">Create your first snapshot to start tracking versions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h3 className="text-xl font-garamond font-bold text-midnight mb-6">Version Timeline</h3>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-ui" />

        {/* Snapshot nodes */}
        <div className="space-y-8">
          {snapshots.map((snapshot, index) => (
            <div key={snapshot.id} className="relative pl-16">
              {/* Timeline node */}
              <div className="absolute left-4 top-2 w-4 h-4 rounded-full bg-bronze border-2 border-vellum shadow-sm" />

              {/* Snapshot card */}
              <button
                onClick={() => onSelect(snapshot)}
                className="w-full text-left bg-white rounded-lg border border-slate-ui p-4 hover:border-bronze hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-garamond text-lg text-midnight group-hover:text-bronze transition-colors">
                      {snapshot.label || 'Untitled Snapshot'}
                    </h4>
                    <p className="text-sm font-sans text-faded-ink mt-1">
                      {new Date(snapshot.created_at).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </p>
                    {snapshot.auto_summary && (
                      <p className="text-sm font-sans text-midnight/80 italic mt-2 whitespace-pre-line">
                        {snapshot.auto_summary}
                      </p>
                    )}
                    {snapshot.description && !snapshot.auto_summary && (
                      <p className="text-sm font-sans text-midnight mt-2">
                        {snapshot.description}
                      </p>
                    )}
                  </div>

                  <div className="ml-4 text-right">
                    <span className="inline-block px-2 py-1 text-xs font-sans rounded bg-bronze/10 text-bronze">
                      {snapshot.trigger_type}
                    </span>
                    <p className="text-sm font-sans text-faded-ink mt-2">
                      {snapshot.word_count.toLocaleString()} words
                    </p>
                  </div>
                </div>
              </button>

              {/* Time since previous snapshot */}
              {index < snapshots.length - 1 && (
                <div className="absolute left-4 top-full mt-2 text-xs font-sans text-faded-ink">
                  {getTimeBetween(snapshot.created_at, snapshots[index + 1].created_at)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Calculate human-readable time between two dates
 */
function getTimeBetween(date1: string, date2: string): string {
  const diff = new Date(date1).getTime() - new Date(date2).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days} day${days !== 1 ? 's' : ''} later`;
  } else if (hours > 0) {
    return `${hours} hour${hours !== 1 ? 's' : ''} later`;
  } else {
    const minutes = Math.floor(diff / (1000 * 60));
    return `${minutes} minute${minutes !== 1 ? 's' : ''} later`;
  }
}
