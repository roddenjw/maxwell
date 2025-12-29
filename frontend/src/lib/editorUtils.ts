/**
 * Editor utility functions for text navigation and highlighting
 */

import { LexicalEditor } from 'lexical';
import { $getRoot, $setSelection, $createRangeSelection, TextNode } from 'lexical';

/**
 * Jump to and select text at a specific character offset in the editor
 * @param editor - Lexical editor instance
 * @param startOffset - Start character position (0-indexed)
 * @param endOffset - End character position (0-indexed)
 */
export function jumpToTextPosition(
  editor: LexicalEditor,
  startOffset: number,
  endOffset: number
): void {
  editor.update(() => {
    const root = $getRoot();

    // Find the node and offset corresponding to the character positions
    const { node: startNode, offset: startNodeOffset } = findNodeAtOffset(root, startOffset);
    const { node: endNode, offset: endNodeOffset } = findNodeAtOffset(root, endOffset);

    if (!startNode || !endNode) {
      console.warn('Could not find text nodes at specified positions');
      return;
    }

    // Create a range selection
    const selection = $createRangeSelection();
    selection.anchor.set(startNode.getKey(), startNodeOffset, 'text');
    selection.focus.set(endNode.getKey(), endNodeOffset, 'text');
    $setSelection(selection);

    // Scroll the selection into view
    setTimeout(() => {
      const domSelection = window.getSelection();
      if (domSelection && domSelection.rangeCount > 0) {
        const range = domSelection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Scroll to the selection with some padding
        window.scrollTo({
          top: window.scrollY + rect.top - window.innerHeight / 3,
          behavior: 'smooth'
        });
      }
    }, 10);
  });
}

/**
 * Find the Lexical node and local offset corresponding to a global character offset
 * @param root - Root node to search from
 * @param targetOffset - Character offset in the plain text representation
 * @returns The text node and local offset within that node
 */
function findNodeAtOffset(root: any, targetOffset: number): { node: TextNode | null; offset: number } {
  let currentOffset = 0;
  let foundNode: TextNode | null = null;
  let foundOffset = 0;

  // Recursive function to walk the tree
  function walkNodes(node: any): boolean {
    if (!node) return false;

    // If it's a text node
    if (node.getType && node.getType() === 'text') {
      const textContent = node.getTextContent();
      const nodeLength = textContent.length;

      // Check if our target offset falls within this node
      if (currentOffset + nodeLength >= targetOffset) {
        foundNode = node;
        foundOffset = targetOffset - currentOffset;
        return true; // Found it!
      }

      currentOffset += nodeLength;
    }
    // Handle paragraph nodes - they add newlines
    else if (node.getType && node.getType() === 'paragraph') {
      // Process children first
      const children = node.getChildren();
      for (const child of children) {
        if (walkNodes(child)) return true;
      }

      // Paragraph adds a newline after its content
      currentOffset += 1;
    }
    // Handle other container nodes
    else if (node.getChildren) {
      const children = node.getChildren();
      for (const child of children) {
        if (walkNodes(child)) return true;
      }
    }

    return false;
  }

  walkNodes(root);

  return { node: foundNode, offset: foundOffset };
}

/**
 * Replace text at a specific character range in the editor
 * @param editor - Lexical editor instance
 * @param startOffset - Start character position (0-indexed)
 * @param endOffset - End character position (0-indexed)
 * @param replacementText - Text to insert (empty string to delete)
 */
export function replaceTextAtPosition(
  editor: LexicalEditor,
  startOffset: number,
  endOffset: number,
  replacementText: string
): void {
  editor.update(() => {
    const root = $getRoot();

    // Find the node and offset corresponding to the character positions
    const { node: startNode, offset: startNodeOffset } = findNodeAtOffset(root, startOffset);
    const { node: endNode, offset: endNodeOffset } = findNodeAtOffset(root, endOffset);

    if (!startNode || !endNode) {
      console.warn('Could not find text nodes at specified positions');
      return;
    }

    // Create a range selection
    const selection = $createRangeSelection();
    selection.anchor.set(startNode.getKey(), startNodeOffset, 'text');
    selection.focus.set(endNode.getKey(), endNodeOffset, 'text');
    $setSelection(selection);

    // Insert the replacement text (or delete if empty)
    selection.insertText(replacementText);
  });
}

/**
 * Get the current editor's plain text content
 * This extracts text the EXACT same way findNodeAtOffset walks the tree
 * to ensure position consistency between backend analysis and frontend navigation
 */
export function getEditorPlainText(editor: LexicalEditor): string {
  let text = '';
  try {
    editor.getEditorState().read(() => {
      const root = $getRoot();
      if (root) {
        text = extractTextFromNode(root);
      }
    });
  } catch (error) {
    console.warn('Error extracting editor text:', error);
    return '';
  }
  return text;
}

/**
 * Extract text from a node in the same way findNodeAtOffset walks it
 * This ensures position consistency
 */
function extractTextFromNode(node: any): string {
  if (!node) return '';

  let text = '';

  try {
    // If it's a text node
    if (node.getType && node.getType() === 'text') {
      return node.getTextContent() || '';
    }
    // Handle paragraph nodes - they add newlines
    else if (node.getType && node.getType() === 'paragraph') {
      // Process children first
      const children = node.getChildren?.() || [];
      for (const child of children) {
        text += extractTextFromNode(child);
      }

      // Paragraph adds a newline after its content
      text += '\n';
    }
    // Handle other container nodes
    else if (node.getChildren) {
      const children = node.getChildren() || [];
      for (const child of children) {
        text += extractTextFromNode(child);
      }
    }
  } catch (error) {
    console.warn('Error in extractTextFromNode:', error);
    return '';
  }

  return text;
}
