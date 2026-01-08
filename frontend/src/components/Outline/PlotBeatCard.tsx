/**
 * PlotBeatCard Component
 * Individual plot beat display with completion tracking and notes
 */

import { useState, useRef, useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import type { PlotBeat } from '@/types/outline';

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
  const { updateBeat, expandedBeatId, setExpandedBeat, beatSuggestions } = useOutlineStore();
  const [isUpdating, setIsUpdating] = useState(false);
  const [notes, setNotes] = useState(beat.user_notes);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const notesTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isExpanded = expandedBeatId === beat.id;
  const hasAISuggestions = beatSuggestions.has(beat.id);

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

  return (
    <div
      className={`bg-white border-2 transition-all ${
        beat.is_completed
          ? 'border-bronze bg-bronze/5'
          : 'border-slate-ui hover:border-bronze/50'
      }`}
      style={{ borderRadius: '2px' }}
    >
      {/* Header - Always Visible */}
      <div
        className="p-3 cursor-pointer"
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
            className={`flex-shrink-0 mt-1 w-5 h-5 border-2 flex items-center justify-center transition-colors ${
              beat.is_completed
                ? 'bg-bronze border-bronze'
                : 'border-slate-ui hover:border-bronze'
            }`}
            style={{ borderRadius: '2px' }}
          >
            {beat.is_completed && (
              <span className="text-white text-xs">✓</span>
            )}
          </button>

          {/* Beat Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                {beat.beat_name}
              </span>
              <span className="text-xs font-sans text-faded-ink">
                {Math.round(beat.target_position_percent * 100)}% through story
              </span>
            </div>

            {/* Beat Title and Status */}
            <div className="flex items-start gap-2 mb-2">
              <h4 className={`flex-1 font-serif font-bold text-lg ${
                beat.is_completed ? 'text-bronze' : 'text-midnight'
              }`}>
                {beat.beat_label}
              </h4>

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
              <p className="mt-1 mb-2 text-sm text-faded-ink italic line-clamp-2">
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
        <div className="px-3 pb-3 border-t border-slate-ui/30">
          {/* Beat Description */}
          {beat.beat_description && (
            <div className="pt-4 mb-4">
              <h5 className="font-sans font-semibold text-midnight text-sm mb-2">
                What should happen in this beat:
              </h5>
              <p className="font-sans text-faded-ink text-sm leading-relaxed whitespace-pre-wrap">
                {beat.beat_description}
              </p>
            </div>
          )}

          {/* User Notes */}
          <div className="mb-4">
            <label className="font-sans font-semibold text-midnight text-sm mb-2 block">
              Your Notes:
            </label>
            <textarea
              value={notes}
              onChange={(e) => handleNotesChange(e.target.value)}
              placeholder="Add your ideas, character notes, or scene details..."
              className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50 min-h-[60px] resize-y"
              style={{ borderRadius: '2px' }}
            />
          </div>

          {/* Content Summary (if exists) */}
          {beat.content_summary && (
            <div className="mb-4 p-3 bg-slate-ui/10 border-l-2 border-bronze">
              <h5 className="font-sans font-semibold text-midnight text-sm mb-1">
                Written Content:
              </h5>
              <p className="font-sans text-faded-ink text-sm">
                {beat.content_summary}
              </p>
            </div>
          )}

          {/* Compact Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {beat.chapter_id && linkedChapter ? (
              <button
                onClick={() => onOpenChapter?.(beat.chapter_id!)}
                className="px-3 py-1.5 text-sm bg-bronze/10 text-bronze border border-bronze/30 hover:bg-bronze/20 font-sans font-medium transition-colors flex items-center gap-1.5"
                style={{ borderRadius: '2px' }}
                title={`Open ${linkedChapter.title}`}
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span className="truncate max-w-[200px]">{linkedChapter.title}</span>
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
                onClick={() => onGetAIIdeas(beat.id)}
                className="ml-auto px-3 py-1.5 text-sm bg-purple-500/10 text-purple-600 border border-purple-500/30 hover:bg-purple-500/20 font-sans font-medium transition-colors flex items-center gap-1.5"
                style={{ borderRadius: '2px' }}
                title="Get AI-powered content suggestions for this beat"
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>{hasAISuggestions ? 'View AI Ideas' : 'AI Ideas'}</span>
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
