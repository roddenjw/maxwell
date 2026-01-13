/**
 * SceneDetectionPlugin - Detects which scene the cursor is currently in
 * Tracks cursor position relative to SceneBreakNodes and notifies parent component
 * Used to show scene context in BeatContextPanel while writing
 */

import { useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  COMMAND_PRIORITY_LOW,
  SELECTION_CHANGE_COMMAND,
  $getRoot,
  LexicalNode,
  TextNode,
} from 'lexical';
import { $isSceneBreakNode } from '../nodes/SceneBreakNode';

interface SceneDetectionPluginProps {
  chapterId: string;
  onSceneChange: (sceneIndex: number, cursorPosition: number) => void;
}

export default function SceneDetectionPlugin({
  chapterId,
  onSceneChange,
}: SceneDetectionPluginProps): null {
  const [editor] = useLexicalComposerContext();
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSceneIndexRef = useRef<number>(-1);

  useEffect(() => {
    // Register command listener for selection changes (cursor movement)
    const removeListener = editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        // Clear any pending debounce
        if (debounceTimeoutRef.current) {
          clearTimeout(debounceTimeoutRef.current);
        }

        // Debounce by 300ms to avoid excessive API calls during typing
        debounceTimeoutRef.current = setTimeout(() => {
          editor.getEditorState().read(() => {
            const selection = $getSelection();
            if (!$isRangeSelection(selection)) {
              return;
            }

            // Get cursor position
            const anchorNode = selection.anchor.getNode();
            const cursorOffset = selection.anchor.offset;

            // Calculate absolute cursor position in the document
            const cursorPosition = calculateAbsoluteCursorPosition(anchorNode, cursorOffset);

            // Find all SceneBreakNodes and their positions
            const sceneBreakPositions = findSceneBreakPositions();

            // Determine which scene the cursor is in
            let sceneIndex = 0; // Before first scene break = scene 0
            for (let i = 0; i < sceneBreakPositions.length; i++) {
              if (cursorPosition >= sceneBreakPositions[i]) {
                sceneIndex = i + 1;
              }
            }

            // Only notify if scene changed (avoid redundant API calls)
            if (sceneIndex !== lastSceneIndexRef.current) {
              lastSceneIndexRef.current = sceneIndex;
              onSceneChange(sceneIndex, cursorPosition);
            }
          });
        }, 300);

        return false;
      },
      COMMAND_PRIORITY_LOW
    );

    // Cleanup
    return () => {
      removeListener();
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [editor, chapterId, onSceneChange]);

  /**
   * Calculate absolute cursor position in the document
   * @param node - The node containing the cursor
   * @param offset - Cursor offset within the node
   * @returns Absolute character position in the document
   */
  function calculateAbsoluteCursorPosition(
    node: LexicalNode,
    offset: number
  ): number {
    let position = 0;
    let found = false;

    // Walk all text nodes in the document until we find the cursor node
    const root = $getRoot();
    const allNodes = root.getAllTextNodes();

    for (const textNode of allNodes) {
      if (textNode === node) {
        // Found the cursor node - add the offset and stop
        position += offset;
        found = true;
        break;
      }

      // Add this node's text length to position
      const textContent = textNode.getTextContent();
      position += textContent.length;
    }

    // If node wasn't found (shouldn't happen), return 0
    if (!found) {
      console.warn('SceneDetectionPlugin: Cursor node not found in document');
      return 0;
    }

    return position;
  }

  /**
   * Find all SceneBreakNodes and calculate their absolute positions
   * @returns Array of character positions where scene breaks occur
   */
  function findSceneBreakPositions(): number[] {
    const positions: number[] = [];
    let currentPosition = 0;

    const root = $getRoot();
    const children = root.getChildren();

    // Walk through all top-level children
    for (const child of children) {
      // Check if this node is a SceneBreakNode
      if ($isSceneBreakNode(child)) {
        positions.push(currentPosition);
      }

      // Add this node's text length to position
      // (SceneBreakNodes have no text, so they contribute 0)
      const textContent = child.getTextContent();
      currentPosition += textContent.length;

      // Add newline for block nodes (paragraphs, headings, etc.)
      // This matches how Lexical calculates character positions
      if (child.getType() === 'paragraph' || child.getType() === 'heading') {
        currentPosition += 1; // Newline character
      }
    }

    return positions;
  }

  // This plugin doesn't render anything
  return null;
}
