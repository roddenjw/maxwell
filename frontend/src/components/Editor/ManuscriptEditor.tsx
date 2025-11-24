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
import AutoSavePlugin from './plugins/AutoSavePlugin';

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
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');

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
    // Load saved content if available (JSON string)
    editorState: initialContent || undefined,
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
          <div className="editor-wrapper relative">
            <RichTextPlugin
              contentEditable={
                <ContentEditable
                  className={`
                    editor-content
                    ${isFocusMode ? 'focus-mode-content' : ''}
                    min-h-screen p-8 pt-20
                    prose prose-lg max-w-4xl mx-auto
                    focus:outline-none
                  `}
                  aria-label="Manuscript editor"
                />
              }
              placeholder={
                <div className="editor-placeholder pointer-events-none">
                  <div className="max-w-4xl mx-auto px-8 pt-20">
                    <p className="text-2xl text-faded-ink font-serif mb-3">
                      Click here to begin writing...
                    </p>
                    <p className="text-sm text-faded-ink font-sans">
                      Your work is automatically saved every 5 seconds
                    </p>
                  </div>
                </div>
              }
              ErrorBoundary={LexicalErrorBoundary}
            />

            {/* History plugin for undo/redo */}
            <HistoryPlugin />

            {/* OnChange plugin to track content changes */}
            <OnChangePlugin onChange={handleEditorChange} />

            {/* Auto-save plugin - saves to localStorage */}
            {manuscriptId && (
              <AutoSavePlugin
                manuscriptId={manuscriptId}
                onSaveStatusChange={setSaveStatus}
              />
            )}
          </div>

          {/* Status indicators - Maxwell Style */}
          {!isFocusMode && (
            <div className="fixed bottom-4 right-4 flex flex-col gap-2 items-end">
              {/* Save status indicator */}
              <div className="bg-white border border-slate-ui px-4 py-2 shadow-book" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 text-sm font-sans">
                  {saveStatus === 'saved' && (
                    <>
                      <span className="text-bronze">✓</span>
                      <span className="text-faded-ink">All changes saved</span>
                    </>
                  )}
                  {saveStatus === 'saving' && (
                    <>
                      <span className="text-bronze animate-pulse">●</span>
                      <span className="text-faded-ink">Saving...</span>
                    </>
                  )}
                  {saveStatus === 'unsaved' && (
                    <>
                      <span className="text-faded-ink">●</span>
                      <span className="text-faded-ink">Unsaved changes</span>
                    </>
                  )}
                </div>
              </div>

              {/* Word count indicator */}
              <div className="bg-white border border-slate-ui px-4 py-2 shadow-book" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 text-sm font-sans">
                  <span className="text-faded-ink">Words:</span>
                  <span className="font-semibold text-midnight">
                    {wordCount.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Focus mode indicator */}
          {isFocusMode && (
            <div className="fixed top-4 right-4 text-sm text-faded-ink font-sans">
              Press F11 to exit focus mode
            </div>
          )}
        </div>
      </LexicalComposer>
    </div>
  );
}
