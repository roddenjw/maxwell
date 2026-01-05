/**
 * Outline and Plot Beat Type Definitions
 * Matches backend API response structure from app/models/outline.py
 */

export interface PlotBeat {
  id: string;
  outline_id: string;
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
