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
    return apiFetch<Manuscript[]>('/manuscripts');
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
   * Resolve an inconsistency
   */
  async resolveInconsistency(inconsistencyId: string): Promise<{ success: boolean; message: string }> {
    return apiFetch(`/timeline/inconsistencies/${inconsistencyId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get timeline statistics
   */
  async getStats(manuscriptId: string): Promise<{ success: boolean; data: TimelineStats }> {
    return apiFetch(`/timeline/stats/${manuscriptId}`);
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
};

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
  return response.json();
}

export default {
  manuscript: manuscriptApi,
  versioning: versioningApi,
  codex: codexApi,
  timeline: timelineApi,
  chapters: chaptersApi,
  healthCheck,
};
