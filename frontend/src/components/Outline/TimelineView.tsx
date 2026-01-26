/**
 * TimelineView Component
 * Vertical card-based timeline visualization of plot beats
 */

import type { PlotBeat } from '@/types/outline';

interface TimelineViewProps {
  beats: PlotBeat[];
  onBeatClick: (beatId: string) => void;
  expandedBeatId: string | null;
}

export default function TimelineView({ beats, onBeatClick, expandedBeatId }: TimelineViewProps) {
  // Sort beats by order_index
  const sortedBeats = [...beats].sort((a, b) => a.order_index - b.order_index);

  // Calculate beat status
  const getBeatStatus = (beat: PlotBeat): 'completed' | 'in-progress' | 'pending' => {
    if (beat.is_completed) return 'completed';
    if (beat.user_notes || beat.chapter_id || beat.actual_word_count > 0) return 'in-progress';
    return 'pending';
  };

  // Get status styling
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          dot: 'bg-green-500 border-green-600',
          card: 'border-green-500/50 bg-green-50/50',
          text: 'text-green-700',
          label: 'Completed',
        };
      case 'in-progress':
        return {
          dot: 'bg-bronze border-bronze-dark',
          card: 'border-bronze/50 bg-bronze/5',
          text: 'text-bronze',
          label: 'In Progress',
        };
      default:
        return {
          dot: 'bg-slate-ui border-faded-ink',
          card: 'border-slate-ui bg-white',
          text: 'text-faded-ink',
          label: 'Not Started',
        };
    }
  };

  // Get act label based on position
  const getActLabel = (position: number): string => {
    if (position <= 0.25) return 'Act 1';
    if (position <= 0.75) return 'Act 2';
    return 'Act 3';
  };

  // Calculate word count progress
  const getWordProgress = (beat: PlotBeat): number => {
    if (beat.target_word_count === 0) return 0;
    return Math.min(100, (beat.actual_word_count / beat.target_word_count) * 100);
  };

  return (
    <div className="p-6 overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h3 className="font-serif text-xl font-bold text-midnight mb-1">Story Timeline</h3>
        <p className="text-sm font-sans text-faded-ink">
          Click any beat to view and edit details in List view
        </p>
      </div>

      {/* Legend */}
      <div className="mb-6 flex flex-wrap items-center gap-4 text-xs font-sans">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-slate-ui border-2 border-faded-ink" />
          <span className="text-faded-ink">Not Started</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-bronze border-2 border-bronze-dark" />
          <span className="text-faded-ink">In Progress</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-green-600" />
          <span className="text-faded-ink">Completed</span>
        </div>
      </div>

      {/* Vertical Timeline */}
      <div className="relative">
        {/* Vertical connecting line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-ui/50" />

        {/* Beat Cards */}
        <div className="space-y-4">
          {sortedBeats.map((beat, index) => {
            const status = getBeatStatus(beat);
            const style = getStatusStyle(status);
            const position = beat.target_position_percent;
            const wordProgress = getWordProgress(beat);
            const isSelected = expandedBeatId === beat.id;
            const isScene = beat.item_type === 'SCENE';

            // Show act divider
            const prevBeat = index > 0 ? sortedBeats[index - 1] : null;
            const currentAct = getActLabel(position);
            const prevAct = prevBeat ? getActLabel(prevBeat.target_position_percent) : null;
            const showActDivider = currentAct !== prevAct;

            return (
              <div key={beat.id}>
                {/* Act Divider */}
                {showActDivider && (
                  <div className="flex items-center gap-3 mb-4 ml-8">
                    <div className="h-px flex-1 bg-bronze/30" />
                    <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider px-2">
                      {currentAct}
                    </span>
                    <div className="h-px flex-1 bg-bronze/30" />
                  </div>
                )}

                {/* Beat Card Row */}
                <div
                  className={`flex items-start gap-4 cursor-pointer group ${
                    isScene ? 'ml-4' : ''
                  }`}
                  onClick={() => onBeatClick(beat.id)}
                >
                  {/* Timeline Dot */}
                  <div className="relative flex-shrink-0 z-10">
                    <div
                      className={`
                        w-8 h-8 rounded-full border-2 flex items-center justify-center
                        transition-all duration-200
                        ${style.dot}
                        ${isSelected ? 'ring-4 ring-bronze/30 scale-110' : ''}
                        group-hover:scale-110 group-hover:shadow-md
                      `}
                    >
                      {beat.is_completed && (
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </div>

                  {/* Beat Card */}
                  <div
                    className={`
                      flex-1 p-3 border-2 transition-all duration-200
                      ${style.card}
                      ${isSelected ? 'border-bronze shadow-md' : ''}
                      ${isScene ? 'border-purple-300/60' : ''}
                      group-hover:border-bronze/70 group-hover:shadow-sm
                    `}
                    style={{ borderRadius: '2px' }}
                  >
                    {/* Card Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="min-w-0 flex-1">
                        {/* Beat Type Label */}
                        <div className="flex items-center gap-2 mb-1">
                          {isScene ? (
                            <span className="text-xs font-sans font-bold text-purple-600 uppercase tracking-wider">
                              Scene
                            </span>
                          ) : (
                            <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                              {beat.beat_name}
                            </span>
                          )}
                          <span className="text-xs font-sans text-faded-ink">
                            {Math.round(position * 100)}%
                          </span>
                        </div>

                        {/* Beat Title */}
                        <h4 className={`font-serif font-bold text-base truncate ${
                          isScene ? 'text-purple-700' : 'text-midnight'
                        }`}>
                          {beat.beat_label}
                        </h4>
                      </div>

                      {/* Status Badge */}
                      <span
                        className={`flex-shrink-0 px-2 py-0.5 text-xs font-sans font-semibold uppercase tracking-wider ${
                          status === 'completed'
                            ? 'bg-green-500 text-white'
                            : status === 'in-progress'
                            ? 'bg-bronze text-white'
                            : 'bg-slate-ui/50 text-faded-ink'
                        }`}
                        style={{ borderRadius: '2px' }}
                      >
                        {style.label}
                      </span>
                    </div>

                    {/* Description Preview */}
                    {beat.beat_description && (
                      <p className="text-sm font-sans text-faded-ink line-clamp-2 mb-2">
                        {beat.beat_description}
                      </p>
                    )}

                    {/* Progress Bar */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
                        <div
                          className={`h-full transition-all duration-300 ${
                            wordProgress >= 100 ? 'bg-green-500' : 'bg-bronze'
                          }`}
                          style={{ width: `${wordProgress}%` }}
                        />
                      </div>
                      <span className="text-xs font-sans text-faded-ink flex-shrink-0">
                        {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()}
                      </span>
                    </div>

                    {/* Indicators */}
                    {(beat.user_notes || beat.chapter_id) && (
                      <div className="flex items-center gap-3 mt-2 text-xs font-sans text-faded-ink">
                        {beat.user_notes && (
                          <span className="flex items-center gap-1">
                            <span>📝</span>
                            <span>Has notes</span>
                          </span>
                        )}
                        {beat.chapter_id && (
                          <span className="flex items-center gap-1 text-bronze">
                            <span>📄</span>
                            <span>Linked to chapter</span>
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Empty State */}
      {sortedBeats.length === 0 && (
        <div className="text-center py-12 text-faded-ink">
          <p className="font-sans">No beats in this outline yet.</p>
          <p className="text-sm mt-1">Switch to List view to add beats.</p>
        </div>
      )}
    </div>
  );
}
