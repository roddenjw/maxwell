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
  start_char?: number;
  end_char?: number;
  line?: number;
  replacement?: string;
  metadata?: Record<string, any>;
}

interface JumpRequest {
  startChar: number;
  endChar: number;
  timestamp: number; // Used to detect new requests
}

interface ApplyReplacementRequest {
  startChar: number;
  endChar: number;
  replacement: string;
  timestamp: number; // Used to detect new requests
}

interface FastCoachStore {
  isSidebarOpen: boolean;
  suggestions: Suggestion[];
  isAnalyzing: boolean;
  jumpRequest: JumpRequest | null;
  applyReplacementRequest: ApplyReplacementRequest | null;

  // Filters
  filterTypes: Set<string>; // Empty = all types shown
  filterSeverities: Set<string>; // Empty = all severities shown
  collapsedSections: Set<string>; // Section keys that are collapsed
  sortBy: 'severity' | 'type' | 'position';

  // Dismissed suggestions (persisted across re-analysis)
  dismissedSuggestionIds: Set<string>;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSuggestions: (suggestions: Suggestion[]) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  requestJumpToText: (startChar: number, endChar: number) => void;
  clearJumpRequest: () => void;
  requestApplyReplacement: (startChar: number, endChar: number, replacement: string) => void;
  clearApplyReplacementRequest: () => void;

  // Filter actions
  toggleFilterType: (type: string) => void;
  toggleFilterSeverity: (severity: string) => void;
  clearFilters: () => void;
  toggleSectionCollapsed: (section: string) => void;
  setSortBy: (sortBy: 'severity' | 'type' | 'position') => void;

  // Dismiss actions
  dismissSuggestion: (suggestion: Suggestion) => void;
  clearDismissed: () => void;
}

/**
 * Generate a unique ID for a suggestion based on its content
 * This allows us to track dismissed suggestions across re-analysis
 */
export function getSuggestionId(suggestion: Suggestion): string {
  // Use type + message + highlight_word as a unique identifier
  const parts = [
    suggestion.type,
    suggestion.message,
    suggestion.highlight_word || '',
  ];
  return parts.join('|');
}

export const useFastCoachStore = create<FastCoachStore>((set) => ({
  isSidebarOpen: false,
  suggestions: [],
  isAnalyzing: false,
  jumpRequest: null,
  applyReplacementRequest: null,

  // Filter defaults
  filterTypes: new Set(),
  filterSeverities: new Set(),
  collapsedSections: new Set(),
  sortBy: 'severity',
  dismissedSuggestionIds: new Set(),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setSidebarOpen: (open) => set({ isSidebarOpen: open }),

  setSuggestions: (suggestions) => set({ suggestions }),

  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  requestJumpToText: (startChar, endChar) =>
    set({ jumpRequest: { startChar, endChar, timestamp: Date.now() } }),

  clearJumpRequest: () => set({ jumpRequest: null }),

  requestApplyReplacement: (startChar, endChar, replacement) =>
    set({ applyReplacementRequest: { startChar, endChar, replacement, timestamp: Date.now() } }),

  clearApplyReplacementRequest: () => set({ applyReplacementRequest: null }),

  // Filter actions
  toggleFilterType: (type) =>
    set((state) => {
      const newFilterTypes = new Set(state.filterTypes);
      if (newFilterTypes.has(type)) {
        newFilterTypes.delete(type);
      } else {
        newFilterTypes.add(type);
      }
      return { filterTypes: newFilterTypes };
    }),

  toggleFilterSeverity: (severity) =>
    set((state) => {
      const newFilterSeverities = new Set(state.filterSeverities);
      if (newFilterSeverities.has(severity)) {
        newFilterSeverities.delete(severity);
      } else {
        newFilterSeverities.add(severity);
      }
      return { filterSeverities: newFilterSeverities };
    }),

  clearFilters: () =>
    set({ filterTypes: new Set(), filterSeverities: new Set() }),

  toggleSectionCollapsed: (section) =>
    set((state) => {
      const newCollapsed = new Set(state.collapsedSections);
      if (newCollapsed.has(section)) {
        newCollapsed.delete(section);
      } else {
        newCollapsed.add(section);
      }
      return { collapsedSections: newCollapsed };
    }),

  setSortBy: (sortBy) => set({ sortBy }),

  // Dismiss actions
  dismissSuggestion: (suggestion) =>
    set((state) => {
      const id = getSuggestionId(suggestion);
      const newDismissed = new Set(state.dismissedSuggestionIds);
      newDismissed.add(id);
      return { dismissedSuggestionIds: newDismissed };
    }),

  clearDismissed: () => set({ dismissedSuggestionIds: new Set() }),
}));
