/**
 * CharacterBrainstorm - Character generation form using Brandon Sanderson's methodology
 * WANT/NEED/FLAW/STRENGTH/ARC framework
 */

import { useState } from 'react';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { brainstormingApi } from '@/lib/api';
import type { CharacterGenerationRequest } from '@/types/brainstorm';

export default function CharacterBrainstorm() {
  const {
    currentSession,
    setGenerating,
    isGenerating,
    addIdeas,
  } = useBrainstormStore();

  const [genre, setGenre] = useState('');
  const [premise, setPremise] = useState('');
  const [numIdeas, setNumIdeas] = useState(5);
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);

  const estimatedCost = numIdeas * 0.015; // ~$0.015 per character idea

  const handleGenerate = async () => {
    if (!currentSession) {
      setError('No active session');
      return;
    }

    if (!genre.trim()) {
      setError('Please enter a genre');
      return;
    }

    if (!premise.trim()) {
      setError('Please enter a story premise');
      return;
    }

    if (!apiKey.trim()) {
      setError('Please enter your OpenRouter API key');
      return;
    }

    try {
      setError(null);
      setGenerating(true);

      const request: CharacterGenerationRequest = {
        api_key: apiKey,
        genre: genre.trim(),
        story_premise: premise.trim(),
        num_ideas: numIdeas,
      };

      const ideas = await brainstormingApi.generateCharacters(
        currentSession.id,
        request
      );

      addIdeas(currentSession.id, ideas);

      // Clear form after successful generation
      setGenre('');
      setPremise('');
    } catch (err) {
      console.error('Generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate characters');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Character Development
        </h3>
        <p className="text-sm text-gray-600">
          Generate compelling characters using Brandon Sanderson's WANT/NEED/FLAW/STRENGTH/ARC methodology
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Genre */}
        <div>
          <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-1">
            Genre *
          </label>
          <input
            id="genre"
            type="text"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            placeholder="e.g., Epic Fantasy, Science Fiction, Mystery"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isGenerating}
          />
        </div>

        {/* Story Premise */}
        <div>
          <label htmlFor="premise" className="block text-sm font-medium text-gray-700 mb-1">
            Story Premise *
          </label>
          <textarea
            id="premise"
            value={premise}
            onChange={(e) => setPremise(e.target.value)}
            placeholder="Describe your story's core concept, setting, and central conflict..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isGenerating}
          />
        </div>

        {/* Number of Ideas */}
        <div>
          <label htmlFor="numIdeas" className="block text-sm font-medium text-gray-700 mb-1">
            Number of Characters: {numIdeas}
          </label>
          <div className="flex items-center gap-4">
            <input
              id="numIdeas"
              type="range"
              min="1"
              max="10"
              value={numIdeas}
              onChange={(e) => setNumIdeas(parseInt(e.target.value))}
              className="flex-1"
              disabled={isGenerating}
            />
            <input
              type="number"
              min="1"
              max="10"
              value={numIdeas}
              onChange={(e) => setNumIdeas(Math.min(10, Math.max(1, parseInt(e.target.value) || 1)))}
              className="w-16 px-2 py-1 border border-gray-300 rounded-md text-center"
              disabled={isGenerating}
            />
          </div>
        </div>

        {/* API Key */}
        <div>
          <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">
            OpenRouter API Key *
          </label>
          <input
            id="apiKey"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-or-v1-..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isGenerating}
          />
          <p className="text-xs text-gray-500 mt-1">
            Your API key is never stored. Get one at{' '}
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              openrouter.ai/keys
            </a>
          </p>
        </div>

        {/* Cost Estimate */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-900 font-medium">Estimated Cost:</span>
            <span className="text-blue-700">${estimatedCost.toFixed(3)}</span>
          </div>
          <p className="text-xs text-blue-600 mt-1">
            Based on {numIdeas} character{numIdeas !== 1 ? 's' : ''} × ~$0.015 each
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !genre || !premise || !apiKey}
          className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? (
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
              Generating Characters...
            </span>
          ) : (
            'Generate Character Ideas'
          )}
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">
          Brandon Sanderson's Character Framework
        </h4>
        <ul className="text-xs text-gray-700 space-y-1">
          <li><strong>WANT:</strong> What the character thinks they need (surface goal)</li>
          <li><strong>NEED:</strong> What they actually need (deeper truth)</li>
          <li><strong>FLAW:</strong> Internal weakness preventing growth</li>
          <li><strong>STRENGTH:</strong> Core ability or positive trait</li>
          <li><strong>ARC:</strong> Journey from WANT to NEED realization</li>
        </ul>
      </div>
    </div>
  );
}
