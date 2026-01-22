/**
 * CharacterLocationTracker - Track character movements through locations
 * Shows a visual map of where each character is at different timeline events
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';
import analytics from '@/lib/analytics';

interface CharacterLocationTrackerProps {
  manuscriptId: string;
}

interface CharacterJourney {
  characterId: string;
  characterName: string;
  locations: {
    eventId: string;
    eventDescription: string;
    locationId: string | null;
    locationName: string;
    orderIndex: number;
    timestamp: string | null;
  }[];
}

export default function CharacterLocationTracker({ manuscriptId }: CharacterLocationTrackerProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="h-full flex flex-col">
        {/* Header skeleton */}
        <div className="p-4 border-b border-slate-ui bg-white">
          <div className="h-6 w-48 bg-slate-ui/30 animate-pulse rounded mb-2" />
          <div className="h-4 w-64 bg-slate-ui/20 animate-pulse rounded" />
        </div>
        <div className="flex-1 flex">
          {/* Character list skeleton */}
          <div className="w-64 border-r border-slate-ui bg-vellum p-3">
            <div className="h-4 w-24 bg-slate-ui/30 animate-pulse rounded mb-4" />
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-3 mb-2 bg-white border border-slate-ui rounded-sm">
                <div className="h-4 w-24 bg-slate-ui/30 animate-pulse rounded mb-2" />
                <div className="h-3 w-16 bg-slate-ui/20 animate-pulse rounded" />
              </div>
            ))}
          </div>
          {/* Content skeleton */}
          <div className="flex-1 p-8 flex items-center justify-center">
            <div className="text-center">
              <div className="h-16 w-16 bg-slate-ui/20 animate-pulse rounded-full mx-auto mb-4" />
              <div className="h-5 w-48 bg-slate-ui/30 animate-pulse rounded mx-auto" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Get characters and locations
  const characters = entities.filter(e => e.type === 'CHARACTER');
  const locations = entities.filter(e => e.type === 'LOCATION');

  // Build character journeys
  const buildCharacterJourneys = (): CharacterJourney[] => {
    const journeys: CharacterJourney[] = [];

    characters.forEach(character => {
      // Find all events this character appears in
      const characterEvents = events
        .filter(event => event.character_ids.includes(character.id))
        .sort((a, b) => a.order_index - b.order_index);

      if (characterEvents.length === 0) return;

      const journey: CharacterJourney = {
        characterId: character.id,
        characterName: character.name,
        locations: characterEvents.map(event => {
          const location = locations.find(l => l.id === event.location_id);
          return {
            eventId: event.id,
            eventDescription: event.description,
            locationId: event.location_id,
            locationName: location?.name || event.event_metadata?.location_name || 'Unknown Location',
            orderIndex: event.order_index,
            timestamp: event.timestamp,
          };
        }),
      };

      journeys.push(journey);
    });

    return journeys;
  };

  const journeys = buildCharacterJourneys();

  if (journeys.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-slate-ui bg-white">
          <h3 className="font-garamond text-lg text-midnight mb-2">
            Character Location Tracker
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div className="max-w-md">
            <span className="text-6xl mb-4 block">🗺️</span>
            <p className="text-midnight font-garamond text-xl font-semibold mb-3">
              No character journeys yet
            </p>
            <p className="text-sm text-faded-ink font-sans mb-6">
              Character journeys appear when you add characters to timeline events with locations.
            </p>
            <div className="text-left bg-white border border-slate-ui p-4 rounded-sm">
              <p className="text-xs font-sans text-faded-ink uppercase mb-2">How to get started:</p>
              <ol className="text-sm font-sans text-midnight space-y-2">
                <li className="flex gap-2">
                  <span className="text-bronze font-semibold">1.</span>
                  <span>Create characters in the Codex</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-bronze font-semibold">2.</span>
                  <span>Create locations in the Codex</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-bronze font-semibold">3.</span>
                  <span>Add timeline events with characters and locations</span>
                </li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Get selected character journey
  const selectedJourney = selectedCharacter
    ? journeys.find(j => j.characterId === selectedCharacter)
    : null;

  // Get all unique locations for the selected character
  const getCharacterLocations = (journey: CharacterJourney) => {
    const locationCounts = new Map<string, number>();
    journey.locations.forEach(loc => {
      const key = loc.locationName;
      locationCounts.set(key, (locationCounts.get(key) || 0) + 1);
    });
    return Array.from(locationCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  };

  // Detect location changes (potential movement events)
  const getLocationChanges = (journey: CharacterJourney) => {
    const changes: { from: string; to: string; eventIndex: number }[] = [];
    for (let i = 1; i < journey.locations.length; i++) {
      const prev = journey.locations[i - 1];
      const curr = journey.locations[i];
      if (prev.locationName !== curr.locationName) {
        changes.push({
          from: prev.locationName,
          to: curr.locationName,
          eventIndex: i,
        });
      }
    }
    return changes;
  };

  // Calculate journey statistics
  const getJourneyStats = (journey: CharacterJourney) => {
    const uniqueLocations = new Set(journey.locations.map(l => l.locationName));
    const locationChanges = getLocationChanges(journey);
    const mostVisitedLocation = getCharacterLocations(journey).sort((a, b) => b.count - a.count)[0];

    // Calculate "time" span (using order_index as proxy for time)
    const firstEvent = journey.locations[0];
    const lastEvent = journey.locations[journey.locations.length - 1];
    const eventSpan = lastEvent.orderIndex - firstEvent.orderIndex;

    return {
      totalEvents: journey.locations.length,
      uniqueLocations: uniqueLocations.size,
      totalMoves: locationChanges.length,
      mostVisited: mostVisitedLocation?.name || 'N/A',
      mostVisitedCount: mostVisitedLocation?.count || 0,
      eventSpan,
    };
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h3 className="font-garamond text-lg text-midnight mb-2">
          Character Location Tracker
        </h3>
        <p className="text-sm font-sans text-faded-ink">
          Track character movements through your story's locations
        </p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Character list */}
        <div className="w-64 border-r border-slate-ui bg-vellum overflow-y-auto">
          <div className="p-3 border-b border-slate-ui bg-white">
            <p className="text-xs font-sans text-faded-ink uppercase">
              Characters ({journeys.length})
            </p>
          </div>
          <div className="p-2">
            {journeys.map(journey => {
              const isSelected = selectedCharacter === journey.characterId;
              const locationChanges = getLocationChanges(journey);

              return (
                <button
                  key={journey.characterId}
                  onClick={() => {
                    setSelectedCharacter(isSelected ? null : journey.characterId);
                    if (!isSelected) {
                      analytics.timelineOpened(manuscriptId); // Track feature usage
                    }
                  }}
                  className={`
                    w-full p-3 mb-2 text-left border transition-colors
                    ${isSelected
                      ? 'bg-bronze/10 border-bronze'
                      : 'bg-white border-slate-ui hover:border-bronze/50'
                    }
                  `}
                  style={{ borderRadius: '2px' }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-serif text-sm text-midnight font-semibold">
                        {journey.characterName}
                      </p>
                      <p className="text-xs font-sans text-faded-ink mt-1">
                        {journey.locations.length} {journey.locations.length === 1 ? 'event' : 'events'}
                      </p>
                    </div>
                    {locationChanges.length > 0 && (
                      <span className="text-xs font-sans text-bronze font-semibold">
                        {locationChanges.length} {locationChanges.length === 1 ? 'move' : 'moves'}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Journey visualization */}
        <div className="flex-1 overflow-y-auto bg-vellum">
          {selectedJourney ? (
            <div className="p-6">
              {/* Character header */}
              <div className="mb-6">
                <h3 className="font-garamond text-2xl text-midnight mb-2">
                  {selectedJourney.characterName}'s Journey
                </h3>
                <div className="flex gap-4 text-sm font-sans text-faded-ink">
                  <span>
                    {selectedJourney.locations.length} {selectedJourney.locations.length === 1 ? 'event' : 'events'}
                  </span>
                  <span>•</span>
                  <span>
                    {getCharacterLocations(selectedJourney).length}{' '}
                    {getCharacterLocations(selectedJourney).length === 1 ? 'location' : 'locations'} visited
                  </span>
                </div>
              </div>

              {/* Journey Statistics */}
              {(() => {
                const stats = getJourneyStats(selectedJourney);
                return (
                  <div className="mb-6 p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
                    <h4 className="text-xs font-sans text-faded-ink uppercase mb-3">
                      Journey Statistics
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-garamond text-bronze font-semibold">{stats.totalEvents}</p>
                        <p className="text-xs font-sans text-faded-ink">Events</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-garamond text-bronze font-semibold">{stats.uniqueLocations}</p>
                        <p className="text-xs font-sans text-faded-ink">Locations</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-garamond text-bronze font-semibold">{stats.totalMoves}</p>
                        <p className="text-xs font-sans text-faded-ink">Moves</p>
                      </div>
                    </div>
                    {stats.mostVisited && (
                      <div className="mt-3 pt-3 border-t border-slate-ui">
                        <p className="text-xs font-sans text-faded-ink">
                          Most visited: <span className="text-midnight font-semibold">{stats.mostVisited}</span> ({stats.mostVisitedCount}×)
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Location summary */}
              <div className="mb-6 p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
                <h4 className="text-xs font-sans text-faded-ink uppercase mb-3">
                  Locations Visited
                </h4>
                <div className="flex flex-wrap gap-2">
                  {getCharacterLocations(selectedJourney).map((loc, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-1 bg-bronze/10 border border-bronze/30"
                      style={{ borderRadius: '2px' }}
                    >
                      <span className="text-sm font-serif text-midnight">{loc.name}</span>
                      <span className="text-xs font-sans text-bronze ml-2">×{loc.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Timeline of events */}
              <div className="space-y-4">
                <h4 className="text-xs font-sans text-faded-ink uppercase">
                  Event Timeline
                </h4>
                {selectedJourney.locations.map((loc, idx) => {
                  const isLocationChange = idx > 0 && selectedJourney.locations[idx - 1].locationName !== loc.locationName;

                  return (
                    <div key={loc.eventId} className="relative">
                      {/* Movement indicator */}
                      {isLocationChange && (
                        <div className="flex items-center gap-2 mb-2 ml-8">
                          <div className="h-px flex-1 bg-bronze/30"></div>
                          <span className="text-xs font-sans text-bronze font-semibold">
                            ↓ Moved to {loc.locationName}
                          </span>
                          <div className="h-px flex-1 bg-bronze/30"></div>
                        </div>
                      )}

                      {/* Event card */}
                      <div className="flex gap-3">
                        {/* Timeline line */}
                        <div className="flex flex-col items-center">
                          <div
                            className="w-8 h-8 rounded-full border-2 border-bronze bg-white flex items-center justify-center text-xs font-sans font-semibold text-bronze"
                          >
                            {idx + 1}
                          </div>
                          {idx < selectedJourney.locations.length - 1 && (
                            <div className="w-0.5 flex-1 bg-bronze/30 my-2"></div>
                          )}
                        </div>

                        {/* Event details */}
                        <div className="flex-1 pb-6">
                          <div className="p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <p className="font-serif text-midnight text-sm leading-relaxed">
                                  {loc.eventDescription}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4 text-xs font-sans text-faded-ink">
                              <span className="flex items-center gap-1">
                                <span>📍</span>
                                <span>{loc.locationName}</span>
                              </span>
                              {loc.timestamp && (
                                <span className="flex items-center gap-1">
                                  <span>⏰</span>
                                  <span>{loc.timestamp}</span>
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md p-8">
                <span className="text-6xl mb-4 block">🗺️</span>
                <p className="font-garamond text-lg text-midnight mb-2">
                  Select a character to track their journey
                </p>
                <p className="text-sm font-sans text-faded-ink">
                  See where they've been and how they move through your story
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
