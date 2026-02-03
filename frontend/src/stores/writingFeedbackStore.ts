/**
 * Writing Feedback Store - Zustand
 * Manages inline writing feedback state including issues, settings, and analysis.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  WritingIssue,
  FeedbackSettings,
  FeedbackStats,
  FeedbackResponse,
} from '@/types/writingFeedback';
import { DEFAULT_FEEDBACK_SETTINGS } from '@/types/writingFeedback';

interface WritingFeedbackState {
  // Issues for the current chapter
  issues: WritingIssue[];

  // Issues grouped by chapter (for manuscript-level view)
  issuesByChapter: Record<string, WritingIssue[]>;

  // Statistics
  stats: FeedbackStats | null;

  // Settings (persisted)
  settings: FeedbackSettings;

  // Loading states
  isAnalyzing: boolean;
  analysisProgress: number;
  lastAnalyzedChapterId: string | null;

  // Enabled state (master toggle)
  isEnabled: boolean;

  // Hovered issue (for editor integration)
  hoveredIssueId: string | null;

  // Dismissed issues (by ID, for this session)
  dismissedIssueIds: Set<string>;

  // Jump to issue request (for editor navigation)
  jumpToIssue: WritingIssue | null;
}

interface WritingFeedbackActions {
  // Issue management
  setIssues: (issues: WritingIssue[]) => void;
  addIssues: (issues: WritingIssue[]) => void;
  clearIssues: () => void;
  setIssuesByChapter: (chapterId: string, issues: WritingIssue[]) => void;

  // Analysis state
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setAnalysisProgress: (progress: number) => void;
  setLastAnalyzedChapterId: (chapterId: string | null) => void;
  setStats: (stats: FeedbackStats | null) => void;

  // Settings
  updateSettings: (settings: Partial<FeedbackSettings>) => void;
  resetSettings: () => void;

  // Toggle feedback on/off
  setEnabled: (enabled: boolean) => void;
  toggleEnabled: () => void;

  // Hover state for editor
  setHoveredIssueId: (id: string | null) => void;

  // Dismiss/ignore issues
  dismissIssue: (issueId: string) => void;
  clearDismissed: () => void;

  // Navigation
  requestJumpToIssue: (issue: WritingIssue) => void;
  clearJumpToIssue: () => void;

  // Dictionary management
  addToDictionary: (word: string) => void;
  removeFromDictionary: (word: string) => void;

  // Rule management
  ignoreRule: (ruleId: string) => void;
  unignoreRule: (ruleId: string) => void;
}

type WritingFeedbackStore = WritingFeedbackState & WritingFeedbackActions;

// Helper to get filtered issues (excluding dismissed)
export function getFilteredIssues(
  issues: WritingIssue[],
  dismissedIds: Set<string>,
  settings: FeedbackSettings
): WritingIssue[] {
  return issues.filter((issue) => {
    // Skip dismissed
    if (dismissedIds.has(issue.id)) {
      return false;
    }

    // Skip by type toggle
    if (issue.type === 'spelling' && !settings.spelling) return false;
    if (issue.type === 'grammar' && !settings.grammar) return false;
    if (issue.type === 'style' && !settings.style) return false;
    if (issue.type === 'word_choice' && !settings.word_choice) return false;
    if (issue.type === 'dialogue' && !settings.dialogue) return false;

    // Skip info-level if disabled
    if (issue.severity === 'info' && !settings.show_info_level) {
      return false;
    }

    // Skip low confidence
    if (issue.confidence && issue.confidence < settings.min_confidence) {
      return false;
    }

    // Skip ignored rules
    if (issue.rule_id && settings.ignored_rules.includes(issue.rule_id)) {
      return false;
    }

    return true;
  });
}

// Helper to get issue at a position
export function getIssueAtPosition(
  issues: WritingIssue[],
  position: number
): WritingIssue | null {
  return issues.find(
    (issue) => position >= issue.start_offset && position < issue.end_offset
  ) || null;
}

// Helper to get issues overlapping a range
export function getIssuesInRange(
  issues: WritingIssue[],
  start: number,
  end: number
): WritingIssue[] {
  return issues.filter(
    (issue) =>
      (issue.start_offset >= start && issue.start_offset < end) ||
      (issue.end_offset > start && issue.end_offset <= end) ||
      (issue.start_offset <= start && issue.end_offset >= end)
  );
}

export const useWritingFeedbackStore = create<WritingFeedbackStore>()(
  persist(
    (set, get) => ({
      // Initial state
      issues: [],
      issuesByChapter: {},
      stats: null,
      settings: DEFAULT_FEEDBACK_SETTINGS,
      isAnalyzing: false,
      analysisProgress: 0,
      lastAnalyzedChapterId: null,
      isEnabled: true,
      hoveredIssueId: null,
      dismissedIssueIds: new Set(),
      jumpToIssue: null,

      // Issue management
      setIssues: (issues) => set({ issues }),

      addIssues: (newIssues) =>
        set((state) => ({
          issues: [...state.issues, ...newIssues],
        })),

      clearIssues: () => set({ issues: [], stats: null }),

      setIssuesByChapter: (chapterId, issues) =>
        set((state) => ({
          issuesByChapter: {
            ...state.issuesByChapter,
            [chapterId]: issues,
          },
        })),

      // Analysis state
      setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

      setAnalysisProgress: (analysisProgress) => set({ analysisProgress }),

      setLastAnalyzedChapterId: (lastAnalyzedChapterId) =>
        set({ lastAnalyzedChapterId }),

      setStats: (stats) => set({ stats }),

      // Settings
      updateSettings: (updates) =>
        set((state) => ({
          settings: { ...state.settings, ...updates },
        })),

      resetSettings: () => set({ settings: DEFAULT_FEEDBACK_SETTINGS }),

      // Toggle
      setEnabled: (isEnabled) => set({ isEnabled }),

      toggleEnabled: () => set((state) => ({ isEnabled: !state.isEnabled })),

      // Hover
      setHoveredIssueId: (hoveredIssueId) => set({ hoveredIssueId }),

      // Dismiss
      dismissIssue: (issueId) =>
        set((state) => {
          const newDismissed = new Set(state.dismissedIssueIds);
          newDismissed.add(issueId);
          return { dismissedIssueIds: newDismissed };
        }),

      clearDismissed: () => set({ dismissedIssueIds: new Set() }),

      // Navigation
      requestJumpToIssue: (issue) => set({ jumpToIssue: issue }),

      clearJumpToIssue: () => set({ jumpToIssue: null }),

      // Dictionary management
      addToDictionary: (word) =>
        set((state) => ({
          settings: {
            ...state.settings,
            custom_dictionary: [...state.settings.custom_dictionary, word],
          },
        })),

      removeFromDictionary: (word) =>
        set((state) => ({
          settings: {
            ...state.settings,
            custom_dictionary: state.settings.custom_dictionary.filter(
              (w) => w !== word
            ),
          },
        })),

      // Rule management
      ignoreRule: (ruleId) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ignored_rules: [...state.settings.ignored_rules, ruleId],
          },
        })),

      unignoreRule: (ruleId) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ignored_rules: state.settings.ignored_rules.filter(
              (r) => r !== ruleId
            ),
          },
        })),
    }),
    {
      name: 'maxwell-writing-feedback',
      // Only persist settings and enabled state
      partialize: (state) => ({
        settings: state.settings,
        isEnabled: state.isEnabled,
      }),
    }
  )
);
