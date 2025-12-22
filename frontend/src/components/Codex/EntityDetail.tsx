/**
 * EntityDetail - Detailed view and editing for selected entity
 */

import { useState } from 'react';
import type { Entity } from '@/types/codex';
import { getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';

interface EntityDetailProps {
  entity: Entity;
  onUpdate: (updates: Partial<Entity>) => void;
  onClose: () => void;
}

export default function EntityDetail({
  entity,
  onUpdate,
  onClose,
}: EntityDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(entity.name);
  const [editedAliases, setEditedAliases] = useState(entity.aliases.join(', '));
  const [editedAttributes, setEditedAttributes] = useState(() => {
    // Convert attributes to editable format
    const attrs = entity.attributes || {};
    return {
      description: attrs.description || '',
      notes: attrs.notes || '',
    };
  });

  const typeColor = getEntityTypeColor(entity.type);
  const typeIcon = getEntityTypeIcon(entity.type);

  const handleSave = () => {
    // Parse aliases
    const aliases = editedAliases
      .split(',')
      .map((a) => a.trim())
      .filter((a) => a.length > 0);

    // Update attributes
    const attributes = {
      ...entity.attributes,
      ...editedAttributes,
    };

    onUpdate({
      name: editedName,
      aliases,
      attributes,
    });

    setIsEditing(false);
  };

  const handleCancel = () => {
    // Reset to original values
    setEditedName(entity.name);
    setEditedAliases(entity.aliases.join(', '));
    setEditedAttributes({
      description: entity.attributes?.description || '',
      notes: entity.attributes?.notes || '',
    });
    setIsEditing(false);
  };

  return (
    <div className="bg-vellum h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-slate-ui p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{typeIcon}</span>
          <div>
            {isEditing ? (
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="text-xl font-garamond font-bold text-midnight bg-white border border-slate-ui px-2 py-1"
                style={{ borderRadius: '2px' }}
              />
            ) : (
              <h2 className="text-xl font-garamond font-bold text-midnight">
                {entity.name}
              </h2>
            )}
            <span
              className="inline-block mt-1 px-2 py-0.5 text-xs font-sans text-white"
              style={{
                backgroundColor: typeColor,
                borderRadius: '2px',
              }}
            >
              {entity.type}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90"
                style={{ borderRadius: '2px' }}
              >
                Save
              </button>
              <button
                onClick={handleCancel}
                className="bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90"
              style={{ borderRadius: '2px' }}
            >
              Edit
            </button>
          )}
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Aliases */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Aliases (comma-separated)
          </label>
          {isEditing ? (
            <input
              type="text"
              value={editedAliases}
              onChange={(e) => setEditedAliases(e.target.value)}
              placeholder="e.g., John, Johnny, The Smith"
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-sans text-midnight">
              {entity.aliases.length > 0 ? entity.aliases.join(', ') : 'None'}
            </p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Description
          </label>
          {isEditing ? (
            <textarea
              value={editedAttributes.description}
              onChange={(e) =>
                setEditedAttributes({ ...editedAttributes, description: e.target.value })
              }
              placeholder="Enter description..."
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif text-midnight min-h-[100px]"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-serif text-midnight whitespace-pre-wrap">
              {editedAttributes.description || 'No description'}
            </p>
          )}
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Notes
          </label>
          {isEditing ? (
            <textarea
              value={editedAttributes.notes}
              onChange={(e) =>
                setEditedAttributes({ ...editedAttributes, notes: e.target.value })
              }
              placeholder="Enter notes..."
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif text-midnight min-h-[100px]"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-serif text-midnight whitespace-pre-wrap">
              {editedAttributes.notes || 'No notes'}
            </p>
          )}
        </div>

        {/* Appearance History */}
        {entity.appearance_history && entity.appearance_history.length > 0 && (
          <div>
            <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
              Appearance History ({entity.appearance_history.length})
            </label>
            <div className="space-y-2">
              {entity.appearance_history.map((appearance, index) => (
                <div
                  key={index}
                  className="bg-white border border-slate-ui p-2"
                  style={{ borderRadius: '2px' }}
                >
                  <p className="text-sm font-serif text-midnight">
                    {appearance.description}
                  </p>
                  {appearance.timestamp && (
                    <p className="text-xs text-faded-ink font-sans mt-1">
                      {new Date(appearance.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="pt-4 border-t border-slate-ui">
          <p className="text-xs text-faded-ink font-sans">
            Created: {new Date(entity.created_at).toLocaleString()}
          </p>
          <p className="text-xs text-faded-ink font-sans">
            Updated: {new Date(entity.updated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
