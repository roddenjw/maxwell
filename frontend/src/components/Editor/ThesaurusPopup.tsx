/**
 * ThesaurusPopup - Floating popup showing synonyms for selected word
 * Appears when user clicks the thesaurus button in SelectionToolbar
 */

import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection } from 'lexical';
import { Z_INDEX } from '@/lib/zIndex';
import { thesaurusApi } from '@/lib/api';
import type { SynonymsResponse, SynonymGroup } from '@/types/thesaurus';

interface ThesaurusPopupProps {
  word: string;
  position: { x: number; y: number };
  onClose: () => void;
  onReplaceWord?: (newWord: string) => void;
}

const POS_COLORS: Record<string, string> = {
  verb: 'bg-blue-100 text-blue-700',
  noun: 'bg-green-100 text-green-700',
  adjective: 'bg-purple-100 text-purple-700',
  adverb: 'bg-amber-100 text-amber-700',
  general: 'bg-slate-100 text-slate-700',
};

const POS_ICONS: Record<string, string> = {
  verb: 'V',
  noun: 'N',
  adjective: 'Adj',
  adverb: 'Adv',
  general: '',
};

export function ThesaurusPopup({
  word,
  position,
  onClose,
  onReplaceWord,
}: ThesaurusPopupProps) {
  const [editor] = useLexicalComposerContext();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<SynonymsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['verb', 'adjective']));

  // Fetch synonyms when word changes
  useEffect(() => {
    let cancelled = false;

    const fetchSynonyms = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await thesaurusApi.getSynonyms(word, 15);
        if (!cancelled) {
          setData(result);
          // Auto-expand first two groups with results
          const groupsWithResults = result.groups?.slice(0, 2).map(g => g.part_of_speech) || [];
          setExpandedGroups(new Set(groupsWithResults));
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to fetch synonyms');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    if (word) {
      fetchSynonyms();
    }

    return () => {
      cancelled = true;
    };
  }, [word]);

  // Handle clicking a synonym to replace the selected word
  const handleSynonymClick = useCallback((synonym: string) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        // Replace the selected text with the synonym
        selection.insertText(synonym);
      }
    });
    onReplaceWord?.(synonym);
    onClose();
  }, [editor, onClose, onReplaceWord]);

  // Toggle group expansion
  const toggleGroup = (pos: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(pos)) {
        next.delete(pos);
      } else {
        next.add(pos);
      }
      return next;
    });
  };

  // Calculate position - keep within viewport
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  const cardWidth = 320;
  const cardMaxHeight = 400;

  let adjustedX = position.x;
  let adjustedY = position.y + 10;

  // Keep within horizontal bounds
  if (adjustedX + cardWidth > viewportWidth - 20) {
    adjustedX = viewportWidth - cardWidth - 20;
  }
  if (adjustedX < 20) {
    adjustedX = 20;
  }

  // Flip above if near bottom
  const shouldFlipUp = adjustedY + cardMaxHeight > viewportHeight - 20;
  if (shouldFlipUp) {
    adjustedY = position.y - 10;
  }

  const style: React.CSSProperties = {
    position: 'fixed',
    left: adjustedX,
    top: shouldFlipUp ? 'auto' : adjustedY,
    bottom: shouldFlipUp ? viewportHeight - position.y + 10 : 'auto',
    zIndex: Z_INDEX.HOVER_CARD,
    width: cardWidth,
    maxHeight: cardMaxHeight,
  };

  const content = (
    <div
      style={style}
      className="bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden animate-in fade-in-0 zoom-in-95 duration-100 flex flex-col"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-bronze/5 to-transparent flex-shrink-0">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-bronze" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <span className="font-medium text-midnight">
            Synonyms for "<span className="text-bronze">{word}</span>"
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-faded-ink hover:text-midnight transition-colors p-1"
          aria-label="Close"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="overflow-y-auto flex-1 p-3">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-bronze border-t-transparent" />
          </div>
        )}

        {error && (
          <div className="text-center py-6 text-red-600 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && data && !data.found && (
          <div className="text-center py-6 text-faded-ink text-sm">
            No synonyms found for "{word}"
          </div>
        )}

        {!loading && !error && data && data.found && (
          <div className="space-y-3">
            {data.groups.map((group: SynonymGroup) => (
              <div key={group.part_of_speech} className="border border-slate-100 rounded-md overflow-hidden">
                {/* Group header */}
                <button
                  onClick={() => toggleGroup(group.part_of_speech)}
                  className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${POS_COLORS[group.part_of_speech] || POS_COLORS.general}`}>
                      {POS_ICONS[group.part_of_speech] || group.part_of_speech}
                    </span>
                    <span className="text-xs text-faded-ink">
                      {group.words.length} synonym{group.words.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <svg
                    className={`w-4 h-4 text-faded-ink transition-transform ${expandedGroups.has(group.part_of_speech) ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Group content */}
                {expandedGroups.has(group.part_of_speech) && (
                  <div className="px-3 py-2">
                    {/* Definition */}
                    {group.definition && (
                      <p className="text-xs text-faded-ink italic mb-2 line-clamp-2">
                        {group.definition}
                      </p>
                    )}

                    {/* Synonym chips */}
                    <div className="flex flex-wrap gap-1.5">
                      {group.words.map((synonym) => (
                        <button
                          key={synonym}
                          onClick={() => handleSynonymClick(synonym)}
                          className="px-2.5 py-1 text-sm bg-white border border-slate-200 rounded-md hover:border-bronze hover:bg-bronze/5 hover:text-bronze transition-colors cursor-pointer"
                          title={`Replace "${word}" with "${synonym}"`}
                        >
                          {synonym}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Antonyms section */}
            {data.antonyms && data.antonyms.length > 0 && (
              <div className="border border-red-100 rounded-md overflow-hidden">
                <div className="px-3 py-2 bg-red-50">
                  <span className="text-xs font-medium text-red-700">Antonyms</span>
                </div>
                <div className="px-3 py-2">
                  <div className="flex flex-wrap gap-1.5">
                    {data.antonyms.map((antonym) => (
                      <button
                        key={antonym}
                        onClick={() => handleSynonymClick(antonym)}
                        className="px-2.5 py-1 text-sm bg-white border border-red-200 rounded-md hover:border-red-400 hover:bg-red-50 hover:text-red-700 transition-colors cursor-pointer"
                        title={`Replace "${word}" with "${antonym}"`}
                      >
                        {antonym}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="px-3 py-2 border-t border-slate-100 bg-slate-50 flex-shrink-0">
        <p className="text-xs text-faded-ink text-center">
          Click a word to replace your selection
        </p>
      </div>
    </div>
  );

  return createPortal(content, document.body);
}

export default ThesaurusPopup;
