/**
 * IdeaResultsPanel - Display and manage generated brainstorm ideas
 */

import IdeaCard from './IdeaCard';
import { useBrainstormStore } from '@/stores/brainstormStore';

export default function IdeaResultsPanel() {
  const {
    currentSession,
    getSessionIdeas,
    selectedIdeaIds,
    selectAllIdeas,
    deselectAllIdeas,
    calculateSessionCost,
  } = useBrainstormStore();

  if (!currentSession) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No active session</p>
      </div>
    );
  }

  const ideas = getSessionIdeas(currentSession.id);
  const sessionCost = calculateSessionCost(currentSession.id);
  const selectedCount = selectedIdeaIds.size;
  const allSelected = ideas.length > 0 && selectedCount === ideas.length;

  const handleToggleAll = () => {
    if (allSelected) {
      deselectAllIdeas();
    } else {
      selectAllIdeas(currentSession.id);
    }
  };

  if (ideas.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">💡</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Ideas Generated Yet
        </h3>
        <p className="text-gray-600">
          Fill out the form above and click "Generate Character Ideas" to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Generated Characters ({ideas.length})
          </h3>
          <p className="text-sm text-gray-600">
            Select the characters you want to add to your Codex
          </p>
        </div>

        {/* Session Stats */}
        <div className="text-right">
          <div className="text-xs text-gray-500">Total Cost</div>
          <div className="text-sm font-semibold text-gray-900">
            ${sessionCost.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Selection Controls */}
      <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={handleToggleAll}
            className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            {selectedCount > 0 ? (
              `${selectedCount} of ${ideas.length} selected`
            ) : (
              'Select all'
            )}
          </span>
        </div>

        {selectedCount > 0 && (
          <button
            onClick={deselectAllIdeas}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Clear selection
          </button>
        )}
      </div>

      {/* Ideas List */}
      <div className="space-y-3">
        {ideas.map((idea) => (
          <IdeaCard key={idea.id} idea={idea} />
        ))}
      </div>

      {/* Footer Info */}
      {selectedCount > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-semibold text-blue-900">
                Ready to integrate
              </h4>
              <p className="text-xs text-blue-700 mt-1">
                {selectedCount} character{selectedCount !== 1 ? 's' : ''} will be added to your Codex
              </p>
            </div>
            <div className="text-right">
              <div className="text-xs text-blue-600">Selected Cost</div>
              <div className="text-sm font-semibold text-blue-900">
                $
                {ideas
                  .filter((idea) => selectedIdeaIds.has(idea.id))
                  .reduce((sum, idea) => sum + idea.ai_cost, 0)
                  .toFixed(4)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="text-xs text-gray-500 italic">
        Tip: Click on any character to expand and see their full profile based on the
        WANT/NEED/FLAW/STRENGTH/ARC framework
      </div>
    </div>
  );
}
