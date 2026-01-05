/**
 * BrainstormingModal - Main modal for AI-powered brainstorming
 * Foundation component for Phase 1: Character Generation MVP
 */

import { useBrainstormStore } from '@/stores/brainstormStore';

export default function BrainstormingModal() {
  const {
    isModalOpen,
    closeModal,
    currentSession,
    currentTechnique,
    isGenerating,
    totalCost,
  } = useBrainstormStore();

  if (!isModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">
              Brainstorm Ideas 💡
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              AI-powered ideation using Brandon Sanderson's methodology
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* Cost Tracker */}
            {totalCost > 0 && (
              <div className="text-right">
                <div className="text-xs text-gray-500">Session Cost</div>
                <div className="text-sm font-semibold text-gray-900">
                  ${totalCost.toFixed(4)}
                </div>
              </div>
            )}
            <button
              onClick={closeModal}
              className="text-gray-400 hover:text-gray-600"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🚧</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Brainstorming UI Coming Soon
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              The backend is complete! Next up: building the character generation interface with Brandon Sanderson's WANT/NEED/FLAW/STRENGTH/ARC methodology.
            </p>
            <div className="mt-6 text-left max-w-lg mx-auto">
              <h4 className="font-semibold text-gray-900 mb-2">What's Ready:</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>✅ Database models (sessions & ideas)</li>
                <li>✅ AI service with OpenRouter integration</li>
                <li>✅ 10 API endpoints</li>
                <li>✅ Codex integration</li>
                <li>✅ TypeScript types</li>
                <li>✅ API client methods</li>
                <li>✅ Zustand state management</li>
              </ul>
              <h4 className="font-semibold text-gray-900 mb-2 mt-4">Next Steps:</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>⏳ Character brainstorming UI</li>
                <li>⏳ Idea results panel</li>
                <li>⏳ Integration flow</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={closeModal}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
