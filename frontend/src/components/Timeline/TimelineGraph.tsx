/**
 * TimelineGraph - Visual timeline with events displayed chronologically
 */

import { useState, useEffect } from 'react';
import { getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';

interface TimelineGraphProps {
  manuscriptId: string;
}

export default function TimelineGraph({ manuscriptId }: TimelineGraphProps) {
  const { events, setEvents, setSelectedEvent } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEvents();
  }, [manuscriptId]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await timelineApi.listEvents(manuscriptId);
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading timeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-redline/10 border-l-4 border-redline p-3 text-sm font-sans text-redline">
          {error}
        </div>
        <button
          onClick={loadEvents}
          className="mt-2 text-sm font-sans text-bronze hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="text-4xl mb-3">📅</div>
        <p className="text-midnight font-garamond font-semibold mb-2">
          No events in timeline
        </p>
        <p className="text-sm text-faded-ink font-sans max-w-xs">
          Create events or use "Extract Timeline" to analyze your manuscript
        </p>
      </div>
    );
  }

  // Sort events by order
  const sortedEvents = [...events].sort((a, b) => a.order_index - b.order_index);

  return (
    <div className="h-full overflow-auto p-6">
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-ui"></div>

        {/* Events */}
        <div className="space-y-6">
          {sortedEvents.map((event, index) => {
            const typeColor = getEventTypeColor(event.event_type);
            const typeIcon = getEventTypeIcon(event.event_type);

            // Get location name
            const location = event.location_id
              ? entities.find((e) => e.id === event.location_id)
              : null;

            // Get character names
            const characters = event.character_ids
              .map((id) => entities.find((e) => e.id === id)?.name)
              .filter(Boolean);

            return (
              <div key={event.id} className="relative pl-16">
                {/* Timeline dot */}
                <div
                  className="absolute left-4 w-5 h-5 rounded-full border-4 border-white shadow-md flex items-center justify-center"
                  style={{ backgroundColor: typeColor, top: '8px' }}
                >
                  <span className="text-xs">{index + 1}</span>
                </div>

                {/* Event card */}
                <div
                  className="bg-white border border-slate-ui p-4 cursor-pointer hover:shadow-md transition-shadow"
                  style={{ borderRadius: '2px' }}
                  onClick={() => setSelectedEvent(event.id)}
                >
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{typeIcon}</span>
                    <span
                      className="text-xs font-sans px-2 py-0.5 text-white"
                      style={{ backgroundColor: typeColor, borderRadius: '2px' }}
                    >
                      {event.event_type}
                    </span>
                    {event.timestamp && (
                      <span className="text-xs font-sans text-faded-ink">
                        {event.timestamp}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-sm font-serif text-midnight mb-2">
                    {event.description}
                  </p>

                  {/* Metadata */}
                  <div className="flex flex-wrap gap-3 text-xs text-faded-ink font-sans">
                    {location && (
                      <span className="flex items-center gap-1">
                        <span>📍</span>
                        {location.name}
                      </span>
                    )}
                    {characters.length > 0 && (
                      <span className="flex items-center gap-1">
                        <span>👥</span>
                        {characters.slice(0, 2).join(', ')}
                        {characters.length > 2 && ` +${characters.length - 2}`}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
