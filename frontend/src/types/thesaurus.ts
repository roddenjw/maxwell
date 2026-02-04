/**
 * TypeScript types for the Thesaurus feature
 */

export interface SynonymGroup {
  part_of_speech: string;
  definition: string;
  words: string[];
}

export interface SynonymsResponse {
  word: string;
  found: boolean;
  groups: SynonymGroup[];
  antonyms: string[];
  fallback?: boolean;
  error?: string;
}

export interface RelatedWordsResponse {
  word: string;
  found: boolean;
  definition?: string;
  broader_terms: string[];
  narrower_terms: string[];
  parts: string[];
  part_of: string[];
  error?: string;
}
