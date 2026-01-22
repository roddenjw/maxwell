/**
 * BrainstormingModal - Main modal for AI-powered brainstorming
 * Multi-type ideation: Characters, Plots, Locations, Conflicts, Scenes
 */

import { useEffect, useState } from 'react';
import { useBrainstormStore } from '@/stores/brainstormStore';
import CharacterBrainstorm from './CharacterBrainstorm';
import PlotBrainstorm from './PlotBrainstorm';
import LocationBrainstorm from './LocationBrainstorm';
import ConflictBrainstorm from './ConflictBrainstorm';
import SceneBrainstorm from './SceneBrainstorm';
import IdeaResultsPanel from './IdeaResultsPanel';
import IdeaIntegrationPanel from './IdeaIntegrationPanel';
import SessionHistoryPanel from './SessionHistoryPanel';
import { MindMapCanvas } from './MindMap';

type IdeaType = 'character' | 'plot' | 'location' | 'conflict' | 'scene';
type ActiveTab = 'generate' | 'results' | 'history' | 'mindmap';

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
    loadManuscriptContext,
  } = useBrainstormStore();

  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>('generate');
  const [ideaType, setIdeaType] = useState<IdeaType>('character');

  // Handle idea type change - create new session
  const handleIdeaTypeChange = async (newType: IdeaType) => {
    if (newType === ideaType) return;

    setIdeaType(newType);
    setIsInitialized(false);
    setActiveTab('generate');

    // Create new session for the new type
    if (modalManuscriptId) {
      try {
        await createSession(
          modalManuscriptId,
          getSessionType(newType),
          {
            technique: newType,
            timestamp: new Date().toISOString(),
          },
          modalOutlineId || undefined
        );
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to create session:', error);
      }
    }
  };

  // Map UI type to session type
  const getSessionType = (type: IdeaType) => {
    switch (type) {
      case 'character':
        return 'CHARACTER';
      case 'plot':
        return 'PLOT_BEAT';
      case 'location':
        return 'WORLD';
      case 'conflict':
        return 'CONFLICT';
      case 'scene':
        return 'SCENE';
      default:
        return 'CHARACTER';
    }
  };

  // Initialize session when modal opens or idea type changes
  useEffect(() => {
    if (isModalOpen && modalManuscriptId && !currentSession && !isInitialized) {
      const initSession = async () => {
        try {
          await createSession(
            modalManuscriptId,
            getSessionType(ideaType),
            {
              technique: ideaType,
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
  }, [isModalOpen, modalManuscriptId, currentSession, createSession, modalOutlineId, isInitialized, ideaType]);

  // Auto-switch to results tab when ideas are generated
  useEffect(() => {
    if (currentSession) {
      const ideas = getSessionIdeas(currentSession.id);
      if (ideas.length > 0 && activeTab === 'generate') {
        setActiveTab('results');
      }
    }
  }, [currentSession, getSessionIdeas, activeTab]);

  // Load manuscript context when modal opens
  useEffect(() => {
    if (isModalOpen && modalManuscriptId) {
      loadManuscriptContext(modalManuscriptId);
    }
  }, [isModalOpen, modalManuscriptId, loadManuscriptContext]);

  if (!isModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">
              {ideaType === 'character' && 'Character Brainstorming'}
              {ideaType === 'plot' && 'Plot Brainstorming'}
              {ideaType === 'location' && 'Location Brainstorming'}
              {ideaType === 'conflict' && 'Conflict Brainstorming'}
              {ideaType === 'scene' && 'Scene Brainstorming'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {ideaType === 'character' && 'AI-powered character generation with detailed personality, backstory, and motivations'}
              {ideaType === 'plot' && 'Generate compelling plot ideas, conflicts, twists, and subplots'}
              {ideaType === 'location' && 'Create immersive locations with rich worldbuilding details'}
              {ideaType === 'conflict' && 'Generate layered conflict scenarios with stakes, escalation, and resolution paths'}
              {ideaType === 'scene' && 'Create structured scene ideas with beats, emotional arcs, and dialogue moments'}
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

        {/* Type Selection Tabs */}
        <div className="bg-gray-50 border-b border-gray-200">
          <div className="flex px-6 py-2 gap-2 flex-wrap">
            <button
              onClick={() => handleIdeaTypeChange('character')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                ideaType === 'character'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              👤 Characters
            </button>
            <button
              onClick={() => handleIdeaTypeChange('plot')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                ideaType === 'plot'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              📖 Plots
            </button>
            <button
              onClick={() => handleIdeaTypeChange('location')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                ideaType === 'location'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              🌍 Locations
            </button>
            <button
              onClick={() => handleIdeaTypeChange('conflict')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                ideaType === 'conflict'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              ⚔️ Conflicts
            </button>
            <button
              onClick={() => handleIdeaTypeChange('scene')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                ideaType === 'scene'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              🎬 Scenes
            </button>
          </div>
        </div>

        {/* Workflow Tabs */}
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
            <button
              onClick={() => setActiveTab('mindmap')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'mindmap'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Mind Map
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              History
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {activeTab === 'generate' && (
            <div className="h-full overflow-y-auto px-6 py-6">
              {ideaType === 'character' && <CharacterBrainstorm />}
              {ideaType === 'plot' && <PlotBrainstorm />}
              {ideaType === 'location' && <LocationBrainstorm />}
              {ideaType === 'conflict' && <ConflictBrainstorm />}
              {ideaType === 'scene' && <SceneBrainstorm />}
            </div>
          )}

          {activeTab === 'results' && (
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

          {activeTab === 'mindmap' && modalManuscriptId && (
            <div className="h-full">
              <MindMapCanvas
                manuscriptId={modalManuscriptId}
                onSave={(nodes, connections) => {
                  console.log('Mind map saved:', { nodes, connections });
                  // TODO: Persist to backend
                }}
              />
            </div>
          )}

          {activeTab === 'history' && modalManuscriptId && (
            <div className="h-full overflow-y-auto px-6 py-6">
              <SessionHistoryPanel
                manuscriptId={modalManuscriptId}
                onResumeSession={(_session) => {
                  setActiveTab('results');
                }}
              />
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
