/**
 * EnhancedSwimlaneTimeline - Visually compelling character journey visualization
 *
 * Features:
 * - Character swimlanes with event nodes
 * - Conflict/tension markers between characters
 * - Emotional arc overlays (gradient backgrounds)
 * - Story beat annotations
 * - Interactive tooltips and selection
 */

import { useState, useEffect, useMemo, useRef } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface EnhancedSwimlaneTimelineProps {
  manuscriptId: string;
}

interface CharacterLane {
  characterId: string;
  characterName: string;
  events: LaneEvent[];
  color: string;
  emotionalArc: EmotionalPoint[];
}

interface LaneEvent {
  eventId: string;
  description: string;
  locationId: string | null;
  locationName: string;
  orderIndex: number;
  timestamp: string | null;
  eventType: string;
  sentiment: number | null;
  narrativeImportance: number;
}

interface EmotionalPoint {
  orderIndex: number;
  sentiment: number; // -1 to 1
  intensity: number; // 0 to 1
}

interface ConflictMarker {
  character1Id: string;
  character2Id: string;
  orderIndex: number;
  intensity: number;
  description: string;
  eventId: string;
}

// Rich color palette for character lanes
const LANE_COLORS = [
  { main: '#9a6f47', light: 'rgba(154, 111, 71, 0.1)', gradient: 'rgba(154, 111, 71, 0.05)' },
  { main: '#3b82f6', light: 'rgba(59, 130, 246, 0.1)', gradient: 'rgba(59, 130, 246, 0.05)' },
  { main: '#10b981', light: 'rgba(16, 185, 129, 0.1)', gradient: 'rgba(16, 185, 129, 0.05)' },
  { main: '#f59e0b', light: 'rgba(245, 158, 11, 0.1)', gradient: 'rgba(245, 158, 11, 0.05)' },
  { main: '#8b5cf6', light: 'rgba(139, 92, 246, 0.1)', gradient: 'rgba(139, 92, 246, 0.05)' },
  { main: '#ec4899', light: 'rgba(236, 72, 153, 0.1)', gradient: 'rgba(236, 72, 153, 0.05)' },
  { main: '#06b6d4', light: 'rgba(6, 182, 212, 0.1)', gradient: 'rgba(6, 182, 212, 0.05)' },
  { main: '#84cc16', light: 'rgba(132, 204, 22, 0.1)', gradient: 'rgba(132, 204, 22, 0.05)' },
];

// Conflict keywords for detection
const CONFLICT_KEYWORDS = [
  'fight', 'fighting', 'fought', 'battle', 'war', 'attack', 'attacked',
  'confront', 'confronted', 'argue', 'argued', 'disagree', 'disagreed',
  'anger', 'angry', 'furious', 'rage', 'hate', 'hated', 'enemy', 'enemies',
  'betray', 'betrayed', 'deceive', 'deceived', 'oppose', 'opposed',
  'threaten', 'threatened', 'accuse', 'accused', 'blame', 'blamed'
];

export default function EnhancedSwimlaneTimeline({ manuscriptId }: EnhancedSwimlaneTimelineProps) {
  const { events } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<string | null>(null);
  const [showConflicts, setShowConflicts] = useState(true);
  const [showEmotionalArcs, setShowEmotionalArcs] = useState(true);
  const svgRef = useRef<SVGSVGElement>(null);

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

  // Build character lanes with emotional arcs
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
          eventType: event.event_type,
          sentiment: event.event_metadata?.sentiment ?? null,
          narrativeImportance: event.narrative_importance || 5,
        }));

      if (characterEvents.length > 0) {
        // Build emotional arc from events
        const emotionalArc: EmotionalPoint[] = characterEvents.map(e => ({
          orderIndex: e.orderIndex,
          sentiment: e.sentiment ?? 0,
          intensity: Math.abs(e.sentiment ?? 0) * (e.narrativeImportance / 10),
        }));

        lanes.push({
          characterId: character.id,
          characterName: character.name,
          events: characterEvents,
          color: LANE_COLORS[index % LANE_COLORS.length].main,
          emotionalArc,
        });
      }
    });

    return lanes;
  }, [events, entities]);

  // Detect conflicts between characters
  const conflictMarkers = useMemo<ConflictMarker[]>(() => {
    const markers: ConflictMarker[] = [];
    const characters = entities.filter(e => e.type === 'CHARACTER');

    events.forEach(event => {
      if (event.character_ids.length < 2) return;

      const eventText = event.description.toLowerCase();
      const conflictKeywords = CONFLICT_KEYWORDS.filter(keyword =>
        eventText.includes(keyword)
      );

      if (conflictKeywords.length === 0) return;

      // Create conflict markers for all character pairs
      for (let i = 0; i < event.character_ids.length; i++) {
        for (let j = i + 1; j < event.character_ids.length; j++) {
          const char1 = characters.find(c => c.id === event.character_ids[i]);
          const char2 = characters.find(c => c.id === event.character_ids[j]);

          if (!char1 || !char2) continue;

          const intensity = Math.min(conflictKeywords.length / 3, 1);

          markers.push({
            character1Id: char1.id,
            character2Id: char2.id,
            orderIndex: event.order_index,
            intensity,
            description: `${char1.name} vs ${char2.name}: ${conflictKeywords.join(', ')}`,
            eventId: event.id,
          });
        }
      }
    });

    return markers;
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
          <p className="text-sm text-faded-ink font-sans">Loading timeline data...</p>
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
          <span className="text-6xl mb-4 block">🎭</span>
          <p className="text-midnight font-garamond text-xl font-semibold mb-3">
            No character journeys to visualize
          </p>

          {!hasCharacters ? (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                Create characters in your Codex to see their journeys.
              </p>
            </div>
          ) : !hasEvents ? (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                Add timeline events to track character arcs.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-faded-ink font-sans">
                Link characters to events to visualize their journeys.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  const laneHeight = 100;
  const nodeRadius = 14;
  const padding = 80;
  const headerHeight = 40;
  const svgWidth = Math.max(900, (maxOrderIndex + 1) * 70 + padding * 2);
  const svgHeight = characterLanes.length * laneHeight + padding * 2 + headerHeight;

  // Get X position for an order index
  const getX = (orderIndex: number) => {
    if (maxOrderIndex === 0) return svgWidth / 2;
    return padding + (orderIndex / maxOrderIndex) * (svgWidth - padding * 2);
  };

  // Get Y position for a lane
  const getY = (laneIndex: number) => padding + headerHeight + laneIndex * laneHeight + laneHeight / 2;

  // Get lane index for a character
  const getLaneIndex = (characterId: string) => {
    return characterLanes.findIndex(l => l.characterId === characterId);
  };

  // Get sentiment color
  const getSentimentColor = (sentiment: number): string => {
    if (sentiment > 0.3) return '#10b981'; // Green for positive
    if (sentiment < -0.3) return '#ef4444'; // Red for negative
    return '#6b7280'; // Gray for neutral
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-garamond text-lg text-midnight mb-1">
              Character Journey Timeline
            </h3>
            <p className="text-sm font-sans text-faded-ink">
              Visualize character arcs, conflicts, and emotional journeys
            </p>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm font-sans cursor-pointer">
              <input
                type="checkbox"
                checked={showConflicts}
                onChange={(e) => setShowConflicts(e.target.checked)}
                className="accent-bronze"
              />
              <span className="text-midnight">Show Conflicts</span>
            </label>
            <label className="flex items-center gap-2 text-sm font-sans cursor-pointer">
              <input
                type="checkbox"
                checked={showEmotionalArcs}
                onChange={(e) => setShowEmotionalArcs(e.target.checked)}
                className="accent-bronze"
              />
              <span className="text-midnight">Emotional Arcs</span>
            </label>
          </div>
        </div>
      </div>

      {/* Character Legend */}
      <div className="p-3 border-b border-slate-ui bg-vellum flex flex-wrap gap-3">
        {characterLanes.map((lane, idx) => (
          <button
            key={lane.characterId}
            onClick={() => setSelectedCharacter(
              selectedCharacter === lane.characterId ? null : lane.characterId
            )}
            className={`
              flex items-center gap-2 px-3 py-1.5 text-xs font-sans transition-all border
              ${selectedCharacter === lane.characterId
                ? 'border-bronze bg-bronze/10'
                : selectedCharacter
                  ? 'opacity-50 border-transparent'
                  : 'border-transparent hover:border-bronze/30'
              }
            `}
            style={{ borderRadius: '4px' }}
          >
            <span
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: lane.color }}
            />
            <span className="text-midnight font-semibold">{lane.characterName}</span>
            <span className="text-faded-ink">({lane.events.length} events)</span>
          </button>
        ))}

        {conflictMarkers.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-sans text-faded-ink border-l border-slate-ui ml-2 pl-4">
            <span className="text-redline">⚡</span>
            <span>{conflictMarkers.length} conflict{conflictMarkers.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* Swimlane Visualization */}
      <div className="flex-1 overflow-auto bg-white">
        <svg ref={svgRef} width={svgWidth} height={svgHeight} className="min-w-full">
          <defs>
            {/* Gradient for emotional arcs */}
            <linearGradient id="emotionalGradientPositive" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="emotionalGradientNegative" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </linearGradient>

            {/* Conflict marker gradient */}
            <linearGradient id="conflictGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.8" />
            </linearGradient>

            {/* Filter for glow effect */}
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Story beat markers at top */}
          <g className="story-beats">
            {Array.from({ length: Math.min(maxOrderIndex + 1, 30) }, (_, i) => {
              const step = Math.ceil((maxOrderIndex + 1) / 30);
              const orderIndex = i * step;
              if (orderIndex > maxOrderIndex) return null;

              return (
                <g key={`beat-${orderIndex}`}>
                  <line
                    x1={getX(orderIndex)}
                    y1={padding}
                    x2={getX(orderIndex)}
                    y2={svgHeight - 20}
                    stroke="#e5e7eb"
                    strokeWidth={1}
                    strokeDasharray="2,4"
                  />
                  <text
                    x={getX(orderIndex)}
                    y={padding - 5}
                    textAnchor="middle"
                    fontSize={10}
                    fill="#9ca3af"
                    fontFamily="sans-serif"
                  >
                    {orderIndex}
                  </text>
                </g>
              );
            })}
          </g>

          {/* Lane backgrounds with emotional gradients */}
          {characterLanes.map((lane, laneIndex) => {
            const isSelected = selectedCharacter === lane.characterId;
            const isDimmed = selectedCharacter && !isSelected;
            const colorSet = LANE_COLORS[laneIndex % LANE_COLORS.length];

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

                {/* Emotional arc overlay */}
                {showEmotionalArcs && lane.emotionalArc.length > 1 && (
                  <path
                    d={generateEmotionalArcPath(lane.emotionalArc, laneIndex, getX, getY, laneHeight)}
                    fill="none"
                    stroke={colorSet.main}
                    strokeWidth={2}
                    strokeOpacity={isDimmed ? 0.2 : 0.4}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Character name label */}
                <text
                  x={15}
                  y={getY(laneIndex)}
                  dominantBaseline="middle"
                  fontSize={12}
                  fontFamily="Georgia, serif"
                  fill={isDimmed ? '#9ca3af' : '#0f172a'}
                  fontWeight="600"
                >
                  {lane.characterName}
                </text>
              </g>
            );
          })}

          {/* Conflict markers (vertical lines connecting conflicting characters) */}
          {showConflicts && conflictMarkers.map((conflict, idx) => {
            const lane1Index = getLaneIndex(conflict.character1Id);
            const lane2Index = getLaneIndex(conflict.character2Id);

            if (lane1Index === -1 || lane2Index === -1) return null;

            const x = getX(conflict.orderIndex);
            const y1 = getY(Math.min(lane1Index, lane2Index));
            const y2 = getY(Math.max(lane1Index, lane2Index));

            const isHighlighted = selectedCharacter === conflict.character1Id ||
                                  selectedCharacter === conflict.character2Id;
            const isDimmed = selectedCharacter && !isHighlighted;

            if (isDimmed) return null;

            return (
              <g key={`conflict-${idx}`} className="cursor-pointer">
                {/* Conflict line */}
                <line
                  x1={x}
                  y1={y1}
                  x2={x}
                  y2={y2}
                  stroke="#ef4444"
                  strokeWidth={3 * conflict.intensity + 1}
                  strokeOpacity={0.6}
                  strokeDasharray="4,2"
                />

                {/* Conflict marker */}
                <circle
                  cx={x}
                  cy={(y1 + y2) / 2}
                  r={8}
                  fill="#ef4444"
                  opacity={0.9}
                  filter="url(#glow)"
                />
                <text
                  x={x}
                  y={(y1 + y2) / 2}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={10}
                  fill="white"
                  fontWeight="bold"
                >
                  ⚡
                </text>

                {/* Tooltip on hover */}
                {hoveredEvent === conflict.eventId && (
                  <g>
                    <rect
                      x={x - 100}
                      y={(y1 + y2) / 2 - 35}
                      width={200}
                      height={30}
                      fill="white"
                      stroke="#ef4444"
                      rx={4}
                    />
                    <text
                      x={x}
                      y={(y1 + y2) / 2 - 17}
                      textAnchor="middle"
                      fontSize={11}
                      fill="#0f172a"
                      fontFamily="sans-serif"
                    >
                      {conflict.description}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Character journey lines and event nodes */}
          {characterLanes.map((lane, laneIndex) => {
            const isSelected = selectedCharacter === lane.characterId;
            const isDimmed = selectedCharacter && !isSelected;
            const y = getY(laneIndex);
            const colorSet = LANE_COLORS[laneIndex % LANE_COLORS.length];

            return (
              <g key={`lane-${lane.characterId}`} opacity={isDimmed ? 0.25 : 1}>
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
                      strokeWidth={isLocationChange ? 4 : 2}
                      strokeDasharray={isLocationChange ? '8,4' : 'none'}
                      opacity={0.8}
                    />
                  );
                })}

                {/* Event nodes */}
                {lane.events.map(event => {
                  const x = getX(event.orderIndex);
                  const isHovered = hoveredEvent === event.eventId;
                  const isHighImportance = event.narrativeImportance > 7;

                  // Determine node size based on importance
                  const radius = isHovered ? nodeRadius + 4 :
                                 isHighImportance ? nodeRadius + 2 : nodeRadius;

                  return (
                    <g key={`node-${event.eventId}`}>
                      {/* Sentiment ring */}
                      {event.sentiment !== null && showEmotionalArcs && (
                        <circle
                          cx={x}
                          cy={y}
                          r={radius + 4}
                          fill="none"
                          stroke={getSentimentColor(event.sentiment)}
                          strokeWidth={2}
                          strokeOpacity={0.6}
                        />
                      )}

                      {/* Main node */}
                      <circle
                        cx={x}
                        cy={y}
                        r={radius}
                        fill={lane.color}
                        stroke="white"
                        strokeWidth={2}
                        className="cursor-pointer transition-all"
                        filter={isHighImportance ? 'url(#glow)' : undefined}
                        onMouseEnter={() => setHoveredEvent(event.eventId)}
                        onMouseLeave={() => setHoveredEvent(null)}
                      />

                      {/* Location initial */}
                      <text
                        x={x}
                        y={y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fontSize={10}
                        fontWeight="bold"
                        fill="white"
                        pointerEvents="none"
                      >
                        {event.locationName.charAt(0).toUpperCase()}
                      </text>

                      {/* High importance star */}
                      {isHighImportance && (
                        <text
                          x={x + radius + 2}
                          y={y - radius - 2}
                          fontSize={12}
                          fill="#f59e0b"
                        >
                          ★
                        </text>
                      )}

                      {/* Tooltip on hover */}
                      {isHovered && (
                        <g>
                          <rect
                            x={x - 120}
                            y={y - 70}
                            width={240}
                            height={55}
                            fill="white"
                            stroke={colorSet.main}
                            strokeWidth={1}
                            rx={4}
                            filter="drop-shadow(0 2px 4px rgba(0,0,0,0.1))"
                          />
                          <text
                            x={x}
                            y={y - 52}
                            textAnchor="middle"
                            fontSize={11}
                            fontWeight="600"
                            fill="#0f172a"
                            fontFamily="Georgia, serif"
                          >
                            {event.locationName}
                            {event.timestamp && ` • ${event.timestamp}`}
                          </text>
                          <text
                            x={x}
                            y={y - 35}
                            textAnchor="middle"
                            fontSize={10}
                            fill="#6b7280"
                            fontFamily="sans-serif"
                          >
                            {event.description.slice(0, 45)}
                            {event.description.length > 45 ? '...' : ''}
                          </text>
                          {event.sentiment !== null && (
                            <text
                              x={x}
                              y={y - 20}
                              textAnchor="middle"
                              fontSize={9}
                              fill={getSentimentColor(event.sentiment)}
                              fontFamily="sans-serif"
                            >
                              Sentiment: {event.sentiment > 0 ? '+' : ''}{(event.sentiment * 100).toFixed(0)}%
                            </text>
                          )}
                        </g>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}

          {/* Timeline axis label */}
          <text
            x={svgWidth / 2}
            y={svgHeight - 5}
            textAnchor="middle"
            fontSize={11}
            fill="#9ca3af"
            fontFamily="sans-serif"
          >
            Story Progression →
          </text>
        </svg>
      </div>

      {/* Selected character summary */}
      {selectedCharacter && (() => {
        const lane = characterLanes.find(l => l.characterId === selectedCharacter);
        if (!lane) return null;

        const relevantConflicts = conflictMarkers.filter(
          c => c.character1Id === selectedCharacter || c.character2Id === selectedCharacter
        );

        const avgSentiment = lane.emotionalArc.length > 0
          ? lane.emotionalArc.reduce((sum, p) => sum + p.sentiment, 0) / lane.emotionalArc.length
          : 0;

        return (
          <div className="p-4 border-t border-slate-ui bg-vellum">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <span
                  className="w-5 h-5 rounded-full"
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
                {relevantConflicts.length > 0 && (
                  <span className="text-faded-ink">
                    <span className="text-redline font-semibold">{relevantConflicts.length}</span> conflicts
                  </span>
                )}
                <span className="text-faded-ink">
                  Avg sentiment:{' '}
                  <span style={{ color: getSentimentColor(avgSentiment) }} className="font-semibold">
                    {avgSentiment > 0 ? '+' : ''}{(avgSentiment * 100).toFixed(0)}%
                  </span>
                </span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

// Helper function to generate emotional arc path
function generateEmotionalArcPath(
  emotionalArc: EmotionalPoint[],
  laneIndex: number,
  getX: (orderIndex: number) => number,
  getY: (laneIndex: number) => number,
  laneHeight: number
): string {
  if (emotionalArc.length < 2) return '';

  const baseY = getY(laneIndex);
  const maxDeviation = laneHeight / 3;

  const points = emotionalArc.map(point => {
    const x = getX(point.orderIndex);
    const y = baseY - (point.sentiment * maxDeviation);
    return { x, y };
  });

  // Create smooth curve using quadratic bezier
  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const cpX = (prev.x + curr.x) / 2;
    path += ` Q ${cpX} ${prev.y} ${curr.x} ${curr.y}`;
  }

  return path;
}
