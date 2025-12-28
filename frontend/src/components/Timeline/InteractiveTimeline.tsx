/**
 * InteractiveTimeline - Visual timeline with dots for events/characters
 * Features:
 * - Horizontal scrollable timeline with visual dots
 * - Hover to see character locations and event details
 * - Filter by characters and locations
 * - Archaic scroll aesthetic
 */

import { useState, useEffect } from 'react';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import type { TimelineEvent } from '@/types/timeline';

interface InteractiveTimelineProps {
  manuscriptId: string;
}

export default function InteractiveTimeline({ manuscriptId }: InteractiveTimelineProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [hoveredEvent, setHoveredEvent] = useState<TimelineEvent | null>(null);
  const [selectedCharacters, setSelectedCharacters] = useState<Set<string>>(new Set());
  const [selectedLocations, setSelectedLocations] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadEvents();
  }, [manuscriptId]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await timelineApi.listEvents(manuscriptId);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get all characters and locations from events
  const allCharacters = Array.from(
    new Set(events.flatMap(e => e.character_ids))
  ).map(charId => entities.find(e => e.id === charId)).filter(Boolean);

  const allLocations = Array.from(
    new Set(events.map(e => e.location_id).filter(Boolean))
  ).map(locId => entities.find(e => e.id === locId)).filter(Boolean);

  // Filter events based on selected characters/locations
  const filteredEvents = events.filter(event => {
    if (selectedCharacters.size > 0) {
      const hasSelectedChar = event.character_ids.some(charId =>
        selectedCharacters.has(charId)
      );
      if (!hasSelectedChar) return false;
    }

    if (selectedLocations.size > 0) {
      if (!event.location_id || !selectedLocations.has(event.location_id)) {
        return false;
      }
    }

    return true;
  });

  const sortedEvents = [...filteredEvents].sort((a, b) => a.order_index - b.order_index);

  const toggleCharacterFilter = (charId: string) => {
    const newSet = new Set(selectedCharacters);
    if (newSet.has(charId)) {
      newSet.delete(charId);
    } else {
      newSet.add(charId);
    }
    setSelectedCharacters(newSet);
  };

  const toggleLocationFilter = (locId: string) => {
    const newSet = new Set(selectedLocations);
    if (newSet.has(locId)) {
      newSet.delete(locId);
    } else {
      newSet.add(locId);
    }
    setSelectedLocations(newSet);
  };

  const clearFilters = () => {
    setSelectedCharacters(new Set());
    setSelectedLocations(new Set());
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm mt-3">Loading timeline...</p>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="text-6xl mb-4">📜</div>
        <p className="text-midnight font-garamond font-semibold text-lg mb-2">
          The Timeline Awaits
        </p>
        <p className="text-sm text-faded-ink font-sans max-w-md">
          Extract your manuscript's timeline to see events, characters, and locations mapped chronologically
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#f5f1e8]">
      {/* Scroll-styled header */}
      <div className="relative border-b-4 border-double border-bronze/40 bg-gradient-to-b from-[#e8dcc8] to-[#f5f1e8] p-6">
        <div className="absolute top-2 left-1/2 -translate-x-1/2 w-24 h-3 bg-bronze/20 rounded-full shadow-inner"></div>

        <h2 className="text-2xl font-garamond font-bold text-center text-midnight mb-4 pt-4">
          Chronicle of Events
        </h2>

        {/* Filter controls */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 bg-bronze/10 border-2 border-bronze/30 text-bronze font-sans text-sm hover:bg-bronze/20 transition-colors rounded-sm flex items-center gap-2"
          >
            <span>🔍</span>
            Filter
            {(selectedCharacters.size > 0 || selectedLocations.size > 0) && (
              <span className="bg-bronze text-white px-2 py-0.5 rounded-full text-xs">
                {selectedCharacters.size + selectedLocations.size}
              </span>
            )}
          </button>

          {(selectedCharacters.size > 0 || selectedLocations.size > 0) && (
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-faded-ink font-sans text-sm hover:text-midnight transition-colors"
            >
              Clear filters
            </button>
          )}

          <div className="text-sm font-sans text-faded-ink">
            {sortedEvents.length} of {events.length} events
          </div>
        </div>

        {/* Filter dropdowns */}
        {showFilters && (
          <div className="mt-4 p-4 bg-white/80 border-2 border-bronze/30 rounded-sm">
            <div className="grid grid-cols-2 gap-4">
              {/* Character filters */}
              <div>
                <h3 className="text-xs font-sans uppercase text-faded-ink mb-2">Characters</h3>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {allCharacters.map(char => (
                    <label key={char!.id} className="flex items-center gap-2 cursor-pointer hover:bg-bronze/5 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={selectedCharacters.has(char!.id)}
                        onChange={() => toggleCharacterFilter(char!.id)}
                        className="rounded border-bronze/30"
                      />
                      <span className="text-sm font-serif text-midnight">{char!.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Location filters */}
              <div>
                <h3 className="text-xs font-sans uppercase text-faded-ink mb-2">Locations</h3>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {allLocations.map(loc => (
                    <label key={loc!.id} className="flex items-center gap-2 cursor-pointer hover:bg-bronze/5 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={selectedLocations.has(loc!.id)}
                        onChange={() => toggleLocationFilter(loc!.id)}
                        className="rounded border-bronze/30"
                      />
                      <span className="text-sm font-serif text-midnight">{loc!.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Horizontal scrollable timeline */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden relative bg-[#f5f1e8] p-8">
        {/* Parchment edge decoration at top */}
        <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-[#d4c4a8]/40 to-transparent pointer-events-none"></div>

        <div className="relative h-full min-w-max flex items-center px-8">
          {/* Timeline line */}
          <div className="absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-bronze/40 via-bronze/60 to-bronze/40 shadow-sm"></div>

          {/* Event dots */}
          <div className="flex items-center gap-16 relative z-10">
            {sortedEvents.map((event, index) => {
              const location = event.location_id
                ? entities.find(e => e.id === event.location_id)
                : null;

              const characters = event.character_ids
                .map(id => entities.find(e => e.id === id))
                .filter(Boolean);

              const isHovered = hoveredEvent?.id === event.id;

              return (
                <div
                  key={event.id}
                  className="relative flex flex-col items-center"
                  onMouseEnter={() => setHoveredEvent(event)}
                  onMouseLeave={() => setHoveredEvent(null)}
                >
                  {/* Event dot */}
                  <div
                    className={`
                      w-6 h-6 rounded-full border-4 border-white shadow-lg cursor-pointer
                      transition-all duration-200
                      ${isHovered ? 'scale-150 shadow-2xl' : 'hover:scale-125'}
                    `}
                    style={{
                      backgroundColor: '#a47551',
                      boxShadow: isHovered
                        ? '0 0 20px rgba(164, 117, 81, 0.6), 0 4px 6px rgba(0,0,0,0.1)'
                        : '0 2px 4px rgba(0,0,0,0.1)'
                    }}
                  >
                    {/* Event number */}
                    <div className="absolute inset-0 flex items-center justify-center text-white text-xs font-bold">
                      {index + 1}
                    </div>
                  </div>

                  {/* Character indicators (small dots above) */}
                  {characters.length > 0 && (
                    <div className="absolute -top-8 flex gap-1">
                      {characters.slice(0, 3).map((char) => (
                        <div
                          key={char!.id}
                          className="w-3 h-3 rounded-full bg-midnight border-2 border-white shadow-sm"
                          title={char!.name}
                        />
                      ))}
                      {characters.length > 3 && (
                        <div className="w-3 h-3 rounded-full bg-faded-ink border-2 border-white shadow-sm flex items-center justify-center">
                          <span className="text-white text-[8px]">+</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Hover tooltip */}
                  {isHovered && (
                    <div className="absolute bottom-full mb-8 w-80 bg-white/95 backdrop-blur-sm border-2 border-bronze/40 rounded-sm shadow-2xl p-4 z-50">
                      {/* Scroll-styled top edge */}
                      <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-16 h-2 bg-bronze/30 rounded-full"></div>

                      <div className="space-y-3">
                        {/* Timestamp */}
                        {event.timestamp && (
                          <div className="text-xs font-sans text-faded-ink">
                            🕐 {event.timestamp}
                          </div>
                        )}

                        {/* Description */}
                        <p className="font-serif text-sm text-midnight leading-relaxed">
                          {event.description}
                        </p>

                        {/* Event type */}
                        <div className="flex items-center gap-2">
                          <span
                            className="px-2 py-1 bg-bronze/20 text-bronze text-xs font-sans rounded-sm"
                          >
                            {event.event_type}
                          </span>
                        </div>

                        {/* Location */}
                        {location && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-bronze">📍</span>
                            <span className="font-serif text-midnight">{location.name}</span>
                          </div>
                        )}

                        {/* Characters present */}
                        {characters.length > 0 && (
                          <div>
                            <div className="text-xs font-sans text-faded-ink uppercase mb-1">
                              Characters Present:
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {characters.map(char => (
                                <span
                                  key={char!.id}
                                  className="px-2 py-1 bg-midnight/10 text-midnight text-xs font-serif rounded-sm"
                                >
                                  {char!.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Scroll-styled bottom edge */}
                      <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-16 h-2 bg-bronze/30 rounded-full"></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Parchment edge decoration at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-[#d4c4a8]/40 to-transparent pointer-events-none"></div>
      </div>

      {/* Scroll footer decoration */}
      <div className="border-t-4 border-double border-bronze/40 bg-gradient-to-t from-[#e8dcc8] to-[#f5f1e8] p-4">
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-24 h-3 bg-bronze/20 rounded-full shadow-inner"></div>
      </div>
    </div>
  );
}
