/**
 * World Store - Zustand
 * Manages world and series state for library organization
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { worldsApi } from '../lib/api';
import type {
  World,
  Series,
  ManuscriptBrief,
  CreateWorldRequest,
  UpdateWorldRequest,
  CreateSeriesRequest,
  UpdateSeriesRequest,
  WorldEntityResponse,
  CreateWorldEntityRequest,
} from '../types/world';

interface WorldStore {
  // State
  worlds: World[];
  currentWorldId: string | null;
  currentSeriesId: string | null;
  seriesByWorld: Record<string, Series[]>;
  manuscriptsBySeries: Record<string, ManuscriptBrief[]>;
  worldEntities: Record<string, WorldEntityResponse[]>;
  isLoading: boolean;
  error: string | null;

  // World Actions
  fetchWorlds: () => Promise<void>;
  createWorld: (data: CreateWorldRequest) => Promise<World>;
  updateWorld: (worldId: string, data: UpdateWorldRequest) => Promise<void>;
  deleteWorld: (worldId: string) => Promise<void>;
  setCurrentWorld: (worldId: string | null) => void;
  getCurrentWorld: () => World | undefined;

  // Series Actions
  fetchSeries: (worldId: string) => Promise<void>;
  createSeries: (worldId: string, data: CreateSeriesRequest) => Promise<Series>;
  updateSeries: (seriesId: string, data: UpdateSeriesRequest) => Promise<void>;
  deleteSeries: (seriesId: string) => Promise<void>;
  setCurrentSeries: (seriesId: string | null) => void;
  getCurrentSeries: () => Series | undefined;
  getSeriesForWorld: (worldId: string) => Series[];

  // Manuscript Assignment Actions
  fetchSeriesManuscripts: (seriesId: string) => Promise<void>;
  assignManuscriptToSeries: (seriesId: string, manuscriptId: string, orderIndex?: number) => Promise<void>;
  removeManuscriptFromSeries: (seriesId: string, manuscriptId: string) => Promise<void>;
  getManuscriptsForSeries: (seriesId: string) => ManuscriptBrief[];

  // World Entity Actions
  fetchWorldEntities: (worldId: string, type?: string) => Promise<void>;
  createWorldEntity: (worldId: string, data: CreateWorldEntityRequest) => Promise<WorldEntityResponse>;
  getWorldEntities: (worldId: string) => WorldEntityResponse[];

  // Utility
  clearError: () => void;
}

export const useWorldStore = create<WorldStore>()(
  persist(
    (set, get) => ({
      // Initial State
      worlds: [],
      currentWorldId: null,
      currentSeriesId: null,
      seriesByWorld: {},
      manuscriptsBySeries: {},
      worldEntities: {},
      isLoading: false,
      error: null,

      // ========================
      // World Actions
      // ========================

      fetchWorlds: async () => {
        try {
          set({ isLoading: true, error: null });
          const worlds = await worldsApi.listWorlds();
          set({ worlds, isLoading: false });
        } catch (error) {
          console.error('fetchWorlds error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch worlds',
            isLoading: false,
          });
        }
      },

      createWorld: async (data: CreateWorldRequest) => {
        try {
          set({ isLoading: true, error: null });
          const world = await worldsApi.createWorld(data);
          set((state) => ({
            worlds: [...state.worlds, world],
            isLoading: false,
          }));
          return world;
        } catch (error) {
          console.error('createWorld error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to create world',
            isLoading: false,
          });
          throw error;
        }
      },

      updateWorld: async (worldId: string, data: UpdateWorldRequest) => {
        try {
          set({ isLoading: true, error: null });
          const updatedWorld = await worldsApi.updateWorld(worldId, data);
          set((state) => ({
            worlds: state.worlds.map((w) => (w.id === worldId ? updatedWorld : w)),
            isLoading: false,
          }));
        } catch (error) {
          console.error('updateWorld error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to update world',
            isLoading: false,
          });
          throw error;
        }
      },

      deleteWorld: async (worldId: string) => {
        try {
          set({ isLoading: true, error: null });
          await worldsApi.deleteWorld(worldId);
          set((state) => ({
            worlds: state.worlds.filter((w) => w.id !== worldId),
            currentWorldId: state.currentWorldId === worldId ? null : state.currentWorldId,
            isLoading: false,
          }));
        } catch (error) {
          console.error('deleteWorld error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to delete world',
            isLoading: false,
          });
          throw error;
        }
      },

      setCurrentWorld: (worldId: string | null) => {
        set({ currentWorldId: worldId, currentSeriesId: null });
      },

      getCurrentWorld: () => {
        const { worlds, currentWorldId } = get();
        if (!currentWorldId) return undefined;
        return worlds.find((w) => w.id === currentWorldId);
      },

      // ========================
      // Series Actions
      // ========================

      fetchSeries: async (worldId: string) => {
        try {
          set({ isLoading: true, error: null });
          const series = await worldsApi.listSeries(worldId);
          set((state) => ({
            seriesByWorld: {
              ...state.seriesByWorld,
              [worldId]: series,
            },
            isLoading: false,
          }));
        } catch (error) {
          console.error('fetchSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch series',
            isLoading: false,
          });
        }
      },

      createSeries: async (worldId: string, data: CreateSeriesRequest) => {
        try {
          set({ isLoading: true, error: null });
          const series = await worldsApi.createSeries(worldId, data);
          set((state) => ({
            seriesByWorld: {
              ...state.seriesByWorld,
              [worldId]: [...(state.seriesByWorld[worldId] || []), series],
            },
            isLoading: false,
          }));
          return series;
        } catch (error) {
          console.error('createSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to create series',
            isLoading: false,
          });
          throw error;
        }
      },

      updateSeries: async (seriesId: string, data: UpdateSeriesRequest) => {
        try {
          set({ isLoading: true, error: null });
          const updatedSeries = await worldsApi.updateSeries(seriesId, data);
          set((state) => {
            const worldId = updatedSeries.world_id;
            return {
              seriesByWorld: {
                ...state.seriesByWorld,
                [worldId]: (state.seriesByWorld[worldId] || []).map((s) =>
                  s.id === seriesId ? updatedSeries : s
                ),
              },
              isLoading: false,
            };
          });
        } catch (error) {
          console.error('updateSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to update series',
            isLoading: false,
          });
          throw error;
        }
      },

      deleteSeries: async (seriesId: string) => {
        try {
          set({ isLoading: true, error: null });
          await worldsApi.deleteSeries(seriesId);
          set((state) => {
            // Find which world this series belongs to
            const newSeriesByWorld = { ...state.seriesByWorld };
            for (const worldId of Object.keys(newSeriesByWorld)) {
              newSeriesByWorld[worldId] = newSeriesByWorld[worldId].filter(
                (s) => s.id !== seriesId
              );
            }
            return {
              seriesByWorld: newSeriesByWorld,
              currentSeriesId: state.currentSeriesId === seriesId ? null : state.currentSeriesId,
              isLoading: false,
            };
          });
        } catch (error) {
          console.error('deleteSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to delete series',
            isLoading: false,
          });
          throw error;
        }
      },

      setCurrentSeries: (seriesId: string | null) => {
        set({ currentSeriesId: seriesId });
      },

      getCurrentSeries: () => {
        const { seriesByWorld, currentSeriesId } = get();
        if (!currentSeriesId) return undefined;
        for (const series of Object.values(seriesByWorld).flat()) {
          if (series.id === currentSeriesId) return series;
        }
        return undefined;
      },

      getSeriesForWorld: (worldId: string) => {
        return get().seriesByWorld[worldId] || [];
      },

      // ========================
      // Manuscript Assignment Actions
      // ========================

      fetchSeriesManuscripts: async (seriesId: string) => {
        try {
          set({ isLoading: true, error: null });
          const manuscripts = await worldsApi.listSeriesManuscripts(seriesId);
          set((state) => ({
            manuscriptsBySeries: {
              ...state.manuscriptsBySeries,
              [seriesId]: manuscripts,
            },
            isLoading: false,
          }));
        } catch (error) {
          console.error('fetchSeriesManuscripts error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch series manuscripts',
            isLoading: false,
          });
        }
      },

      assignManuscriptToSeries: async (
        seriesId: string,
        manuscriptId: string,
        orderIndex?: number
      ) => {
        try {
          set({ isLoading: true, error: null });
          const manuscript = await worldsApi.assignManuscriptToSeries(seriesId, {
            manuscript_id: manuscriptId,
            order_index: orderIndex,
          });
          set((state) => ({
            manuscriptsBySeries: {
              ...state.manuscriptsBySeries,
              [seriesId]: [...(state.manuscriptsBySeries[seriesId] || []), manuscript],
            },
            isLoading: false,
          }));
        } catch (error) {
          console.error('assignManuscriptToSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to assign manuscript to series',
            isLoading: false,
          });
          throw error;
        }
      },

      removeManuscriptFromSeries: async (seriesId: string, manuscriptId: string) => {
        try {
          set({ isLoading: true, error: null });
          await worldsApi.removeManuscriptFromSeries(seriesId, manuscriptId);
          set((state) => ({
            manuscriptsBySeries: {
              ...state.manuscriptsBySeries,
              [seriesId]: (state.manuscriptsBySeries[seriesId] || []).filter(
                (m) => m.id !== manuscriptId
              ),
            },
            isLoading: false,
          }));
        } catch (error) {
          console.error('removeManuscriptFromSeries error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to remove manuscript from series',
            isLoading: false,
          });
          throw error;
        }
      },

      getManuscriptsForSeries: (seriesId: string) => {
        return get().manuscriptsBySeries[seriesId] || [];
      },

      // ========================
      // World Entity Actions
      // ========================

      fetchWorldEntities: async (worldId: string, type?: string) => {
        try {
          set({ isLoading: true, error: null });
          const entities = await worldsApi.listWorldEntities(worldId, type);
          set((state) => ({
            worldEntities: {
              ...state.worldEntities,
              [worldId]: entities,
            },
            isLoading: false,
          }));
        } catch (error) {
          console.error('fetchWorldEntities error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch world entities',
            isLoading: false,
          });
        }
      },

      createWorldEntity: async (worldId: string, data: CreateWorldEntityRequest) => {
        try {
          set({ isLoading: true, error: null });
          const entity = await worldsApi.createWorldEntity(worldId, data);
          set((state) => ({
            worldEntities: {
              ...state.worldEntities,
              [worldId]: [...(state.worldEntities[worldId] || []), entity],
            },
            isLoading: false,
          }));
          return entity;
        } catch (error) {
          console.error('createWorldEntity error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to create world entity',
            isLoading: false,
          });
          throw error;
        }
      },

      getWorldEntities: (worldId: string) => {
        return get().worldEntities[worldId] || [];
      },

      // ========================
      // Utility
      // ========================

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'maxwell-worlds', // localStorage key
      partialize: (state) => ({
        currentWorldId: state.currentWorldId,
        currentSeriesId: state.currentSeriesId,
      }),
    }
  )
);
