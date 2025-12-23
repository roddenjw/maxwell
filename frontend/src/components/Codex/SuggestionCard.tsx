/**
 * SuggestionCard - Card for displaying entity suggestions from NLP
 */

import { useState } from 'react';
import type { Entity, EntitySuggestion } from '@/types/codex';
import { getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';

interface SuggestionCardProps {
  suggestion: EntitySuggestion;
  entities: Entity[];
  onApprove: () => void;
  onAddAsAlias: (entityId: string) => void;
  onReject: () => void;
  isProcessing?: boolean;
}

export default function SuggestionCard({
  suggestion,
  entities,
  onApprove,
  onAddAsAlias,
  onReject,
  isProcessing = false,
}: SuggestionCardProps) {
  const [showMergeOptions, setShowMergeOptions] = useState(false);
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
      {!showMergeOptions ? (
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            disabled={isProcessing}
            className="flex-1 bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Create new entity"
          >
            {isProcessing && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            {isProcessing ? 'Approving...' : '✓ Approve'}
          </button>
          <button
            onClick={() => setShowMergeOptions(true)}
            disabled={isProcessing || entities.length === 0}
            className="flex-1 bg-blue-500 text-white px-3 py-1.5 text-sm font-sans hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Add as alias to existing entity"
          >
            ⮕ Merge
          </button>
          <button
            onClick={onReject}
            disabled={isProcessing}
            className="flex-1 bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Reject this suggestion"
          >
            {isProcessing && <div className="w-3 h-3 border-2 border-midnight border-t-transparent rounded-full animate-spin"></div>}
            {isProcessing ? 'Rejecting...' : '× Reject'}
          </button>
        </div>
      ) : (
        <div>
          <p className="text-xs text-faded-ink font-sans mb-2">Merge with existing entity:</p>
          <div className="max-h-32 overflow-y-auto mb-2 space-y-1">
            {entities
              .filter((e) => e.type === suggestion.type)
              .map((entity) => (
                <button
                  key={entity.id}
                  onClick={() => onAddAsAlias(entity.id)}
                  disabled={isProcessing}
                  className="w-full text-left px-2 py-1.5 text-sm font-sans bg-vellum hover:bg-bronze/10 transition-colors disabled:opacity-50"
                  style={{ borderRadius: '2px' }}
                >
                  {entity.name}
                  {entity.aliases.length > 0 && (
                    <span className="text-xs text-faded-ink ml-2">
                      (aka {entity.aliases.join(', ')})
                    </span>
                  )}
                </button>
              ))}
          </div>
          <button
            onClick={() => setShowMergeOptions(false)}
            className="text-xs text-bronze hover:underline"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
