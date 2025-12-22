/**
 * EntityList - Main entity management interface
 */

import { useState, useEffect } from 'react';
import type { Entity } from '@/types/codex';
import { EntityType } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import EntityCard from './EntityCard';
import EntityDetail from './EntityDetail';

interface EntityListProps {
  manuscriptId: string;
}

export default function EntityList({ manuscriptId }: EntityListProps) {
  const {
    entities,
    setEntities,
    removeEntity,
    updateEntity,
    selectedEntityId,
    setSelectedEntity,
  } = useCodexStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<EntityType | 'ALL'>('ALL');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);

  // Create form state
  const [newEntityName, setNewEntityName] = useState('');
  const [newEntityType, setNewEntityType] = useState<EntityType>(EntityType.CHARACTER);

  // Load entities on mount
  useEffect(() => {
    loadEntities();
  }, [manuscriptId]);

  const loadEntities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await codexApi.listEntities(manuscriptId);
      setEntities(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load entities');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEntity = async () => {
    if (!newEntityName.trim()) {
      setError('Entity name is required');
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const entity = await codexApi.createEntity({
        manuscript_id: manuscriptId,
        type: newEntityType,
        name: newEntityName.trim(),
      });

      // Add to store
      setEntities([...entities, entity]);

      // Reset form
      setNewEntityName('');
      setNewEntityType(EntityType.CHARACTER);
      setShowCreateForm(false);

      // Select new entity
      setSelectedEntity(entity.id);
    } catch (err) {
      setError('Failed to create entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteEntity = async (entityId: string) => {
    try {
      await codexApi.deleteEntity(entityId);
      removeEntity(entityId);
    } catch (err) {
      alert('Failed to delete entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleUpdateEntity = async (entityId: string, updates: Partial<Entity>) => {
    try {
      const updated = await codexApi.updateEntity(entityId, updates);
      updateEntity(entityId, updated);
    } catch (err) {
      alert('Failed to update entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  // Filter entities
  const filteredEntities = entities.filter((entity) =>
    filterType === 'ALL' ? true : entity.type === filterType
  );

  // Get selected entity
  const selectedEntity = selectedEntityId
    ? entities.find((e) => e.id === selectedEntityId)
    : null;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading entities...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-redline/10 border-l-4 border-redline p-3 text-sm font-sans text-redline">
          {error}
        </div>
        <button
          onClick={loadEntities}
          className="mt-2 text-sm font-sans text-bronze hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  // If entity is selected, show detail view
  if (selectedEntity) {
    return (
      <EntityDetail
        entity={selectedEntity}
        onUpdate={(updates) => handleUpdateEntity(selectedEntity.id, updates)}
        onClose={() => setSelectedEntity(null)}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Create Button */}
      <div className="p-4 border-b border-slate-ui">
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          + Create Entity
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="p-4 bg-white border-b border-slate-ui transition-opacity duration-300 ease-in-out">
          <h3 className="font-garamond font-semibold text-midnight mb-3">New Entity</h3>

          {error && (
            <div className="mb-3 bg-redline/10 border-l-4 border-redline p-2 text-xs font-sans text-redline">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                Name
              </label>
              <input
                type="text"
                value={newEntityName}
                onChange={(e) => {
                  setNewEntityName(e.target.value);
                  setError(null);
                }}
                placeholder="Enter entity name..."
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
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
                value={newEntityType}
                onChange={(e) => setNewEntityType(e.target.value as EntityType)}
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
                disabled={creating}
              >
                <option value={EntityType.CHARACTER}>Character</option>
                <option value={EntityType.LOCATION}>Location</option>
                <option value={EntityType.ITEM}>Item</option>
                <option value={EntityType.LORE}>Lore</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleCreateEntity}
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
                  setNewEntityName('');
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
      <div className="flex border-b border-slate-ui overflow-x-auto">
        {['ALL', ...Object.values(EntityType)].map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type as EntityType | 'ALL')}
            className={`
              px-4 py-2 text-sm font-sans whitespace-nowrap transition-colors
              ${filterType === type
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            {type}
            {type !== 'ALL' && (
              <span className="ml-1 text-xs">
                ({entities.filter((e) => e.type === type).length})
              </span>
            )}
            {type === 'ALL' && <span className="ml-1 text-xs">({entities.length})</span>}
          </button>
        ))}
      </div>

      {/* Entity List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredEntities.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="text-4xl mb-3">📝</div>
            <p className="text-midnight font-garamond font-semibold mb-2">
              No {filterType === 'ALL' ? 'entities' : filterType.toLowerCase() + 's'} yet
            </p>
            <p className="text-sm text-faded-ink font-sans max-w-xs">
              Create one manually or use the "Analyze" button to extract entities from your text
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEntities.map((entity) => (
              <EntityCard
                key={entity.id}
                entity={entity}
                isSelected={selectedEntityId === entity.id}
                onSelect={() => setSelectedEntity(entity.id)}
                onDelete={() => handleDeleteEntity(entity.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
