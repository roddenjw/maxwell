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
}

export default function PlotBeatCard({ beat, manuscriptId, onCreateChapter, onOpenChapter }: PlotBeatCardProps) {
  const { updateBeat, expandedBeatId, setExpandedBeat } = useOutlineStore();
  const [isUpdating, setIsUpdating] = useState(false);
  const [notes, setNotes] = useState(beat.user_notes);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const notesTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isExpanded = expandedBeatId === beat.id;

  // Update local notes when beat changes
  useEffect(() => {
    setNotes(beat.user_notes);
  }, [beat.user_notes]);

  // Fetch chapters when beat is expanded
  useEffect(() => {
    if (isExpanded && chapters.length === 0) {
      fetchChapters();
    }
  }, [isExpanded]);

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
        className="p-4 cursor-pointer"
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
            <h4 className={`font-serif font-bold text-lg mb-1 ${
              beat.is_completed ? 'text-bronze' : 'text-midnight'
            }`}>
              {beat.beat_label}
            </h4>

            {/* Word Count Progress Bar */}
            <div className="flex items-center gap-2 text-xs font-sans text-faded-ink">
              <div className="flex-1 h-1.5 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
                <div
                  className="h-full bg-bronze transition-all duration-300"
                  style={{ width: `${wordCountProgress}%` }}
                />
              </div>
              <span>
                {beat.actual_word_count.toLocaleString()} / {beat.target_word_count.toLocaleString()} words
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
        <div className="px-4 pb-4 border-t border-slate-ui/30">
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
              className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50 min-h-[100px] resize-y"
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

          {/* Action Buttons */}
          <div className="space-y-3">
            {beat.chapter_id ? (
              <button
                onClick={() => onOpenChapter?.(beat.chapter_id!)}
                className="w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Open Linked Chapter
              </button>
            ) : (
              <>
                {/* Link Existing Chapter */}
                {chapters.length > 0 && (
                  <div>
                    <label className="block font-sans text-xs font-semibold text-midnight mb-2">
                      Link to Existing Chapter:
                    </label>
                    <select
                      onChange={(e) => e.target.value && handleLinkChapter(e.target.value)}
                      value=""
                      disabled={isUpdating || loadingChapters}
                      className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight disabled:opacity-50"
                      style={{ borderRadius: '2px' }}
                    >
                      <option value="">Select a chapter...</option>
                      {chapters.map((chapter) => (
                        <option key={chapter.id} value={chapter.id}>
                          {chapter.title}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Create New Chapter */}
                <button
                  onClick={() => onCreateChapter?.(beat)}
                  className="w-full px-4 py-2 border-2 border-bronze text-bronze hover:bg-bronze hover:text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  {chapters.length > 0 ? 'Or Create New Chapter' : 'Create Chapter for This Beat'}
                </button>
              </>
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
