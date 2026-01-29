import { useState, useEffect, useRef, Suspense } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'
import { CharacterSheetEditor, NotesEditor, TitlePageForm } from './components/Editor'
import type { Chapter } from './lib/api'
import ManuscriptLibrary from './components/ManuscriptLibrary'
import { WorldLibrary } from './components/WorldLibrary'
import { CodexMainView } from './components/Codex'
import TimelineSidebar from './components/Timeline/TimelineSidebar'
import DocumentNavigator from './components/Document/DocumentNavigator'
import FastCoachSidebar from './components/FastCoach/FastCoachSidebar'
import UnifiedSidebar from './components/Navigation/UnifiedSidebar'
import ToastContainer from './components/Common/ToastContainer'
import KeyboardShortcutsModal from './components/Common/KeyboardShortcutsModal'
import ViewLoadingSpinner from './components/Common/ViewLoadingSpinner'
import { OutlineMainView } from './components/Outline'
import { BrainstormingModal } from './components/Brainstorming'
import { useManuscriptStore } from './stores/manuscriptStore'
import { useOnboardingStore } from './stores/onboardingStore'
import { useCodexStore } from './stores/codexStore'
import { useTimelineStore } from './stores/timelineStore'
import { useChapterStore } from './stores/chapterStore'
import { useChapterCacheStore } from './stores/chapterCacheStore'
import { useFastCoachStore } from './stores/fastCoachStore'
import { useOutlineStore } from './stores/outlineStore'
import { useAchievementStore } from './stores/achievementStore'
import { chaptersApi } from './lib/api'
import { useKeyboardShortcuts, type KeyboardShortcut } from './hooks/useKeyboardShortcuts'
import { toast } from './stores/toastStore'
import { getErrorMessage } from './lib/retry'
import { useUnsavedChanges } from './hooks/useUnsavedChanges'
import { convertPlainTextToLexical } from './lib/lexicalConversion'
import analytics from './lib/analytics'

// Lazy-loaded components for better bundle splitting
import {
  LazyAnalyticsDashboard,
  LazyTimeMachine,
  LazyExportModal,
  LazyRecapModal,
  LazyManuscriptWizard,
  LazyWelcomeModal,
  LazyFeatureTour,
  LazySettingsModal,
} from './views'
import { AchievementDashboard } from './components/Achievements'

function App() {
  const { currentManuscriptId, setCurrentManuscript, getCurrentManuscript } = useManuscriptStore()
  const currentManuscript = getCurrentManuscript()
  const { loadEntities } = useCodexStore()
  const { isTimelineOpen, setTimelineOpen } = useTimelineStore()
  const { setCurrentChapter, currentChapterId } = useChapterStore()
  const { isSidebarOpen: isCoachOpen, toggleSidebar: toggleCoach } = useFastCoachStore()
  const { clearOutline } = useOutlineStore()
  const { loadAchievements, showDashboard: showAchievements, setShowDashboard: setShowAchievements, earnAchievement } = useAchievementStore()
  const [activeView, setActiveView] = useState<'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'recap' | 'analytics' | 'export' | 'outline'>('chapters')
  const [editorKey, setEditorKey] = useState(0) // Force editor re-mount on restore
  const [currentChapterContent, setCurrentChapterContent] = useState<string>('')
  const [currentChapterData, setCurrentChapterData] = useState<Chapter | null>(null)
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved')

  // Ref to track and abort in-flight chapter load requests (prevents race conditions)
  const chapterLoadAbortRef = useRef<AbortController | null>(null)

  // Onboarding state
  const {
    hasCompletedTour,
    shouldShowOnboarding,
    markWelcomeComplete,
    markTourComplete,
    markFirstManuscriptCreated
  } = useOnboardingStore()
  const [showWelcome, setShowWelcome] = useState(false)
  const [showTour, setShowTour] = useState(false)
  const [showWizard, setShowWizard] = useState(false)
  const [libraryView, setLibraryView] = useState<'manuscripts' | 'worlds'>('manuscripts')

  // Track unsaved changes and warn before closing
  const { checkNavigateAway } = useUnsavedChanges(saveStatus === 'unsaved' || saveStatus === 'saving')

  // Check if should show onboarding on mount
  useEffect(() => {
    if (shouldShowOnboarding()) {
      setShowWelcome(true)
    }
  }, [])

  // Load achievements on mount
  useEffect(() => {
    loadAchievements()
  }, [loadAchievements])

  const handleWelcomeComplete = async (sampleManuscriptId?: string, manuscriptData?: {title: string; wordCount: number}) => {
    markWelcomeComplete()
    setShowWelcome(false)
    analytics.onboardingCompleted(!!sampleManuscriptId)

    if (sampleManuscriptId && manuscriptData) {
      // Add sample manuscript to store (bridge backend to frontend)
      const { addManuscript } = useManuscriptStore.getState()
      addManuscript({
        id: sampleManuscriptId,
        title: manuscriptData.title,
        content: '',
        wordCount: manuscriptData.wordCount,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      })

      // Open the sample manuscript
      await handleOpenManuscript(sampleManuscriptId)
      markFirstManuscriptCreated()

      // Show feature tour after opening manuscript (delayed for proper mounting)
      setTimeout(() => {
        if (!hasCompletedTour) {
          setShowTour(true)
        }
      }, 1000)
    }
  }

  const handleWelcomeSkip = () => {
    markWelcomeComplete()
    setShowWelcome(false)
    analytics.onboardingSkipped()
  }

  const handleTourComplete = () => {
    markTourComplete()
    setShowTour(false)
    analytics.tourCompleted()
    toast.success('You\'re all set! Happy writing! ✨')
  }

  const handleTourSkip = () => {
    markTourComplete()
    setShowTour(false)
    analytics.tourSkipped()
  }

  const handleWizardComplete = async (manuscriptId: string, _outlineId: string) => {
    setShowWizard(false)

    // Fetch the created manuscript to add to store
    try {
      const response = await fetch(`http://localhost:8000/api/manuscripts/${manuscriptId}`)
      const manuscriptData = await response.json()

      // Add manuscript to store
      const { addManuscript } = useManuscriptStore.getState()
      addManuscript({
        id: manuscriptData.id,
        title: manuscriptData.title,
        content: '',
        wordCount: manuscriptData.word_count || 0,
        createdAt: manuscriptData.created_at,
        updatedAt: manuscriptData.updated_at,
      })

      // Open the manuscript
      await handleOpenManuscript(manuscriptId)

      // Show outline view with all plot beats (self-contained, no sidebar needed)
      setActiveView('outline')

      // Track creation with outline
      analytics.manuscriptCreated(manuscriptId, manuscriptData.title)
      toast.success('Manuscript created with story structure! Start writing your first beat.')
    } catch (error) {
      console.error('Failed to load created manuscript:', error)
      toast.error('Manuscript created but failed to open. Please refresh.')
    }
  }

  const handleOpenManuscript = async (manuscriptId: string) => {
    setCurrentManuscript(manuscriptId)

    if (!currentManuscriptId) {
      markFirstManuscriptCreated()
      earnAchievement('FIRST_MANUSCRIPT', manuscriptId)
    }

    // Track manuscript opened
    const manuscript = useManuscriptStore.getState().manuscripts.find(m => m.id === manuscriptId)
    if (manuscript) {
      analytics.manuscriptOpened(manuscriptId, manuscript.title)
    }

    // Preload entities for hover cards (load in background)
    try {
      loadEntities(manuscriptId).catch(error => {
        console.error('Failed to preload entities:', error)
      })
    } catch (error) {
      console.error('Failed to preload entities:', error)
    }

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
    setCurrentChapterData(null) // Clear chapter data
    clearOutline() // Clear outline state
    setSaveStatus('saved') // Reset save status
    setActiveView('chapters') // Reset view
  }

  const handleNavigate = (view: 'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'recap' | 'analytics' | 'export' | 'outline') => {
    setActiveView(view)

    // Track feature usage
    if (currentManuscriptId) {
      switch (view) {
        case 'codex':
          analytics.codexOpened(currentManuscriptId)
          break
        case 'timeline':
          analytics.timelineOpened(currentManuscriptId)
          break
        case 'analytics':
          analytics.analyticsOpened(currentManuscriptId)
          break
        case 'coach':
          analytics.fastCoachOpened(currentManuscriptId)
          break
        case 'recap':
          analytics.recapOpened(currentManuscriptId)
          break
        case 'timemachine':
          analytics.timeMachineOpened(currentManuscriptId)
          break
        case 'outline':
          // Track outline opened if needed
          break
      }
    }

    // Handle view-specific state updates
    if (view === 'chapters') {
      // No additional state needed
    } else if (view === 'codex') {
      // Codex is now a full-page view, no sidebar toggle needed
    } else if (view === 'timeline') {
      if (!isTimelineOpen) setTimelineOpen(true)
    } else if (view === 'timemachine') {
      // Time machine is a modal, handled separately
    } else if (view === 'coach') {
      if (!isCoachOpen) toggleCoach()
    } else if (view === 'outline') {
      // Outline is self-contained, no sidebar needed
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

  const handleCreateChapterFromBeat = async (beat: any) => {
    if (!currentManuscriptId) return

    try {
      // Create a new chapter with beat information
      const chapter = await chaptersApi.createChapter({
        manuscript_id: currentManuscriptId,
        title: beat.beat_label,
        is_folder: false,
      })

      // Update the beat to link it to the chapter
      const { updateBeat } = useOutlineStore.getState()
      await updateBeat(beat.id, { chapter_id: chapter.id })

      // Switch to chapters view and select the new chapter
      setActiveView('chapters')
      setTimeout(() => {
        handleChapterSelect(chapter.id)
      }, 100)

      toast.success(`Chapter "${beat.beat_label}" created!`)
    } catch (error) {
      console.error('Failed to create chapter from beat:', error)
      toast.error('Failed to create chapter')
    }
  }

  const handleViewBeat = (beatId: string) => {
    // Switch to outline view
    setActiveView('outline')

    // Expand the specific beat using the store
    // OutlineMainView will handle scrolling via the expandedBeatId effect
    const { setExpandedBeat } = useOutlineStore.getState()
    setExpandedBeat(beatId)
  }

  const handleChapterSelect = async (chapterId: string) => {
    // Check for unsaved changes before switching chapters
    if (!checkNavigateAway()) {
      return
    }

    // Get cache store
    const { getFromCache, setCache, setLoading } = useChapterCacheStore.getState()

    // Check cache first for instant loading
    const cached = getFromCache(chapterId)
    if (cached) {
      setCurrentChapter(chapterId)
      setCurrentChapterContent(cached.content)
      setEditorKey(prev => prev + 1)
      setSaveStatus('saved')
      // Still need to fetch chapter data for document type routing
      chaptersApi.getChapter(chapterId).then(chapter => {
        setCurrentChapterData(chapter)
      }).catch(err => {
        console.error('Failed to fetch chapter data:', err)
      })
      return // Instant switch!
    }

    // Abort any in-flight chapter load request to prevent race conditions
    if (chapterLoadAbortRef.current) {
      chapterLoadAbortRef.current.abort()
    }

    // Create new AbortController for this request
    const abortController = new AbortController()
    chapterLoadAbortRef.current = abortController

    // Store the chapter ID we're loading to verify it hasn't changed
    const targetChapterId = chapterId

    try {
      // Set loading state - this prevents editing
      setLoading(chapterId)
      setCurrentChapter(chapterId)

      // Fetch chapter content
      const chapter = await chaptersApi.getChapter(chapterId)

      // Store full chapter data for document type routing
      setCurrentChapterData(chapter)

      // Check if this request was aborted (user switched to a different chapter)
      if (abortController.signal.aborted) {
        console.log('Chapter load aborted - user switched chapters:', chapterId)
        return
      }

      // Defense in depth: verify we're still loading the same chapter
      // This handles edge cases where abort didn't fire but state changed
      const { currentChapterId: currentId } = useChapterStore.getState()
      if (currentId !== targetChapterId) {
        console.log('Chapter changed during load, discarding stale response:', chapterId)
        return
      }

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

      // Update cache with fetched content
      setCache(chapterId, {
        content: editorContent || '',
        lexicalState: chapter.lexical_state || null,
        loadedAt: Date.now(),
        wordCount: chapter.word_count || 0,
      })

      // Clear loading state
      setLoading(null)

      setCurrentChapterContent(editorContent || '')

      // Force editor re-mount with new content
      setEditorKey(prev => prev + 1)
      setSaveStatus('saved') // Reset save status for new chapter
    } catch (error) {
      // Clear loading state on error
      setLoading(null)

      // Silently ignore aborted requests
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      console.error('Failed to load chapter:', error)
      toast.error(getErrorMessage(error))
    }
  }

  // Reload chapter content when switching views (back to an editor view)
  // Note: Chapter switching is handled by handleChapterSelect, NOT here
  // This only handles the case where user navigates away (e.g., to Analytics) and back
  useEffect(() => {
    const viewsWithEditor = ['chapters', 'codex', 'coach'];

    // Only reload when returning TO an editor view from a non-editor view
    // We track the previous view to avoid reloading on initial mount or chapter changes
    if (!viewsWithEditor.includes(activeView) || !currentChapterId || saveStatus === 'saving') {
      return;
    }

    // Use abort controller to handle race conditions when view changes rapidly
    const abortController = new AbortController();

    const reloadChapterContent = async () => {
      try {
        const chapter = await chaptersApi.getChapter(currentChapterId);

        // Check if we were aborted (view changed again)
        if (abortController.signal.aborted) {
          return;
        }

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
        if (error instanceof Error && error.name === 'AbortError') {
          return;
        }
        console.error('Failed to reload chapter content:', error);
        toast.error('Failed to load chapter content');
      }
    };

    reloadChapterContent();

    return () => {
      abortController.abort();
    };
  }, [activeView]); // Only run when activeView changes, NOT when chapter changes

  // Listen for openSettings custom event from brainstorming components
  useEffect(() => {
    const handleOpenSettings = () => {
      setShowSettings(true);
    };

    window.addEventListener('openSettings', handleOpenSettings);
    return () => window.removeEventListener('openSettings', handleOpenSettings);
  }, []);

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
          onSettingsClick={() => setShowSettings(true)}
          onAchievementsClick={() => setShowAchievements(true)}
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
                <div className="w-64 flex-shrink-0" data-tour="chapters-nav">
                  <DocumentNavigator
                    manuscriptId={currentManuscript.id}
                    onChapterSelect={handleChapterSelect}
                  />
                </div>
                <div className="flex-1 overflow-auto" data-tour="editor">
                  {currentChapterId ? (
                    // Route to appropriate editor based on document type
                    (() => {
                      const docType = currentChapterData?.document_type || 'CHAPTER';
                      switch (docType) {
                        case 'CHARACTER_SHEET':
                          return (
                            <CharacterSheetEditor
                              key={editorKey}
                              chapterId={currentChapterId}
                              manuscriptId={currentManuscript.id}
                            />
                          );
                        case 'NOTES':
                          return (
                            <NotesEditor
                              key={editorKey}
                              chapterId={currentChapterId}
                            />
                          );
                        case 'TITLE_PAGE':
                          return (
                            <TitlePageForm
                              key={editorKey}
                              chapterId={currentChapterId}
                            />
                          );
                        case 'FOLDER':
                          // Folders show a summary view
                          return (
                            <div className="flex items-center justify-center h-full bg-vellum">
                              <div className="text-center max-w-md p-8">
                                <div className="text-6xl mb-4">📁</div>
                                <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
                                  {currentChapterData?.title || 'Folder'}
                                </h2>
                                <p className="font-sans text-faded-ink">
                                  This is a folder. Select a document inside to view its contents.
                                </p>
                              </div>
                            </div>
                          );
                        default:
                          // Default: standard manuscript editor for CHAPTER type
                          return (
                            <ManuscriptEditor
                              key={editorKey}
                              manuscriptId={currentManuscript.id}
                              chapterId={currentChapterId}
                              initialContent={currentChapterContent}
                              mode="normal"
                              onSaveStatusChange={setSaveStatus}
                              onViewBeat={handleViewBeat}
                            />
                          );
                      }
                    })()
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

            {/* Codex View - Full-page entity browser */}
            {activeView === 'codex' && (
              <div className="flex-1 flex bg-vellum">
                <CodexMainView
                  manuscriptId={currentManuscript.id}
                  onOpenChapter={handleChapterSelect}
                />
              </div>
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
                <div className="flex-1 overflow-auto">
                  {currentChapterId ? (
                    <ManuscriptEditor
                      key={editorKey}
                      manuscriptId={currentManuscript.id}
                      chapterId={currentChapterId}
                      initialContent={currentChapterContent}
                      mode="normal"
                      onSaveStatusChange={setSaveStatus}
                      onViewBeat={handleViewBeat}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full bg-vellum">
                      <div className="text-center max-w-md p-8">
                        <div className="text-6xl mb-6">✨</div>
                        <h2 className="font-garamond text-2xl font-semibold text-midnight mb-4">
                          Writing Coach
                        </h2>
                        <p className="font-sans text-faded-ink mb-6">
                          Select a chapter to get AI-powered writing assistance.
                          The coach analyzes your text in real-time.
                        </p>
                        <button
                          onClick={() => setActiveView('chapters')}
                          className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors"
                          style={{ borderRadius: '2px' }}
                        >
                          Select a Chapter
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                <FastCoachSidebar
                  manuscriptId={currentManuscript.id}
                  isOpen={true}
                  onToggle={() => setActiveView('chapters')}
                />
              </>
            )}

            {/* Time Machine View (Modal) */}
            {activeView === 'timemachine' && (
              <Suspense fallback={<ViewLoadingSpinner />}>
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                  <div className="bg-vellum rounded-lg shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
                    <LazyTimeMachine
                      manuscriptId={currentManuscript.id}
                      currentContent={currentChapterContent}
                      onRestore={handleRestoreSnapshot}
                      onClose={() => setActiveView('chapters')}
                    />
                  </div>
                </div>
              </Suspense>
            )}

            {/* Analytics View */}
            {activeView === 'analytics' && (
              <Suspense fallback={<ViewLoadingSpinner />}>
                <div className="flex-1 overflow-auto">
                  <LazyAnalyticsDashboard manuscriptId={currentManuscript.id} />
                </div>
              </Suspense>
            )}

            {/* Export View (Modal) */}
            {activeView === 'export' && (
              <Suspense fallback={<ViewLoadingSpinner />}>
                <LazyExportModal
                  manuscriptId={currentManuscript.id}
                  onClose={() => setActiveView('chapters')}
                />
              </Suspense>
            )}

            {/* Recap View (Modal) */}
            {activeView === 'recap' && (
              <Suspense fallback={<ViewLoadingSpinner />}>
                <LazyRecapModal
                  manuscriptId={currentManuscript.id}
                  onClose={() => setActiveView('chapters')}
                />
              </Suspense>
            )}

            {/* Outline View - Self-contained, no sidebar needed */}
            {activeView === 'outline' && (
              <div className="flex-1 flex bg-vellum">
                <OutlineMainView
                  manuscriptId={currentManuscript.id}
                  onCreateChapter={handleCreateChapterFromBeat}
                  onOpenChapter={handleChapterSelect}
                />
              </div>
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

        {/* Settings Modal */}
        {showSettings && (
          <Suspense fallback={<ViewLoadingSpinner />}>
            <LazySettingsModal
              isOpen={showSettings}
              onClose={() => setShowSettings(false)}
            />
          </Suspense>
        )}

        {/* Toast Notifications */}
        <ToastContainer />

        {/* Achievement Dashboard */}
        <AchievementDashboard
          isOpen={showAchievements}
          onClose={() => setShowAchievements(false)}
        />

        {/* Onboarding Modals */}
        {showWelcome && (
          <Suspense fallback={<ViewLoadingSpinner />}>
            <LazyWelcomeModal onComplete={handleWelcomeComplete} onSkip={handleWelcomeSkip} />
          </Suspense>
        )}
        {showTour && (
          <Suspense fallback={<ViewLoadingSpinner />}>
            <LazyFeatureTour onComplete={handleTourComplete} onSkip={handleTourSkip} />
          </Suspense>
        )}

        {/* Brainstorming Modal */}
        <BrainstormingModal />
      </div>
    )
  }

  // Show manuscript/world library by default
  return (
    <>
      {libraryView === 'manuscripts' ? (
        <ManuscriptLibrary
          onOpenManuscript={handleOpenManuscript}
          onSettingsClick={() => setShowSettings(true)}
          onCreateWithWizard={() => setShowWizard(true)}
        />
      ) : (
        <WorldLibrary
          onOpenManuscript={handleOpenManuscript}
          onSettingsClick={() => setShowSettings(true)}
          onCreateWithWizard={() => setShowWizard(true)}
          onBackToManuscripts={() => setLibraryView('manuscripts')}
        />
      )}

      {/* Library View Toggle - Fixed position button */}
      <button
        onClick={() => setLibraryView(libraryView === 'manuscripts' ? 'worlds' : 'manuscripts')}
        className="fixed bottom-6 right-6 px-4 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium shadow-book transition-colors flex items-center gap-2 z-40"
        style={{ borderRadius: '2px' }}
        title={libraryView === 'manuscripts' ? 'Switch to World Library' : 'Switch to All Manuscripts'}
      >
        {libraryView === 'manuscripts' ? (
          <>
            <span>&#x1F30D;</span>
            <span>World Library</span>
          </>
        ) : (
          <>
            <span>&#x1F4DA;</span>
            <span>All Manuscripts</span>
          </>
        )}
      </button>

      <ToastContainer />

      {/* Achievement Dashboard */}
      <AchievementDashboard
        isOpen={showAchievements}
        onClose={() => setShowAchievements(false)}
      />

      {/* Settings Modal */}
      {showSettings && (
        <Suspense fallback={<ViewLoadingSpinner />}>
          <LazySettingsModal
            isOpen={showSettings}
            onClose={() => setShowSettings(false)}
          />
        </Suspense>
      )}

      {/* Manuscript Creation Wizard */}
      {showWizard && (
        <Suspense fallback={<ViewLoadingSpinner />}>
          <LazyManuscriptWizard
            onComplete={handleWizardComplete}
            onCancel={() => setShowWizard(false)}
          />
        </Suspense>
      )}

      {/* Onboarding Modals */}
      {showWelcome && (
        <Suspense fallback={<ViewLoadingSpinner />}>
          <LazyWelcomeModal onComplete={handleWelcomeComplete} onSkip={handleWelcomeSkip} />
        </Suspense>
      )}
      {showTour && (
        <Suspense fallback={<ViewLoadingSpinner />}>
          <LazyFeatureTour onComplete={handleTourComplete} onSkip={handleTourSkip} />
        </Suspense>
      )}

      {/* Brainstorming Modal */}
      <BrainstormingModal />
    </>
  )
}

export default App
