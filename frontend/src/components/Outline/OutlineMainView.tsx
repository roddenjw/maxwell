/**
 * OutlineMainView Component
 * Full outline display for the center area when outline tab is active
 * Self-contained view with all features (no sidebar required)
 */

import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import { toast } from '@/stores/toastStore';
import PlotBeatCard from './PlotBeatCard';
import AddSceneButton from './AddSceneButton';
import CreateOutlineModal from './CreateOutlineModal';
import SwitchStructureModal from './SwitchStructureModal';
import OutlineSettingsModal from './OutlineSettingsModal';
import TimelineView from './TimelineView';
import ProgressDashboard from './ProgressDashboard';
import AISuggestionsPanel from './AISuggestionsPanel';
import type { PlotBeat } from '@/types/outline';

interface OutlineMainViewProps {
  manuscriptId: string;
  onCreateChapter?: (beat: PlotBeat) => void;
  onOpenChapter?: (chapterId: string) => void;
}

export default function OutlineMainView({
  manuscriptId,
  onCreateChapter,
  onOpenChapter,
}: OutlineMainViewProps) {
  const {
    outline,
    isLoading,
    loadOutline,
    progress,
    getCompletionPercentage,
    expandedBeatId,
    setExpandedBeat,
    getBeatAISuggestions,
    getApiKey,
  } = useOutlineStore();

  // Modal and view state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSwitchModal, setShowSwitchModal] = useState(false);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'timeline' | 'analytics'>('list');
  const [showStructureInfo, setShowStructureInfo] = useState(false);
  const [structureDetails, setStructureDetails] = useState<any>(null);

  // Refs for beat navigation
  const beatRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevExpandedBeatIdRef = useRef<string | null>(null);

  // Load outline when component mounts or manuscriptId changes
  useEffect(() => {
    if (manuscriptId) {
      loadOutline(manuscriptId);
    }
  }, [manuscriptId, loadOutline]);

  // Auto-navigate when expandedBeatId changes (from external sources like breadcrumb button)
  useEffect(() => {
    if (expandedBeatId && expandedBeatId !== prevExpandedBeatIdRef.current) {
      setViewMode('list');
      setTimeout(() => {
        const beatElement = beatRefs.current.get(expandedBeatId);
        if (beatElement && scrollContainerRef.current) {
          beatElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          beatElement.style.animation = 'pulse 0.5s ease-in-out 2';
        }
      }, 150);
    }
    prevExpandedBeatIdRef.current = expandedBeatId;
  }, [expandedBeatId]);

  // Memoized derived state with null safety
  const { completedBeats, totalBeats, structureTypeDisplay } = useMemo(() => {
    if (!outline?.plot_beats) {
      return {
        completedBeats: 0,
        totalBeats: 0,
        structureTypeDisplay: '',
      };
    }

    const completedBeats = outline.plot_beats.filter(b => b.is_completed).length;
    const totalBeats = outline.plot_beats.length;

    const structureTypeDisplay = outline.structure_type
      ? outline.structure_type
          .split('-')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ')
      : '';

    return { completedBeats, totalBeats, structureTypeDisplay };
  }, [outline?.plot_beats, outline?.structure_type]);

  const completionPercentage = getCompletionPercentage();

  // Handle AI suggestions
  const handleGetAIIdeas = useCallback(async (beatId: string) => {
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in the AI panel first');
      setShowAIPanel(true);
      return;
    }
    try {
      await getBeatAISuggestions(beatId);
      toast.success('AI suggestions generated!');
    } catch (error) {
      console.error('Failed to get AI suggestions:', error);
      toast.error('Failed to generate AI suggestions. Check your API key.');
    }
  }, [getApiKey, getBeatAISuggestions]);

  // Handle structure info display
  const handleShowStructureInfo = useCallback(async () => {
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
  }, [outline?.structure_type]);

  // Navigate to a beat (from timeline or other views)
  const handleBeatNavigation = useCallback((beatId: string) => {
    setViewMode('list');
    setExpandedBeat(beatId);
    setTimeout(() => {
      const beatElement = beatRefs.current.get(beatId);
      if (beatElement && scrollContainerRef.current) {
        beatElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        beatElement.style.animation = 'pulse 0.5s ease-in-out 2';
      }
    }, 100);
  }, [setExpandedBeat]);

  const handleCreateSuccess = useCallback(() => {
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
              onClick={() => setShowCreateModal(true)}
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

        {/* Create Outline Modal */}
        <CreateOutlineModal
          manuscriptId={manuscriptId}
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      </div>
    );
  }

  // Sorted beats for list view
  const sortedBeats = useMemo(() => {
    return outline?.plot_beats ? [...outline.plot_beats].sort((a, b) => a.order_index - b.order_index) : [];
  }, [outline?.plot_beats]);

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
              {outline && (
                <button
                  onClick={handleShowStructureInfo}
                  className="w-5 h-5 flex items-center justify-center hover:bg-bronze/10 text-bronze hover:text-bronze-dark transition-colors rounded-full text-xs"
                  title="View structure details"
                >
                  ℹ️
                </button>
              )}
              <span className="font-sans text-faded-ink text-sm">
                {progress?.actual_word_count?.toLocaleString() || 0} / {outline?.target_word_count?.toLocaleString() || 0} words
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="px-4 py-2 bg-slate-ui/20 hover:bg-slate-ui/40 text-faded-ink hover:text-midnight font-sans text-sm font-medium uppercase tracking-button transition-colors flex items-center gap-2"
              style={{ borderRadius: '2px' }}
              title="Edit outline settings"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </button>
          </div>
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

      {/* View Toggle */}
      <div className="flex-shrink-0 border-b border-slate-ui bg-white px-6 py-3">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <button
            onClick={() => setViewMode('list')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              viewMode === 'list'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📋 List
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              viewMode === 'timeline'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            ⏱️ Timeline
          </button>
          <button
            onClick={() => setViewMode('analytics')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              viewMode === 'analytics'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📊 Analytics
          </button>
        </div>
      </div>

      {/* Premise Section (only in list view) */}
      {viewMode === 'list' && (outline?.premise || outline?.logline || outline?.synopsis) && (
        <div className="flex-shrink-0 border-b border-slate-ui bg-white/50 p-6">
          <div className="max-w-4xl mx-auto">
            <h2 className="font-serif text-lg font-bold text-midnight mb-3">Story Summary</h2>
            <div className="space-y-3">
              {outline?.premise && (
                <div>
                  <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Premise</span>
                  <p className="font-sans text-midnight text-sm mt-1">{outline.premise}</p>
                </div>
              )}
              {outline?.logline && (
                <div>
                  <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Logline</span>
                  <p className="font-sans text-midnight text-sm mt-1">{outline.logline}</p>
                </div>
              )}
              {outline?.synopsis && (
                <div>
                  <span className="font-sans text-xs font-semibold text-faded-ink uppercase tracking-wider">Synopsis</span>
                  <p className="font-sans text-midnight text-sm mt-1">{outline.synopsis}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
        {/* List View - Using PlotBeatCard components */}
        {viewMode === 'list' && (
          <div className="p-6">
            <div className="max-w-4xl mx-auto space-y-3">
              {sortedBeats.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-3">📋</div>
                  <p className="font-sans text-faded-ink text-sm">No plot beats found</p>
                </div>
              ) : (
                sortedBeats.map((beat, index) => {
                  const nextBeat = sortedBeats[index + 1];
                  return (
                    <div key={beat.id}>
                      <div
                        ref={(el) => {
                          if (el) {
                            beatRefs.current.set(beat.id, el);
                          } else {
                            beatRefs.current.delete(beat.id);
                          }
                        }}
                      >
                        <PlotBeatCard
                          beat={beat}
                          manuscriptId={manuscriptId}
                          onCreateChapter={onCreateChapter}
                          onOpenChapter={onOpenChapter}
                          onGetAIIdeas={handleGetAIIdeas}
                        />
                      </div>
                      {/* Add Scene button between beats (only after BEAT items, not scenes) */}
                      {beat.item_type === 'BEAT' && (
                        <AddSceneButton
                          afterBeat={beat}
                          nextBeat={nextBeat}
                        />
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Timeline View */}
        {viewMode === 'timeline' && outline?.plot_beats && (
          <TimelineView
            beats={outline.plot_beats}
            onBeatClick={handleBeatNavigation}
            expandedBeatId={expandedBeatId}
          />
        )}

        {/* Analytics View */}
        {viewMode === 'analytics' && outline && (
          <ProgressDashboard outline={outline} />
        )}
      </div>

      {/* Footer with action buttons */}
      <div className="flex-shrink-0 border-t-2 border-slate-ui bg-white p-4">
        <div className="flex justify-center gap-4 max-w-4xl mx-auto">
          <button
            onClick={() => setShowSwitchModal(true)}
            className="px-4 py-2 border-2 border-bronze text-bronze hover:bg-bronze hover:text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
            style={{ borderRadius: '2px' }}
            title="Switch to a different story structure"
          >
            🔄 Switch Structure
          </button>
          <button
            onClick={() => setShowAIPanel(true)}
            className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors shadow-md"
            style={{ borderRadius: '2px' }}
            title="Get AI-powered insights and suggestions"
          >
            🤖 AI Insights
          </button>
        </div>
      </div>

      {/* Modals */}
      <CreateOutlineModal
        manuscriptId={manuscriptId}
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />

      {outline && (
        <>
          <SwitchStructureModal
            outlineId={outline.id}
            currentStructureType={outline.structure_type}
            isOpen={showSwitchModal}
            onClose={() => setShowSwitchModal(false)}
            onSuccess={handleCreateSuccess}
          />

          <OutlineSettingsModal
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            outlineId={outline.id}
          />

          <AISuggestionsPanel
            outline={outline}
            isOpen={showAIPanel}
            onClose={() => setShowAIPanel(false)}
          />
        </>
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
                  <p className="text-xs font-sans font-semibold text-faded-ink mb-1">Plot Beats</p>
                  <p className="text-2xl font-serif font-bold text-midnight">{structureDetails.beat_count}</p>
                </div>
                <div className="p-4 bg-slate-ui/20 border-2 border-slate-ui" style={{ borderRadius: '2px' }}>
                  <p className="text-xs font-sans font-semibold text-faded-ink mb-1">Target Range</p>
                  <p className="text-lg font-serif font-bold text-midnight">
                    {structureDetails.word_count_range?.[0]?.toLocaleString()}-{structureDetails.word_count_range?.[1]?.toLocaleString()} words
                  </p>
                </div>
              </div>

              {/* Recommended For */}
              {structureDetails.recommended_for && (
                <div>
                  <h3 className="font-sans font-semibold text-midnight text-sm mb-3">Recommended For:</h3>
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
              )}

              {/* Beat Templates */}
              {structureDetails.beats && structureDetails.beats.length > 0 && (
                <div>
                  <h3 className="font-sans font-semibold text-midnight text-sm mb-3">Plot Beat Structure:</h3>
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
                        <h4 className="font-serif font-bold text-base text-midnight mb-2">{beat.beat_label}</h4>
                        <p className="text-sm font-sans text-faded-ink leading-relaxed mb-2">{beat.beat_description}</p>
                        {beat.tips && (
                          <div className="mt-2 pt-2 border-t border-slate-ui/30">
                            <p className="text-xs font-sans text-bronze italic leading-relaxed">💡 {beat.tips}</p>
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
