/**
 * Wiki Types
 * Type definitions for the World Wiki system
 */

// ==================== Entry Types ====================

export type WikiEntryType =
  | 'character'
  | 'character_arc'
  | 'character_relationship'
  | 'location'
  | 'location_history'
  | 'magic_system'
  | 'world_rule'
  | 'technology'
  | 'culture'
  | 'religion'
  | 'faction'
  | 'artifact'
  | 'creature'
  | 'event'
  | 'timeline_fact'
  | 'theme';

export type WikiEntryStatus = 'draft' | 'published' | 'archived';

export type WikiChangeType = 'create' | 'update' | 'merge' | 'delete';

export type WikiChangeStatus = 'pending' | 'approved' | 'rejected';

export type WikiReferenceType =
  | 'mentions'
  | 'related_to'
  | 'part_of'
  | 'conflicts_with'
  | 'depends_on'
  | 'child_of'
  | 'ally_of'
  | 'enemy_of'
  | 'owns'
  | 'member_of'
  | 'located_in'
  // Culture-specific reference types
  | 'born_in'
  | 'exiled_from'
  | 'adopted_into'
  | 'leader_of'
  | 'rebel_against'
  | 'worships'
  | 'trades_with'
  | 'originated_in'
  | 'sacred_to'
  | 'resents';

// ==================== Wiki Entry ====================

export interface WikiEntry {
  id: string;
  world_id: string;
  entry_type: WikiEntryType;
  title: string;
  slug: string;
  content: string | null;
  structured_data: Record<string, any>;
  summary: string | null;
  image_url: string | null;
  parent_id: string | null;
  linked_entity_id: string | null;
  source_manuscripts: string[];
  source_chapters: Array<{
    manuscript_id: string;
    chapter_id: string;
    excerpt?: string;
  }>;
  status: WikiEntryStatus;
  confidence_score: number;
  tags: string[];
  aliases: string[];
  created_by: 'author' | 'ai' | 'codex_sync';
  created_at: string;
  updated_at: string | null;
}

export interface WikiEntryCreate {
  world_id: string;
  entry_type: WikiEntryType;
  title: string;
  content?: string;
  structured_data?: Record<string, any>;
  summary?: string;
  parent_id?: string;
  linked_entity_id?: string;
  tags?: string[];
  aliases?: string[];
}

export interface WikiEntryUpdate {
  title?: string;
  content?: string;
  structured_data?: Record<string, any>;
  summary?: string;
  status?: WikiEntryStatus;
  parent_id?: string;
  tags?: string[];
  aliases?: string[];
  image_url?: string;
}

// ==================== Cross References ====================

export interface WikiCrossReference {
  id: string;
  source_entry_id: string;
  target_entry_id: string;
  reference_type: WikiReferenceType;
  context: string | null;
  bidirectional: boolean;
  display_label: string | null;
  created_by: 'author' | 'ai';
  created_at: string;
}

export interface WikiCrossReferenceCreate {
  source_entry_id: string;
  target_entry_id: string;
  reference_type: WikiReferenceType;
  context?: string;
  bidirectional?: boolean;
}

// ==================== Change Queue ====================

export interface WikiChange {
  id: string;
  wiki_entry_id: string | null;
  world_id: string;
  change_type: WikiChangeType;
  field_changed: string | null;
  old_value: Record<string, any> | null;
  new_value: Record<string, any>;
  proposed_entry: WikiEntryCreate | null;
  reason: string | null;
  source_text: string | null;
  source_chapter_id: string | null;
  source_manuscript_id: string | null;
  confidence: number;
  status: WikiChangeStatus;
  priority: number;
  created_at: string;
  reviewed_at: string | null;
  reviewer_note: string | null;
  entry_title: string | null;
  entry_type: string | null;
}

// ==================== UI State ====================

export interface WikiFilters {
  entryType?: WikiEntryType;
  status?: WikiEntryStatus;
  parentId?: string;
  searchQuery?: string;
}

export interface WikiBrowserState {
  selectedEntry: WikiEntry | null;
  isEditing: boolean;
  filters: WikiFilters;
  viewMode: 'list' | 'grid' | 'tree';
}

// ==================== Entry Type Metadata ====================

export const WIKI_ENTRY_TYPE_INFO: Record<WikiEntryType, {
  label: string;
  icon: string;
  color: string;
  category: string;
}> = {
  character: { label: 'Character', icon: '👤', color: 'text-blue-600', category: 'Characters' },
  character_arc: { label: 'Character Arc', icon: '📈', color: 'text-blue-400', category: 'Characters' },
  character_relationship: { label: 'Relationship', icon: '🤝', color: 'text-blue-300', category: 'Characters' },
  location: { label: 'Location', icon: '🏠', color: 'text-green-600', category: 'Locations' },
  location_history: { label: 'Location History', icon: '📜', color: 'text-green-400', category: 'Locations' },
  magic_system: { label: 'Magic System', icon: '✨', color: 'text-purple-600', category: 'World Rules' },
  world_rule: { label: 'World Rule', icon: '📋', color: 'text-purple-400', category: 'World Rules' },
  technology: { label: 'Technology', icon: '⚙️', color: 'text-gray-600', category: 'World Rules' },
  culture: { label: 'Culture', icon: '🎭', color: 'text-orange-600', category: 'World Rules' },
  religion: { label: 'Religion', icon: '🙏', color: 'text-yellow-600', category: 'World Rules' },
  faction: { label: 'Faction', icon: '⚔️', color: 'text-red-600', category: 'Organizations' },
  artifact: { label: 'Artifact', icon: '💎', color: 'text-amber-600', category: 'Items' },
  creature: { label: 'Creature', icon: '🐉', color: 'text-emerald-600', category: 'Creatures' },
  event: { label: 'Historical Event', icon: '📅', color: 'text-indigo-600', category: 'Events' },
  timeline_fact: { label: 'Timeline Fact', icon: '⏰', color: 'text-cyan-600', category: 'Timeline' },
  theme: { label: 'Theme', icon: '💡', color: 'text-pink-600', category: 'Meta' },
};

export const WIKI_REFERENCE_TYPE_INFO: Record<WikiReferenceType, {
  label: string;
  reverseLabel: string;
}> = {
  mentions: { label: 'Mentions', reverseLabel: 'Mentioned by' },
  related_to: { label: 'Related to', reverseLabel: 'Related to' },
  part_of: { label: 'Part of', reverseLabel: 'Contains' },
  conflicts_with: { label: 'Conflicts with', reverseLabel: 'Conflicts with' },
  depends_on: { label: 'Depends on', reverseLabel: 'Required by' },
  child_of: { label: 'Child of', reverseLabel: 'Parent of' },
  ally_of: { label: 'Ally of', reverseLabel: 'Ally of' },
  enemy_of: { label: 'Enemy of', reverseLabel: 'Enemy of' },
  owns: { label: 'Owns', reverseLabel: 'Owned by' },
  member_of: { label: 'Member of', reverseLabel: 'Has member' },
  located_in: { label: 'Located in', reverseLabel: 'Contains' },
  // Culture-specific reference types
  born_in: { label: 'Born in', reverseLabel: 'Birthplace of' },
  exiled_from: { label: 'Exiled from', reverseLabel: 'Exiled' },
  adopted_into: { label: 'Adopted into', reverseLabel: 'Adopted' },
  leader_of: { label: 'Leader of', reverseLabel: 'Led by' },
  rebel_against: { label: 'Rebel against', reverseLabel: 'Opposed by' },
  worships: { label: 'Worships', reverseLabel: 'Worshipped by' },
  trades_with: { label: 'Trades with', reverseLabel: 'Trades with' },
  originated_in: { label: 'Originated in', reverseLabel: 'Origin of' },
  sacred_to: { label: 'Sacred to', reverseLabel: 'Holds sacred' },
  resents: { label: 'Resents', reverseLabel: 'Resented by' },
};

/** Culture-specific reference types for UI filtering */
export const CULTURE_REFERENCE_TYPES: WikiReferenceType[] = [
  'born_in',
  'exiled_from',
  'adopted_into',
  'leader_of',
  'rebel_against',
  'worships',
  'trades_with',
  'originated_in',
  'sacred_to',
  'resents',
  'member_of',
  'part_of',
  'located_in',
];

// ==================== API Response Types ====================

export interface WikiEntryReferences {
  outgoing: WikiCrossReference[];
  incoming: WikiCrossReference[];
}

export interface WikiSyncStats {
  total: number;
  created: number;
  updated: number;
  linked?: number;
  skipped?: number;
  errors: Array<{
    entity_id?: string;
    entity_name?: string;
    wiki_entry_id?: string;
    wiki_title?: string;
    error: string;
  }>;
}

export interface WikiValidationResult {
  violations: Array<{
    rule_id: string;
    rule_name: string;
    rule_type: string;
    severity: 'error' | 'warning' | 'info';
    message: string;
    text_excerpt: string;
  }>;
  count: number;
}
