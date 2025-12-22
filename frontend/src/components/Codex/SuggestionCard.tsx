/**
 * SuggestionCard - Card for displaying entity suggestions from NLP
 */

import type { EntitySuggestion } from '@/types/codex';
import { getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';

interface SuggestionCardProps {
  suggestion: EntitySuggestion;
  onApprove: () => void;
  onReject: () => void;
}

export default function SuggestionCard({
  suggestion,
  onApprove,
  onReject,
}: SuggestionCardProps) {
  const typeColor = getEntityTypeColor(suggestion.type);
  const typeIcon = getEntityTypeIcon(suggestion.type);

  return (
    <div
      className="bg-white border border-slate-ui p-3 hover:shadow-sm transition-shadow"
      style={{ borderRadius: '2px' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg" title={suggestion.type}>
            {typeIcon}
          </span>
          <h4 className="font-garamond font-semibold text-midnight">
            {suggestion.name}
          </h4>
        </div>

        {/* Type Badge */}
        <span
          className="inline-block px-2 py-0.5 text-xs font-sans text-white"
          style={{
            backgroundColor: typeColor,
            borderRadius: '2px',
          }}
        >
          {suggestion.type}
        </span>
      </div>

      {/* Context */}
      {suggestion.context && (
        <div className="mb-3">
          <p className="text-xs text-faded-ink font-sans mb-1">Found in:</p>
          <p className="text-sm text-midnight font-serif italic line-clamp-2">
            "{suggestion.context}"
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={onApprove}
          className="flex-1 bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          ✓ Approve
        </button>
        <button
          onClick={onReject}
          className="flex-1 bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          × Reject
        </button>
      </div>
    </div>
  );
}
