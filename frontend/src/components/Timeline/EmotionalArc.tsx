/**
 * EmotionalArc - Line chart showing emotional journey
 * Tracks sentiment over timeline events
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface EmotionalArcProps {
  manuscriptId: string;
}

export default function EmotionalArc({ manuscriptId }: EmotionalArcProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [showAllEvents, setShowAllEvents] = useState(true);

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

  if (loading || events.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-faded-ink font-sans text-sm">
          {loading ? 'Loading...' : 'No events to visualize'}
        </p>
      </div>
    );
  }

  const sortedEvents = [...events].sort((a, b) => a.order_index - b.order_index);

  // Filter events by character if selected
  const filteredEvents = selectedCharacter && !showAllEvents
    ? sortedEvents.filter(e => e.character_ids.includes(selectedCharacter))
    : sortedEvents;

  // Get characters in timeline
  const charactersInTimeline = Array.from(
    new Set(sortedEvents.flatMap(e => e.character_ids))
  ).map(charId => entities.find(e => e.id === charId)).filter(Boolean);

  // Chart dimensions
  const width = 700;
  const height = 400;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Calculate scales
  const xScale = (index: number) => {
    return padding.left + (index / Math.max(filteredEvents.length - 1, 1)) * chartWidth;
  };

  const yScale = (sentiment: number) => {
    // Sentiment ranges from -1 to 1, map to chart height
    const normalized = (sentiment + 1) / 2; // 0 to 1
    return padding.top + chartHeight - (normalized * chartHeight);
  };

  // Generate path for line chart
  const generatePath = () => {
    if (filteredEvents.length === 0) return '';

    const points = filteredEvents.map((event, index) => {
      const sentiment = event.event_metadata?.sentiment || 0;
      const x = xScale(index);
      const y = yScale(sentiment);
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  };

  // Get color based on sentiment
  const getSentimentColor = (sentiment: number): string => {
    if (sentiment > 0.3) return '#10b981'; // green
    if (sentiment > 0) return '#84cc16'; // lime
    if (sentiment > -0.3) return '#94a3b8'; // slate
    if (sentiment > -0.6) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="p-4 border-b border-slate-ui bg-white space-y-3">
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
            Character Filter
          </label>
          <select
            value={selectedCharacter || ''}
            onChange={(e) => setSelectedCharacter(e.target.value || null)}
            className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
            style={{ borderRadius: '2px' }}
          >
            <option value="">All Events</option>
            {charactersInTimeline.map((char) => (
              <option key={char!.id} value={char!.id}>
                {char!.name}
              </option>
            ))}
          </select>
        </div>

        {selectedCharacter && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showAllEvents}
              onChange={(e) => setShowAllEvents(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm font-sans text-midnight">
              Show all events (highlight character scenes)
            </span>
          </label>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 overflow-auto p-4 bg-vellum">
        <div className="max-w-4xl mx-auto">
          <h3 className="font-garamond text-lg text-midnight mb-4 text-center">
            Emotional Arc
            {selectedCharacter && !showAllEvents && (
              <span className="text-bronze">
                {' - '}{entities.find(e => e.id === selectedCharacter)?.name}
              </span>
            )}
          </h3>

          <svg width={width} height={height} className="mx-auto">
            {/* Y-axis grid lines */}
            <g className="grid-lines">
              {[-1, -0.5, 0, 0.5, 1].map(sentiment => {
                const y = yScale(sentiment);
                return (
                  <g key={sentiment}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={width - padding.right}
                      y2={y}
                      stroke="#e2e8f0"
                      strokeWidth={sentiment === 0 ? 2 : 1}
                      strokeDasharray={sentiment === 0 ? '0' : '4'}
                    />
                    <text
                      x={padding.left - 10}
                      y={y}
                      textAnchor="end"
                      dominantBaseline="middle"
                      fontSize="11"
                      fill="#64748b"
                    >
                      {sentiment > 0 ? '+' : ''}{sentiment.toFixed(1)}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* X-axis labels */}
            <g className="x-axis">
              {filteredEvents.map((event, index) => {
                if (index % Math.max(1, Math.floor(filteredEvents.length / 10)) === 0) {
                  const x = xScale(index);
                  return (
                    <g key={event.id}>
                      <line
                        x1={x}
                        y1={padding.top}
                        x2={x}
                        y2={height - padding.bottom}
                        stroke="#e2e8f0"
                        strokeWidth={1}
                        strokeDasharray="4"
                      />
                      <text
                        x={x}
                        y={height - padding.bottom + 20}
                        textAnchor="middle"
                        fontSize="10"
                        fill="#64748b"
                      >
                        Event {event.order_index + 1}
                      </text>
                    </g>
                  );
                }
                return null;
              })}
            </g>

            {/* Emotion line */}
            <path
              d={generatePath()}
              fill="none"
              stroke="#9a6f47"
              strokeWidth={3}
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data points */}
            {filteredEvents.map((event, index) => {
              const sentiment = event.event_metadata?.sentiment || 0;
              const x = xScale(index);
              const y = yScale(sentiment);
              const isCharacterEvent = selectedCharacter && event.character_ids.includes(selectedCharacter);
              const radius = isCharacterEvent ? 6 : 4;

              return (
                <g key={event.id} className="cursor-pointer">
                  <circle
                    cx={x}
                    cy={y}
                    r={radius}
                    fill={getSentimentColor(sentiment)}
                    stroke="white"
                    strokeWidth={2}
                  />
                  <title>
                    Event {event.order_index + 1}: {event.description.slice(0, 50)}
                    {'\n'}Sentiment: {sentiment.toFixed(2)}
                    {'\n'}Tone: {event.event_metadata?.tone || 'N/A'}
                  </title>
                </g>
              );
            })}

            {/* Axis labels */}
            <text
              x={padding.left + chartWidth / 2}
              y={height - 10}
              textAnchor="middle"
              fontSize="12"
              fontFamily="sans-serif"
              fill="#475569"
            >
              Timeline Progression
            </text>
            <text
              x={-height / 2}
              y={20}
              textAnchor="middle"
              fontSize="12"
              fontFamily="sans-serif"
              fill="#475569"
              transform={`rotate(-90, 20, ${height / 2})`}
            >
              Emotional Sentiment
            </text>
          </svg>

          {/* Legend */}
          <div className="mt-6 p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
            <h4 className="text-xs font-sans text-faded-ink uppercase mb-3">Sentiment Scale</h4>
            <div className="grid grid-cols-5 gap-2 text-center">
              <div>
                <div className="w-full h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
                <p className="text-xs font-sans text-faded-ink mt-1">Very Negative</p>
              </div>
              <div>
                <div className="w-full h-4 rounded" style={{ backgroundColor: '#f59e0b' }} />
                <p className="text-xs font-sans text-faded-ink mt-1">Negative</p>
              </div>
              <div>
                <div className="w-full h-4 rounded" style={{ backgroundColor: '#94a3b8' }} />
                <p className="text-xs font-sans text-faded-ink mt-1">Neutral</p>
              </div>
              <div>
                <div className="w-full h-4 rounded" style={{ backgroundColor: '#84cc16' }} />
                <p className="text-xs font-sans text-faded-ink mt-1">Positive</p>
              </div>
              <div>
                <div className="w-full h-4 rounded" style={{ backgroundColor: '#10b981' }} />
                <p className="text-xs font-sans text-faded-ink mt-1">Very Positive</p>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-slate-ui">
              <div>
                <p className="text-xs text-faded-ink font-sans">Average Sentiment:</p>
                <p className="text-lg font-semibold text-midnight">
                  {(filteredEvents.reduce((sum, e) => sum + (e.event_metadata?.sentiment || 0), 0) / filteredEvents.length).toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-xs text-faded-ink font-sans">Emotional Range:</p>
                <p className="text-lg font-semibold text-midnight">
                  {Math.max(...filteredEvents.map(e => e.event_metadata?.sentiment || 0)).toFixed(2)} to{' '}
                  {Math.min(...filteredEvents.map(e => e.event_metadata?.sentiment || 0)).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
