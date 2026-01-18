/**
 * EntityList - Main entity management interface
 */

import { useState, useEffect } from 'react';

import type { Entity } from '@/types/codex';

import EntityCard from './EntityCard';
import EntityDetail from './EntityDetail';
import MergeEntitiesModal from './MergeEntitiesModal';
import EntityTemplateWizard from './EntityTemplateWizard';

import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { EntityType, TemplateType } from '@/types/codex';

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
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedEntityIds, setSelectedEntityIds] = useState<Set<string>>(new Set());
  const [showMergeModal, setShowMergeModal] = useState(false);

  // Create form state (for quick create)
  const [newEntityName, setNewEntityName] = useState('');
  const [newEntityType, setNewEntityType] = useState<EntityType>(EntityType.CHARACTER);

  // Brainstorming
  const { openModal } = useBrainstormStore();

  const handleBrainstorm = () => {
    openModal(manuscriptId, undefined, 'character');
  };

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

  const handleWizardComplete = async (entityData: {
    name: string;
    type: EntityType;
    template_type: TemplateType;
    template_data: any;
    aliases: string[];
  }) => {
    try {
      setCreating(true);
      setError(null);

      const entity = await codexApi.createEntity({
        manuscript_id: manuscriptId,
        type: entityData.type,
        name: entityData.name,
        aliases: entityData.aliases,
        template_type: entityData.template_type,
        template_data: entityData.template_data,
      });

      // Add to store
      setEntities([...entities, entity]);

      // Close wizard and select new entity
      setShowWizard(false);
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

  // Filter entities by type and search
  const filteredEntities = entities.filter((entity) => {
    // Type filter
    const matchesType = filterType === 'ALL' || entity.type === filterType;

    // Search filter
    const matchesSearch = !searchQuery ||
      entity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entity.aliases.some(alias => alias.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesType && matchesSearch;
  });

  // Bulk operations
  const handleToggleSelect = (entityId: string) => {
    const newSelected = new Set(selectedEntityIds);
    if (newSelected.has(entityId)) {
      newSelected.delete(entityId);
    } else {
      newSelected.add(entityId);
    }
    setSelectedEntityIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedEntityIds.size === filteredEntities.length) {
      setSelectedEntityIds(new Set());
    } else {
      setSelectedEntityIds(new Set(filteredEntities.map(e => e.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedEntityIds.size === 0) return;

    if (!confirm(`Delete ${selectedEntityIds.size} selected entities? This cannot be undone.`)) {
      return;
    }

    try {
      // Delete all selected entities
      await Promise.all(
        Array.from(selectedEntityIds).map(id => codexApi.deleteEntity(id))
      );

      // Remove from store
      selectedEntityIds.forEach(id => removeEntity(id));
      setSelectedEntityIds(new Set());
    } catch (err) {
      alert('Failed to delete entities: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleMergeEntities = () => {
    if (selectedEntityIds.size < 2) {
      alert('Select at least 2 entities to merge');
      return;
    }

    setShowMergeModal(true);
  };

  const handleConfirmMerge = async (primaryEntityId: string) => {
    const selectedEntities = entities.filter(e => selectedEntityIds.has(e.id));
    const primaryEntity = selectedEntities.find(e => e.id === primaryEntityId);
    const otherEntities = selectedEntities.filter(e => e.id !== primaryEntityId);

    if (!primaryEntity) {
      alert('Primary entity not found');
      return;
    }

    try {
      // Merge aliases and attributes
      const mergedAliases = new Set([
        ...primaryEntity.aliases,
        ...otherEntities.flatMap(e => [e.name, ...e.aliases])
      ]);

      const mergedAttributes = {
        ...primaryEntity.attributes,
        appearance: [
          ...(primaryEntity.attributes?.appearance || []),
          ...otherEntities.flatMap(e => e.attributes?.appearance || [])
        ],
        personality: [
          ...(primaryEntity.attributes?.personality || []),
          ...otherEntities.flatMap(e => e.attributes?.personality || [])
        ],
        background: [
          ...(primaryEntity.attributes?.background || []),
          ...otherEntities.flatMap(e => e.attributes?.background || [])
        ],
        actions: [
          ...(primaryEntity.attributes?.actions || []),
          ...otherEntities.flatMap(e => e.attributes?.actions || [])
        ],
      };

      // Update primary entity with merged data
      await handleUpdateEntity(primaryEntity.id, {
        aliases: Array.from(mergedAliases).filter(a => a !== primaryEntity.name),
        attributes: mergedAttributes
      });

      // Delete other entities
      await Promise.all(
        otherEntities.map(e => codexApi.deleteEntity(e.id))
      );

      // Remove from store
      otherEntities.forEach(e => removeEntity(e.id));
      setSelectedEntityIds(new Set());
      setShowMergeModal(false);

      alert(`✓ Successfully merged ${selectedEntities.length} entities into "${primaryEntity.name}"`);
    } catch (err) {
      alert('Failed to merge entities: ' + (err instanceof Error ? err.message : 'Unknown error'));
      throw err; // Re-throw to let modal handle it
    }
  };

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
        onDelete={handleDeleteEntity}
        onClose={() => setSelectedEntity(null)}
      />
    );
  }

  // If wizard is open, show the template wizard
  if (showWizard) {
    return (
      <EntityTemplateWizard
        manuscriptId={manuscriptId}
        onComplete={handleWizardComplete}
        onCancel={() => setShowWizard(false)}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Create Buttons */}
      <div className="p-4 border-b border-slate-ui space-y-2">
        {/* Primary: Guided Creation */}
        <button
          onClick={() => setShowWizard(true)}
          className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 transition-colors flex items-center justify-center gap-2"
          style={{ borderRadius: '2px' }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Create with Template</span>
        </button>

        {/* Secondary: Quick Create */}
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="w-full bg-white text-bronze border border-bronze px-4 py-2 text-sm font-sans hover:bg-bronze/10 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          Quick Create (Name Only)
        </button>

        {/* Brainstorm */}
        <button
          onClick={handleBrainstorm}
          className="w-full bg-white text-bronze border border-bronze px-4 py-2 text-sm font-sans hover:bg-bronze/10 transition-colors flex items-center justify-center gap-2"
          style={{ borderRadius: '2px' }}
          title="AI-powered character generation using Brandon Sanderson's methodology"
        >
          <span>💡</span>
          <span>Brainstorm Characters</span>
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

      {/* Search Bar */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search entities by name or alias..."
            className="w-full bg-white border border-slate-ui px-3 py-2 pl-9 text-sm font-sans"
            style={{ borderRadius: '2px' }}
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-faded-ink"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Bulk Operations Bar */}
      {selectedEntityIds.size > 0 && (
        <div className="p-3 bg-bronze/10 border-b border-bronze/30 flex items-center justify-between">
          <span className="text-sm font-sans text-midnight">
            {selectedEntityIds.size} selected
          </span>
          <div className="flex gap-2">
            {selectedEntityIds.size >= 2 && (
              <button
                onClick={handleMergeEntities}
                className="px-3 py-1 bg-bronze text-white text-sm font-sans hover:bg-bronze/90"
                style={{ borderRadius: '2px' }}
                title="Merge selected entities into one"
              >
                Merge
              </button>
            )}
            <button
              onClick={handleBulkDelete}
              className="px-3 py-1 bg-redline text-white text-sm font-sans hover:bg-redline/90"
              style={{ borderRadius: '2px' }}
            >
              Delete Selected
            </button>
            <button
              onClick={() => setSelectedEntityIds(new Set())}
              className="px-3 py-1 bg-slate-ui text-midnight text-sm font-sans hover:bg-slate-ui/80"
              style={{ borderRadius: '2px' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-ui overflow-x-auto bg-white">
        <button
          onClick={handleSelectAll}
          className="px-3 py-2 text-sm font-sans text-faded-ink hover:text-midnight border-r border-slate-ui"
          title={selectedEntityIds.size === filteredEntities.length ? "Deselect all" : "Select all"}
        >
          {selectedEntityIds.size === filteredEntities.length && filteredEntities.length > 0 ? '☑' : '☐'}
        </button>
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
              <div key={entity.id} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={selectedEntityIds.has(entity.id)}
                  onChange={() => handleToggleSelect(entity.id)}
                  className="mt-4 w-4 h-4 text-bronze cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex-1">
                  <EntityCard
                    entity={entity}
                    isSelected={selectedEntityId === entity.id}
                    onSelect={() => setSelectedEntity(entity.id)}
                    onDelete={() => handleDeleteEntity(entity.id)}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Merge Entities Modal */}
      {showMergeModal && (
        <MergeEntitiesModal
          entities={entities.filter(e => selectedEntityIds.has(e.id))}
          onConfirm={handleConfirmMerge}
          onCancel={() => setShowMergeModal(false)}
        />
      )}
    </div>
  );
}
