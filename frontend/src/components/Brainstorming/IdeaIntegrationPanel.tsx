/**
 * IdeaIntegrationPanel - Integrate selected ideas into Codex
 */

import { useState } from 'react';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { brainstormingApi } from '@/lib/api';
import type { CharacterMetadata } from '@/types/brainstorm';

export default function IdeaIntegrationPanel() {
  const {
    getSelectedIdeas,
    updateIdea,
    deselectAllIdeas,
  } = useBrainstormStore();

  const [isIntegrating, setIsIntegrating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successCount, setSuccessCount] = useState(0);
  const [entityType, setEntityType] = useState<'CHARACTER' | 'LORE'>('CHARACTER');

  const selectedIdeas = getSelectedIdeas();

  const handleIntegrate = async () => {
    if (selectedIdeas.length === 0) {
      setError('No ideas selected');
      return;
    }

    try {
      setError(null);
      setIsIntegrating(true);
      setSuccessCount(0);

      let integrated = 0;

      for (const idea of selectedIdeas) {
        try {
          await brainstormingApi.integrateToCodex(idea.id, {
            entity_type: entityType,
          });

          updateIdea(idea.id, { integrated_to_codex: true });
          integrated++;
          setSuccessCount(integrated);
        } catch (err) {
          console.error(`Failed to integrate idea ${idea.id}:`, err);
          // Continue with next idea
        }
      }

      if (integrated === selectedIdeas.length) {
        // All succeeded
        setTimeout(() => {
          deselectAllIdeas();
          setSuccessCount(0);
        }, 2000);
      } else {
        setError(`Integrated ${integrated} of ${selectedIdeas.length} ideas. Check console for errors.`);
      }
    } catch (err) {
      console.error('Integration error:', err);
      setError(err instanceof Error ? err.message : 'Failed to integrate ideas');
    } finally {
      setIsIntegrating(false);
    }
  };

  if (selectedIdeas.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <div className="text-3xl mb-2">👈</div>
        <p className="text-sm text-gray-600">
          Select one or more characters to integrate them into your Codex
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">
          Integrate to Codex
        </h3>
        <p className="text-sm text-gray-600">
          Add {selectedIdeas.length} selected character{selectedIdeas.length !== 1 ? 's' : ''} to your
          story's knowledge base
        </p>
      </div>

      {/* Entity Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Entity Type
        </label>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="CHARACTER"
              checked={entityType === 'CHARACTER'}
              onChange={(e) => setEntityType(e.target.value as 'CHARACTER')}
              className="text-blue-600 focus:ring-blue-500"
              disabled={isIntegrating}
            />
            <span className="text-sm text-gray-700">Character</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="LORE"
              checked={entityType === 'LORE'}
              onChange={(e) => setEntityType(e.target.value as 'LORE')}
              className="text-blue-600 focus:ring-blue-500"
              disabled={isIntegrating}
            />
            <span className="text-sm text-gray-700">Lore / Concept</span>
          </label>
        </div>
      </div>

      {/* Preview List */}
      <div className="border border-gray-200 rounded-md max-h-48 overflow-y-auto">
        <div className="divide-y divide-gray-200">
          {selectedIdeas.map((idea) => {
            const metadata = idea.idea_metadata as CharacterMetadata;
            return (
              <div
                key={idea.id}
                className="px-3 py-2 flex items-center justify-between hover:bg-gray-50"
              >
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {metadata.name}
                  </div>
                  <div className="text-xs text-gray-500">{metadata.role}</div>
                </div>
                {idea.integrated_to_codex && (
                  <span className="text-xs text-green-600 font-medium">
                    ✓ Already integrated
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Success Message */}
      {successCount > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <p className="text-sm text-green-800">
            ✓ Successfully integrated {successCount} of {selectedIdeas.length} character
            {selectedIdeas.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Integrate Button */}
      <button
        onClick={handleIntegrate}
        disabled={isIntegrating}
        className="w-full px-4 py-3 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isIntegrating ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Integrating to Codex...
          </span>
        ) : (
          `Add ${selectedIdeas.length} to Codex`
        )}
      </button>

      {/* Info */}
      <div className="text-xs text-gray-500">
        <p>
          Characters will be added as <strong>{entityType}</strong> entities in your Codex with
          all character framework fields preserved in their attributes.
        </p>
      </div>
    </div>
  );
}
