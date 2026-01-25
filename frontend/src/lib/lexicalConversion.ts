/**
 * Lexical Editor Conversion Utilities
 * Shared utilities for converting between Lexical editor JSON and other formats.
 */

export interface LexicalTextNode {
  detail: number;
  format: number;
  mode: string;
  style: string;
  text: string;
  type: 'text';
  version: number;
}

export interface LexicalParagraphNode {
  children: LexicalTextNode[];
  direction: string;
  format: string;
  indent: number;
  type: 'paragraph' | 'heading';
  tag?: string;
  version: number;
}

export interface LexicalRootNode {
  children: LexicalParagraphNode[];
  direction: string;
  format: string;
  indent: number;
  type: 'root';
  version: number;
}

export interface LexicalEditorState {
  root: LexicalRootNode;
}

/**
 * Convert plain text to Lexical editor state format.
 *
 * @param plainText - Plain text string, with paragraphs separated by newlines
 * @returns JSON string representing Lexical editor state
 */
export function convertPlainTextToLexical(plainText: string): string {
  // Split text into paragraphs, preserving structure
  const paragraphs = plainText.split('\n').filter(line => line.trim() !== '');

  // Create Lexical nodes for each paragraph
  const children = paragraphs.map(text => ({
    children: [
      {
        detail: 0,
        format: 0,
        mode: 'normal',
        style: '',
        text: text,
        type: 'text',
        version: 1
      }
    ],
    direction: 'ltr',
    format: '',
    indent: 0,
    type: 'paragraph',
    version: 1
  }));

  // Create root Lexical state
  const lexicalState: LexicalEditorState = {
    root: {
      children: children as LexicalParagraphNode[],
      direction: 'ltr',
      format: '',
      indent: 0,
      type: 'root',
      version: 1
    }
  };

  return JSON.stringify(lexicalState);
}

/**
 * Extract plain text from Lexical editor state JSON.
 *
 * @param lexicalStateStr - JSON string containing Lexical editor state
 * @returns Plain text extracted from the editor state
 */
export function extractTextFromLexical(lexicalStateStr: string): string {
  try {
    if (!lexicalStateStr || lexicalStateStr.trim() === '') {
      return '';
    }

    const state = JSON.parse(lexicalStateStr) as LexicalEditorState;

    function walkNodes(node: unknown): string {
      const textParts: string[] = [];

      if (typeof node === 'object' && node !== null) {
        const typedNode = node as Record<string, unknown>;

        // Direct text content
        if (typedNode.type === 'text' && 'text' in typedNode) {
          textParts.push(String(typedNode.text));
        }

        // Process children
        if ('children' in typedNode && Array.isArray(typedNode.children)) {
          for (const child of typedNode.children) {
            textParts.push(walkNodes(child));
          }

          // Add newline after paragraph
          if (typedNode.type === 'paragraph') {
            textParts.push('\n');
          }
        }
      }

      return textParts.join('');
    }

    // Start from root
    const root = state.root || {};
    const text = walkNodes(root);

    // Clean up extra newlines
    return text.trim();
  } catch (e) {
    console.warn('Failed to extract text from lexical state:', e);
    return '';
  }
}

/**
 * Check if a string is valid Lexical editor state JSON.
 *
 * @param content - String to check
 * @returns true if the string appears to be valid Lexical state
 */
export function isLexicalState(content: string): boolean {
  if (!content || content.trim() === '') {
    return false;
  }

  try {
    const parsed = JSON.parse(content);
    return parsed && typeof parsed === 'object' && 'root' in parsed;
  } catch {
    return false;
  }
}

/**
 * Create an empty Lexical editor state.
 *
 * @returns JSON string representing empty Lexical editor state
 */
export function createEmptyLexicalState(): string {
  const state: LexicalEditorState = {
    root: {
      children: [],
      direction: 'ltr',
      format: '',
      indent: 0,
      type: 'root',
      version: 1
    }
  };
  return JSON.stringify(state);
}
