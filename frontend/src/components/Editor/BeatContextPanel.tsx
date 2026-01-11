/**
 * BeatContextPanel Component
 * Compact panel showing current plot beat context while writing
 * Position: Top-right of editor, collapsible
 */

import React, { useState, useEffect, useRef } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import { toast } from '@/stores/toastStore';
import type { PlotBeat } from '@/types/outline';

interface BeatContextPanelProps {
  manuscriptId: string;
  chapterId: string;
  onViewBeat?: (beatId: string) => void;
}

const BeatContextPanel = React.memo(function BeatContextPanel({
  manuscriptId,
  chapterId,
  onViewBeat,
}: BeatContextPanelProps) {
  // Use ref to track previous completion state for this component instance
  const prevCompletedRef = useRef<boolean | undefined>(undefined);

  const {
    outline,
    loadOutline,
    loadProgress,
    getBeatByChapterId,
    updateBeat,
    beatContextPanelCollapsed,
    toggleBeatContextPanel,
    notifiedCompletedBeats,
  } = useOutlineStore();

  // Get the beat linked to this chapter
  const beat = getBeatByChapterId?.(chapterId) || null;

  // Load outline on mount if not already loaded
  useEffect(() => {
    if (!outline && manuscriptId) {
      loadOutline(manuscriptId);
    }
  }, [manuscriptId, outline, loadOutline]);

  // Poll for beat progress updates every 10 seconds
  useEffect(() => {
    if (!beat || !outline) return;

    const interval = setInterval(() => {
      loadProgress(outline.id);
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [beat, outline, loadProgress]);

  // Track completion state for notifications
  useEffect(() => {
    if (!beat) {
      prevCompletedRef.current = undefined;
      return;
    }

    // Initialize prevCompleted on first render for this beat
    if (prevCompletedRef.current === undefined) {
      prevCompletedRef.current = beat.is_completed;
      return;
    }

    // Only notify if:
    // 1. Beat just transitioned from incomplete to complete
    // 2. We haven't already notified for this beat (checked in global store)
    const isNewlyCompleted = beat.is_completed && !prevCompletedRef.current;
    const hasNotNotifiedYet = !notifiedCompletedBeats.has(beat.id);

    if (isNewlyCompleted && hasNotNotifiedYet) {
      // Beat just completed - show celebration toast
      toast.success(`🎉 Beat completed: ${beat.beat_label}!`);

      // Add to global store so we don't notify again
      useOutlineStore.setState({
        notifiedCompletedBeats: new Set([...notifiedCompletedBeats, beat.id])
      });
    }

    // Update ref for next comparison
    prevCompletedRef.current = beat.is_completed;
  }, [beat, notifiedCompletedBeats]);

  // Handle marking beat as complete
  const handleToggleComplete = async () => {
    if (!beat) return;

    try {
      await updateBeat(beat.id, {
        is_completed: !beat.is_completed,
      });
    } catch (error) {
      console.error('Failed to update beat completion:', error);
    }
  };

  // Handle viewing beat in outline sidebar
  const handleViewBeat = () => {
    if (beat && onViewBeat) {
      onViewBeat(beat.id);
    }
  };

  // Handle unlinking chapter from beat
  const handleUnlink = async () => {
    if (!beat) return;

    const confirmed = window.confirm(
      `Unlink this chapter from "${beat.beat_label}"?\n\nThis chapter will no longer track progress for this plot beat. You can re-link it later.`
    );

    if (!confirmed) return;

    try {
      await updateBeat(beat.id, { chapter_id: null });
    } catch (error) {
      console.error('Failed to unlink beat:', error);
    }
  };

  // Show "Create Outline" prompt if no outline exists
  if (!outline && !beat) {
    return (
      <div className="fixed top-20 right-4 z-20 w-80">
        <div className="bg-vellum border-2 border-bronze/30 rounded shadow-lg">
          <div className="p-4 space-y-3">
            <div className="text-center">
              <div className="text-4xl mb-3">📋</div>
              <h3 className="font-serif font-bold text-lg text-midnight mb-2">
                No Story Structure Yet
              </h3>
              <p className="text-sm font-sans text-faded-ink mb-4">
                Create an outline to track your progress with plot beats while writing.
              </p>
              <button
                onClick={() => {
                  // User can create outline from the main navigation
                  alert('Switch to the Outline view in the sidebar to create your story structure!');
                }}
                className="w-full px-4 py-2 bg-bronze text-white font-sans font-semibold hover:bg-bronze-dark transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Create Outline
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Don't render if no beat linked (but outline exists)
  if (!beat) {
    return null;
  }

  // Calculate progress percentage
  const progressPercent = beat.target_word_count > 0
    ? Math.min(100, (beat.actual_word_count / beat.target_word_count) * 100)
    : 0;

  // Get status info
  const getStatusInfo = () => {
    if (beat.is_completed) {
      return { label: 'Completed', color: 'green' };
    }
    if (beat.actual_word_count > 0) {
      return { label: 'In Progress', color: 'bronze' };
    }
    return { label: 'Not Started', color: 'gray' };
  };

  const status = getStatusInfo();

  if (beatContextPanelCollapsed) {
    // Collapsed view - just an icon
    return (
      <div
        className="fixed top-20 right-4 z-20 cursor-pointer"
        onClick={toggleBeatContextPanel}
        title={`${beat.beat_label} - ${Math.round(progressPercent)}%`}
      >
        <div className="p-2 bg-bronze text-white rounded shadow-lg hover:bg-bronze-dark transition-colors">
          <span className="text-lg">📋</span>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed top-20 right-4 z-20 w-80">
      <div className="bg-vellum border-2 border-bronze rounded shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-3 bg-bronze/10 border-b border-bronze/30">
          <div className="flex-1">
            <div className="text-xs font-sans font-semibold text-bronze uppercase tracking-wider">
              {beat.beat_name}
            </div>
            <div className="text-sm font-serif font-bold text-midnight">
              {beat.beat_label}
            </div>
          </div>
          <button
            onClick={toggleBeatContextPanel}
            className="ml-2 p-1 hover:bg-bronze/20 rounded transition-colors"
            title="Collapse panel"
          >
            <span className="text-faded-ink">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Position in story */}
          <div className="flex items-center justify-between text-xs font-sans">
            <span className="text-faded-ink">Position in story:</span>
            <span className="font-semibold text-midnight">
              {Math.round(beat.target_position_percent * 100)}%
            </span>
          </div>

          {/* Status badge */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-sans text-faded-ink">Status:</span>
            <span
              className={`
                px-2 py-1 text-xs font-sans font-semibold uppercase tracking-wider rounded
                ${status.color === 'green' ? 'bg-green-500/20 text-green-700' : ''}
                ${status.color === 'bronze' ? 'bg-bronze/20 text-bronze-dark' : ''}
                ${status.color === 'gray' ? 'bg-gray-500/20 text-gray-700' : ''}
              `}
            >
              {status.label}
            </span>
          </div>

          {/* Word count progress */}
          <div>
            <div className="flex items-center justify-between text-xs font-sans mb-1">
              <span className="text-faded-ink">Word count:</span>
              <span className="font-semibold text-midnight">
                {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()}
              </span>
            </div>
            <div className="h-2 bg-slate-ui/30 rounded-full overflow-hidden">
              <div
                className="h-full bg-bronze transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="text-xs font-sans text-faded-ink text-right mt-1">
              {Math.round(progressPercent)}%
            </div>
          </div>

          {/* Beat description (if available) */}
          {beat.beat_description && (
            <div className="pt-2 border-t border-slate-ui/30">
              <div className="text-xs font-sans text-faded-ink mb-1">Description:</div>
              <div className="text-sm font-sans text-midnight leading-relaxed">
                {beat.beat_description.length > 120
                  ? beat.beat_description.substring(0, 120) + '...'
                  : beat.beat_description}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="pt-2 border-t border-slate-ui/30 space-y-2">
            {/* Mark complete checkbox */}
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={beat.is_completed}
                onChange={handleToggleComplete}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="text-sm font-sans text-midnight group-hover:text-bronze transition-colors">
                Mark as complete
              </span>
            </label>

            {/* View beat button */}
            {onViewBeat && (
              <button
                onClick={handleViewBeat}
                className="w-full px-3 py-2 text-sm font-sans font-medium text-bronze border border-bronze rounded hover:bg-bronze hover:text-white transition-colors"
              >
                View Beat Details →
              </button>
            )}

            {/* Unlink button */}
            <button
              onClick={handleUnlink}
              className="w-full px-3 py-2 text-sm font-sans font-medium text-faded-ink border border-slate-ui rounded hover:border-red-500 hover:text-red-600 transition-colors"
            >
              Unlink from Beat
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

export default BeatContextPanel;
