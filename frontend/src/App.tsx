import { useState } from 'react'
import ManuscriptEditor from './components/Editor/ManuscriptEditor'

function App() {
  const [showEditor, setShowEditor] = useState(false)

  if (showEditor) {
    return (
      <div className="min-h-screen bg-vellum text-midnight">
        {/* Header - Maxwell Style */}
        <header className="border-b border-slate-ui bg-white px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowEditor(false)}
                className="text-faded-ink hover:text-midnight transition-colors font-sans text-sm"
                title="Back to home"
              >
                ← Back
              </button>
              <h1 className="text-xl font-serif font-bold text-midnight">
                Untitled Manuscript
              </h1>
            </div>
          </div>
        </header>

        {/* Editor */}
        <main>
          <ManuscriptEditor mode="normal" />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-vellum text-midnight">
      {/* Header - Maxwell Brand */}
      <header className="border-b border-slate-ui bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-serif font-bold text-midnight tracking-tight">
              MAXWELL
            </h1>
            <span className="text-sm text-faded-ink font-sans">
              The Author's Study
            </span>
          </div>
        </div>
      </header>

      {/* Main Content - Classic Literary Design */}
      <main className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto space-y-12">
          {/* Hero Section */}
          <div className="text-center space-y-6">
            <h2 className="text-5xl font-serif font-bold text-midnight leading-tight">
              A Distraction-Free Study<br />For The Serious Author
            </h2>
            <p className="text-xl text-faded-ink font-sans max-w-2xl mx-auto">
              Write with the focus of a classic library. Your manuscript, versioned like a scholar's notebook. Your story bible, organized like an archivist's dream.
            </p>
          </div>

          {/* Feature Cards - Clean & Professional */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
            <div className="p-8 bg-white border border-slate-ui">
              <div className="text-4xl mb-4 text-bronze">📝</div>
              <h3 className="font-serif font-bold text-xl mb-3 text-midnight">
                The Living Manuscript
              </h3>
              <p className="text-sm text-faded-ink font-sans leading-relaxed">
                Write with confidence. Every keystroke automatically preserved. Navigate your revision history like turning pages in a leather-bound journal.
              </p>
            </div>

            <div className="p-8 bg-white border border-slate-ui">
              <div className="text-4xl mb-4 text-bronze">📚</div>
              <h3 className="font-serif font-bold text-xl mb-3 text-midnight">
                The Story Bible
              </h3>
              <p className="text-sm text-faded-ink font-sans leading-relaxed">
                Your codex of characters, locations, and lore. Automatically extracted as you write. Never lose track of your world's consistency.
              </p>
            </div>

            <div className="p-8 bg-white border border-slate-ui">
              <div className="text-4xl mb-4 text-bronze">✨</div>
              <h3 className="font-serif font-bold text-xl mb-3 text-midnight">
                The Muse
              </h3>
              <p className="text-sm text-faded-ink font-sans leading-relaxed">
                Context-aware AI assistance when you need it. Expand outlines, enhance descriptions, maintain your unique voice.
              </p>
            </div>
          </div>

          {/* Primary CTA - The Bronze Stamp */}
          <div className="pt-12 text-center">
            <button
              onClick={() => setShowEditor(true)}
              className="px-10 py-4 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
              style={{ borderRadius: '2px' }}
            >
              Begin Writing
            </button>
            <p className="mt-4 text-sm text-faded-ink font-sans">
              No account required. Your work stays on your device.
            </p>
          </div>

          {/* Status Footer */}
          <div className="pt-16 text-center border-t border-slate-ui">
            <p className="text-sm text-faded-ink font-sans">
              Status: <span className="text-bronze font-medium">● Ready to Write</span>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
