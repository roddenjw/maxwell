/**
 * Outline Store
 * Manages story structure outline and plot beats state using Zustand
 */

import { create } from 'zustand';
import type {
  Outline,
  PlotBeat,
  PlotBeatUpdate,
  OutlineProgress,
  AIAnalysisResult,
  BeatSuggestionsResult,
  SceneCreate,
  SeriesStructureSummary,
  SeriesStructureWithManuscripts,
  BeatFeedback,
} from '@/types/outline';
import { outlineApi, seriesOutlineApi } from '@/lib/api';
import { toast } from './toastStore';

interface OutlineStore {
  // State
  outline: Outline | null;
  progress: OutlineProgress | null;
  isLoading: boolean;
  isSidebarOpen: boolean;
  outlineReferenceSidebarOpen: boolean;
  beatContextPanelCollapsed: boolean;
  expandedBeatId: string | null;
  error: string | null;
  notifiedCompletedBeats: Set<string>;  // Track which beats we've shown completion notification for

  // AI State
  aiSuggestions: AIAnalysisResult | null;
  beatSuggestions: Map<string, BeatSuggestionsResult>;  // beatId -> suggestions
  isAnalyzing: boolean;
  apiKey: string | null;

  // Feedback state for AI refinement
  beatFeedback: Map<string, BeatFeedback>;  // beatName -> feedback

  // Actions
  setOutline: (outline: Outline | null) => void;
  setProgress: (progress: OutlineProgress | null) => void;
  setLoading: (isLoading: boolean) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  toggleSidebar: () => void;
  setOutlineReferenceSidebarOpen: (isOpen: boolean) => void;
  toggleOutlineReferenceSidebar: () => void;
  setBeatContextPanelCollapsed: (collapsed: boolean) => void;
  toggleBeatContextPanel: () => void;
  setExpandedBeat: (beatId: string | null) => void;
  setError: (error: string | null) => void;

  // Async Actions
  loadOutline: (manuscriptId: string) => Promise<void>;
  loadProgress: (outlineId: string) => Promise<void>;
  updateBeat: (beatId: string, updates: PlotBeatUpdate) => Promise<void>;
  createScene: (data: SceneCreate) => Promise<PlotBeat | null>;
  deleteItem: (itemId: string) => Promise<void>;
  clearOutline: () => void;

  // AI Actions
  setApiKey: (apiKey: string) => void;
  getApiKey: () => string | null;
  runAIAnalysis: (outlineId: string, analysisTypes?: string[]) => Promise<void>;
  runAIAnalysisWithFeedback: (outlineId: string, analysisTypes?: string[]) => Promise<void>;
  getBeatAISuggestions: (beatId: string) => Promise<void>;
  clearAISuggestions: () => void;
  markPlotHoleResolved: (index: number) => void;

  // Feedback Actions
  setBeatFeedback: (beatName: string, feedback: BeatFeedback) => void;
  addBeatFeedbackLike: (beatName: string, description: string) => void;
  addBeatFeedbackDislike: (beatName: string, description: string) => void;
  setBeatFeedbackNotes: (beatName: string, notes: string) => void;
  clearBeatFeedback: (beatName?: string) => void;
  hasFeedback: () => boolean;

  // Computed
  getCompletedBeatsCount: () => number;
  getTotalBeatsCount: () => number;
  getBeatById: (beatId: string) => PlotBeat | undefined;
  getBeatByChapterId: (chapterId: string) => PlotBeat | null;
  getCompletionPercentage: () => number;

  // Series/World Outline State
  seriesOutline: Outline | null;
  worldOutline: Outline | null;
  seriesStructures: SeriesStructureSummary[];
  seriesStructureWithManuscripts: SeriesStructureWithManuscripts | null;
  isLoadingSeriesOutline: boolean;

  // Series/World Outline Actions
  setSeriesOutline: (outline: Outline | null) => void;
  setWorldOutline: (outline: Outline | null) => void;
  setSeriesStructures: (structures: SeriesStructureSummary[]) => void;
  loadSeriesStructures: () => Promise<void>;
  loadSeriesOutline: (seriesId: string) => Promise<void>;
  loadWorldOutline: (worldId: string) => Promise<void>;
  loadSeriesStructureWithManuscripts: (seriesId: string) => Promise<void>;
  createSeriesOutline: (seriesId: string, structureType: string, genre?: string) => Promise<Outline | null>;
  createWorldOutline: (worldId: string, structureType: string, genre?: string) => Promise<Outline | null>;
}

export const useOutlineStore = create<OutlineStore>((set, get) => ({
  // Initial State
  outline: null,
  progress: null,
  isLoading: false,
  isSidebarOpen: false,
  outlineReferenceSidebarOpen: false,
  beatContextPanelCollapsed: false,
  expandedBeatId: null,
  error: null,
  notifiedCompletedBeats: new Set(),

  // AI Initial State
  aiSuggestions: null,
  beatSuggestions: new Map(),
  isAnalyzing: false,
  apiKey: typeof window !== 'undefined' ? localStorage.getItem('openrouter_api_key') : null,
  beatFeedback: new Map(),

  // Synchronous Actions
  setOutline: (outline) => set({ outline, error: null }),

  setProgress: (progress) => set({ progress }),

  setLoading: (isLoading) => set({ isLoading }),

  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setOutlineReferenceSidebarOpen: (isOpen) => set({ outlineReferenceSidebarOpen: isOpen }),

  toggleOutlineReferenceSidebar: () => set((state) => ({ outlineReferenceSidebarOpen: !state.outlineReferenceSidebarOpen })),

  setBeatContextPanelCollapsed: (collapsed) => set({ beatContextPanelCollapsed: collapsed }),

  toggleBeatContextPanel: () => set((state) => ({ beatContextPanelCollapsed: !state.beatContextPanelCollapsed })),

  setExpandedBeat: (beatId) => set({ expandedBeatId: beatId }),

  setError: (error) => set({ error }),

  // Async Actions
  loadOutline: async (manuscriptId: string) => {
    set({ isLoading: true, error: null });
    try {
      const outline = await outlineApi.getActiveOutline(manuscriptId);
      set({ outline, isLoading: false });

      // Auto-load progress if outline exists
      if (outline) {
        get().loadProgress(outline.id);
      }
    } catch (error: any) {
      // 404 means no outline exists - this is not an error, just clear state
      if (error.message?.includes('404') || error.message?.includes('No active outline')) {
        set({ outline: null, isLoading: false, error: null });
      } else {
        console.error('Failed to load outline:', error);
        set({ error: error.message || 'Failed to load outline', isLoading: false });
        toast.error('Failed to load outline');
      }
    }
  },

  loadProgress: (() => {
    // Debounce map: outlineId -> timeout
    const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
    const DEBOUNCE_MS = 1000; // 1 second debounce

    return async (outlineId: string) => {
      // Clear existing timer for this outline
      const existingTimer = debounceTimers.get(outlineId);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // Set new debounced timer
      const timer = setTimeout(async () => {
        try {
          const progress = await outlineApi.getProgress(outlineId);
          set({ progress });
        } catch (error: any) {
          console.error('Failed to load outline progress:', error);
          // Don't show error toast for progress - it's not critical
        } finally {
          debounceTimers.delete(outlineId);
        }
      }, DEBOUNCE_MS);

      debounceTimers.set(outlineId, timer);
    };
  })(),

  updateBeat: async (beatId: string, updates: PlotBeatUpdate) => {
    const currentOutline = get().outline;
    if (!currentOutline) return;

    // Store original state for rollback
    const originalOutline = { ...currentOutline };

    // Optimistic update - immediately update local state
    const optimisticBeats = currentOutline.plot_beats.map((beat) =>
      beat.id === beatId ? { ...beat, ...updates } : beat
    );
    set({
      outline: {
        ...currentOutline,
        plot_beats: optimisticBeats,
      },
    });

    try {
      // Call API to persist changes
      const updatedBeat = await outlineApi.updateBeat(beatId, updates);

      // Update with actual API response
      const updatedBeats = currentOutline.plot_beats.map((beat) =>
        beat.id === beatId ? updatedBeat : beat
      );
      set({
        outline: {
          ...currentOutline,
          plot_beats: updatedBeats,
        },
      });

      // Reload progress if completion status changed
      if (updates.is_completed !== undefined) {
        get().loadProgress(currentOutline.id);
      }
    } catch (error: any) {
      // Revert to original state on error
      set({ outline: originalOutline });

      console.error('Failed to update beat:', error);
      toast.error('Failed to update plot beat');
      throw error;
    }
  },

  createScene: async (data: SceneCreate) => {
    const currentOutline = get().outline;
    if (!currentOutline) return null;

    try {
      const newScene = await outlineApi.createScene(currentOutline.id, data);

      // Reload the full outline to get updated order_index for all items
      if (currentOutline.manuscript_id) {
        await get().loadOutline(currentOutline.manuscript_id);
      }

      toast.success('Scene added to outline');
      return newScene;
    } catch (error: any) {
      console.error('Failed to create scene:', error);
      toast.error('Failed to create scene');
      return null;
    }
  },

  deleteItem: async (itemId: string) => {
    const currentOutline = get().outline;
    if (!currentOutline) return;

    try {
      await outlineApi.deleteBeat(itemId);

      // Reload the full outline to get updated order_index for all items
      if (currentOutline.manuscript_id) {
        await get().loadOutline(currentOutline.manuscript_id);
      }

      toast.success('Item removed from outline');
    } catch (error: any) {
      console.error('Failed to delete item:', error);
      toast.error('Failed to delete item');
    }
  },

  clearOutline: () => {
    set({
      outline: null,
      progress: null,
      expandedBeatId: null,
      isSidebarOpen: false,
      error: null,
      aiSuggestions: null,
      beatSuggestions: new Map(),
    });
  },

  // AI Actions
  setApiKey: (apiKey: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('openrouter_api_key', apiKey);
    }
    set({ apiKey });
  },

  getApiKey: () => {
    const state = get();
    if (state.apiKey) return state.apiKey;

    // Try to load from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('openrouter_api_key');
      if (stored) {
        set({ apiKey: stored });
        return stored;
      }
    }
    return null;
  },

  runAIAnalysis: async (outlineId: string, analysisTypes?: string[]) => {
    const apiKey = get().getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    set({ isAnalyzing: true, error: null });

    try {
      // This will be implemented in the API client
      const { aiApi } = await import('@/lib/api');
      const result = await aiApi.analyzeOutline(outlineId, apiKey, analysisTypes);

      set({
        aiSuggestions: result.data,
        isAnalyzing: false,
      });

      toast.success(`AI analysis complete! Cost: ${result.cost?.formatted || '$0.00'}`);
    } catch (error: any) {
      console.error('AI analysis failed:', error);
      set({ isAnalyzing: false, error: error.message });

      // Handle specific error types with helpful messages
      if (error.message?.includes('insufficient_credits') || error.message?.includes('insufficient credits')) {
        toast.error('Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits');
      } else if (error.message?.includes('invalid_api_key') || error.message?.includes('invalid')) {
        toast.error('Your OpenRouter API key is invalid. Please check your API key in Settings.');
      } else {
        toast.error('AI analysis failed: ' + (error.message || 'Unknown error'));
      }
      throw error;
    }
  },

  getBeatAISuggestions: async (beatId: string) => {
    const apiKey = get().getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    set({ isAnalyzing: true, error: null });

    try {
      const { aiApi } = await import('@/lib/api');
      const result = await aiApi.getBeatSuggestions(beatId, apiKey);

      // Update the beat suggestions map
      const newMap = new Map(get().beatSuggestions);
      newMap.set(beatId, result.data);

      set({
        beatSuggestions: newMap,
        isAnalyzing: false,
      });

      toast.success(`AI suggestions generated! Cost: ${result.cost?.formatted || '$0.00'}`);
    } catch (error: any) {
      console.error('Beat suggestions failed:', error);
      set({ isAnalyzing: false, error: error.message });

      // Handle specific error types with helpful messages
      if (error.message?.includes('insufficient_credits') || error.message?.includes('insufficient credits')) {
        toast.error('Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits');
      } else if (error.message?.includes('invalid_api_key') || error.message?.includes('invalid')) {
        toast.error('Your OpenRouter API key is invalid. Please check your API key in Settings.');
      } else {
        toast.error('Failed to get AI suggestions: ' + (error.message || 'Unknown error'));
      }
      throw error;
    }
  },

  clearAISuggestions: () => {
    set({
      aiSuggestions: null,
      beatSuggestions: new Map(),
    });
  },

  markPlotHoleResolved: (index: number) => {
    const current = get().aiSuggestions;
    if (!current || !current.plot_holes) return;

    const updated = { ...current };
    updated.plot_holes = [...current.plot_holes];
    if (updated.plot_holes[index]) {
      updated.plot_holes[index] = {
        ...updated.plot_holes[index],
        resolved: true,
      };
    }

    set({ aiSuggestions: updated });
  },

  // Feedback Actions
  setBeatFeedback: (beatName: string, feedback: BeatFeedback) => {
    const newMap = new Map(get().beatFeedback);
    newMap.set(beatName, feedback);
    set({ beatFeedback: newMap });
  },

  addBeatFeedbackLike: (beatName: string, description: string) => {
    const current = get().beatFeedback.get(beatName) || { liked: [], disliked: [], notes: '' };
    const liked = current.liked.includes(description)
      ? current.liked.filter(d => d !== description)  // Toggle off
      : [...current.liked, description];
    const newMap = new Map(get().beatFeedback);
    newMap.set(beatName, { ...current, liked });
    set({ beatFeedback: newMap });
  },

  addBeatFeedbackDislike: (beatName: string, description: string) => {
    const current = get().beatFeedback.get(beatName) || { liked: [], disliked: [], notes: '' };
    const disliked = current.disliked.includes(description)
      ? current.disliked.filter(d => d !== description)  // Toggle off
      : [...current.disliked, description];
    const newMap = new Map(get().beatFeedback);
    newMap.set(beatName, { ...current, disliked });
    set({ beatFeedback: newMap });
  },

  setBeatFeedbackNotes: (beatName: string, notes: string) => {
    const current = get().beatFeedback.get(beatName) || { liked: [], disliked: [], notes: '' };
    const newMap = new Map(get().beatFeedback);
    newMap.set(beatName, { ...current, notes });
    set({ beatFeedback: newMap });
  },

  clearBeatFeedback: (beatName?: string) => {
    if (beatName) {
      const newMap = new Map(get().beatFeedback);
      newMap.delete(beatName);
      set({ beatFeedback: newMap });
    } else {
      set({ beatFeedback: new Map() });
    }
  },

  hasFeedback: () => {
    const feedback = get().beatFeedback;
    for (const [, value] of feedback) {
      if (value.liked.length > 0 || value.disliked.length > 0 || value.notes.trim()) {
        return true;
      }
    }
    return false;
  },

  runAIAnalysisWithFeedback: async (outlineId: string, analysisTypes?: string[]) => {
    const apiKey = get().getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    const feedback = get().beatFeedback;
    const hasFeedback = get().hasFeedback();

    set({ isAnalyzing: true, error: null });

    try {
      const { aiApi } = await import('@/lib/api');

      // Convert Map to object for API
      const feedbackObj: { [beatName: string]: BeatFeedback } = {};
      if (hasFeedback) {
        for (const [beatName, fb] of feedback) {
          if (fb.liked.length > 0 || fb.disliked.length > 0 || fb.notes.trim()) {
            feedbackObj[beatName] = fb;
          }
        }
      }

      const result = await aiApi.analyzeOutlineWithFeedback(outlineId, apiKey, analysisTypes, feedbackObj);

      set({
        aiSuggestions: result.data,
        isAnalyzing: false,
        beatFeedback: new Map(),  // Clear feedback after successful regeneration
      });

      toast.success(`AI analysis complete with feedback! Cost: ${result.cost?.formatted || '$0.00'}`);
    } catch (error: any) {
      console.error('AI analysis with feedback failed:', error);
      set({ isAnalyzing: false, error: error.message });

      if (error.message?.includes('insufficient_credits') || error.message?.includes('insufficient credits')) {
        toast.error('Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits');
      } else if (error.message?.includes('invalid_api_key') || error.message?.includes('invalid')) {
        toast.error('Your OpenRouter API key is invalid. Please check your API key in Settings.');
      } else {
        toast.error('AI analysis failed: ' + (error.message || 'Unknown error'));
      }
      throw error;
    }
  },

  // Computed Values
  getCompletedBeatsCount: () => {
    const outline = get().outline;
    if (!outline?.plot_beats) return 0;
    return outline.plot_beats.filter((beat) => beat.is_completed).length;
  },

  getTotalBeatsCount: () => {
    const outline = get().outline;
    if (!outline?.plot_beats) return 0;
    return outline.plot_beats.length;
  },

  getBeatById: (beatId: string) => {
    const outline = get().outline;
    if (!outline?.plot_beats) return undefined;
    return outline.plot_beats.find((beat) => beat.id === beatId);
  },

  getBeatByChapterId: (() => {
    // Memoization cache for beat lookups
    const cache = new Map<string, PlotBeat | null>();
    let lastOutlineId: string | null = null;

    return (chapterId: string) => {
      const outline = get().outline;

      // Clear cache if outline changed
      if (outline?.id !== lastOutlineId) {
        cache.clear();
        lastOutlineId = outline?.id || null;
      }

      if (!outline) return null;

      // Return cached result if available
      if (cache.has(chapterId)) {
        return cache.get(chapterId) || null;
      }

      // Find beat and cache result
      const beat = outline.plot_beats.find((beat) => beat.chapter_id === chapterId) || null;
      cache.set(chapterId, beat);
      return beat;
    };
  })(),

  getCompletionPercentage: () => {
    const total = get().getTotalBeatsCount();
    if (total === 0) return 0;
    const completed = get().getCompletedBeatsCount();
    return Math.round((completed / total) * 100);
  },

  // Series/World Outline State
  seriesOutline: null,
  worldOutline: null,
  seriesStructures: [],
  seriesStructureWithManuscripts: null,
  isLoadingSeriesOutline: false,

  // Series/World Outline Actions
  setSeriesOutline: (seriesOutline) => set({ seriesOutline }),

  setWorldOutline: (worldOutline) => set({ worldOutline }),

  setSeriesStructures: (seriesStructures) => set({ seriesStructures }),

  loadSeriesStructures: async () => {
    try {
      const structures = await seriesOutlineApi.listSeriesStructures();
      set({ seriesStructures: structures });
    } catch (error: any) {
      console.error('Failed to load series structures:', error);
      toast.error('Failed to load series structures');
    }
  },

  loadSeriesOutline: async (seriesId: string) => {
    set({ isLoadingSeriesOutline: true });
    try {
      const outline = await seriesOutlineApi.getActiveSeriesOutline(seriesId);
      set({ seriesOutline: outline, isLoadingSeriesOutline: false });
    } catch (error: any) {
      // No active outline is OK, just clear the state
      set({ seriesOutline: null, isLoadingSeriesOutline: false });
    }
  },

  loadWorldOutline: async (worldId: string) => {
    set({ isLoadingSeriesOutline: true });
    try {
      const outlines = await seriesOutlineApi.getWorldOutlines(worldId);
      // Get the active one or first
      const activeOutline = outlines.find(o => o.is_active) || outlines[0] || null;
      set({ worldOutline: activeOutline, isLoadingSeriesOutline: false });
    } catch (error: any) {
      set({ worldOutline: null, isLoadingSeriesOutline: false });
    }
  },

  loadSeriesStructureWithManuscripts: async (seriesId: string) => {
    set({ isLoadingSeriesOutline: true });
    try {
      const data = await seriesOutlineApi.getSeriesStructureWithManuscripts(seriesId);
      set({ seriesStructureWithManuscripts: data, isLoadingSeriesOutline: false });
    } catch (error: any) {
      console.error('Failed to load series structure:', error);
      set({ seriesStructureWithManuscripts: null, isLoadingSeriesOutline: false });
    }
  },

  createSeriesOutline: async (seriesId: string, structureType: string, genre?: string) => {
    set({ isLoadingSeriesOutline: true });
    try {
      const outline = await seriesOutlineApi.createSeriesOutline(seriesId, {
        series_id: seriesId,
        structure_type: structureType,
        genre,
      });
      set({ seriesOutline: outline, isLoadingSeriesOutline: false });
      toast.success('Series outline created successfully');
      return outline;
    } catch (error: any) {
      console.error('Failed to create series outline:', error);
      set({ isLoadingSeriesOutline: false });
      toast.error('Failed to create series outline: ' + error.message);
      return null;
    }
  },

  createWorldOutline: async (worldId: string, structureType: string, genre?: string) => {
    set({ isLoadingSeriesOutline: true });
    try {
      const outline = await seriesOutlineApi.createWorldOutline(worldId, {
        world_id: worldId,
        structure_type: structureType,
        genre,
      });
      set({ worldOutline: outline, isLoadingSeriesOutline: false });
      toast.success('World outline created successfully');
      return outline;
    } catch (error: any) {
      console.error('Failed to create world outline:', error);
      set({ isLoadingSeriesOutline: false });
      toast.error('Failed to create world outline: ' + error.message);
      return null;
    }
  },
}));

export default useOutlineStore;
