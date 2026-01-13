import { useState } from 'react';
import type { BeatSuggestion } from '../../types/outline';

interface BeatSuggestionCardProps {
  suggestion: BeatSuggestion;
  onApply: () => void;
  onDismiss: () => void;
}

/**
 * BeatSuggestionCard Component
 *
 * Displays a single AI-generated suggestion for a plot beat with options to apply or dismiss.
 * Part of the AI beat analysis feature.
 *
 * Features:
 * - Type-based icons (scene, character, dialogue, subplot)
 * - Expandable description
 * - Apply button to use the suggestion
 * - Dismiss button to mark as used
 * - Visual dimming when marked as used
 */
export default function BeatSuggestionCard({ suggestion, onApply, onDismiss }: BeatSuggestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

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

          {/* Expanded Description */}
          {isExpanded && (
            <p className={`text-sm mt-2 ${suggestion.used ? 'text-gray-500' : 'text-midnight'}`}>
              {suggestion.description}
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

          {/* Apply and Dismiss Buttons (only if not used) */}
          {!suggestion.used && (
            <div className="flex flex-col gap-1">
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
          )}

          {/* Used Badge */}
          {suggestion.used && (
            <span className="text-[9px] font-sans font-bold uppercase text-gray-400 px-1 text-center">
              Used
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
