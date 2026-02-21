/**
 * InconsistencyList - Display timeline inconsistencies and allow resolution
 * Enhanced with expandable items, resolution tracking, and type grouping
 */

import { useState, useEffect, useMemo } from 'react';
import { Severity, getSeverityColor, getSeverityIcon, TimelineInconsistency } from '@/types/timeline';
import { timelineApi } from '@/lib/api';
import { useTimelineStore } from '@/stores/timelineStore';
import { toast } from '@/stores/toastStore';

interface InconsistencyListProps {
  manuscriptId: string;
  onNavigateToChapter?: (chapterId: string) => void;
}

type ViewMode = 'list' | 'grouped';

export default function InconsistencyList({ manuscriptId, onNavigateToChapter }: InconsistencyListProps) {
  const { inconsistencies, setInconsistencies, removeInconsistency } = useTimelineStore();
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<Severity | 'ALL'>('ALL');
  const [viewMode, setViewMode] = useState<ViewMode>('grouped');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [collapsedTypes, setCollapsedTypes] = useState<Set<string>>(new Set());
  const [resolutionNotes, setResolutionNotes] = useState<Map<string, string>>(new Map());
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  useEffect(() => {
    loadInconsistencies();
  }, [manuscriptId]);

  const loadInconsistencies = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await timelineApi.listInconsistencies(manuscriptId);
      setInconsistencies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load inconsistencies');
    } finally {
      setLoading(false);
    }
  };

  const handleDetect = async () => {
    try {
      setDetecting(true);
      setError(null);
      const result = await timelineApi.detectInconsistencies(manuscriptId);
      setInconsistencies(result);
    } catch (err) {
      setError('Failed to detect inconsistencies: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setDetecting(false);
    }
  };

  const handleResolve = async (inconsistencyId: string) => {
    const note = resolutionNotes.get(inconsistencyId) || '';

    try {
      setResolvingId(inconsistencyId);
      await timelineApi.resolveInconsistency(inconsistencyId, note);
      removeInconsistency(inconsistencyId);
      // Clear the note after resolution
      const newNotes = new Map(resolutionNotes);
      newNotes.delete(inconsistencyId);
      setResolutionNotes(newNotes);
    } catch (err) {
      toast.error('Failed to resolve inconsistency: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setResolvingId(null);
    }
  };

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  const toggleTypeCollapse = (type: string) => {
    const newCollapsed = new Set(collapsedTypes);
    if (newCollapsed.has(type)) {
      newCollapsed.delete(type);
    } else {
      newCollapsed.add(type);
    }
    setCollapsedTypes(newCollapsed);
  };

  const updateResolutionNote = (id: string, note: string) => {
    const newNotes = new Map(resolutionNotes);
    newNotes.set(id, note);
    setResolutionNotes(newNotes);
  };

  const filteredInconsistencies = inconsistencies.filter((inc) => {
    return filterSeverity === 'ALL' || inc.severity === filterSeverity;
  });

  // Group inconsistencies by type
  const groupedInconsistencies = useMemo(() => {
    const groups: Record<string, TimelineInconsistency[]> = {};
    filteredInconsistencies.forEach((inc) => {
      const type = inc.inconsistency_type;
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(inc);
    });
    // Sort groups by count (highest first)
    return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  }, [filteredInconsistencies]);

  const renderInconsistencyCard = (inc: TimelineInconsistency) => {
    const isExpanded = expandedIds.has(inc.id);
    const isResolving = resolvingId === inc.id;
    const note = resolutionNotes.get(inc.id) || '';

    return (
      <div
        key={inc.id}
        className={`border border-slate-ui bg-white transition-all ${
          isExpanded ? 'shadow-md' : ''
        }`}
        style={{ borderRadius: '2px' }}
      >
        {/* Collapsed Header - Always visible */}
        <button
          onClick={() => toggleExpand(inc.id)}
          className="w-full p-3 text-left hover:bg-slate-ui/10 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className="text-lg flex-shrink-0">{getSeverityIcon(inc.severity)}</span>
              <span
                className="text-xs font-sans px-2 py-0.5 text-white flex-shrink-0"
                style={{
                  backgroundColor: getSeverityColor(inc.severity),
                  borderRadius: '2px',
                }}
              >
                {inc.severity}
              </span>
              <p className="text-sm font-serif text-midnight truncate">
                {inc.description}
              </p>
            </div>
            <svg
              className={`w-5 h-5 text-faded-ink flex-shrink-0 ml-2 transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-slate-ui/50">
            {/* Full Description */}
            <div className="mt-3">
              <h4 className="text-xs font-sans font-semibold text-faded-ink uppercase mb-1">
                Description
              </h4>
              <p className="text-sm font-serif text-midnight">
                {inc.description}
              </p>
            </div>

            {/* Metadata */}
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div>
                <h4 className="text-xs font-sans font-semibold text-faded-ink uppercase mb-1">
                  Type
                </h4>
                <p className="text-sm font-sans text-midnight">
                  {inc.inconsistency_type.replace(/_/g, ' ')}
                </p>
              </div>
              <div>
                <h4 className="text-xs font-sans font-semibold text-faded-ink uppercase mb-1">
                  Detected
                </h4>
                <p className="text-sm font-sans text-midnight">
                  {new Date(inc.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {inc.affected_event_ids.length > 0 && (
              <div className="mt-3">
                <h4 className="text-xs font-sans font-semibold text-faded-ink uppercase mb-1">
                  Affected Events
                </h4>
                <p className="text-sm font-sans text-midnight">
                  {inc.affected_event_ids.length} event{inc.affected_event_ids.length > 1 ? 's' : ''} affected
                </p>
              </div>
            )}

            {/* Jump to Chapter */}
            {inc.source_chapter_id && onNavigateToChapter && (
              <div className="mt-3">
                <button
                  onClick={() => onNavigateToChapter(inc.source_chapter_id!)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-sans text-bronze hover:text-white hover:bg-bronze border border-bronze transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Jump to Chapter
                </button>
              </div>
            )}

            {/* Resolution Section */}
            <div className="mt-4 pt-3 border-t border-slate-ui">
              <h4 className="text-xs font-sans font-semibold text-faded-ink uppercase mb-2">
                Resolution Notes (optional)
              </h4>
              <textarea
                value={note}
                onChange={(e) => updateResolutionNote(inc.id, e.target.value)}
                placeholder="Add notes about how you resolved this issue..."
                className="w-full px-3 py-2 text-sm font-sans border border-slate-ui focus:border-bronze focus:outline-none resize-none"
                style={{ borderRadius: '2px' }}
                rows={2}
              />
              <div className="flex justify-end mt-2">
                <button
                  onClick={() => handleResolve(inc.id)}
                  disabled={isResolving}
                  className="px-4 py-2 text-sm font-sans font-medium bg-green-600 hover:bg-green-700 text-white transition-colors disabled:opacity-50 flex items-center gap-2"
                  style={{ borderRadius: '2px' }}
                >
                  {isResolving && (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  )}
                  {isResolving ? 'Resolving...' : '✓ Mark as Resolved'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading issues...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui">
        <button
          onClick={handleDetect}
          disabled={detecting}
          className="w-full bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 flex items-center justify-center gap-2"
          style={{ borderRadius: '2px' }}
        >
          {detecting && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
          {detecting ? 'Detecting...' : '🔍 Detect Issues'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-redline/10 border-b border-redline">
          <p className="text-sm font-sans text-redline">{error}</p>
        </div>
      )}

      {/* View Mode Toggle + Severity Filter */}
      <div className="border-b border-slate-ui bg-white">
        {/* View Mode Toggle */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-slate-ui/50">
          <span className="text-xs font-sans font-semibold text-faded-ink uppercase">View:</span>
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode('grouped')}
              className={`px-3 py-1 text-xs font-sans transition-colors ${
                viewMode === 'grouped'
                  ? 'bg-bronze text-white'
                  : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
              }`}
              style={{ borderRadius: '2px' }}
            >
              Grouped
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 text-xs font-sans transition-colors ${
                viewMode === 'list'
                  ? 'bg-bronze text-white'
                  : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
              }`}
              style={{ borderRadius: '2px' }}
            >
              List
            </button>
          </div>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex overflow-x-auto">
          {['ALL', ...Object.values(Severity)].map((severity) => (
            <button
              key={severity}
              onClick={() => setFilterSeverity(severity as Severity | 'ALL')}
              className={`
                px-4 py-2 text-xs font-sans whitespace-nowrap transition-colors flex items-center gap-1
                ${filterSeverity === severity
                  ? 'text-bronze border-b-2 border-bronze'
                  : 'text-faded-ink hover:text-midnight'
                }
              `}
            >
              {severity !== 'ALL' && getSeverityIcon(severity as Severity)}
              <span>{severity}</span>
              <span className="ml-1 opacity-70">
                ({severity === 'ALL' ? inconsistencies.length : inconsistencies.filter((i) => i.severity === severity).length})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Inconsistency List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredInconsistencies.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="text-4xl mb-3">✅</div>
            <p className="text-midnight font-garamond font-semibold mb-2">
              {inconsistencies.length === 0
                ? 'No issues detected'
                : `No ${filterSeverity.toLowerCase()} severity issues`}
            </p>
            <p className="text-sm text-faded-ink font-sans max-w-xs">
              {inconsistencies.length === 0
                ? 'Your story is consistent! Click "Detect Issues" to check again.'
                : 'Try a different severity filter.'}
            </p>
          </div>
        ) : viewMode === 'grouped' ? (
          // Grouped View
          <div className="space-y-4">
            {groupedInconsistencies.map(([type, items]) => {
              const isCollapsed = collapsedTypes.has(type);
              const typeLabel = type.replace(/_/g, ' ');

              return (
                <div key={type} className="border border-slate-ui bg-vellum" style={{ borderRadius: '2px' }}>
                  {/* Group Header */}
                  <button
                    onClick={() => toggleTypeCollapse(type)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-ui/20 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-sans font-semibold text-midnight capitalize">
                        {typeLabel}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-sans bg-bronze/20 text-bronze rounded-full">
                        {items.length}
                      </span>
                    </div>
                    <svg
                      className={`w-5 h-5 text-faded-ink transition-transform ${
                        isCollapsed ? '' : 'rotate-180'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Group Items */}
                  {!isCollapsed && (
                    <div className="p-3 pt-0 space-y-2">
                      {items.map((inc) => renderInconsistencyCard(inc))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          // List View
          <div className="space-y-2">
            {filteredInconsistencies.map((inc) => renderInconsistencyCard(inc))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-slate-ui bg-white text-xs font-sans text-faded-ink flex items-center justify-between">
        <span>
          {filteredInconsistencies.length} issue{filteredInconsistencies.length !== 1 ? 's' : ''}
          {filterSeverity !== 'ALL' && ` (${filterSeverity.toLowerCase()})`}
        </span>
        <span className="text-bronze">
          {expandedIds.size > 0 && `${expandedIds.size} expanded`}
        </span>
      </div>
    </div>
  );
}
