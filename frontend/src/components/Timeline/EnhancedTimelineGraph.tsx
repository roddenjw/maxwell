/**
 * EnhancedTimelineGraph - Advanced timeline visualization with character journeys
 * Features:
 * - Visual timeline with events
 * - Character journey paths
 * - Location grouping
 * - Emotional tone indicators
 */

import { useState, useEffect } from 'react';
import { getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { getManuscriptScale, getLayoutConfig, getScaleInfo } from '@/lib/timelineUtils';

interface EnhancedTimelineGraphProps {
  manuscriptId: string;
}

export default function EnhancedTimelineGraph({ manuscriptId }: EnhancedTimelineGraphProps) {
  const { events, setEvents, setSelectedEvent } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'journey'>('timeline');

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

  // Determine manuscript scale and layout
  const scale = getManuscriptScale(sortedEvents.length);
  const layout = getLayoutConfig(scale);
  const scaleInfo = getScaleInfo(scale);

  // Get all characters involved in timeline
  const charactersInTimeline = Array.from(
    new Set(sortedEvents.flatMap(e => e.character_ids))
  ).map(charId => entities.find(e => e.id === charId)).filter(Boolean);

  // Get emotional tone color
  const getToneColor = (tone?: string) => {
    switch (tone) {
      case 'happy': return '#10b981'; // green
      case 'sad': return '#3b82f6'; // blue
      case 'angry': return '#ef4444'; // red
      case 'afraid': return '#a855f7'; // purple
      case 'surprised': return '#f59e0b'; // amber
      case 'tense': return '#6b7280'; // gray
      default: return '#94a3b8'; // slate
    }
  };

  // Render timeline view
  const renderTimelineView = () => (
    <div className="relative" style={{ minHeight: `${layout.graphHeight}px` }}>
      {/* Timeline line */}
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-ui"></div>

      {/* Events - spacing adapts to scale */}
      <div className="space-y-6" style={{ '--event-spacing': `${layout.eventSpacing}px` } as React.CSSProperties}>
        {sortedEvents.map((event, index) => {
          const typeColor = getEventTypeColor(event.event_type);
          const typeIcon = getEventTypeIcon(event.event_type);
          const tone = event.event_metadata?.tone;
          const toneColor = getToneColor(tone);

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
              {/* Timeline dot with tone indicator */}
              <div
                className="absolute left-4 w-5 h-5 rounded-full border-4 border-white shadow-md flex items-center justify-center"
                style={{
                  backgroundColor: typeColor,
                  top: '8px',
                  boxShadow: `0 0 0 3px ${toneColor}40`
                }}
              >
                <span className="text-xs text-white font-bold">{index + 1}</span>
              </div>

              {/* Event card */}
              <div
                className="bg-white border border-slate-ui p-4 cursor-pointer hover:shadow-lg transition-all relative"
                style={{ borderRadius: '2px' }}
                onClick={() => setSelectedEvent(event.id)}
              >
                {/* Tone indicator bar */}
                {tone && tone !== 'neutral' && (
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1"
                    style={{ backgroundColor: toneColor }}
                    title={`Tone: ${tone}`}
                  />
                )}

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
                  {tone && tone !== 'neutral' && (
                    <span
                      className="text-xs font-sans px-2 py-0.5 rounded-full"
                      style={{
                        backgroundColor: `${toneColor}20`,
                        color: toneColor
                      }}
                    >
                      {tone}
                    </span>
                  )}
                </div>

                {/* Description */}
                <p
                  className="font-serif text-midnight mb-2"
                  style={{ fontSize: `${layout.fontSize}px` }}
                >
                  {event.description}
                </p>

                {/* Actions - hide in condensed view */}
                {layout.showAllLabels && event.event_metadata?.actions && event.event_metadata.actions.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-sans text-faded-ink uppercase mb-1">Actions:</p>
                    <div className="flex flex-wrap gap-1">
                      {event.event_metadata.actions.slice(0, 3).map((action: string, idx: number) => (
                        <span
                          key={idx}
                          className="text-xs font-mono bg-slate-ui/50 px-2 py-0.5 text-midnight"
                          style={{ borderRadius: '2px' }}
                        >
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

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
                  {event.event_metadata?.word_count && (
                    <span className="flex items-center gap-1">
                      <span>📝</span>
                      {event.event_metadata.word_count} words
                    </span>
                  )}
                  {event.event_metadata?.has_transition && (
                    <span className="flex items-center gap-1 text-bronze">
                      <span>🔄</span>
                      Transition
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Render character journey view
  const renderJourneyView = () => {
    if (!selectedCharacter) {
      return (
        <div className="p-4 text-center">
          <p className="text-faded-ink font-sans text-sm">
            Select a character to view their journey
          </p>
        </div>
      );
    }

    const characterEvents = sortedEvents.filter(e =>
      e.character_ids.includes(selectedCharacter)
    );

    const character = entities.find(e => e.id === selectedCharacter);

    // Calculate character relationships from co-occurrences
    const relationships = new Map<string, number>();
    characterEvents.forEach(event => {
      const otherChars = event.character_ids.filter(id => id !== selectedCharacter);
      otherChars.forEach(otherId => {
        relationships.set(otherId, (relationships.get(otherId) || 0) + 1);
      });
    });

    const relationshipsList = Array.from(relationships.entries())
      .map(([charId, count]) => ({
        character: entities.find(e => e.id === charId),
        interactions: count
      }))
      .filter(r => r.character)
      .sort((a, b) => b.interactions - a.interactions);

    // Calculate emotional journey stats
    const avgSentiment = characterEvents.reduce((sum, e) => sum + (e.event_metadata?.sentiment || 0), 0) / characterEvents.length || 0;
    const locations = new Set(characterEvents.map(e => e.location_id).filter(Boolean));

    return (
      <div className="space-y-4">
        <div className="p-4 bg-white border-b border-slate-ui">
          <h3 className="font-garamond text-lg text-midnight">
            {character?.name}'s Journey
          </h3>
          <p className="text-sm font-sans text-faded-ink">
            {characterEvents.length} events • {locations.size} locations
          </p>
          <div className="mt-2 flex items-center gap-4">
            <div className="text-xs font-sans">
              <span className="text-faded-ink">Avg Sentiment:</span>
              <span className={`ml-1 font-semibold ${avgSentiment > 0 ? 'text-green-600' : avgSentiment < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                {avgSentiment.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Relationships */}
        {relationshipsList.length > 0 && (
          <div className="px-4">
            <h4 className="text-xs font-sans text-faded-ink uppercase mb-2">
              Key Relationships
            </h4>
            <div className="flex flex-wrap gap-2">
              {relationshipsList.slice(0, 5).map(rel => (
                <div
                  key={rel.character!.id}
                  className="px-3 py-1 bg-bronze/10 border border-bronze/30 text-sm"
                  style={{ borderRadius: '2px' }}
                  title={`${rel.interactions} shared scenes`}
                >
                  <span className="font-serif text-midnight">{rel.character!.name}</span>
                  <span className="ml-1 text-xs text-bronze font-semibold">×{rel.interactions}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="relative px-4">
          {/* Journey path */}
          <div className="absolute left-10 top-0 bottom-0 w-1 bg-bronze/30"></div>

          {/* Character events */}
          <div className="space-y-6">
            {characterEvents.map((event, idx) => {
              const location = event.location_id
                ? entities.find(e => e.id === event.location_id)
                : null;

              const sentiment = event.event_metadata?.sentiment || 0;
              const tone = event.event_metadata?.tone;

              // Get other characters in this scene
              const otherChars = event.character_ids
                .filter(id => id !== selectedCharacter)
                .map(id => entities.find(e => e.id === id)?.name)
                .filter(Boolean);

              return (
                <div key={event.id} className="relative pl-12">
                  {/* Journey node */}
                  <div
                    className="absolute left-6 w-8 h-8 rounded-full bg-bronze border-4 border-white shadow-md flex items-center justify-center"
                    style={{
                      top: '8px',
                      boxShadow: sentiment > 0 ? '0 0 0 3px rgba(16, 185, 129, 0.3)' : sentiment < 0 ? '0 0 0 3px rgba(239, 68, 68, 0.3)' : undefined
                    }}
                  >
                    <span className="text-xs text-white font-bold">{idx + 1}</span>
                  </div>

                  {/* Event info */}
                  <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
                    <p className="text-sm font-serif text-midnight mb-2">
                      {event.description}
                    </p>
                    <div className="flex flex-wrap gap-2 text-xs text-faded-ink font-sans mb-2">
                      {event.timestamp && (
                        <span>🕐 {event.timestamp}</span>
                      )}
                      {location && (
                        <span>📍 {location.name}</span>
                      )}
                      {tone && tone !== 'neutral' && (
                        <span className="text-bronze">💭 {tone}</span>
                      )}
                    </div>
                    {otherChars.length > 0 && (
                      <div className="text-xs font-sans text-faded-ink">
                        <span>With: {otherChars.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* View mode tabs with scale indicator */}
      <div className="flex items-center border-b border-slate-ui bg-white">
        <div className="flex flex-1">
          <button
            onClick={() => setViewMode('timeline')}
            className={`
              flex-1 px-4 py-2 text-sm font-sans transition-colors
              ${viewMode === 'timeline'
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            Timeline
          </button>
          <button
            onClick={() => setViewMode('journey')}
            className={`
              flex-1 px-4 py-2 text-sm font-sans transition-colors
              ${viewMode === 'journey'
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            Journey
          </button>
        </div>

        {/* Scale indicator */}
        <div className="px-4 py-2 flex items-center gap-2 border-l border-slate-ui">
          <span className="text-sm">{scaleInfo.icon}</span>
          <span className="text-xs font-sans text-faded-ink">
            {scaleInfo.label}
          </span>
          <span className="text-xs font-sans text-bronze font-semibold">
            ({sortedEvents.length} events)
          </span>
        </div>
      </div>

      {/* Character selector for journey view */}
      {viewMode === 'journey' && (
        <div className="p-4 bg-white border-b border-slate-ui">
          <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
            Select Character
          </label>
          <select
            value={selectedCharacter || ''}
            onChange={(e) => setSelectedCharacter(e.target.value || null)}
            className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
            style={{ borderRadius: '2px' }}
          >
            <option value="">Choose a character...</option>
            {charactersInTimeline.map((char) => (
              <option key={char!.id} value={char!.id}>
                {char!.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {viewMode === 'timeline' ? renderTimelineView() : renderJourneyView()}
      </div>
    </div>
  );
}
