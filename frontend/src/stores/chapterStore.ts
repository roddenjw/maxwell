/**
 * Chapter Store - Zustand
 * Manages hierarchical chapter/folder structure
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Chapter, ChapterTree } from '@/lib/api';

interface ChapterStore {
  chapters: Chapter[];
  chapterTree: ChapterTree[];
  currentChapterId: string | null;
  expandedFolders: Set<string>;

  // Actions
  setChapters: (chapters: Chapter[]) => void;
  setChapterTree: (tree: ChapterTree[]) => void;
  setCurrentChapter: (id: string | null) => void;
  addChapter: (chapter: Chapter) => void;
  updateChapter: (id: string, updates: Partial<Chapter>) => void;
  removeChapter: (id: string) => void;
  toggleFolder: (id: string) => void;
  expandFolder: (id: string) => void;
  collapseFolder: (id: string) => void;
  getCurrentChapter: () => Chapter | undefined;
}

export const useChapterStore = create<ChapterStore>()(
  persist(
    (set, get) => ({
      chapters: [],
      chapterTree: [],
      currentChapterId: null,
      expandedFolders: new Set<string>(),

  setChapters: (chapters) => set({ chapters }),

  setChapterTree: (tree) => set({ chapterTree: tree }),

  setCurrentChapter: (id) => set({ currentChapterId: id }),

  addChapter: (chapter) =>
    set((state) => ({
      chapters: [...state.chapters, chapter],
    })),

  updateChapter: (id, updates) =>
    set((state) => ({
      chapters: state.chapters.map((chapter) =>
        chapter.id === id ? { ...chapter, ...updates } : chapter
      ),
    })),

  removeChapter: (id) =>
    set((state) => ({
      chapters: state.chapters.filter((chapter) => chapter.id !== id),
      currentChapterId: state.currentChapterId === id ? null : state.currentChapterId,
    })),

  toggleFolder: (id) =>
    set((state) => {
      const newExpanded = new Set(state.expandedFolders);
      if (newExpanded.has(id)) {
        newExpanded.delete(id);
      } else {
        newExpanded.add(id);
      }
      return { expandedFolders: newExpanded };
    }),

  expandFolder: (id) =>
    set((state) => {
      const newExpanded = new Set(state.expandedFolders);
      newExpanded.add(id);
      return { expandedFolders: newExpanded };
    }),

  collapseFolder: (id) =>
    set((state) => {
      const newExpanded = new Set(state.expandedFolders);
      newExpanded.delete(id);
      return { expandedFolders: newExpanded };
    }),

  getCurrentChapter: () => {
    const state = get();
    return state.chapters.find((ch) => ch.id === state.currentChapterId);
  },
}),
    {
      name: 'maxwell-chapter-storage',
      storage: createJSONStorage(() => localStorage),
      // Custom serializer to handle Set
      serialize: (state) => {
        return JSON.stringify({
          ...state,
          state: {
            ...state.state,
            expandedFolders: Array.from(state.state.expandedFolders),
          },
        });
      },
      // Custom deserializer to convert array back to Set
      deserialize: (str) => {
        const parsed = JSON.parse(str);
        return {
          ...parsed,
          state: {
            ...parsed.state,
            expandedFolders: new Set(parsed.state.expandedFolders || []),
          },
        };
      },
    }
  )
);
