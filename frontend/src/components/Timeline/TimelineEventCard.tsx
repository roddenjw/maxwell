/**
 * TimelineEventCard - Event card with orchestrator features (issue badges, prerequisites)
 */

import type { TimelineEvent } from '@/types/timeline';
import { getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import { useCodexStore } from '@/stores/codexStore';
import { useTimelineStore } from '@/stores/timelineStore';

interface TimelineEventCardProps {
  event: TimelineEvent;
  isSelected: boolean;
  onSelect: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

export default function TimelineEventCard({
  event,
  isSelected,
  onSelect,
  onEdit,
  onDelete,
}: TimelineEventCardProps) {
  const { entities } = useCodexStore();
  const { inconsistencies, events } = useTimelineStore();

  // Get location name
  const location = event.location_id
    ? entities.find((e) => e.id === event.location_id)
    : null;

  // Get character names
  const characters = event.character_ids
    .map((id) => entities.find((e) => e.id === id)?.name)
    .filter(Boolean);

  // Get prerequisite events
  const prerequisites = event.prerequisite_ids
    .map((id) => events.find((e) => e.id === id))
    .filter(Boolean);

  // Get issues affecting this event
  const eventIssues = inconsistencies.filter(
    (inc) => inc.affected_event_ids.includes(event.id) && !inc.is_resolved
  );

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
        <div className="flex items-center gap-2 flex-wrap">
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
          {eventIssues.length > 0 && (
            <span
              className="text-xs font-sans px-2 py-0.5 bg-redline text-white"
              style={{ borderRadius: '2px' }}
              title={`${eventIssues.length} issue${eventIssues.length > 1 ? 's' : ''}`}
            >
              ⚠️ {eventIssues.length}
            </span>
          )}
          {event.narrative_importance > 5 && (
            <span
              className="text-xs font-sans px-2 py-0.5 bg-bronze/10 text-bronze border border-bronze"
              style={{ borderRadius: '2px' }}
              title={`Narrative importance: ${event.narrative_importance}/10`}
            >
              ⭐
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {onEdit && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              className="text-bronze hover:text-bronze/80 text-sm px-1"
              title="Edit event"
            >
              ✎
            </button>
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="text-faded-ink hover:text-redline text-sm px-1"
              title="Delete event"
            >
              ×
            </button>
          )}
        </div>
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

        {prerequisites.length > 0 && (
          <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
            <span>🔗</span>
            <span>{prerequisites.length} prerequisite{prerequisites.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
}
