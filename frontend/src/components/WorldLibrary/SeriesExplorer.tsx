/**
 * SeriesExplorer Component
 * Shows series within a world and allows navigation
 */

import { useState } from 'react';
import { useWorldStore } from '../../stores/worldStore';
import { toast } from '../../stores/toastStore';
import type { World, Series } from '../../types/world';

interface SeriesExplorerProps {
  world: World;
  series: Series[];
  onSelectSeries: (series: Series) => void;
  onBack?: () => void;
  isLoading: boolean;
}

export default function SeriesExplorer({
  world,
  series,
  onSelectSeries,
  isLoading,
}: SeriesExplorerProps) {
  const { createSeries } = useWorldStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSeriesName, setNewSeriesName] = useState('');
  const [newSeriesDescription, setNewSeriesDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleCreateSeries = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSeriesName.trim()) return;

    setIsCreating(true);
    try {
      const newSeries = await createSeries(world.id, {
        name: newSeriesName.trim(),
        description: newSeriesDescription.trim(),
      });
      toast.success(`Series "${newSeries.name}" created!`);
      setShowCreateModal(false);
      setNewSeriesName('');
      setNewSeriesDescription('');
      onSelectSeries(newSeries);
    } catch (err) {
      console.error('Failed to create series:', err);
      toast.error('Failed to create series');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-serif font-bold text-midnight mb-2">{world.name}</h2>
          <p className="text-faded-ink font-sans">
            {series.length === 0
              ? 'Create a series to organize your manuscripts'
              : `${series.length} ${series.length === 1 ? 'series' : 'series'}`}
          </p>
          {world.description && (
            <p className="text-faded-ink font-sans text-sm mt-2 max-w-2xl">
              {world.description}
            </p>
          )}
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
          style={{ borderRadius: '2px' }}
        >
          + New Series
        </button>
      </div>

      {/* World Settings Quick View */}
      {world.settings?.genre && (
        <div className="mb-6 flex items-center gap-4">
          <span className="px-3 py-1 bg-bronze/10 text-bronze font-sans text-sm font-medium rounded-sm">
            {world.settings.genre as string}
          </span>
        </div>
      )}

      {/* Series Grid */}
      {isLoading ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-4 text-bronze">&#x23F3;</div>
          <p className="text-faded-ink font-sans">Loading series...</p>
        </div>
      ) : series.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-6xl mb-6 text-bronze">&#x1F4DA;</div>
          <h3 className="text-2xl font-serif font-bold text-midnight mb-3">No Series Yet</h3>
          <p className="text-faded-ink font-sans mb-8 max-w-md mx-auto">
            A series groups related manuscripts together. Create a series like "Main Trilogy" or
            "Standalone Books".
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-8 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
            style={{ borderRadius: '2px' }}
          >
            Create Your First Series
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {series.map((s) => (
            <div
              key={s.id}
              className="bg-white border border-slate-ui p-6 hover:shadow-book transition-shadow cursor-pointer group"
              style={{ borderRadius: '2px' }}
              onClick={() => onSelectSeries(s)}
            >
              {/* Series Icon */}
              <div className="text-3xl mb-3 group-hover:scale-110 transition-transform">
                &#x1F4DA;
              </div>

              {/* Series Name */}
              <h3 className="text-xl font-serif font-bold text-midnight mb-2 group-hover:text-bronze transition-colors">
                {s.name}
              </h3>

              {/* Description */}
              {s.description && (
                <p className="text-sm font-sans text-faded-ink mb-3 line-clamp-2">
                  {s.description}
                </p>
              )}

              {/* Metadata */}
              <div className="text-sm font-sans text-faded-ink mb-4">
                <p>Updated {formatDate(s.updated_at)}</p>
              </div>

              {/* Action Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectSeries(s);
                }}
                className="w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                View Manuscripts
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create Series Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white p-8 max-w-lg w-full shadow-book"
            style={{ borderRadius: '2px' }}
          >
            <h3 className="text-2xl font-serif font-bold text-midnight mb-2">Create New Series</h3>
            <p className="text-faded-ink font-sans mb-6 text-sm">
              A series groups related manuscripts. For example: "The Dark Trilogy" or "Standalone
              Novels".
            </p>

            <form onSubmit={handleCreateSeries}>
              {/* Series Name */}
              <div className="mb-4">
                <label className="block text-sm font-sans font-medium text-midnight mb-2">
                  Series Name <span className="text-redline">*</span>
                </label>
                <input
                  type="text"
                  value={newSeriesName}
                  onChange={(e) => setNewSeriesName(e.target.value)}
                  placeholder="e.g., The Dark Trilogy"
                  className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight"
                  style={{ borderRadius: '2px' }}
                  autoFocus
                />
              </div>

              {/* Description */}
              <div className="mb-6">
                <label className="block text-sm font-sans font-medium text-midnight mb-2">
                  Description
                </label>
                <textarea
                  value={newSeriesDescription}
                  onChange={(e) => setNewSeriesDescription(e.target.value)}
                  placeholder="A brief description of this series..."
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight resize-none"
                  style={{ borderRadius: '2px' }}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewSeriesName('');
                    setNewSeriesDescription('');
                  }}
                  className="flex-1 px-6 py-3 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors"
                  style={{ borderRadius: '2px' }}
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50"
                  style={{ borderRadius: '2px' }}
                  disabled={isCreating || !newSeriesName.trim()}
                >
                  {isCreating ? 'Creating...' : 'Create Series'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
