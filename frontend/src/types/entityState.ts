/**
 * Entity Timeline State Type Definitions
 * Tracks entity states at different narrative points across manuscripts
 */

// Entity state data structure (flexible JSON)
export interface EntityStateData {
  // Common fields for characters
  age?: number | string;
  status?: 'alive' | 'dead' | 'missing' | 'transformed' | string;
  location_id?: string;
  allegiances?: string[];
  power_level?: string;
  relationships?: Record<string, {
    type: string;
    strength: number;
    notes?: string;
  }>;
  notes?: string;

  // Location-specific fields
  condition?: string;
  population?: string;
  ruler?: string;

  // Item-specific fields
  owner_id?: string;
  item_location?: string;
  item_condition?: string;

  // Custom fields
  custom_fields?: Record<string, unknown>;
}

// Entity Timeline State
export interface EntityTimelineState {
  id: string;
  entity_id: string;
  manuscript_id: string | null;
  chapter_id: string | null;
  timeline_event_id: string | null;
  order_index: number;
  narrative_timestamp: string | null;
  state_data: EntityStateData;
  label: string | null;
  is_canonical: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// Create state request
export interface CreateStateRequest {
  state_data: EntityStateData;
  manuscript_id?: string;
  chapter_id?: string;
  timeline_event_id?: string;
  order_index?: number;
  narrative_timestamp?: string;
  label?: string;
  is_canonical?: boolean;
}

// Update state request
export interface UpdateStateRequest {
  state_data?: EntityStateData;
  narrative_timestamp?: string;
  label?: string;
  is_canonical?: boolean;
  order_index?: number;
}

// State diff result
export interface StateDiffResult {
  from_state: {
    id: string;
    label: string | null;
    narrative_timestamp: string | null;
  };
  to_state: {
    id: string;
    label: string | null;
    narrative_timestamp: string | null;
  };
  added: Record<string, unknown>;
  removed: Record<string, unknown>;
  changed: Record<string, { from: unknown; to: unknown }>;
}

// State change for journey
export interface StateChange {
  type: 'added' | 'changed' | 'removed';
  value?: unknown;
  from?: unknown;
  to?: unknown;
}

// Journey point
export interface JourneyPoint {
  state_id: string;
  manuscript_id: string | null;
  chapter_id: string | null;
  timeline_event_id: string | null;
  order_index: number;
  narrative_timestamp: string | null;
  label: string | null;
  state_data: EntityStateData;
  changes: Record<string, StateChange> | null;
}

// API Response wrappers
export interface EntityStateResponse {
  success: boolean;
  data: EntityTimelineState;
}

export interface EntityStatesListResponse {
  success: boolean;
  data: EntityTimelineState[];
}

export interface StateDiffResponse {
  success: boolean;
  data: StateDiffResult;
}

export interface JourneyResponse {
  success: boolean;
  data: JourneyPoint[];
}
