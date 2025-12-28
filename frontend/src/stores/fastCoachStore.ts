/**
 * FastCoach Store - Zustand
 * Manages Fast Coach sidebar state and suggestions
 */

import { create } from 'zustand';

export interface Suggestion {
  type: string;
  severity: string;
  message: string;
  suggestion: string;
  highlight_word?: string;
  metadata?: Record<string, any>;
}

interface FastCoachStore {
  isSidebarOpen: boolean;
  suggestions: Suggestion[];
  isAnalyzing: boolean;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSuggestions: (suggestions: Suggestion[]) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
}

export const useFastCoachStore = create<FastCoachStore>((set) => ({
  isSidebarOpen: false,
  suggestions: [],
  isAnalyzing: false,

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setSidebarOpen: (open) => set({ isSidebarOpen: open }),

  setSuggestions: (suggestions) => set({ suggestions }),

  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
}));
