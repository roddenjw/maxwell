/**
 * Brainstorming & Ideation Tool Types
 * Matches backend models from app/models/brainstorm.py
 */

export type BrainstormSessionType = 'CHARACTER' | 'PLOT_BEAT' | 'WORLD' | 'CONFLICT';
export type BrainstormSessionStatus = 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';

export interface BrainstormSession {
  id: string;
  manuscript_id: string;
  outline_id?: string;
  session_type: BrainstormSessionType;
  context_data: Record<string, any>;
  status: BrainstormSessionStatus;
  created_at: string;
  updated_at: string;
}

export interface BrainstormIdea {
  id: string;
  session_id: string;
  idea_type: string;
  title: string;
  description: string;
  idea_metadata: Record<string, any>;
  is_selected: boolean;
  user_notes: string;
  edited_content?: string;
  integrated_to_outline: boolean;
  integrated_to_codex: boolean;
  plot_beat_id?: string;
  entity_id?: string;
  ai_cost: number;
  ai_tokens: number;
  ai_model: string;
  created_at: string;
  updated_at: string;
}

// Character-specific metadata (Brandon Sanderson methodology)
export interface CharacterMetadata {
  name: string;
  role: string;
  want: string;
  need: string;
  flaw: string;
  strength: string;
  arc: string;
  hook: string;
  relationships: string;
  story_potential: string;
}

// Session statistics
export interface BrainstormSessionStats {
  session_id: string;
  session_type: BrainstormSessionType;
  status: BrainstormSessionStatus;
  total_ideas: number;
  selected_ideas: number;
  integrated_ideas: number;
  total_cost: number;
  total_tokens: number;
  created_at: string;
}

// API request/response types
export interface CreateSessionRequest {
  manuscript_id: string;
  outline_id?: string;
  session_type: BrainstormSessionType;
  context_data: Record<string, any>;
}

export interface CharacterGenerationRequest {
  api_key: string;
  genre: string;
  story_premise: string;
  num_ideas?: number;
}

export interface UpdateIdeaRequest {
  is_selected?: boolean;
  user_notes?: string;
  edited_content?: string;
}

export interface IntegrateCodexRequest {
  entity_type?: string;
}

// UI-specific types
export type BrainstormTechnique = 'character' | 'plot' | 'world' | 'conflict';

export interface BrainstormModalState {
  isOpen: boolean;
  technique?: BrainstormTechnique;
  manuscriptId?: string;
  outlineId?: string;
  plotBeatId?: string;
}
