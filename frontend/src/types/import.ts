/**
 * Import Types
 * Types for manuscript import functionality
 */

/**
 * Information about a supported import format
 */
export interface SupportedFormat {
  extension: string;
  name: string;
  description: string;
  formatting_support: 'full' | 'partial' | 'none';
  warning?: string;
}

/**
 * Preview of a detected chapter during import
 */
export interface ImportChapterPreview {
  index: number;
  title: string;
  word_count: number;
  preview_text: string;
  included: boolean;
}

/**
 * Result of parsing a document for import
 */
export interface ImportPreview {
  parse_id: string;
  title: string;
  author: string | null;
  total_words: number;
  detection_method: string;
  format_warnings: string[];
  chapters: ImportChapterPreview[];
  source_format: string;
}

/**
 * Request to create a manuscript from an import
 */
export interface ImportCreateRequest {
  parse_id: string;
  title?: string;
  author?: string;
  description?: string;
  chapter_adjustments?: ChapterAdjustment[];
  series_id?: string;
}

/**
 * Adjustment to a chapter during import
 */
export interface ChapterAdjustment {
  index: number;
  title?: string;
  included: boolean;
}

/**
 * Response from creating a manuscript via import
 */
export interface ImportCreateResponse {
  success: boolean;
  manuscript_id: string;
  title: string;
  chapter_count: number;
  total_words: number;
}

/**
 * Detection modes for chapter splitting
 */
export type DetectionMode = 'auto' | 'headings' | 'pattern' | 'page_breaks' | 'single';

/**
 * Detection mode display information
 */
export interface DetectionModeInfo {
  value: DetectionMode;
  label: string;
  description: string;
}

/**
 * Available detection modes with descriptions
 */
export const DETECTION_MODES: DetectionModeInfo[] = [
  {
    value: 'auto',
    label: 'Auto-detect',
    description: 'Automatically detect chapters using headings, patterns, or page breaks',
  },
  {
    value: 'headings',
    label: 'By Headings',
    description: 'Split on H1/H2 heading styles in the document',
  },
  {
    value: 'pattern',
    label: 'By Pattern',
    description: 'Split on "Chapter 1", "CHAPTER ONE", "Part I" patterns',
  },
  {
    value: 'page_breaks',
    label: 'By Page Breaks',
    description: 'Split on explicit page breaks in the document',
  },
  {
    value: 'single',
    label: 'Single Chapter',
    description: 'Import entire document as one chapter',
  },
];
