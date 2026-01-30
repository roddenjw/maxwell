/**
 * OutlineGanttView Component
 * Horizontal bar chart showing plot beats proportional to target word count
 * with chapters/scenes linked to beats shown as markers
 */

import { useMemo } from 'react';
import type { PlotBeat } from '@/types/outline';

interface OutlineGanttViewProps {
  beats: PlotBeat[];
  onBeatClick?: (beatId: string) => void;
  expandedBeatId?: string | null;
}

interface GanttBeatData {
  id: string;
  beat_name: string;
  beat_label: string;
  target_word_count: number;
  actual_word_count: number;
  is_completed: boolean;
  startPercent: number;
  widthPercent: number;
  hasChapter: boolean;
}

interface GanttBeatBarProps {
  beat: GanttBeatData;
  onClick?: () => void;
  isExpanded?: boolean;
}

function GanttBeatBar({ beat, onClick, isExpanded }: GanttBeatBarProps) {
  const progressPercent = beat.target_word_count > 0
    ? Math.min((beat.actual_word_count / beat.target_word_count) * 100, 100)
    : 0;

  const barColor = beat.is_completed
    ? 'bg-green-500'
    : progressPercent > 0
    ? 'bg-bronze'
    : 'bg-bronze/30';

  return (
    <div
      className={`relative mb-6 ${onClick ? 'cursor-pointer' : ''} ${isExpanded ? 'ring-2 ring-bronze ring-offset-2' : ''}`}
      onClick={onClick}
    >
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
        <div className="flex items-center gap-3">
          {beat.hasChapter && (
            <div className="text-xs font-sans text-midnight bg-slate-ui/30 px-2 py-1 rounded">
              Linked to Chapter
            </div>
          )}
          {beat.is_completed && (
            <div className="text-xs font-sans font-semibold text-green-600 uppercase tracking-wide flex items-center gap-1">
              <span>+</span>
              <span>Complete</span>
            </div>
          )}
        </div>
      </div>

      {/* Gantt Bar Container */}
      <div className="relative h-12 bg-vellum border border-slate-ui/30" style={{ borderRadius: '2px' }}>
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
      <div className="flex flex-wrap gap-6">
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
      <div className="mt-3 text-xs font-sans text-faded-ink italic">
        Click on a beat to navigate to it in the list view. Bar widths are proportional to target word count.
      </div>
    </div>
  );
}

export default function OutlineGanttView({
  beats,
  onBeatClick,
  expandedBeatId,
}: OutlineGanttViewProps) {
  // Compute Gantt data from beats
  const ganttData = useMemo(() => {
    if (!beats || beats.length === 0) return [];

    // Filter to only BEAT items (not scenes)
    const plotBeats = beats.filter(b => b.item_type === 'BEAT');

    // Sort beats by target_position_percent
    const sortedBeats = [...plotBeats].sort((a, b) => a.target_position_percent - b.target_position_percent);

    // Calculate total word count for proportional sizing
    const totalWordCount = sortedBeats.reduce((sum, beat) => sum + beat.target_word_count, 0);

    // If no word count, use equal widths
    const useEqualWidths = totalWordCount === 0;
    const equalWidth = 100 / sortedBeats.length;

    // Build Gantt beats with computed positions and widths
    let cumulativePercent = 0;
    return sortedBeats.map((beat) => {
      const widthPercent = useEqualWidths ? equalWidth : (beat.target_word_count / totalWordCount) * 100;
      const startPercent = cumulativePercent;
      cumulativePercent += widthPercent;

      return {
        id: beat.id,
        beat_name: beat.beat_name,
        beat_label: beat.beat_label,
        target_word_count: beat.target_word_count,
        actual_word_count: beat.actual_word_count,
        is_completed: beat.is_completed,
        startPercent,
        widthPercent,
        hasChapter: !!beat.chapter_id,
      };
    });
  }, [beats]);

  // Empty state: No outline
  if (ganttData.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-16">
          <div className="text-6xl mb-4">+</div>
          <h2 className="font-serif text-2xl font-bold text-midnight mb-2">
            No Plot Beats Yet
          </h2>
          <p className="font-sans text-sm text-faded-ink mb-6 max-w-md mx-auto">
            Add plot beats to your outline to see the Gantt visualization.
            This view shows your story structure with beats sized by target word count.
          </p>
        </div>
      </div>
    );
  }

  // Calculate total word count for display
  const totalTargetWords = ganttData.reduce((sum, beat) => sum + beat.target_word_count, 0);
  const totalActualWords = ganttData.reduce((sum, beat) => sum + beat.actual_word_count, 0);
  const overallProgress = totalTargetWords > 0 ? Math.round((totalActualWords / totalTargetWords) * 100) : 0;
  const completedBeats = ganttData.filter(b => b.is_completed).length;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-serif text-2xl font-bold text-midnight mb-2">
          Story Structure Gantt Chart
        </h2>
        <p className="font-sans text-sm text-faded-ink mb-4">
          Horizontal bars show plot beats sized by target word count.
          {completedBeats} of {ganttData.length} beats completed.
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
        {ganttData.map((beat) => (
          <GanttBeatBar
            key={beat.id}
            beat={beat}
            onClick={onBeatClick ? () => onBeatClick(beat.id) : undefined}
            isExpanded={expandedBeatId === beat.id}
          />
        ))}
      </div>

      {/* Legend */}
      <Legend />
    </div>
  );
}
