/**
 * CodexMainView Component
 * Full-page entity browser for the Codex view
 * Provides entity list, detail view, and relationship visualization
 */

import { useState, useEffect, useCallback } from 'react';
import { useCodexStore } from '@/stores/codexStore';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { codexApi, chaptersApi } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import type { Entity, EntityType } from '@/types/codex';
import EntityCard from './EntityCard';
import EntityDetail from './EntityDetail';
import EntityTemplateWizard from './EntityTemplateWizard';
import MergeEntitiesModal from './MergeEntitiesModal';
import RelationshipGraph from './RelationshipGraph';
import SuggestionQueue from './SuggestionQueue';
import { EntityType as EntityTypeEnum, TemplateType } from '@/types/codex';

interface CodexMainViewProps {
  manuscriptId: string;
  onOpenChapter?: (chapterId: string) => void;
}

type CodexTab = 'entities' | 'relationships' | 'intel';

export default function CodexMainView({
  manuscriptId,
  onOpenChapter: _onOpenChapter,
}: CodexMainViewProps) {
  const {
    entities,
    setEntities,
    removeEntity,
    updateEntity,
    selectedEntityId,
    setSelectedEntity,
    loadEntities,
    getPendingSuggestionsCount,
    activeTab: storeActiveTab,
    isSidebarOpen: storeWantsOpen,
    setSidebarOpen,
  } = useCodexStore();

  const { openModal } = useBrainstormStore();

  // Local state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<EntityType | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [showWizard, setShowWizard] = useState(false);
  const [showQuickCreate, setShowQuickCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedEntityIds, setSelectedEntityIds] = useState<Set<string>>(new Set());
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [mergeSourceEntityId, setMergeSourceEntityId] = useState<string | null>(null); // For single-entity merge
  // Initialize activeTab from store (in case user clicked "View in Queue" from entity detection toast)
  const [activeTab, setActiveTab] = useState<CodexTab>(() => {
    if (storeActiveTab === 'intel') return 'intel';
    return 'entities';
  });
  const pendingSuggestionsCount = getPendingSuggestionsCount();
  // Local state for immediate entity selection feedback
  const [localSelectedId, setLocalSelectedId] = useState<string | null>(null);

  // Quick create form state
  const [newEntityName, setNewEntityName] = useState('');
  const [newEntityType, setNewEntityType] = useState<EntityType>(EntityTypeEnum.CHARACTER);

  // Load entities on mount
  useEffect(() => {
    const fetchEntities = async () => {
      try {
        setLoading(true);
        setError(null);
        await loadEntities(manuscriptId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load entities');
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [manuscriptId, loadEntities]);

  // Sync local selected ID with store (for external updates)
  useEffect(() => {
    if (selectedEntityId !== localSelectedId) {
      setLocalSelectedId(selectedEntityId);
    }
  }, [selectedEntityId]);

  // Sync with store activeTab when user clicks "View in Queue" from entity detection toast
  useEffect(() => {
    if (storeActiveTab === 'intel' && storeWantsOpen) {
      setActiveTab('intel');
      // Reset the store flag
      setSidebarOpen(false);
    }
  }, [storeActiveTab, storeWantsOpen, setSidebarOpen]);

  // Handle entity selection - updates both local state (immediate) and store
  const handleEntitySelect = useCallback((entityId: string) => {
    setLocalSelectedId(entityId);
    setSelectedEntity(entityId);
  }, [setSelectedEntity]);

  // Handle entity creation
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

      setEntities([...entities, entity]);
      setNewEntityName('');
      setNewEntityType(EntityTypeEnum.CHARACTER);
      setShowQuickCreate(false);
      setSelectedEntity(entity.id);
    } catch (err) {
      setError('Failed to create entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setCreating(false);
    }
  };

  // Handle wizard completion
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

      setEntities([...entities, entity]);
      setShowWizard(false);
      setSelectedEntity(entity.id);
    } catch (err) {
      setError('Failed to create entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setCreating(false);
    }
  };

  // Handle entity deletion
  const handleDeleteEntity = useCallback(async (entityId: string) => {
    try {
      await codexApi.deleteEntity(entityId);
      removeEntity(entityId);
      if (selectedEntityId === entityId) {
        setSelectedEntity(null);
      }
    } catch (err) {
      alert('Failed to delete entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  }, [removeEntity, selectedEntityId, setSelectedEntity]);

  // Handle entity update
  const handleUpdateEntity = useCallback(async (entityId: string, updates: Partial<Entity>) => {
    try {
      const updated = await codexApi.updateEntity(entityId, updates);
      updateEntity(entityId, updated);
    } catch (err) {
      alert('Failed to update entity: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  }, [updateEntity]);

  // Handle brainstorming
  const handleBrainstorm = () => {
    openModal(manuscriptId, undefined, 'character');
  };

  // Handle adding entity to binder as character sheet
  const handleAddToBinder = useCallback(async (entityId: string) => {
    try {
      const chapter = await chaptersApi.createFromEntity({
        manuscript_id: manuscriptId,
        entity_id: entityId,
      });
      toast.success(`Character sheet created: "${chapter.title}"`);
    } catch (err) {
      toast.error('Failed to create character sheet: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  }, [manuscriptId]);

  // Filter entities
  const filteredEntities = entities.filter((entity) => {
    const matchesType = filterType === 'ALL' || entity.type === filterType;
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
    if (!confirm(`Delete ${selectedEntityIds.size} selected entities? This cannot be undone.`)) return;

    try {
      await Promise.all(
        Array.from(selectedEntityIds).map(id => codexApi.deleteEntity(id))
      );
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

  const handleConfirmMerge = async (primaryEntityId: string, secondaryEntityIds: string[]) => {
    try {
      // Call the merge API
      const mergedEntity = await codexApi.mergeEntities({
        primary_entity_id: primaryEntityId,
        secondary_entity_ids: secondaryEntityIds,
        merge_strategy: { aliases: 'combine', attributes: 'merge' }
      });

      // Update local state - remove secondary entities, update primary
      secondaryEntityIds.forEach(id => removeEntity(id));
      updateEntity(primaryEntityId, mergedEntity);

      // Reset selection states
      setSelectedEntityIds(new Set());
      setShowMergeModal(false);
      setMergeSourceEntityId(null);
      setLocalSelectedId(primaryEntityId); // Select the merged entity

      toast.success(`Successfully merged entities into "${mergedEntity.name}"`);
    } catch (err) {
      toast.error('Failed to merge entities: ' + (err instanceof Error ? err.message : 'Unknown error'));
      throw err;
    }
  };

  // Handler for single-entity merge (from EntityDetail Merge button)
  const handleStartMerge = (entityId: string) => {
    setMergeSourceEntityId(entityId);
    setShowMergeModal(true);
  };

  // Get selected entity - use local state for immediate feedback
  const effectiveSelectedId = localSelectedId || selectedEntityId;
  const selectedEntity = effectiveSelectedId
    ? entities.find((e) => e.id === effectiveSelectedId)
    : null;

  // Entity counts by type
  const entityCounts = {
    ALL: entities.length,
    CHARACTER: entities.filter(e => e.type === EntityTypeEnum.CHARACTER).length,
    LOCATION: entities.filter(e => e.type === EntityTypeEnum.LOCATION).length,
    ITEM: entities.filter(e => e.type === EntityTypeEnum.ITEM).length,
    LORE: entities.filter(e => e.type === EntityTypeEnum.LORE).length,
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-2 border-bronze border-t-transparent rounded-full animate-spin mb-3" />
          <p className="font-sans text-faded-ink text-sm">Loading Codex...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && entities.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-center max-w-md p-8">
          <div className="text-6xl mb-6">📖</div>
          <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
            Failed to Load Codex
          </h2>
          <p className="font-sans text-faded-ink mb-6">{error}</p>
          <button
            onClick={() => loadEntities(manuscriptId)}
            className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium rounded-sm"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show wizard if active
  if (showWizard) {
    return (
      <div className="flex-1 flex bg-vellum">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto">
            <EntityTemplateWizard
              manuscriptId={manuscriptId}
              onComplete={handleWizardComplete}
              onCancel={() => setShowWizard(false)}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-vellum overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b-2 border-slate-ui bg-white p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="font-garamond text-3xl font-bold text-midnight mb-2">
              The Codex
            </h1>
            <p className="font-sans text-faded-ink text-sm">
              Characters, locations, items, and lore for your story
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowWizard(true)}
              className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors flex items-center gap-2"
              style={{ borderRadius: '2px' }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create with Template
            </button>
            <button
              onClick={() => setShowQuickCreate(!showQuickCreate)}
              className="px-4 py-2 border-2 border-bronze text-bronze hover:bg-bronze/10 font-sans text-sm font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
            >
              Quick Create
            </button>
            <button
              onClick={handleBrainstorm}
              className="px-4 py-2 border-2 border-bronze text-bronze hover:bg-bronze/10 font-sans text-sm font-medium uppercase tracking-button transition-colors flex items-center gap-2"
              style={{ borderRadius: '2px' }}
              title="AI-powered character generation"
            >
              <span>💡</span>
              Brainstorm
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-2xl font-garamond font-bold text-bronze">{entityCounts.ALL}</div>
            <div className="text-xs font-sans text-faded-ink uppercase">Total</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-garamond font-bold text-midnight">{entityCounts.CHARACTER}</div>
            <div className="text-xs font-sans text-faded-ink uppercase">Characters</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-garamond font-bold text-midnight">{entityCounts.LOCATION}</div>
            <div className="text-xs font-sans text-faded-ink uppercase">Locations</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-garamond font-bold text-midnight">{entityCounts.ITEM}</div>
            <div className="text-xs font-sans text-faded-ink uppercase">Items</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-garamond font-bold text-midnight">{entityCounts.LORE}</div>
            <div className="text-xs font-sans text-faded-ink uppercase">Lore</div>
          </div>
        </div>
      </div>

      {/* Quick Create Form */}
      {showQuickCreate && (
        <div className="flex-shrink-0 border-b border-slate-ui bg-white p-6">
          <div className="max-w-xl mx-auto">
            <h3 className="font-garamond font-semibold text-midnight mb-3">Quick Create Entity</h3>
            {error && (
              <div className="mb-3 bg-redline/10 border-l-4 border-redline p-2 text-xs font-sans text-redline">
                {error}
              </div>
            )}
            <div className="flex gap-3">
              <input
                type="text"
                value={newEntityName}
                onChange={(e) => {
                  setNewEntityName(e.target.value);
                  setError(null);
                }}
                placeholder="Entity name..."
                className="flex-1 bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
                autoFocus
                disabled={creating}
              />
              <select
                value={newEntityType}
                onChange={(e) => setNewEntityType(e.target.value as EntityType)}
                className="bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
                disabled={creating}
              >
                <option value={EntityTypeEnum.CHARACTER}>Character</option>
                <option value={EntityTypeEnum.LOCATION}>Location</option>
                <option value={EntityTypeEnum.ITEM}>Item</option>
                <option value={EntityTypeEnum.LORE}>Lore</option>
              </select>
              <button
                onClick={handleCreateEntity}
                disabled={creating || !newEntityName.trim()}
                className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium disabled:opacity-50"
                style={{ borderRadius: '2px' }}
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setShowQuickCreate(false);
                  setNewEntityName('');
                  setError(null);
                }}
                disabled={creating}
                className="px-4 py-2 bg-slate-ui text-midnight font-sans text-sm font-medium hover:bg-slate-ui/80"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Toggle */}
      <div className="flex-shrink-0 border-b border-slate-ui bg-white px-6 py-3">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <button
            onClick={() => setActiveTab('entities')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              activeTab === 'entities'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            📝 Entities
          </button>
          <button
            onClick={() => setActiveTab('relationships')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors ${
              activeTab === 'relationships'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            🕸️ Relationships
          </button>
          <button
            onClick={() => setActiveTab('intel')}
            className={`flex-1 px-4 py-2 font-sans text-sm font-medium uppercase tracking-button transition-colors relative ${
              activeTab === 'intel'
                ? 'bg-bronze text-white'
                : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
            }`}
            style={{ borderRadius: '2px' }}
          >
            🔍 Intel
            {pendingSuggestionsCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-redline text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                {pendingSuggestionsCount > 9 ? '9+' : pendingSuggestionsCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'entities' && (
          <>
            {/* Entity List Panel */}
            <div className="w-96 border-r border-slate-ui bg-white flex flex-col overflow-hidden">
              {/* Search Bar */}
              <div className="flex-shrink-0 p-4 border-b border-slate-ui">
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search entities..."
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
                <div className="flex-shrink-0 p-3 bg-bronze/10 border-b border-bronze/30 flex items-center justify-between">
                  <span className="text-sm font-sans text-midnight">
                    {selectedEntityIds.size} selected
                  </span>
                  <div className="flex gap-2">
                    {selectedEntityIds.size >= 2 && (
                      <button
                        onClick={handleMergeEntities}
                        className="px-3 py-1 bg-bronze text-white text-xs font-sans hover:bg-bronze/90"
                        style={{ borderRadius: '2px' }}
                      >
                        Merge
                      </button>
                    )}
                    <button
                      onClick={handleBulkDelete}
                      className="px-3 py-1 bg-redline text-white text-xs font-sans hover:bg-redline/90"
                      style={{ borderRadius: '2px' }}
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => setSelectedEntityIds(new Set())}
                      className="px-3 py-1 bg-slate-ui text-midnight text-xs font-sans hover:bg-slate-ui/80"
                      style={{ borderRadius: '2px' }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Filter Tabs */}
              <div className="flex-shrink-0 flex border-b border-slate-ui overflow-x-auto bg-vellum">
                <button
                  onClick={handleSelectAll}
                  className="px-3 py-2 text-sm font-sans text-faded-ink hover:text-midnight border-r border-slate-ui"
                  title={selectedEntityIds.size === filteredEntities.length ? "Deselect all" : "Select all"}
                >
                  {selectedEntityIds.size === filteredEntities.length && filteredEntities.length > 0 ? '☑' : '☐'}
                </button>
                {['ALL', ...Object.values(EntityTypeEnum)].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type as EntityType | 'ALL')}
                    className={`
                      px-3 py-2 text-xs font-sans whitespace-nowrap transition-colors
                      ${filterType === type
                        ? 'text-bronze border-b-2 border-bronze bg-white'
                        : 'text-faded-ink hover:text-midnight'
                      }
                    `}
                  >
                    {type}
                    <span className="ml-1 text-xs">
                      ({entityCounts[type as keyof typeof entityCounts] || 0})
                    </span>
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
                      Create your first entity using the buttons above
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
                            isSelected={effectiveSelectedId === entity.id}
                            onSelect={() => handleEntitySelect(entity.id)}
                            onDelete={() => handleDeleteEntity(entity.id)}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Entity Detail Panel */}
            <div className="flex-1 bg-vellum overflow-y-auto">
              {selectedEntity ? (
                <EntityDetail
                  entity={selectedEntity}
                  onUpdate={(updates) => handleUpdateEntity(selectedEntity.id, updates)}
                  onDelete={handleDeleteEntity}
                  onClose={() => setSelectedEntity(null)}
                  onAddToBinder={handleAddToBinder}
                  onMerge={handleStartMerge}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center max-w-md p-8">
                    <div className="text-6xl mb-6">📖</div>
                    <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
                      Select an Entity
                    </h2>
                    <p className="font-sans text-faded-ink">
                      Choose an entity from the list to view and edit its details.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'relationships' && (
          <div className="flex-1 overflow-hidden">
            <RelationshipGraph manuscriptId={manuscriptId} />
          </div>
        )}

        {activeTab === 'intel' && (
          <div className="flex-1 overflow-y-auto bg-vellum">
            <div className="max-w-4xl mx-auto p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-serif font-bold text-midnight mb-2">Entity Intel</h2>
                <p className="text-faded-ink font-sans text-sm">
                  Review and approve automatically detected entities from your manuscript
                </p>
              </div>
              <SuggestionQueue manuscriptId={manuscriptId} />
            </div>
          </div>
        )}
      </div>

      {/* Merge Entities Modal */}
      {showMergeModal && (
        <MergeEntitiesModal
          // Single-entity mode: pass the source entity
          sourceEntity={mergeSourceEntityId ? entities.find(e => e.id === mergeSourceEntityId) : undefined}
          // Multi-select mode: pass selected entities
          entities={selectedEntityIds.size >= 2 ? entities.filter(e => selectedEntityIds.has(e.id)) : undefined}
          // Available entities to pick from (for single-entity merge)
          availableEntities={entities}
          onConfirm={handleConfirmMerge}
          onCancel={() => {
            setShowMergeModal(false);
            setMergeSourceEntityId(null);
          }}
        />
      )}
    </div>
  );
}
