/**
 * SuggestionCard - Card for displaying entity suggestions from NLP
 * Supports both quick approval and edit-before-approval modes
 */

import { useState } from 'react';
import type { Entity, EntitySuggestion, EntityType } from '@/types/codex';
import { getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';

interface SuggestionCardProps {
  suggestion: EntitySuggestion;
  entities: Entity[];
  onApprove: (overrides?: {
    name?: string;
    type?: EntityType;
    description?: string;
  }) => void;
  onAddAsAlias: (entityId: string) => void;
  onReject: () => void;
  isProcessing?: boolean;
}

const ENTITY_TYPES: EntityType[] = ['CHARACTER', 'LOCATION', 'ITEM', 'LORE'] as EntityType[];

export default function SuggestionCard({
  suggestion,
  entities,
  onApprove,
  onAddAsAlias,
  onReject,
  isProcessing = false,
}: SuggestionCardProps) {
  const [showMergeOptions, setShowMergeOptions] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Edit form state
  const [editedName, setEditedName] = useState(suggestion.name);
  const [editedType, setEditedType] = useState<EntityType>(suggestion.type);
  const [editedDescription, setEditedDescription] = useState(
    suggestion.extracted_description || ''
  );

  const typeColor = getEntityTypeColor(suggestion.type);
  const typeIcon = getEntityTypeIcon(suggestion.type);

  // Reset edit form when exiting edit mode
  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedName(suggestion.name);
    setEditedType(suggestion.type);
    setEditedDescription(suggestion.extracted_description || '');
  };

  // Handle save from edit mode
  const handleSaveAndCreate = () => {
    const overrides: { name?: string; type?: EntityType; description?: string } = {};

    if (editedName !== suggestion.name) {
      overrides.name = editedName;
    }
    if (editedType !== suggestion.type) {
      overrides.type = editedType;
    }
    if (editedDescription.trim()) {
      overrides.description = editedDescription.trim();
    }

    onApprove(Object.keys(overrides).length > 0 ? overrides : undefined);
  };

  // Check if we have extracted attributes to display
  const hasExtractedInfo = suggestion.extracted_description ||
    (suggestion.extracted_attributes && Object.keys(suggestion.extracted_attributes).length > 0);

  return (
    <div
      className="bg-white border border-slate-ui p-3 hover:shadow-sm transition-shadow"
      style={{ borderRadius: '2px' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg" title={editMode ? editedType : suggestion.type}>
            {editMode ? getEntityTypeIcon(editedType) : typeIcon}
          </span>
          {editMode ? (
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              className="font-garamond font-semibold text-midnight border border-slate-ui px-2 py-1 w-full"
              style={{ borderRadius: '2px' }}
              placeholder="Entity name"
            />
          ) : (
            <h4 className="font-garamond font-semibold text-midnight">
              {suggestion.name}
            </h4>
          )}
        </div>

        {/* Type Badge / Dropdown */}
        {editMode ? (
          <select
            value={editedType}
            onChange={(e) => setEditedType(e.target.value as EntityType)}
            className="text-xs font-sans px-2 py-1 border border-slate-ui"
            style={{ borderRadius: '2px' }}
          >
            {ENTITY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        ) : (
          <span
            className="inline-block px-2 py-0.5 text-xs font-sans text-white"
            style={{
              backgroundColor: typeColor,
              borderRadius: '2px',
            }}
          >
            {suggestion.type}
          </span>
        )}
      </div>

      {/* Context */}
      {suggestion.context && !editMode && (
        <div className="mb-3">
          <p className="text-xs text-faded-ink font-sans mb-1">Found in:</p>
          <p className="text-sm text-midnight font-serif italic line-clamp-2">
            "{suggestion.context}"
          </p>
        </div>
      )}

      {/* Extracted Description (if available and not in edit mode) */}
      {hasExtractedInfo && !editMode && (
        <div className="mb-3 p-2 bg-vellum" style={{ borderRadius: '2px' }}>
          {suggestion.extracted_description && (
            <div className="mb-2">
              <p className="text-xs text-faded-ink font-sans mb-1">Extracted description:</p>
              <p className="text-sm text-midnight font-sans">
                {suggestion.extracted_description}
              </p>
            </div>
          )}

          {/* Extracted attributes as tags */}
          {suggestion.extracted_attributes && (
            <div className="space-y-1">
              {suggestion.extracted_attributes.appearance && suggestion.extracted_attributes.appearance.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-faded-ink">Appearance:</span>
                  {suggestion.extracted_attributes.appearance.slice(0, 3).map((attr, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-800 px-1 rounded">
                      {attr}
                    </span>
                  ))}
                </div>
              )}
              {suggestion.extracted_attributes.personality && suggestion.extracted_attributes.personality.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-faded-ink">Personality:</span>
                  {suggestion.extracted_attributes.personality.slice(0, 3).map((attr, i) => (
                    <span key={i} className="text-xs bg-purple-100 text-purple-800 px-1 rounded">
                      {attr}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Description field in edit mode */}
      {editMode && (
        <div className="mb-3">
          <label className="text-xs text-faded-ink font-sans mb-1 block">
            Description (optional):
          </label>
          <textarea
            value={editedDescription}
            onChange={(e) => setEditedDescription(e.target.value)}
            placeholder="Add a description for this entity..."
            className="w-full border border-slate-ui px-2 py-1 text-sm font-sans resize-none"
            style={{ borderRadius: '2px' }}
            rows={3}
          />
          {suggestion.extracted_description && editedDescription !== suggestion.extracted_description && (
            <button
              onClick={() => setEditedDescription(suggestion.extracted_description || '')}
              className="text-xs text-bronze hover:underline mt-1"
            >
              Use extracted description
            </button>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {!showMergeOptions && !editMode && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => onApprove()}
            disabled={isProcessing}
            className="flex-1 bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Create entity with suggested values"
          >
            {isProcessing && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            {isProcessing ? 'Creating...' : 'Quick Approve'}
          </button>
          <button
            onClick={() => setEditMode(true)}
            disabled={isProcessing}
            className="flex-1 bg-blue-500 text-white px-3 py-1.5 text-sm font-sans hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Edit details before creating entity"
          >
            Edit & Approve
          </button>
          <button
            onClick={() => setShowMergeOptions(true)}
            disabled={isProcessing || entities.length === 0}
            className="bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Add as alias to existing entity"
          >
            Merge
          </button>
          <button
            onClick={onReject}
            disabled={isProcessing}
            className="bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
            title="Reject this suggestion"
          >
            {isProcessing && <div className="w-3 h-3 border-2 border-midnight border-t-transparent rounded-full animate-spin"></div>}
            Reject
          </button>
        </div>
      )}

      {/* Edit mode buttons */}
      {editMode && (
        <div className="flex gap-2">
          <button
            onClick={handleSaveAndCreate}
            disabled={isProcessing || !editedName.trim()}
            className="flex-1 bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            style={{ borderRadius: '2px' }}
          >
            {isProcessing && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            {isProcessing ? 'Creating...' : 'Save & Create'}
          </button>
          <button
            onClick={handleCancelEdit}
            disabled={isProcessing}
            className="flex-1 bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 transition-colors disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Merge options */}
      {showMergeOptions && (
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
