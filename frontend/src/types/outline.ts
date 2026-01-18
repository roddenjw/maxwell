/**
 * Outline and Plot Beat Type Definitions
 * Matches backend API response structure from app/models/outline.py
 */

// Item type constants
export type ItemType = 'BEAT' | 'SCENE';

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

export interface Outline {
  id: string;
  manuscript_id: string;
  structure_type: string;
  genre: string | null;
  target_word_count: number;
  premise: string;
  logline: string;
  synopsis: string;
  notes: string;
  is_active: boolean;
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

export interface PlotHole {
  severity: 'high' | 'medium' | 'low';
  location: string;
  issue: string;
  suggestion: string;
  resolved?: boolean;  // Frontend-only flag
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
