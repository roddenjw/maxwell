/**
 * Timeline Types
 * Type definitions for timeline events, inconsistencies, and character locations
 */

export enum EventType {
  SCENE = "SCENE",
  CHAPTER = "CHAPTER",
  FLASHBACK = "FLASHBACK",
  DREAM = "DREAM",
  MONTAGE = "MONTAGE",
}

export enum InconsistencyType {
  LOCATION_CONFLICT = "LOCATION_CONFLICT",
  TIMESTAMP_VIOLATION = "TIMESTAMP_VIOLATION",
  CHARACTER_RESURRECTION = "CHARACTER_RESURRECTION",
  MISSING_TRANSITION = "MISSING_TRANSITION",
  PACING_ISSUE = "PACING_ISSUE",
}

export enum Severity {
  HIGH = "HIGH",
  MEDIUM = "MEDIUM",
  LOW = "LOW",
}

export interface TimelineEvent {
  id: string;
  manuscript_id: string;
  description: string;
  event_type: EventType;
  order_index: number;
  timestamp: string | null;
  location_id: string | null;
  character_ids: string[];
  event_metadata: {
    auto_generated?: boolean;
    paragraph_index?: number;
    word_count?: number;
    actions?: string[];
    tone?: string;
    emotions?: string[];
    sentiment?: number;
    intensity?: number;
    emotion_scores?: Record<string, number>;
    adjectives?: string[];
    adverbs?: string[];
    has_transition?: boolean;
    location_changed?: boolean;
    character_set_changed?: boolean;
    detected_persons?: string[];
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface TimelineInconsistency {
  id: string;
  manuscript_id: string;
  inconsistency_type: InconsistencyType;
  description: string;
  severity: Severity;
  affected_event_ids: string[];
  extra_data: Record<string, any>;
  created_at: string;
}

export interface CharacterLocation {
  id: string;
  character_id: string;
  event_id: string;
  location_id: string;
  manuscript_id: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineStats {
  total_events: number;
  event_types: Record<string, number>;
  locations_used: number;
  characters_involved: number;
  total_inconsistencies: number;
  inconsistency_severity: Record<Severity, number>;
}

// API Request types
export interface CreateEventRequest {
  manuscript_id: string;
  description: string;
  event_type: EventType;
  order_index?: number;
  timestamp?: string;
  location_id?: string;
  character_ids?: string[];
  metadata?: Record<string, any>;
}

export interface UpdateEventRequest {
  description?: string;
  event_type?: EventType;
  order_index?: number;
  timestamp?: string;
  location_id?: string;
  character_ids?: string[];
  metadata?: Record<string, any>;
}

export interface AnalyzeTimelineRequest {
  manuscript_id: string;
  text: string;
}

// Utility functions
export function getEventTypeColor(type: EventType): string {
  switch (type) {
    case EventType.SCENE:
      return "#6366f1"; // indigo
    case EventType.CHAPTER:
      return "#8b5cf6"; // purple
    case EventType.FLASHBACK:
      return "#f59e0b"; // amber
    case EventType.DREAM:
      return "#ec4899"; // pink
    case EventType.MONTAGE:
      return "#14b8a6"; // teal
    default:
      return "#6b7280"; // gray
  }
}

export function getEventTypeIcon(type: EventType): string {
  switch (type) {
    case EventType.SCENE:
      return "🎬";
    case EventType.CHAPTER:
      return "📖";
    case EventType.FLASHBACK:
      return "⏪";
    case EventType.DREAM:
      return "💭";
    case EventType.MONTAGE:
      return "🎞️";
    default:
      return "📝";
  }
}

export function getSeverityColor(severity: Severity): string {
  switch (severity) {
    case Severity.HIGH:
      return "#dc2626"; // red
    case Severity.MEDIUM:
      return "#f59e0b"; // amber
    case Severity.LOW:
      return "#10b981"; // green
    default:
      return "#6b7280"; // gray
  }
}

export function getSeverityIcon(severity: Severity): string {
  switch (severity) {
    case Severity.HIGH:
      return "🔴";
    case Severity.MEDIUM:
      return "🟡";
    case Severity.LOW:
      return "🟢";
    default:
      return "⚪";
  }
}
