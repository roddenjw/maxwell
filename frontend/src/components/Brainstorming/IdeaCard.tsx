/**
 * IdeaCard - Display individual brainstorm idea with selection, editing, and refinement
 * Supports CHARACTER, PLOT_BEAT, WORLD, CONFLICT, and SCENE idea types
 */

import { useState, useEffect } from 'react';
import type { BrainstormIdea } from '@/types/brainstorm';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { brainstormingApi } from '@/lib/api';

interface IdeaCardProps {
  idea: BrainstormIdea;
}

type RefineDirection = 'refine' | 'expand' | 'contrast';

export default function IdeaCard({ idea }: IdeaCardProps) {
  const { selectedIdeaIds, toggleIdeaSelection, updateIdea, addIdeas, currentSession } = useBrainstormStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notes, setNotes] = useState(idea.user_notes || '');
  const [showRefineMenu, setShowRefineMenu] = useState(false);
  const [refineFeedback, setRefineFeedback] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const [refineError, setRefineError] = useState<string | null>(null);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);

  const isSelected = selectedIdeaIds.has(idea.id);
  const metadata = idea.idea_metadata;

  // Check for stored API key on mount
  useEffect(() => {
    const key = localStorage.getItem('openrouter_api_key');
    setStoredApiKey(key);
  }, []);

  const handleSaveNotes = () => {
    updateIdea(idea.id, { user_notes: notes });
    setIsEditingNotes(false);
  };

  const handleCancelNotes = () => {
    setNotes(idea.user_notes || '');
    setIsEditingNotes(false);
  };

  const handleRefine = async (direction: RefineDirection) => {
    if (!storedApiKey) {
      setRefineError('No API key configured');
      return;
    }

    if (!refineFeedback.trim() && direction === 'refine') {
      setRefineError('Please provide feedback for refinement');
      return;
    }

    try {
      setIsRefining(true);
      setRefineError(null);

      const feedbackText = direction === 'refine'
        ? refineFeedback
        : direction === 'expand'
          ? 'Add more depth, detail, and nuance'
          : 'Create a contrasting version';

      const refinedIdea = await brainstormingApi.refineIdea(idea.id, {
        api_key: storedApiKey,
        feedback: feedbackText,
        direction: direction,
      });

      // Add the refined idea to the session
      if (currentSession) {
        addIdeas(currentSession.id, [refinedIdea]);
      }

      // Close the menu
      setShowRefineMenu(false);
      setRefineFeedback('');
    } catch (err) {
      console.error('Refinement error:', err);
      setRefineError(err instanceof Error ? err.message : 'Failed to refine idea');
    } finally {
      setIsRefining(false);
    }
  };

  // Get display title based on idea type
  const getTitle = () => {
    return metadata.name || metadata.title || idea.title;
  };

  // Get subtitle based on idea type
  const getSubtitle = () => {
    if (idea.idea_type === 'CHARACTER') {
      return metadata.role || 'Character';
    } else if (idea.idea_type === 'PLOT_BEAT') {
      return metadata.type?.replace('_', ' ').toUpperCase() || 'Plot Element';
    } else if (idea.idea_type === 'WORLD') {
      return metadata.type?.toUpperCase() || 'Location';
    } else if (idea.idea_type === 'CONFLICT') {
      return metadata.type?.replace('_', ' ').toUpperCase() || 'Conflict';
    } else if (idea.idea_type === 'SCENE') {
      return metadata.purpose?.toUpperCase() || 'Scene';
    }
    return idea.idea_type;
  };

  // Get hook/summary based on idea type
  const getHook = () => {
    return metadata.hook || metadata.opening_hook || metadata.core_tension || metadata.description?.substring(0, 150) || '';
  };

  // Get accent color based on idea type
  const getAccentColor = () => {
    switch (idea.idea_type) {
      case 'CHARACTER': return 'blue';
      case 'PLOT_BEAT': return 'green';
      case 'WORLD': return 'teal';
      case 'CONFLICT': return 'orange';
      case 'SCENE': return 'purple';
      default: return 'gray';
    }
  };

  const accentColor = getAccentColor();

  // Render expanded content based on idea type
  const renderExpandedContent = () => {
    switch (idea.idea_type) {
      case 'CHARACTER':
        return (
          <>
            {metadata.want && (
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Want</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.want}</p>
              </div>
            )}
            {metadata.need && (
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Need</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.need}</p>
              </div>
            )}
            {metadata.flaw && (
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Flaw</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.flaw}</p>
              </div>
            )}
            {metadata.strength && (
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">Strength</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.strength}</p>
              </div>
            )}
            {metadata.arc && (
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">Character Arc</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.arc}</p>
              </div>
            )}
            {metadata.relationships && (
              <div>
                <span className="text-xs font-semibold text-gray-600 uppercase">Relationships</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.relationships}</p>
              </div>
            )}
            {metadata.story_potential && (
              <div>
                <span className="text-xs font-semibold text-gray-600 uppercase">Story Potential</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.story_potential}</p>
              </div>
            )}
          </>
        );

      case 'PLOT_BEAT':
        return (
          <>
            {metadata.description && (
              <div>
                <span className="text-xs font-semibold text-gray-600 uppercase">Description</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.description}</p>
              </div>
            )}
            {metadata.setup && (
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Setup</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.setup}</p>
              </div>
            )}
            {metadata.escalation && (
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">Escalation</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.escalation}</p>
              </div>
            )}
            {metadata.resolution && (
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Resolution</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.resolution}</p>
              </div>
            )}
            {metadata.stakes && (
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Stakes</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.stakes}</p>
              </div>
            )}
            {metadata.beat_position && (
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">Position</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.beat_position}</p>
              </div>
            )}
          </>
        );

      case 'WORLD':
        return (
          <>
            {metadata.atmosphere && (
              <div>
                <span className="text-xs font-semibold text-teal-600 uppercase">Atmosphere</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.atmosphere}</p>
              </div>
            )}
            {metadata.culture && (
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">Culture</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.culture}</p>
              </div>
            )}
            {metadata.geography && (
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Geography</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.geography}</p>
              </div>
            )}
            {metadata.history && (
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">History</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.history}</p>
              </div>
            )}
            {metadata.story_role && (
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Story Role</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.story_role}</p>
              </div>
            )}
            {metadata.secrets && (
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Secrets</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.secrets}</p>
              </div>
            )}
          </>
        );

      case 'CONFLICT':
        return (
          <>
            {metadata.participants && (
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Participants</span>
                <p className="text-sm text-gray-700 mt-1">
                  {Array.isArray(metadata.participants) ? metadata.participants.join(', ') : metadata.participants}
                </p>
              </div>
            )}
            {metadata.core_tension && (
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">Core Tension</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.core_tension}</p>
              </div>
            )}
            {metadata.stakes && (
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Stakes</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.stakes}</p>
              </div>
            )}
            {metadata.trigger && (
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">Trigger</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.trigger}</p>
              </div>
            )}
            {metadata.escalation_points && (
              <div>
                <span className="text-xs font-semibold text-yellow-600 uppercase">Escalation Points</span>
                <ul className="text-sm text-gray-700 mt-1 list-disc list-inside">
                  {metadata.escalation_points.map((point: string, idx: number) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
            {metadata.possible_resolutions && (
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Possible Resolutions</span>
                <ul className="text-sm text-gray-700 mt-1 list-disc list-inside">
                  {metadata.possible_resolutions.map((res: string, idx: number) => (
                    <li key={idx}>{res}</li>
                  ))}
                </ul>
              </div>
            )}
            {metadata.emotional_core && (
              <div>
                <span className="text-xs font-semibold text-pink-600 uppercase">Emotional Core</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.emotional_core}</p>
              </div>
            )}
          </>
        );

      case 'SCENE':
        return (
          <>
            {metadata.pov_character && (
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">POV Character</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.pov_character}</p>
              </div>
            )}
            {metadata.location && (
              <div>
                <span className="text-xs font-semibold text-teal-600 uppercase">Location</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.location}</p>
              </div>
            )}
            {metadata.scene_goal && (
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Scene Goal</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.scene_goal}</p>
              </div>
            )}
            {metadata.obstacle && (
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Obstacle</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.obstacle}</p>
              </div>
            )}
            {metadata.emotional_arc && (
              <div>
                <span className="text-xs font-semibold text-pink-600 uppercase">Emotional Arc</span>
                <div className="text-sm text-gray-700 mt-1 space-y-1">
                  <p><span className="font-medium">Start:</span> {metadata.emotional_arc.start}</p>
                  <p><span className="font-medium">Shift:</span> {metadata.emotional_arc.shift}</p>
                  <p><span className="font-medium">End:</span> {metadata.emotional_arc.end}</p>
                </div>
              </div>
            )}
            {metadata.scene_beats && (
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">Scene Beats</span>
                <ol className="text-sm text-gray-700 mt-1 list-decimal list-inside">
                  {metadata.scene_beats.map((beat: string, idx: number) => (
                    <li key={idx}>{beat}</li>
                  ))}
                </ol>
              </div>
            )}
            {metadata.sensory_details && (
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Sensory Details</span>
                <ul className="text-sm text-gray-700 mt-1 list-disc list-inside">
                  {metadata.sensory_details.map((detail: string, idx: number) => (
                    <li key={idx}>{detail}</li>
                  ))}
                </ul>
              </div>
            )}
            {metadata.dialogue_moments && (
              <div>
                <span className="text-xs font-semibold text-indigo-600 uppercase">Dialogue Moments</span>
                <ul className="text-sm text-gray-700 mt-1 list-disc list-inside">
                  {metadata.dialogue_moments.map((moment: string, idx: number) => (
                    <li key={idx}>{moment}</li>
                  ))}
                </ul>
              </div>
            )}
            {metadata.subtext && (
              <div>
                <span className="text-xs font-semibold text-gray-600 uppercase">Subtext</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.subtext}</p>
              </div>
            )}
          </>
        );

      default:
        return (
          <div>
            <span className="text-xs font-semibold text-gray-600 uppercase">Details</span>
            <pre className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">
              {JSON.stringify(metadata, null, 2)}
            </pre>
          </div>
        );
    }
  };

  return (
    <div
      className={`border rounded-lg p-4 transition-all ${
        isSelected
          ? `border-${accentColor}-500 bg-${accentColor}-50`
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
      style={{
        borderColor: isSelected ? `var(--color-${accentColor}-500, #3b82f6)` : undefined,
        backgroundColor: isSelected ? `var(--color-${accentColor}-50, #eff6ff)` : undefined,
      }}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        {/* Selection Checkbox */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleIdeaSelection(idea.id)}
          className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title & Type Badge */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-gray-900">{getTitle()}</h4>
              <span className={`px-2 py-0.5 text-xs rounded-full bg-${accentColor}-100 text-${accentColor}-700`}
                style={{
                  backgroundColor: `var(--color-${accentColor}-100, #dbeafe)`,
                  color: `var(--color-${accentColor}-700, #1d4ed8)`,
                }}>
                {getSubtitle()}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {/* Refine Button */}
              <div className="relative">
                <button
                  onClick={() => setShowRefineMenu(!showRefineMenu)}
                  className="text-gray-400 hover:text-blue-600 p-1 rounded hover:bg-blue-50"
                  aria-label="Refine idea"
                  title="Refine this idea"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>

                {/* Refine Menu Dropdown */}
                {showRefineMenu && (
                  <div className="absolute right-0 top-8 z-10 w-72 bg-white border border-gray-200 rounded-lg shadow-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-3">Refine This Idea</h5>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">
                          Feedback / Direction
                        </label>
                        <textarea
                          value={refineFeedback}
                          onChange={(e) => setRefineFeedback(e.target.value)}
                          placeholder="e.g., 'Make the character darker', 'Add more humor', 'Strengthen the motivation'..."
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          disabled={isRefining}
                        />
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleRefine('refine')}
                          disabled={isRefining || !refineFeedback.trim()}
                          className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                        >
                          {isRefining ? 'Refining...' : 'Refine'}
                        </button>
                        <button
                          onClick={() => handleRefine('expand')}
                          disabled={isRefining}
                          className="px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:bg-gray-300"
                          title="Add more depth and detail"
                        >
                          Expand
                        </button>
                        <button
                          onClick={() => handleRefine('contrast')}
                          disabled={isRefining}
                          className="px-3 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700 disabled:bg-gray-300"
                          title="Create a contrasting version"
                        >
                          Contrast
                        </button>
                      </div>

                      {refineError && (
                        <p className="text-xs text-red-600">{refineError}</p>
                      )}

                      <button
                        onClick={() => {
                          setShowRefineMenu(false);
                          setRefineFeedback('');
                          setRefineError(null);
                        }}
                        className="w-full px-3 py-1 text-gray-600 text-sm hover:bg-gray-100 rounded"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-gray-400 hover:text-gray-600 p-1"
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
              >
                <svg
                  className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Hook (Always visible) */}
          {getHook() && (
            <p className="text-sm text-gray-700 mt-2 italic">"{getHook()}"</p>
          )}

          {/* Refined From indicator */}
          {metadata.refined_from && (
            <p className="text-xs text-blue-600 mt-1">
              Refined from previous idea ({metadata.refinement_direction})
            </p>
          )}

          {/* Expanded Details */}
          {isExpanded && (
            <div className="mt-4 space-y-3 border-t border-gray-200 pt-3">
              {renderExpandedContent()}

              {/* User Notes Section */}
              <div className="border-t border-gray-200 pt-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-600 uppercase">Your Notes</span>
                  {!isEditingNotes && (
                    <button
                      onClick={() => setIsEditingNotes(true)}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      {notes ? 'Edit' : 'Add notes'}
                    </button>
                  )}
                </div>

                {isEditingNotes ? (
                  <div className="space-y-2">
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add your thoughts, modifications, or reminders..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveNotes}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={handleCancelNotes}
                        className="px-3 py-1 bg-gray-200 text-gray-700 text-xs rounded-md hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : notes ? (
                  <p className="text-sm text-gray-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                    {notes}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">No notes yet</p>
                )}
              </div>
            </div>
          )}

          {/* Footer Metadata */}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            <span>Cost: ${idea.ai_cost.toFixed(4)}</span>
            <span>Tokens: {idea.ai_tokens.toLocaleString()}</span>
            {idea.integrated_to_codex && (
              <span className="text-green-600 font-medium">In Codex</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
