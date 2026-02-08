/**
 * WikiEntryEditor Component
 * Editor for creating and editing wiki entries
 */

import { useState, useEffect } from 'react';
import type {
  WikiEntry,
  WikiEntryType,
  WikiEntryCreate,
  WikiEntryUpdate,
} from '../../types/wiki';
import { WIKI_ENTRY_TYPE_INFO } from '../../types/wiki';
import { cultureApi } from '../../lib/api';

const ENTRY_TYPES: WikiEntryType[] = [
  'character',
  'location',
  'magic_system',
  'world_rule',
  'artifact',
  'creature',
  'faction',
  'event',
  'theme',
  'culture',
  'religion',
  'technology',
];

interface WikiEntryEditorProps {
  entry: WikiEntry | null;
  worldId: string;
  onSave: (data: WikiEntryCreate | WikiEntryUpdate) => Promise<void>;
  onClose: () => void;
}

export function WikiEntryEditor({
  entry,
  worldId,
  onSave,
  onClose,
}: WikiEntryEditorProps) {
  const [title, setTitle] = useState(entry?.title || '');
  const [entryType, setEntryType] = useState<WikiEntryType>(
    entry?.entry_type || 'character'
  );
  const [summary, setSummary] = useState(entry?.summary || '');
  const [content, setContent] = useState(entry?.content || '');
  const [aliases, setAliases] = useState<string[]>(entry?.aliases || []);
  const [tags, setTags] = useState<string[]>(entry?.tags || []);
  const [newAlias, setNewAlias] = useState('');
  const [newTag, setNewTag] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parentCultureId, setParentCultureId] = useState<string>(entry?.parent_id || '');
  const [availableCultures, setAvailableCultures] = useState<Array<{ id: string; title: string }>>([]);

  const isEditing = !!entry;

  // Load cultures for parent culture dropdown
  useEffect(() => {
    cultureApi.getWorldCultures(worldId)
      .then((cultures: any[]) => setAvailableCultures(cultures.map(c => ({ id: c.id, title: c.title }))))
      .catch(() => setAvailableCultures([]));
  }, [worldId]);

  const handleAddAlias = () => {
    if (newAlias.trim() && !aliases.includes(newAlias.trim())) {
      setAliases([...aliases, newAlias.trim()]);
      setNewAlias('');
    }
  };

  const handleRemoveAlias = (alias: string) => {
    setAliases(aliases.filter((a) => a !== alias));
  };

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      if (isEditing) {
        const updates: WikiEntryUpdate = {
          title: title.trim(),
          summary: summary.trim() || undefined,
          content: content.trim() || undefined,
          aliases: aliases.length > 0 ? aliases : undefined,
          tags: tags.length > 0 ? tags : undefined,
          parent_id: parentCultureId || undefined,
        };
        await onSave(updates);
      } else {
        const data: WikiEntryCreate = {
          world_id: worldId,
          entry_type: entryType,
          title: title.trim(),
          summary: summary.trim() || undefined,
          content: content.trim() || undefined,
          aliases: aliases.length > 0 ? aliases : undefined,
          tags: tags.length > 0 ? tags : undefined,
          parent_id: parentCultureId || undefined,
        };
        await onSave(data);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            {isEditing ? 'Edit Wiki Entry' : 'New Wiki Entry'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Entry Type (only for new entries) */}
            {!isEditing && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Entry Type
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {ENTRY_TYPES.map((type) => {
                    const info = WIKI_ENTRY_TYPE_INFO[type];
                    return (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setEntryType(type)}
                        className={`
                          p-2 rounded border text-center transition-all
                          ${entryType === type
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                            : 'border-gray-200 hover:border-gray-300'
                          }
                        `}
                      >
                        <span className="text-xl block mb-1">{info.icon}</span>
                        <span className="text-xs text-gray-600">{info.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter entry title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>

            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Summary
              </label>
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="Brief summary of this entry..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Detailed content (supports markdown)..."
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              />
            </div>

            {/* Aliases */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Aliases
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newAlias}
                  onChange={(e) => setNewAlias(e.target.value)}
                  placeholder="Add alias..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddAlias();
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddAlias}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Add
                </button>
              </div>
              {aliases.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {aliases.map((alias, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded"
                    >
                      {alias}
                      <button
                        type="button"
                        onClick={() => handleRemoveAlias(alias)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="Add tag..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Add
                </button>
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Parent Culture (for non-culture entry types) */}
            {entryType !== 'culture' && availableCultures.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Parent Culture
                  <span className="text-xs text-gray-400 ml-1">(optional)</span>
                </label>
                <select
                  value={parentCultureId}
                  onChange={(e) => setParentCultureId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">None</option>
                  {availableCultures.map((c) => (
                    <option key={c.id} value={c.id}>
                      🎭 {c.title}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Organize this entry under a culture
                </p>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
                {error}
              </div>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving || !title.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Entry'}
          </button>
        </div>
      </div>
    </div>
  );
}
