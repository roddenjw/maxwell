/**
 * ConflictBrainstorm - Conflict scenario generation form
 * Creates layered conflicts with stakes, escalation, and resolution paths
 */

import { useState, useEffect, useRef, useCallback } from 'react';

import type { ConflictGenerationRequest } from '@/types/brainstorm';

import { brainstormingApi } from '@/lib/api';
import { useBrainstormStore } from '@/stores/brainstormStore';
import { AIGenerationProgress } from '@/components/Common';

type ConflictType = 'internal' | 'interpersonal' | 'external' | 'societal' | 'any';

export default function ConflictBrainstorm() {
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
  const [conflictType, setConflictType] = useState<ConflictType>('any');
  const [numIdeas, setNumIdeas] = useState(5);
  const [selectedCharacters, setSelectedCharacters] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);
  const [useCustomContext, setUseCustomContext] = useState(false);

  const estimatedCost = numIdeas * 0.018; // ~$0.018 per conflict idea

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
      setGenre('');
      setPremise('');
    } else if (manuscriptContext?.outline) {
      setGenre(manuscriptContext.outline.genre || '');
      setPremise(manuscriptContext.outline.premise || '');
    }
  };

  const toggleCharacter = (charId: string) => {
    setSelectedCharacters(prev =>
      prev.includes(charId)
        ? prev.filter(id => id !== charId)
        : [...prev, charId]
    );
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

      const request: ConflictGenerationRequest = {
        api_key: storedApiKey,
        genre: genre.trim(),
        premise: premise.trim(),
        conflict_type: conflictType,
        character_ids: selectedCharacters.length > 0 ? selectedCharacters : undefined,
        num_ideas: numIdeas,
      };

      const ideas = await brainstormingApi.generateConflicts(
        currentSession.id,
        request
      );

      addIdeas(currentSession.id, ideas);
    } catch (err) {
      console.error('Generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate conflicts');
    } finally {
      setGenerating(false);
    }
  };

  const conflictTypeDescriptions: Record<ConflictType, string> = {
    any: 'Generate a mix of all conflict types',
    internal: 'Character vs Self - moral dilemmas, inner demons, identity struggles',
    interpersonal: 'Character vs Character - relationships, betrayals, rivalries',
    external: 'Character vs Environment - nature, obstacles, survival',
    societal: 'Character vs System - institutions, norms, oppression',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Conflict Development
        </h3>
        <p className="text-sm text-gray-600">
          Generate layered conflict scenarios with clear stakes, escalation paths, and resolution options
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Context Toggle */}
        {manuscriptContext?.outline && (
          <div className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-md">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-orange-900">
                {useCustomContext ? 'Using custom context' : 'Using manuscript context'}
              </span>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <span className="text-sm text-orange-700">Use custom context</span>
              <input
                type="checkbox"
                checked={useCustomContext}
                onChange={(e) => handleToggleCustomContext(e.target.checked)}
                className="w-4 h-4 text-orange-600 rounded focus:ring-orange-500"
              />
            </label>
          </div>
        )}

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
            placeholder="e.g., Epic Fantasy, Thriller, Romance"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
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
            onChange={(e) => handlePremiseChange(e.target.value)}
            placeholder="Describe your story's core concept, setting, and any existing tensions..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
            disabled={isGenerating}
          />
        </div>

        {/* Conflict Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Conflict Type
          </label>
          <div className="grid grid-cols-2 gap-2">
            {(['any', 'internal', 'interpersonal', 'external', 'societal'] as ConflictType[]).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setConflictType(type)}
                className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                  conflictType === type
                    ? 'bg-orange-500 text-white border-orange-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
                disabled={isGenerating}
              >
                {type === 'any' ? 'Any Type' : type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {conflictTypeDescriptions[conflictType]}
          </p>
        </div>

        {/* Character Selection */}
        {!useCustomContext && manuscriptContext?.existing_entities?.characters && manuscriptContext.existing_entities.characters.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Involve Characters <span className="text-gray-500 font-normal">(Optional)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {manuscriptContext.existing_entities.characters.map(char => (
                <button
                  key={char.id}
                  type="button"
                  onClick={() => toggleCharacter(char.id)}
                  className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                    selectedCharacters.includes(char.id)
                      ? 'bg-orange-100 text-orange-800 border-orange-300'
                      : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
                  }`}
                  disabled={isGenerating}
                >
                  {char.name}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Select characters to feature in the conflicts, or leave empty for general suggestions
            </p>
          </div>
        )}

        {/* Number of Ideas */}
        <div>
          <label htmlFor="numIdeas" className="block text-sm font-medium text-gray-700 mb-1">
            Number of Conflicts: {numIdeas}
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
                You need an OpenRouter API key to use AI brainstorming features.
              </p>
              <button
                onClick={() => {
                  const event = new CustomEvent('openSettings');
                  window.dispatchEvent(event);
                }}
                className="px-4 py-2 bg-orange-600 text-white text-sm rounded-md hover:bg-orange-700 transition-colors"
              >
                Open Settings
              </button>
            </div>
          )}
        </div>

        {/* Cost Estimate */}
        <div className="bg-orange-50 border border-orange-200 rounded-md p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-orange-900 font-medium">Estimated Cost:</span>
            <span className="text-orange-700">${estimatedCost.toFixed(3)}</span>
          </div>
          <p className="text-xs text-orange-600 mt-1">
            Based on {numIdeas} conflict{numIdeas !== 1 ? 's' : ''} x ~$0.018 each
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
          className="w-full px-4 py-3 bg-orange-600 text-white font-medium rounded-md hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
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
              Generating Conflicts...
            </span>
          ) : (
            'Generate Conflict Ideas'
          )}
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">
          Conflict Development Framework
        </h4>
        <ul className="text-xs text-gray-700 space-y-1">
          <li><strong>Core Tension:</strong> The fundamental opposition or struggle</li>
          <li><strong>Stakes:</strong> What characters stand to gain or lose</li>
          <li><strong>Trigger:</strong> What initiates the conflict</li>
          <li><strong>Escalation:</strong> How the conflict intensifies</li>
          <li><strong>Resolution Paths:</strong> Different ways the conflict could resolve</li>
        </ul>
      </div>

      {/* AI Generation Progress Overlay */}
      <AIGenerationProgress
        isGenerating={isGenerating}
        message="Generating Conflicts"
        estimatedSeconds={numIdeas * 4}
      />
    </div>
  );
}
