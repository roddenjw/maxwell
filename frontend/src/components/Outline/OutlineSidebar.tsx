/**
 * OutlineSidebar Component
 * Right-side panel showing story structure outline and plot beats
 */

import { useEffect, useState } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import PlotBeatCard from './PlotBeatCard';
import CreateOutlineModal from './CreateOutlineModal';
import SwitchStructureModal from './SwitchStructureModal';
import OutlineCompletionDonut from './OutlineCompletionDonut';
import type { PlotBeat } from '@/types/outline';

interface OutlineSidebarProps {
  manuscriptId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onCreateChapter?: (beat: PlotBeat) => void;
  onOpenChapter?: (chapterId: string) => void;
}

export default function OutlineSidebar({
  manuscriptId,
  isOpen,
  onClose,
  onCreateChapter,
  onOpenChapter,
}: OutlineSidebarProps) {
  const {
    outline,
    progress,
    isLoading,
    loadOutline,
    clearOutline,
    getCompletionPercentage,
  } = useOutlineStore();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showStructureInfo, setShowStructureInfo] = useState(false);
  const [structureDetails, setStructureDetails] = useState<any>(null);
  const [showSwitchModal, setShowSwitchModal] = useState(false);

  // Load outline when manuscript changes
  useEffect(() => {
    if (manuscriptId && isOpen) {
      loadOutline(manuscriptId);
    }

    return () => {
      if (!manuscriptId) {
        clearOutline();
      }
    };
  }, [manuscriptId, isOpen]);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  const handleCreateSuccess = () => {
    if (manuscriptId) {
      loadOutline(manuscriptId);
    }
  };

  const completionPercentage = getCompletionPercentage();
  const structureTypeDisplay = outline?.structure_type
    ? outline.structure_type
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    : '';

  const handleShowStructureInfo = async () => {
    if (!outline?.structure_type) return;

    try {
      const response = await fetch(`http://localhost:8000/api/outlines/structures`);
      const data = await response.json();
      if (data.success) {
        const structure = data.structures.find((s: any) => s.id === outline.structure_type);
        if (structure) {
          setStructureDetails(structure);
          setShowStructureInfo(true);
        }
      }
    } catch (error) {
      console.error('Failed to fetch structure details:', error);
    }
  };

  return (
    <div
      className="fixed right-0 top-0 h-full bg-white border-l-2 border-slate-ui shadow-2xl flex flex-col z-40"
      style={{ width: '384px' }}
    >
      {/* Header */}
      <div className="flex-shrink-0 border-b-2 border-slate-ui bg-vellum p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0 pr-2">
            <h2 className="font-serif font-bold text-xl text-midnight mb-1 truncate">
              Story Outline
            </h2>
            <div className="flex items-center gap-2">
              <p className="font-sans text-sm text-bronze font-medium">
                {structureTypeDisplay}
              </p>
              {outline && (
                <button
                  onClick={handleShowStructureInfo}
                  className="flex-shrink-0 w-5 h-5 flex items-center justify-center hover:bg-bronze/10 text-bronze hover:text-bronze-dark transition-colors rounded-full text-xs"
                  title="View structure details"
                >
                  ℹ️
                </button>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center hover:bg-slate-ui/30 text-faded-ink hover:text-midnight transition-colors"
            style={{ borderRadius: '2px' }}
            title="Close Outline"
          >
            ✕
          </button>
        </div>

        {/* Progress Section */}
        {outline && (
          <div className="space-y-4">
            {/* Donut Chart */}
            <div className="flex justify-center pt-2">
              <OutlineCompletionDonut
                completed={progress?.completed_beats || 0}
                total={progress?.total_beats || 0}
                percentage={completionPercentage}
              />
            </div>

            {/* Progress Bar (Keep for precise reading) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm font-sans">
                <span className="text-faded-ink">
                  {progress?.completed_beats || 0} of {progress?.total_beats || 0} beats completed
                </span>
                <span className="font-bold text-bronze">
                  {completionPercentage}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
                <div
                  className="h-full bg-bronze transition-all duration-500"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-2 border-bronze border-t-transparent rounded-full animate-spin mb-3" />
            <p className="font-sans text-faded-ink text-sm">Loading outline...</p>
          </div>
        </div>
      )}

      {/* No Outline State */}
      {!isLoading && !outline && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center max-w-sm">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="font-serif text-xl font-bold text-midnight mb-2">
              No Story Outline
            </h3>
            <p className="font-sans text-faded-ink text-sm mb-6">
              Add a story structure outline to guide your writing with proven plot beats and checkpoints.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
              style={{ borderRadius: '2px' }}
            >
              Create Outline
            </button>
          </div>
        </div>
      )}

      {/* Plot Beats List */}
      {!isLoading && outline && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {outline.plot_beats.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-3">📋</div>
                <p className="font-sans text-faded-ink text-sm">
                  No plot beats found
                </p>
              </div>
            ) : (
              outline.plot_beats
                .sort((a, b) => a.order_index - b.order_index)
                .map((beat) => (
                  <PlotBeatCard
                    key={beat.id}
                    beat={beat}
                    manuscriptId={manuscriptId!}
                    onCreateChapter={onCreateChapter}
                    onOpenChapter={onOpenChapter}
                  />
                ))
            )}
          </div>

          {/* Footer */}
          <div className="flex-shrink-0 border-t-2 border-slate-ui bg-vellum p-4">
            {/* Switch Structure Button */}
            <button
              onClick={() => setShowSwitchModal(true)}
              className="w-full px-4 py-2 mb-3 border-2 border-bronze text-bronze hover:bg-bronze hover:text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
              title="Switch to a different story structure"
            >
              🔄 Switch Structure
            </button>

            <div className="space-y-2">
              {/* Target Word Count */}
              <div className="flex items-center justify-between text-sm font-sans">
                <span className="text-faded-ink">Target Word Count</span>
                <span className="font-bold text-midnight">
                  {outline.target_word_count.toLocaleString()}
                </span>
              </div>

              {/* Actual Word Count */}
              {progress && (
                <div className="flex items-center justify-between text-sm font-sans">
                  <span className="text-faded-ink">Current Word Count</span>
                  <span className="font-bold text-bronze">
                    {progress.actual_word_count.toLocaleString()}
                  </span>
                </div>
              )}

              {/* Premise (if exists) */}
              {outline.premise && (
                <div className="pt-2 border-t border-slate-ui/30">
                  <p className="text-xs font-sans font-semibold text-midnight mb-1">
                    Story Premise:
                  </p>
                  <p className="text-xs font-sans text-faded-ink leading-relaxed">
                    {outline.premise}
                  </p>
                </div>
              )}

              {/* Logline (if exists) */}
              {outline.logline && (
                <div className="pt-2">
                  <p className="text-xs font-sans font-semibold text-midnight mb-1">
                    Logline:
                  </p>
                  <p className="text-xs font-sans text-faded-ink italic leading-relaxed">
                    {outline.logline}
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Create Outline Modal */}
      {manuscriptId && (
        <CreateOutlineModal
          manuscriptId={manuscriptId}
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      {/* Switch Structure Modal */}
      {outline && (
        <SwitchStructureModal
          outlineId={outline.id}
          currentStructureType={outline.structure_type}
          isOpen={showSwitchModal}
          onClose={() => setShowSwitchModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      {/* Structure Info Modal */}
      {showStructureInfo && structureDetails && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-book"
            style={{ borderRadius: '2px' }}
          >
            {/* Header */}
            <div className="border-b-2 border-slate-ui p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-serif font-bold text-midnight mb-2">
                    {structureDetails.name}
                  </h2>
                  <p className="text-faded-ink font-sans">
                    {structureDetails.description}
                  </p>
                </div>
                <button
                  onClick={() => setShowStructureInfo(false)}
                  className="w-8 h-8 flex items-center justify-center hover:bg-slate-ui/30 text-faded-ink hover:text-midnight transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Overview Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
                  <p className="text-xs font-sans font-semibold text-faded-ink mb-1">
                    Plot Beats
                  </p>
                  <p className="text-2xl font-serif font-bold text-midnight">
                    {structureDetails.beat_count}
                  </p>
                </div>
                <div className="p-4 bg-slate-ui/20 border-2 border-slate-ui" style={{ borderRadius: '2px' }}>
                  <p className="text-xs font-sans font-semibold text-faded-ink mb-1">
                    Target Range
                  </p>
                  <p className="text-lg font-serif font-bold text-midnight">
                    {structureDetails.word_count_range[0].toLocaleString()}-{structureDetails.word_count_range[1].toLocaleString()} words
                  </p>
                </div>
              </div>

              {/* Recommended For */}
              <div>
                <h3 className="font-sans font-semibold text-midnight text-sm mb-3">
                  Recommended For:
                </h3>
                <div className="flex flex-wrap gap-2">
                  {structureDetails.recommended_for.map((rec: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 bg-bronze/10 border border-bronze/30 text-sm font-sans text-midnight"
                      style={{ borderRadius: '2px' }}
                    >
                      {rec}
                    </span>
                  ))}
                </div>
              </div>

              {/* Beat Templates */}
              {structureDetails.beats && structureDetails.beats.length > 0 && (
                <div>
                  <h3 className="font-sans font-semibold text-midnight text-sm mb-3">
                    Plot Beat Structure:
                  </h3>
                  <div className="space-y-3">
                    {structureDetails.beats.map((beat: any, i: number) => (
                      <div
                        key={i}
                        className="p-4 bg-slate-ui/10 border-l-2 border-bronze"
                        style={{ borderRadius: '2px' }}
                      >
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                            {beat.beat_name}
                          </span>
                          <span className="text-xs font-sans text-faded-ink">
                            {Math.round(beat.target_position_percent * 100)}% through story
                          </span>
                        </div>
                        <h4 className="font-serif font-bold text-base text-midnight mb-2">
                          {beat.beat_label}
                        </h4>
                        <p className="text-sm font-sans text-faded-ink leading-relaxed mb-2">
                          {beat.beat_description}
                        </p>
                        {beat.tips && (
                          <div className="mt-2 pt-2 border-t border-slate-ui/30">
                            <p className="text-xs font-sans text-bronze italic leading-relaxed">
                              💡 {beat.tips}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t-2 border-slate-ui p-6">
              <button
                onClick={() => setShowStructureInfo(false)}
                className="w-full px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
