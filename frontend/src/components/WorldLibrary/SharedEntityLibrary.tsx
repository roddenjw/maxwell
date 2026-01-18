/**
 * SharedEntityLibrary Component
 * Displays and manages world-scoped entities that can be shared across manuscripts
 */

import { useState, useEffect } from 'react';
import { useWorldStore } from '../../stores/worldStore';
import { toast } from '../../stores/toastStore';
import type { World, WorldEntityResponse, CreateWorldEntityRequest } from '../../types/world';
import { EntityTemplateWizard } from '../Codex';
import type { EntityType as CodexEntityType, TemplateType } from '../../types/codex';

interface SharedEntityLibraryProps {
  world: World;
  onCopyToManuscript?: (entity: WorldEntityResponse, manuscriptId: string) => void;
}

type EntityType = 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';

const ENTITY_TYPE_INFO: Record<EntityType, { label: string; icon: string; color: string }> = {
  CHARACTER: { label: 'Characters', icon: '&#x1F464;', color: 'text-blue-600' },
  LOCATION: { label: 'Locations', icon: '&#x1F3E0;', color: 'text-green-600' },
  ITEM: { label: 'Items', icon: '&#x2728;', color: 'text-yellow-600' },
  LORE: { label: 'Lore', icon: '&#x1F4DC;', color: 'text-purple-600' },
};

export default function SharedEntityLibrary({ world, onCopyToManuscript }: SharedEntityLibraryProps) {
  const { fetchWorldEntities, createWorldEntity, getWorldEntities, isLoading } =
    useWorldStore();

  const [activeTab, setActiveTab] = useState<EntityType>('CHARACTER');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [newEntityName, setNewEntityName] = useState('');
  const [newEntityDescription, setNewEntityDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<WorldEntityResponse | null>(null);

  // Fetch world entities on mount and when world changes
  useEffect(() => {
    fetchWorldEntities(world.id);
  }, [world.id, fetchWorldEntities]);

  const entities = getWorldEntities(world.id);
  const filteredEntities = entities.filter((e) => e.type === activeTab);

  const handleCreateEntity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEntityName.trim()) return;

    setIsCreating(true);
    try {
      const data: CreateWorldEntityRequest = {
        type: activeTab,
        name: newEntityName.trim(),
        attributes: newEntityDescription.trim()
          ? { description: newEntityDescription.trim() }
          : {},
      };

      await createWorldEntity(world.id, data);
      toast.success(`${ENTITY_TYPE_INFO[activeTab].label.slice(0, -1)} "${newEntityName}" created!`);
      setShowCreateModal(false);
      setNewEntityName('');
      setNewEntityDescription('');
    } catch (err) {
      console.error('Failed to create entity:', err);
      toast.error('Failed to create entity');
    } finally {
      setIsCreating(false);
    }
  };

  // Copy entity functionality is available through the API but not yet exposed in UI
  // Will be enabled when manuscript-selection UI is added
  void onCopyToManuscript; // Acknowledge prop for future use

  const handleWizardComplete = async (entityData: {
    name: string;
    type: CodexEntityType;
    template_type: TemplateType;
    template_data: any;
    aliases: string[];
  }) => {
    setIsCreating(true);
    try {
      // Map codex entity type to world entity type
      const worldEntityType = entityData.type as 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';

      const data: CreateWorldEntityRequest = {
        type: worldEntityType,
        name: entityData.name,
        aliases: entityData.aliases.length > 0 ? entityData.aliases : undefined,
        attributes: {
          ...entityData.template_data,
          template_type: entityData.template_type,
        },
      };

      await createWorldEntity(world.id, data);
      toast.success(`${entityData.type.charAt(0) + entityData.type.slice(1).toLowerCase()} "${entityData.name}" created!`);
      setShowWizard(false);
    } catch (err) {
      console.error('Failed to create entity:', err);
      toast.error('Failed to create entity');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="bg-white border border-slate-ui rounded-sm">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui">
        <h3 className="text-lg font-serif font-bold text-midnight">World Codex</h3>
        <p className="text-sm font-sans text-faded-ink">
          Shared entities available across all manuscripts in this world
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-ui">
        {(Object.keys(ENTITY_TYPE_INFO) as EntityType[]).map((type) => (
          <button
            key={type}
            onClick={() => setActiveTab(type)}
            className={`flex-1 px-4 py-3 text-sm font-sans font-medium transition-colors ${
              activeTab === type
                ? 'text-bronze border-b-2 border-bronze bg-bronze/5'
                : 'text-faded-ink hover:text-midnight hover:bg-slate-ui/20'
            }`}
          >
            <span
              className="mr-1"
              dangerouslySetInnerHTML={{ __html: ENTITY_TYPE_INFO[type].icon }}
            />
            {ENTITY_TYPE_INFO[type].label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Add Buttons */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex-1 px-4 py-2 border-2 border-dashed border-slate-ui hover:border-bronze text-faded-ink hover:text-bronze font-sans text-sm font-medium transition-colors rounded-sm"
          >
            + Quick Add
          </button>
          <button
            onClick={() => setShowWizard(true)}
            className="flex-1 px-4 py-2 bg-bronze/10 border-2 border-bronze/30 hover:border-bronze text-bronze font-sans text-sm font-medium transition-colors rounded-sm"
          >
            + Use Wizard
          </button>
        </div>

        {/* Entity List */}
        {isLoading ? (
          <div className="text-center py-8">
            <p className="text-faded-ink font-sans text-sm">Loading...</p>
          </div>
        ) : filteredEntities.length === 0 ? (
          <div className="text-center py-8">
            <div
              className="text-4xl mb-2"
              dangerouslySetInnerHTML={{ __html: ENTITY_TYPE_INFO[activeTab].icon }}
            />
            <p className="text-faded-ink font-sans text-sm">
              No shared {ENTITY_TYPE_INFO[activeTab].label.toLowerCase()} yet
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredEntities.map((entity) => (
              <div
                key={entity.id}
                className="p-3 border border-slate-ui hover:border-bronze transition-colors rounded-sm cursor-pointer"
                onClick={() => setSelectedEntity(entity)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={ENTITY_TYPE_INFO[activeTab].color}
                      dangerouslySetInnerHTML={{ __html: ENTITY_TYPE_INFO[activeTab].icon }}
                    />
                    <span className="font-sans font-medium text-midnight">{entity.name}</span>
                  </div>
                  <span className="text-xs font-sans text-faded-ink bg-slate-ui/30 px-2 py-1 rounded">
                    WORLD
                  </span>
                </div>
                {entity.attributes?.description ? (
                  <p className="mt-2 text-sm font-sans text-faded-ink line-clamp-2">
                    {`${entity.attributes.description}`}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Entity Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white p-6 max-w-md w-full shadow-book rounded-sm">
            <h3 className="text-xl font-serif font-bold text-midnight mb-4">
              Create {ENTITY_TYPE_INFO[activeTab].label.slice(0, -1)}
            </h3>

            <form onSubmit={handleCreateEntity}>
              <div className="mb-4">
                <label className="block text-sm font-sans font-medium text-midnight mb-2">
                  Name <span className="text-redline">*</span>
                </label>
                <input
                  type="text"
                  value={newEntityName}
                  onChange={(e) => setNewEntityName(e.target.value)}
                  placeholder={`${ENTITY_TYPE_INFO[activeTab].label.slice(0, -1)} name...`}
                  className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight rounded-sm"
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-sans font-medium text-midnight mb-2">
                  Description
                </label>
                <textarea
                  value={newEntityDescription}
                  onChange={(e) => setNewEntityDescription(e.target.value)}
                  placeholder="A brief description..."
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-ui focus:border-bronze focus:ring-1 focus:ring-bronze outline-none font-sans text-midnight resize-none rounded-sm"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewEntityName('');
                    setNewEntityDescription('');
                  }}
                  className="flex-1 px-4 py-2 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors rounded-sm"
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors rounded-sm disabled:opacity-50"
                  disabled={isCreating || !newEntityName.trim()}
                >
                  {isCreating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Entity Detail Modal */}
      {selectedEntity && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white p-6 max-w-lg w-full shadow-book rounded-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-serif font-bold text-midnight">{selectedEntity.name}</h3>
                <span
                  className={`text-sm ${ENTITY_TYPE_INFO[selectedEntity.type as EntityType]?.color || 'text-faded-ink'}`}
                >
                  {ENTITY_TYPE_INFO[selectedEntity.type as EntityType]?.label.slice(0, -1) ||
                    selectedEntity.type}
                </span>
              </div>
              <span className="text-xs font-sans text-faded-ink bg-slate-ui/30 px-2 py-1 rounded">
                {selectedEntity.scope}
              </span>
            </div>

            {selectedEntity.aliases && selectedEntity.aliases.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-sans font-medium text-midnight mb-1">Aliases</p>
                <p className="text-sm font-sans text-faded-ink">
                  {selectedEntity.aliases.join(', ')}
                </p>
              </div>
            )}

            {selectedEntity.attributes?.description ? (
              <div className="mb-4">
                <p className="text-sm font-sans font-medium text-midnight mb-1">Description</p>
                <p className="text-sm font-sans text-faded-ink">
                  {`${selectedEntity.attributes.description}`}
                </p>
              </div>
            ) : null}

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setSelectedEntity(null)}
                className="flex-1 px-4 py-2 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors rounded-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Entity Template Wizard */}
      {showWizard && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-book rounded-sm">
            <EntityTemplateWizard
              manuscriptId={world.id}
              onComplete={handleWizardComplete}
              onCancel={() => setShowWizard(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
