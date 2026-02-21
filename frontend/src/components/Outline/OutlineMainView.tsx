/**
 * OutlineMainView Component
 * Full outline display for the center area when outline tab is active
 * Self-contained view with all features (no sidebar required)
 */

import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useOutlineStore } from '@/stores/outlineStore';
import { useCodexStore } from '@/stores/codexStore';
import { toast } from '@/stores/toastStore';
import { Z_INDEX } from '@/lib/zIndex';
import { brainstormingApi, outlineApi } from '@/lib/api';
import { getErrorMessage } from '@/lib/retry';
import PlotBeatCard from './PlotBeatCard';
import AddSceneButton from './AddSceneButton';
import CreateOutlineModal from './CreateOutlineModal';
import SwitchStructureModal from './SwitchStructureModal';
import OutlineSettingsModal from './OutlineSettingsModal';
import TimelineView from './TimelineView';
import ProgressDashboard from './ProgressDashboard';
import AISuggestionsPanel from './AISuggestionsPanel';
import OutlineGanttView from './OutlineGanttView';
import FillFromManuscriptModal from './FillFromManuscriptModal';
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
    error: outlineError,
  } = useOutlineStore();

  // Modal and view state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSwitchModal, setShowSwitchModal] = useState(false);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'timeline' | 'gantt' | 'analytics'>('list');
  const [showStructureInfo, setShowStructureInfo] = useState(false);
  const [structureDetails, setStructureDetails] = useState<any>(null);
  const [isGeneratingFromCharacters, setIsGeneratingFromCharacters] = useState(false);
  const [isFillingFromManuscript, setIsFillingFromManuscript] = useState(false);
  const [fillResult, setFillResult] = useState<any>(null);
  const [fillCost, setFillCost] = useState<{ formatted: string } | undefined>(undefined);
  const [showFillModal, setShowFillModal] = useState(false);
  const [isAnalyzingGaps, setIsAnalyzingGaps] = useState(false);
  const [gapAnalysis, setGapAnalysis] = useState<{
    beat_analysis: Array<{
      beat_name: string;
      beat_label: string;
      coverage: 'strong' | 'adequate' | 'thin' | 'missing';
      word_count_assessment: string;
      notes: string;
      suggestion: string;
    }>;
    overall_assessment: string;
    priority_gaps: Array<{
      beat_name: string;
      severity: string;
      description: string;
      suggested_scene: string;
    }>;
  } | null>(null);

  // Get characters from codex store
  const { entities, loadEntities } = useCodexStore();
  const characterCount = useMemo(() =>
    entities.filter(e => e.type === 'CHARACTER').length,
    [entities]
  );

  // Load entities on mount
  useEffect(() => {
    if (manuscriptId) {
      loadEntities(manuscriptId);
    }
  }, [manuscriptId, loadEntities]);

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

  // Sorted beats for list view - must be defined before any early returns
  const sortedBeats = useMemo(() => {
    return outline?.plot_beats ? [...outline.plot_beats].sort((a, b) => a.order_index - b.order_index) : [];
  }, [outline?.plot_beats]);

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

  // Handle generating outline from characters
  const handleGenerateFromCharacters = useCallback(async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    if (characterCount === 0) {
      toast.error('No characters found. Create some characters in the Codex first.');
      return;
    }

    try {
      setIsGeneratingFromCharacters(true);
      toast.info(`Generating outline from ${characterCount} characters...`);

      const result = await brainstormingApi.generateOutlineFromCharacters({
        api_key: apiKey,
        manuscript_id: manuscriptId,
        genre: 'Fiction', // TODO: Could make this configurable
        premise: 'A story driven by these characters',
        target_word_count: 80000,
      });

      // Show results in a toast for now
      toast.success(`Generated outline with ${result.beats.length} beats! Theme: ${result.theme}`);

      // Log to console for review
      console.log('Generated outline:', result);

      // TODO: Could show a modal to review and create the outline from these beats
      toast.info('Check console for full outline details. Create outline manually using the suggested beats.');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsGeneratingFromCharacters(false);
    }
  }, [manuscriptId, getApiKey, characterCount]);

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

  const handleAnalyzeGaps = async () => {
    if (!outline) return;
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please add your OpenRouter API key in Settings');
      return;
    }
    setIsAnalyzingGaps(true);
    setGapAnalysis(null);
    try {
      const result = await outlineApi.analyzeGaps(outline.id, {
        manuscript_id: manuscriptId,
        api_key: apiKey,
      });
      if (result.success) {
        setGapAnalysis(result.data);
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsAnalyzingGaps(false);
    }
  };

  const handleFillFromManuscript = async () => {
    if (!outline) return;
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    setIsFillingFromManuscript(true);
    try {
      const result = await outlineApi.fillFromManuscript(outline.id, {
        manuscript_id: manuscriptId,
        api_key: apiKey,
      });

      if (result.success) {
        setFillResult(result.data);
        setFillCost(result.cost);
        setShowFillModal(true);
        toast.success(`Structure mapped! ${result.data.beats_created} beats, ${result.data.scenes_created} scenes created.`);
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsFillingFromManuscript(false);
    }
  };

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

  // Error state - show friendly message with retry option
  if (outlineError && !outline) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum p-8">
        <div className="text-center max-w-lg">
          <div className="text-6xl mb-6">📋</div>
          <h2 className="font-serif text-3xl font-bold text-midnight mb-4">
            Unable to Load Outline
          </h2>
          <p className="font-sans text-faded-ink text-lg mb-6">
            {outlineError}
          </p>
          <div className="flex flex-col gap-3 items-center">
            <button
              onClick={() => loadOutline(manuscriptId)}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
              style={{ borderRadius: '2px' }}
            >
              Try Again
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 border-2 border-bronze text-bronze hover:bg-bronze/10 font-sans font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
            >
              Create New Outline
            </button>
          </div>

          {/* Create Outline Modal */}
          <CreateOutlineModal
            manuscriptId={manuscriptId}
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onSuccess={handleCreateSuccess}
          />
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
          <div className="flex flex-col gap-4 items-center">
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

            {/* Generate from Characters section */}
            {characterCount > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-ui w-full">
                <p className="font-sans text-faded-ink text-sm mb-3">
                  Or generate an outline based on your {characterCount} character{characterCount !== 1 ? 's' : ''}:
                </p>
                <button
                  onClick={handleGenerateFromCharacters}
                  disabled={isGeneratingFromCharacters}
                  className="px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-sans font-medium uppercase tracking-button transition-all shadow-book disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
                  style={{ borderRadius: '2px' }}
                >
                  {isGeneratingFromCharacters ? (
                    <>
                      <span className="animate-spin">⟳</span>
                      Generating...
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      Generate from Characters
                    </>
                  )}
                </button>
              </div>
            )}
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
            onClick={() => setViewMode('gantt')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              viewMode === 'gantt'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📊 Gantt
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
            📈 Analytics
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

        {/* Gantt View */}
        {viewMode === 'gantt' && outline?.plot_beats && (
          <OutlineGanttView
            beats={outline.plot_beats}
            onBeatClick={handleBeatNavigation}
            expandedBeatId={expandedBeatId}
          />
        )}

        {/* Analytics View */}
        {viewMode === 'analytics' && outline && (
          <div>
            <ProgressDashboard outline={outline} />

            {/* Gap Analysis Section */}
            <div className="max-w-4xl mx-auto px-6 pb-6">
              <div className="border-2 border-slate-ui bg-white p-6" style={{ borderRadius: '2px' }}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-serif font-bold text-lg text-midnight">Structure Analysis</h3>
                    <p className="text-sm font-sans text-faded-ink">
                      Compare outline beats against actual manuscript content
                    </p>
                  </div>
                  <button
                    onClick={handleAnalyzeGaps}
                    disabled={isAnalyzingGaps}
                    className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50"
                    style={{ borderRadius: '2px' }}
                  >
                    {isAnalyzingGaps ? 'Analyzing...' : gapAnalysis ? 'Refresh Analysis' : 'Analyze Structure'}
                  </button>
                </div>

                {isAnalyzingGaps && (
                  <div className="flex items-center gap-3 py-8 justify-center">
                    <div className="inline-block w-5 h-5 border-2 border-bronze border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm font-sans text-faded-ink">AI is comparing outline to manuscript...</span>
                  </div>
                )}

                {gapAnalysis && (
                  <div className="space-y-4">
                    {/* Overall Assessment */}
                    <div className="p-3 bg-vellum border border-slate-ui" style={{ borderRadius: '2px' }}>
                      <p className="text-sm font-sans text-midnight">{gapAnalysis.overall_assessment}</p>
                    </div>

                    {/* Beat Coverage */}
                    <div className="space-y-2">
                      {gapAnalysis.beat_analysis.map((beat) => {
                        const coverageColor = {
                          strong: 'bg-green-100 text-green-700 border-green-300',
                          adequate: 'bg-blue-100 text-blue-700 border-blue-300',
                          thin: 'bg-amber-100 text-amber-700 border-amber-300',
                          missing: 'bg-red-100 text-red-700 border-red-300',
                        }[beat.coverage] || 'bg-gray-100 text-gray-700 border-gray-300';

                        return (
                          <div key={beat.beat_name} className="flex items-start gap-3 p-3 border border-slate-ui" style={{ borderRadius: '2px' }}>
                            <span className={`flex-shrink-0 px-2 py-0.5 text-xs font-medium border ${coverageColor}`} style={{ borderRadius: '2px' }}>
                              {beat.coverage}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-sans font-medium text-midnight">{beat.beat_label}</p>
                              <p className="text-xs font-sans text-faded-ink mt-0.5">{beat.notes}</p>
                              {beat.suggestion && (beat.coverage === 'thin' || beat.coverage === 'missing') && (
                                <p className="text-xs font-sans text-bronze mt-1">Suggestion: {beat.suggestion}</p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Priority Gaps */}
                    {gapAnalysis.priority_gaps.length > 0 && (
                      <div>
                        <h4 className="font-sans font-semibold text-sm text-midnight mb-2 uppercase tracking-wider">Priority Gaps</h4>
                        <div className="space-y-2">
                          {gapAnalysis.priority_gaps.map((gap, i) => {
                            const severityColor = {
                              high: 'border-l-red-500',
                              medium: 'border-l-amber-500',
                              low: 'border-l-blue-500',
                            }[gap.severity] || 'border-l-gray-500';

                            return (
                              <div key={i} className={`p-3 border border-slate-ui border-l-4 ${severityColor}`} style={{ borderRadius: '2px' }}>
                                <p className="text-sm font-sans font-medium text-midnight">{gap.description}</p>
                                {gap.suggested_scene && (
                                  <p className="text-xs font-sans text-bronze mt-1">Scene idea: {gap.suggested_scene}</p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
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
            onClick={handleFillFromManuscript}
            disabled={isFillingFromManuscript}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-sans text-sm font-medium uppercase tracking-button transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            style={{ borderRadius: '2px' }}
            title="AI analyzes your manuscript and maps it to outline beats"
          >
            {isFillingFromManuscript ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing...
              </>
            ) : (
              '📖 Fill from Manuscript'
            )}
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

      {/* Fill from Manuscript Modal */}
      {fillResult && (
        <FillFromManuscriptModal
          isOpen={showFillModal}
          onClose={() => setShowFillModal(false)}
          result={fillResult}
          cost={fillCost}
          onReload={() => loadOutline(manuscriptId)}
        />
      )}

      {/* Structure Info Modal */}
      {showStructureInfo && structureDetails && createPortal(
        <div
          className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4"
          style={{ zIndex: Z_INDEX.MODAL_BACKDROP }}
        >
          <div
            className="bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-book"
            style={{ borderRadius: '2px', zIndex: Z_INDEX.MODAL }}
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
        </div>,
        document.body
      )}
    </div>
  );
}
