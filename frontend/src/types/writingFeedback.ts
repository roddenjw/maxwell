/**
 * Types for the Writing Feedback system.
 * Used for inline highlighting of grammar, spelling, style, and other issues.
 */

// Issue Types - matches backend IssueType enum
export type WritingIssueType =
  | 'spelling'
  | 'grammar'
  | 'style'
  | 'word_choice'
  | 'dialogue'
  | 'consistency'
  | 'readability'
  | 'sentence_variety'
  | 'overused_phrase';

// Severity levels - matches backend IssueSeverity enum
export type IssueSeverity = 'error' | 'warning' | 'info';

/**
 * A writing issue detected by the analysis service.
 * Contains position, message, suggestions, and teaching content.
 */
export interface WritingIssue {
  id: string;
  type: WritingIssueType;
  severity: IssueSeverity;

  // Position in text (for highlighting)
  start_offset: number;
  end_offset: number;

  // Issue details
  message: string;
  original_text: string;
  suggestions: string[];

  // Teaching moment (optional)
  teaching_point?: string;

  // Metadata for filtering/ignoring
  rule_id?: string;
  category?: string;
  confidence?: number;

  // Chapter info (for manuscript-level analysis)
  chapter_id?: string;
  chapter_title?: string;
}

/**
 * Statistics about issues found.
 */
export interface FeedbackStats {
  total: number;
  spelling: number;
  grammar: number;
  style: number;
  word_choice: number;
  dialogue: number;
  readability: number;
  sentence_variety: number;
  overused_phrase: number;
  errors: number;
  warnings: number;
  info: number;
}

/**
 * Response from the writing feedback API.
 */
export interface FeedbackResponse {
  issues: WritingIssue[];
  stats: FeedbackStats;
  analysis_time_ms: number;
  text_length: number;
  chapters_analyzed?: number;
}

/**
 * Settings for writing feedback.
 * Stored per-manuscript in manuscript.settings.writing_feedback
 */
export interface FeedbackSettings {
  // Enable/disable by type
  spelling: boolean;
  grammar: boolean;
  style: boolean;
  word_choice: boolean;
  dialogue: boolean;

  // Sensitivity
  show_info_level: boolean;
  min_confidence: number;

  // Custom dictionary for fiction terms
  custom_dictionary: string[];

  // Ignored rules
  ignored_rules: string[];

  // Language
  language: string;
}

/**
 * Default feedback settings.
 */
export const DEFAULT_FEEDBACK_SETTINGS: FeedbackSettings = {
  spelling: true,
  grammar: true,
  style: true,
  word_choice: true,
  dialogue: true,
  show_info_level: false,
  min_confidence: 0.5,
  custom_dictionary: [],
  ignored_rules: [],
  language: 'en-US',
};

/**
 * Configuration for each issue type (colors, icons, labels).
 */
export interface IssueTypeConfig {
  label: string;
  icon: string;
  underlineClass: string;
  headerClass: string;
  badgeClass: string;
}

/**
 * Visual configuration for each issue type.
 */
export const ISSUE_TYPE_CONFIG: Record<WritingIssueType, IssueTypeConfig> = {
  spelling: {
    label: 'Spelling',
    icon: '🔤',
    underlineClass: 'writing-issue-spelling',
    headerClass: 'text-red-600',
    badgeClass: 'bg-red-100 text-red-700',
  },
  grammar: {
    label: 'Grammar',
    icon: '📝',
    underlineClass: 'writing-issue-grammar',
    headerClass: 'text-blue-600',
    badgeClass: 'bg-blue-100 text-blue-700',
  },
  style: {
    label: 'Style',
    icon: '✨',
    underlineClass: 'writing-issue-style',
    headerClass: 'text-amber-600',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  word_choice: {
    label: 'Word Choice',
    icon: '💬',
    underlineClass: 'writing-issue-style',
    headerClass: 'text-amber-600',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  dialogue: {
    label: 'Dialogue',
    icon: '🗣️',
    underlineClass: 'writing-issue-dialogue',
    headerClass: 'text-teal-600',
    badgeClass: 'bg-teal-100 text-teal-700',
  },
  consistency: {
    label: 'Consistency',
    icon: '🔗',
    underlineClass: 'writing-issue-consistency',
    headerClass: 'text-purple-600',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
  readability: {
    label: 'Readability',
    icon: '📊',
    underlineClass: 'writing-issue-readability',
    headerClass: 'text-gray-600',
    badgeClass: 'bg-gray-100 text-gray-700',
  },
  sentence_variety: {
    label: 'Sentence Variety',
    icon: '📐',
    underlineClass: 'writing-issue-style',
    headerClass: 'text-amber-600',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  overused_phrase: {
    label: 'Overused Phrase',
    icon: '🔄',
    underlineClass: 'writing-issue-style',
    headerClass: 'text-amber-600',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
};

/**
 * Get the configuration for an issue type.
 */
export function getIssueTypeConfig(type: WritingIssueType): IssueTypeConfig {
  return ISSUE_TYPE_CONFIG[type] || ISSUE_TYPE_CONFIG.grammar;
}

/**
 * Get the CSS class for underlining an issue.
 */
export function getUnderlineClass(type: WritingIssueType): string {
  return ISSUE_TYPE_CONFIG[type]?.underlineClass || 'writing-issue-grammar';
}
