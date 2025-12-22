import { useState } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'
import ManuscriptLibrary from './components/ManuscriptLibrary'
import { TimeMachine } from './components/TimeMachine'
import { CodexSidebar } from './components/Codex'
import { useManuscriptStore } from './stores/manuscriptStore'
import { useCodexStore } from './stores/codexStore'

function App() {
  const { currentManuscriptId, setCurrentManuscript, getCurrentManuscript, updateManuscript } = useManuscriptStore()
  const currentManuscript = getCurrentManuscript()
  const { isSidebarOpen, toggleSidebar } = useCodexStore()
  const [showTimeMachine, setShowTimeMachine] = useState(false)
  const [editorKey, setEditorKey] = useState(0) // Force editor re-mount on restore

  const handleOpenManuscript = (manuscriptId: string) => {
    setCurrentManuscript(manuscriptId)
  }

  const handleCloseEditor = () => {
    setCurrentManuscript(null)
  }

  const handleRestoreSnapshot = (content: string) => {
    if (currentManuscriptId) {
      updateManuscript(currentManuscriptId, { content })
      setShowTimeMachine(false)
      // Force editor re-mount with new content
      setEditorKey(prev => prev + 1)
    }
  }

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
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
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

              {/* Codex Toggle Button */}
              <button
                onClick={toggleSidebar}
                className="flex items-center gap-2 px-4 py-2 bg-bronze text-white font-sans text-sm rounded hover:bg-bronze/90 transition-colors"
                title="Toggle Codex"
              >
                📖 Codex
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area with Editor and Sidebar */}
        <main className="flex-1 flex overflow-hidden">
          {/* Editor */}
          <div className="flex-1 overflow-auto">
            <ManuscriptEditor
              key={editorKey}
              manuscriptId={currentManuscript.id}
              initialContent={currentManuscript.content}
              mode="normal"
            />
          </div>

          {/* Codex Sidebar */}
          <CodexSidebar
            manuscriptId={currentManuscript.id}
            isOpen={isSidebarOpen}
            onToggle={toggleSidebar}
          />
        </main>

        {/* Time Machine Modal */}
        {showTimeMachine && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-vellum rounded-lg shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
              <TimeMachine
                manuscriptId={currentManuscript.id}
                currentContent={currentManuscript.content}
                onRestore={handleRestoreSnapshot}
                onClose={() => setShowTimeMachine(false)}
              />
            </div>
          </div>
        )}
      </div>
    )
  }

  // Show manuscript library by default
  return <ManuscriptLibrary onOpenManuscript={handleOpenManuscript} />
}

export default App
