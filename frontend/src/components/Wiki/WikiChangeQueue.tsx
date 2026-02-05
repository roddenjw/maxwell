/**
 * WikiChangeQueue Component
 * Review and approve/reject AI-suggested wiki changes
 */

import { useState, useEffect, useCallback } from 'react';
import type { WikiChange } from '../../types/wiki';

const API_BASE = 'http://localhost:8000';

interface WikiChangeQueueProps {
  worldId: string;
  manuscriptId?: string;
  onClose: () => void;
}

interface PendingSummary {
  total_pending: number;
  by_type: Record<string, number>;
  average_confidence: number;
  high_confidence_count: number;
}

export function WikiChangeQueue({ worldId, manuscriptId, onClose }: WikiChangeQueueProps) {
  const [changes, setChanges] = useState<WikiChange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [filterType, setFilterType] = useState<string | null>(null);
  const [summary, setSummary] = useState<PendingSummary | null>(null);
  const [selectedChanges, setSelectedChanges] = useState<Set<string>>(new Set());

  // Fetch pending changes
  const fetchChanges = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/wiki/worlds/${worldId}/changes?limit=100`
      );
      if (!response.ok) throw new Error('Failed to fetch changes');

      const data = await response.json();
      setChanges(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load changes');
    } finally {
      setIsLoading(false);
    }
  }, [worldId]);

  // Fetch summary
  const fetchSummary = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/wiki/worlds/${worldId}/pending-summary`
      );
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch {
      // Ignore summary errors
    }
  }, [worldId]);

  useEffect(() => {
    fetchChanges();
    fetchSummary();
  }, [fetchChanges, fetchSummary]);

  // Trigger manuscript analysis
  const handleAnalyzeManuscript = async () => {
    if (!manuscriptId) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/wiki/auto-populate/manuscript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manuscript_id: manuscriptId,
          world_id: worldId
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');

      const result = await response.json();

      // Refresh changes and summary
      await fetchChanges();
      await fetchSummary();

      // Show success message (could use toast)
      console.log('Analysis complete:', result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Toggle change selection
  const toggleSelection = (changeId: string) => {
    setSelectedChanges(prev => {
      const next = new Set(prev);
      if (next.has(changeId)) {
        next.delete(changeId);
      } else {
        next.add(changeId);
      }
      return next;
    });
  };

  // Select/deselect all
  const toggleSelectAll = () => {
    if (selectedChanges.size === filteredChanges.length) {
      setSelectedChanges(new Set());
    } else {
      setSelectedChanges(new Set(filteredChanges.map(c => c.id)));
    }
  };

  // Filter changes by type
  const filteredChanges = filterType
    ? changes.filter(c => c.change_type === filterType)
    : changes;

  // Approve change
  const handleApprove = async (changeId: string, note?: string) => {
    setProcessingId(changeId);
    try {
      const response = await fetch(
        `${API_BASE}/wiki/changes/${changeId}/approve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reviewer_note: note }),
        }
      );

      if (!response.ok) throw new Error('Failed to approve');

      setChanges((prev) => prev.filter((c) => c.id !== changeId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    } finally {
      setProcessingId(null);
    }
  };

  // Reject change
  const handleReject = async (changeId: string, note?: string) => {
    setProcessingId(changeId);
    try {
      const response = await fetch(
        `${API_BASE}/wiki/changes/${changeId}/reject`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reviewer_note: note }),
        }
      );

      if (!response.ok) throw new Error('Failed to reject');

      setChanges((prev) => prev.filter((c) => c.id !== changeId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject');
    } finally {
      setProcessingId(null);
    }
  };

  // Approve selected
  const handleApproveSelected = async () => {
    const toApprove = selectedChanges.size > 0
      ? Array.from(selectedChanges)
      : filteredChanges.map(c => c.id);

    for (const changeId of toApprove) {
      await handleApprove(changeId);
    }
    setSelectedChanges(new Set());
  };

  // Reject selected
  const handleRejectSelected = async () => {
    const toReject = selectedChanges.size > 0
      ? Array.from(selectedChanges)
      : filteredChanges.map(c => c.id);

    for (const changeId of toReject) {
      await handleReject(changeId);
    }
    setSelectedChanges(new Set());
  };

  // Auto-approve high confidence
  const handleAutoApprove = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/wiki/worlds/${worldId}/auto-approve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ threshold: 0.95 }),
        }
      );

      if (!response.ok) throw new Error('Auto-approve failed');

      const result = await response.json();

      // Refresh changes
      await fetchChanges();
      await fetchSummary();

      console.log('Auto-approved:', result.approved_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auto-approve failed');
    }
  };

  const getChangeTypeLabel = (type: string) => {
    switch (type) {
      case 'create':
        return { label: 'New Entry', color: 'bg-green-100 text-green-700' };
      case 'update':
        return { label: 'Update', color: 'bg-blue-100 text-blue-700' };
      case 'delete':
        return { label: 'Delete', color: 'bg-red-100 text-red-700' };
      case 'merge':
        return { label: 'Merge', color: 'bg-purple-100 text-purple-700' };
      default:
        return { label: type, color: 'bg-gray-100 text-gray-700' };
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                Approval Queue
              </h2>
              <p className="text-sm text-gray-500">
                Review AI-suggested changes to your world wiki
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Summary Stats */}
          {summary && summary.total_pending > 0 && (
            <div className="mt-3 flex items-center gap-4 text-sm">
              <span className="text-gray-600">
                {summary.total_pending} pending
              </span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-600">
                Avg. confidence: {Math.round(summary.average_confidence * 100)}%
              </span>
              {summary.high_confidence_count > 0 && (
                <>
                  <span className="text-gray-400">|</span>
                  <span className="text-green-600">
                    {summary.high_confidence_count} high-confidence
                  </span>
                </>
              )}
            </div>
          )}

          {/* Toolbar */}
          <div className="mt-3 flex items-center justify-between">
            {/* Filters */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Filter:</span>
              <button
                onClick={() => setFilterType(null)}
                className={`px-2 py-1 text-xs rounded ${
                  filterType === null
                    ? 'bg-gray-700 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType('create')}
                className={`px-2 py-1 text-xs rounded ${
                  filterType === 'create'
                    ? 'bg-green-600 text-white'
                    : 'bg-green-50 text-green-700 hover:bg-green-100'
                }`}
              >
                New ({summary?.by_type?.create || 0})
              </button>
              <button
                onClick={() => setFilterType('update')}
                className={`px-2 py-1 text-xs rounded ${
                  filterType === 'update'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                }`}
              >
                Update ({summary?.by_type?.update || 0})
              </button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {manuscriptId && (
                <button
                  onClick={handleAnalyzeManuscript}
                  disabled={isAnalyzing}
                  className="px-3 py-1 text-sm bg-amber-100 text-amber-700 rounded hover:bg-amber-200 disabled:opacity-50"
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Manuscript'}
                </button>
              )}
              {summary && summary.high_confidence_count > 0 && (
                <button
                  onClick={handleAutoApprove}
                  className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  Auto-Approve High Confidence
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading changes...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-red-500">{error}</div>
            </div>
          ) : filteredChanges.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <span className="text-4xl mb-2">✓</span>
              <p>No pending changes</p>
              <p className="text-sm">
                {manuscriptId ? 'Click "Analyze Manuscript" to detect wiki updates' : 'All caught up!'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {/* Select All Header */}
              <div className="px-4 py-2 bg-gray-50 flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedChanges.size === filteredChanges.length && filteredChanges.length > 0}
                  onChange={toggleSelectAll}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-600">
                  {selectedChanges.size > 0
                    ? `${selectedChanges.size} selected`
                    : 'Select all'}
                </span>
              </div>

              {filteredChanges.map((change) => {
                const typeInfo = getChangeTypeLabel(change.change_type);
                const isProcessing = processingId === change.id;

                return (
                  <div key={change.id} className="p-4">
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <input
                        type="checkbox"
                        checked={selectedChanges.has(change.id)}
                        onChange={() => toggleSelection(change.id)}
                        className="mt-1 rounded border-gray-300"
                      />

                      <div className="flex-1 min-w-0 flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                        {/* Change Type Badge */}
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className={`px-2 py-0.5 text-xs font-medium rounded ${typeInfo.color}`}
                          >
                            {typeInfo.label}
                          </span>
                          <span className="text-sm text-gray-500">
                            Confidence: {Math.round(change.confidence * 100)}%
                          </span>
                        </div>

                        {/* Change Details */}
                        {change.change_type === 'create' && change.proposed_entry && (
                          <div className="mb-3">
                            <h3 className="font-medium text-gray-800">
                              {change.proposed_entry.title}
                            </h3>
                            <p className="text-sm text-gray-500">
                              Type: {change.proposed_entry.entry_type?.replace(/_/g, ' ')}
                            </p>
                            {change.proposed_entry.summary && (
                              <p className="text-sm text-gray-600 mt-1">
                                {change.proposed_entry.summary}
                              </p>
                            )}
                          </div>
                        )}

                        {change.change_type === 'update' && (
                          <div className="mb-3">
                            <p className="text-sm text-gray-600">
                              <span className="font-medium">Field: </span>
                              {change.field_changed || 'Multiple fields'}
                            </p>
                            {change.old_value && (
                              <div className="mt-2 p-2 bg-red-50 rounded text-sm">
                                <span className="text-red-600 font-medium">Old: </span>
                                <span className="text-red-700">
                                  {typeof change.old_value === 'string'
                                    ? change.old_value
                                    : JSON.stringify(change.old_value, null, 2)}
                                </span>
                              </div>
                            )}
                            <div className="mt-1 p-2 bg-green-50 rounded text-sm">
                              <span className="text-green-600 font-medium">New: </span>
                              <span className="text-green-700">
                                {typeof change.new_value === 'string'
                                  ? change.new_value
                                  : JSON.stringify(change.new_value, null, 2)}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* AI Reasoning */}
                        {change.reason && (
                          <div className="mt-2 p-3 bg-amber-50 rounded">
                            <p className="text-xs font-medium text-amber-700 mb-1">
                              AI Reasoning:
                            </p>
                            <p className="text-sm text-amber-800">{change.reason}</p>
                          </div>
                        )}

                        {/* Source Text */}
                        {change.source_text && (
                          <div className="mt-2 p-3 bg-gray-50 rounded">
                            <p className="text-xs font-medium text-gray-500 mb-1">
                              Source Text:
                            </p>
                            <p className="text-sm text-gray-700 italic">
                              "{change.source_text}"
                            </p>
                          </div>
                        )}
                      </div>

                        {/* Actions */}
                        <div className="flex flex-col gap-2">
                          <button
                            onClick={() => handleApprove(change.id)}
                            disabled={isProcessing}
                            className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            {isProcessing ? '...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => handleReject(change.id)}
                            disabled={isProcessing}
                            className="px-4 py-2 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200 disabled:opacity-50"
                          >
                            {isProcessing ? '...' : 'Reject'}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {filteredChanges.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {selectedChanges.size > 0
                ? `${selectedChanges.size} of ${filteredChanges.length} selected`
                : `${filteredChanges.length} pending change${filteredChanges.length !== 1 ? 's' : ''}`
              }
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={handleRejectSelected}
                disabled={processingId !== null}
                className="px-4 py-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
              >
                {selectedChanges.size > 0 ? 'Reject Selected' : 'Reject All'}
              </button>
              <button
                onClick={handleApproveSelected}
                disabled={processingId !== null}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {selectedChanges.size > 0 ? 'Approve Selected' : 'Approve All'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
