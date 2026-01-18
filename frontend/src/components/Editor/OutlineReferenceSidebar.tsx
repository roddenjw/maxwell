/**
 * OutlineReferenceSidebar Component
 * Shows full outline structure as reference while writing
 * Collapsible sidebar on the right side of the editor
 */

import React, { useState, useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';

interface OutlineReferenceSidebarProps {
  manuscriptId: string;
  currentChapterId?: string;
  onViewBeat?: (beatId: string) => void;
}

const OutlineReferenceSidebar = React.memo(function OutlineReferenceSidebar({
  manuscriptId,
  currentChapterId,
  onViewBeat,
}: OutlineReferenceSidebarProps) {
  const [expandedBeatIds, setExpandedBeatIds] = useState<Set<string>>(new Set());

  const {
    outline,
    loadOutline,
    getCompletedBeatsCount,
    getTotalBeatsCount,
    getBeatByChapterId,
    outlineReferenceSidebarOpen,
    toggleOutlineReferenceSidebar,
  } = useOutlineStore();

  // Get current beat if chapter is linked
  const currentBeat = currentChapterId ? getBeatByChapterId?.(currentChapterId) : null;

  // Load outline on mount
  useEffect(() => {
    if (!outline && manuscriptId) {
      loadOutline(manuscriptId);
    }
  }, [manuscriptId, outline, loadOutline]);

  // Handle beat expand/collapse
  const handleToggleBeat = (beatId: string) => {
    const newSet = new Set(expandedBeatIds);
    if (newSet.has(beatId)) {
      newSet.delete(beatId);
    } else {
      newSet.add(beatId);
    }
    setExpandedBeatIds(newSet);
  };

  // Calculate overall progress
  const totalBeats = getTotalBeatsCount();
  const completedBeats = getCompletedBeatsCount();
  const progressPercent = totalBeats > 0 ? Math.round((completedBeats / totalBeats) * 100) : 0;

  // Don't render if no outline
  if (!outline) {
    return null;
  }

  // Collapsed view - just an icon bar
  if (!outlineReferenceSidebarOpen) {
    return (
      <div className="fixed top-0 right-0 h-full w-10 bg-bronze/10 border-l-2 border-bronze/30 flex flex-col items-center py-4 z-10">
        <button
          onClick={toggleOutlineReferenceSidebar}
          className="p-2 hover:bg-bronze/20 rounded transition-colors"
          title="Show outline"
        >
          <span className="text-bronze text-xl">📋</span>
        </button>
        {progressPercent > 0 && (
          <div className="mt-4 text-xs font-sans text-bronze font-bold writing-mode-vertical">
            {progressPercent}%
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="fixed top-0 right-0 h-full w-80 bg-vellum border-l-2 border-bronze/30 flex flex-col z-10 shadow-2xl">
      {/* Sticky Header */}
      <div className="flex-shrink-0 bg-bronze/10 border-b-2 border-bronze/30 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex-1">
            <h3 className="font-serif font-bold text-lg text-midnight">
              {outline.structure_type.replace(/[_-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            <p className="text-xs font-sans text-faded-ink">
              {totalBeats} beats
            </p>
          </div>
          <button
            onClick={toggleOutlineReferenceSidebar}
            className="p-2 hover:bg-bronze/20 rounded transition-colors"
            title="Collapse outline"
          >
            <span className="text-faded-ink">✕</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs font-sans">
            <span className="text-faded-ink">Progress:</span>
            <span className="font-semibold text-midnight">
              {completedBeats} / {totalBeats} ({progressPercent}%)
            </span>
          </div>
          <div className="h-2 bg-slate-ui/30 rounded-full overflow-hidden">
            <div
              className="h-full bg-bronze transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Scrollable Beat List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {outline.plot_beats.map((beat) => {
          const isExpanded = expandedBeatIds.has(beat.id);
          const isCurrent = currentBeat?.id === beat.id;
          const beatProgress = beat.target_word_count > 0
            ? Math.min(100, (beat.actual_word_count / beat.target_word_count) * 100)
            : 0;

          // Status icon
          const getStatusIcon = () => {
            if (beat.is_completed) return '✓';
            if (beat.actual_word_count > 0) return '●';
            return '○';
          };

          const getStatusColor = () => {
            if (beat.is_completed) return 'text-green-600';
            if (beat.actual_word_count > 0) return 'text-bronze';
            return 'text-slate-ui';
          };

          return (
            <div
              key={beat.id}
              className={`
                border-2 transition-all
                ${isCurrent ? 'border-bronze bg-bronze/5' : 'border-slate-ui bg-white'}
                ${!isExpanded && 'hover:border-bronze/50 cursor-pointer'}
              `}
              style={{ borderRadius: '2px' }}
              onClick={() => !isExpanded && handleToggleBeat(beat.id)}
            >
              {/* Beat Header */}
              <div className="p-3">
                <div className="flex items-start gap-2">
                  {/* Status Icon */}
                  <span className={`flex-shrink-0 mt-1 font-bold ${getStatusColor()}`}>
                    {getStatusIcon()}
                  </span>

                  {/* Beat Info */}
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-sans font-bold text-bronze uppercase tracking-wider mb-1">
                      {beat.beat_name}
                    </div>
                    <div className={`font-serif font-bold text-sm ${isCurrent ? 'text-bronze' : 'text-midnight'}`}>
                      {beat.beat_label}
                    </div>

                    {/* Word Count Progress Mini Bar */}
                    {beat.target_word_count > 0 && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs font-sans mb-1">
                          <span className="text-faded-ink">
                            {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()}
                          </span>
                          <span className="font-semibold text-midnight">
                            {Math.round(beatProgress)}%
                          </span>
                        </div>
                        <div className="h-1 bg-slate-ui/30 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-bronze transition-all duration-300"
                            style={{ width: `${beatProgress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Expand/Collapse Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleBeat(beat.id);
                    }}
                    className="flex-shrink-0 p-1 hover:bg-bronze/10 rounded transition-colors"
                  >
                    <span className="text-faded-ink text-xs">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </button>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-ui/30 space-y-3">
                    {/* Beat Description */}
                    {beat.beat_description && (
                      <div>
                        <div className="text-xs font-sans text-faded-ink mb-1">Description:</div>
                        <div className="text-sm font-sans text-midnight leading-relaxed">
                          {beat.beat_description}
                        </div>
                      </div>
                    )}

                    {/* Content Summary */}
                    {beat.content_summary && (
                      <div>
                        <div className="text-xs font-sans text-faded-ink mb-1">Written:</div>
                        <div className="text-sm font-sans text-midnight leading-relaxed">
                          {beat.content_summary}
                        </div>
                      </div>
                    )}

                    {/* User Notes */}
                    {beat.user_notes && (
                      <div>
                        <div className="text-xs font-sans text-faded-ink mb-1">Notes:</div>
                        <div className="text-sm font-sans text-midnight leading-relaxed italic">
                          {beat.user_notes}
                        </div>
                      </div>
                    )}

                    {/* Position in Story */}
                    <div className="flex items-center justify-between text-xs font-sans">
                      <span className="text-faded-ink">Position:</span>
                      <span className="font-semibold text-midnight">
                        {Math.round(beat.target_position_percent * 100)}% through story
                      </span>
                    </div>

                    {/* View Beat Button */}
                    {onViewBeat && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewBeat(beat.id);
                        }}
                        className="w-full px-3 py-2 text-sm font-sans font-medium text-bronze border border-bronze hover:bg-bronze hover:text-white transition-colors"
                        style={{ borderRadius: '2px' }}
                      >
                        View Beat Details →
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer - Quick Stats */}
      <div className="flex-shrink-0 bg-bronze/10 border-t-2 border-bronze/30 p-3">
        <div className="flex items-center justify-between text-xs font-sans">
          <span className="text-faded-ink">Total Target:</span>
          <span className="font-semibold text-midnight">
            {outline.target_word_count.toLocaleString()} words
          </span>
        </div>
        <div className="flex items-center justify-between text-xs font-sans mt-1">
          <span className="text-faded-ink">Current:</span>
          <span className="font-semibold text-midnight">
            {outline.plot_beats.reduce((sum, b) => sum + b.actual_word_count, 0).toLocaleString()} words
          </span>
        </div>
      </div>
    </div>
  );
});

export default OutlineReferenceSidebar;
