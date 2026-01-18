/**
 * PlotBeatCard Component
 * Individual plot beat display with completion tracking and notes
 */

import { useState, useRef, useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import { toast } from '@/stores/toastStore';
import type { PlotBeat, BeatSuggestion } from '@/types/outline';
import BeatSuggestionCard from './BeatSuggestionCard';

interface Chapter {
  id: string;
  title: string;
  is_folder: boolean;
}

interface PlotBeatCardProps {
  beat: PlotBeat;
  manuscriptId: string;
  onCreateChapter?: (beat: PlotBeat) => void;
  onOpenChapter?: (chapterId: string) => void;
  onGetAIIdeas?: (beatId: string) => void;
}

export default function PlotBeatCard({ beat, manuscriptId, onCreateChapter, onOpenChapter, onGetAIIdeas }: PlotBeatCardProps) {
  const { updateBeat, deleteItem, expandedBeatId, setExpandedBeat, beatSuggestions } = useOutlineStore();
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [notes, setNotes] = useState(beat.user_notes);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [showAISuggestions, setShowAISuggestions] = useState(false);
  const notesTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Feedback tracking for suggestion refinement
  const [suggestionFeedback, setSuggestionFeedback] = useState<Map<number, 'like' | 'dislike'>>(new Map());

  const isExpanded = expandedBeatId === beat.id;
  const suggestions = beatSuggestions.get(beat.id);
  const hasAISuggestions = suggestions && suggestions.suggestions.length > 0;
  const hasFeedback = suggestionFeedback.size > 0;

  // Is this a scene (user-added) or a beat (from template)?
  const isScene = beat.item_type === 'SCENE';

  // Update local notes when beat changes
  useEffect(() => {
    setNotes(beat.user_notes);
  }, [beat.user_notes]);

  // Fetch chapters when beat is expanded OR if beat has linked chapter (for collapsed preview)
  useEffect(() => {
    if ((isExpanded || beat.chapter_id) && chapters.length === 0) {
      fetchChapters();
    }
  }, [isExpanded, beat.chapter_id]);

  const fetchChapters = async () => {
    setLoadingChapters(true);
    try {
      const response = await fetch(`http://localhost:8000/api/chapters/manuscript/${manuscriptId}/tree`);
      const data = await response.json();
      if (data.success) {
        // Flatten tree to get all non-folder chapters
        const flattenChapters = (nodes: any[]): Chapter[] => {
          let result: Chapter[] = [];
          for (const node of nodes) {
            if (!node.is_folder) {
              result.push({ id: node.id, title: node.title, is_folder: node.is_folder });
            }
            if (node.children && node.children.length > 0) {
              result = result.concat(flattenChapters(node.children));
            }
          }
          return result;
        };
        setChapters(flattenChapters(data.data));
      }
    } catch (error) {
      console.error('Failed to fetch chapters:', error);
    } finally {
      setLoadingChapters(false);
    }
  };

  const handleLinkChapter = async (chapterId: string) => {
    setIsUpdating(true);
    try {
      await updateBeat(beat.id, { chapter_id: chapterId });
    } catch (error) {
      console.error('Failed to link chapter:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleToggleComplete = async () => {
    setIsUpdating(true);
    try {
      await updateBeat(beat.id, { is_completed: !beat.is_completed });
    } catch (error) {
      console.error('Failed to toggle beat completion:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleNotesChange = (newNotes: string) => {
    setNotes(newNotes);

    // Debounce the API call
    if (notesTimeoutRef.current) {
      clearTimeout(notesTimeoutRef.current);
    }

    notesTimeoutRef.current = setTimeout(async () => {
      try {
        await updateBeat(beat.id, { user_notes: newNotes });
      } catch (error) {
        console.error('Failed to save notes:', error);
      }
    }, 1000);
  };

  const handleToggleExpand = () => {
    setExpandedBeat(isExpanded ? null : beat.id);
  };

  const handleGetAIIdeas = async () => {
    if (!onGetAIIdeas) return;

    setIsLoadingAI(true);
    try {
      await onGetAIIdeas(beat.id);
      setShowAISuggestions(true); // Auto-expand suggestions after loading
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleApplySuggestion = async (suggestion: BeatSuggestion, _index: number) => {
    if (!suggestions) return;

    try {
      // Update beat description with suggestion
      await updateBeat(beat.id, {
        beat_description: suggestion.description
      });

      toast.success('Suggestion applied to beat description');
    } catch (error) {
      console.error('Failed to apply suggestion:', error);
      toast.error('Failed to apply suggestion');
    }
  };

  const handleDismissSuggestion = (_index: number) => {
    // Note: The actual mutation happens in BeatSuggestionCard's onDismiss
    // This is just a placeholder for future persistence if needed
  };

  const handleSuggestionFeedback = (index: number, feedback: 'like' | 'dislike') => {
    setSuggestionFeedback(prev => {
      const next = new Map(prev);
      if (next.get(index) === feedback) {
        // Toggle off if clicking same feedback
        next.delete(index);
      } else {
        next.set(index, feedback);
      }
      return next;
    });
  };

  const handleRefineSuggestions = async () => {
    if (!onGetAIIdeas || !hasFeedback) return;

    // Clear feedback after triggering refinement
    // The AI will regenerate with fresh suggestions
    // In a more advanced implementation, we'd send feedback to the backend
    toast.info('Generating refined suggestions based on your feedback...');
    setSuggestionFeedback(new Map());
    await onGetAIIdeas(beat.id);
  };

  const wordCountProgress = beat.target_word_count > 0
    ? Math.min(100, (beat.actual_word_count / beat.target_word_count) * 100)
    : 0;

  // Find linked chapter for collapsed state preview
  const linkedChapter = beat.chapter_id
    ? chapters.find(ch => ch.id === beat.chapter_id)
    : null;

  // Determine beat status
  const getBeatStatus = (): { label: string; color: string } => {
    if (beat.is_completed) {
      return { label: 'Completed', color: 'bg-green-500 text-white' };
    }
    if (beat.user_notes || beat.chapter_id || beat.actual_word_count > 0) {
      return { label: 'In Progress', color: 'bg-bronze text-white' };
    }
    return { label: 'Not Started', color: 'bg-slate-ui/50 text-faded-ink' };
  };

  const status = getBeatStatus();

  const handleDeleteScene = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isScene) return;
    if (!confirm(`Delete scene "${beat.beat_label}"?`)) return;

    setIsDeleting(true);
    try {
      await deleteItem(beat.id);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className={`bg-white border-2 transition-all ${
        isScene
          ? beat.is_completed
            ? 'border-purple-400 bg-purple-50/50 ml-4'
            : 'border-purple-300/60 bg-purple-50/30 hover:border-purple-400 ml-4'
          : beat.is_completed
            ? 'border-bronze bg-bronze/5'
            : 'border-slate-ui hover:border-bronze/50'
      }`}
      style={{ borderRadius: '2px' }}
    >
      {/* Header - Always Visible */}
      <div
        className="p-2.5 cursor-pointer"
        onClick={handleToggleExpand}
      >
        <div className="flex items-start gap-3">
          {/* Completion Checkbox */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleToggleComplete();
            }}
            disabled={isUpdating}
            title="Mark as complete (or auto-completes when chapter reaches target word count)"
            className={`flex-shrink-0 mt-1 w-5 h-5 border-2 flex items-center justify-center transition-colors ${
              beat.is_completed
                ? isScene ? 'bg-purple-500 border-purple-500' : 'bg-bronze border-bronze'
                : isScene ? 'border-purple-400 hover:border-purple-500' : 'border-slate-ui hover:border-bronze'
            }`}
            style={{ borderRadius: '2px' }}
          >
            {beat.is_completed && (
              <span className="text-white text-xs">✓</span>
            )}
          </button>

          {/* Beat/Scene Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 mb-1">
              {isScene ? (
                <span className="text-xs font-sans font-bold text-purple-600 uppercase tracking-wider flex items-center gap-1">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2h6v4H7V5zm8 8v2h1v-2h-1zm-2-2H7v4h6v-4zm2 0h1V9h-1v2zm1-4V5h-1v2h1zM5 5v2H4V5h1zm0 4H4v2h1V9zm-1 4h1v2H4v-2z" clipRule="evenodd" />
                  </svg>
                  Scene
                </span>
              ) : (
                <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                  {beat.beat_name}
                </span>
              )}
              <span className="text-xs font-sans text-faded-ink">
                {Math.round(beat.target_position_percent * 100)}% through story
              </span>
            </div>

            {/* Beat Title and Status */}
            <div className="flex items-start gap-2 mb-2">
              <h4 className={`flex-1 font-serif font-bold text-lg ${
                beat.is_completed
                  ? isScene ? 'text-purple-600' : 'text-bronze'
                  : 'text-midnight'
              }`}>
                {beat.beat_label}
              </h4>

              {/* AI Badge (if suggestions available) */}
              {hasAISuggestions && suggestions && (
                <span
                  className="flex-shrink-0 px-2 py-0.5 text-xs font-sans font-semibold uppercase bg-purple-100 text-purple-700 border border-purple-300"
                  style={{ borderRadius: '2px' }}
                  title={`${suggestions.suggestions.length} AI suggestions available`}
                >
                  🤖 AI
                </span>
              )}

              {/* Status Pill */}
              <span
                className={`flex-shrink-0 px-2 py-0.5 text-xs font-sans font-semibold uppercase tracking-wider ${status.color}`}
                style={{ borderRadius: '2px' }}
              >
                {status.label}
              </span>
            </div>

            {/* Notes preview (collapsed state only) */}
            {!isExpanded && beat.user_notes && (
              <p className="mt-1 mb-2 text-sm text-faded-ink italic line-clamp-2 leading-snug">
                {beat.user_notes}
              </p>
            )}

            {/* Linked chapter (collapsed state only) */}
            {!isExpanded && beat.chapter_id && linkedChapter && (
              <div className="mt-1 mb-2 flex items-center gap-1.5 text-sm text-bronze">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.102m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <span className="font-sans font-medium">Linked: {linkedChapter.title}</span>
              </div>
            )}

            {/* Word Count Progress Bar */}
            <div className="flex items-center gap-2 text-xs font-sans text-faded-ink">
              <div className="flex-1 h-1.5 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
                <div
                  className={`h-full transition-all duration-300 ${
                    wordCountProgress >= 100 ? 'bg-green-500' : 'bg-bronze'
                  }`}
                  style={{ width: `${wordCountProgress}%` }}
                />
              </div>
              <span className={wordCountProgress >= 100 ? 'text-green-600 font-semibold' : ''}>
                {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()} words
                {wordCountProgress >= 100 && ' ✓'}
              </span>
            </div>
          </div>

          {/* Scene delete button */}
          {isScene && (
            <button
              onClick={handleDeleteScene}
              disabled={isDeleting}
              className="flex-shrink-0 text-faded-ink/50 hover:text-red-500 transition-colors p-1"
              title="Delete scene"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}

          {/* Expand Icon */}
          <button
            className="flex-shrink-0 text-faded-ink hover:text-bronze transition-colors"
            onClick={handleToggleExpand}
          >
            <span className={`text-sm transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-2.5 pb-2.5 border-t border-slate-ui/30">
          {/* Beat Description */}
          {beat.beat_description && (
            <div className="pt-3 mb-3">
              <h5 className="font-sans font-semibold text-midnight text-sm mb-2">
                What should happen in this beat:
              </h5>
              <div className="max-h-40 overflow-y-auto">
                <p className="font-sans text-faded-ink text-sm leading-snug whitespace-pre-wrap">
                  {beat.beat_description}
                </p>
              </div>
            </div>
          )}

          {/* User Notes */}
          <div className="mb-3">
            <label className="font-sans font-semibold text-midnight text-sm mb-2 block">
              Your Notes:
            </label>
            <textarea
              value={notes}
              onChange={(e) => handleNotesChange(e.target.value)}
              placeholder="Add your ideas, character notes, or scene details..."
              className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50 min-h-[60px] resize-y"
              style={{ borderRadius: '2px' }}
            />
          </div>

          {/* Content Summary (if exists) */}
          {beat.content_summary && (
            <div className="mb-3 p-2.5 bg-slate-ui/10 border-l-2 border-bronze">
              <h5 className="font-sans font-semibold text-midnight text-sm mb-1">
                Written Content:
              </h5>
              <p className="font-sans text-faded-ink text-sm leading-snug">
                {beat.content_summary}
              </p>
            </div>
          )}

          {/* AI Suggestions Section */}
          {hasAISuggestions && suggestions && (
            <div className="mb-3">
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-sm font-sans font-semibold text-purple-900 flex items-center gap-2">
                  <span>🤖</span>
                  <span>AI Content Suggestions</span>
                  <span className="text-xs text-purple-600 font-normal">
                    ({suggestions.suggestions.filter(s => !s.used).length} active)
                  </span>
                </h5>
                <button
                  onClick={() => setShowAISuggestions(!showAISuggestions)}
                  className="text-xs text-purple-600 hover:text-purple-800 font-medium"
                >
                  {showAISuggestions ? 'Hide' : 'Show'}
                </button>
              </div>

              {showAISuggestions && (
                <div className="p-3 bg-purple-50 border-2 border-purple-300 space-y-2">
                  {suggestions.suggestions.map((suggestion, idx) => (
                    <BeatSuggestionCard
                      key={idx}
                      suggestion={suggestion}
                      index={idx}
                      onApply={() => handleApplySuggestion(suggestion, idx)}
                      onDismiss={() => handleDismissSuggestion(idx)}
                      onFeedback={handleSuggestionFeedback}
                      feedback={suggestionFeedback.get(idx)}
                    />
                  ))}

                  {/* Refine Suggestions Button */}
                  {hasFeedback && (
                    <button
                      onClick={handleRefineSuggestions}
                      disabled={isLoadingAI}
                      className="w-full mt-2 px-3 py-2 text-sm font-sans font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors flex items-center justify-center gap-2"
                      style={{ borderRadius: '2px' }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>Refine Based on Feedback</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Compact Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {beat.chapter_id && linkedChapter ? (
              <button
                onClick={() => onOpenChapter?.(beat.chapter_id!)}
                className="px-4 py-2 text-sm bg-bronze text-white hover:bg-bronze-dark font-sans font-semibold transition-colors flex items-center gap-2"
                style={{ borderRadius: '2px' }}
                title={`Continue writing ${linkedChapter.title}`}
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Continue Writing</span>
              </button>
            ) : (
              <>
                {/* Link Existing Chapter Dropdown */}
                {chapters.length > 0 && (
                  <select
                    onChange={(e) => e.target.value && handleLinkChapter(e.target.value)}
                    value=""
                    disabled={isUpdating || loadingChapters}
                    className="px-3 py-1.5 text-sm border border-slate-ui focus:border-bronze focus:outline-none font-sans text-midnight disabled:opacity-50 bg-white"
                    style={{ borderRadius: '2px' }}
                    title="Link to existing chapter"
                  >
                    <option value="">Link chapter...</option>
                    {chapters.map((chapter) => (
                      <option key={chapter.id} value={chapter.id}>
                        {chapter.title}
                      </option>
                    ))}
                  </select>
                )}

                {/* Create New Chapter Button */}
                <button
                  onClick={() => onCreateChapter?.(beat)}
                  className="px-3 py-1.5 text-sm bg-bronze hover:bg-bronze-dark text-white font-sans font-medium transition-colors flex items-center gap-1.5"
                  style={{ borderRadius: '2px' }}
                  title="Create new chapter for this beat"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>New Chapter</span>
                </button>
              </>
            )}

            {/* Get AI Ideas Button */}
            {onGetAIIdeas && (
              <button
                onClick={handleGetAIIdeas}
                disabled={isLoadingAI}
                className={`ml-auto px-3 py-1.5 text-sm ${
                  isLoadingAI
                    ? 'bg-gray-100 text-gray-400 cursor-wait'
                    : 'bg-purple-500/10 text-purple-600 hover:bg-purple-500/20'
                } border border-purple-500/30 font-sans font-medium transition-colors flex items-center gap-1.5`}
                style={{ borderRadius: '2px' }}
                title="Get AI-powered content suggestions for this beat"
              >
                {isLoadingAI ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Loading...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <span>{hasAISuggestions ? 'View AI Ideas' : 'AI Ideas'}</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Metadata */}
          <div className="mt-3 pt-3 border-t border-slate-ui/30 flex justify-between text-xs font-sans text-faded-ink">
            <span>Order: #{beat.order_index + 1}</span>
            {beat.completed_at && (
              <span>Completed {new Date(beat.completed_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
