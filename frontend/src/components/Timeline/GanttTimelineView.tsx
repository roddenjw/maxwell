/**
 * GanttTimelineView Component
 * Horizontal bar chart showing plot beats proportional to target word count
 * with timeline events overlaid as dots
 */

import { useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { toast } from '@/stores/toastStore';
import type { GanttBeat } from '@/types/timeline';

interface GanttTimelineViewProps {
  manuscriptId: string;
  timelineId?: string;
}

interface GanttBeatBarProps {
  beat: GanttBeat;
}

function GanttBeatBar({ beat }: GanttBeatBarProps) {
  const progressPercent = beat.target_word_count > 0
    ? Math.min((beat.actual_word_count / beat.target_word_count) * 100, 100)
    : 0;

  const barColor = beat.is_completed
    ? 'bg-green-500'
    : progressPercent > 0
    ? 'bg-bronze'
    : 'bg-bronze/30';

  return (
    <div className="relative mb-6">
      {/* Beat Label (left side) */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="w-48 flex-shrink-0">
            <div className="text-xs font-sans font-semibold text-bronze uppercase tracking-wide">
              {beat.beat_name}
            </div>
            <div className="text-sm font-serif font-bold text-midnight">
              {beat.beat_label}
            </div>
          </div>
          <div className="text-xs font-sans text-faded-ink">
            {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()} words
            {progressPercent > 0 && (
              <span className="ml-2 text-bronze font-semibold">
                ({Math.round(progressPercent)}%)
              </span>
            )}
          </div>
        </div>
        {beat.is_completed && (
          <div className="text-xs font-sans font-semibold text-green-600 uppercase tracking-wide flex items-center gap-1">
            <span>✓</span>
            <span>Complete</span>
          </div>
        )}
      </div>

      {/* Gantt Bar Container */}
      <div className="relative h-16 bg-vellum border border-slate-ui/30" style={{ borderRadius: '2px' }}>
        {/* Beat Bar */}
        <div
          className={`absolute top-0 bottom-0 ${barColor} border-2 border-bronze-dark transition-all duration-300`}
          style={{
            left: `${beat.startPercent}%`,
            width: `${beat.widthPercent}%`,
            borderRadius: '2px',
          }}
        >
          {/* Progress Fill (if in progress) */}
          {!beat.is_completed && progressPercent > 0 && (
            <div
              className="absolute top-0 left-0 bottom-0 bg-bronze-dark opacity-50 transition-all duration-300"
              style={{
                width: `${progressPercent}%`,
                borderRadius: '2px 0 0 2px'
              }}
            />
          )}

          {/* Event Dots */}
          {beat.events.map((event) => {
            const eventColor =
              event.narrative_importance === 'high' ? 'bg-red-500 border-red-600'
              : event.narrative_importance === 'medium' ? 'bg-blue-500 border-blue-600'
              : 'bg-gray-400 border-gray-500';

            return (
              <div
                key={event.id}
                className={`absolute top-1/2 transform -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full ${eventColor} border-2 border-white shadow-sm cursor-pointer hover:scale-150 hover:z-10 transition-transform group`}
                style={{ left: `${event.positionInBeat * 100}%` }}
                title={event.event_name}
              >
                {/* Tooltip on hover */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block whitespace-nowrap z-20">
                  <div className="bg-midnight text-vellum px-2 py-1 text-xs font-sans shadow-book" style={{ borderRadius: '2px' }}>
                    {event.event_name}
                    <div className="text-xs text-faded-ink mt-0.5 capitalize">
                      {event.narrative_importance} importance
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Vertical Grid Lines (every 25%) */}
        {[25, 50, 75].map((percent) => (
          <div
            key={percent}
            className="absolute top-0 bottom-0 w-px bg-slate-ui/20 pointer-events-none"
            style={{ left: `${percent}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="mt-8 pt-6 border-t border-slate-ui/30">
      <div className="text-xs font-sans font-semibold text-faded-ink uppercase tracking-wide mb-3">
        Legend
      </div>
      <div className="grid grid-cols-2 gap-4">
        {/* Beat Status */}
        <div>
          <div className="text-xs font-sans font-semibold text-midnight mb-2">Beat Status</div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-6 h-3 bg-green-500 border-2 border-bronze-dark" style={{ borderRadius: '2px' }} />
              <span className="text-faded-ink">Completed</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-6 h-3 bg-bronze border-2 border-bronze-dark" style={{ borderRadius: '2px' }} />
              <span className="text-faded-ink">In Progress</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-6 h-3 bg-bronze/30 border-2 border-bronze-dark" style={{ borderRadius: '2px' }} />
              <span className="text-faded-ink">Not Started</span>
            </div>
          </div>
        </div>

        {/* Event Importance */}
        <div>
          <div className="text-xs font-sans font-semibold text-midnight mb-2">Event Importance</div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-3 h-3 rounded-full bg-red-500 border-2 border-white" />
              <span className="text-faded-ink">High (Critical moments)</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
              <span className="text-faded-ink">Medium (Important scenes)</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-sans">
              <div className="w-3 h-3 rounded-full bg-gray-400 border-2 border-white" />
              <span className="text-faded-ink">Low (Supporting events)</span>
            </div>
          </div>
        </div>
      </div>
      <div className="mt-3 text-xs font-sans text-faded-ink italic">
        Hover over event dots to see their descriptions. Bar widths are proportional to target word count.
      </div>
    </div>
  );
}

export default function GanttTimelineView({
  manuscriptId,
}: GanttTimelineViewProps) {
  const { ganttViewData, plotBeats, loadOutline, computeGanttData } = useTimelineStore();

  // Load outline if not already loaded
  useEffect(() => {
    if (manuscriptId && plotBeats.length === 0) {
      loadOutline(manuscriptId);
    } else if (plotBeats.length > 0 && !ganttViewData) {
      // If beats loaded but gantt data not computed, compute it
      computeGanttData();
    }
  }, [manuscriptId, plotBeats.length, ganttViewData, loadOutline, computeGanttData]);

  // Empty state: No outline
  if (!ganttViewData || ganttViewData.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-16">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="font-serif text-2xl font-bold text-midnight mb-2">
            No Story Structure Yet
          </h2>
          <p className="font-sans text-sm text-faded-ink mb-6 max-w-md mx-auto">
            Create an outline with plot beats to see the Gantt timeline visualization.
            This view shows your story structure with beats sized by target word count.
          </p>
          <button
            className="px-4 py-2 bg-bronze text-vellum font-sans font-semibold border-2 border-bronze-dark shadow-book hover:bg-bronze-dark transition-colors"
            style={{ borderRadius: '2px' }}
            onClick={() => {
              // Navigate to outline creation (you can implement this)
              toast.info('Navigate to Outline view to create a story structure');
            }}
          >
            Create Outline
          </button>
        </div>
      </div>
    );
  }

  // Calculate total word count for display
  const totalTargetWords = ganttViewData.reduce((sum, beat) => sum + beat.target_word_count, 0);
  const totalActualWords = ganttViewData.reduce((sum, beat) => sum + beat.actual_word_count, 0);
  const overallProgress = totalTargetWords > 0 ? Math.round((totalActualWords / totalTargetWords) * 100) : 0;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-serif text-2xl font-bold text-midnight mb-2">
          Story Structure Timeline
        </h2>
        <p className="font-sans text-sm text-faded-ink mb-4">
          Horizontal bars show plot beats sized by target word count.
          Dots show timeline events within each beat.
        </p>

        {/* Overall Progress */}
        <div className="bg-vellum border border-slate-ui/30 p-4 mb-6" style={{ borderRadius: '2px' }}>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-sans font-semibold text-faded-ink uppercase tracking-wide">
              Overall Progress
            </div>
            <div className="text-sm font-sans font-bold text-bronze">
              {overallProgress}% Complete
            </div>
          </div>
          <div className="h-3 bg-slate-ui/20 overflow-hidden" style={{ borderRadius: '2px' }}>
            <div
              className="h-full bg-bronze transition-all duration-300"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-2 text-xs font-sans text-faded-ink">
            <span>{totalActualWords.toLocaleString()} words written</span>
            <span>{totalTargetWords.toLocaleString()} target words</span>
          </div>
        </div>
      </div>

      {/* Gantt Bars */}
      <div className="space-y-4">
        {ganttViewData.map((beat) => (
          <GanttBeatBar key={beat.id} beat={beat} />
        ))}
      </div>

      {/* Legend */}
      <Legend />
    </div>
  );
}
