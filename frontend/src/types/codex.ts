/**
 * TypeScript types for The Codex
 * Entity and relationship management
 */

// Entity Types
export enum EntityType {
  CHARACTER = "CHARACTER",
  LOCATION = "LOCATION",
  ITEM = "ITEM",
  LORE = "LORE",
}

// Template Types for structured entity creation
export enum TemplateType {
  CHARACTER = "CHARACTER",
  LOCATION = "LOCATION",
  ITEM = "ITEM",
  MAGIC_SYSTEM = "MAGIC_SYSTEM",
  CREATURE = "CREATURE",
  ORGANIZATION = "ORGANIZATION",
  CUSTOM = "CUSTOM",
}

// Character template data structure
export interface CharacterTemplateData {
  role?: string;
  physical?: {
    age?: string;
    appearance?: string;
    distinguishing_features?: string;
  };
  personality?: {
    traits?: string[];
    flaws?: string;
    strengths?: string;
  };
  backstory?: {
    origin?: string;
    key_events?: string;
    secrets?: string;
  };
  motivation?: {
    want?: string;
    need?: string;
  };
  relationships?: Array<{
    entity_id?: string;
    entity_name?: string;
    type?: string;
    notes?: string;
  }>;
}

// Location template data structure
export interface LocationTemplateData {
  type?: string;  // city, village, castle, forest, etc.
  geography?: {
    terrain?: string;
    climate?: string;
    size?: string;
  };
  atmosphere?: {
    mood?: string;
    sounds?: string;
    smells?: string;
  };
  history?: {
    founded?: string;
    key_events?: string;
    current_state?: string;
  };
  notable_features?: string[];
  inhabitants?: string;
  secrets?: string;
}

// Item template data structure
export interface ItemTemplateData {
  type?: string;  // weapon, artifact, tool, etc.
  origin?: {
    creator?: string;
    creation_date?: string;
    creation_story?: string;
  };
  properties?: {
    physical_description?: string;
    powers?: string;
    limitations?: string;
  };
  history?: {
    previous_owners?: string;
    notable_events?: string;
  };
  current_owner?: string;
  significance?: string;
}

// Magic System template data structure
export interface MagicSystemTemplateData {
  name?: string;
  source?: string;  // where magic comes from
  rules?: {
    how_it_works?: string;
    limitations?: string;
    costs?: string;
  };
  users?: {
    who_can_use?: string;
    how_learned?: string;
    organizations?: string;
  };
  effects?: string[];
  weaknesses?: string;
  cultural_impact?: string;
}

// Creature template data structure
export interface CreatureTemplateData {
  species?: string;
  habitat?: string;
  physical?: {
    appearance?: string;
    size?: string;
    distinguishing_features?: string;
  };
  behavior?: {
    temperament?: string;
    diet?: string;
    social_structure?: string;
  };
  abilities?: string[];
  weaknesses?: string;
  cultural_significance?: string;
}

// Organization template data structure
export interface OrganizationTemplateData {
  type?: string;  // guild, government, cult, etc.
  purpose?: string;
  structure?: {
    leadership?: string;
    hierarchy?: string;
    membership_requirements?: string;
  };
  history?: {
    founding?: string;
    key_events?: string;
    current_status?: string;
  };
  resources?: string;
  allies?: string;
  enemies?: string;
  secrets?: string;
}

// Union type for all template data
export type TemplateData =
  | CharacterTemplateData
  | LocationTemplateData
  | ItemTemplateData
  | MagicSystemTemplateData
  | CreatureTemplateData
  | OrganizationTemplateData
  | Record<string, any>;

// Relationship Types
export enum RelationshipType {
  ROMANTIC = "ROMANTIC",
  CONFLICT = "CONFLICT",
  ALLIANCE = "ALLIANCE",
  FAMILY = "FAMILY",
  PROFESSIONAL = "PROFESSIONAL",
  ACQUAINTANCE = "ACQUAINTANCE",
}

// Suggestion Status
export enum SuggestionStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

// Base Entity Interface
export interface Entity {
  id: string;
  manuscript_id: string;
  world_id?: string;
  scope?: 'MANUSCRIPT' | 'SERIES' | 'WORLD';
  type: EntityType;
  template_type?: TemplateType;
  template_data?: TemplateData;
  name: string;
  aliases: string[];
  attributes: Record<string, any>;
  appearance_history: AppearanceRecord[];
  created_at: string;
  updated_at: string;
}

// Appearance Record
export interface AppearanceRecord {
  scene_id?: string;
  description: string;
  timestamp: string;
}

// Character-specific type (extends Entity)
export interface Character extends Entity {
  type: EntityType.CHARACTER;
  attributes: {
    age?: string;
    appearance?: string;
    voice?: string;
    personality?: string;
    backstory?: string;
    [key: string]: any;
  };
}

// Location-specific type (extends Entity)
export interface Location extends Entity {
  type: EntityType.LOCATION;
  attributes: {
    description?: string;
    atmosphere?: string;
    geography?: string;
    [key: string]: any;
  };
}

// Item-specific type (extends Entity)
export interface Item extends Entity {
  type: EntityType.ITEM;
  attributes: {
    description?: string;
    significance?: string;
    owner?: string;
    [key: string]: any;
  };
}

// Lore-specific type (extends Entity)
export interface Lore extends Entity {
  type: EntityType.LORE;
  attributes: {
    description?: string;
    significance?: string;
    category?: string;
    [key: string]: any;
  };
}

// Relationship Interface
export interface Relationship {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: RelationshipType;
  strength: number;
  context: RelationshipContext[];
  created_at: string;
  updated_at: string;
}

// Relationship Context
export interface RelationshipContext {
  scene_id?: string;
  description: string;
}

// Entity Suggestion Interface
export interface EntitySuggestion {
  id: string;
  manuscript_id: string;
  name: string;
  type: EntityType;
  context: string;
  status: SuggestionStatus;
  created_at: string;
}

// API Request Types

export interface CreateEntityRequest {
  manuscript_id: string;
  type: EntityType;
  name: string;
  aliases?: string[];
  attributes?: Record<string, any>;
  template_type?: TemplateType;
  template_data?: TemplateData;
}

export interface UpdateEntityRequest {
  name?: string;
  aliases?: string[];
  attributes?: Record<string, any>;
  template_type?: TemplateType;
  template_data?: TemplateData;
}

export interface CreateRelationshipRequest {
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: RelationshipType;
  strength?: number;
  context?: RelationshipContext[];
}

export interface ApproveSuggestionRequest {
  suggestion_id: string;
  aliases?: string[];
  attributes?: Record<string, any>;
}

export interface AnalyzeTextRequest {
  manuscript_id: string;
  text: string;
}

// UI State Types

export type CodexTab = "entities" | "intel" | "links" | "timeline" | "timeline-issues" | "timeline-graph";

export interface CodexUIState {
  activeTab: CodexTab;
  isSidebarOpen: boolean;
  selectedEntityId: string | null;
  isAnalyzing: boolean;
}

// Graph Visualization Types

export interface GraphNode {
  id: string;
  name: string;
  type: EntityType;
  color: string;
}

export interface GraphLink {
  source: string;
  target: string;
  type: RelationshipType;
  strength: number;
  label: string;
}

// Helper Types

export type EntityMap = Record<string, Entity>;
export type RelationshipMap = Record<string, Relationship>;

// Type Guards

export function isCharacter(entity: Entity): entity is Character {
  return entity.type === EntityType.CHARACTER;
}

export function isLocation(entity: Entity): entity is Location {
  return entity.type === EntityType.LOCATION;
}

export function isItem(entity: Entity): entity is Item {
  return entity.type === EntityType.ITEM;
}

export function isLore(entity: Entity): entity is Lore {
  return entity.type === EntityType.LORE;
}

// Utility Functions

export function getEntityTypeColor(type: EntityType): string {
  switch (type) {
    case EntityType.CHARACTER:
      return "#B48E55"; // bronze
    case EntityType.LOCATION:
      return "#60A5FA"; // blue
    case EntityType.ITEM:
      return "#34D399"; // green
    case EntityType.LORE:
      return "#A78BFA"; // purple
    default:
      return "#94A3B8"; // slate
  }
}

export function getRelationshipTypeLabel(type: RelationshipType): string {
  switch (type) {
    case RelationshipType.ROMANTIC:
      return "Romantic";
    case RelationshipType.CONFLICT:
      return "Conflict";
    case RelationshipType.ALLIANCE:
      return "Alliance";
    case RelationshipType.FAMILY:
      return "Family";
    case RelationshipType.PROFESSIONAL:
      return "Professional";
    case RelationshipType.ACQUAINTANCE:
      return "Acquaintance";
    default:
      return type;
  }
}

export function getEntityTypeIcon(type: EntityType): string {
  switch (type) {
    case EntityType.CHARACTER:
      return "👤";
    case EntityType.LOCATION:
      return "📍";
    case EntityType.ITEM:
      return "📦";
    case EntityType.LORE:
      return "📖";
    default:
      return "•";
  }
}
