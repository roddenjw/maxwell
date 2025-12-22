/**
 * EntityCard - Compact card for displaying entity in list
 */

import type { Entity } from '@/types/codex';
import { getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';

interface EntityCardProps {
  entity: Entity;
  isSelected?: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export default function EntityCard({
  entity,
  isSelected = false,
  onSelect,
  onDelete,
}: EntityCardProps) {
  const typeColor = getEntityTypeColor(entity.type);
  const typeIcon = getEntityTypeIcon(entity.type);

  return (
    <div
      onClick={onSelect}
      className={`
        relative bg-white border rounded cursor-pointer transition-all
        ${isSelected ? 'border-bronze shadow-md' : 'border-slate-ui hover:border-bronze/50 hover:shadow-sm'}
      `}
      style={{ borderRadius: '2px' }}
      title={`Click to view ${entity.name} details`}
    >
      {/* Entity Header */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            {/* Type Icon and Name */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg" title={entity.type}>
                {typeIcon}
              </span>
              <h3 className="font-garamond font-semibold text-midnight truncate">
                {entity.name}
              </h3>
            </div>

            {/* Type Badge */}
            <span
              className="inline-block px-2 py-0.5 text-xs font-sans text-white"
              style={{
                backgroundColor: typeColor,
                borderRadius: '2px',
              }}
            >
              {entity.type}
            </span>

            {/* Aliases */}
            {entity.aliases && entity.aliases.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-faded-ink font-sans">
                  Also known as: {entity.aliases.join(', ')}
                </p>
              </div>
            )}
          </div>

          {/* Delete Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete entity "${entity.name}"?`)) {
                onDelete();
              }
            }}
            className="text-faded-ink hover:text-redline transition-colors text-sm p-1"
            title="Delete entity"
          >
            ×
          </button>
        </div>

        {/* Appearance Count */}
        {entity.appearance_history && entity.appearance_history.length > 0 && (
          <div className="mt-2 text-xs text-faded-ink font-sans" title="Number of times this entity appears in the manuscript">
            {entity.appearance_history.length} appearance{entity.appearance_history.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Selected Indicator */}
      {isSelected && (
        <div
          className="absolute left-0 top-0 bottom-0 w-1"
          style={{ backgroundColor: typeColor }}
        />
      )}
    </div>
  );
}
