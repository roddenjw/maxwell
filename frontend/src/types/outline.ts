/**
 * Outline and Plot Beat Type Definitions
 * Matches backend API response structure from app/models/outline.py
 */

// Item type constants
export type ItemType = 'BEAT' | 'SCENE';

// Outline scope constants
export type OutlineScope = 'MANUSCRIPT' | 'SERIES' | 'WORLD';

// Series arc types
export type ArcType = 'trilogy' | 'duology' | 'ongoing' | 'saga' | string;

export interface PlotBeat {
  id: string;
  outline_id: string;
  item_type: ItemType;  // BEAT (major story beat) or SCENE (user-added between beats)
  parent_beat_id: string | null;  // For scenes: the beat this scene follows
  beat_name: string;
  beat_label: string;
  beat_description: string;
  target_position_percent: number;
  target_word_count: number;
  actual_word_count: number;
  order_index: number;
  user_notes: string;
  content_summary: string;
  chapter_id: string | null;
  is_completed: boolean;
  // Series outline linking
  linked_manuscript_outline_id: string | null;
  target_book_index: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface SceneCreate {
  scene_label: string;
  scene_description?: string;
  after_beat_id: string;
  target_word_count?: number;
  user_notes?: string;
}

export interface BridgeSceneSuggestion {
  title: string;
  description: string;
  emotional_purpose: string;
  suggested_word_count: number;
}

export interface BridgeScenesResult {
  scenes: BridgeSceneSuggestion[];
  bridging_analysis: string;
  from_beat_id: string;
  to_beat_id: string;
}

export interface Outline {
  id: string;
  manuscript_id: string | null;
  series_id: string | null;
  world_id: string | null;
  scope: OutlineScope;
  structure_type: string;
  genre: string | null;
  arc_type: ArcType | null;
  book_count: number | null;
  target_word_count: number;
  premise: string;
  logline: string;
  synopsis: string;
  notes: string;
  is_active: boolean;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  plot_beats: PlotBeat[];
}

export interface OutlineProgress {
  outline_id: string;
  total_beats: number;
  completed_beats: number;
  completion_percentage: number;
  target_word_count: number;
  actual_word_count: number;
}

export interface PlotBeatUpdate {
  beat_label?: string;
  beat_description?: string;
  user_notes?: string;
  content_summary?: string;
  chapter_id?: string | null;
  is_completed?: boolean;
}

export interface OutlineUpdate {
  structure_type?: string;
  genre?: string;
  target_word_count?: number;
  premise?: string;
  logline?: string;
  synopsis?: string;
  notes?: string;
  is_active?: boolean;
}

// === AI Analysis Types ===

export interface PlotHoleFix {
  title: string;
  description: string;
  implementation: string;
  impact: string;
}

export interface PlotHoleDismissal {
  id: string;
  outline_id: string;
  plot_hole_hash: string;
  severity: 'high' | 'medium' | 'low';
  location: string;
  issue: string;
  suggestion: string | null;
  status: 'dismissed' | 'accepted';
  user_explanation: string | null;
  ai_fix_suggestions: PlotHoleFix[] | null;
  created_at: string;
  updated_at: string;
}

export interface PlotHole {
  severity: 'high' | 'medium' | 'low';
  location: string;
  issue: string;
  suggestion: string;
  resolved?: boolean;  // Frontend-only flag (legacy)
  dismissal?: PlotHoleDismissal;  // Linked dismissal if one exists
}

export interface PacingAnalysis {
  overall_score: number;
  act_balance: {
    act1_percent: number;
    act2_percent: number;
    act3_percent: number;
  };
  issues: string[];
  recommendations: string[];
  strengths?: string[];
}

export interface BeatSuggestion {
  type: 'scene' | 'character' | 'dialogue' | 'subplot';
  title: string;
  description: string;
  used?: boolean;  // Frontend-only flag
}

export interface AIAnalysisResult {
  beat_descriptions?: { [beatName: string]: string };
  plot_holes?: PlotHole[];
  pacing_analysis?: PacingAnalysis;
  overall_assessment?: string;
  cost?: {
    total_usd: number;
    formatted: string;
  };
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface BeatSuggestionsResult {
  beat_id: string;
  suggestions: BeatSuggestion[];
  cost?: {
    total_usd: number;
    formatted: string;
  };
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface AIAnalysisRequest {
  api_key: string;
  analysis_types?: ('beat_descriptions' | 'plot_holes' | 'pacing')[];
}

// Feedback for AI suggestion refinement
export interface BeatFeedback {
  liked: string[];  // Descriptions of liked aspects
  disliked: string[];  // Descriptions of disliked aspects
  notes: string;  // Free-form refinement notes
}

export interface AIAnalysisWithFeedbackRequest {
  api_key: string;
  analysis_types?: ('beat_descriptions' | 'plot_holes' | 'pacing')[];
  feedback?: { [beatName: string]: BeatFeedback };
}

// === Series/World Outline Types ===

export interface SeriesStructureBeat {
  beat_name: string;
  beat_label: string;
  beat_description: string;
  target_position_percent: number;
  order_index: number;
  target_book_index: number;
  tips?: string;
}

export interface SeriesStructure {
  name: string;
  description: string;
  book_count: number | null;
  arc_type: ArcType;
  beats: SeriesStructureBeat[];
}

export interface SeriesStructureSummary {
  type: string;
  name: string;
  description: string;
  book_count: number | null;
  arc_type: ArcType;
  beat_count: number;
}

export interface SeriesOutlineCreate {
  series_id: string;
  structure_type: string;
  genre?: string;
  target_word_count?: number;
  premise?: string;
  logline?: string;
  synopsis?: string;
}

export interface WorldOutlineCreate {
  world_id: string;
  structure_type: string;
  genre?: string;
  target_word_count?: number;
  premise?: string;
  logline?: string;
  synopsis?: string;
}

export interface LinkBeatToManuscriptRequest {
  beat_id: string;
  manuscript_outline_id: string;
}

export interface SeriesStructureWithManuscripts {
  series: {
    id: string;
    name: string;
    description: string;
  };
  series_outline: Outline | null;
  manuscripts: Array<{
    id: string;
    title: string;
    order_index: number;
    outline: Outline | null;
  }>;
}
