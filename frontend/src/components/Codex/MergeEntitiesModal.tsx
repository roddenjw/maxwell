/**
 * MergeEntitiesModal - Modal for merging multiple entities into one
 */

import { useState } from 'react';
import type { Entity } from '@/types/codex';

interface MergeEntitiesModalProps {
  entities: Entity[];
  onConfirm: (primaryEntityId: string) => Promise<void>;
  onCancel: () => void;
}

export default function MergeEntitiesModal({
  entities,
  onConfirm,
  onCancel,
}: MergeEntitiesModalProps) {
  const [selectedPrimaryId, setSelectedPrimaryId] = useState<string>(entities[0]?.id || '');
  const [isMerging, setIsMerging] = useState(false);

  const handleMerge = async () => {
    if (!selectedPrimaryId) return;

    try {
      setIsMerging(true);
      await onConfirm(selectedPrimaryId);
    } catch (err) {
      console.error('Merge failed:', err);
    } finally {
      setIsMerging(false);
    }
  };

  const primaryEntity = entities.find(e => e.id === selectedPrimaryId);
  const otherEntities = entities.filter(e => e.id !== selectedPrimaryId);

  // Preview merged data
  const mergedAliases = new Set([
    ...(primaryEntity?.aliases || []),
    ...otherEntities.flatMap(e => [e.name, ...e.aliases])
  ]);

  const mergedAppearance = [
    ...(primaryEntity?.attributes?.appearance || []),
    ...otherEntities.flatMap(e => e.attributes?.appearance || [])
  ];

  const mergedPersonality = [
    ...(primaryEntity?.attributes?.personality || []),
    ...otherEntities.flatMap(e => e.attributes?.personality || [])
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-vellum rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui bg-white">
          <h2 className="text-2xl font-garamond font-semibold text-midnight">
            Merge Entities
          </h2>
          <p className="text-sm font-sans text-faded-ink mt-1">
            Combine {entities.length} entities into one. Select which entity should be the primary.
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Primary Entity Selection */}
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-3">
              Choose Primary Entity
            </label>
            <div className="space-y-2">
              {entities.map((entity) => (
                <label
                  key={entity.id}
                  className={`
                    flex items-start gap-3 p-3 border-2 rounded cursor-pointer transition-colors
                    ${selectedPrimaryId === entity.id
                      ? 'border-bronze bg-bronze/5'
                      : 'border-slate-ui hover:border-bronze/50'
                    }
                  `}
                  style={{ borderRadius: '2px' }}
                >
                  <input
                    type="radio"
                    name="primary"
                    value={entity.id}
                    checked={selectedPrimaryId === entity.id}
                    onChange={(e) => setSelectedPrimaryId(e.target.value)}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-sans font-semibold text-midnight">
                      {entity.name}
                    </div>
                    <div className="text-xs font-sans text-faded-ink">
                      {entity.type} • {entity.aliases.length} aliases • {' '}
                      {entity.attributes?.appearance?.length || 0} appearance notes
                    </div>
                    {entity.aliases.length > 0 && (
                      <div className="text-xs font-sans text-faded-ink mt-1">
                        Aliases: {entity.aliases.join(', ')}
                      </div>
                    )}
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Merge Preview */}
          <div className="bg-white border border-slate-ui p-4" style={{ borderRadius: '2px' }}>
            <h3 className="font-sans font-semibold text-midnight mb-3">
              Merge Preview
            </h3>

            {/* What will be kept */}
            <div className="mb-4">
              <div className="text-sm font-sans font-semibold text-midnight mb-2">
                ✓ Will Keep:
              </div>
              <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                <li>• Name: "{primaryEntity?.name}"</li>
                <li>• Type: {primaryEntity?.type}</li>
                <li>• ID: {primaryEntity?.id.substring(0, 8)}...</li>
              </ul>
            </div>

            {/* What will be merged */}
            <div className="mb-4">
              <div className="text-sm font-sans font-semibold text-midnight mb-2">
                ↓ Will Merge In:
              </div>
              <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                <li>• {mergedAliases.size} total aliases (from all entities)</li>
                <li>• {mergedAppearance.length} appearance notes</li>
                <li>• {mergedPersonality.length} personality notes</li>
              </ul>
            </div>

            {/* What will be deleted */}
            <div>
              <div className="text-sm font-sans font-semibold text-redline mb-2">
                ✕ Will Delete:
              </div>
              <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                {otherEntities.map((entity) => (
                  <li key={entity.id}>• "{entity.name}" ({entity.type})</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-amber-50 border-l-4 border-amber-400 p-3">
            <div className="flex items-start gap-2">
              <span className="text-amber-600 text-lg">⚠️</span>
              <div className="text-sm font-sans text-amber-800">
                <strong>Warning:</strong> This action cannot be undone. The deleted entities
                will be permanently removed, and their data will be merged into "{primaryEntity?.name}".
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-ui bg-white flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isMerging}
            className="px-4 py-2 bg-slate-ui text-midnight font-sans text-sm hover:bg-slate-ui/80 disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleMerge}
            disabled={isMerging || !selectedPrimaryId}
            className="px-4 py-2 bg-bronze text-white font-sans text-sm hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ borderRadius: '2px' }}
          >
            {isMerging ? 'Merging...' : `Merge ${entities.length} Entities`}
          </button>
        </div>
      </div>
    </div>
  );
}
