/**
 * TimelineHeatmap - Visual heatmap of timeline events
 * Shows:
 * - Emotional intensity across timeline
 * - Scene density
 * - Character activity
 * - Location usage
 */

import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface TimelineHeatmapProps {
  manuscriptId: string;
}

export default function TimelineHeatmap({ manuscriptId }: TimelineHeatmapProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [heatmapMode, setHeatmapMode] = useState<'emotion' | 'density' | 'character' | 'location'>('emotion');
  const [hoveredEvent, setHoveredEvent] = useState<{ index: number; rect: DOMRect } | null>(null);
  const cardRefs = useRef<Map<number, HTMLDivElement>>(new Map());

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

  // Determine if we should sample events for large manuscripts
  const shouldSample = sortedEvents.length > 100; // Novel-length
  const displayEvents = shouldSample
    ? sortedEvents.filter((_, idx) => idx % 2 === 0) // Show every other event
    : sortedEvents;

  // Calculate heatmap values based on mode
  const getHeatmapValue = (eventIndex: number): number => {
    const event = sortedEvents[eventIndex];

    switch (heatmapMode) {
      case 'emotion':
        // Use tone to derive intensity
        const tone = event.event_metadata?.tone?.toLowerCase();
        const intensityMap: Record<string, number> = {
          'triumphant': 1.0, 'joyful': 0.9, 'dramatic': 0.8, 'tragic': 0.9,
          'mysterious': 0.6, 'hopeful': 0.5, 'tense': 0.7, 'peaceful': 0.3
        };
        return tone ? (intensityMap[tone] || 0.5) : 0.5;

      case 'density':
        // Use number of characters as density proxy
        return Math.min(event.character_ids.length / 3, 1.0);

      case 'character':
        // Number of characters
        return Math.min(event.character_ids.length / 5, 1.0);

      case 'location':
        // Has location
        return event.location_id ? 1.0 : 0.2;

      default:
        return 0;
    }
  };

  // Get color based on value and sentiment
  const getHeatmapColor = (value: number, eventIndex: number): string => {
    const event = sortedEvents[eventIndex];
    const sentiment = event.event_metadata?.sentiment || 0;

    if (heatmapMode === 'emotion') {
      // Color based on sentiment: positive = green, negative = red, neutral = gray
      if (sentiment > 0.2) {
        const intensity = Math.floor(value * 255);
        return `rgb(${255 - intensity}, ${200 + intensity * 0.2}, ${255 - intensity})`;
      } else if (sentiment < -0.2) {
        const intensity = Math.floor(value * 255);
        return `rgb(${200 + intensity * 0.2}, ${255 - intensity}, ${255 - intensity})`;
      } else {
        const intensity = Math.floor(value * 200);
        return `rgb(${150 + intensity * 0.5}, ${150 + intensity * 0.5}, ${200 + intensity * 0.2})`;
      }
    } else {
      // Standard blue gradient
      const intensity = Math.floor(value * 200);
      return `rgb(${255 - intensity}, ${255 - intensity * 0.5}, 255)`;
    }
  };

  // Get tooltip text
  const getTooltipText = (eventIndex: number): string => {
    const event = sortedEvents[eventIndex];
    const value = getHeatmapValue(eventIndex);

    switch (heatmapMode) {
      case 'emotion':
        return `Event ${eventIndex + 1}\n${event.description.slice(0, 50)}...\nSentiment: ${event.event_metadata?.sentiment?.toFixed(2) || 0}\nIntensity: ${(value * 100).toFixed(0)}%`;

      case 'density':
        return `Event ${eventIndex + 1}\n${event.description.slice(0, 50)}...\nWords: ${event.event_metadata?.word_count || 0}`;

      case 'character':
        const charNames = event.character_ids
          .map(id => entities.find(e => e.id === id)?.name)
          .filter(Boolean)
          .join(', ');
        return `Event ${eventIndex + 1}\n${event.description.slice(0, 50)}...\nCharacters: ${charNames || 'None'}`;

      case 'location':
        const location = event.location_id ? entities.find(e => e.id === event.location_id)?.name : 'Unknown';
        return `Event ${eventIndex + 1}\n${event.description.slice(0, 50)}...\nLocation: ${location}`;

      default:
        return event.description.slice(0, 50);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Mode selector */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
          Heatmap Mode
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setHeatmapMode('emotion')}
            className={`px-3 py-2 text-sm font-sans transition-colors ${
              heatmapMode === 'emotion'
                ? 'bg-bronze text-white'
                : 'bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20'
            }`}
            style={{ borderRadius: '2px' }}
          >
            💭 Emotion
          </button>
          <button
            onClick={() => setHeatmapMode('density')}
            className={`px-3 py-2 text-sm font-sans transition-colors ${
              heatmapMode === 'density'
                ? 'bg-bronze text-white'
                : 'bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📊 Density
          </button>
          <button
            onClick={() => setHeatmapMode('character')}
            className={`px-3 py-2 text-sm font-sans transition-colors ${
              heatmapMode === 'character'
                ? 'bg-bronze text-white'
                : 'bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20'
            }`}
            style={{ borderRadius: '2px' }}
          >
            👥 Characters
          </button>
          <button
            onClick={() => setHeatmapMode('location')}
            className={`px-3 py-2 text-sm font-sans transition-colors ${
              heatmapMode === 'location'
                ? 'bg-bronze text-white'
                : 'bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📍 Location
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="flex items-center gap-2 text-xs font-sans text-faded-ink">
          <span>Low</span>
          <div className="flex-1 h-4 rounded overflow-hidden flex">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="flex-1"
                style={{
                  backgroundColor: getHeatmapColor(i / 10, 0)
                }}
              />
            ))}
          </div>
          <span>High</span>
        </div>
        {heatmapMode === 'emotion' && (
          <p className="text-xs text-faded-ink mt-2">
            Green = Positive, Red = Negative, Blue = Neutral
          </p>
        )}
      </div>

      {/* Heatmap grid */}
      <div className="flex-1 overflow-auto p-4 pb-8">
        {shouldSample && (
          <div className="mb-4 p-2 bg-bronze/10 border border-bronze/20 rounded text-xs font-sans text-bronze">
            Showing sample of {displayEvents.length} / {sortedEvents.length} events (every other event)
          </div>
        )}
        <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(auto-fill, minmax(60px, 1fr))` }}>
          {displayEvents.map((event) => {
            // Get original index for proper coloring and tooltip
            const index = sortedEvents.indexOf(event);
            const value = getHeatmapValue(index);
            const color = getHeatmapColor(value, index);

            return (
              <div
                key={event.id}
                ref={(el) => {
                  if (el) cardRefs.current.set(index, el);
                }}
                className="aspect-square flex flex-col items-center justify-center cursor-pointer hover:scale-105 transition-transform relative"
                style={{
                  backgroundColor: color,
                  borderRadius: '4px',
                  border: '1px solid rgba(0,0,0,0.1)'
                }}
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setHoveredEvent({ index, rect });
                }}
                onMouseLeave={() => setHoveredEvent(null)}
              >
                {event.event_metadata?.tone && heatmapMode === 'emotion' ? (
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="text-xs text-gray-700 font-medium capitalize">
                      {event.event_metadata.tone}
                    </span>
                    <span className="text-xs text-gray-500 font-medium">
                      #{index + 1}
                    </span>
                  </div>
                ) : (
                  <span className="text-xs font-bold text-midnight">
                    {index + 1}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Statistics */}
        <div className="mt-6 p-4 bg-white border border-slate-ui" style={{ borderRadius: '2px' }}>
          <h3 className="font-garamond font-semibold text-midnight mb-3">Statistics</h3>
          <div className="grid grid-cols-2 gap-4 text-sm font-sans">
            <div>
              <span className="text-faded-ink">Total Events:</span>
              <span className="ml-2 font-semibold text-midnight">{sortedEvents.length}</span>
            </div>
            {heatmapMode === 'emotion' && (
              <>
                <div>
                  <span className="text-faded-ink">Avg Sentiment:</span>
                  <span className="ml-2 font-semibold text-midnight">
                    {(sortedEvents.reduce((sum, e) => sum + (e.event_metadata?.sentiment || 0), 0) / sortedEvents.length).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-faded-ink">Avg Intensity:</span>
                  <span className="ml-2 font-semibold text-midnight">
                    {(sortedEvents.reduce((sum, e) => sum + (e.event_metadata?.intensity || 0), 0) / sortedEvents.length * 100).toFixed(0)}%
                  </span>
                </div>
              </>
            )}
            {heatmapMode === 'density' && (
              <div>
                <span className="text-faded-ink">Total Words:</span>
                <span className="ml-2 font-semibold text-midnight">
                  {sortedEvents.reduce((sum, e) => sum + (e.event_metadata?.word_count || 0), 0)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Portal tooltip - renders at document root to avoid z-index issues */}
      {hoveredEvent && createPortal(
        <div
          className="fixed pointer-events-none z-[10000]"
          style={{
            left: `${hoveredEvent.rect.left + hoveredEvent.rect.width / 2}px`,
            top: `${hoveredEvent.rect.top - 10}px`,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <div className="bg-midnight text-white text-xs p-3 rounded-lg shadow-2xl whitespace-pre-wrap max-w-xs border-2 border-bronze">
            {getTooltipText(hoveredEvent.index)}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
