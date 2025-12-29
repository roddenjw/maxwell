import { useState, useEffect } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'
import ManuscriptLibrary from './components/ManuscriptLibrary'
import { TimeMachine } from './components/TimeMachine'
import { CodexSidebar } from './components/Codex'
import TimelineSidebar from './components/Timeline/TimelineSidebar'
import DocumentNavigator from './components/Document/DocumentNavigator'
import FastCoachSidebar from './components/FastCoach/FastCoachSidebar'
import UnifiedSidebar from './components/Navigation/UnifiedSidebar'
import ToastContainer from './components/common/ToastContainer'
import KeyboardShortcutsModal from './components/common/KeyboardShortcutsModal'
import AnalyticsDashboard from './components/Analytics/AnalyticsDashboard'
import ExportModal from './components/Export/ExportModal'
import { useManuscriptStore } from './stores/manuscriptStore'
import { useCodexStore } from './stores/codexStore'
import { useTimelineStore } from './stores/timelineStore'
import { useChapterStore } from './stores/chapterStore'
import { useFastCoachStore } from './stores/fastCoachStore'
import { chaptersApi } from './lib/api'
import { useKeyboardShortcuts, type KeyboardShortcut } from './hooks/useKeyboardShortcuts'
import { toast } from './stores/toastStore'
import { getErrorMessage } from './lib/retry'
import { useUnsavedChanges } from './hooks/useUnsavedChanges'
import RecapModal from './components/RecapModal'

function App() {
  const { currentManuscriptId, setCurrentManuscript, getCurrentManuscript } = useManuscriptStore()
  const currentManuscript = getCurrentManuscript()
  const { isSidebarOpen, toggleSidebar } = useCodexStore()
  const { isTimelineOpen, setTimelineOpen } = useTimelineStore()
  const { setCurrentChapter, currentChapterId } = useChapterStore()
  const { isSidebarOpen: isCoachOpen, toggleSidebar: toggleCoach } = useFastCoachStore()
  const [activeView, setActiveView] = useState<'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'recap' | 'analytics' | 'export'>('chapters')
  const [editorKey, setEditorKey] = useState(0) // Force editor re-mount on restore
  const [currentChapterContent, setCurrentChapterContent] = useState<string>('')
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved')

  // Track unsaved changes and warn before closing
  const { checkNavigateAway } = useUnsavedChanges(saveStatus === 'unsaved' || saveStatus === 'saving')

  const handleOpenManuscript = async (manuscriptId: string) => {
    setCurrentManuscript(manuscriptId)

    // Auto-select first chapter if available
    try {
      const response = await fetch(`http://localhost:8000/api/chapters/manuscript/${manuscriptId}/tree`)
      const data = await response.json()

      if (data.success && data.data.length > 0) {
        // Find first non-folder chapter
        const findFirstChapter = (nodes: any[]): any => {
          for (const node of nodes) {
            if (!node.is_folder) {
              return node
            }
            if (node.children && node.children.length > 0) {
              const found = findFirstChapter(node.children)
              if (found) return found
            }
          }
          return null
        }

        const firstChapter = findFirstChapter(data.data)
        if (firstChapter) {
          // Use setTimeout to ensure manuscript state is set first
          setTimeout(() => {
            handleChapterSelect(firstChapter.id)
          }, 100)
        }
      }
    } catch (error) {
      console.error('Failed to load chapters:', error)
    }
  }

  const handleCloseEditor = () => {
    if (!checkNavigateAway()) {
      return
    }
    setCurrentManuscript(null)
    setCurrentChapter(null) // Clear chapter selection
    setSaveStatus('saved') // Reset save status
    setActiveView('chapters') // Reset view
  }

  const handleNavigate = (view: 'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'recap' | 'analytics' | 'export') => {
    setActiveView(view)

    // Handle view-specific state updates
    if (view === 'chapters') {
      // No additional state needed
    } else if (view === 'codex') {
      if (!isSidebarOpen) toggleSidebar()
    } else if (view === 'timeline') {
      if (!isTimelineOpen) setTimelineOpen(true)
    } else if (view === 'timemachine') {
      // Time machine is a modal, handled separately
    } else if (view === 'coach') {
      if (!isCoachOpen) toggleCoach()
    }
  }

  const handleRestoreSnapshot = async (snapshotId: string) => {
    if (!currentManuscriptId) {
      alert('No manuscript selected')
      return
    }

    try {
      // Call the restore API - it now restores ALL chapters
      const response = await fetch('http://localhost:8000/api/versioning/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manuscript_id: currentManuscriptId,
          snapshot_id: snapshotId,
          create_backup: true
        })
      })

      if (!response.ok) {
        throw new Error('Failed to restore snapshot')
      }

      const result = await response.json()
      const data = result.data

      console.log('Snapshot restored:', data)

      setActiveView('chapters')

      // Show success message with restoration details
      if (data.legacy_format) {
        toast.success('Snapshot restored (legacy format)')
      } else {
        toast.success(
          `Restored ${data.chapters_restored} chapter${data.chapters_restored !== 1 ? 's' : ''}` +
          (data.chapters_deleted > 0 ? ` (${data.chapters_deleted} deleted)` : '')
        )
      }

      // Reload the current chapter if one is selected
      if (currentChapterId) {
        try {
          const chapter = await chaptersApi.getChapter(currentChapterId)

          const hasLexicalState = chapter.lexical_state && chapter.lexical_state.trim() !== ''
          const hasPlainContent = chapter.content && chapter.content.trim() !== ''

          let editorContent: string | undefined

          if (hasLexicalState) {
            editorContent = chapter.lexical_state
          } else if (hasPlainContent) {
            editorContent = convertPlainTextToLexical(chapter.content)
          }

          setCurrentChapterContent(editorContent || '')
          setEditorKey(prev => prev + 1)
          setSaveStatus('saved')
        } catch (error) {
          console.error('Failed to reload chapter after restore:', error)
          // Chapter might have been deleted, clear selection
          setCurrentChapter(null)
        }
      }

    } catch (error) {
      console.error('Failed to restore snapshot:', error)
      toast.error('Failed to restore snapshot: ' + getErrorMessage(error))
    }
  }

  // Convert plain text to Lexical editor state format
  const convertPlainTextToLexical = (plainText: string): string => {
    // Split text into paragraphs
    const paragraphs = plainText.split('\n').filter(line => line.trim() !== '')

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
    }))

    // Create root Lexical state
    const lexicalState = {
      root: {
        children: children,
        direction: 'ltr',
        format: '',
        indent: 0,
        type: 'root',
        version: 1
      }
    }

    return JSON.stringify(lexicalState)
  }

  const handleChapterSelect = async (chapterId: string) => {
    // Check for unsaved changes before switching chapters
    if (!checkNavigateAway()) {
      return
    }

    try {
      setCurrentChapter(chapterId)

      // Fetch chapter content
      const chapter = await chaptersApi.getChapter(chapterId)

      // Data integrity check: Log chapter content status
      const hasLexicalState = chapter.lexical_state && chapter.lexical_state.trim() !== ''
      const hasPlainContent = chapter.content && chapter.content.trim() !== ''

      console.log(`Chapter ${chapterId} content status:`, {
        hasLexicalState,
        hasPlainContent,
        lexicalStateLength: chapter.lexical_state?.length || 0,
        plainContentLength: chapter.content?.length || 0,
        wordCount: chapter.word_count || 0
      })

      // Determine editor content to load
      let editorContent: string | undefined

      if (hasLexicalState) {
        // Use Lexical state if available
        editorContent = chapter.lexical_state
        console.log('Loaded Lexical state for chapter:', chapterId)
      } else if (hasPlainContent) {
        // Fallback: Convert plain text content to Lexical format
        console.warn('Lexical state missing - converting plain text to Lexical format for chapter:', chapterId)
        editorContent = convertPlainTextToLexical(chapter.content)
        toast.info('Chapter content recovered from plain text backup')
      } else {
        // No content - start with blank editor
        console.warn('Chapter has no content:', chapterId)
        editorContent = undefined

        // Only show warning if word_count suggests there should be content
        if (chapter.word_count && chapter.word_count > 0) {
          console.error('DATA INTEGRITY ISSUE: Chapter reports word count but has no content!', {
            chapterId,
            wordCount: chapter.word_count
          })
          toast.error('Warning: Chapter data may be incomplete (word count mismatch)')
        }
      }

      setCurrentChapterContent(editorContent || '')

      // Force editor re-mount with new content
      setEditorKey(prev => prev + 1)
      setSaveStatus('saved') // Reset save status for new chapter
    } catch (error) {
      console.error('Failed to load chapter:', error)
      toast.error(getErrorMessage(error))
    }
  }

  // Reload chapter content when switching to views that show the editor
  // This ensures the editor always has the latest saved content
  useEffect(() => {
    const viewsWithEditor = ['chapters', 'codex', 'coach'];

    // Only reload if:
    // 1. We're switching to a view that shows the editor
    // 2. There's a current chapter selected
    // 3. We're not already in a saving state (to avoid conflicts)
    if (viewsWithEditor.includes(activeView) && currentChapterId && saveStatus !== 'saving') {
      // Reload the chapter content from the database
      const reloadChapterContent = async () => {
        try {
          const chapter = await chaptersApi.getChapter(currentChapterId);

          const hasLexicalState = chapter.lexical_state && chapter.lexical_state.trim() !== '';
          const hasPlainContent = chapter.content && chapter.content.trim() !== '';

          let editorContent: string | undefined;

          if (hasLexicalState) {
            editorContent = chapter.lexical_state;
          } else if (hasPlainContent) {
            editorContent = convertPlainTextToLexical(chapter.content);
          }

          // Only update if content has actually changed to avoid unnecessary re-renders
          if (editorContent !== currentChapterContent) {
            setCurrentChapterContent(editorContent || '');
            setEditorKey(prev => prev + 1); // Force editor remount with new content
          }
        } catch (error) {
          console.error('Failed to reload chapter content:', error);
        }
      };

      reloadChapterContent();
    }
  }, [activeView]); // Only run when activeView changes

  // Define keyboard shortcuts
  const shortcuts: KeyboardShortcut[] = [
    {
      key: '/',
      ctrl: true,
      description: 'Show keyboard shortcuts',
      handler: () => setShowKeyboardShortcuts(true),
    },
    {
      key: 'b',
      ctrl: true,
      description: 'Navigate to Codex',
      handler: () => handleNavigate('codex'),
    },
    {
      key: 't',
      ctrl: true,
      description: 'Navigate to Timeline',
      handler: () => handleNavigate('timeline'),
    },
    {
      key: 'd',
      ctrl: true,
      description: 'Navigate to Chapters',
      handler: () => handleNavigate('chapters'),
    },
    {
      key: 'h',
      ctrl: true,
      description: 'Navigate to Time Machine',
      handler: () => handleNavigate('timemachine'),
    },
    {
      key: 'Escape',
      description: 'Return to chapters view',
      handler: () => {
        setActiveView('chapters');
        setShowKeyboardShortcuts(false);
      },
    },
  ];

  // Enable keyboard shortcuts when editing manuscript
  useKeyboardShortcuts(shortcuts, !!currentManuscriptId)

  // Show editor when a manuscript is selected
  if (currentManuscriptId && currentManuscript) {
    return (
      <div className="min-h-screen bg-vellum text-midnight flex">
        {/* Unified Left Sidebar Navigation */}
        <UnifiedSidebar
          currentManuscriptId={currentManuscriptId}
          manuscriptTitle={currentManuscript.title}
          onNavigate={handleNavigate}
          onCloseEditor={handleCloseEditor}
          activeView={activeView}
        />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Minimal Header */}
          <header className="border-b border-slate-ui bg-white px-6 py-3 flex-shrink-0">
            <div className="flex items-center justify-end gap-4">
              {/* Save status indicator */}
              <span className="text-xs font-sans text-faded-ink">
                {saveStatus === 'saved' && '✓ Saved'}
                {saveStatus === 'saving' && '⋯ Saving...'}
                {saveStatus === 'unsaved' && '• Unsaved changes'}
              </span>
            </div>
          </header>

          {/* Content based on active view */}
          <div className="flex-1 flex overflow-hidden">
            {/* Chapters View */}
            {activeView === 'chapters' && (
              <>
                <div className="w-64 flex-shrink-0">
                  <DocumentNavigator
                    manuscriptId={currentManuscript.id}
                    onChapterSelect={handleChapterSelect}
                  />
                </div>
                <div className="flex-1 overflow-auto">
                  {currentChapterId ? (
                    <ManuscriptEditor
                      key={editorKey}
                      manuscriptId={currentManuscript.id}
                      chapterId={currentChapterId}
                      initialContent={currentChapterContent}
                      mode="normal"
                      onSaveStatusChange={setSaveStatus}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full bg-vellum">
                      <div className="text-center max-w-md p-8">
                        <h2 className="font-garamond text-3xl font-semibold text-midnight mb-4">
                          {currentManuscript.title}
                        </h2>
                        <p className="font-sans text-faded-ink mb-6">
                          Select a chapter from the navigator to start writing, or create a new chapter.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Codex View */}
            {activeView === 'codex' && (
              <>
                {currentChapterId && (
                  <div className="flex-1 overflow-auto">
                    <ManuscriptEditor
                      key={editorKey}
                      manuscriptId={currentManuscript.id}
                      chapterId={currentChapterId}
                      initialContent={currentChapterContent}
                      mode="normal"
                      onSaveStatusChange={setSaveStatus}
                    />
                  </div>
                )}
                <CodexSidebar
                  manuscriptId={currentManuscript.id}
                  isOpen={true}
                  onToggle={() => setActiveView('chapters')}
                />
              </>
            )}

            {/* Timeline View */}
            {activeView === 'timeline' && (
              <div className="flex-1 flex">
                <TimelineSidebar
                  manuscriptId={currentManuscript.id}
                  isOpen={true}
                  onToggle={() => setActiveView('chapters')}
                />
              </div>
            )}

            {/* Coach View */}
            {activeView === 'coach' && (
              <>
                {currentChapterId && (
                  <div className="flex-1 overflow-auto">
                    <ManuscriptEditor
                      key={editorKey}
                      manuscriptId={currentManuscript.id}
                      chapterId={currentChapterId}
                      initialContent={currentChapterContent}
                      mode="normal"
                      onSaveStatusChange={setSaveStatus}
                    />
                  </div>
                )}
                <FastCoachSidebar
                  manuscriptId={currentManuscript.id}
                  isOpen={true}
                  onToggle={() => setActiveView('chapters')}
                />
              </>
            )}

            {/* Time Machine View (Modal) */}
            {activeView === 'timemachine' && (
              <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                <div className="bg-vellum rounded-lg shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
                  <TimeMachine
                    manuscriptId={currentManuscript.id}
                    currentContent={currentChapterContent}
                    onRestore={handleRestoreSnapshot}
                    onClose={() => setActiveView('chapters')}
                  />
                </div>
              </div>
            )}

            {/* Analytics View */}
            {activeView === 'analytics' && (
              <div className="flex-1 overflow-auto">
                <AnalyticsDashboard manuscriptId={currentManuscript.id} />
              </div>
            )}

            {/* Export View (Modal) */}
            {activeView === 'export' && (
              <ExportModal
                manuscriptId={currentManuscript.id}
                onClose={() => setActiveView('chapters')}
              />
            )}

            {/* Recap View (Modal) */}
            {activeView === 'recap' && (
              <RecapModal
                manuscriptId={currentManuscript.id}
                onClose={() => setActiveView('chapters')}
              />
            )}
          </div>
        </main>

        {/* Keyboard Shortcuts Modal */}
        {showKeyboardShortcuts && (
          <KeyboardShortcutsModal
            shortcuts={shortcuts}
            onClose={() => setShowKeyboardShortcuts(false)}
          />
        )}

        {/* Toast Notifications */}
        <ToastContainer />
      </div>
    )
  }

  // Show manuscript library by default
  return (
    <>
      <ManuscriptLibrary onOpenManuscript={handleOpenManuscript} />
      <ToastContainer />
    </>
  )
}

export default App
