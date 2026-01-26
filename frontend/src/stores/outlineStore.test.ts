/**
 * Tests for Outline Store
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import { useOutlineStore } from './outlineStore';
import type { Outline, PlotBeat, OutlineProgress, BeatFeedback } from '@/types/outline';

// Mock the API module
vi.mock('@/lib/api', () => ({
  outlineApi: {
    getActiveOutline: vi.fn(),
    getProgress: vi.fn(),
    updateBeat: vi.fn(),
    createScene: vi.fn(),
    deleteBeat: vi.fn(),
  },
  seriesOutlineApi: {
    listSeriesStructures: vi.fn(),
    getActiveSeriesOutline: vi.fn(),
    getWorldOutlines: vi.fn(),
    getSeriesStructureWithManuscripts: vi.fn(),
    createSeriesOutline: vi.fn(),
    createWorldOutline: vi.fn(),
  },
  aiApi: {
    analyzeOutline: vi.fn(),
    getBeatSuggestions: vi.fn(),
    analyzeOutlineWithFeedback: vi.fn(),
  },
}));

// Mock toast
vi.mock('./toastStore', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('OutlineStore', () => {
  beforeEach(() => {
    useOutlineStore.setState({
      outline: null,
      progress: null,
      isLoading: false,
      isSidebarOpen: false,
      outlineReferenceSidebarOpen: false,
      beatContextPanelCollapsed: false,
      expandedBeatId: null,
      error: null,
      notifiedCompletedBeats: new Set(),
      aiSuggestions: null,
      beatSuggestions: new Map(),
      isAnalyzing: false,
      apiKey: null,
      beatFeedback: new Map(),
      seriesOutline: null,
      worldOutline: null,
      seriesStructures: [],
      seriesStructureWithManuscripts: null,
      isLoadingSeriesOutline: false,
    });

    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have null outline', () => {
      const { outline } = useOutlineStore.getState();
      expect(outline).toBeNull();
    });

    it('should have null progress', () => {
      const { progress } = useOutlineStore.getState();
      expect(progress).toBeNull();
    });

    it('should not be loading', () => {
      const { isLoading } = useOutlineStore.getState();
      expect(isLoading).toBe(false);
    });

    it('should have sidebar closed', () => {
      const { isSidebarOpen } = useOutlineStore.getState();
      expect(isSidebarOpen).toBe(false);
    });

    it('should have null error', () => {
      const { error } = useOutlineStore.getState();
      expect(error).toBeNull();
    });

    it('should not be analyzing', () => {
      const { isAnalyzing } = useOutlineStore.getState();
      expect(isAnalyzing).toBe(false);
    });
  });

  describe('Synchronous Actions', () => {
    describe('setOutline', () => {
      it('should set outline and clear error', () => {
        const mockOutline: Outline = {
          id: 'outline-1',
          manuscript_id: 'ms-1',
          structure_type: 'three_act',
          is_active: true,
          plot_beats: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useOutlineStore.setState({ error: 'Previous error' });
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const state = useOutlineStore.getState();
        expect(state.outline).toEqual(mockOutline);
        expect(state.error).toBeNull();
      });
    });

    describe('setProgress', () => {
      it('should set progress', () => {
        const mockProgress: OutlineProgress = {
          total_beats: 10,
          completed_beats: 5,
          completion_percentage: 50,
          total_target_words: 80000,
          current_words: 40000,
          word_progress_percentage: 50,
        };

        act(() => {
          useOutlineStore.getState().setProgress(mockProgress);
        });

        const { progress } = useOutlineStore.getState();
        expect(progress).toEqual(mockProgress);
      });
    });

    describe('setLoading', () => {
      it('should set loading state', () => {
        act(() => {
          useOutlineStore.getState().setLoading(true);
        });

        const { isLoading } = useOutlineStore.getState();
        expect(isLoading).toBe(true);
      });
    });

    describe('setSidebarOpen', () => {
      it('should set sidebar open state', () => {
        act(() => {
          useOutlineStore.getState().setSidebarOpen(true);
        });

        const { isSidebarOpen } = useOutlineStore.getState();
        expect(isSidebarOpen).toBe(true);
      });
    });

    describe('toggleSidebar', () => {
      it('should toggle sidebar state', () => {
        const initial = useOutlineStore.getState().isSidebarOpen;

        act(() => {
          useOutlineStore.getState().toggleSidebar();
        });

        expect(useOutlineStore.getState().isSidebarOpen).toBe(!initial);
      });
    });

    describe('setOutlineReferenceSidebarOpen', () => {
      it('should set outline reference sidebar state', () => {
        act(() => {
          useOutlineStore.getState().setOutlineReferenceSidebarOpen(true);
        });

        const { outlineReferenceSidebarOpen } = useOutlineStore.getState();
        expect(outlineReferenceSidebarOpen).toBe(true);
      });
    });

    describe('toggleOutlineReferenceSidebar', () => {
      it('should toggle outline reference sidebar', () => {
        const initial = useOutlineStore.getState().outlineReferenceSidebarOpen;

        act(() => {
          useOutlineStore.getState().toggleOutlineReferenceSidebar();
        });

        expect(useOutlineStore.getState().outlineReferenceSidebarOpen).toBe(!initial);
      });
    });

    describe('setBeatContextPanelCollapsed', () => {
      it('should set beat context panel collapsed state', () => {
        act(() => {
          useOutlineStore.getState().setBeatContextPanelCollapsed(true);
        });

        const { beatContextPanelCollapsed } = useOutlineStore.getState();
        expect(beatContextPanelCollapsed).toBe(true);
      });
    });

    describe('toggleBeatContextPanel', () => {
      it('should toggle beat context panel', () => {
        const initial = useOutlineStore.getState().beatContextPanelCollapsed;

        act(() => {
          useOutlineStore.getState().toggleBeatContextPanel();
        });

        expect(useOutlineStore.getState().beatContextPanelCollapsed).toBe(!initial);
      });
    });

    describe('setExpandedBeat', () => {
      it('should set expanded beat id', () => {
        act(() => {
          useOutlineStore.getState().setExpandedBeat('beat-1');
        });

        const { expandedBeatId } = useOutlineStore.getState();
        expect(expandedBeatId).toBe('beat-1');
      });
    });

    describe('setError', () => {
      it('should set error message', () => {
        act(() => {
          useOutlineStore.getState().setError('Something went wrong');
        });

        const { error } = useOutlineStore.getState();
        expect(error).toBe('Something went wrong');
      });
    });

    describe('clearOutline', () => {
      it('should reset outline-related state', () => {
        act(() => {
          useOutlineStore.setState({
            outline: { id: 'test' } as any,
            progress: { total_beats: 10 } as any,
            expandedBeatId: 'beat-1',
            isSidebarOpen: true,
            error: 'error',
            aiSuggestions: { test: true } as any,
          });
          useOutlineStore.getState().clearOutline();
        });

        const state = useOutlineStore.getState();
        expect(state.outline).toBeNull();
        expect(state.progress).toBeNull();
        expect(state.expandedBeatId).toBeNull();
        expect(state.isSidebarOpen).toBe(false);
        expect(state.error).toBeNull();
        expect(state.aiSuggestions).toBeNull();
      });
    });
  });

  describe('API Key Actions', () => {
    describe('setApiKey', () => {
      it('should set API key and store in localStorage', () => {
        act(() => {
          useOutlineStore.getState().setApiKey('test-api-key');
        });

        const { apiKey } = useOutlineStore.getState();
        expect(apiKey).toBe('test-api-key');
        expect(localStorageMock.setItem).toHaveBeenCalledWith('openrouter_api_key', 'test-api-key');
      });
    });

    describe('getApiKey', () => {
      it('should return stored API key', () => {
        act(() => {
          useOutlineStore.setState({ apiKey: 'stored-key' });
        });

        const result = useOutlineStore.getState().getApiKey();
        expect(result).toBe('stored-key');
      });

      it('should load from localStorage if not in state', () => {
        localStorageMock.getItem.mockReturnValue('localStorage-key');

        const result = useOutlineStore.getState().getApiKey();
        expect(result).toBe('localStorage-key');
        expect(useOutlineStore.getState().apiKey).toBe('localStorage-key');
      });

      it('should return null if no key available', () => {
        localStorageMock.getItem.mockReturnValue(null);

        const result = useOutlineStore.getState().getApiKey();
        expect(result).toBeNull();
      });
    });
  });

  describe('Feedback Actions', () => {
    describe('setBeatFeedback', () => {
      it('should set beat feedback', () => {
        const feedback: BeatFeedback = {
          liked: ['description1'],
          disliked: [],
          notes: 'Test notes',
        };

        act(() => {
          useOutlineStore.getState().setBeatFeedback('Opening', feedback);
        });

        const stored = useOutlineStore.getState().beatFeedback.get('Opening');
        expect(stored).toEqual(feedback);
      });
    });

    describe('addBeatFeedbackLike', () => {
      it('should add like to beat feedback', () => {
        act(() => {
          useOutlineStore.getState().addBeatFeedbackLike('Opening', 'Good description');
        });

        const feedback = useOutlineStore.getState().beatFeedback.get('Opening');
        expect(feedback?.liked).toContain('Good description');
      });

      it('should toggle like off if already liked', () => {
        act(() => {
          useOutlineStore.getState().addBeatFeedbackLike('Opening', 'Good description');
          useOutlineStore.getState().addBeatFeedbackLike('Opening', 'Good description');
        });

        const feedback = useOutlineStore.getState().beatFeedback.get('Opening');
        expect(feedback?.liked).not.toContain('Good description');
      });
    });

    describe('addBeatFeedbackDislike', () => {
      it('should add dislike to beat feedback', () => {
        act(() => {
          useOutlineStore.getState().addBeatFeedbackDislike('Opening', 'Bad description');
        });

        const feedback = useOutlineStore.getState().beatFeedback.get('Opening');
        expect(feedback?.disliked).toContain('Bad description');
      });
    });

    describe('setBeatFeedbackNotes', () => {
      it('should set notes for beat feedback', () => {
        act(() => {
          useOutlineStore.getState().setBeatFeedbackNotes('Opening', 'These are my notes');
        });

        const feedback = useOutlineStore.getState().beatFeedback.get('Opening');
        expect(feedback?.notes).toBe('These are my notes');
      });
    });

    describe('clearBeatFeedback', () => {
      it('should clear specific beat feedback', () => {
        act(() => {
          useOutlineStore.getState().setBeatFeedback('Opening', { liked: ['test'], disliked: [], notes: '' });
          useOutlineStore.getState().setBeatFeedback('Climax', { liked: [], disliked: ['test'], notes: '' });
          useOutlineStore.getState().clearBeatFeedback('Opening');
        });

        expect(useOutlineStore.getState().beatFeedback.has('Opening')).toBe(false);
        expect(useOutlineStore.getState().beatFeedback.has('Climax')).toBe(true);
      });

      it('should clear all beat feedback when no beatName provided', () => {
        act(() => {
          useOutlineStore.getState().setBeatFeedback('Opening', { liked: ['test'], disliked: [], notes: '' });
          useOutlineStore.getState().setBeatFeedback('Climax', { liked: [], disliked: ['test'], notes: '' });
          useOutlineStore.getState().clearBeatFeedback();
        });

        expect(useOutlineStore.getState().beatFeedback.size).toBe(0);
      });
    });

    describe('hasFeedback', () => {
      it('should return true when there is feedback', () => {
        act(() => {
          useOutlineStore.getState().setBeatFeedback('Opening', { liked: ['test'], disliked: [], notes: '' });
        });

        expect(useOutlineStore.getState().hasFeedback()).toBe(true);
      });

      it('should return false when no feedback', () => {
        expect(useOutlineStore.getState().hasFeedback()).toBe(false);
      });

      it('should return false when feedback is empty', () => {
        act(() => {
          useOutlineStore.getState().setBeatFeedback('Opening', { liked: [], disliked: [], notes: '' });
        });

        expect(useOutlineStore.getState().hasFeedback()).toBe(false);
      });
    });
  });

  describe('AI Actions', () => {
    describe('clearAISuggestions', () => {
      it('should clear AI suggestions and beat suggestions', () => {
        act(() => {
          useOutlineStore.setState({
            aiSuggestions: { test: true } as any,
            beatSuggestions: new Map([['beat-1', { suggestions: [] }]]) as any,
          });
          useOutlineStore.getState().clearAISuggestions();
        });

        const state = useOutlineStore.getState();
        expect(state.aiSuggestions).toBeNull();
        expect(state.beatSuggestions.size).toBe(0);
      });
    });

    describe('markPlotHoleResolved', () => {
      it('should mark plot hole as resolved', () => {
        const aiSuggestions = {
          plot_holes: [
            { description: 'Hole 1', resolved: false },
            { description: 'Hole 2', resolved: false },
          ],
        };

        act(() => {
          useOutlineStore.setState({ aiSuggestions: aiSuggestions as any });
          useOutlineStore.getState().markPlotHoleResolved(0);
        });

        const { aiSuggestions: updated } = useOutlineStore.getState();
        expect(updated?.plot_holes[0].resolved).toBe(true);
        expect(updated?.plot_holes[1].resolved).toBe(false);
      });

      it('should do nothing if no AI suggestions', () => {
        act(() => {
          useOutlineStore.getState().markPlotHoleResolved(0);
        });

        // Should not throw
        expect(useOutlineStore.getState().aiSuggestions).toBeNull();
      });
    });
  });

  describe('Computed Values', () => {
    const mockOutline: Outline = {
      id: 'outline-1',
      manuscript_id: 'ms-1',
      structure_type: 'three_act',
      is_active: true,
      plot_beats: [
        { id: 'beat-1', beat_name: 'Opening', is_completed: true, chapter_id: 'ch-1' } as PlotBeat,
        { id: 'beat-2', beat_name: 'Climax', is_completed: false, chapter_id: 'ch-2' } as PlotBeat,
        { id: 'beat-3', beat_name: 'Resolution', is_completed: true, chapter_id: null } as PlotBeat,
      ],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    describe('getCompletedBeatsCount', () => {
      it('should return count of completed beats', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const count = useOutlineStore.getState().getCompletedBeatsCount();
        expect(count).toBe(2);
      });

      it('should return 0 when no outline', () => {
        const count = useOutlineStore.getState().getCompletedBeatsCount();
        expect(count).toBe(0);
      });
    });

    describe('getTotalBeatsCount', () => {
      it('should return total beat count', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const count = useOutlineStore.getState().getTotalBeatsCount();
        expect(count).toBe(3);
      });

      it('should return 0 when no outline', () => {
        const count = useOutlineStore.getState().getTotalBeatsCount();
        expect(count).toBe(0);
      });
    });

    describe('getBeatById', () => {
      it('should return beat by id', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const beat = useOutlineStore.getState().getBeatById('beat-1');
        expect(beat?.beat_name).toBe('Opening');
      });

      it('should return undefined for non-existent beat', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const beat = useOutlineStore.getState().getBeatById('non-existent');
        expect(beat).toBeUndefined();
      });
    });

    describe('getBeatByChapterId', () => {
      it('should return beat by chapter id', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const beat = useOutlineStore.getState().getBeatByChapterId('ch-1');
        expect(beat?.beat_name).toBe('Opening');
      });

      it('should return null for non-existent chapter', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const beat = useOutlineStore.getState().getBeatByChapterId('non-existent');
        expect(beat).toBeNull();
      });
    });

    describe('getCompletionPercentage', () => {
      it('should calculate completion percentage', () => {
        act(() => {
          useOutlineStore.getState().setOutline(mockOutline);
        });

        const percentage = useOutlineStore.getState().getCompletionPercentage();
        expect(percentage).toBe(67); // 2/3 rounded
      });

      it('should return 0 when no beats', () => {
        const percentage = useOutlineStore.getState().getCompletionPercentage();
        expect(percentage).toBe(0);
      });
    });
  });

  describe('Series/World Outline Actions', () => {
    describe('setSeriesOutline', () => {
      it('should set series outline', () => {
        const mockOutline: Outline = {
          id: 'series-outline-1',
          series_id: 'series-1',
          structure_type: 'three_act',
          is_active: true,
          plot_beats: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useOutlineStore.getState().setSeriesOutline(mockOutline);
        });

        const { seriesOutline } = useOutlineStore.getState();
        expect(seriesOutline).toEqual(mockOutline);
      });
    });

    describe('setWorldOutline', () => {
      it('should set world outline', () => {
        const mockOutline: Outline = {
          id: 'world-outline-1',
          world_id: 'world-1',
          structure_type: 'hero_journey',
          is_active: true,
          plot_beats: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useOutlineStore.getState().setWorldOutline(mockOutline);
        });

        const { worldOutline } = useOutlineStore.getState();
        expect(worldOutline).toEqual(mockOutline);
      });
    });

    describe('setSeriesStructures', () => {
      it('should set series structures', () => {
        const structures = [
          { id: 'struct-1', name: 'Three Act', slug: 'three_act' },
          { id: 'struct-2', name: 'Hero Journey', slug: 'hero_journey' },
        ];

        act(() => {
          useOutlineStore.getState().setSeriesStructures(structures as any);
        });

        const { seriesStructures } = useOutlineStore.getState();
        expect(seriesStructures).toHaveLength(2);
      });
    });
  });
});
