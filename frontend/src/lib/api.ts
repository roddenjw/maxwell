/**
 * API Service for Maxwell Backend
 * Handles all HTTP requests to the FastAPI backend
 */

import type {
  Entity,
  Relationship,
  EntitySuggestion,
  CreateEntityRequest,
  UpdateEntityRequest,
  CreateRelationshipRequest,
  ApproveSuggestionRequest,
  AnalyzeTextRequest,
} from '@/types/codex';

import type {
  TimelineEvent,
  TimelineInconsistency,
  CharacterLocation,
  TimelineStats,
  CreateEventRequest,
  UpdateEventRequest,
  AnalyzeTimelineRequest,
} from '@/types/timeline';

import type {
  Outline,
  PlotBeat,
  OutlineProgress,
  PlotBeatUpdate,
  OutlineUpdate,
  AIAnalysisResult,
  BeatSuggestionsResult,
  SceneCreate,
  BridgeScenesResult,
  SeriesStructure,
  SeriesStructureSummary,
  SeriesOutlineCreate,
  WorldOutlineCreate,
  LinkBeatToManuscriptRequest,
  SeriesStructureWithManuscripts,
  BeatFeedback,
} from '@/types/outline';

import type {
  EntityTimelineState,
  CreateStateRequest,
  UpdateStateRequest,
  StateDiffResult,
  JourneyPoint,
} from '@/types/entityState';

import type {
  BrainstormSession,
  BrainstormIdea,
  BrainstormSessionStats,
  BrainstormContext,
  CreateSessionRequest,
  CharacterGenerationRequest,
  PlotGenerationRequest,
  LocationGenerationRequest,
  UpdateIdeaRequest,
  IntegrateCodexRequest,
  RefineIdeaRequest,
  ConflictGenerationRequest,
  SceneGenerationRequest,
  CharacterWorksheetRequest,
  ExpandEntityRequest,
  CharacterWorksheet,
  EntityExpansion,
  RelatedEntity,
} from '@/types/brainstorm';

import type {
  World,
  Series,
  ManuscriptBrief,
  CreateWorldRequest,
  UpdateWorldRequest,
  CreateSeriesRequest,
  UpdateSeriesRequest,
  AssignManuscriptRequest,
  CreateWorldEntityRequest,
  ChangeScopeRequest,
  CopyEntityRequest,
  WorldEntityResponse,
  DeleteResponse,
} from '@/types/world';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Standard API response format
 */
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp: string;
    version: string;
  };
}

/**
 * Manuscript types
 */
export interface Manuscript {
  id: string;
  title: string;
  author?: string;
  description?: string;
  lexical_state: string;
  word_count: number;
  // Story metadata for AI context
  premise?: string;          // Story premise/logline
  premise_source?: string;   // 'ai_generated' or 'user_written'
  genre?: string;            // e.g., 'Fantasy', 'Mystery', 'Romance'
  created_at: string;
  updated_at: string;
  settings?: any;
}

/**
 * Snapshot types
 */
export interface Snapshot {
  id: string;
  manuscript_id: string;
  commit_hash: string;
  label: string;
  description: string;
  auto_summary: string;  // Auto-generated changeset summary (like commit messages)
  trigger_type: 'MANUAL' | 'AUTO' | 'CHAPTER_COMPLETE' | 'PRE_GENERATION' | 'SESSION_END';
  word_count: number;
  created_at: string;
}

/**
 * Scene Variant types
 */
export interface SceneVariant {
  id: string;
  scene_id: string;
  label: string;
  content: string;
  is_main: boolean;
  created_at: string;
}

/**
 * Chapter types
 */
export type DocumentType = 'CHAPTER' | 'FOLDER' | 'CHARACTER_SHEET' | 'NOTES' | 'TITLE_PAGE';

export interface Chapter {
  id: string;
  manuscript_id: string;
  parent_id: string | null;
  title: string;
  is_folder: boolean;
  order_index: number;
  lexical_state: string;
  content: string;
  word_count: number;
  document_type: DocumentType;
  linked_entity_id?: string | null;
  document_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  children?: Chapter[];
}

export interface ChapterTree {
  id: string;
  title: string;
  is_folder: boolean;
  order_index: number;
  word_count: number;
  document_type: DocumentType;
  linked_entity_id?: string | null;
  children: ChapterTree[];
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data: ApiResponse<T> = await response.json();

  if (!response.ok || !data.success) {
    throw new Error(data.error?.message || 'API request failed');
  }

  return data.data as T;
}

/**
 * Manuscript API
 */
export const manuscriptApi = {
  /**
   * Get all manuscripts
   */
  async list(): Promise<Manuscript[]> {
    const url = `${API_BASE_URL}/manuscripts`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error('Failed to fetch manuscripts');
    }

    return response.json();
  },

  /**
   * Get a single manuscript by ID
   */
  async get(id: string): Promise<Manuscript> {
    return apiFetch<Manuscript>(`/manuscripts/${id}`);
  },

  /**
   * Create a new manuscript
   */
  async create(data: {
    title: string;
    author?: string;
    description?: string;
  }): Promise<Manuscript> {
    return apiFetch<Manuscript>('/manuscripts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a manuscript
   */
  async update(id: string, data: Partial<Manuscript>): Promise<Manuscript> {
    return apiFetch<Manuscript>(`/manuscripts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a manuscript
   */
  async delete(id: string): Promise<void> {
    return apiFetch<void>(`/manuscripts/${id}`, {
      method: 'DELETE',
    });
  },
};

/**
 * Versioning API
 */
export const versioningApi = {
  /**
   * Create a snapshot (save version of ALL chapters)
   */
  async createSnapshot(data: {
    manuscript_id: string;
    trigger_type: Snapshot['trigger_type'];
    label?: string;
    description?: string;
    word_count?: number;
  }): Promise<Snapshot> {
    return apiFetch<Snapshot>('/versioning/snapshots', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all snapshots for a manuscript
   */
  async listSnapshots(manuscriptId: string): Promise<Snapshot[]> {
    return apiFetch<Snapshot[]>(`/versioning/snapshots/${manuscriptId}`);
  },

  /**
   * Get a specific snapshot
   */
  async getSnapshot(snapshotId: string): Promise<Snapshot> {
    return apiFetch<Snapshot>(`/versioning/snapshots/${snapshotId}`);
  },

  /**
   * Restore ALL chapters to a snapshot state
   */
  async restoreSnapshot(data: {
    manuscript_id: string;
    snapshot_id: string;
    create_backup?: boolean;
  }): Promise<{
    chapters_restored: number;
    chapters_deleted: number;
    snapshot_label: string;
    legacy_format: boolean;
  }> {
    return apiFetch('/versioning/restore', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get diff between two snapshots
   */
  async getDiff(data: {
    manuscript_id: string;
    snapshot_id_old: string;
    snapshot_id_new: string;
  }): Promise<{
    diff_html: string;
    additions: number;
    deletions: number;
  }> {
    return apiFetch('/versioning/diff', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Create a variant (branch)
   */
  async createVariant(data: {
    manuscript_id: string;
    scene_id: string;
    variant_label: string;
    base_snapshot_id?: string;
  }): Promise<{ variant_id: string; branch_name: string }> {
    return apiFetch('/versioning/variants', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List variants for a scene
   */
  async listVariants(sceneId: string): Promise<SceneVariant[]> {
    return apiFetch<SceneVariant[]>(`/versioning/variants?scene_id=${sceneId}`);
  },

  /**
   * Merge a variant back to main
   */
  async mergeVariant(data: {
    manuscript_id: string;
    variant_branch: string;
  }): Promise<{ commit_hash: string }> {
    return apiFetch('/versioning/merge', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

/**
 * Codex API (Entity and Relationship Management)
 */
export const codexApi = {
  // Entity Endpoints

  /**
   * Create a new entity
   */
  async createEntity(data: CreateEntityRequest): Promise<Entity> {
    return apiFetch<Entity>('/codex/entities', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List entities for a manuscript
   */
  async listEntities(manuscriptId: string, type?: string): Promise<Entity[]> {
    const params = type ? `?type=${type}` : '';
    return apiFetch<Entity[]>(`/codex/entities/${manuscriptId}${params}`);
  },

  /**
   * Get a single entity by ID
   */
  async getEntity(entityId: string): Promise<Entity> {
    return apiFetch<Entity>(`/codex/entities/single/${entityId}`);
  },

  /**
   * Update an entity
   */
  async updateEntity(entityId: string, data: UpdateEntityRequest): Promise<Entity> {
    return apiFetch<Entity>(`/codex/entities/${entityId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an entity
   */
  async deleteEntity(entityId: string): Promise<void> {
    return apiFetch<void>(`/codex/entities/${entityId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Merge multiple entities into a primary entity
   */
  async mergeEntities(data: {
    primary_entity_id: string;
    secondary_entity_ids: string[];
    merge_strategy?: { aliases?: string; attributes?: string };
  }): Promise<Entity> {
    return apiFetch<Entity>('/codex/entities/merge', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Add appearance record to entity
   */
  async addAppearance(data: {
    entity_id: string;
    scene_id?: string;
    description: string;
  }): Promise<Entity> {
    return apiFetch<Entity>('/codex/entities/appearance', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Generate AI suggestion for entity template field
   */
  async generateFieldSuggestion(data: {
    api_key: string;
    entity_name: string;
    entity_type: string;
    template_type: string;
    field_path: string;
    existing_data?: Record<string, any>;
    manuscript_context?: string;
  }): Promise<{ suggestion: string | string[]; usage: any; cost: { total: number; formatted: string } }> {
    const url = `${API_BASE_URL}/codex/entities/ai-field-suggestion`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error?.message || result.detail || 'AI generation failed');
    }

    return {
      suggestion: result.data.suggestion,
      usage: result.data.usage,
      cost: result.cost,
    };
  },

  /**
   * Extract entity information from selected text and surrounding context using AI
   */
  async extractEntityFromSelection(data: {
    api_key: string;
    selected_text: string;
    surrounding_context: string;
    manuscript_genre?: string;
  }): Promise<{
    type: 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';
    name: string;
    description: string | null;
    suggested_aliases: string[];
    attributes: Record<string, any>;
    confidence: 'high' | 'medium' | 'low';
  }> {
    const url = `${API_BASE_URL}/codex/entities/ai-extract`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error?.message || result.detail || 'AI extraction failed');
    }

    return result.data;
  },

  /**
   * Get first/last appearance summary for an entity
   */
  async getEntityAppearanceSummary(entityId: string): Promise<{
    first_appearance: {
      chapter_id: string;
      chapter_title: string;
      chapter_order: number;
      summary: string;
      created_at: string | null;
    } | null;
    last_appearance: {
      chapter_id: string;
      chapter_title: string;
      chapter_order: number;
      summary: string;
      created_at: string | null;
    } | null;
    total_appearances: number;
  }> {
    return apiFetch(`/codex/entities/${entityId}/appearances/summary`);
  },

  /**
   * Get all appearance contexts for an entity (for AI analysis)
   */
  async getEntityAppearanceContexts(entityId: string): Promise<Array<{
    chapter_title: string;
    summary: string;
    context_text: string | null;
  }>> {
    return apiFetch(`/codex/entities/${entityId}/appearances/contexts`);
  },

  /**
   * Generate comprehensive entity content from all appearances using AI
   */
  async aiEntityFill(data: {
    api_key: string;
    entity_id: string;
  }): Promise<{
    description: string;
    attributes: Record<string, any>;
    suggested_aliases: string[];
  }> {
    const url = `${API_BASE_URL}/codex/entities/ai-fill`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error?.message || result.detail || 'AI fill failed');
    }

    return result.data;
  },

  // Relationship Endpoints

  /**
   * Create a relationship between entities
   */
  async createRelationship(data: CreateRelationshipRequest): Promise<Relationship> {
    return apiFetch<Relationship>('/codex/relationships', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List relationships for a manuscript
   */
  async listRelationships(manuscriptId: string, entityId?: string): Promise<Relationship[]> {
    const params = entityId ? `?entity_id=${entityId}` : '';
    return apiFetch<Relationship[]>(`/codex/relationships/${manuscriptId}${params}`);
  },

  /**
   * Delete a relationship
   */
  async deleteRelationship(relationshipId: string): Promise<void> {
    return apiFetch<void>(`/codex/relationships/${relationshipId}`, {
      method: 'DELETE',
    });
  },

  // Suggestion Endpoints

  /**
   * List entity suggestions
   */
  async listSuggestions(manuscriptId: string, status?: string): Promise<EntitySuggestion[]> {
    const params = status ? `?status=${status}` : '';
    return apiFetch<EntitySuggestion[]>(`/codex/suggestions/${manuscriptId}${params}`);
  },

  /**
   * Approve a suggestion and create entity
   */
  async approveSuggestion(data: ApproveSuggestionRequest): Promise<Entity> {
    return apiFetch<Entity>('/codex/suggestions/approve', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Reject a suggestion
   */
  async rejectSuggestion(suggestionId: string): Promise<void> {
    return apiFetch<void>('/codex/suggestions/reject', {
      method: 'POST',
      body: JSON.stringify({ suggestion_id: suggestionId }),
    });
  },

  // Analysis Endpoints

  /**
   * Analyze text for entities and relationships
   */
  async analyzeText(data: AnalyzeTextRequest): Promise<{ message: string; manuscript_id: string }> {
    return apiFetch('/codex/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Check NLP service status
   */
  async nlpStatus(): Promise<{ available: boolean; model: string | null }> {
    return apiFetch('/codex/nlp/status');
  },
};

/**
 * Timeline API
 */
export const timelineApi = {
  /**
   * List timeline events for a manuscript
   */
  async listEvents(manuscriptId: string, filters?: {
    event_type?: string;
    character_id?: string;
    location_id?: string;
  }): Promise<TimelineEvent[]> {
    const params = new URLSearchParams();
    if (filters?.event_type) params.append('event_type', filters.event_type);
    if (filters?.character_id) params.append('character_id', filters.character_id);
    if (filters?.location_id) params.append('location_id', filters.location_id);

    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch(`/timeline/events/${manuscriptId}${query}`);
  },

  /**
   * Get a single event
   */
  async getEvent(eventId: string): Promise<TimelineEvent> {
    return apiFetch(`/timeline/events/single/${eventId}`);
  },

  /**
   * Create a new event
   */
  async createEvent(data: CreateEventRequest): Promise<TimelineEvent> {
    return apiFetch('/timeline/events', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update an event
   */
  async updateEvent(eventId: string, data: UpdateEventRequest): Promise<TimelineEvent> {
    return apiFetch(`/timeline/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an event
   */
  async deleteEvent(eventId: string): Promise<{ success: boolean; message: string }> {
    return apiFetch(`/timeline/events/${eventId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Delete all auto-generated events for a manuscript
   */
  async deleteAutoGeneratedEvents(manuscriptId: string): Promise<{ success: boolean; message: string; deleted_count: number }> {
    return apiFetch(`/timeline/events/auto-generated/${manuscriptId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Mark all existing events as auto-generated (migration helper)
   */
  async markEventsAsAutoGenerated(manuscriptId: string): Promise<{ success: boolean; message: string; marked_count: number }> {
    return apiFetch(`/timeline/events/mark-auto-generated/${manuscriptId}`, {
      method: 'POST',
    });
  },

  /**
   * Delete ALL events for a manuscript
   */
  async deleteAllEvents(manuscriptId: string): Promise<{ success: boolean; message: string; deleted_count: number }> {
    return apiFetch(`/timeline/events/all/${manuscriptId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Reorder events
   */
  async reorderEvents(eventIds: string[]): Promise<{ success: boolean; message: string }> {
    return apiFetch('/timeline/events/reorder', {
      method: 'POST',
      body: JSON.stringify({ event_ids: eventIds }),
    });
  },

  /**
   * Analyze text for timeline events
   */
  async analyzeTimeline(data: AnalyzeTimelineRequest): Promise<{ success: boolean; message: string; manuscript_id: string }> {
    return apiFetch('/timeline/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Track character location at event
   */
  async trackCharacterLocation(data: {
    character_id: string;
    event_id: string;
    location_id: string;
    manuscript_id: string;
  }): Promise<{ success: boolean; data: CharacterLocation }> {
    return apiFetch('/timeline/character-locations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get character locations
   */
  async getCharacterLocations(characterId: string, manuscriptId: string): Promise<{ success: boolean; data: CharacterLocation[] }> {
    return apiFetch(`/timeline/character-locations/${characterId}?manuscript_id=${manuscriptId}`);
  },

  /**
   * Detect timeline inconsistencies
   */
  async detectInconsistencies(manuscriptId: string): Promise<TimelineInconsistency[]> {
    return apiFetch(`/timeline/inconsistencies/detect/${manuscriptId}`, {
      method: 'POST',
    });
  },

  /**
   * List timeline inconsistencies
   */
  async listInconsistencies(manuscriptId: string, severity?: string): Promise<TimelineInconsistency[]> {
    const query = severity ? `?severity=${severity}` : '';
    return apiFetch(`/timeline/inconsistencies/${manuscriptId}${query}`);
  },

  /**
   * Resolve an inconsistency with optional resolution notes
   */
  async resolveInconsistency(inconsistencyId: string, resolutionNote?: string): Promise<{ success: boolean; message: string }> {
    const url = resolutionNote
      ? `/timeline/inconsistencies/${inconsistencyId}?resolution_note=${encodeURIComponent(resolutionNote)}`
      : `/timeline/inconsistencies/${inconsistencyId}`;
    return apiFetch(url, {
      method: 'DELETE',
    });
  },

  /**
   * Get timeline statistics
   */
  async getStats(manuscriptId: string): Promise<{ success: boolean; data: TimelineStats }> {
    return apiFetch(`/timeline/stats/${manuscriptId}`);
  },

  /**
   * Get comprehensive journey summary for a character
   */
  async getCharacterJourneySummary(
    characterId: string,
    manuscriptId: string
  ): Promise<{
    character_id: string;
    manuscript_id: string;
    total_events: number;
    unique_locations: number;
    total_distance_km: number;
    key_events: Array<{
      event_id: string;
      description: string;
      order_index: number;
      narrative_importance: number;
      timestamp: string | null;
    }>;
    location_timeline: Array<{
      event_id: string;
      event_description: string;
      location_id: string | null;
      location_name: string;
      order_index: number;
      timestamp: string | null;
      is_location_change: boolean;
    }>;
    emotional_arc: Array<{
      order_index: number;
      emotional_tone: string;
      event_id: string;
    }>;
    first_appearance_index: number;
    last_appearance_index: number;
    location_changes: number;
  }> {
    return apiFetch(`/timeline/character-journey/${characterId}?manuscript_id=${manuscriptId}`);
  },
};

/**
 * Chapters API (Hierarchical document structure)
 */
export const chaptersApi = {
  /**
   * Create a new chapter or folder
   */
  async createChapter(data: {
    manuscript_id: string;
    title: string;
    is_folder?: boolean;
    parent_id?: string;
    order_index?: number;
    lexical_state?: string;
    content?: string;
    document_type?: DocumentType;
    linked_entity_id?: string;
    document_metadata?: Record<string, unknown>;
  }): Promise<Chapter> {
    return apiFetch<Chapter>('/chapters', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List chapters for a manuscript
   */
  async listChapters(manuscriptId: string, parentId?: string): Promise<Chapter[]> {
    const params = parentId ? `?parent_id=${parentId}` : '';
    return apiFetch<Chapter[]>(`/chapters/manuscript/${manuscriptId}${params}`);
  },

  /**
   * Get chapter tree structure
   */
  async getChapterTree(manuscriptId: string): Promise<ChapterTree[]> {
    return apiFetch<ChapterTree[]>(`/chapters/manuscript/${manuscriptId}/tree`);
  },

  /**
   * Get a single chapter
   */
  async getChapter(chapterId: string): Promise<Chapter> {
    return apiFetch<Chapter>(`/chapters/${chapterId}`);
  },

  /**
   * Update a chapter
   */
  async updateChapter(chapterId: string, data: Partial<Chapter>): Promise<Chapter> {
    return apiFetch<Chapter>(`/chapters/${chapterId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a chapter
   */
  async deleteChapter(chapterId: string): Promise<void> {
    return apiFetch<void>(`/chapters/${chapterId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Reorder chapters
   */
  async reorderChapters(chapterIds: string[]): Promise<void> {
    return apiFetch<void>('/chapters/reorder', {
      method: 'POST',
      body: JSON.stringify({ chapter_ids: chapterIds }),
    });
  },

  /**
   * Create a character sheet from an existing Codex entity
   */
  async createFromEntity(data: {
    manuscript_id: string;
    entity_id: string;
    parent_id?: string;
    order_index?: number;
  }): Promise<Chapter> {
    return apiFetch<Chapter>('/chapters/from-entity', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Sync a character sheet with its linked Codex entity
   * @param direction - "from_entity" pulls from entity, "to_entity" pushes to entity
   */
  async syncEntity(chapterId: string, direction: 'from_entity' | 'to_entity' = 'from_entity'): Promise<{
    chapter: Chapter;
    entity: { id: string; name: string; type: string };
  }> {
    // Backend returns { success, data (chapter), entity }
    // apiFetch unwraps to the data field, but we need both chapter and entity
    const url = `${API_BASE_URL}/chapters/${chapterId}/sync-entity?direction=${direction}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
    });
    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.error?.message || 'Failed to sync entity');
    }
    return { chapter: result.data, entity: result.entity };
  },
};

/**
 * Outline API (Story Structure & Plot Beats)
 */
export const outlineApi = {
  /**
   * Get the active outline for a manuscript
   */
  async getActiveOutline(manuscriptId: string): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/manuscript/${manuscriptId}/active`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No active outline found for manuscript');
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get outline by ID
   */
  async getOutline(outlineId: string): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get all outlines for a manuscript
   */
  async listOutlines(manuscriptId: string): Promise<Outline[]> {
    const response = await fetch(`${API_BASE_URL}/outlines/manuscript/${manuscriptId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list outlines');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Update an outline
   */
  async updateOutline(outlineId: string, data: OutlineUpdate): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Update a plot beat
   */
  async updateBeat(beatId: string, data: PlotBeatUpdate): Promise<PlotBeat> {
    const response = await fetch(`${API_BASE_URL}/outlines/beats/${beatId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update beat');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get outline progress/completion stats
   */
  async getProgress(outlineId: string): Promise<OutlineProgress> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/progress`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get progress');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Create a new plot beat
   */
  async createBeat(outlineId: string, data: {
    beat_name: string;
    beat_label: string;
    beat_description?: string;
    target_position_percent: number;
    order_index: number;
    user_notes?: string;
  }): Promise<PlotBeat> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/beats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create beat');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Delete a plot beat or scene
   */
  async deleteBeat(beatId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/outlines/beats/${beatId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete beat');
    }

    return response.json();
  },

  /**
   * Create a scene between beats
   * Scenes are user-added outline items that bridge major story beats.
   */
  async createScene(outlineId: string, data: SceneCreate): Promise<PlotBeat> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/scenes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create scene');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Generate premise and logline from brainstorm text using AI
   */
  async generatePremise(data: {
    brainstorm_text: string;
    api_key: string;
    genre?: string;
  }): Promise<{ success: boolean; premise: string; logline: string; usage: any }> {
    const response = await fetch(`${API_BASE_URL}/outlines/generate-premise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate premise');
    }

    return response.json();
  },

  /**
   * Generate AI-powered scene suggestions to bridge the gap between two beats
   */
  async generateBridgeScenes(
    outlineId: string,
    fromBeatId: string,
    toBeatId: string,
    apiKey: string
  ): Promise<{ data: BridgeScenesResult; usage: any; cost: { total_usd: number; formatted: string } }> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/ai-bridge-scenes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_beat_id: fromBeatId,
        to_beat_id: toBeatId,
        api_key: apiKey,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate bridge scenes');
    }

    return response.json();
  },

  /**
   * Switch to a different story structure (two-phase process)
   * Phase 1: Get suggested beat mappings (don't provide beat_mappings)
   * Phase 2: Apply mappings and create new outline (provide beat_mappings)
   */
  async switchStructure(data: {
    current_outline_id: string;
    new_structure_type: string;
    beat_mappings?: Record<string, string>;
  }): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/outlines/switch-structure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to switch structure');
    }

    return response.json();
  },
};

/**
 * Recap types
 */
export interface ChapterRecap {
  recap_id: string;
  recap_type: 'chapter' | 'arc';
  word_count?: number;
  content: {
    summary: string;
    key_events: string[];
    character_developments: Array<{ character: string; development: string }>;
    themes: string[];
    emotional_tone: string;
    narrative_arc: string;
    memorable_moments: string[];
    // Arc-specific fields
    major_plot_points?: string[];
    character_arcs?: Array<{ character: string; arc: string }>;
    central_themes?: string[];
    emotional_journey?: string;
    arc_structure?: string;
    climactic_moment?: string;
    unresolved_threads?: string[];
    chapter_ids?: string[];
  };
  created_at: string;
  is_cached?: boolean;
}

/**
 * Recap API
 */
export const recapApi = {
  /**
   * Generate or retrieve a chapter recap
   */
  async generateChapterRecap(chapterId: string, forceRegenerate = false): Promise<ChapterRecap> {
    const response = await fetch(`${API_BASE_URL}/recap/chapter/${chapterId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ force_regenerate: forceRegenerate }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate recap');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get a cached chapter recap
   */
  async getChapterRecap(chapterId: string): Promise<ChapterRecap> {
    const response = await fetch(`${API_BASE_URL}/recap/chapter/${chapterId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No recap found for this chapter');
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get recap');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Generate an arc recap for multiple chapters
   */
  async generateArcRecap(data: {
    arc_title: string;
    chapter_ids: string[];
  }): Promise<ChapterRecap> {
    const response = await fetch(`${API_BASE_URL}/recap/arc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate arc recap');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Delete a chapter recap
   */
  async deleteChapterRecap(chapterId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/recap/chapter/${chapterId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete recap');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get all recaps for a manuscript
   */
  async getManuscriptRecaps(manuscriptId: string): Promise<{ recaps: ChapterRecap[] }> {
    const response = await fetch(`${API_BASE_URL}/recap/manuscript/${manuscriptId}/recaps`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get recaps');
    }

    const result = await response.json();
    return result.data;
  },
};

/**
 * Analytics types
 */
export interface WritingAnalytics {
  overview: {
    total_words: number;
    total_chapters: number;
    words_this_period: number;
    current_streak: number;
    longest_streak: number;
    days_active: number;
    total_sessions: number;
  };
  daily_stats: Array<{
    date: string;
    word_count: number;
    sessions: number;
    snapshots: Array<{
      id: string;
      created_at: string;
      word_count: number;
      label: string;
    }>;
  }>;
  recent_sessions: Array<{
    id: string;
    date: string;
    word_count: number;
    label: string;
    trigger_type: string;
  }>;
  timeframe: {
    start: string;
    end: string;
    days: number;
  };
}

/**
 * Analytics API
 */
export const analyticsApi = {
  /**
   * Get comprehensive analytics for a manuscript
   */
  async getAnalytics(manuscriptId: string, days = 30): Promise<WritingAnalytics> {
    const response = await fetch(`${API_BASE_URL}/stats/analytics/${manuscriptId}?days=${days}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get analytics');
    }

    const data = await response.json();
    return data.data;
  },
};

/**
 * Brainstorming API
 */
export const brainstormingApi = {
  /**
   * Create a new brainstorming session
   */
  async createSession(request: CreateSessionRequest): Promise<BrainstormSession> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create brainstorming session');
    }

    return response.json();
  },

  /**
   * Get session details
   */
  async getSession(sessionId: string): Promise<BrainstormSession> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/sessions/${sessionId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get session');
    }

    return response.json();
  },

  /**
   * List all sessions for a manuscript
   */
  async listManuscriptSessions(manuscriptId: string): Promise<BrainstormSession[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/manuscripts/${manuscriptId}/sessions`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list sessions');
    }

    return response.json();
  },

  /**
   * Get manuscript context for brainstorming (outline + existing entities)
   */
  async getBrainstormContext(manuscriptId: string): Promise<BrainstormContext> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/manuscripts/${manuscriptId}/context`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get brainstorm context');
    }

    return response.json();
  },

  /**
   * Update session status
   */
  async updateSessionStatus(sessionId: string, status: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/status?status=${status}`,
      {
        method: 'PATCH',
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update session status');
    }
  },

  /**
   * Generate character ideas using AI
   */
  async generateCharacters(
    sessionId: string,
    request: CharacterGenerationRequest
  ): Promise<BrainstormIdea[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/characters`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate characters');
    }

    return response.json();
  },

  /**
   * Generate plot ideas using AI
   */
  async generatePlots(
    sessionId: string,
    request: PlotGenerationRequest
  ): Promise<BrainstormIdea[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/plots`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate plots');
    }

    return response.json();
  },

  /**
   * Generate location ideas using AI
   */
  async generateLocations(
    sessionId: string,
    request: LocationGenerationRequest
  ): Promise<BrainstormIdea[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/locations`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate locations');
    }

    return response.json();
  },

  /**
   * List all ideas for a session
   */
  async listSessionIdeas(sessionId: string): Promise<BrainstormIdea[]> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/sessions/${sessionId}/ideas`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list ideas');
    }

    return response.json();
  },

  /**
   * Update an idea
   */
  async updateIdea(ideaId: string, updates: UpdateIdeaRequest): Promise<BrainstormIdea> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/ideas/${ideaId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update idea');
    }

    return response.json();
  },

  /**
   * Delete an idea
   */
  async deleteIdea(ideaId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/ideas/${ideaId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete idea');
    }
  },

  /**
   * Integrate idea to Codex as entity
   */
  async integrateToCodex(
    ideaId: string,
    request?: IntegrateCodexRequest
  ): Promise<{ success: boolean; idea_id: string; entity: any }> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/ideas/${ideaId}/integrate/codex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request || {}),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to integrate to Codex');
    }

    return response.json();
  },

  /**
   * Get session statistics
   */
  async getSessionStats(sessionId: string): Promise<BrainstormSessionStats> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/sessions/${sessionId}/stats`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get session stats');
    }

    const data = await response.json();
    return data.data;
  },

  /**
   * Refine an existing idea based on user feedback
   */
  async refineIdea(ideaId: string, request: RefineIdeaRequest): Promise<BrainstormIdea> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/ideas/${ideaId}/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to refine idea');
    }

    return response.json();
  },

  /**
   * Generate conflict ideas using AI
   */
  async generateConflicts(
    sessionId: string,
    request: ConflictGenerationRequest
  ): Promise<BrainstormIdea[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/conflicts`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate conflicts');
    }

    return response.json();
  },

  /**
   * Generate scene ideas using AI
   */
  async generateScenes(
    sessionId: string,
    request: SceneGenerationRequest
  ): Promise<BrainstormIdea[]> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/scenes`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate scenes');
    }

    return response.json();
  },

  /**
   * Generate character development worksheet
   */
  async generateCharacterWorksheet(
    sessionId: string,
    request: CharacterWorksheetRequest
  ): Promise<{ success: boolean; worksheet: CharacterWorksheet }> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/sessions/${sessionId}/generate/character-worksheet`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate character worksheet');
    }

    return response.json();
  },

  /**
   * Expand an existing entity with AI-generated content
   */
  async expandEntity(
    entityId: string,
    request: ExpandEntityRequest
  ): Promise<{ success: boolean; entity_id: string; expansion: EntityExpansion }> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/entities/${entityId}/expand`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to expand entity');
    }

    return response.json();
  },

  /**
   * Generate new entities related to an existing one
   */
  async generateRelatedEntities(
    entityId: string,
    request: ExpandEntityRequest
  ): Promise<{ success: boolean; source_entity_id: string; related_entities: RelatedEntity[] }> {
    const response = await fetch(
      `${API_BASE_URL}/brainstorming/entities/${entityId}/generate-related`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate related entities');
    }

    return response.json();
  },

  /**
   * Generate outline from existing characters
   */
  async generateOutlineFromCharacters(data: {
    api_key: string;
    manuscript_id: string;
    genre: string;
    premise: string;
    target_word_count?: number;
  }): Promise<{
    beats: Array<{
      beat_name: string;
      beat_label: string;
      description: string;
      characters_involved: string[];
      character_growth: string;
      target_position_percent: number;
    }>;
    central_conflict: string;
    theme: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/outline-from-characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate outline from characters');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Generate a story premise from manuscript content
   * Uses AI to analyze the manuscript and derive a compelling premise/logline
   */
  async generatePremise(data: {
    api_key: string;
    manuscript_id: string;
  }): Promise<{
    success: boolean;
    premise: string;
    genre: string;
    themes: string[];
    tone: string;
    confidence: number;
    cost: { total: number; formatted: string };
  }> {
    const response = await fetch(`${API_BASE_URL}/brainstorming/generate-premise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate premise');
    }

    return response.json();
  },
};

/**
 * AI Analysis API
 * Endpoints for AI-powered outline analysis using Claude 3.5 Sonnet
 */
export const aiApi = {
  /**
   * Run AI analysis on entire outline
   * @param outlineId - Outline ID to analyze
   * @param apiKey - User's OpenRouter API key
   * @param analysisTypes - Optional array of analysis types to run
   * @returns Analysis results with cost information
   */
  async analyzeOutline(
    outlineId: string,
    apiKey: string,
    analysisTypes?: string[]
  ): Promise<{
    success: boolean;
    data: AIAnalysisResult;
    cost?: { total_usd: number; formatted: string };
    usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  }> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/ai-analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        analysis_types: analysisTypes,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'AI analysis failed');
    }

    return response.json();
  },

  /**
   * Get AI content suggestions for a specific beat
   * @param beatId - Beat ID to generate suggestions for
   * @param apiKey - User's OpenRouter API key
   * @returns Beat suggestions with cost information
   */
  async getBeatSuggestions(
    beatId: string,
    apiKey: string
  ): Promise<{
    success: boolean;
    data: BeatSuggestionsResult;
    cost?: { total_usd: number; formatted: string };
    usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  }> {
    const response = await fetch(`${API_BASE_URL}/outlines/beats/${beatId}/ai-suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get beat suggestions');
    }

    return response.json();
  },

  /**
   * Run AI analysis on outline with user feedback for refinement
   * @param outlineId - Outline ID to analyze
   * @param apiKey - User's OpenRouter API key
   * @param analysisTypes - Optional array of analysis types to run
   * @param feedback - User feedback on previous suggestions for refinement
   * @returns Analysis results with cost information
   */
  async analyzeOutlineWithFeedback(
    outlineId: string,
    apiKey: string,
    analysisTypes?: string[],
    feedback?: { [beatName: string]: BeatFeedback }
  ): Promise<{
    success: boolean;
    data: AIAnalysisResult;
    cost?: { total_usd: number; formatted: string };
    usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  }> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/ai-analyze-with-feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        analysis_types: analysisTypes,
        feedback: feedback,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'AI analysis with feedback failed');
    }

    return response.json();
  },
};

/**
 * Worlds API (Library & World Management)
 */
export const worldsApi = {
  // ========================
  // World CRUD
  // ========================

  /**
   * Create a new world
   */
  async createWorld(data: CreateWorldRequest): Promise<World> {
    const response = await fetch(`${API_BASE_URL}/worlds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create world');
    }

    return response.json();
  },

  /**
   * List all worlds
   */
  async listWorlds(skip = 0, limit = 100): Promise<World[]> {
    const response = await fetch(`${API_BASE_URL}/worlds?skip=${skip}&limit=${limit}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list worlds');
    }

    return response.json();
  },

  /**
   * Get a specific world
   */
  async getWorld(worldId: string): Promise<World> {
    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get world');
    }

    return response.json();
  },

  /**
   * Update a world
   */
  async updateWorld(worldId: string, data: UpdateWorldRequest): Promise<World> {
    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update world');
    }

    return response.json();
  },

  /**
   * Delete a world
   */
  async deleteWorld(worldId: string): Promise<DeleteResponse> {
    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete world');
    }

    return response.json();
  },

  // ========================
  // Series CRUD
  // ========================

  /**
   * Create a series in a world
   */
  async createSeries(worldId: string, data: CreateSeriesRequest): Promise<Series> {
    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}/series`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create series');
    }

    return response.json();
  },

  /**
   * List series in a world
   */
  async listSeries(worldId: string, skip = 0, limit = 100): Promise<Series[]> {
    const response = await fetch(
      `${API_BASE_URL}/worlds/${worldId}/series?skip=${skip}&limit=${limit}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list series');
    }

    return response.json();
  },

  /**
   * Get a specific series
   */
  async getSeries(seriesId: string): Promise<Series> {
    const response = await fetch(`${API_BASE_URL}/worlds/series/${seriesId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get series');
    }

    return response.json();
  },

  /**
   * Update a series
   */
  async updateSeries(seriesId: string, data: UpdateSeriesRequest): Promise<Series> {
    const response = await fetch(`${API_BASE_URL}/worlds/series/${seriesId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update series');
    }

    return response.json();
  },

  /**
   * Delete a series
   */
  async deleteSeries(seriesId: string): Promise<DeleteResponse> {
    const response = await fetch(`${API_BASE_URL}/worlds/series/${seriesId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete series');
    }

    return response.json();
  },

  // ========================
  // Manuscript Assignment
  // ========================

  /**
   * List manuscripts in a series
   */
  async listSeriesManuscripts(seriesId: string, skip = 0, limit = 100): Promise<ManuscriptBrief[]> {
    const response = await fetch(
      `${API_BASE_URL}/worlds/series/${seriesId}/manuscripts?skip=${skip}&limit=${limit}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list series manuscripts');
    }

    return response.json();
  },

  /**
   * Assign a manuscript to a series
   */
  async assignManuscriptToSeries(
    seriesId: string,
    data: AssignManuscriptRequest
  ): Promise<ManuscriptBrief> {
    const response = await fetch(`${API_BASE_URL}/worlds/series/${seriesId}/manuscripts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to assign manuscript to series');
    }

    return response.json();
  },

  /**
   * Remove a manuscript from a series
   */
  async removeManuscriptFromSeries(seriesId: string, manuscriptId: string): Promise<DeleteResponse> {
    const response = await fetch(
      `${API_BASE_URL}/worlds/series/${seriesId}/manuscripts/${manuscriptId}`,
      { method: 'DELETE' }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to remove manuscript from series');
    }

    return response.json();
  },

  /**
   * List all manuscripts in a world
   */
  async listWorldManuscripts(worldId: string, skip = 0, limit = 100): Promise<ManuscriptBrief[]> {
    const response = await fetch(
      `${API_BASE_URL}/worlds/${worldId}/manuscripts?skip=${skip}&limit=${limit}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list world manuscripts');
    }

    return response.json();
  },

  // ========================
  // World Entities
  // ========================

  /**
   * Create a world-scoped entity
   */
  async createWorldEntity(worldId: string, data: CreateWorldEntityRequest): Promise<WorldEntityResponse> {
    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}/entities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create world entity');
    }

    return response.json();
  },

  /**
   * List world-scoped entities
   */
  async listWorldEntities(
    worldId: string,
    type?: string,
    skip = 0,
    limit = 100
  ): Promise<WorldEntityResponse[]> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (type) params.append('type', type);

    const response = await fetch(`${API_BASE_URL}/worlds/${worldId}/entities?${params}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list world entities');
    }

    return response.json();
  },

  /**
   * Change an entity's scope
   */
  async changeEntityScope(entityId: string, data: ChangeScopeRequest): Promise<WorldEntityResponse> {
    const response = await fetch(`${API_BASE_URL}/worlds/entities/${entityId}/scope`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to change entity scope');
    }

    return response.json();
  },

  /**
   * Copy a world entity to a manuscript
   */
  async copyEntityToManuscript(
    entityId: string,
    data: CopyEntityRequest
  ): Promise<WorldEntityResponse> {
    const response = await fetch(`${API_BASE_URL}/worlds/entities/${entityId}/copy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to copy entity to manuscript');
    }

    return response.json();
  },
};

/**
 * Entity State API - Track entity states at different narrative points
 */
export const entityStateApi = {
  /**
   * Create a state snapshot for an entity
   */
  async createStateSnapshot(
    entityId: string,
    data: CreateStateRequest
  ): Promise<EntityTimelineState> {
    const response = await fetch(`${API_BASE_URL}/entities/${entityId}/states`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create state snapshot');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * List all state snapshots for an entity
   */
  async listEntityStates(
    entityId: string,
    manuscriptId?: string,
    canonicalOnly = false
  ): Promise<EntityTimelineState[]> {
    const params = new URLSearchParams();
    if (manuscriptId) params.append('manuscript_id', manuscriptId);
    if (canonicalOnly) params.append('canonical_only', 'true');

    const response = await fetch(
      `${API_BASE_URL}/entities/${entityId}/states?${params.toString()}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list entity states');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get state at a specific narrative point
   */
  async getStateAtPoint(
    entityId: string,
    manuscriptId?: string,
    chapterId?: string,
    timelineEventId?: string
  ): Promise<EntityTimelineState | null> {
    const params = new URLSearchParams();
    if (manuscriptId) params.append('manuscript_id', manuscriptId);
    if (chapterId) params.append('chapter_id', chapterId);
    if (timelineEventId) params.append('timeline_event_id', timelineEventId);

    const response = await fetch(
      `${API_BASE_URL}/entities/${entityId}/states/at?${params.toString()}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get state at point');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Compare two state snapshots
   */
  async getStateDiff(
    entityId: string,
    fromStateId: string,
    toStateId: string
  ): Promise<StateDiffResult> {
    const response = await fetch(`${API_BASE_URL}/entities/${entityId}/states/diff`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_state_id: fromStateId,
        to_state_id: toStateId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get state diff');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get character journey
   */
  async getCharacterJourney(
    entityId: string,
    manuscriptId?: string
  ): Promise<JourneyPoint[]> {
    const params = new URLSearchParams();
    if (manuscriptId) params.append('manuscript_id', manuscriptId);

    const response = await fetch(
      `${API_BASE_URL}/entities/${entityId}/journey?${params.toString()}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get character journey');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Update a state snapshot
   */
  async updateState(
    entityId: string,
    stateId: string,
    data: UpdateStateRequest
  ): Promise<EntityTimelineState> {
    const response = await fetch(`${API_BASE_URL}/entities/${entityId}/states/${stateId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update state');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Delete a state snapshot
   */
  async deleteState(entityId: string, stateId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/entities/${entityId}/states/${stateId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete state');
    }
  },

  /**
   * Bulk create state snapshots
   */
  async bulkCreateStates(
    entityId: string,
    states: CreateStateRequest[]
  ): Promise<EntityTimelineState[]> {
    const response = await fetch(`${API_BASE_URL}/entities/${entityId}/states/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ states }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to bulk create states');
    }

    const result = await response.json();
    return result.data;
  },
};

/**
 * Series/World Outline API - Multi-book outline management
 */
export const seriesOutlineApi = {
  /**
   * List available series structure templates
   */
  async listSeriesStructures(): Promise<SeriesStructureSummary[]> {
    const response = await fetch(`${API_BASE_URL}/outlines/series-structures`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list series structures');
    }

    const result = await response.json();
    return result.structures;
  },

  /**
   * Get detailed series structure template
   */
  async getSeriesStructure(structureType: string): Promise<SeriesStructure> {
    const response = await fetch(`${API_BASE_URL}/outlines/series-structures/${structureType}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get series structure');
    }

    const result = await response.json();
    return result.structure;
  },

  /**
   * Create a series-level outline
   */
  async createSeriesOutline(seriesId: string, data: SeriesOutlineCreate): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/series/${seriesId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create series outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get all outlines for a series
   */
  async getSeriesOutlines(seriesId: string): Promise<Outline[]> {
    const response = await fetch(`${API_BASE_URL}/outlines/series/${seriesId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get series outlines');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get active series outline
   */
  async getActiveSeriesOutline(seriesId: string): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/series/${seriesId}/active`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get active series outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get full series structure with manuscripts
   */
  async getSeriesStructureWithManuscripts(seriesId: string): Promise<SeriesStructureWithManuscripts> {
    const response = await fetch(`${API_BASE_URL}/outlines/series/${seriesId}/structure`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get series structure');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Create a world-level outline
   */
  async createWorldOutline(worldId: string, data: WorldOutlineCreate): Promise<Outline> {
    const response = await fetch(`${API_BASE_URL}/outlines/world/${worldId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create world outline');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Get all outlines for a world
   */
  async getWorldOutlines(worldId: string): Promise<Outline[]> {
    const response = await fetch(`${API_BASE_URL}/outlines/world/${worldId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get world outlines');
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Link a series beat to a manuscript outline
   */
  async linkBeatToManuscript(
    outlineId: string,
    data: LinkBeatToManuscriptRequest
  ): Promise<PlotBeat> {
    const response = await fetch(`${API_BASE_URL}/outlines/${outlineId}/link-manuscript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to link beat to manuscript');
    }

    const result = await response.json();
    return result.data;
  },
};

// ==================== Import API ====================

/**
 * Import API - Manuscript import from various document formats
 */
export const importApi = {
  /**
   * Get list of supported import formats
   */
  async getSupportedFormats(): Promise<SupportedFormat[]> {
    const response = await fetch(`${API_BASE_URL}/import/formats`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get supported formats');
    }

    const result = await response.json();
    return result.formats;
  },

  /**
   * Parse an uploaded document and detect chapters
   * Step 1 of the two-step import flow
   */
  async parseFile(
    file: File,
    detectionMode: DetectionMode = 'auto'
  ): Promise<ImportPreview> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${API_BASE_URL}/import/parse?detection_mode=${detectionMode}`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to parse document');
    }

    return response.json();
  },

  /**
   * Create a manuscript from a previously parsed import
   * Step 2 of the two-step import flow
   */
  async createFromImport(data: ImportCreateRequest): Promise<ImportCreateResponse> {
    const response = await fetch(`${API_BASE_URL}/import/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create manuscript from import');
    }

    return response.json();
  },

  /**
   * Get cached parse preview by ID
   */
  async getParsePreview(parseId: string): Promise<ImportPreview> {
    const response = await fetch(`${API_BASE_URL}/import/preview/${parseId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Parse result not found or expired');
    }

    return response.json();
  },
};

// ==================== Foreshadowing API ====================

import type {
  ForeshadowingPair,
  ForeshadowingType,
  ForeshadowingStats,
  PayoffSuggestion,
} from '@/types/foreshadowing';

import type {
  SupportedFormat,
  ImportPreview,
  ImportCreateRequest,
  ImportCreateResponse,
  DetectionMode,
} from '@/types/import';

export const foreshadowingApi = {
  /**
   * Create a new foreshadowing pair
   */
  async createPair(data: {
    manuscript_id: string;
    foreshadowing_event_id: string;
    foreshadowing_type: ForeshadowingType;
    foreshadowing_text: string;
    payoff_event_id?: string;
    payoff_text?: string;
    confidence?: number;
    notes?: string;
  }): Promise<ForeshadowingPair> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair }>(
      '/foreshadowing/pairs',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
    return response.data;
  },

  /**
   * Get all foreshadowing pairs for a manuscript
   */
  async getPairs(
    manuscriptId: string,
    options?: {
      include_resolved?: boolean;
      foreshadowing_type?: ForeshadowingType;
    }
  ): Promise<ForeshadowingPair[]> {
    const params = new URLSearchParams();
    if (options?.include_resolved !== undefined) {
      params.set('include_resolved', String(options.include_resolved));
    }
    if (options?.foreshadowing_type) {
      params.set('foreshadowing_type', options.foreshadowing_type);
    }
    const queryString = params.toString();
    const url = `/foreshadowing/pairs/${manuscriptId}${queryString ? `?${queryString}` : ''}`;
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair[] }>(url);
    // Ensure we return an array even if data is undefined
    return response.data || [];
  },

  /**
   * Get a single foreshadowing pair by ID
   */
  async getPair(pairId: string): Promise<ForeshadowingPair> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair }>(
      `/foreshadowing/pairs/single/${pairId}`
    );
    return response.data;
  },

  /**
   * Update a foreshadowing pair
   */
  async updatePair(
    pairId: string,
    data: {
      foreshadowing_type?: ForeshadowingType;
      foreshadowing_text?: string;
      payoff_event_id?: string;
      payoff_text?: string;
      confidence?: number;
      notes?: string;
    }
  ): Promise<ForeshadowingPair> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair }>(
      `/foreshadowing/pairs/${pairId}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
    return response.data;
  },

  /**
   * Delete a foreshadowing pair
   */
  async deletePair(pairId: string): Promise<void> {
    await apiFetch(`/foreshadowing/pairs/${pairId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Link a payoff event to a foreshadowing setup
   */
  async linkPayoff(
    pairId: string,
    data: {
      payoff_event_id: string;
      payoff_text: string;
    }
  ): Promise<ForeshadowingPair> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair }>(
      `/foreshadowing/pairs/${pairId}/link-payoff`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
    return response.data;
  },

  /**
   * Unlink a payoff from a foreshadowing setup
   */
  async unlinkPayoff(pairId: string): Promise<ForeshadowingPair> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair }>(
      `/foreshadowing/pairs/${pairId}/unlink-payoff`,
      {
        method: 'POST',
      }
    );
    return response.data;
  },

  /**
   * Get unresolved foreshadowing pairs (Chekhov violations)
   */
  async getUnresolved(manuscriptId: string): Promise<ForeshadowingPair[]> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingPair[]; count: number }>(
      `/foreshadowing/unresolved/${manuscriptId}`
    );
    return response.data;
  },

  /**
   * Get foreshadowing pairs involving a specific event
   */
  async getForEvent(eventId: string): Promise<{
    setups: ForeshadowingPair[];
    payoffs: ForeshadowingPair[];
  }> {
    const response = await apiFetch<{
      success: boolean;
      data: { setups: ForeshadowingPair[]; payoffs: ForeshadowingPair[] };
    }>(`/foreshadowing/event/${eventId}`);
    return response.data;
  },

  /**
   * Get foreshadowing statistics for a manuscript
   */
  async getStats(manuscriptId: string): Promise<ForeshadowingStats> {
    const response = await apiFetch<{ success: boolean; data: ForeshadowingStats }>(
      `/foreshadowing/stats/${manuscriptId}`
    );
    return response.data;
  },

  /**
   * Get suggested potential payoff events for a setup
   */
  async getSuggestions(pairId: string): Promise<PayoffSuggestion[]> {
    const response = await apiFetch<{ success: boolean; data: PayoffSuggestion[] }>(
      `/foreshadowing/suggestions/${pairId}`
    );
    return response.data;
  },
};


// ========================
// Share API - Shareable recap cards
// ========================

export interface CreateShareRequest {
  manuscript_id: string;
  chapter_id?: string;
  recap_type: 'chapter' | 'writing_stats';
  title: string;
  description?: string;
  template: string;
  image_data_base64?: string;
  recap_content?: Record<string, any>;
}

export interface ShareResponse {
  share_id: string;
  share_url: string;
}

export interface ShareStats {
  share_id: string;
  view_count: number;
  share_count: number;
  created_at: string;
}

export const shareApi = {
  /**
   * Create a shareable recap card
   */
  async createShare(data: CreateShareRequest): Promise<ShareResponse> {
    const response = await fetch(`${API_BASE_URL}/share/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create share');
    }

    return response.json();
  },

  /**
   * Get share statistics
   */
  async getStats(shareId: string): Promise<ShareStats> {
    const response = await fetch(`${API_BASE_URL}/share/stats/${shareId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get share stats');
    }

    return response.json();
  },

  /**
   * Track a share action (when user clicks share)
   */
  async trackShare(shareId: string, platform: string): Promise<void> {
    await fetch(`${API_BASE_URL}/share/track/${shareId}?platform=${encodeURIComponent(platform)}`, {
      method: 'POST',
    });
  },

  /**
   * Get the share URL for a given share ID
   */
  getShareUrl(shareId: string): string {
    return `${window.location.origin}/share/${shareId}`;
  },

  /**
   * Get the image URL for a share
   */
  getImageUrl(shareId: string): string {
    return `${API_BASE_URL}/share/image/${shareId}.png`;
  },
};

// ========================
// Agent API - Smart Coach & Writing Assistant
// ========================

export interface AnalyzeTextAgentRequest {
  api_key: string;
  text: string;
  user_id: string;
  manuscript_id: string;
  chapter_id?: string;
  model_provider?: string;
  model_name?: string;
  agents?: string[];
  include_insights?: boolean;
}

export interface QuickCheckAgentRequest {
  api_key: string;
  text: string;
  user_id: string;
  manuscript_id: string;
  agent_type: string;
  model_provider?: string;
  model_name?: string;
}

export interface SuggestionFeedbackRequest {
  user_id: string;
  agent_type: string;
  suggestion_type: string;
  suggestion_text: string;
  action: 'accepted' | 'rejected' | 'modified' | 'ignored';
  original_text?: string;
  modified_text?: string;
  manuscript_id?: string;
  analysis_id?: string;
  user_explanation?: string;
}

export interface StartCoachSessionRequest {
  api_key: string;
  user_id: string;
  manuscript_id?: string;
  title?: string;
  initial_context?: Record<string, any>;
  model_provider?: string;
  model_name?: string;
}

export interface CoachChatRequest {
  api_key: string;
  user_id: string;
  session_id: string;
  message: string;
  context?: Record<string, any>;
  model_provider?: string;
  model_name?: string;
}

export const agentApi = {
  // ========================
  // Writing Assistant
  // ========================

  /**
   * Run multi-agent analysis on text
   */
  async analyzeText(data: AnalyzeTextAgentRequest): Promise<{
    success: boolean;
    data: any;
    cost: { total: number; formatted: string };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis failed');
    }

    return response.json();
  },

  /**
   * Run single-agent quick check
   */
  async quickCheck(data: QuickCheckAgentRequest): Promise<{
    success: boolean;
    data: any;
    cost: { total: number; formatted: string };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/quick-check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Quick check failed');
    }

    return response.json();
  },

  /**
   * Record feedback on a suggestion
   */
  async recordFeedback(data: SuggestionFeedbackRequest): Promise<{
    success: boolean;
    data: { id: string; action: string; message: string };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to record feedback');
    }

    return response.json();
  },

  /**
   * Get author insights and learning data
   */
  async getAuthorInsights(userId: string): Promise<{ success: boolean; data: any }> {
    const response = await fetch(`${API_BASE_URL}/agents/insights/${userId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get insights');
    }

    return response.json();
  },

  /**
   * Get analysis history
   */
  async getAnalysisHistory(
    userId: string,
    manuscriptId?: string,
    limit = 20
  ): Promise<{ success: boolean; data: any[] }> {
    const params = new URLSearchParams();
    if (manuscriptId) params.append('manuscript_id', manuscriptId);
    params.append('limit', String(limit));

    const response = await fetch(
      `${API_BASE_URL}/agents/history/${userId}?${params.toString()}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get history');
    }

    return response.json();
  },

  /**
   * Get a specific analysis
   */
  async getAnalysis(analysisId: string): Promise<{ success: boolean; data: any }> {
    const response = await fetch(`${API_BASE_URL}/agents/analysis/${analysisId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis not found');
    }

    return response.json();
  },

  /**
   * Rate an analysis
   */
  async rateAnalysis(
    analysisId: string,
    rating: number,
    feedback?: string
  ): Promise<{ success: boolean; message: string }> {
    const params = new URLSearchParams();
    params.append('rating', String(rating));
    if (feedback) params.append('feedback', feedback);

    const response = await fetch(
      `${API_BASE_URL}/agents/analysis/${analysisId}/rate?${params.toString()}`,
      { method: 'PUT' }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to rate analysis');
    }

    return response.json();
  },

  /**
   * Get available agent types
   */
  async getAgentTypes(): Promise<{
    success: boolean;
    data: Array<{ type: string; name: string; description: string }>;
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/types`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get agent types');
    }

    return response.json();
  },

  // ========================
  // Smart Coach
  // ========================

  /**
   * Start a new coaching session
   */
  async startCoachSession(data: StartCoachSessionRequest): Promise<{
    success: boolean;
    data: {
      id: string;
      title: string;
      manuscript_id?: string;
      status: string;
      created_at: string;
    };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/coach/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start session');
    }

    return response.json();
  },

  /**
   * Send a message to the coach
   */
  async coachChat(data: CoachChatRequest): Promise<{
    success: boolean;
    data: {
      content: string;
      tools_used: string[];
      tool_results: Record<string, any>;
      cost: number;
      tokens: number;
      session_id: string;
    };
    cost: { total: number; formatted: string };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/coach/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat failed');
    }

    return response.json();
  },

  /**
   * List coaching sessions for a user
   */
  async listCoachSessions(
    userId: string,
    manuscriptId?: string,
    includeArchived = false,
    limit = 20
  ): Promise<{
    success: boolean;
    data: Array<{
      id: string;
      title: string;
      manuscript_id?: string;
      message_count: number;
      total_cost: number;
      status: string;
      created_at: string;
      updated_at?: string;
      last_message_at?: string;
    }>;
  }> {
    const params = new URLSearchParams();
    if (manuscriptId) params.append('manuscript_id', manuscriptId);
    params.append('include_archived', String(includeArchived));
    params.append('limit', String(limit));

    const response = await fetch(
      `${API_BASE_URL}/agents/coach/sessions/${userId}?${params.toString()}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list sessions');
    }

    return response.json();
  },

  /**
   * Get a coaching session with messages
   */
  async getCoachSession(sessionId: string): Promise<{
    success: boolean;
    data: {
      session: {
        id: string;
        title: string;
        manuscript_id?: string;
        message_count: number;
        total_cost: number;
        total_tokens: number;
        status: string;
        initial_context?: Record<string, any>;
        created_at: string;
        updated_at?: string;
      };
      messages: Array<{
        id: string;
        role: string;
        content: string;
        tools_used?: string[];
        cost?: number;
        tokens?: number;
        created_at: string;
      }>;
    };
  }> {
    const response = await fetch(`${API_BASE_URL}/agents/coach/session/${sessionId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Session not found');
    }

    return response.json();
  },

  /**
   * Archive a coaching session
   */
  async archiveCoachSession(
    sessionId: string,
    userId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(
      `${API_BASE_URL}/agents/coach/session/${sessionId}/archive?user_id=${encodeURIComponent(userId)}`,
      { method: 'PUT' }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to archive session');
    }

    return response.json();
  },

  /**
   * Update session title
   */
  async updateCoachSessionTitle(
    sessionId: string,
    userId: string,
    title: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(
      `${API_BASE_URL}/agents/coach/session/${sessionId}/title?user_id=${encodeURIComponent(userId)}&title=${encodeURIComponent(title)}`,
      { method: 'PUT' }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update title');
    }

    return response.json();
  },
};

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
  const result = await response.json();
  return result.data;
}

export default {
  manuscript: manuscriptApi,
  versioning: versioningApi,
  codex: codexApi,
  timeline: timelineApi,
  chapters: chaptersApi,
  outline: outlineApi,
  recap: recapApi,
  analytics: analyticsApi,
  brainstorming: brainstormingApi,
  ai: aiApi,
  worlds: worldsApi,
  entityState: entityStateApi,
  seriesOutline: seriesOutlineApi,
  foreshadowing: foreshadowingApi,
  import: importApi,
  share: shareApi,
  agent: agentApi,
  healthCheck,
};
