/**
 * Entity State Store - State management for entity timeline states
 * Tracks how entities change across narrative points in manuscripts
 */

import { create } from 'zustand';
import type {
  EntityTimelineState,
  JourneyPoint,
} from '@/types/entityState';

interface EntityStateStore {
  // State - keyed by entity ID
  statesByEntity: Record<string, EntityTimelineState[]>;
  journeysByEntity: Record<string, JourneyPoint[]>;

  // Current selections
  selectedStateId: string | null;
  comparisonStateIds: [string | null, string | null];

  // Loading states
  isLoading: boolean;
  error: string | null;

  // State Actions
  setEntityStates: (entityId: string, states: EntityTimelineState[]) => void;
  addEntityState: (entityId: string, state: EntityTimelineState) => void;
  updateEntityState: (entityId: string, stateId: string, updates: Partial<EntityTimelineState>) => void;
  removeEntityState: (entityId: string, stateId: string) => void;
  clearEntityStates: (entityId: string) => void;

  // Journey Actions
  setEntityJourney: (entityId: string, journey: JourneyPoint[]) => void;
  clearEntityJourney: (entityId: string) => void;

  // Selection Actions
  setSelectedState: (stateId: string | null) => void;
  setComparisonStates: (fromId: string | null, toId: string | null) => void;

  // Loading Actions
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;

  // Utility Functions
  getEntityStates: (entityId: string) => EntityTimelineState[];
  getEntityJourney: (entityId: string) => JourneyPoint[];
  getStateById: (entityId: string, stateId: string) => EntityTimelineState | undefined;
  getStatesByManuscript: (entityId: string, manuscriptId: string) => EntityTimelineState[];
  clearAll: () => void;
}

export const useEntityStateStore = create<EntityStateStore>((set, get) => ({
  // Initial State
  statesByEntity: {},
  journeysByEntity: {},
  selectedStateId: null,
  comparisonStateIds: [null, null],
  isLoading: false,
  error: null,

  // State Actions
  setEntityStates: (entityId, states) => set((state) => ({
    statesByEntity: {
      ...state.statesByEntity,
      [entityId]: states,
    },
  })),

  addEntityState: (entityId, newState) => set((state) => ({
    statesByEntity: {
      ...state.statesByEntity,
      [entityId]: [...(state.statesByEntity[entityId] || []), newState],
    },
  })),

  updateEntityState: (entityId, stateId, updates) => set((state) => ({
    statesByEntity: {
      ...state.statesByEntity,
      [entityId]: (state.statesByEntity[entityId] || []).map((s) =>
        s.id === stateId ? { ...s, ...updates } : s
      ),
    },
  })),

  removeEntityState: (entityId, stateId) => set((state) => ({
    statesByEntity: {
      ...state.statesByEntity,
      [entityId]: (state.statesByEntity[entityId] || []).filter((s) => s.id !== stateId),
    },
    selectedStateId: state.selectedStateId === stateId ? null : state.selectedStateId,
  })),

  clearEntityStates: (entityId) => set((state) => {
    const { [entityId]: _, ...rest } = state.statesByEntity;
    return { statesByEntity: rest };
  }),

  // Journey Actions
  setEntityJourney: (entityId, journey) => set((state) => ({
    journeysByEntity: {
      ...state.journeysByEntity,
      [entityId]: journey,
    },
  })),

  clearEntityJourney: (entityId) => set((state) => {
    const { [entityId]: _, ...rest } = state.journeysByEntity;
    return { journeysByEntity: rest };
  }),

  // Selection Actions
  setSelectedState: (stateId) => set({ selectedStateId: stateId }),

  setComparisonStates: (fromId, toId) => set({ comparisonStateIds: [fromId, toId] }),

  // Loading Actions
  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  // Utility Functions
  getEntityStates: (entityId) => {
    const { statesByEntity } = get();
    return statesByEntity[entityId] || [];
  },

  getEntityJourney: (entityId) => {
    const { journeysByEntity } = get();
    return journeysByEntity[entityId] || [];
  },

  getStateById: (entityId, stateId) => {
    const { statesByEntity } = get();
    return (statesByEntity[entityId] || []).find((s) => s.id === stateId);
  },

  getStatesByManuscript: (entityId, manuscriptId) => {
    const { statesByEntity } = get();
    return (statesByEntity[entityId] || []).filter((s) => s.manuscript_id === manuscriptId);
  },

  clearAll: () => set({
    statesByEntity: {},
    journeysByEntity: {},
    selectedStateId: null,
    comparisonStateIds: [null, null],
    isLoading: false,
    error: null,
  }),
}));
