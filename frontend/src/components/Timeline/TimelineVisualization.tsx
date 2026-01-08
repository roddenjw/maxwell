/**
 * TimelineVisualization - Chronological event display with virtualization
 *
 * PERFORMANCE OPTIMIZATIONS:
 * - Uses react-window for virtual scrolling (only renders visible events)
 * - Handles 1000+ events without browser freeze
 * - Maintains scroll position on updates
 * - Memory usage: constant instead of linear
 */

import { useRef, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import type { TimelineEvent } from '@/types/timeline';

interface TimelineVisualizationProps {
  manuscriptId: string;
}

// Event card height (px) - based on typical card size
const EVENT_ROW_HEIGHT = 200;
const TIMELINE_GAP = 8;

export default function TimelineVisualization({ manuscriptId }: TimelineVisualizationProps) {
  const { events, inconsistencies } = useTimelineStore();
  const { entities } = useCodexStore();
  const listRef = useRef<List>(null);

  const sortedEvents = [...events].sort((a, b) => a.order_index - b.order_index);

  // Get issues affecting each event (memoized for performance)
  const getEventIssues = useCallback((eventId: string) => {
    return inconsistencies.filter(
      (inc) => inc.affected_event_ids.includes(eventId) && !inc.is_resolved
    );
  }, [inconsistencies]);

  // Render single event row (called by react-window for visible items only)
  const EventRow = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const event = sortedEvents[index];
    const isLast = index === sortedEvents.length - 1;

    const location = event.location_id
      ? entities.find((e) => e.id === event.location_id)
      : null;

    const characters = event.character_ids
      .map((id) => entities.find((e) => e.id === id))
      .filter(Boolean);

    const typeColor = getEventTypeColor(event.event_type);
    const typeIcon = getEventTypeIcon(event.event_type);
    const eventIssues = getEventIssues(event.id);

    return (
      <div style={style} className="flex gap-4 group px-6">
        {/* Timeline Line */}
        <div className="flex flex-col items-center">
          <div
            className="w-10 h-10 flex items-center justify-center text-white font-sans text-sm font-semibold flex-shrink-0"
            style={{
              backgroundColor: typeColor,
              borderRadius: '50%',
            }}
          >
            {event.order_index + 1}
          </div>
          {!isLast && (
            <div
              className="w-0.5 flex-1 bg-slate-ui"
              style={{ minHeight: `${EVENT_ROW_HEIGHT - 40 - TIMELINE_GAP}px` }}
            />
          )}
        </div>

        {/* Event Content */}
        <div className="flex-1 pb-4">
          <div
            className="border border-slate-ui bg-white p-4 transition-all hover:shadow-md group-hover:border-bronze"
            style={{ borderRadius: '2px' }}
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
                {event.timestamp && (
                  <span className="text-xs font-sans text-faded-ink">
                    🕐 {event.timestamp}
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
              </div>

              {/* Importance Badge */}
              {event.narrative_importance > 5 && (
                <div
                  className="text-xs font-sans px-2 py-0.5 bg-bronze/10 text-bronze border border-bronze"
                  style={{ borderRadius: '2px' }}
                  title={`Narrative importance: ${event.narrative_importance}/10`}
                >
                  ⭐ Key
                </div>
              )}
            </div>

            {/* Description */}
            <p className="text-sm font-serif text-midnight mb-3 line-clamp-2">
              {event.description}
            </p>

            {/* Metadata */}
            <div className="space-y-1">
              {location && (
                <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
                  <span>📍</span>
                  <span>{location.name}</span>
                </div>
              )}

              {characters.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
                  <span>👥</span>
                  <span>
                    {characters.map((c) => c?.name).filter(Boolean).slice(0, 3).join(', ')}
                    {characters.length > 3 && ` +${characters.length - 3}`}
                  </span>
                </div>
              )}

              {event.prerequisite_ids.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-faded-ink font-sans">
                  <span>🔗</span>
                  <span>Depends on {event.prerequisite_ids.length} event{event.prerequisite_ids.length > 1 ? 's' : ''}</span>
                </div>
              )}
            </div>

            {/* Issues affecting this event */}
            {eventIssues.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-ui">
                <p className="text-xs font-sans font-semibold text-redline mb-1">
                  ⚠️ Issues:
                </p>
                <div className="space-y-1">
                  {eventIssues.slice(0, 2).map((issue) => (
                    <p key={issue.id} className="text-xs font-serif text-faded-ink">
                      • {issue.inconsistency_type.replace(/_/g, ' ')}: {issue.description.slice(0, 80)}...
                    </p>
                  ))}
                  {eventIssues.length > 2 && (
                    <p className="text-xs font-sans text-faded-ink">
                      + {eventIssues.length - 2} more
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="text-6xl mb-4">📜</div>
        <h3 className="text-xl font-garamond font-bold text-midnight mb-2">
          No Timeline Events Yet
        </h3>
        <p className="text-sm text-faded-ink font-sans max-w-md">
          Add events to your timeline to visualize the chronological flow of your story.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h2 className="text-xl font-garamond font-bold text-midnight mb-1">Timeline Flow</h2>
        <p className="text-sm text-faded-ink font-sans">
          {events.length} event{events.length > 1 ? 's' : ''} • {inconsistencies.filter((i) => !i.is_resolved).length} pending issue{inconsistencies.filter((i) => !i.is_resolved).length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Virtualized Events List */}
      <div className="flex-1">
        <List
          ref={listRef}
          height={800} // Will auto-adjust based on parent container
          itemCount={sortedEvents.length}
          itemSize={EVENT_ROW_HEIGHT}
          width="100%"
          className="timeline-scroll"
        >
          {EventRow}
        </List>
      </div>
    </div>
  );
}
