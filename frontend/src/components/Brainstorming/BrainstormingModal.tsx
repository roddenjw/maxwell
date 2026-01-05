/**
 * BrainstormingModal - Main modal for AI-powered brainstorming
 * Character Generation MVP with Brandon Sanderson's methodology
 */

import { useEffect, useState } from 'react';
import { useBrainstormStore } from '@/stores/brainstormStore';
import CharacterBrainstorm from './CharacterBrainstorm';
import IdeaResultsPanel from './IdeaResultsPanel';
import IdeaIntegrationPanel from './IdeaIntegrationPanel';

export default function BrainstormingModal() {
  const {
    isModalOpen,
    closeModal,
    currentSession,
    createSession,
    totalCost,
    modalManuscriptId,
    modalOutlineId,
    getSessionIdeas,
  } = useBrainstormStore();

  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState<'generate' | 'results'>('generate');

  // Initialize session when modal opens
  useEffect(() => {
    if (isModalOpen && modalManuscriptId && !currentSession && !isInitialized) {
      const initSession = async () => {
        try {
          await createSession(
            modalManuscriptId,
            'CHARACTER',
            {
              technique: 'character',
              timestamp: new Date().toISOString(),
            },
            modalOutlineId || undefined
          );
          setIsInitialized(true);
        } catch (error) {
          console.error('Failed to create session:', error);
        }
      };

      initSession();
    }

    // Reset when modal closes
    if (!isModalOpen) {
      setIsInitialized(false);
      setActiveTab('generate');
    }
  }, [isModalOpen, modalManuscriptId, currentSession, createSession, modalOutlineId, isInitialized]);

  // Auto-switch to results tab when ideas are generated
  useEffect(() => {
    if (currentSession) {
      const ideas = getSessionIdeas(currentSession.id);
      if (ideas.length > 0 && activeTab === 'generate') {
        setActiveTab('results');
      }
    }
  }, [currentSession, getSessionIdeas, activeTab]);

  if (!isModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">
              Character Brainstorming
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              AI-powered character generation using Brandon Sanderson's methodology
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

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('generate')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'generate'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Generate Ideas
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'results'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Review & Integrate
              {currentSession && getSessionIdeas(currentSession.id).length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {getSessionIdeas(currentSession.id).length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'generate' ? (
            <div className="h-full overflow-y-auto px-6 py-6">
              <CharacterBrainstorm />
            </div>
          ) : (
            <div className="h-full grid grid-cols-3 gap-6 p-6 overflow-hidden">
              {/* Results Panel - 2 columns */}
              <div className="col-span-2 overflow-y-auto">
                <IdeaResultsPanel />
              </div>

              {/* Integration Panel - 1 column */}
              <div className="overflow-y-auto">
                <IdeaIntegrationPanel />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            {currentSession && (
              <span>Session ID: {currentSession.id.substring(0, 8)}...</span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={closeModal}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
