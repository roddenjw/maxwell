/**
 * MergeEntitiesModal - Modal for merging multiple entities into one
 * Supports both multi-select merge and single entity "merge with" flow
 */

import { useState, useMemo } from 'react';
import type { Entity } from '@/types/codex';
import { getEntityTypeIcon } from '@/types/codex';

interface MergeEntitiesModalProps {
  // Initial entity to merge (if using single-entity flow)
  sourceEntity?: Entity;
  // All entities to merge (if using multi-select flow)
  entities?: Entity[];
  // Available entities to pick from (for single-entity flow)
  availableEntities?: Entity[];
  onConfirm: (primaryEntityId: string, secondaryEntityIds: string[]) => Promise<void>;
  onCancel: () => void;
}

export default function MergeEntitiesModal({
  sourceEntity,
  entities: preselectedEntities,
  availableEntities = [],
  onConfirm,
  onCancel,
}: MergeEntitiesModalProps) {
  // Determine mode: single-entity or multi-select
  const isSingleEntityMode = !!sourceEntity && !preselectedEntities;

  // For single-entity mode: let user select target entity
  const [selectedTargetId, setSelectedTargetId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  // For multi-select mode: let user pick primary
  const [selectedPrimaryId, setSelectedPrimaryId] = useState<string>(
    preselectedEntities?.[0]?.id || sourceEntity?.id || ''
  );

  const [isMerging, setIsMerging] = useState(false);

  // Build the list of entities for merging
  const entitiesToMerge = useMemo(() => {
    if (isSingleEntityMode) {
      if (!selectedTargetId || !sourceEntity) return [];
      const target = availableEntities.find(e => e.id === selectedTargetId);
      return target ? [sourceEntity, target] : [];
    }
    return preselectedEntities || [];
  }, [isSingleEntityMode, selectedTargetId, sourceEntity, availableEntities, preselectedEntities]);

  // Filter available entities for search (exclude source entity)
  const filteredAvailable = useMemo(() => {
    if (!isSingleEntityMode) return [];
    return availableEntities
      .filter(e => e.id !== sourceEntity?.id)
      .filter(e => {
        if (!searchQuery) return true;
        const query = searchQuery.toLowerCase();
        return (
          e.name.toLowerCase().includes(query) ||
          e.aliases.some(a => a.toLowerCase().includes(query)) ||
          e.type.toLowerCase().includes(query)
        );
      })
      .slice(0, 20); // Limit for performance
  }, [isSingleEntityMode, availableEntities, sourceEntity, searchQuery]);

  const handleMerge = async () => {
    if (entitiesToMerge.length < 2) return;

    // Determine primary and secondary
    const primaryId = selectedPrimaryId || entitiesToMerge[0].id;
    const secondaryIds = entitiesToMerge
      .filter(e => e.id !== primaryId)
      .map(e => e.id);

    try {
      setIsMerging(true);
      await onConfirm(primaryId, secondaryIds);
    } catch (err) {
      console.error('Merge failed:', err);
    } finally {
      setIsMerging(false);
    }
  };

  const primaryEntity = entitiesToMerge.find(e => e.id === selectedPrimaryId);
  const secondaryEntities = entitiesToMerge.filter(e => e.id !== selectedPrimaryId);

  // Preview merged data
  const mergedPreview = useMemo(() => {
    if (!primaryEntity || secondaryEntities.length === 0) return null;

    const mergedAliases = new Set([
      ...(primaryEntity?.aliases || []),
      ...secondaryEntities.flatMap(e => [e.name, ...e.aliases])
    ]);

    return {
      aliasCount: mergedAliases.size,
      aliases: Array.from(mergedAliases).slice(0, 5),
    };
  }, [primaryEntity, secondaryEntities]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-vellum shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" style={{ borderRadius: '4px' }}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui bg-white">
          <h2 className="text-2xl font-garamond font-semibold text-midnight">
            {isSingleEntityMode ? 'Merge Entity' : 'Merge Entities'}
          </h2>
          <p className="text-sm font-sans text-faded-ink mt-1">
            {isSingleEntityMode
              ? `Select an entity to merge with "${sourceEntity?.name}"`
              : `Combine ${entitiesToMerge.length} entities into one. Select which entity should be the primary.`
            }
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Single-entity mode: Entity picker */}
          {isSingleEntityMode && (
            <div>
              <label className="block text-sm font-sans font-semibold text-midnight mb-3">
                Select Entity to Merge With
              </label>

              {/* Search input */}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search entities by name, alias, or type..."
                className="w-full px-3 py-2 border border-slate-ui text-sm font-sans mb-3 bg-white"
                style={{ borderRadius: '2px' }}
              />

              {/* Entity list */}
              <div className="space-y-2 max-h-[300px] overflow-y-auto border border-slate-ui p-2 bg-white" style={{ borderRadius: '2px' }}>
                {filteredAvailable.length === 0 ? (
                  <p className="text-sm font-sans text-faded-ink text-center py-4">
                    {searchQuery ? 'No matching entities found' : 'No other entities available'}
                  </p>
                ) : (
                  filteredAvailable.map((entity) => (
                    <label
                      key={entity.id}
                      className={`
                        flex items-start gap-3 p-3 border-2 cursor-pointer transition-colors
                        ${selectedTargetId === entity.id
                          ? 'border-bronze bg-bronze/5'
                          : 'border-slate-ui hover:border-bronze/50'
                        }
                      `}
                      style={{ borderRadius: '2px' }}
                    >
                      <input
                        type="radio"
                        name="target"
                        value={entity.id}
                        checked={selectedTargetId === entity.id}
                        onChange={(e) => {
                          setSelectedTargetId(e.target.value);
                          // Auto-select primary if not set
                          if (!selectedPrimaryId) {
                            setSelectedPrimaryId(sourceEntity?.id || '');
                          }
                        }}
                        className="mt-1"
                      />
                      <span className="text-xl">{getEntityTypeIcon(entity.type)}</span>
                      <div className="flex-1">
                        <div className="font-sans font-semibold text-midnight">
                          {entity.name}
                        </div>
                        <div className="text-xs font-sans text-faded-ink">
                          {entity.type}
                          {entity.aliases.length > 0 && (
                            <> • Aliases: {entity.aliases.slice(0, 3).join(', ')}{entity.aliases.length > 3 ? '...' : ''}</>
                          )}
                        </div>
                        {entity.attributes?.description && (
                          <div className="text-xs font-sans text-faded-ink mt-1 truncate">
                            {entity.attributes.description.slice(0, 80)}...
                          </div>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Show entities to merge */}
          {entitiesToMerge.length >= 2 && (
            <>
              {/* Primary Entity Selection */}
              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-3">
                  Choose Primary Entity (the one to keep)
                </label>
                <div className="space-y-2">
                  {entitiesToMerge.map((entity) => (
                    <label
                      key={entity.id}
                      className={`
                        flex items-start gap-3 p-3 border-2 cursor-pointer transition-colors
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
                      <span className="text-xl">{getEntityTypeIcon(entity.type)}</span>
                      <div className="flex-1">
                        <div className="font-sans font-semibold text-midnight">
                          {entity.name}
                        </div>
                        <div className="text-xs font-sans text-faded-ink">
                          {entity.type} • {entity.aliases.length} aliases
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
              {mergedPreview && (
                <div className="bg-white border border-slate-ui p-4" style={{ borderRadius: '2px' }}>
                  <h3 className="font-sans font-semibold text-midnight mb-3">
                    Merge Preview
                  </h3>

                  {/* What will be kept */}
                  <div className="mb-4">
                    <div className="text-sm font-sans font-semibold text-midnight mb-2">
                      Will Keep:
                    </div>
                    <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                      <li>Name: "{primaryEntity?.name}"</li>
                      <li>Type: {primaryEntity?.type}</li>
                    </ul>
                  </div>

                  {/* What will be merged */}
                  <div className="mb-4">
                    <div className="text-sm font-sans font-semibold text-midnight mb-2">
                      Will Merge:
                    </div>
                    <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                      <li>{mergedPreview.aliasCount} total aliases</li>
                      {mergedPreview.aliases.length > 0 && (
                        <li className="text-xs">
                          Preview: {mergedPreview.aliases.join(', ')}{mergedPreview.aliasCount > 5 ? '...' : ''}
                        </li>
                      )}
                    </ul>
                  </div>

                  {/* What will be deleted */}
                  <div>
                    <div className="text-sm font-sans font-semibold text-redline mb-2">
                      Will Delete:
                    </div>
                    <ul className="text-sm font-sans text-faded-ink space-y-1 ml-4">
                      {secondaryEntities.map((entity) => (
                        <li key={entity.id}>"{entity.name}" ({entity.type})</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Warning */}
              <div className="bg-amber-50 border-l-4 border-amber-400 p-3">
                <div className="flex items-start gap-2">
                  <span className="text-amber-600 text-lg">!</span>
                  <div className="text-sm font-sans text-amber-800">
                    <strong>Warning:</strong> This action cannot be undone. The deleted entities
                    will be permanently removed, and their data will be merged into "{primaryEntity?.name}".
                  </div>
                </div>
              </div>
            </>
          )}
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
            disabled={isMerging || entitiesToMerge.length < 2 || !selectedPrimaryId}
            className="px-4 py-2 bg-bronze text-white font-sans text-sm hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ borderRadius: '2px' }}
          >
            {isMerging ? 'Merging...' : `Merge Entities`}
          </button>
        </div>
      </div>
    </div>
  );
}
