import { useState } from 'react'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        {/* Header */}
        <header className="border-b border-gray-200 dark:border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
                Codex IDE
              </h1>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                v0.1.0-alpha
              </span>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              {darkMode ? '☀️ Light' : '🌙 Dark'}
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-12">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold">
                Welcome to Codex IDE
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400">
                An AI-powered writing environment for fiction authors
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              {/* Feature Cards */}
              <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="text-3xl mb-3">📝</div>
                <h3 className="font-semibold mb-2">Living Manuscript</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Write with confidence. Your work is automatically versioned and never lost.
                </p>
              </div>

              <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="text-3xl mb-3">📚</div>
                <h3 className="font-semibold mb-2">Story Bible</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Your Codex tracks characters, locations, and relationships automatically.
                </p>
              </div>

              <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="text-3xl mb-3">✨</div>
                <h3 className="font-semibold mb-2">AI Muse</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Get unstuck with context-aware writing assistance powered by AI.
                </p>
              </div>
            </div>

            <div className="pt-8">
              <button className="px-8 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-colors shadow-lg">
                Create New Manuscript
              </button>
            </div>

            <div className="pt-12 border-t border-gray-200 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Status: <span className="text-green-600 dark:text-green-400">● Backend Connected</span>
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
