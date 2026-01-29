/**
 * EventDetail - Detailed view and editing for selected event
 */

import { useState } from 'react';
import type { TimelineEvent } from '@/types/timeline';
import { EventType, getEventTypeColor, getEventTypeIcon } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import { useTimelineStore } from '@/stores/timelineStore';

interface EventDetailProps {
  event: TimelineEvent;
  onClose: () => void;
  onUpdate: () => void;
}

export default function EventDetail({
  event,
  onClose,
  onUpdate,
}: EventDetailProps) {
  const { entities } = useCodexStore();
  const { updateEvent: updateEventInStore } = useTimelineStore();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [editedDesc, setEditedDesc] = useState(event.description);
  const [editedType, setEditedType] = useState(event.event_type);
  const [editedTimestamp, setEditedTimestamp] = useState(event.timestamp || '');
  const [editedLocationId, setEditedLocationId] = useState(event.location_id || '');
  const [editedCharacterIds, setEditedCharacterIds] = useState<string[]>(event.character_ids);

  const typeColor = getEventTypeColor(isEditing ? editedType : event.event_type);
  const typeIcon = getEventTypeIcon(isEditing ? editedType : event.event_type);

  // Get location and character entities
  const location = event.location_id
    ? entities.find((e) => e.id === event.location_id)
    : null;

  const characters = event.character_ids
    .map((id) => entities.find((e) => e.id === id))
    .filter(Boolean);

  // Available locations and characters
  const availableLocations = entities.filter((e) => e.type === 'LOCATION');
  const availableCharacters = entities.filter((e) => e.type === 'CHARACTER');

  const handleSave = async () => {
    try {
      setSaving(true);

      const updatedEvent = await timelineApi.updateEvent(event.id, {
        description: editedDesc,
        event_type: editedType,
        timestamp: editedTimestamp || undefined,
        location_id: editedLocationId || undefined,
        character_ids: editedCharacterIds,
      });

      // Update local store with the response from API
      updateEventInStore(event.id, updatedEvent);

      setIsEditing(false);
      onUpdate();
    } catch (err) {
      alert('Failed to update event: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedDesc(event.description);
    setEditedType(event.event_type);
    setEditedTimestamp(event.timestamp || '');
    setEditedLocationId(event.location_id || '');
    setEditedCharacterIds(event.character_ids);
    setIsEditing(false);
  };

  const toggleCharacter = (characterId: string) => {
    if (editedCharacterIds.includes(characterId)) {
      setEditedCharacterIds(editedCharacterIds.filter((id) => id !== characterId));
    } else {
      setEditedCharacterIds([...editedCharacterIds, characterId]);
    }
  };

  return (
    <div className="bg-vellum h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-slate-ui p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{typeIcon}</span>
          <div>
            {isEditing ? (
              <select
                value={editedType}
                onChange={(e) => setEditedType(e.target.value as EventType)}
                className="bg-white border border-slate-ui px-2 py-1 text-sm font-sans"
                style={{ borderRadius: '2px' }}
              >
                <option value={EventType.SCENE}>Scene</option>
                <option value={EventType.CHAPTER}>Chapter</option>
                <option value={EventType.FLASHBACK}>Flashback</option>
                <option value={EventType.DREAM}>Dream</option>
                <option value={EventType.MONTAGE}>Montage</option>
              </select>
            ) : (
              <>
                <span
                  className="inline-block px-2 py-0.5 text-xs font-sans text-white"
                  style={{
                    backgroundColor: typeColor,
                    borderRadius: '2px',
                  }}
                >
                  {event.event_type}
                </span>
                <span className="ml-2 text-sm text-faded-ink font-sans">
                  Event #{event.order_index + 1}
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50"
                style={{ borderRadius: '2px' }}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={handleCancel}
                disabled={saving}
                className="bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80 disabled:opacity-50"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90"
              style={{ borderRadius: '2px' }}
            >
              Edit
            </button>
          )}
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Description */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Description
          </label>
          {isEditing ? (
            <textarea
              value={editedDesc}
              onChange={(e) => setEditedDesc(e.target.value)}
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif min-h-[120px]"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-serif text-midnight whitespace-pre-wrap">
              {event.description}
            </p>
          )}
        </div>

        {/* Timestamp */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Timestamp
          </label>
          {isEditing ? (
            <input
              type="text"
              value={editedTimestamp}
              onChange={(e) => setEditedTimestamp(e.target.value)}
              placeholder="e.g., Day 3, Morning"
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-sans text-midnight">
              {event.timestamp || 'None'}
            </p>
          )}
        </div>

        {/* Location */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Location
          </label>
          {isEditing ? (
            <select
              value={editedLocationId}
              onChange={(e) => setEditedLocationId(e.target.value)}
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
              style={{ borderRadius: '2px' }}
            >
              <option value="">None</option>
              {availableLocations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-sm font-sans text-midnight">
              {location ? location.name : 'None'}
            </p>
          )}
        </div>

        {/* Characters */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
            Characters Involved
          </label>
          {isEditing ? (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableCharacters.map((char) => (
                <label key={char.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editedCharacterIds.includes(char.id)}
                    onChange={() => toggleCharacter(char.id)}
                    className="w-4 h-4 text-bronze"
                  />
                  <span className="text-sm font-sans text-midnight">{char.name}</span>
                </label>
              ))}
              {availableCharacters.length === 0 && (
                <p className="text-sm text-faded-ink font-sans">
                  No characters in Codex. Create characters first.
                </p>
              )}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {characters.length > 0 ? (
                characters.map((char) => (
                  <span
                    key={char!.id}
                    className="px-2 py-1 bg-white border border-slate-ui text-xs font-sans text-midnight"
                    style={{ borderRadius: '2px' }}
                  >
                    {char!.name}
                  </span>
                ))
              ) : (
                <p className="text-sm text-faded-ink font-sans">None</p>
              )}
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="pt-4 border-t border-slate-ui">
          <p className="text-xs text-faded-ink font-sans">
            Created: {new Date(event.created_at).toLocaleString()}
          </p>
          <p className="text-xs text-faded-ink font-sans">
            Updated: {new Date(event.updated_at).toLocaleString()}
          </p>
          {event.event_metadata?.word_count && (
            <p className="text-xs text-faded-ink font-sans">
              Word count: {event.event_metadata.word_count}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
