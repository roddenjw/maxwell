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
   * Create a snapshot (save version)
   */
  async createSnapshot(data: {
    manuscript_id: string;
    content: string;
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
   * Restore a snapshot
   */
  async restoreSnapshot(data: {
    manuscript_id: string;
    snapshot_id: string;
    create_backup?: boolean;
  }): Promise<{
    content: string;
    backup_snapshot_id?: string;
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
  healthCheck,
};
