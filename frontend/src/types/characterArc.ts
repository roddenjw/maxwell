/**
 * Character Arc Types
 * Type definitions for the Character Arc system
 */

// ==================== Arc Types ====================

export type ArcTemplate =
  | 'redemption'
  | 'fall'
  | 'coming_of_age'
  | 'positive_change'
  | 'flat_arc'
  | 'negative_change'
  | 'disillusionment'
  | 'corruption'
  | 'transformation'
  | 'custom';

export type ArcHealth = 'healthy' | 'at_risk' | 'broken' | 'undefined';

// ==================== Arc Stage ====================

export interface ArcStage {
  id: string;
  name: string;
  description: string;
}

// ==================== Arc Beat ====================

export interface ArcBeat {
  beat_id: string;
  outline_id?: string;
  arc_stage: string;
  chapter_id?: string;
  description?: string;
  is_planned: boolean;
  is_detected: boolean;
  created_at?: string;
}

// ==================== Character Arc ====================

export interface CharacterArc {
  id: string;
  wiki_entry_id: string;
  manuscript_id: string;
  arc_template: ArcTemplate;
  arc_name: string | null;
  planned_arc: Record<string, string>;
  detected_arc: Record<string, DetectedStage>;
  arc_beats: ArcBeat[];
  custom_stages: ArcStage[];
  arc_completion: number;
  arc_health: ArcHealth;
  arc_deviation_notes: string | null;
  last_analyzed_at: string | null;
  analysis_confidence: number;
  created_at: string;
  updated_at: string | null;
}

export interface DetectedStage {
  found: boolean;
  match_count: number;
  sample_match?: string;
  confidence: number;
}

// ==================== Create/Update ====================

export interface CharacterArcCreate {
  wiki_entry_id: string;
  manuscript_id: string;
  arc_template?: ArcTemplate;
  arc_name?: string;
  planned_arc?: Record<string, string>;
  custom_stages?: ArcStage[];
}

export interface CharacterArcUpdate {
  arc_template?: ArcTemplate;
  arc_name?: string;
  planned_arc?: Record<string, string>;
  custom_stages?: ArcStage[];
  arc_deviation_notes?: string;
}

// ==================== Templates ====================

export interface ArcTemplateInfo {
  id: ArcTemplate;
  name: string;
  description: string;
  stages: ArcStage[];
  stage_count: number;
}

export interface ArcTemplateDefinition {
  name: string;
  description: string;
  stages: ArcStage[];
  beat_mapping: Record<string, Record<string, string>>;
}

// ==================== Mapping ====================

export interface ArcBeatMapping {
  arc_stage: string;
  stage_name: string;
  stage_description: string;
  suggested_beat_type: string | null;
  matched_beat_id: string | null;
  matched_beat_name: string | null;
}

// ==================== Comparison ====================

export interface ArcStageComparison {
  stage_id: string;
  stage_name: string;
  planned: string | null;
  detected: boolean;
  detection_confidence: number;
  status: 'matched' | 'missing' | 'unexpected' | 'absent' | 'unknown';
}

export interface ArcComparison {
  arc_id: string;
  comparison: ArcStageComparison[];
  deviations: Array<{
    stage: string;
    stage_name: string;
    issue: string;
  }>;
  health: ArcHealth;
  matched_stages: number;
  total_planned_stages: number;
}

// ==================== Outline View ====================

export interface CharacterOutlineBeat {
  beat_id: string;
  beat_name: string;
  beat_label: string;
  description: string | null;
  order_index: number;
  is_arc_beat: boolean;
  arc_stage: string | null;
  arc_description: string | null;
}

export interface CharacterOutlineView {
  character_name: string;
  wiki_entry_id: string;
  arc: {
    id: string | null;
    template: ArcTemplate | null;
    completion: number;
    health: ArcHealth;
  } | null;
  beats: CharacterOutlineBeat[];
  total_beats: number;
  arc_beats: number;
}

// ==================== Template Metadata ====================

export const ARC_TEMPLATE_INFO: Record<ArcTemplate, {
  name: string;
  icon: string;
  color: string;
  description: string;
}> = {
  redemption: {
    name: 'Redemption Arc',
    icon: '🌅',
    color: 'text-amber-600',
    description: 'Character moves from moral failing to redemption',
  },
  fall: {
    name: 'Tragic Fall',
    icon: '📉',
    color: 'text-red-600',
    description: 'Character descends from nobility to destruction',
  },
  coming_of_age: {
    name: 'Coming of Age',
    icon: '🌱',
    color: 'text-green-600',
    description: 'Character matures from innocence through experience',
  },
  positive_change: {
    name: 'Positive Change',
    icon: '✨',
    color: 'text-blue-600',
    description: 'Character overcomes a lie to embrace truth',
  },
  flat_arc: {
    name: 'Flat Arc',
    icon: '➡️',
    color: 'text-gray-600',
    description: 'Character holds a truth and changes the world',
  },
  negative_change: {
    name: 'Negative Change',
    icon: '⬇️',
    color: 'text-purple-600',
    description: 'Character rejects truth and embraces a lie',
  },
  disillusionment: {
    name: 'Disillusionment',
    icon: '😔',
    color: 'text-indigo-600',
    description: 'Character moves from optimism to realistic worldview',
  },
  corruption: {
    name: 'Corruption',
    icon: '🖤',
    color: 'text-gray-800',
    description: 'Character is gradually corrupted by power',
  },
  transformation: {
    name: 'Transformation',
    icon: '🦋',
    color: 'text-pink-600',
    description: 'Character undergoes fundamental identity change',
  },
  custom: {
    name: 'Custom Arc',
    icon: '✏️',
    color: 'text-teal-600',
    description: 'Define your own arc stages',
  },
};
