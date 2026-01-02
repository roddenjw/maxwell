/**
 * ConflictTracker - Visualize character conflicts and tensions
 * Tracks antagonistic relationships and story conflicts
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface ConflictTrackerProps {
  manuscriptId: string;
}

interface Conflict {
  id: string;
  character1: { id: string; name: string };
  character2: { id: string; name: string };
  intensity: number; // 1-5 scale based on event emotions and keywords
  events: {
    eventId: string;
    description: string;
    orderIndex: number;
    conflictKeywords: string[];
  }[];
  status: 'active' | 'resolved' | 'escalating';
}

export default function ConflictTracker({ manuscriptId }: ConflictTrackerProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedConflict, setSelectedConflict] = useState<string | null>(null);

  // Conflict keywords for detection
  const CONFLICT_KEYWORDS = [
    'fight', 'fighting', 'fought', 'battle', 'war', 'attack', 'attacked',
    'confront', 'confronted', 'argue', 'argued', 'disagree', 'disagreed',
    'anger', 'angry', 'furious', 'rage', 'hate', 'hated', 'enemy', 'enemies',
    'betray', 'betrayed', 'deceive', 'deceived', 'lie', 'lied', 'trick', 'tricked',
    'oppose', 'opposed', 'resist', 'resisted', 'challenge', 'challenged',
    'threaten', 'threatened', 'accuse', 'accused', 'blame', 'blamed'
  ];

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
      <div className="flex items-center justify-center p-8">
        <p className="text-faded-ink font-sans text-sm">Analyzing conflicts...</p>
      </div>
    );
  }

  // Detect conflicts from events
  const detectConflicts = (): Conflict[] => {
    const characters = entities.filter(e => e.type === 'CHARACTER');
    const conflicts: Map<string, Conflict> = new Map();

    // Find events where multiple characters appear and conflict keywords are present
    events.forEach(event => {
      if (event.character_ids.length < 2) return;

      const eventText = event.description.toLowerCase();
      const conflictKeywords = CONFLICT_KEYWORDS.filter(keyword =>
        eventText.includes(keyword)
      );

      if (conflictKeywords.length === 0) return;

      // Create conflicts for all character pairs in this event
      for (let i = 0; i < event.character_ids.length; i++) {
        for (let j = i + 1; j < event.character_ids.length; j++) {
          const char1 = characters.find(c => c.id === event.character_ids[i]);
          const char2 = characters.find(c => c.id === event.character_ids[j]);

          if (!char1 || !char2) continue;

          // Use sorted IDs as conflict key to avoid duplicates
          const conflictKey = [char1.id, char2.id].sort().join('-');

          if (!conflicts.has(conflictKey)) {
            conflicts.set(conflictKey, {
              id: conflictKey,
              character1: { id: char1.id, name: char1.name },
              character2: { id: char2.id, name: char2.name },
              intensity: 0,
              events: [],
              status: 'active',
            });
          }

          const conflict = conflicts.get(conflictKey)!;
          conflict.events.push({
            eventId: event.id,
            description: event.description,
            orderIndex: event.order_index,
            conflictKeywords,
          });

          // Increase intensity based on negative emotions and keywords
          const sentiment = event.event_metadata?.sentiment;
          const intensity = conflictKeywords.length + (sentiment !== undefined && sentiment < 0 ? 2 : 0);
          conflict.intensity = Math.max(conflict.intensity, Math.min(intensity, 5));
        }
      }
    });

    // Determine conflict status based on event progression
    conflicts.forEach(conflict => {
      if (conflict.events.length === 0) return;

      // Sort events by order
      conflict.events.sort((a, b) => a.orderIndex - b.orderIndex);

      // Check if conflict is escalating (more keywords in recent events)
      const recentEvents = conflict.events.slice(-2);
      const earlierEvents = conflict.events.slice(0, 2);

      const recentIntensity = recentEvents.reduce((sum, e) => sum + e.conflictKeywords.length, 0);
      const earlierIntensity = earlierEvents.reduce((sum, e) => sum + e.conflictKeywords.length, 0);

      if (recentIntensity > earlierIntensity * 1.5) {
        conflict.status = 'escalating';
      } else if (recentIntensity < earlierIntensity * 0.5) {
        conflict.status = 'resolved';
      }
    });

    return Array.from(conflicts.values()).sort((a, b) => b.intensity - a.intensity);
  };

  const conflicts = detectConflicts();

  if (conflicts.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-center">
        <div>
          <p className="text-midnight font-garamond font-semibold mb-2">
            No conflicts detected
          </p>
          <p className="text-sm text-faded-ink font-sans max-w-md">
            Conflicts are automatically detected from events containing conflict keywords
            (fight, argue, betray, etc.) between characters
          </p>
        </div>
      </div>
    );
  }

  const selectedConflictData = selectedConflict
    ? conflicts.find(c => c.id === selectedConflict)
    : null;

  const getIntensityColor = (intensity: number): string => {
    if (intensity >= 4) return 'text-red-600';
    if (intensity >= 3) return 'text-orange-500';
    if (intensity >= 2) return 'text-yellow-600';
    return 'text-blue-500';
  };

  const getIntensityLabel = (intensity: number): string => {
    if (intensity >= 4) return 'High Intensity';
    if (intensity >= 3) return 'Medium Intensity';
    if (intensity >= 2) return 'Low Intensity';
    return 'Minor Tension';
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'escalating': return '📈';
      case 'resolved': return '✅';
      default: return '⚡';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'escalating': return 'Escalating';
      case 'resolved': return 'Resolved';
      default: return 'Active';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h3 className="font-garamond text-lg text-midnight mb-2">
          Conflict Tracker
        </h3>
        <p className="text-sm font-sans text-faded-ink">
          Visualize antagonistic relationships and story conflicts
        </p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Conflict list */}
        <div className="w-80 border-r border-slate-ui bg-vellum overflow-y-auto">
          <div className="p-3 border-b border-slate-ui bg-white">
            <p className="text-xs font-sans text-faded-ink uppercase">
              Detected Conflicts ({conflicts.length})
            </p>
          </div>
          <div className="p-2">
            {conflicts.map(conflict => {
              const isSelected = selectedConflict === conflict.id;

              return (
                <button
                  key={conflict.id}
                  onClick={() => setSelectedConflict(isSelected ? null : conflict.id)}
                  className={`
                    w-full p-3 mb-2 text-left border transition-colors
                    ${isSelected
                      ? 'bg-bronze/10 border-bronze'
                      : 'bg-white border-slate-ui hover:border-bronze/50'
                    }
                  `}
                  style={{ borderRadius: '2px' }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{getStatusIcon(conflict.status)}</span>
                    <span className="text-xs font-sans text-faded-ink">
                      {getStatusLabel(conflict.status)}
                    </span>
                  </div>

                  <div className="mb-2">
                    <p className="font-serif text-sm text-midnight font-semibold">
                      {conflict.character1.name}
                    </p>
                    <p className="text-xs font-sans text-faded-ink my-1">versus</p>
                    <p className="font-serif text-sm text-midnight font-semibold">
                      {conflict.character2.name}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs font-sans">
                    <span className={getIntensityColor(conflict.intensity)}>
                      {getIntensityLabel(conflict.intensity)}
                    </span>
                    <span className="text-faded-ink">
                      {conflict.events.length} {conflict.events.length === 1 ? 'event' : 'events'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Conflict details */}
        <div className="flex-1 overflow-y-auto bg-vellum">
          {selectedConflictData ? (
            <div className="p-6">
              {/* Conflict header */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-3xl">{getStatusIcon(selectedConflictData.status)}</span>
                  <div>
                    <h3 className="font-garamond text-2xl text-midnight">
                      {selectedConflictData.character1.name} vs {selectedConflictData.character2.name}
                    </h3>
                    <p className="text-sm font-sans text-faded-ink mt-1">
                      {getStatusLabel(selectedConflictData.status)} • {getIntensityLabel(selectedConflictData.intensity)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Conflict summary */}
              <div className="mb-6 p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
                <h4 className="text-xs font-sans text-faded-ink uppercase mb-3">
                  Conflict Summary
                </h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-midnight">
                      {selectedConflictData.events.length}
                    </p>
                    <p className="text-xs font-sans text-faded-ink">Events</p>
                  </div>
                  <div>
                    <p className={`text-2xl font-bold ${getIntensityColor(selectedConflictData.intensity)}`}>
                      {selectedConflictData.intensity}/5
                    </p>
                    <p className="text-xs font-sans text-faded-ink">Intensity</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-midnight">
                      {Array.from(new Set(selectedConflictData.events.flatMap(e => e.conflictKeywords))).length}
                    </p>
                    <p className="text-xs font-sans text-faded-ink">Keywords</p>
                  </div>
                </div>
              </div>

              {/* Timeline of conflict events */}
              <div className="space-y-4">
                <h4 className="text-xs font-sans text-faded-ink uppercase">
                  Conflict Timeline
                </h4>
                {selectedConflictData.events.map((event, idx) => (
                  <div key={event.eventId} className="relative">
                    <div className="flex gap-3">
                      {/* Timeline line */}
                      <div className="flex flex-col items-center">
                        <div
                          className={`
                            w-8 h-8 rounded-full border-2 bg-white flex items-center justify-center text-xs font-sans font-semibold
                            ${event.conflictKeywords.length >= 3 ? 'border-red-500 text-red-500' : 'border-bronze text-bronze'}
                          `}
                        >
                          {idx + 1}
                        </div>
                        {idx < selectedConflictData.events.length - 1 && (
                          <div className="w-0.5 flex-1 bg-bronze/30 my-2"></div>
                        )}
                      </div>

                      {/* Event details */}
                      <div className="flex-1 pb-6">
                        <div className="p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
                          <p className="font-serif text-midnight text-sm leading-relaxed mb-3">
                            {event.description}
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {event.conflictKeywords.map((keyword, kidx) => (
                              <span
                                key={kidx}
                                className="px-2 py-1 bg-red-50 text-red-600 text-xs font-sans font-semibold"
                                style={{ borderRadius: '2px' }}
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md p-8">
                <span className="text-6xl mb-4 block">⚔️</span>
                <p className="font-garamond text-lg text-midnight mb-2">
                  Select a conflict to view details
                </p>
                <p className="text-sm font-sans text-faded-ink">
                  Track antagonistic relationships and story conflicts
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
