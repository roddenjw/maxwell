/**
 * Codex Store - State management for entities and relationships
 * Using Zustand for lightweight state management
 */

import { create } from 'zustand';
import type {
  Entity,
  Relationship,
  EntitySuggestion,
  CodexTab,
  EntityType,
} from '@/types/codex';

interface CodexStore {
  // State
  entities: Entity[];
  relationships: Relationship[];
  suggestions: EntitySuggestion[];
  selectedEntityId: string | null;
  activeTab: CodexTab;
  isSidebarOpen: boolean;
  isAnalyzing: boolean;

  // Entity Actions
  setEntities: (entities: Entity[]) => void;
  addEntity: (entity: Entity) => void;
  updateEntity: (entityId: string, updates: Partial<Entity>) => void;
  removeEntity: (entityId: string) => void;

  // Relationship Actions
  setRelationships: (relationships: Relationship[]) => void;
  addRelationship: (relationship: Relationship) => void;
  removeRelationship: (relationshipId: string) => void;

  // Suggestion Actions
  setSuggestions: (suggestions: EntitySuggestion[]) => void;
  addSuggestion: (suggestion: EntitySuggestion) => void;
  removeSuggestion: (suggestionId: string) => void;

  // UI Actions
  setSelectedEntity: (entityId: string | null) => void;
  setActiveTab: (tab: CodexTab) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  toggleSidebar: () => void;
  setAnalyzing: (isAnalyzing: boolean) => void;

  // Utility Actions
  clearAll: () => void;
  getPendingSuggestionsCount: () => number;
  getEntitiesByType: (type: EntityType) => Entity[];
  getEntityRelationships: (entityId: string) => Relationship[];
}

export const useCodexStore = create<CodexStore>((set, get) => ({
  // Initial State
  entities: [],
  relationships: [],
  suggestions: [],
  selectedEntityId: null,
  activeTab: 'entities',
  isSidebarOpen: false,
  isAnalyzing: false,

  // Entity Actions
  setEntities: (entities) => set({ entities }),

  addEntity: (entity) => set((state) => ({
    entities: [...state.entities, entity],
  })),

  updateEntity: (entityId, updates) => set((state) => ({
    entities: state.entities.map((entity) =>
      entity.id === entityId ? { ...entity, ...updates } : entity
    ),
  })),

  removeEntity: (entityId) => set((state) => ({
    entities: state.entities.filter((entity) => entity.id !== entityId),
    selectedEntityId: state.selectedEntityId === entityId ? null : state.selectedEntityId,
    // Also remove relationships involving this entity
    relationships: state.relationships.filter(
      (rel) => rel.source_entity_id !== entityId && rel.target_entity_id !== entityId
    ),
  })),

  // Relationship Actions
  setRelationships: (relationships) => set({ relationships }),

  addRelationship: (relationship) => set((state) => ({
    relationships: [...state.relationships, relationship],
  })),

  removeRelationship: (relationshipId) => set((state) => ({
    relationships: state.relationships.filter((rel) => rel.id !== relationshipId),
  })),

  // Suggestion Actions
  setSuggestions: (suggestions) => set({ suggestions }),

  addSuggestion: (suggestion) => set((state) => ({
    suggestions: [...state.suggestions, suggestion],
  })),

  removeSuggestion: (suggestionId) => set((state) => ({
    suggestions: state.suggestions.filter((sug) => sug.id !== suggestionId),
  })),

  // UI Actions
  setSelectedEntity: (entityId) => set({ selectedEntityId: entityId }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  // Utility Actions
  clearAll: () => set({
    entities: [],
    relationships: [],
    suggestions: [],
    selectedEntityId: null,
    activeTab: 'entities',
    isAnalyzing: false,
  }),

  getPendingSuggestionsCount: () => {
    const { suggestions } = get();
    return suggestions.filter((sug) => sug.status === 'PENDING').length;
  },

  getEntitiesByType: (type) => {
    const { entities } = get();
    return entities.filter((entity) => entity.type === type);
  },

  getEntityRelationships: (entityId) => {
    const { relationships } = get();
    return relationships.filter(
      (rel) => rel.source_entity_id === entityId || rel.target_entity_id === entityId
    );
  },
}));
