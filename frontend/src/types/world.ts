/**
 * World and Series types for Library & World Management
 */

// Entity scope constants (match backend)
export type EntityScope = 'MANUSCRIPT' | 'SERIES' | 'WORLD';

/**
 * World - A shared fictional universe
 */
export interface World {
  id: string;
  name: string;
  description: string;
  settings: WorldSettings;
  created_at: string;
  updated_at: string;
}

/**
 * World settings (customizable per world)
 */
export interface WorldSettings {
  genre?: string;
  subgenres?: string[];
  magic_system?: string;
  technology_level?: string;
  time_period?: string;
  themes?: string[];
  [key: string]: unknown;
}

/**
 * Series - A collection of manuscripts within a world
 */
export interface Series {
  id: string;
  world_id: string;
  name: string;
  description: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}

/**
 * Brief manuscript info for listings
 */
export interface ManuscriptBrief {
  id: string;
  title: string;
  author: string;
  description: string;
  word_count: number;
  order_index: number;
  created_at: string;
  updated_at: string;
}

/**
 * World with nested series for hierarchical display
 */
export interface WorldWithSeries extends World {
  series: SeriesWithManuscripts[];
}

/**
 * Series with nested manuscripts for hierarchical display
 */
export interface SeriesWithManuscripts extends Series {
  manuscripts: ManuscriptBrief[];
}

// ========================
// Request Types
// ========================

export interface CreateWorldRequest {
  name: string;
  description?: string;
  settings?: WorldSettings;
}

export interface UpdateWorldRequest {
  name?: string;
  description?: string;
  settings?: WorldSettings;
}

export interface CreateSeriesRequest {
  name: string;
  description?: string;
  order_index?: number;
}

export interface UpdateSeriesRequest {
  name?: string;
  description?: string;
  order_index?: number;
}

export interface AssignManuscriptRequest {
  manuscript_id: string;
  order_index?: number;
}

export interface CreateWorldEntityRequest {
  type: 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';
  name: string;
  aliases?: string[];
  attributes?: Record<string, unknown>;
}

export interface ChangeScopeRequest {
  new_scope: EntityScope;
  world_id?: string;
}

export interface CopyEntityRequest {
  manuscript_id: string;
}

// ========================
// Response Types
// ========================

export interface WorldEntityResponse {
  id: string;
  world_id: string | null;
  manuscript_id: string | null;
  scope: EntityScope;
  type: string;
  name: string;
  aliases: string[];
  attributes: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DeleteResponse {
  success: boolean;
  message: string;
}

export interface MoveManuscriptRequest {
  target_series_id: string;
  order_index?: number;
}

export interface MoveManuscriptResponse {
  entries_copied: number;
  entries_merged: number;
  changes_copied: number;
  arcs_updated: number;
  cross_world: boolean;
}
