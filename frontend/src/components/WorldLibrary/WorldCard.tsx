/**
 * WorldCard Component
 * Displays a single world in the library grid
 */

import type { World } from '../../types/world';

interface WorldCardProps {
  world: World;
  onSelect: () => void;
}

export default function WorldCard({ world, onSelect }: WorldCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Get genre from settings
  const genre = world.settings?.genre as string | undefined;

  return (
    <div
      className="bg-white border border-slate-ui p-6 hover:shadow-book transition-shadow cursor-pointer group"
      style={{ borderRadius: '2px' }}
      onClick={onSelect}
    >
      {/* World Icon */}
      <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">
        &#x1F30D;
      </div>

      {/* World Name */}
      <h3 className="text-xl font-serif font-bold text-midnight mb-2 group-hover:text-bronze transition-colors">
        {world.name}
      </h3>

      {/* Description */}
      {world.description && (
        <p className="text-sm font-sans text-faded-ink mb-3 line-clamp-2">
          {world.description}
        </p>
      )}

      {/* Metadata */}
      <div className="space-y-1 text-sm font-sans text-faded-ink mb-4">
        {genre && <p className="font-medium text-bronze">{genre}</p>}
        <p>Updated {formatDate(world.updated_at)}</p>
      </div>

      {/* Action Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
        className="w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
        style={{ borderRadius: '2px' }}
      >
        Explore World
      </button>
    </div>
  );
}
