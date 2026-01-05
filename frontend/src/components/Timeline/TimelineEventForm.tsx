/**
 * TimelineEventForm - Create/edit events with prerequisite selection
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { EventType } from '@/types/timeline';
import type { TimelineEvent } from '@/types/timeline';

interface TimelineEventFormProps {
  manuscriptId: string;
  eventToEdit?: TimelineEvent | null;
  onSave: () => void;
  onCancel: () => void;
}

export default function TimelineEventForm({
  manuscriptId,
  eventToEdit,
  onSave,
  onCancel,
}: TimelineEventFormProps) {
  const { addEvent, updateEvent, events } = useTimelineStore();
  const { entities } = useCodexStore();

  const [description, setDescription] = useState('');
  const [eventType, setEventType] = useState<EventType>(EventType.SCENE);
  const [orderIndex, setOrderIndex] = useState(0);
  const [timestamp, setTimestamp] = useState('');
  const [locationId, setLocationId] = useState('');
  const [characterIds, setCharacterIds] = useState<string[]>([]);
  const [narrativeImportance, setNarrativeImportance] = useState(5);
  const [prerequisiteIds, setPrerequisiteIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  // Populate form if editing
  useEffect(() => {
    if (eventToEdit) {
      setDescription(eventToEdit.description);
      setEventType(eventToEdit.event_type);
      setOrderIndex(eventToEdit.order_index);
      setTimestamp(eventToEdit.timestamp || '');
      setLocationId(eventToEdit.location_id || '');
      setCharacterIds(eventToEdit.character_ids);
      setNarrativeImportance(eventToEdit.narrative_importance || 5);
      setPrerequisiteIds(eventToEdit.prerequisite_ids || []);
    } else {
      // Default order index for new events
      const maxIndex = events.length > 0 ? Math.max(...events.map((e) => e.order_index)) : -1;
      setOrderIndex(maxIndex + 1);
    }
  }, [eventToEdit, events]);

  const locations = entities.filter((e) => e.type === 'LOCATION');
  const characters = entities.filter((e) => e.type === 'CHARACTER');

  // Only show events that could be prerequisites (before this event)
  const availablePrerequisites = events
    .filter((e) => e.id !== eventToEdit?.id && e.order_index < orderIndex)
    .sort((a, b) => a.order_index - b.order_index);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!description.trim()) {
      alert('Please enter a description');
      return;
    }

    try {
      setSaving(true);

      const eventData: Partial<TimelineEvent> = {
        manuscript_id: manuscriptId,
        description: description.trim(),
        event_type: eventType,
        order_index: orderIndex,
        timestamp: timestamp || null,
        location_id: locationId || null,
        character_ids: characterIds,
        narrative_importance: narrativeImportance,
        prerequisite_ids: prerequisiteIds,
        event_metadata: {},
      };

      if (eventToEdit) {
        updateEvent(eventToEdit.id, { ...eventToEdit, ...eventData } as TimelineEvent);
      } else {
        addEvent({
          id: crypto.randomUUID(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          ...eventData,
        } as TimelineEvent);
      }

      onSave();
    } catch (error) {
      console.error('Failed to save event:', error);
      alert('Failed to save event: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full bg-vellum">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white flex items-center justify-between">
        <h3 className="text-lg font-garamond font-bold text-midnight">
          {eventToEdit ? 'Edit Event' : 'New Event'}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
        >
          ×
        </button>
      </div>

      {/* Form Fields */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Description */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Description *
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What happens in this event?"
            className="w-full border border-slate-ui p-2 text-sm font-serif text-midnight resize-none"
            style={{ borderRadius: '2px' }}
            rows={3}
            required
          />
        </div>

        {/* Event Type */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Event Type
          </label>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value as EventType)}
            className="w-full border border-slate-ui p-2 text-sm font-sans text-midnight"
            style={{ borderRadius: '2px' }}
          >
            {Object.values(EventType).map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        {/* Order Index & Narrative Importance */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Order Index
            </label>
            <input
              type="number"
              value={orderIndex}
              onChange={(e) => setOrderIndex(parseInt(e.target.value))}
              className="w-full border border-slate-ui p-2 text-sm font-sans text-midnight"
              style={{ borderRadius: '2px' }}
              min={0}
            />
            <p className="text-xs text-faded-ink font-sans mt-1">Position in timeline</p>
          </div>

          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Importance (1-10)
            </label>
            <input
              type="number"
              value={narrativeImportance}
              onChange={(e) => setNarrativeImportance(parseInt(e.target.value))}
              className="w-full border border-slate-ui p-2 text-sm font-sans text-midnight"
              style={{ borderRadius: '2px' }}
              min={1}
              max={10}
            />
            <p className="text-xs text-faded-ink font-sans mt-1">Narrative weight</p>
          </div>
        </div>

        {/* Timestamp */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Timestamp (optional)
          </label>
          <input
            type="text"
            value={timestamp}
            onChange={(e) => setTimestamp(e.target.value)}
            placeholder="e.g., Day 1, Morning or 2024-01-15 09:00"
            className="w-full border border-slate-ui p-2 text-sm font-sans text-midnight"
            style={{ borderRadius: '2px' }}
          />
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Location (optional)
          </label>
          <select
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            className="w-full border border-slate-ui p-2 text-sm font-sans text-midnight"
            style={{ borderRadius: '2px' }}
          >
            <option value="">-- None --</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Characters */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Characters (optional)
          </label>
          <div className="border border-slate-ui p-2 max-h-32 overflow-y-auto" style={{ borderRadius: '2px' }}>
            {characters.length === 0 ? (
              <p className="text-xs text-faded-ink font-sans">No characters available</p>
            ) : (
              characters.map((char) => (
                <label key={char.id} className="flex items-center gap-2 py-1 hover:bg-vellum cursor-pointer">
                  <input
                    type="checkbox"
                    checked={characterIds.includes(char.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setCharacterIds([...characterIds, char.id]);
                      } else {
                        setCharacterIds(characterIds.filter((id) => id !== char.id));
                      }
                    }}
                    className="text-bronze"
                  />
                  <span className="text-sm font-sans text-midnight">{char.name}</span>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Prerequisites */}
        <div>
          <label className="block text-sm font-sans font-semibold text-midnight mb-1">
            Prerequisites (optional)
          </label>
          <p className="text-xs text-faded-ink font-sans mb-2">
            Events that must occur before this one (causality tracking)
          </p>
          <div className="border border-slate-ui p-2 max-h-40 overflow-y-auto" style={{ borderRadius: '2px' }}>
            {availablePrerequisites.length === 0 ? (
              <p className="text-xs text-faded-ink font-sans">No earlier events available</p>
            ) : (
              availablePrerequisites.map((prereq) => (
                <label key={prereq.id} className="flex items-start gap-2 py-1 hover:bg-vellum cursor-pointer">
                  <input
                    type="checkbox"
                    checked={prerequisiteIds.includes(prereq.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setPrerequisiteIds([...prerequisiteIds, prereq.id]);
                      } else {
                        setPrerequisiteIds(prerequisiteIds.filter((id) => id !== prereq.id));
                      }
                    }}
                    className="mt-0.5 text-bronze"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-sans text-midnight">
                      #{prereq.order_index + 1}: {prereq.description.slice(0, 50)}
                      {prereq.description.length > 50 ? '...' : ''}
                    </span>
                  </div>
                </label>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-ui bg-white flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-sans text-faded-ink hover:text-midnight transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          {saving ? 'Saving...' : eventToEdit ? 'Save Changes' : 'Create Event'}
        </button>
      </div>
    </form>
  );
}
