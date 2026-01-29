/**
 * CharacterJourneySwimlane - Horizontal swimlane visualization of character journeys
 * Shows characters as parallel lanes with events as nodes and movements as connecting lines
 */

import { useState, useEffect, useMemo } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface CharacterJourneySwimlaneProps {
  manuscriptId: string;
}

interface CharacterLane {
  characterId: string;
  characterName: string;
  events: {
    eventId: string;
    description: string;
    locationId: string | null;
    locationName: string;
    orderIndex: number;
    timestamp: string | null;
  }[];
  color: string;
}

// Color palette for character lanes
const LANE_COLORS = [
  '#9a6f47', // bronze
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

export default function CharacterJourneySwimlane({ manuscriptId }: CharacterJourneySwimlaneProps) {
  const { events } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<string | null>(null);

  // Load events if needed
  useEffect(() => {
    const loadEvents = async () => {
      if (events.length === 0) {
        setLoading(true);
        try {
          const data = await timelineApi.listEvents(manuscriptId);
          useTimelineStore.getState().setEvents(data);
        } catch (err) {
          console.error('Failed to load events:', err);
        } finally {
          setLoading(false);
        }
      }
    };
    loadEvents();
  }, [manuscriptId, events.length]);

  // Build character lanes from events
  const characterLanes = useMemo<CharacterLane[]>(() => {
    const characters = entities.filter(e => e.type === 'CHARACTER');
    const locations = entities.filter(e => e.type === 'LOCATION');
    const locationMap = new Map(locations.map(l => [l.id, l.name]));

    const lanes: CharacterLane[] = [];

    characters.forEach((character, index) => {
      const characterEvents = events
        .filter(event => event.character_ids.includes(character.id))
        .sort((a, b) => a.order_index - b.order_index)
        .map(event => ({
          eventId: event.id,
          description: event.description,
          locationId: event.location_id,
          locationName: event.location_id
            ? locationMap.get(event.location_id) || 'Unknown'
            : 'Unknown',
          orderIndex: event.order_index,
          timestamp: event.timestamp,
        }));

      if (characterEvents.length > 0) {
        lanes.push({
          characterId: character.id,
          characterName: character.name,
          events: characterEvents,
          color: LANE_COLORS[index % LANE_COLORS.length],
        });
      }
    });

    return lanes;
  }, [events, entities]);

  // Calculate visualization dimensions
  const maxOrderIndex = useMemo(() => {
    if (events.length === 0) return 0;
    return Math.max(...events.map(e => e.order_index));
  }, [events]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 border-2 border-bronze border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-faded-ink font-sans">Loading swimlane data...</p>
        </div>
      </div>
    );
  }

  if (characterLanes.length === 0) {
    const hasCharacters = entities.filter(e => e.type === 'CHARACTER').length > 0;
    const hasEvents = events.length > 0;

    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center max-w-lg">
          <span className="text-6xl mb-4 block">🏊</span>
          <p className="text-midnight font-garamond text-xl font-semibold mb-3">
            No character journeys to display
          </p>

          {!hasCharacters ? (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                You need characters in your Codex first.
              </p>
              <p className="text-xs text-faded-ink font-sans bg-vellum p-3 rounded">
                <strong>Tip:</strong> Go to the Codex panel and create CHARACTER entities for your story's characters.
              </p>
            </div>
          ) : !hasEvents ? (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                You need timeline events to track character journeys.
              </p>
              <p className="text-xs text-faded-ink font-sans bg-vellum p-3 rounded">
                <strong>Tip:</strong> Use the "Events" tab to create events manually or "Extract Timeline" to analyze your manuscript.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                Your events exist but don't have characters linked to them.
              </p>
              <p className="text-xs text-faded-ink font-sans bg-vellum p-3 rounded">
                <strong>How to fix:</strong> Go to the "Events" tab, click on an event to edit it,
                and check the characters who appear in that event. Once characters are linked to events,
                their journeys will appear here as swimlanes.
              </p>
              <p className="text-xs text-faded-ink font-sans mt-2">
                You have <strong>{entities.filter(e => e.type === 'CHARACTER').length}</strong> characters
                and <strong>{events.length}</strong> events ready to connect.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  const laneHeight = 80;
  const nodeRadius = 12;
  const padding = 60;
  const svgWidth = Math.max(800, (maxOrderIndex + 1) * 60 + padding * 2);
  const svgHeight = characterLanes.length * laneHeight + padding * 2;

  // Get X position for an order index
  const getX = (orderIndex: number) => {
    if (maxOrderIndex === 0) return svgWidth / 2;
    return padding + (orderIndex / maxOrderIndex) * (svgWidth - padding * 2);
  };

  // Get Y position for a lane
  const getY = (laneIndex: number) => padding + laneIndex * laneHeight + laneHeight / 2;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h3 className="font-garamond text-lg text-midnight mb-2">
          Character Journey Swimlanes
        </h3>
        <p className="text-sm font-sans text-faded-ink">
          Horizontal view of character movements through your story
        </p>
      </div>

      {/* Legend */}
      <div className="p-3 border-b border-slate-ui bg-vellum flex flex-wrap gap-3">
        {characterLanes.map(lane => (
          <button
            key={lane.characterId}
            onClick={() => setSelectedCharacter(
              selectedCharacter === lane.characterId ? null : lane.characterId
            )}
            className={`
              flex items-center gap-2 px-2 py-1 text-xs font-sans transition-all
              ${selectedCharacter === lane.characterId
                ? 'ring-2 ring-bronze'
                : selectedCharacter
                  ? 'opacity-50'
                  : ''
              }
            `}
            style={{ borderRadius: '2px' }}
          >
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: lane.color }}
            />
            <span className="text-midnight">{lane.characterName}</span>
            <span className="text-faded-ink">({lane.events.length})</span>
          </button>
        ))}
      </div>

      {/* Swimlane Visualization */}
      <div className="flex-1 overflow-auto bg-white">
        <svg width={svgWidth} height={svgHeight} className="min-w-full">
          {/* Lane backgrounds */}
          {characterLanes.map((lane, laneIndex) => {
            const isSelected = selectedCharacter === lane.characterId;
            const isDimmed = selectedCharacter && !isSelected;

            return (
              <g key={`lane-bg-${lane.characterId}`}>
                {/* Lane stripe */}
                <rect
                  x={0}
                  y={getY(laneIndex) - laneHeight / 2}
                  width={svgWidth}
                  height={laneHeight}
                  fill={laneIndex % 2 === 0 ? '#fefcf8' : '#faf7f0'}
                  opacity={isDimmed ? 0.3 : 1}
                />

                {/* Character name label */}
                <text
                  x={10}
                  y={getY(laneIndex)}
                  dominantBaseline="middle"
                  fontSize={11}
                  fontFamily="serif"
                  fill={isDimmed ? '#9ca3af' : '#0f172a'}
                  fontWeight="600"
                >
                  {lane.characterName}
                </text>
              </g>
            );
          })}

          {/* Timeline axis */}
          <line
            x1={padding}
            y1={svgHeight - 20}
            x2={svgWidth - padding}
            y2={svgHeight - 20}
            stroke="#d1d5db"
            strokeWidth={1}
          />

          {/* Connection lines and nodes */}
          {characterLanes.map((lane, laneIndex) => {
            const isSelected = selectedCharacter === lane.characterId;
            const isDimmed = selectedCharacter && !isSelected;
            const y = getY(laneIndex);

            return (
              <g key={`lane-${lane.characterId}`} opacity={isDimmed ? 0.3 : 1}>
                {/* Connection lines */}
                {lane.events.map((event, eventIndex) => {
                  if (eventIndex === 0) return null;
                  const prevEvent = lane.events[eventIndex - 1];
                  const x1 = getX(prevEvent.orderIndex);
                  const x2 = getX(event.orderIndex);
                  const isLocationChange = prevEvent.locationName !== event.locationName;

                  return (
                    <line
                      key={`line-${event.eventId}`}
                      x1={x1}
                      y1={y}
                      x2={x2}
                      y2={y}
                      stroke={lane.color}
                      strokeWidth={isLocationChange ? 3 : 2}
                      strokeDasharray={isLocationChange ? '5,3' : 'none'}
                      opacity={0.7}
                    />
                  );
                })}

                {/* Event nodes */}
                {lane.events.map(event => {
                  const x = getX(event.orderIndex);
                  const isHovered = hoveredEvent === event.eventId;

                  return (
                    <g key={`node-${event.eventId}`}>
                      <circle
                        cx={x}
                        cy={y}
                        r={isHovered ? nodeRadius + 3 : nodeRadius}
                        fill={lane.color}
                        stroke="white"
                        strokeWidth={2}
                        className="cursor-pointer transition-all"
                        onMouseEnter={() => setHoveredEvent(event.eventId)}
                        onMouseLeave={() => setHoveredEvent(null)}
                      />

                      {/* Location indicator */}
                      <text
                        x={x}
                        y={y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fontSize={8}
                        fontWeight="bold"
                        fill="white"
                        pointerEvents="none"
                      >
                        {event.locationName.charAt(0).toUpperCase()}
                      </text>

                      {/* Tooltip on hover */}
                      {isHovered && (
                        <g>
                          <rect
                            x={x - 100}
                            y={y - 55}
                            width={200}
                            height={45}
                            fill="white"
                            stroke="#d1d5db"
                            rx={2}
                          />
                          <text
                            x={x}
                            y={y - 40}
                            textAnchor="middle"
                            fontSize={10}
                            fontWeight="600"
                            fill="#0f172a"
                          >
                            {event.locationName}
                          </text>
                          <text
                            x={x}
                            y={y - 25}
                            textAnchor="middle"
                            fontSize={9}
                            fill="#6b7280"
                          >
                            {event.description.slice(0, 35)}
                            {event.description.length > 35 ? '...' : ''}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}

          {/* Order index markers */}
          {Array.from({ length: Math.min(maxOrderIndex + 1, 20) }, (_, i) => {
            const step = Math.ceil((maxOrderIndex + 1) / 20);
            const orderIndex = i * step;
            if (orderIndex > maxOrderIndex) return null;

            return (
              <text
                key={`marker-${orderIndex}`}
                x={getX(orderIndex)}
                y={svgHeight - 8}
                textAnchor="middle"
                fontSize={9}
                fill="#9ca3af"
              >
                {orderIndex}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Selected character details */}
      {selectedCharacter && (() => {
        const lane = characterLanes.find(l => l.characterId === selectedCharacter);
        if (!lane) return null;

        return (
          <div className="p-4 border-t border-slate-ui bg-vellum">
            <div className="flex items-center gap-3 mb-2">
              <span
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: lane.color }}
              />
              <h4 className="font-garamond text-lg text-midnight font-semibold">
                {lane.characterName}
              </h4>
            </div>
            <div className="flex gap-6 text-sm font-sans">
              <span className="text-faded-ink">
                <span className="text-midnight font-semibold">{lane.events.length}</span> events
              </span>
              <span className="text-faded-ink">
                <span className="text-midnight font-semibold">
                  {new Set(lane.events.map(e => e.locationName)).size}
                </span> locations
              </span>
              <span className="text-faded-ink">
                <span className="text-midnight font-semibold">
                  {lane.events.filter((e, i) =>
                    i > 0 && e.locationName !== lane.events[i - 1].locationName
                  ).length}
                </span> moves
              </span>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
