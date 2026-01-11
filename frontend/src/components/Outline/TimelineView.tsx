/**
 * TimelineView Component
 * Horizontal timeline visualization of plot beats
 */

import { useState } from 'react';
import type { PlotBeat } from '@/types/outline';

interface TimelineViewProps {
  beats: PlotBeat[];
  onBeatClick: (beatId: string) => void;
  expandedBeatId: string | null;
}

export default function TimelineView({ beats, onBeatClick, expandedBeatId }: TimelineViewProps) {
  const [hoveredBeatId, setHoveredBeatId] = useState<string | null>(null);

  // Sort beats by order_index
  const sortedBeats = [...beats].sort((a, b) => a.order_index - b.order_index);

  // Calculate beat status
  const getBeatStatus = (beat: PlotBeat): 'completed' | 'in-progress' | 'pending' => {
    if (beat.is_completed) return 'completed';
    if (beat.user_notes || beat.chapter_id) return 'in-progress';
    return 'pending';
  };

  // Get color based on status
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 border-green-600';
      case 'in-progress':
        return 'bg-bronze border-bronze-dark';
      case 'pending':
        return 'bg-slate-ui border-faded-ink';
      default:
        return 'bg-slate-ui border-faded-ink';
    }
  };

  // Calculate position on timeline (percentage)
  const getPosition = (beat: PlotBeat): number => {
    return beat.target_position_percent * 100;
  };

  return (
    <div className="p-6 overflow-x-auto">
      <div className="min-w-[800px] relative">
        {/* Story Progress Markers */}
        <div className="mb-4 flex justify-between text-xs font-sans text-faded-ink px-4">
          <span>Beginning</span>
          <span className="text-center">25%<br />End Act 1</span>
          <span className="text-center">50%<br />Midpoint</span>
          <span className="text-center">75%<br />End Act 2</span>
          <span>End</span>
        </div>

        {/* Timeline Bar */}
        <div className="relative h-32 mb-8">
          {/* Background line */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-ui transform -translate-y-1/2" />

          {/* Act Markers (vertical lines) */}
          {[0, 25, 50, 75, 100].map((percent) => (
            <div
              key={percent}
              className="absolute top-0 bottom-0 w-px bg-slate-ui/50"
              style={{ left: `${percent}%` }}
            />
          ))}

          {/* Plot Beats */}
          {sortedBeats.map((beat) => {
            const status = getBeatStatus(beat);
            const position = getPosition(beat);
            const isHovered = hoveredBeatId === beat.id;
            const isExpanded = expandedBeatId === beat.id;

            return (
              <div
                key={beat.id}
                className="absolute top-1/2 transform -translate-y-1/2 -translate-x-1/2 cursor-pointer group"
                style={{ left: `${position}%` }}
                onClick={() => onBeatClick(beat.id)}
                onMouseEnter={() => setHoveredBeatId(beat.id)}
                onMouseLeave={() => setHoveredBeatId(null)}
              >
                {/* Beat Circle */}
                <div
                  className={`
                    w-8 h-8 rounded-full border-2 transition-all duration-200
                    ${getStatusColor(status)}
                    ${isExpanded ? 'ring-4 ring-bronze/30 scale-125' : ''}
                    ${isHovered ? 'scale-110' : ''}
                    group-hover:shadow-lg
                    flex items-center justify-center
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

                {/* Beat Label (below circle) */}
                <div className="absolute top-12 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                  <div className={`
                    text-xs font-sans font-medium transition-all duration-200
                    ${isExpanded ? 'text-bronze font-bold' : 'text-midnight'}
                    ${isHovered ? 'text-bronze' : ''}
                  `}>
                    {beat.beat_label}
                  </div>
                  <div className="text-xs text-faded-ink text-center mt-1">
                    {Math.round(position)}%
                  </div>
                </div>

                {/* Hover Tooltip - Smart positioning to avoid cutoff */}
                {isHovered && (
                  <div className={`absolute bottom-12 z-10 w-64 pointer-events-none ${
                    position < 20 ? 'left-0' : position > 80 ? 'right-0' : 'left-1/2 -translate-x-1/2'
                  }`}>
                    <div className="bg-midnight text-white p-3 shadow-xl transition-opacity duration-200" style={{ borderRadius: '2px' }}>
                      <div className="font-sans font-bold text-sm mb-1">{beat.beat_label}</div>
                      <div className="text-xs text-white/80 mb-2 max-h-12 overflow-y-auto">
                        {beat.beat_description}
                      </div>
                      <div className="flex items-center justify-between text-xs flex-wrap gap-1">
                        <span className="text-white/60">
                          Target: {beat.target_word_count.toLocaleString()}w
                        </span>
                        <div className="flex gap-2">
                          {beat.user_notes && <span className="text-bronze">📝 Has notes</span>}
                          {beat.chapter_id && <span className="text-bronze">📄 Linked</span>}
                        </div>
                      </div>
                    </div>
                    {/* Arrow pointing down */}
                    <div className={`w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-midnight ${
                      position < 20 ? 'ml-8' : position > 80 ? 'mr-8' : 'mx-auto'
                    }`} />
                  </div>
                )}

                {/* Badges */}
                <div className="absolute -top-2 -right-2 flex gap-0.5">
                  {beat.user_notes && (
                    <div className="w-4 h-4 bg-bronze text-white text-xs flex items-center justify-center" style={{ borderRadius: '2px' }} title="Has notes">
                      📝
                    </div>
                  )}
                  {beat.chapter_id && (
                    <div className="w-4 h-4 bg-blue-500 text-white text-xs flex items-center justify-center" style={{ borderRadius: '2px' }} title="Linked to chapter">
                      📄
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-8 flex items-center justify-center gap-6 text-xs font-sans">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-ui border-2 border-faded-ink" />
            <span className="text-faded-ink">Not Started</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-bronze border-2 border-bronze-dark" />
            <span className="text-faded-ink">In Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-green-600 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <span className="text-faded-ink">Completed</span>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 text-center text-xs font-sans text-faded-ink">
          Click on a beat to view details • Hover to see preview
        </div>
      </div>
    </div>
  );
}
