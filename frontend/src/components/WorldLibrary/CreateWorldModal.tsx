/**
 * CreateWorldModal Component
 * Modal for creating a new world
 */

import { useState } from 'react';
import { useWorldStore } from '../../stores/worldStore';
import type { World, WorldSettings } from '../../types/world';

interface CreateWorldModalProps {
  onClose: () => void;
  onCreated: (world: World) => void;
}

const GENRE_OPTIONS = [
  'Fantasy',
  'Science Fiction',
  'Mystery',
  'Romance',
  'Thriller',
  'Horror',
  'Literary Fiction',
  'Historical Fiction',
  'Young Adult',
  'Other',
];

export default function CreateWorldModal({ onClose, onCreated }: CreateWorldModalProps) {
  const { createWorld, isLoading } = useWorldStore();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [genre, setGenre] = useState('');
  const [customGenre, setCustomGenre] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('World name is required');
      return;
    }

    try {
      const settings: WorldSettings = {};
      const selectedGenre = genre === 'Other' ? customGenre : genre;
      if (selectedGenre) {
        settings.genre = selectedGenre;
      }

      const world = await createWorld({
        name: name.trim(),
        description: description.trim(),
        settings,
      });

      onCreated(world);
      onClose();
    } catch (err) {
      console.error('Failed to create world:', err);
      setError(err instanceof Error ? err.message : 'Failed to create world');
    }
  };

  return (
    <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div
        className="bg-white p-8 max-w-lg w-full shadow-book"
        style={{ borderRadius: '2px' }}
      >
        <h3 className="text-2xl font-serif font-bold text-midnight mb-2">Create New World</h3>
        <p className="text-faded-ink font-sans mb-6 text-sm">
          A world is a shared universe for your manuscripts. Characters, locations, and lore can be
          shared across all books in the same world.
        </p>

        <form onSubmit={handleSubmit}>
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-redline/10 border border-redline rounded-sm">
              <p className="text-redline text-sm font-sans">{error}</p>
            </div>
          )}

          {/* World Name */}
          <div className="mb-4">
            <label className="block text-sm font-sans font-medium text-midnight mb-2">
              World Name <span className="text-redline">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., The Realm of Shadows"
              className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight"
              style={{ borderRadius: '2px' }}
              autoFocus
            />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-sans font-medium text-midnight mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="A brief description of your world..."
              rows={3}
              className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight resize-none"
              style={{ borderRadius: '2px' }}
            />
          </div>

          {/* Genre */}
          <div className="mb-6">
            <label className="block text-sm font-sans font-medium text-midnight mb-2">Genre</label>
            <select
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight bg-white"
              style={{ borderRadius: '2px' }}
            >
              <option value="">Select a genre (optional)</option>
              {GENRE_OPTIONS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            {genre === 'Other' && (
              <input
                type="text"
                value={customGenre}
                onChange={(e) => setCustomGenre(e.target.value)}
                placeholder="Enter custom genre"
                className="w-full mt-2 px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight"
                style={{ borderRadius: '2px' }}
              />
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50"
              style={{ borderRadius: '2px' }}
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create World'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
