/**
 * SuggestionQueue - List of entity suggestions from NLP analysis
 * Features auto-polling for real-time updates
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { EntitySuggestion, EntityType } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import SuggestionCard from './SuggestionCard';

interface SuggestionQueueProps {
  manuscriptId: string;
  pollingInterval?: number; // ms, default 30000 (30 seconds)
}

export default function SuggestionQueue({ manuscriptId, pollingInterval = 30000 }: SuggestionQueueProps) {
  const { suggestions, setSuggestions, removeSuggestion, addEntity, entities, updateEntity } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [newSuggestionCount, setNewSuggestionCount] = useState(0);
  const [lastFetchedIds, setLastFetchedIds] = useState<Set<string>>(new Set());
  const pollingRef = useRef<ReturnType<typeof setInterval>>();
  const isMountedRef = useRef(true);

  // Load suggestions (with tracking for new ones)
  const loadSuggestions = useCallback(async (isPolling = false) => {
    if (!isMountedRef.current) return;

    try {
      if (!isPolling) {
        setLoading(true);
      }
      setError(null);

      const data = await codexApi.listSuggestions(manuscriptId, 'PENDING');

      if (!isMountedRef.current) return;

      // Track new suggestions since last fetch
      if (isPolling && lastFetchedIds.size > 0) {
        const newIds = data.filter(s => !lastFetchedIds.has(s.id));
        if (newIds.length > 0) {
          setNewSuggestionCount(prev => prev + newIds.length);
        }
      }

      // Update tracked IDs
      setLastFetchedIds(new Set(data.map(s => s.id)));
      setSuggestions(data);
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load suggestions');
      }
    } finally {
      if (isMountedRef.current && !isPolling) {
        setLoading(false);
      }
    }
  }, [manuscriptId, setSuggestions, lastFetchedIds]);

  // Initial load and polling setup
  useEffect(() => {
    isMountedRef.current = true;
    loadSuggestions(false);

    // Set up polling
    pollingRef.current = setInterval(() => {
      loadSuggestions(true);
    }, pollingInterval);

    return () => {
      isMountedRef.current = false;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [manuscriptId, pollingInterval]);

  // Clear new suggestion indicator when user scrolls/interacts
  const clearNewIndicator = useCallback(() => {
    setNewSuggestionCount(0);
  }, []);

  const handleApprove = async (
    suggestion: EntitySuggestion,
    overrides?: { name?: string; type?: EntityType; description?: string }
  ) => {
    try {
      setProcessingId(suggestion.id);
      setError(null);

      const entity = await codexApi.approveSuggestion({
        suggestion_id: suggestion.id,
        name: overrides?.name,
        type: overrides?.type,
        description: overrides?.description,
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

  const handleAddAsAlias = async (suggestion: EntitySuggestion, entityId: string) => {
    try {
      setProcessingId(suggestion.id);
      setError(null);

      // Get the entity
      const entity = entities.find((e) => e.id === entityId);
      if (!entity) {
        setError('Entity not found');
        return;
      }

      // Add suggestion name as alias if not already present
      const newAliases = [...entity.aliases];
      if (!newAliases.includes(suggestion.name) && entity.name !== suggestion.name) {
        newAliases.push(suggestion.name);
      }

      // Update entity with new alias
      const updated = await codexApi.updateEntity(entityId, {
        aliases: newAliases,
      });

      updateEntity(entityId, updated);

      // Reject the suggestion (it's now an alias)
      await codexApi.rejectSuggestion(suggestion.id);
      removeSuggestion(suggestion.id);
    } catch (err) {
      setError('Failed to merge: ' + (err instanceof Error ? err.message : 'Unknown error'));
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
          onClick={() => loadSuggestions(false)}
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
          Start writing and Maxwell will automatically detect characters, locations, and other entities
        </p>
        <p className="text-xs text-faded-ink font-sans mt-2 opacity-70">
          Auto-refreshes every 30 seconds
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3" onClick={clearNewIndicator}>
      {/* Header with new suggestion indicator */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-sans text-faded-ink uppercase">
            Pending Suggestions ({pendingSuggestions.length})
          </h3>
          {newSuggestionCount > 0 && (
            <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold bg-bronze text-white rounded-full animate-pulse">
              +{newSuggestionCount} new
            </span>
          )}
        </div>
        <button
          onClick={() => {
            clearNewIndicator();
            loadSuggestions(false);
          }}
          className="text-sm font-sans text-bronze hover:underline flex items-center gap-1"
          title="Refresh suggestions"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
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
            entities={entities}
            onApprove={(overrides) => handleApprove(suggestion, overrides)}
            onAddAsAlias={(entityId) => handleAddAsAlias(suggestion, entityId)}
            onReject={() => handleReject(suggestion)}
            isProcessing={processingId === suggestion.id}
          />
        ))}
      </div>
    </div>
  );
}
