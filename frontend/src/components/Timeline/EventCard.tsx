/**
 * EventCard - Compact timeline event card
 */

import type { TimelineEvent } from '@/types/timeline';
import { getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import { useCodexStore } from '@/stores/codexStore';

interface EventCardProps {
  event: TimelineEvent;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export default function EventCard({
  event,
  isSelected,
  onSelect,
  onDelete,
}: EventCardProps) {
  const { entities } = useCodexStore();

  // Get location name
  const location = event.location_id
    ? entities.find((e) => e.id === event.location_id)
    : null;

  // Get character names
  const characters = event.character_ids
    .map((id) => entities.find((e) => e.id === id)?.name)
    .filter(Boolean);

  const typeColor = getEventTypeColor(event.event_type);
  const typeIcon = getEventTypeIcon(event.event_type);

  return (
    <div
      className={`
        border border-slate-ui bg-white p-3 cursor-pointer transition-all
        hover:shadow-md
        ${isSelected ? 'ring-2 ring-bronze' : ''}
      `}
      style={{ borderRadius: '2px' }}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{typeIcon}</span>
          <span
            className="text-xs font-sans px-2 py-0.5 text-white"
            style={{ backgroundColor: typeColor, borderRadius: '2px' }}
          >
            {event.event_type}
          </span>
          {event.order_index !== null && (
            <span className="text-xs font-sans text-faded-ink">
              #{event.order_index + 1}
            </span>
          )}
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="text-faded-ink hover:text-redline text-sm"
          title="Delete event"
        >
          ×
        </button>
      </div>

      {/* Description */}
      <p className="text-sm font-serif text-midnight mb-2 line-clamp-2">
        {event.description}
      </p>

      {/* Metadata */}
      <div className="space-y-1">
        {event.timestamp && (
          <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
            <span>🕐</span>
            <span>{event.timestamp}</span>
          </div>
        )}

        {location && (
          <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
            <span>📍</span>
            <span>{location.name}</span>
          </div>
        )}

        {characters.length > 0 && (
          <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
            <span>👥</span>
            <span>{characters.slice(0, 3).join(', ')}</span>
            {characters.length > 3 && <span>+{characters.length - 3}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
