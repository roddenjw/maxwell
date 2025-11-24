/**
 * TypeScript types for Lexical editor and manuscripts
 */

export interface Manuscript {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  word_count: number;
  active_variant_id?: string;
  lexical_state: string; // JSON serialized Lexical editor state
}

export interface Scene {
  id: string;
  manuscript_id: string;
  position: number;
  pov_character_id?: string;
  setting_id?: string;
  time_of_day?: string;
  beat_type?: string;
  word_count: number;
  completion_status: 'DRAFT' | 'REVISION' | 'FINAL';
  content: string; // Lexical serialized state
  created_at: string;
  updated_at: string;
}

export interface EditorTheme {
  ltr: string;
  rtl: string;
  paragraph: string;
  heading: {
    h1: string;
    h2: string;
    h3: string;
    h4: string;
    h5: string;
    h6: string;
  };
  text: {
    bold: string;
    italic: string;
    underline: string;
    strikethrough: string;
    code: string;
  };
  list: {
    ul: string;
    ol: string;
    listitem: string;
  };
  quote: string;
  link: string;
}

export type EditorMode = 'focus' | 'architect' | 'normal';

export interface EditorConfig {
  mode: EditorMode;
  showWordCount: boolean;
  autoSave: boolean;
  autoSaveDelay: number; // milliseconds
}
