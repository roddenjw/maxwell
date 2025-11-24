/**
 * ManuscriptEditor Component
 * Main Lexical-based rich text editor for manuscripts
 */

import { useEffect, useState } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import LexicalErrorBoundary from '@lexical/react/LexicalErrorBoundary';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import { EditorState } from 'lexical';

import editorTheme from '@/lib/editorTheme';
import type { EditorMode } from '@/types/editor';
import EditorToolbar from './EditorToolbar';
import { SceneBreakNode } from './nodes/SceneBreakNode';
import { EntityMentionNode } from './nodes/EntityMentionNode';

interface ManuscriptEditorProps {
  manuscriptId?: string;
  initialContent?: string;
  mode?: EditorMode;
  onChange?: (editorState: EditorState) => void;
}

export default function ManuscriptEditor({
  manuscriptId,
  initialContent,
  mode = 'normal',
  onChange,
}: ManuscriptEditorProps) {
  const [wordCount, setWordCount] = useState(0);
  const [isFocusMode, setIsFocusMode] = useState(mode === 'focus');

  // Configure Lexical editor
  const initialConfig = {
    namespace: 'CodexEditor',
    theme: editorTheme,
    onError: (error: Error) => {
      console.error('Lexical Editor Error:', error);
    },
    nodes: [
      HeadingNode,
      QuoteNode,
      ListNode,
      ListItemNode,
      LinkNode,
      SceneBreakNode,
      EntityMentionNode,
    ],
    editorState: initialContent,
  };

  // Handle editor state changes
  const handleEditorChange = (editorState: EditorState) => {
    // Calculate word count
    editorState.read(() => {
      const text = editorState.read(() => {
        const root = editorState._nodeMap;
        let allText = '';
        root.forEach((node) => {
          if ('__text' in node) {
            allText += node.__text + ' ';
          }
        });
        return allText;
      });

      const words = text.trim().split(/\s+/).filter((word) => word.length > 0);
      setWordCount(words.length);
    });

    // Call parent onChange if provided
    onChange?.(editorState);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus mode toggle: F11 or Ctrl+Shift+F
      if (e.key === 'F11' || (e.ctrlKey && e.shiftKey && e.key === 'f')) {
        e.preventDefault();
        setIsFocusMode((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className={`editor-container ${isFocusMode ? 'focus-mode' : ''}`}>
      <LexicalComposer initialConfig={initialConfig}>
        <div className="relative">
          {/* Toolbar - hidden in focus mode */}
          {!isFocusMode && (
            <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
              <EditorToolbar />
            </div>
          )}

          {/* Main editor area */}
          <div className="editor-wrapper">
            <RichTextPlugin
              contentEditable={
                <ContentEditable
                  className={`
                    editor-content
                    ${isFocusMode ? 'focus-mode-content' : ''}
                    min-h-screen p-8
                    prose prose-lg dark:prose-invert max-w-4xl mx-auto
                    focus:outline-none
                  `}
                  aria-label="Manuscript editor"
                />
              }
              placeholder={
                <div className="editor-placeholder absolute top-8 left-8 text-gray-400 dark:text-gray-600 pointer-events-none">
                  Start writing your story...
                </div>
              }
              ErrorBoundary={LexicalErrorBoundary}
            />

            {/* History plugin for undo/redo */}
            <HistoryPlugin />

            {/* OnChange plugin to track content changes */}
            <OnChangePlugin onChange={handleEditorChange} />

            {/* Auto-save plugin will be added here */}
            {/* <AutoSavePlugin manuscriptId={manuscriptId} /> */}
          </div>

          {/* Word count indicator - hidden in focus mode */}
          {!isFocusMode && (
            <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2 shadow-lg">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500 dark:text-gray-400">Words:</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {wordCount.toLocaleString()}
                </span>
              </div>
            </div>
          )}

          {/* Focus mode indicator */}
          {isFocusMode && (
            <div className="fixed top-4 right-4 text-sm text-gray-400 dark:text-gray-600">
              Press F11 to exit focus mode
            </div>
          )}
        </div>
      </LexicalComposer>
    </div>
  );
}
