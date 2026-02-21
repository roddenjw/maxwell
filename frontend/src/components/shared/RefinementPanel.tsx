/**
 * RefinementPanel Component
 *
 * Reusable AI refinement loop for any suggestion type.
 * Manages iterative "suggest -> feedback -> refine -> accept" flow.
 *
 * Used across: beat suggestions, beat descriptions, beat mappings,
 * brainstorm ideas, entity suggestions, wiki entries, plot hole fixes.
 */

import { useState, type ReactNode } from 'react';
import { refinementApi } from '@/lib/api';
import { toast } from '@/stores/toastStore';

interface RefinementPanelProps {
  suggestion: any;
  domain: string;
  context: Record<string, string>;
  renderSuggestion: (suggestion: any) => ReactNode;
  onAccept: (refined: any) => void;
  onCancel: () => void;
}

interface RefinementTurn {
  feedback: string;
  result: any;
}

export default function RefinementPanel({
  suggestion,
  domain,
  context,
  renderSuggestion,
  onAccept,
  onCancel,
}: RefinementPanelProps) {
  const [currentSuggestion, setCurrentSuggestion] = useState(suggestion);
  const [refinementHistory, setRefinementHistory] = useState<RefinementTurn[]>([]);
  const [feedbackInput, setFeedbackInput] = useState('');
  const [isRefining, setIsRefining] = useState(false);

  const getApiKey = (): string | null => {
    return localStorage.getItem('openrouter_api_key');
  };

  const handleRefine = async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    if (!feedbackInput.trim()) {
      toast.error('Please provide feedback for refinement');
      return;
    }

    setIsRefining(true);
    try {
      // Build history from previous turns
      const history = refinementHistory.flatMap((turn) => [
        { role: 'user', content: turn.feedback },
        { role: 'assistant', content: JSON.stringify(turn.result) },
      ]);

      const result = await refinementApi.refine({
        api_key: apiKey,
        domain,
        original: currentSuggestion,
        feedback: feedbackInput.trim(),
        context,
        history,
      });

      if (result.error) {
        toast.error(result.error);
        return;
      }

      // Add to history
      setRefinementHistory((prev) => [
        ...prev,
        { feedback: feedbackInput.trim(), result: result.data },
      ]);

      setCurrentSuggestion(result.data);
      setFeedbackInput('');

      if (result.cost?.formatted) {
        toast.success(`Refined! Cost: ${result.cost.formatted}`);
      }
    } catch (error: any) {
      console.error('Refinement failed:', error);
      if (error.message?.includes('invalid_api_key') || error.message?.includes('Invalid API key')) {
        toast.error('Invalid API key. Check your settings.');
      } else {
        toast.error(error.message || 'Refinement failed');
      }
    } finally {
      setIsRefining(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleRefine();
    }
  };

  return (
    <div
      className="mt-2 p-3 bg-purple-50 border-2 border-purple-300"
      style={{ borderRadius: '2px' }}
    >
      {/* Current version */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-sans font-bold text-purple-800 uppercase tracking-wider">
            {refinementHistory.length > 0 ? `Refined (v${refinementHistory.length + 1})` : 'Current'}
          </span>
        </div>
        <div className="p-2 bg-white border border-purple-200" style={{ borderRadius: '2px' }}>
          {renderSuggestion(currentSuggestion)}
        </div>
      </div>

      {/* History */}
      {refinementHistory.length > 0 && (
        <div className="mb-3 max-h-32 overflow-y-auto">
          <span className="text-xs font-sans font-semibold text-purple-700 uppercase tracking-wider mb-1 block">
            Refinement History
          </span>
          <div className="space-y-1">
            {refinementHistory.map((turn, i) => (
              <div
                key={i}
                className="text-xs font-sans text-faded-ink p-1.5 bg-purple-50/50 border-l-2 border-purple-200"
              >
                <span className="font-medium text-purple-700">You:</span>{' '}
                {turn.feedback}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feedback input */}
      <div className="mb-3">
        <textarea
          value={feedbackInput}
          onChange={(e) => setFeedbackInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="How should this be improved? e.g., 'Make it more dramatic', 'Focus on the mentor relationship'..."
          className="w-full px-2.5 py-2 text-sm border border-purple-300 focus:border-purple-500 focus:outline-none font-sans text-midnight placeholder:text-faded-ink/50 resize-y min-h-[60px]"
          style={{ borderRadius: '2px' }}
          disabled={isRefining}
        />
        <p className="text-xs text-faded-ink mt-1">
          Press Cmd+Enter to refine
        </p>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleRefine}
          disabled={isRefining || !feedbackInput.trim()}
          className="px-3 py-1.5 text-sm font-sans font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          style={{ borderRadius: '2px' }}
        >
          {isRefining ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Refining...</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refine</span>
            </>
          )}
        </button>

        <button
          onClick={() => onAccept(currentSuggestion)}
          className="px-3 py-1.5 text-sm font-sans font-medium bg-green-600 hover:bg-green-700 text-white transition-colors flex items-center gap-1.5"
          style={{ borderRadius: '2px' }}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>Accept & Save</span>
        </button>

        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm font-sans font-medium text-faded-ink hover:text-midnight transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
