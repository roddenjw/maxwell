/**
 * AddSceneButton Component
 * Button to add a scene between beats in the outline, with AI bridge suggestions
 */

import { useState } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import { outlineApi } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import type { PlotBeat, BridgeSceneSuggestion } from '@/types/outline';

interface AddSceneButtonProps {
  afterBeat: PlotBeat;
  nextBeat?: PlotBeat;
}

export default function AddSceneButton({ afterBeat, nextBeat }: AddSceneButtonProps) {
  const { createScene, outline, getApiKey } = useOutlineStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [sceneLabel, setSceneLabel] = useState('');
  const [sceneDescription, setSceneDescription] = useState('');
  const [targetWordCount, setTargetWordCount] = useState(1000);

  // AI Bridge state
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<BridgeSceneSuggestion[]>([]);
  const [bridgingAnalysis, setBridgingAnalysis] = useState('');
  const [showAISuggestions, setShowAISuggestions] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sceneLabel.trim()) return;

    setIsCreating(true);
    try {
      await createScene({
        scene_label: sceneLabel.trim(),
        scene_description: sceneDescription.trim(),
        after_beat_id: afterBeat.id,
        target_word_count: targetWordCount,
      });
      resetForm();
    } finally {
      setIsCreating(false);
    }
  };

  const handleGetAISuggestions = async () => {
    if (!outline || !nextBeat) {
      toast.error('Cannot generate suggestions without a next beat');
      return;
    }

    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    setIsLoadingAI(true);
    try {
      const result = await outlineApi.generateBridgeScenes(
        outline.id,
        afterBeat.id,
        nextBeat.id,
        apiKey
      );

      setAiSuggestions(result.data.scenes || []);
      setBridgingAnalysis(result.data.bridging_analysis || '');
      setShowAISuggestions(true);

      toast.success(`Bridge scene ideas generated! Cost: ${result.cost?.formatted || '$0.00'}`);
    } catch (error: any) {
      console.error('Failed to generate bridge scenes:', error);
      if (error.message?.includes('insufficient_credits')) {
        toast.error('Insufficient OpenRouter credits. Add credits at openrouter.ai');
      } else if (error.message?.includes('invalid_api_key')) {
        toast.error('Invalid API key. Check your settings.');
      } else {
        toast.error('Failed to generate bridge scenes');
      }
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleSelectSuggestion = (suggestion: BridgeSceneSuggestion) => {
    setSceneLabel(suggestion.title);
    setSceneDescription(suggestion.description);
    setTargetWordCount(suggestion.suggested_word_count);
    setShowAISuggestions(false);
  };

  const resetForm = () => {
    setIsOpen(false);
    setSceneLabel('');
    setSceneDescription('');
    setTargetWordCount(1000);
    setAiSuggestions([]);
    setBridgingAnalysis('');
    setShowAISuggestions(false);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full py-1.5 px-3 flex items-center justify-center gap-2 text-sm text-faded-ink/60 hover:text-bronze hover:bg-bronze/5 transition-colors border-2 border-dashed border-transparent hover:border-bronze/30 group"
        style={{ borderRadius: '2px' }}
        title={`Add a scene between "${afterBeat.beat_label}" and "${nextBeat?.beat_label || 'end'}"`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        <span className="opacity-0 group-hover:opacity-100 transition-opacity">Add Scene</span>
      </button>
    );
  }

  return (
    <div className="p-3 bg-bronze/5 border-2 border-bronze/30" style={{ borderRadius: '2px' }}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-sans font-semibold text-bronze">
          Add Scene
        </h4>
        <button
          type="button"
          onClick={resetForm}
          className="text-faded-ink hover:text-midnight transition-colors text-sm"
        >
          Cancel
        </button>
      </div>

      <p className="text-xs text-faded-ink mb-3">
        Bridge between <strong>{afterBeat.beat_label}</strong> and <strong>{nextBeat?.beat_label || 'the end'}</strong>
      </p>

      {/* AI Bridge Button */}
      {nextBeat && !showAISuggestions && (
        <button
          type="button"
          onClick={handleGetAISuggestions}
          disabled={isLoadingAI}
          className={`w-full mb-3 px-3 py-2 flex items-center justify-center gap-2 text-sm font-sans font-medium transition-colors ${
            isLoadingAI
              ? 'bg-purple-100 text-purple-400 cursor-wait'
              : 'bg-purple-500/10 text-purple-600 hover:bg-purple-500/20 border border-purple-300'
          }`}
          style={{ borderRadius: '2px' }}
        >
          {isLoadingAI ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Generating Ideas...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>AI: Bridge This Gap</span>
            </>
          )}
        </button>
      )}

      {/* AI Suggestions Panel */}
      {showAISuggestions && aiSuggestions.length > 0 && (
        <div className="mb-4 p-3 bg-purple-50 border border-purple-200" style={{ borderRadius: '2px' }}>
          <div className="flex items-center justify-between mb-2">
            <h5 className="text-sm font-sans font-semibold text-purple-900">
              AI Scene Suggestions
            </h5>
            <button
              type="button"
              onClick={() => setShowAISuggestions(false)}
              className="text-xs text-purple-600 hover:text-purple-800"
            >
              Hide
            </button>
          </div>

          {bridgingAnalysis && (
            <p className="text-xs text-purple-700 mb-3 italic">
              {bridgingAnalysis}
            </p>
          )}

          <div className="space-y-2">
            {aiSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectSuggestion(suggestion)}
                className="w-full text-left p-2 bg-white border border-purple-200 hover:border-purple-400 hover:bg-purple-50/50 transition-colors"
                style={{ borderRadius: '2px' }}
              >
                <div className="font-sans font-medium text-sm text-midnight mb-1">
                  {suggestion.title}
                </div>
                <div className="text-xs text-faded-ink mb-1">
                  {suggestion.description}
                </div>
                <div className="flex items-center gap-2 text-xs text-purple-600">
                  <span>{suggestion.suggested_word_count.toLocaleString()} words</span>
                  <span>•</span>
                  <span className="italic">{suggestion.emotional_purpose}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Manual Entry Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-xs font-sans font-medium text-midnight mb-1">
            Scene Title *
          </label>
          <input
            type="text"
            value={sceneLabel}
            onChange={(e) => setSceneLabel(e.target.value)}
            placeholder="e.g., Character meets mentor"
            className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50"
            style={{ borderRadius: '2px' }}
            autoFocus
          />
        </div>

        <div>
          <label className="block text-xs font-sans font-medium text-midnight mb-1">
            Description (optional)
          </label>
          <textarea
            value={sceneDescription}
            onChange={(e) => setSceneDescription(e.target.value)}
            placeholder="What happens in this scene..."
            className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50 min-h-[60px] resize-y"
            style={{ borderRadius: '2px' }}
          />
        </div>

        <div>
          <label className="block text-xs font-sans font-medium text-midnight mb-1">
            Target Word Count
          </label>
          <input
            type="number"
            value={targetWordCount}
            onChange={(e) => setTargetWordCount(parseInt(e.target.value) || 1000)}
            min={100}
            max={10000}
            step={100}
            className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight"
            style={{ borderRadius: '2px' }}
          />
        </div>

        <button
          type="submit"
          disabled={!sceneLabel.trim() || isCreating}
          className="w-full px-3 py-2 bg-bronze hover:bg-bronze-dark disabled:bg-slate-ui/50 text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
          style={{ borderRadius: '2px' }}
        >
          {isCreating ? 'Adding...' : 'Add Scene'}
        </button>
      </form>
    </div>
  );
}
