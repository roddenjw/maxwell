import { useState } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'
import ManuscriptLibrary from './components/ManuscriptLibrary'
import { TimeMachine } from './components/TimeMachine'
import { CodexSidebar } from './components/Codex'
import TimelineSidebar from './components/Timeline/TimelineSidebar'
import DocumentNavigator from './components/Document/DocumentNavigator'
import FastCoachSidebar from './components/FastCoach/FastCoachSidebar'
import ToastContainer from './components/common/ToastContainer'
import KeyboardShortcutsModal from './components/common/KeyboardShortcutsModal'
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
  const [showTimeMachine, setShowTimeMachine] = useState(false)
  const [isDocNavOpen, setDocNavOpen] = useState(true)
  const [editorKey, setEditorKey] = useState(0) // Force editor re-mount on restore
  const [currentChapterContent, setCurrentChapterContent] = useState<string>('')
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved')
  const [showRecap, setShowRecap] = useState(false)

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

      setShowTimeMachine(false)

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
      description: 'Toggle Codex sidebar',
      handler: () => toggleSidebar(),
    },
    {
      key: 't',
      ctrl: true,
      description: 'Toggle Timeline sidebar',
      handler: () => setTimelineOpen(!isTimelineOpen),
    },
    {
      key: 'd',
      ctrl: true,
      description: 'Toggle chapter navigator',
      handler: () => setDocNavOpen(!isDocNavOpen),
    },
    {
      key: 'h',
      ctrl: true,
      description: 'Show Time Machine (history)',
      handler: () => setShowTimeMachine(true),
    },
    {
      key: 'Escape',
      description: 'Close modals and sidebars',
      handler: () => {
        setShowTimeMachine(false);
        setShowKeyboardShortcuts(false);
      },
    },
  ];

  // Enable keyboard shortcuts when editing manuscript
  useKeyboardShortcuts(shortcuts, !!currentManuscriptId)

  // Show editor when a manuscript is selected
  if (currentManuscriptId && currentManuscript) {
    return (
      <div className="min-h-screen bg-vellum text-midnight flex flex-col">
        {/* Header - Maxwell Style */}
        <header className="border-b border-slate-ui bg-white px-6 py-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={handleCloseEditor}
                className="text-faded-ink hover:text-midnight transition-colors font-sans text-sm"
                title="Back to library"
              >
                ← Library
              </button>
              <h1 className="text-xl font-serif font-bold text-midnight">
                {currentManuscript.title}
              </h1>
              {/* Save status indicator */}
              <span className="text-xs font-sans text-faded-ink">
                {saveStatus === 'saved' && '✓ Saved'}
                {saveStatus === 'saving' && '⋯ Saving...'}
                {saveStatus === 'unsaved' && '• Unsaved changes'}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              {/* Document Navigator Toggle */}
              <button
                onClick={() => setDocNavOpen(!isDocNavOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Toggle Document Navigator"
              >
                📑 Chapters
              </button>

              {/* Writing Recap Button */}
              <button
                onClick={() => setShowRecap(true)}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Generate writing recap card"
              >
                ✨ Recap
              </button>

              {/* Time Machine Button */}
              <button
                onClick={() => setShowTimeMachine(true)}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="View version history"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Time Machine
              </button>

              {/* Timeline Toggle Button */}
              <button
                onClick={() => setTimelineOpen(!isTimelineOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Toggle Timeline"
              >
                📅 Timeline
              </button>

              {/* Codex Toggle Button */}
              <button
                onClick={toggleSidebar}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Toggle Codex"
              >
                📖 Codex
              </button>

              {/* Coach Toggle Button */}
              <button
                onClick={toggleCoach}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Toggle Writing Coach"
              >
                ✨ Coach
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area with Editor and Sidebars */}
        <main className="flex-1 flex overflow-hidden">
          {/* Document Navigator (Far Left) */}
          {isDocNavOpen && (
            <div className="w-64 flex-shrink-0">
              <DocumentNavigator
                manuscriptId={currentManuscript.id}
                onChapterSelect={handleChapterSelect}
              />
            </div>
          )}

          {/* Timeline Sidebar (Left) */}
          <TimelineSidebar
            manuscriptId={currentManuscript.id}
            isOpen={isTimelineOpen}
            onToggle={() => setTimelineOpen(!isTimelineOpen)}
          />

          {/* Editor */}
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
                  <button
                    onClick={() => setDocNavOpen(true)}
                    className="px-6 py-3 bg-bronze text-white font-sans rounded hover:bg-bronze/90 transition-colors"
                  >
                    {isDocNavOpen ? 'Create New Chapter' : 'Show Chapters'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Codex Sidebar (Right) */}
          <CodexSidebar
            manuscriptId={currentManuscript.id}
            isOpen={isSidebarOpen}
            onToggle={toggleSidebar}
          />

          {/* FastCoach Sidebar (Far Right) */}
          <FastCoachSidebar
            manuscriptId={currentManuscript.id}
            isOpen={isCoachOpen}
            onToggle={toggleCoach}
          />
        </main>

        {/* Time Machine Modal */}
        {showTimeMachine && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-vellum rounded-lg shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
              <TimeMachine
                manuscriptId={currentManuscript.id}
                currentContent={currentChapterContent}
                onRestore={handleRestoreSnapshot}
                onClose={() => setShowTimeMachine(false)}
              />
            </div>
          </div>
        )}

        {/* Keyboard Shortcuts Modal */}
        {showKeyboardShortcuts && (
          <KeyboardShortcutsModal
            shortcuts={shortcuts}
            onClose={() => setShowKeyboardShortcuts(false)}
          />
        )}

        {/* Writing Recap Modal */}
        {showRecap && (
          <RecapModal
            manuscriptId={currentManuscript.id}
            onClose={() => setShowRecap(false)}
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
