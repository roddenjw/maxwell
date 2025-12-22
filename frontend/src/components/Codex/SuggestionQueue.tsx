/**
 * SuggestionQueue - List of entity suggestions from NLP analysis
 */

import { useState, useEffect } from 'react';
import type { EntitySuggestion } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import SuggestionCard from './SuggestionCard';

interface SuggestionQueueProps {
  manuscriptId: string;
}

export default function SuggestionQueue({ manuscriptId }: SuggestionQueueProps) {
  const { suggestions, setSuggestions, removeSuggestion, addEntity } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  // Load suggestions on mount
  useEffect(() => {
    loadSuggestions();
  }, [manuscriptId]);

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await codexApi.listSuggestions(manuscriptId, 'PENDING');
      setSuggestions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (suggestion: EntitySuggestion) => {
    try {
      setProcessingId(suggestion.id);
      setError(null);

      const entity = await codexApi.approveSuggestion({
        suggestion_id: suggestion.id,
      });

      // Add to entities store
      addEntity(entity);

      // Remove from suggestions
      removeSuggestion(suggestion.id);
    } catch (err) {
      setError('Failed to approve: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (suggestion: EntitySuggestion) => {
    try {
      setProcessingId(suggestion.id);
      setError(null);

      await codexApi.rejectSuggestion(suggestion.id);

      // Remove from suggestions
      removeSuggestion(suggestion.id);
    } catch (err) {
      setError('Failed to reject: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setProcessingId(null);
    }
  };

  const pendingSuggestions = suggestions.filter((s) => s.status === 'PENDING');

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading suggestions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-redline/10 border-l-4 border-redline p-3 text-sm font-sans text-redline">
          {error}
        </div>
        <button
          onClick={loadSuggestions}
          className="mt-2 text-sm font-sans text-bronze hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (pendingSuggestions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <p className="text-midnight font-garamond font-semibold mb-2">
          No suggestions yet
        </p>
        <p className="text-sm text-faded-ink font-sans max-w-xs">
          Click the "Analyze" button in the editor toolbar to extract entities from your manuscript
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-sans text-faded-ink uppercase">
          Pending Suggestions ({pendingSuggestions.length})
        </h3>
        <button
          onClick={loadSuggestions}
          className="text-sm font-sans text-bronze hover:underline"
          title="Refresh suggestions"
        >
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-redline/10 border-l-4 border-redline p-2 text-xs font-sans text-redline">
          {error}
        </div>
      )}

      {/* Suggestion Cards */}
      <div className="space-y-3">
        {pendingSuggestions.map((suggestion) => (
          <SuggestionCard
            key={suggestion.id}
            suggestion={suggestion}
            onApprove={() => handleApprove(suggestion)}
            onReject={() => handleReject(suggestion)}
            isProcessing={processingId === suggestion.id}
          />
        ))}
      </div>
    </div>
  );
}
