import { useState } from 'react';
import type { BeatSuggestion } from '../../types/outline';
import RefinementPanel from '../shared/RefinementPanel';

interface BeatSuggestionCardProps {
  suggestion: BeatSuggestion;
  index: number;
  onApply: () => void;
  onDismiss: () => void;
  onFeedback?: (index: number, feedback: 'like' | 'dislike') => void;
  feedback?: 'like' | 'dislike' | null;
  onRefineAccept?: (refined: any) => void;
  beatContext?: Record<string, string>;
}

/**
 * BeatSuggestionCard Component
 *
 * Displays a single AI-generated suggestion for a plot beat with options to apply, dismiss, refine, or provide feedback.
 * Part of the AI beat analysis feature with refinement loop support.
 */
export default function BeatSuggestionCard({
  suggestion,
  index,
  onApply,
  onDismiss,
  onFeedback,
  feedback,
  onRefineAccept,
  beatContext,
}: BeatSuggestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showRefine, setShowRefine] = useState(false);

  // Type-based icons and colors
  const typeConfig = {
    scene: { icon: '🎬', color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' },
    character: { icon: '👤', color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
    dialogue: { icon: '💬', color: 'text-purple-600', bgColor: 'bg-purple-50', borderColor: 'border-purple-200' },
    subplot: { icon: '🔀', color: 'text-orange-600', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' },
  };

  const config = typeConfig[suggestion.type];

  return (
    <div
      className={`p-2 border ${config.borderColor} transition-all ${
        suggestion.used
          ? 'opacity-50 bg-gray-50 border-gray-200'
          : `${config.bgColor} hover:shadow-sm`
      }`}
      style={{ borderRadius: '2px' }}
    >
      <div className="flex items-start justify-between gap-2">
        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base flex-shrink-0">{config.icon}</span>
            <span
              className={`font-sans font-semibold text-sm flex-1 ${
                suggestion.used ? 'text-gray-500 line-through' : config.color
              }`}
            >
              {suggestion.title}
            </span>
            <span
              className={`text-[10px] font-sans font-bold uppercase px-1.5 py-0.5 ${
                suggestion.used
                  ? 'bg-gray-100 text-gray-500'
                  : `${config.bgColor} ${config.color}`
              }`}
              style={{ borderRadius: '2px' }}
            >
              {suggestion.type}
            </span>
          </div>

          {/* Description */}
          {isExpanded ? (
            <p className={`text-sm mt-2 ${suggestion.used ? 'text-gray-500' : 'text-midnight'}`}>
              {suggestion.description}
            </p>
          ) : suggestion.description && (
            <p className={`text-xs mt-1 truncate ${suggestion.used ? 'text-gray-400' : 'text-faded-ink'}`}>
              {suggestion.description.length > 80
                ? suggestion.description.slice(0, 80) + '...'
                : suggestion.description}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-1 flex-shrink-0">
          {/* Expand/Collapse Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-white rounded transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
            aria-label={isExpanded ? 'Collapse suggestion' : 'Expand suggestion'}
          >
            <svg
              className="w-4 h-4 text-faded-ink"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {isExpanded ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              )}
            </svg>
          </button>

          {/* Apply, Refine, and Dismiss Buttons (only if not used) */}
          {!suggestion.used && (
            <>
              {/* Feedback Buttons */}
              {onFeedback && (
                <div className="flex gap-0.5">
                  <button
                    onClick={() => onFeedback(index, 'like')}
                    className={`p-1 rounded transition-colors ${
                      feedback === 'like'
                        ? 'bg-green-100 text-green-600'
                        : 'text-gray-400 hover:bg-green-50 hover:text-green-500'
                    }`}
                    title="Like this suggestion (use for refinement)"
                    aria-label="Like suggestion"
                  >
                    <svg className="w-3 h-3" fill={feedback === 'like' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onFeedback(index, 'dislike')}
                    className={`p-1 rounded transition-colors ${
                      feedback === 'dislike'
                        ? 'bg-red-100 text-red-600'
                        : 'text-gray-400 hover:bg-red-50 hover:text-red-500'
                    }`}
                    title="Dislike this suggestion (avoid in refinement)"
                    aria-label="Dislike suggestion"
                  >
                    <svg className="w-3 h-3" fill={feedback === 'dislike' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                    </svg>
                  </button>
                </div>
              )}

              <div className="flex flex-col gap-1">
                {/* Refine Button */}
                {onRefineAccept && (
                  <button
                    onClick={() => setShowRefine(!showRefine)}
                    className={`p-1 rounded transition-colors ${
                      showRefine
                        ? 'bg-purple-100 text-purple-600'
                        : 'text-purple-400 hover:bg-purple-50 hover:text-purple-600'
                    }`}
                    title="Refine this suggestion with AI"
                    aria-label="Refine suggestion"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                )}
                <button
                  onClick={onApply}
                  className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
                  title="Apply this suggestion to beat description"
                  aria-label="Apply suggestion"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={onDismiss}
                  className="p-1 text-gray-500 hover:bg-gray-100 rounded transition-colors"
                  title="Dismiss this suggestion"
                  aria-label="Dismiss suggestion"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </>
          )}

          {/* Used Badge */}
          {suggestion.used && (
            <span className="text-[9px] font-sans font-bold uppercase text-gray-400 px-1 text-center">
              Used
            </span>
          )}
        </div>
      </div>

      {/* Inline Refinement Panel */}
      {showRefine && onRefineAccept && (
        <RefinementPanel
          suggestion={{
            title: suggestion.title,
            description: suggestion.description,
            type: suggestion.type,
          }}
          domain="beat_suggestion"
          context={beatContext || {}}
          renderSuggestion={(s) => (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base">{config.icon}</span>
                <span className={`font-sans font-semibold text-sm ${config.color}`}>
                  {s.title}
                </span>
              </div>
              <p className="text-sm text-midnight">{s.description}</p>
            </div>
          )}
          onAccept={(refined) => {
            onRefineAccept(refined);
            setShowRefine(false);
          }}
          onCancel={() => setShowRefine(false)}
        />
      )}
    </div>
  );
}
