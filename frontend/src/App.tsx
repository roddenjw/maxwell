import { useState } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'
import ManuscriptLibrary from './components/ManuscriptLibrary'
import { useManuscriptStore } from './stores/manuscriptStore'

function App() {
  const { currentManuscriptId, setCurrentManuscript, getCurrentManuscript } = useManuscriptStore()
  const currentManuscript = getCurrentManuscript()

  const handleOpenManuscript = (manuscriptId: string) => {
    setCurrentManuscript(manuscriptId)
  }

  const handleCloseEditor = () => {
    setCurrentManuscript(null)
  }

  // Show editor when a manuscript is selected
  if (currentManuscriptId && currentManuscript) {
    return (
      <div className="min-h-screen bg-vellum text-midnight">
        {/* Header - Maxwell Style */}
        <header className="border-b border-slate-ui bg-white px-6 py-3">
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
          </div>
        </header>

        {/* Editor */}
        <main>
          <ManuscriptEditor
            manuscriptId={currentManuscript.id}
            initialContent={currentManuscript.content}
            mode="normal"
          />
        </main>
      </div>
    )
  }

  // Show manuscript library by default
  return <ManuscriptLibrary onOpenManuscript={handleOpenManuscript} />
}

export default App
