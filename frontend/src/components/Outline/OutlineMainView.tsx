/**
 * OutlineMainView Component
 * Full outline display for the center area when outline tab is active
 */

import { useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';

interface OutlineMainViewProps {
  manuscriptId: string;
  onOpenSidebar: () => void;
  onCreateOutline: () => void;
}

export default function OutlineMainView({
  manuscriptId,
  onOpenSidebar,
  onCreateOutline,
}: OutlineMainViewProps) {
  const { outline, isLoading, loadOutline, progress, getCompletionPercentage } = useOutlineStore();

  // Load outline when component mounts or manuscriptId changes
  useEffect(() => {
    if (manuscriptId) {
      loadOutline(manuscriptId);
    }
  }, [manuscriptId, loadOutline]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-2 border-bronze border-t-transparent rounded-full animate-spin mb-3" />
          <p className="font-sans text-faded-ink text-sm">Loading outline...</p>
        </div>
      </div>
    );
  }

  // No outline state
  if (!outline) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum p-8">
        <div className="text-center max-w-lg">
          <div className="text-6xl mb-6">📋</div>
          <h2 className="font-serif text-3xl font-bold text-midnight mb-4">
            Story Structure Outline
          </h2>
          <p className="font-sans text-faded-ink text-lg mb-6">
            Create a story structure outline to guide your writing with proven plot beats and checkpoints.
          </p>
          <div className="flex flex-col gap-3 items-center">
            <button
              onClick={onCreateOutline}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
              style={{ borderRadius: '2px' }}
            >
              Create Outline
            </button>
            <p className="font-sans text-faded-ink text-sm">
              Choose from structures like Three Act, Hero's Journey, Save the Cat, and more.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Outline exists - show full info
  const structureTypeDisplay = outline.structure_type
    ? outline.structure_type
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    : '';

  const completionPercentage = getCompletionPercentage();
  const completedBeats = outline.plot_beats.filter(b => b.is_completed).length;
  const totalBeats = outline.plot_beats.length;

  // Group beats by act (estimate based on position)
  const getActForBeat = (positionPercent: number): number => {
    if (positionPercent <= 0.25) return 1;
    if (positionPercent <= 0.75) return 2;
    return 3;
  };

  const beatsByAct: { [key: number]: typeof outline.plot_beats } = { 1: [], 2: [], 3: [] };
  outline.plot_beats.forEach(beat => {
    const act = getActForBeat(beat.target_position_percent);
    if (!beatsByAct[act]) beatsByAct[act] = [];
    beatsByAct[act].push(beat);
  });

  return (
    <div className="flex-1 flex flex-col bg-vellum overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b-2 border-slate-ui bg-white p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="font-serif text-3xl font-bold text-midnight mb-2">
              Story Structure Outline
            </h1>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-bronze/10 text-bronze font-sans text-sm font-medium" style={{ borderRadius: '2px' }}>
                {structureTypeDisplay}
              </span>
              <span className="font-sans text-faded-ink text-sm">
                {progress?.actual_word_count?.toLocaleString() || 0} / {outline.target_word_count.toLocaleString()} words
              </span>
            </div>
          </div>
          <button
            onClick={onOpenSidebar}
            className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Open Sidebar
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="w-full h-3 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
            <div
              className="h-full bg-bronze transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          <div className="flex justify-between font-sans text-sm text-faded-ink">
            <span>{completedBeats} of {totalBeats} beats completed ({completionPercentage}%)</span>
          </div>
        </div>
      </div>

      {/* Premise Section */}
      {(outline.premise || outline.logline || outline.synopsis) && (
        <div className="flex-shrink-0 border-b border-slate-ui bg-white/50 p-6">
          <h2 className="font-serif text-lg font-bold text-midnight mb-3">Story Summary</h2>
          <div className="space-y-3">
            {outline.premise && (
              <div>
                <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Premise</span>
                <p className="font-sans text-midnight text-sm mt-1">{outline.premise}</p>
              </div>
            )}
            {outline.logline && (
              <div>
                <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Logline</span>
                <p className="font-sans text-midnight text-sm mt-1">{outline.logline}</p>
              </div>
            )}
            {outline.synopsis && (
              <div>
                <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Synopsis</span>
                <p className="font-sans text-midnight text-sm mt-1">{outline.synopsis}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Beats Overview */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8">
          {[1, 2, 3].map(act => {
            const beatsInAct = beatsByAct[act] || [];
            if (beatsInAct.length === 0) return null;

            const actLabels = ['', 'Act I: Setup', 'Act II: Confrontation', 'Act III: Resolution'];
            const completedInAct = beatsInAct.filter(b => b.is_completed).length;

            return (
              <div key={act} className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-serif text-xl font-bold text-midnight">
                    {actLabels[act]}
                  </h3>
                  <span className="font-sans text-sm text-faded-ink">
                    {completedInAct} / {beatsInAct.length} completed
                  </span>
                </div>

                <div className="grid gap-3">
                  {beatsInAct.map(beat => (
                    <div
                      key={beat.id}
                      className={`p-4 bg-white border-l-4 shadow-sm ${
                        beat.is_completed ? 'border-green-500' : 'border-bronze'
                      }`}
                      style={{ borderRadius: '2px' }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-lg ${beat.is_completed ? 'text-green-500' : 'text-bronze'}`}>
                            {beat.is_completed ? '✓' : '○'}
                          </span>
                          <h4 className="font-serif font-bold text-midnight">
                            {beat.beat_label || beat.beat_name}
                          </h4>
                        </div>
                        <span className="font-sans text-xs text-faded-ink">
                          {Math.round(beat.target_position_percent * 100)}%
                        </span>
                      </div>

                      {beat.beat_description && (
                        <p className="font-sans text-sm text-faded-ink mb-2 pl-7">
                          {beat.beat_description}
                        </p>
                      )}

                      {beat.content_summary && (
                        <div className="pl-7 mt-2 p-2 bg-bronze/5 border-l-2 border-bronze/30" style={{ borderRadius: '2px' }}>
                          <span className="font-sans text-xs font-semibold text-bronze uppercase tracking-wider">Your Content</span>
                          <p className="font-sans text-sm text-midnight mt-1">{beat.content_summary}</p>
                        </div>
                      )}

                      {beat.user_notes && (
                        <div className="pl-7 mt-2 p-2 bg-slate-ui/10" style={{ borderRadius: '2px' }}>
                          <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Notes</span>
                          <p className="font-sans text-sm text-midnight mt-1">{beat.user_notes}</p>
                        </div>
                      )}

                      {beat.chapter_id && (
                        <div className="pl-7 mt-2 font-sans text-xs text-faded-ink">
                          <span className="text-bronze">📎 Linked to chapter</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer with quick actions */}
      <div className="flex-shrink-0 border-t border-slate-ui bg-white p-4">
        <div className="flex justify-center gap-4">
          <button
            onClick={onOpenSidebar}
            className="px-4 py-2 border-2 border-bronze text-bronze hover:bg-bronze hover:text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
            style={{ borderRadius: '2px' }}
          >
            View Sidebar
          </button>
        </div>
      </div>
    </div>
  );
}
