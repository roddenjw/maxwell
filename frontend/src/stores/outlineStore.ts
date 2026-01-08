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
  BeatSuggestionsResult
} from '@/types/outline';
import { outlineApi } from '@/lib/api';
import { toast } from './toastStore';

interface OutlineStore {
  // State
  outline: Outline | null;
  progress: OutlineProgress | null;
  isLoading: boolean;
  isSidebarOpen: boolean;
  expandedBeatId: string | null;
  error: string | null;

  // AI State
  aiSuggestions: AIAnalysisResult | null;
  beatSuggestions: Map<string, BeatSuggestionsResult>;  // beatId -> suggestions
  isAnalyzing: boolean;
  apiKey: string | null;

  // Actions
  setOutline: (outline: Outline | null) => void;
  setProgress: (progress: OutlineProgress | null) => void;
  setLoading: (isLoading: boolean) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  toggleSidebar: () => void;
  setExpandedBeat: (beatId: string | null) => void;
  setError: (error: string | null) => void;

  // Async Actions
  loadOutline: (manuscriptId: string) => Promise<void>;
  loadProgress: (outlineId: string) => Promise<void>;
  updateBeat: (beatId: string, updates: PlotBeatUpdate) => Promise<void>;
  clearOutline: () => void;

  // AI Actions
  setApiKey: (apiKey: string) => void;
  getApiKey: () => string | null;
  runAIAnalysis: (outlineId: string, analysisTypes?: string[]) => Promise<void>;
  getBeatAISuggestions: (beatId: string) => Promise<void>;
  clearAISuggestions: () => void;
  markPlotHoleResolved: (index: number) => void;

  // Computed
  getCompletedBeatsCount: () => number;
  getTotalBeatsCount: () => number;
  getBeatById: (beatId: string) => PlotBeat | undefined;
  getCompletionPercentage: () => number;
}

export const useOutlineStore = create<OutlineStore>((set, get) => ({
  // Initial State
  outline: null,
  progress: null,
  isLoading: false,
  isSidebarOpen: false,
  expandedBeatId: null,
  error: null,

  // AI Initial State
  aiSuggestions: null,
  beatSuggestions: new Map(),
  isAnalyzing: false,
  apiKey: typeof window !== 'undefined' ? localStorage.getItem('openrouter_api_key') : null,

  // Synchronous Actions
  setOutline: (outline) => set({ outline, error: null }),

  setProgress: (progress) => set({ progress }),

  setLoading: (isLoading) => set({ isLoading }),

  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

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

  loadProgress: async (outlineId: string) => {
    try {
      const progress = await outlineApi.getProgress(outlineId);
      set({ progress });
    } catch (error: any) {
      console.error('Failed to load outline progress:', error);
      // Don't show error toast for progress - it's not critical
    }
  },

  updateBeat: async (beatId: string, updates: PlotBeatUpdate) => {
    try {
      const updatedBeat = await outlineApi.updateBeat(beatId, updates);

      // Update the beat in the local state
      const currentOutline = get().outline;
      if (currentOutline) {
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
      }
    } catch (error: any) {
      console.error('Failed to update beat:', error);
      toast.error('Failed to update plot beat');
      throw error;
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

  // Computed Values
  getCompletedBeatsCount: () => {
    const outline = get().outline;
    if (!outline) return 0;
    return outline.plot_beats.filter((beat) => beat.is_completed).length;
  },

  getTotalBeatsCount: () => {
    const outline = get().outline;
    if (!outline) return 0;
    return outline.plot_beats.length;
  },

  getBeatById: (beatId: string) => {
    const outline = get().outline;
    if (!outline) return undefined;
    return outline.plot_beats.find((beat) => beat.id === beatId);
  },

  getCompletionPercentage: () => {
    const total = get().getTotalBeatsCount();
    if (total === 0) return 0;
    const completed = get().getCompletedBeatsCount();
    return Math.round((completed / total) * 100);
  },
}));

export default useOutlineStore;
