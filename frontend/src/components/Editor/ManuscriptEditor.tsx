/**
 * ManuscriptEditor Component
 * Main Lexical-based rich text editor for manuscripts
 */

import { useEffect, useState, useCallback } from 'react';
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
import BeatContextPanel from './BeatContextPanel';
import OutlineReferenceSidebar from './OutlineReferenceSidebar';
import { SceneBreakNode } from './nodes/SceneBreakNode';
import { EntityMentionNode } from './nodes/EntityMentionNode';
import AutoSavePlugin from './plugins/AutoSavePlugin';
import EntityMentionsPlugin from './plugins/EntityMentionsPlugin';
import RealtimeNLPPlugin from './plugins/RealtimeNLPPlugin';
import FastCoachPlugin from './plugins/FastCoachPlugin';
import SceneDetectionPlugin from './plugins/SceneDetectionPlugin';
import SelectionToolbar from './SelectionToolbar';
import QuickEntityModal from './QuickEntityModal';
import { versioningApi, chaptersApi } from '@/lib/api';
import { useOutlineStore } from '@/stores/outlineStore';

interface ManuscriptEditorProps {
  manuscriptId?: string;
  chapterId?: string;
  initialContent?: string;
  mode?: EditorMode;
  onChange?: (editorState: EditorState) => void;
  onSaveStatusChange?: (status: 'saved' | 'saving' | 'unsaved') => void;
  onViewBeat?: (beatId: string) => void;
}

export default function ManuscriptEditor({
  manuscriptId,
  chapterId,
  initialContent,
  mode = 'normal',
  onChange,
  onSaveStatusChange,
  onViewBeat,
}: ManuscriptEditorProps) {
  const [wordCount, setWordCount] = useState(0);
  const [isFocusMode, setIsFocusMode] = useState(mode === 'focus');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');
  const [latestEditorState, setLatestEditorState] = useState<EditorState | null>(null);
  const [chapterTitle, setChapterTitle] = useState<string>('');
  const [currentSceneContext, setCurrentSceneContext] = useState<any>(null);

  // Quick entity creation state
  const [showQuickEntityModal, setShowQuickEntityModal] = useState(false);
  const [selectedTextForEntity, setSelectedTextForEntity] = useState('');
  const [entityModalPosition, setEntityModalPosition] = useState({ x: 0, y: 0 });

  const {
    getBeatByChapterId,
    toggleBeatContextPanel,
    toggleOutlineReferenceSidebar
  } = useOutlineStore();
  const beat = chapterId ? getBeatByChapterId?.(chapterId) : null;

  // Notify parent of save status changes
  useEffect(() => {
    onSaveStatusChange?.(saveStatus);
  }, [saveStatus, onSaveStatusChange]);

  // Fetch chapter title when chapter changes
  useEffect(() => {
    if (!chapterId) {
      setChapterTitle('');
      return;
    }

    const fetchChapterTitle = async () => {
      try {
        const chapter = await chaptersApi.getChapter(chapterId);
        setChapterTitle(chapter.title);
      } catch (error) {
        console.error('Failed to fetch chapter title:', error);
      }
    };

    fetchChapterTitle();
  }, [chapterId]);

  // Handle creating entity from selected text
  const handleCreateEntityFromSelection = useCallback((selectedText: string, position: { x: number; y: number }) => {
    setSelectedTextForEntity(selectedText);
    setEntityModalPosition(position);
    setShowQuickEntityModal(true);
  }, []);

  // Handle scene changes from SceneDetectionPlugin
  const handleSceneChange = useCallback(async (_sceneIndex: number, cursorPosition: number) => {
    if (!chapterId) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/chapters/${chapterId}/scene-context?cursor_position=${cursorPosition}`
      );
      const data = await response.json();

      if (data.success) {
        setCurrentSceneContext(data.scene);
      }
    } catch (error) {
      console.error('Failed to fetch scene context:', error);
      // Don't show error to user - scene context is optional enhancement
    }
  }, [chapterId]);

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
    // Pass undefined if empty to get a fresh editor
    editorState: initialContent && initialContent.trim() !== '' ? initialContent : undefined,
  };

  // Handle editor state changes
  const handleEditorChange = (editorState: EditorState) => {
    // Store latest state for snapshot creation
    setLatestEditorState(editorState);

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

  // Create manual snapshot
  const createManualSnapshot = async () => {
    if (!manuscriptId) return;

    try {
      const label = prompt('Enter a label for this snapshot:');
      if (!label) return;

      await versioningApi.createSnapshot({
        manuscript_id: manuscriptId,
        trigger_type: 'MANUAL',
        label,
        word_count: wordCount,
      });

      alert('✅ Snapshot created! All chapters have been saved.');
    } catch (error) {
      console.error('Failed to create snapshot:', error);
      alert('Failed to create snapshot: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Create snapshot: Cmd+S (Mac) or Ctrl+S (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        createManualSnapshot();
        return;
      }

      // Toggle beat context panel: Cmd+B or Ctrl+B
      if ((e.metaKey || e.ctrlKey) && e.key === 'b' && !e.shiftKey) {
        e.preventDefault();
        if (beat) {
          toggleBeatContextPanel();
        }
        return;
      }

      // Toggle outline reference sidebar: Cmd+Shift+O or Ctrl+Shift+O
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'o') {
        e.preventDefault();
        toggleOutlineReferenceSidebar();
        return;
      }

      // Focus mode toggle: F11 or Ctrl+Shift+F
      if (e.key === 'F11' || (e.ctrlKey && e.shiftKey && e.key === 'f')) {
        e.preventDefault();
        setIsFocusMode((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [manuscriptId, latestEditorState, wordCount, beat, toggleBeatContextPanel, toggleOutlineReferenceSidebar]);

  return (
    <div className={`editor-container ${isFocusMode ? 'focus-mode' : ''}`}>
      <LexicalComposer initialConfig={initialConfig}>
        <div className="relative">
          {/* Breadcrumb Navigation - shows beat context */}
          {!isFocusMode && beat && chapterTitle && onViewBeat && (
            <div className="sticky top-0 z-10 bg-bronze/5 border-b border-bronze/20 px-4 py-2">
              <div className="flex items-center gap-2 text-sm font-sans">
                <span className="text-faded-ink">Writing:</span>
                <button
                  onClick={() => onViewBeat(beat.id)}
                  className="text-bronze hover:text-bronze-dark font-semibold transition-colors"
                >
                  {beat.beat_label} ({Math.round(beat.target_position_percent * 100)}%)
                </button>
                <span className="text-faded-ink">›</span>
                <span className="text-midnight font-semibold">{chapterTitle}</span>
              </div>
            </div>
          )}

          {/* Toolbar - hidden in focus mode */}
          {!isFocusMode && (
            <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
              <EditorToolbar
                manuscriptId={manuscriptId}
                chapterId={chapterId}
              />
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

            {/* Auto-save plugin - saves to localStorage and creates snapshots */}
            {manuscriptId && (
              <AutoSavePlugin
                manuscriptId={manuscriptId}
                chapterId={chapterId}
                onSaveStatusChange={setSaveStatus}
                enableSnapshots={true}
                snapshotInterval={5}
              />
            )}

            {/* Entity mentions plugin - @mention autocomplete */}
            {manuscriptId && <EntityMentionsPlugin manuscriptId={manuscriptId} />}

            {/* Realtime NLP plugin - live entity detection via WebSocket */}
            {manuscriptId && <RealtimeNLPPlugin manuscriptId={manuscriptId} />}

            {/* Fast Coach plugin - real-time writing suggestions */}
            {manuscriptId && <FastCoachPlugin manuscriptId={manuscriptId} enabled={true} />}

            {/* Scene Detection plugin - tracks which scene cursor is in */}
            {chapterId && (
              <SceneDetectionPlugin
                chapterId={chapterId}
                onSceneChange={handleSceneChange}
              />
            )}

            {/* Selection Toolbar - appears when text is selected, offers "Create Entity" */}
            {manuscriptId && (
              <SelectionToolbar
                manuscriptId={manuscriptId}
                onCreateEntity={handleCreateEntityFromSelection}
              />
            )}

            {/* Quick Entity Modal - for creating entities from selected text */}
            {showQuickEntityModal && manuscriptId && (
              <QuickEntityModal
                manuscriptId={manuscriptId}
                selectedText={selectedTextForEntity}
                position={entityModalPosition}
                onClose={() => setShowQuickEntityModal(false)}
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

          {/* Beat Context Panel - shows current plot beat while writing */}
          {!isFocusMode && manuscriptId && chapterId && (
            <BeatContextPanel
              manuscriptId={manuscriptId}
              chapterId={chapterId}
              onViewBeat={onViewBeat}
              currentSceneContext={currentSceneContext}
            />
          )}

          {/* Outline Reference Sidebar - full outline as reference while writing */}
          {!isFocusMode && manuscriptId && (
            <OutlineReferenceSidebar
              manuscriptId={manuscriptId}
              currentChapterId={chapterId}
              onViewBeat={onViewBeat}
            />
          )}
        </div>
      </LexicalComposer>
    </div>
  );
}
