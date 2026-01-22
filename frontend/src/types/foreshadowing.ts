/**
 * Foreshadowing Types
 * Types for foreshadowing setup/payoff pair tracking
 */

export type ForeshadowingType =
  | 'CHEKHOV_GUN'  // Object that must be used
  | 'PROPHECY'     // Prediction to fulfill
  | 'SYMBOL'       // Recurring symbol
  | 'HINT'         // Subtle clue
  | 'PARALLEL';    // Repeated pattern

export interface ForeshadowingPair {
  id: string;
  manuscript_id: string;
  foreshadowing_event_id: string;
  foreshadowing_type: ForeshadowingType;
  foreshadowing_text: string;
  payoff_event_id: string | null;
  payoff_text: string | null;
  is_resolved: boolean;
  confidence: number; // 1-10
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ForeshadowingStats {
  total: number;
  resolved: number;
  unresolved: number;
  by_type: Record<ForeshadowingType, number>;
  average_confidence: number;
}

export interface PayoffSuggestion {
  event_id: string;
  description: string;
  order_index: number;
  keyword_matches: number;
  score: number;
}

// Type labels for UI display
export const FORESHADOWING_TYPE_LABELS: Record<ForeshadowingType, string> = {
  CHEKHOV_GUN: "Chekhov's Gun",
  PROPHECY: 'Prophecy',
  SYMBOL: 'Symbol',
  HINT: 'Hint',
  PARALLEL: 'Parallel',
};

// Type descriptions for UI tooltips
export const FORESHADOWING_TYPE_DESCRIPTIONS: Record<ForeshadowingType, string> = {
  CHEKHOV_GUN: 'An object or detail introduced that must be used later',
  PROPHECY: 'A prediction, vision, or warning that must be fulfilled',
  SYMBOL: 'A recurring motif that gains meaning over time',
  HINT: 'A subtle clue about future events',
  PARALLEL: 'A repeated pattern or situation with variations',
};

// Type icons for UI
export const FORESHADOWING_TYPE_ICONS: Record<ForeshadowingType, string> = {
  CHEKHOV_GUN: '🔫',
  PROPHECY: '🔮',
  SYMBOL: '♾️',
  HINT: '💡',
  PARALLEL: '🔄',
};
