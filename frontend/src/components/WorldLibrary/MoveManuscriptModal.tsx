/**
 * MoveManuscriptModal - Move a manuscript to a different world/series
 */

import { useState, useEffect } from 'react';
import { useWorldStore } from '../../stores/worldStore';
import type { World, Series, MoveManuscriptResponse } from '../../types/world';

interface MoveManuscriptModalProps {
  manuscriptId: string;
  currentWorldId: string | null;
  onClose: () => void;
  onMoved: (result: MoveManuscriptResponse) => void;
}

export default function MoveManuscriptModal({
  manuscriptId,
  currentWorldId,
  onClose,
  onMoved,
}: MoveManuscriptModalProps) {
  const { worlds, fetchWorlds, fetchSeries, getSeriesForWorld, moveManuscriptToWorld } =
    useWorldStore();

  const [selectedWorldId, setSelectedWorldId] = useState<string | null>(null);
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
  const [isMoving, setIsMoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorlds();
  }, [fetchWorlds]);

  useEffect(() => {
    if (selectedWorldId) {
      fetchSeries(selectedWorldId);
    }
  }, [selectedWorldId, fetchSeries]);

  const seriesInSelectedWorld = selectedWorldId ? getSeriesForWorld(selectedWorldId) : [];
  const isCrossWorld = selectedWorldId && selectedWorldId !== currentWorldId;

  const handleMove = async () => {
    if (!selectedSeriesId) return;

    setIsMoving(true);
    setError(null);

    try {
      const result = await moveManuscriptToWorld(manuscriptId, selectedSeriesId);
      onMoved(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to move manuscript');
      setIsMoving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div
        className="bg-white max-w-lg w-full max-h-[80vh] overflow-hidden flex flex-col shadow-2xl"
        style={{ borderRadius: '2px' }}
      >
        {/* Header */}
        <div className="border-b border-slate-ui px-6 py-4">
          <h2 className="font-garamond text-xl font-bold text-midnight">Move Manuscript</h2>
          <p className="text-sm font-sans text-faded-ink mt-1">
            Choose a destination world and series
          </p>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* World Selection */}
          <div>
            <label className="block text-sm font-sans font-medium text-midnight mb-2">
              Destination World
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {worlds.map((world: World) => (
                <button
                  key={world.id}
                  onClick={() => {
                    setSelectedWorldId(world.id);
                    setSelectedSeriesId(null);
                  }}
                  className={`w-full text-left px-4 py-3 border transition-colors ${
                    selectedWorldId === world.id
                      ? 'border-bronze bg-bronze/5'
                      : 'border-slate-ui hover:border-bronze/50'
                  }`}
                  style={{ borderRadius: '2px' }}
                >
                  <div className="font-sans text-sm font-medium text-midnight">
                    {world.name}
                    {world.id === currentWorldId && (
                      <span className="ml-2 text-xs text-faded-ink">(current)</span>
                    )}
                  </div>
                  {world.description && (
                    <div className="text-xs font-sans text-faded-ink mt-1 truncate">
                      {world.description}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Series Selection */}
          {selectedWorldId && (
            <div>
              <label className="block text-sm font-sans font-medium text-midnight mb-2">
                Destination Series
              </label>
              {seriesInSelectedWorld.length === 0 ? (
                <p className="text-sm font-sans text-faded-ink">
                  No series in this world.
                </p>
              ) : (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {seriesInSelectedWorld.map((series: Series) => (
                    <button
                      key={series.id}
                      onClick={() => setSelectedSeriesId(series.id)}
                      className={`w-full text-left px-4 py-3 border transition-colors ${
                        selectedSeriesId === series.id
                          ? 'border-bronze bg-bronze/5'
                          : 'border-slate-ui hover:border-bronze/50'
                      }`}
                      style={{ borderRadius: '2px' }}
                    >
                      <div className="font-sans text-sm font-medium text-midnight">
                        {series.name}
                      </div>
                      {series.description && (
                        <div className="text-xs font-sans text-faded-ink mt-1 truncate">
                          {series.description}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Cross-world warning */}
          {isCrossWorld && selectedSeriesId && (
            <div className="p-4 bg-amber-50 border border-amber-200" style={{ borderRadius: '2px' }}>
              <div className="flex items-start gap-2">
                <span className="text-amber-600 text-lg">&#x26A0;</span>
                <div>
                  <p className="text-sm font-sans font-medium text-amber-800">
                    Cross-world move
                  </p>
                  <p className="text-xs font-sans text-amber-700 mt-1">
                    Wiki entries from this manuscript will be copied to the new world.
                    Duplicate entries will be merged. Character arcs and cross-references
                    will be updated.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-3 bg-redline/10 border border-redline text-sm font-sans text-redline" style={{ borderRadius: '2px' }}>
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-ui px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 font-sans text-sm text-faded-ink hover:text-midnight transition-colors"
            disabled={isMoving}
          >
            Cancel
          </button>
          <button
            onClick={handleMove}
            disabled={!selectedSeriesId || isMoving}
            className="px-6 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ borderRadius: '2px' }}
          >
            {isMoving ? 'Moving...' : 'Move'}
          </button>
        </div>
      </div>
    </div>
  );
}
