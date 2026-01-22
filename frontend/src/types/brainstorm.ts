/**
 * Brainstorming & Ideation Tool Types
 * Matches backend models from app/models/brainstorm.py
 */

export type BrainstormSessionType = 'CHARACTER' | 'PLOT_BEAT' | 'WORLD' | 'CONFLICT' | 'SCENE';
export type BrainstormSessionStatus = 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';
export type BrainstormIdeaType = 'CHARACTER' | 'PLOT_BEAT' | 'WORLD' | 'CONFLICT' | 'SCENE' | 'CHARACTER_WORKSHEET';

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
  character_ideas?: string;
  num_ideas?: number;
}

export interface PlotGenerationRequest {
  api_key: string;
  genre: string;
  premise: string;
  num_ideas?: number;
}

export interface LocationGenerationRequest {
  api_key: string;
  genre: string;
  premise: string;
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

// New Phase 5 request types
export interface RefineIdeaRequest {
  api_key: string;
  feedback: string;
  direction: 'refine' | 'expand' | 'contrast' | 'combine';
  combine_with_idea_id?: string;
}

export interface ConflictGenerationRequest {
  api_key: string;
  genre: string;
  premise: string;
  character_ids?: string[];
  conflict_type: 'internal' | 'interpersonal' | 'external' | 'societal' | 'any';
  num_ideas?: number;
}

export interface SceneGenerationRequest {
  api_key: string;
  genre: string;
  premise: string;
  beat_id?: string;
  character_ids?: string[];
  location_id?: string;
  scene_purpose: 'introduction' | 'conflict' | 'revelation' | 'climax' | 'resolution' | 'any';
  num_ideas?: number;
}

export interface CharacterWorksheetRequest {
  api_key: string;
  character_id?: string;
  character_name?: string;
  worksheet_type: 'full' | 'backstory' | 'psychology' | 'voice' | 'relationships';
}

export interface ExpandEntityRequest {
  api_key: string;
  expansion_type: 'deepen' | 'relationships' | 'history' | 'secrets' | 'conflicts';
}

// Conflict metadata
export interface ConflictMetadata {
  title: string;
  type: 'internal' | 'interpersonal' | 'external' | 'societal';
  participants: string[];
  core_tension: string;
  stakes: string;
  trigger: string;
  escalation_points: string[];
  possible_resolutions: string[];
  emotional_core: string;
  scene_opportunities: string[];
  thematic_connection: string;
}

// Scene metadata
export interface SceneMetadata {
  title: string;
  purpose: 'introduction' | 'conflict' | 'revelation' | 'climax' | 'resolution';
  pov_character: string;
  characters_present: string[];
  location: string;
  opening_hook: string;
  scene_goal: string;
  obstacle: string;
  outcome: 'disaster' | 'partial_success' | 'success' | 'twist';
  emotional_arc: {
    start: string;
    shift: string;
    end: string;
  };
  scene_beats: string[];
  sensory_details: string[];
  dialogue_moments: string[];
  subtext: string;
}

// Character worksheet response
export interface CharacterWorksheet {
  character_name: string;
  worksheet_type: string;
  sections: Record<string, any>;
  _metadata: {
    character_id?: string;
    idea_id?: string;
    ai_cost: number;
    ai_tokens: number;
  };
}

// Entity expansion response
export interface EntityExpansion {
  expanded_attributes: Record<string, any>;
  suggestions: string[];
  story_hooks: string[];
  _expansion_metadata: {
    type: string;
    ai_cost: number;
    ai_tokens: number;
  };
}

// Related entity response
export interface RelatedEntity {
  type: string;
  name: string;
  relationship_to_source: string;
  hook: string;
  [key: string]: any;
  _metadata: {
    source_entity_id: string;
    relationship_type: string;
    ai_cost: number;
  };
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

// Manuscript context for auto-loading
export interface BrainstormContext {
  outline: {
    genre: string | null;
    premise: string | null;
    logline: string | null;
  };
  existing_entities: {
    characters: { id: string; name: string }[];
    locations: { id: string; name: string }[];
  };
}

// Session with preview and stats
export interface SessionWithPreview {
  session: BrainstormSession;
  preview_ideas: {
    id: string;
    title: string;
    description: string;
  }[];
  stats: {
    total_ideas: number;
    integrated_count: number;
    pending_count: number;
  };
}
