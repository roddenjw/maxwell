/**
 * EventList - Main event browsing interface
 */

import { useState, useEffect } from 'react';
import { EventType } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';
import EventCard from './EventCard';
import EventDetail from './EventDetail';

interface EventListProps {
  manuscriptId: string;
}

export default function EventList({ manuscriptId }: EventListProps) {
  const {
    events,
    setEvents,
    selectedEventId,
    setSelectedEvent,
  } = useTimelineStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<EventType | 'ALL'>('ALL');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Create form state
  const [newEventDesc, setNewEventDesc] = useState('');
  const [newEventType, setNewEventType] = useState<EventType>(EventType.SCENE);
  const [newEventTimestamp, setNewEventTimestamp] = useState('');

  // Load events on mount
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

  const handleCreateEvent = async () => {
    if (!newEventDesc.trim()) {
      setError('Event description is required');
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const event = await timelineApi.createEvent({
        manuscript_id: manuscriptId,
        description: newEventDesc.trim(),
        event_type: newEventType,
        timestamp: newEventTimestamp.trim() || undefined,
      });

      // Add to store
      setEvents([...events, event]);

      // Reset form
      setNewEventDesc('');
      setNewEventType(EventType.SCENE);
      setNewEventTimestamp('');
      setShowCreateForm(false);

      // Select new event
      setSelectedEvent(event.id);
    } catch (err) {
      setError('Failed to create event: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!confirm('Delete this event? This cannot be undone.')) {
      return;
    }

    try {
      await timelineApi.deleteEvent(eventId);
      setEvents(events.filter((e) => e.id !== eventId));
      if (selectedEventId === eventId) {
        setSelectedEvent(null);
      }
    } catch (err) {
      alert('Failed to delete event: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleExtractTimeline = async () => {
    if (!confirm('This will analyze your manuscript and automatically create timeline events. Continue?')) {
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);

      // For now, use a sample text. In production, this would come from the editor
      const sampleText = "Your manuscript text here...";

      await timelineApi.analyzeTimeline({
        manuscript_id: manuscriptId,
        text: sampleText,
      });

      // Show success message
      alert('Timeline analysis started! Events will be created automatically in the background. Refresh to see results.');

      // Reload events after a short delay to allow background processing
      setTimeout(() => {
        loadEvents();
      }, 3000);
    } catch (err) {
      setError('Failed to analyze timeline: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setAnalyzing(false);
    }
  };

  // Filter events by type
  const filteredEvents = events.filter((event) => {
    return filterType === 'ALL' || event.event_type === filterType;
  });

  // Sort by order_index
  const sortedEvents = [...filteredEvents].sort((a, b) => a.order_index - b.order_index);

  // Get selected event
  const selectedEvent = selectedEventId
    ? events.find((e) => e.id === selectedEventId)
    : null;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading timeline...</p>
      </div>
    );
  }

  if (error && events.length === 0) {
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

  // If event is selected, show detail view
  if (selectedEvent) {
    return (
      <EventDetail
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onUpdate={loadEvents}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Create and Extract Buttons */}
      <div className="p-4 border-b border-slate-ui space-y-2">
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          + Create Event
        </button>
        <button
          onClick={handleExtractTimeline}
          disabled={analyzing}
          className="w-full bg-white border border-bronze text-bronze px-4 py-2 text-sm font-sans hover:bg-bronze/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ borderRadius: '2px' }}
        >
          {analyzing && <div className="w-4 h-4 border-2 border-bronze border-t-transparent rounded-full animate-spin"></div>}
          {analyzing ? 'Analyzing...' : '🔍 Extract Timeline'}
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="p-4 bg-white border-b border-slate-ui">
          <h3 className="font-garamond font-semibold text-midnight mb-3">New Event</h3>

          {error && (
            <div className="mb-3 bg-redline/10 border-l-4 border-redline p-2 text-xs font-sans text-redline">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                Description
              </label>
              <textarea
                value={newEventDesc}
                onChange={(e) => {
                  setNewEventDesc(e.target.value);
                  setError(null);
                }}
                placeholder="What happens in this event?"
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif min-h-[80px]"
                style={{ borderRadius: '2px' }}
                autoFocus
                disabled={creating}
              />
            </div>

            <div>
              <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                Type
              </label>
              <select
                value={newEventType}
                onChange={(e) => setNewEventType(e.target.value as EventType)}
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
                disabled={creating}
              >
                <option value={EventType.SCENE}>Scene</option>
                <option value={EventType.CHAPTER}>Chapter</option>
                <option value={EventType.FLASHBACK}>Flashback</option>
                <option value={EventType.DREAM}>Dream</option>
                <option value={EventType.MONTAGE}>Montage</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                Timestamp (optional)
              </label>
              <input
                type="text"
                value={newEventTimestamp}
                onChange={(e) => setNewEventTimestamp(e.target.value)}
                placeholder="e.g., Day 3, Morning"
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
                disabled={creating}
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleCreateEvent}
                disabled={creating}
                className="flex-1 bg-bronze text-white px-3 py-2 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                style={{ borderRadius: '2px' }}
              >
                {creating && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewEventDesc('');
                  setNewEventTimestamp('');
                  setError(null);
                }}
                disabled={creating}
                className="flex-1 bg-slate-ui text-midnight px-3 py-2 text-sm font-sans hover:bg-slate-ui/80 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-ui overflow-x-auto bg-white">
        {['ALL', ...Object.values(EventType)].map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type as EventType | 'ALL')}
            className={`
              px-4 py-2 text-sm font-sans whitespace-nowrap transition-colors
              ${filterType === type
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            {type}
            <span className="ml-1 text-xs">
              ({type === 'ALL' ? events.length : events.filter((e) => e.event_type === type).length})
            </span>
          </button>
        ))}
      </div>

      {/* Event List */}
      <div className="flex-1 overflow-y-auto p-4">
        {sortedEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="text-4xl mb-3">🎬</div>
            <p className="text-midnight font-garamond font-semibold mb-2">
              No {filterType === 'ALL' ? 'events' : filterType.toLowerCase() + 's'} yet
            </p>
            <p className="text-sm text-faded-ink font-sans max-w-xs">
              Create events manually or use the "Extract Timeline" button to analyze your manuscript
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedEvents.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                isSelected={selectedEventId === event.id}
                onSelect={() => setSelectedEvent(event.id)}
                onDelete={() => handleDeleteEvent(event.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
