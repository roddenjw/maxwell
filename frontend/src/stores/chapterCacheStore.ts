/**
 * Chapter Cache Store - Client-side caching for instant chapter switching
 * Prevents race conditions and data loss when switching between chapters
 */

import { create } from 'zustand';

interface CachedChapter {
  content: string;
  lexicalState: string | null;
  loadedAt: number;
  wordCount: number;
}

interface ChapterCacheStore {
  // State
  cache: Record<string, CachedChapter>;
  loadingChapterId: string | null;

  // Actions
  getFromCache: (chapterId: string) => CachedChapter | null;
  setCache: (chapterId: string, data: CachedChapter) => void;
  invalidate: (chapterId: string) => void;
  invalidateAll: () => void;
  setLoading: (chapterId: string | null) => void;
  isLoading: () => boolean;
  isLoadingChapter: (chapterId: string) => boolean;
}

// Cache expiry time: 5 minutes
const CACHE_EXPIRY_MS = 5 * 60 * 1000;

export const useChapterCacheStore = create<ChapterCacheStore>((set, get) => ({
  // Initial State
  cache: {},
  loadingChapterId: null,

  // Get cached chapter (returns null if expired or not found)
  getFromCache: (chapterId: string) => {
    const { cache } = get();
    const cached = cache[chapterId];

    if (!cached) return null;

    // Check if cache is expired
    const now = Date.now();
    if (now - cached.loadedAt > CACHE_EXPIRY_MS) {
      // Expired - remove from cache and return null
      set((state) => {
        const newCache = { ...state.cache };
        delete newCache[chapterId];
        return { cache: newCache };
      });
      return null;
    }

    return cached;
  },

  // Set cache for a chapter
  setCache: (chapterId: string, data: CachedChapter) => {
    set((state) => ({
      cache: {
        ...state.cache,
        [chapterId]: {
          ...data,
          loadedAt: Date.now(),
        },
      },
    }));
  },

  // Invalidate cache for a specific chapter (e.g., after save)
  invalidate: (chapterId: string) => {
    set((state) => {
      const newCache = { ...state.cache };
      delete newCache[chapterId];
      return { cache: newCache };
    });
  },

  // Invalidate all cached chapters
  invalidateAll: () => {
    set({ cache: {} });
  },

  // Set loading state
  setLoading: (chapterId: string | null) => {
    set({ loadingChapterId: chapterId });
  },

  // Check if any chapter is loading
  isLoading: () => {
    const { loadingChapterId } = get();
    return loadingChapterId !== null;
  },

  // Check if a specific chapter is loading
  isLoadingChapter: (chapterId: string) => {
    const { loadingChapterId } = get();
    return loadingChapterId === chapterId;
  },
}));
