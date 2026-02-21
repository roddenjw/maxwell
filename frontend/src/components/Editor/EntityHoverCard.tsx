/**
 * EntityHoverCard - Floating tooltip for entity mentions
 * Shows entity details when hovering over mentions in the editor
 */

import { createPortal } from 'react-dom';
import type { Entity, EntityType } from '@/types/codex';
import { getEntityTypeIcon } from '@/types/codex';
import { Z_INDEX } from '@/lib/zIndex';

interface EntityHoverCardProps {
  entity: Entity | null;
  entityName: string;
  entityType: EntityType;
  position: { x: number; y: number };
  onViewInCodex: () => void;
}

const TYPE_BADGE_STYLES: Record<EntityType, string> = {
  CHARACTER: 'bg-bronze/20 text-bronze',
  LOCATION: 'bg-green-100 text-green-700',
  ITEM: 'bg-amber-100 text-amber-700',
  LORE: 'bg-purple-100 text-purple-700',
  CULTURE: 'bg-amber-100 text-amber-800',
  CREATURE: 'bg-red-100 text-red-700',
  RACE: 'bg-pink-100 text-pink-700',
  ORGANIZATION: 'bg-violet-100 text-violet-700',
  EVENT: 'bg-teal-100 text-teal-700',
};

const TYPE_LABELS: Record<EntityType, string> = {
  CHARACTER: 'Character',
  LOCATION: 'Location',
  ITEM: 'Item',
  LORE: 'Lore',
  CULTURE: 'Culture',
  CREATURE: 'Creature',
  RACE: 'Race',
  ORGANIZATION: 'Organization',
  EVENT: 'Event',
};

export function EntityHoverCard({
  entity,
  entityName,
  entityType,
  position,
  onViewInCodex,
}: EntityHoverCardProps) {
  // Get description from entity attributes or use fallback
  const description = entity?.attributes?.description
    || entity?.attributes?.backstory
    || entity?.attributes?.appearance
    || null;

  // Truncate description to ~100 chars
  const truncatedDescription = description
    ? description.length > 100
      ? description.slice(0, 100).trim() + '...'
      : description
    : null;

  // Calculate position - flip above if near bottom of viewport
  const viewportHeight = window.innerHeight;
  const cardHeight = 120; // Approximate card height
  const shouldFlipUp = position.y + cardHeight > viewportHeight - 20;

  // Keep card within horizontal bounds
  const viewportWidth = window.innerWidth;
  const cardWidth = 280;
  let adjustedX = position.x;
  if (adjustedX + cardWidth > viewportWidth - 20) {
    adjustedX = viewportWidth - cardWidth - 20;
  }
  if (adjustedX < 20) {
    adjustedX = 20;
  }

  const style: React.CSSProperties = {
    position: 'fixed',
    left: adjustedX,
    top: shouldFlipUp ? 'auto' : position.y + 8,
    bottom: shouldFlipUp ? viewportHeight - position.y + 8 : 'auto',
    zIndex: Z_INDEX.HOVER_CARD,
    width: cardWidth,
  };

  const card = (
    <div
      style={style}
      className="bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden animate-in fade-in-0 zoom-in-95 duration-100"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-base flex-shrink-0">
            {getEntityTypeIcon(entityType)}
          </span>
          <span className="font-medium text-midnight truncate">
            {entity?.name || entityName}
          </span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${TYPE_BADGE_STYLES[entityType]}`}
        >
          {TYPE_LABELS[entityType]}
        </span>
      </div>

      {/* Description */}
      <div className="px-3 py-2 text-sm text-faded-ink min-h-[40px]">
        {truncatedDescription || (
          <span className="italic text-slate-400">No description available</span>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-slate-100">
        <button
          onClick={onViewInCodex}
          className="text-xs text-bronze hover:text-bronze/80 hover:underline transition-colors"
        >
          Click to view in Codex &rarr;
        </button>
      </div>
    </div>
  );

  return createPortal(card, document.body);
}
