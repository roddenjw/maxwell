/**
 * PlotBrainstorm - Plot generation form for conflicts, twists, and subplots
 * Generates central conflicts, plot twists, subplots, and complications
 */

import { useState, useEffect, useRef, useCallback } from 'react';

import type { PlotGenerationRequest } from '@/types/brainstorm';

import { brainstormingApi } from '@/lib/api';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { AIGenerationProgress } from '@/components/Common';

export default function PlotBrainstorm() {
  const {
    currentSession,
    setGenerating,
    isGenerating,
    addIdeas,
    manuscriptContext,
    savePremise,
  } = useBrainstormStore();

  const [genre, setGenre] = useState('');
  const [premise, setPremise] = useState('');
  const [numIdeas, setNumIdeas] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);
  const [useCustomContext, setUseCustomContext] = useState(false);

  const estimatedCost = numIdeas * 0.012; // ~$0.012 per plot idea

  // Debounced save of premise when user edits it
  const saveTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const handlePremiseChange = useCallback((value: string) => {
    setPremise(value);
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    if (value.trim()) {
      saveTimerRef.current = setTimeout(() => {
        savePremise(value, 'user_written');
      }, 1500);
    }
  }, [savePremise]);

  // Check for stored API key on mount
  useEffect(() => {
    const key = localStorage.getItem('openrouter_api_key');
    setStoredApiKey(key);
  }, []);

  // Auto-populate from manuscript context
  useEffect(() => {
    if (manuscriptContext?.outline && !useCustomContext) {
      setGenre(manuscriptContext.outline.genre || '');
      setPremise(manuscriptContext.outline.premise || '');
    }
  }, [manuscriptContext, useCustomContext]);

  // Handle custom context toggle
  const handleToggleCustomContext = (enabled: boolean) => {
    setUseCustomContext(enabled);
    if (enabled) {
      // Clear fields when switching to custom context
      setGenre('');
      setPremise('');
    } else if (manuscriptContext?.outline) {
      // Restore manuscript context
      setGenre(manuscriptContext.outline.genre || '');
      setPremise(manuscriptContext.outline.premise || '');
    }
  };

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

    if (!storedApiKey) {
      setError('Please set your OpenRouter API key in Settings');
      return;
    }

    try {
      setError(null);
      setGenerating(true);

      const request: PlotGenerationRequest = {
        api_key: storedApiKey,
        genre: genre.trim(),
        premise: premise.trim(),
        num_ideas: numIdeas,
      };

      const ideas = await brainstormingApi.generatePlots(
        currentSession.id,
        request
      );

      addIdeas(currentSession.id, ideas);

      // Clear form after successful generation
      setGenre('');
      setPremise('');
    } catch (err) {
      console.error('Generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate plot ideas');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Plot Development
        </h3>
        <p className="text-sm text-gray-600">
          Generate compelling plot ideas including central conflicts, plot twists, subplots, and complications
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Context Toggle (only show if manuscript has context) */}
        {manuscriptContext?.outline && (
          <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-blue-900">
                {useCustomContext ? 'Using custom context' : 'Using manuscript context'}
              </span>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <span className="text-sm text-blue-700">Use custom context</span>
              <input
                type="checkbox"
                checked={useCustomContext}
                onChange={(e) => handleToggleCustomContext(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        )}

        {/* Genre */}
        <div>
          <label htmlFor="plot-genre" className="block text-sm font-medium text-gray-700 mb-1">
            Genre *
          </label>
          <input
            id="plot-genre"
            type="text"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            placeholder="e.g., Thriller, Romance, Horror"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isGenerating}
          />
        </div>

        {/* Story Premise */}
        <div>
          <label htmlFor="plot-premise" className="block text-sm font-medium text-gray-700 mb-1">
            Story Premise *
          </label>
          <textarea
            id="plot-premise"
            value={premise}
            onChange={(e) => handlePremiseChange(e.target.value)}
            placeholder="Describe your story's world, main characters, and initial situation..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isGenerating}
          />
        </div>

        {/* Number of Ideas */}
        <div>
          <label htmlFor="plot-numIdeas" className="block text-sm font-medium text-gray-700 mb-1">
            Number of Plot Ideas: {numIdeas}
          </label>
          <div className="flex items-center gap-4">
            <input
              id="plot-numIdeas"
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

        {/* API Key Status */}
        <div>
          {storedApiKey ? (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-green-800 font-medium">API key configured</span>
            </div>
          ) : (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-900 font-medium mb-2">
                No API key found
              </p>
              <p className="text-xs text-yellow-800 mb-3">
                You need an OpenRouter API key to use AI brainstorming features. Set it up once in Settings.
              </p>
              <button
                onClick={() => {
                  const event = new CustomEvent('openSettings');
                  window.dispatchEvent(event);
                }}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
              >
                Open Settings →
              </button>
            </div>
          )}
        </div>

        {/* Cost Estimate */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-900 font-medium">Estimated Cost:</span>
            <span className="text-blue-700">${estimatedCost.toFixed(3)}</span>
          </div>
          <p className="text-xs text-blue-600 mt-1">
            Based on {numIdeas} plot idea{numIdeas !== 1 ? 's' : ''} × ~$0.012 each
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
          disabled={isGenerating || !genre || !premise || !storedApiKey}
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
              Generating Plot Ideas...
            </span>
          ) : (
            'Generate Plot Ideas'
          )}
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">
          Plot Elements Generated
        </h4>
        <ul className="text-xs text-gray-700 space-y-1">
          <li><strong>Central Conflict:</strong> The main dramatic tension driving the story</li>
          <li><strong>Plot Twist:</strong> Surprising revelation that changes the narrative</li>
          <li><strong>Subplot:</strong> Secondary story thread that enriches the main plot</li>
          <li><strong>Complication:</strong> Obstacle that raises stakes and tension</li>
        </ul>
      </div>

      {/* AI Generation Progress Overlay */}
      <AIGenerationProgress
        isGenerating={isGenerating}
        message="Generating Plot Ideas"
        estimatedSeconds={numIdeas * 4}
      />
    </div>
  );
}
