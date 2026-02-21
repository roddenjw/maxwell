/**
 * TimelineIssuesPanel - Display timeline inconsistencies with suggestions and teaching points
 */

import { useState } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { toast } from '@/stores/toastStore';
import { getSeverityColor, getSeverityIcon, Severity } from '@/types/timeline';
import type { TimelineInconsistency } from '@/types/timeline';

interface TimelineIssuesPanelProps {
  manuscriptId: string;
}

export default function TimelineIssuesPanel({ }: TimelineIssuesPanelProps) {
  const { getFilteredInconsistencies, showTeachingMoments, resolveInconsistency } = useTimelineStore();
  const [selectedIssue, setSelectedIssue] = useState<TimelineInconsistency | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<Severity | 'ALL'>('ALL');

  const filteredIssues = getFilteredInconsistencies();

  const issuesBySeverity = filteredIssues.filter((issue) =>
    severityFilter === 'ALL' || issue.severity === severityFilter
  );

  const highCount = filteredIssues.filter((i) => i.severity === 'HIGH').length;
  const mediumCount = filteredIssues.filter((i) => i.severity === 'MEDIUM').length;
  const lowCount = filteredIssues.filter((i) => i.severity === 'LOW').length;

  const handleResolve = async () => {
    if (!selectedIssue) return;

    try {
      setResolving(true);
      await resolveInconsistency(selectedIssue.id, resolutionNotes);
      setSelectedIssue(null);
      setResolutionNotes('');
    } catch (error) {
      toast.error('Failed to resolve issue: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Issues List */}
      <div className="flex-1 flex flex-col border-r border-slate-ui">
        {/* Severity Filter Tabs */}
        <div className="flex border-b border-slate-ui bg-white">
          <button
            onClick={() => setSeverityFilter('ALL')}
            className={`px-4 py-2 text-sm font-sans transition-colors flex items-center gap-1 ${
              severityFilter === 'ALL'
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
            }`}
          >
            All <span className="text-xs">({filteredIssues.length})</span>
          </button>
          <button
            onClick={() => setSeverityFilter(Severity.HIGH)}
            className={`px-4 py-2 text-sm font-sans transition-colors flex items-center gap-1 ${
              severityFilter === Severity.HIGH
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
            }`}
          >
            {getSeverityIcon(Severity.HIGH)} High <span className="text-xs">({highCount})</span>
          </button>
          <button
            onClick={() => setSeverityFilter(Severity.MEDIUM)}
            className={`px-4 py-2 text-sm font-sans transition-colors flex items-center gap-1 ${
              severityFilter === Severity.MEDIUM
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
            }`}
          >
            {getSeverityIcon(Severity.MEDIUM)} Medium <span className="text-xs">({mediumCount})</span>
          </button>
          <button
            onClick={() => setSeverityFilter(Severity.LOW)}
            className={`px-4 py-2 text-sm font-sans transition-colors flex items-center gap-1 ${
              severityFilter === Severity.LOW
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
            }`}
          >
            {getSeverityIcon(Severity.LOW)} Low <span className="text-xs">({lowCount})</span>
          </button>
        </div>

        {/* Issues */}
        <div className="flex-1 overflow-y-auto p-4">
          {issuesBySeverity.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center">
              <div className="text-4xl mb-3">✅</div>
              <p className="text-midnight font-garamond font-semibold mb-2">
                {filteredIssues.length === 0 ? 'No issues found' : `No ${severityFilter.toLowerCase()} severity issues`}
              </p>
              <p className="text-sm text-faded-ink font-sans max-w-xs">
                {filteredIssues.length === 0
                  ? 'Your timeline looks good! Run validation to check for issues.'
                  : 'Try a different severity filter.'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {issuesBySeverity.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => setSelectedIssue(issue)}
                  className={`w-full text-left border bg-white p-3 transition-all hover:shadow-md ${
                    selectedIssue?.id === issue.id
                      ? 'border-bronze ring-2 ring-bronze'
                      : 'border-slate-ui'
                  }`}
                  style={{ borderRadius: '2px' }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1">
                      <span className="text-base">{getSeverityIcon(issue.severity)}</span>
                      <span
                        className="text-xs font-sans px-2 py-0.5 text-white"
                        style={{
                          backgroundColor: getSeverityColor(issue.severity),
                          borderRadius: '2px',
                        }}
                      >
                        {issue.severity}
                      </span>
                      <span className="text-xs font-sans text-faded-ink uppercase">
                        {issue.inconsistency_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    {issue.is_resolved && (
                      <span className="text-xs font-sans px-2 py-0.5 bg-green-100 text-green-800" style={{ borderRadius: '2px' }}>
                        ✓ Resolved
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-serif text-midnight line-clamp-2">
                    {issue.description}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedIssue && (
        <div className="w-96 flex flex-col bg-vellum">
          <div className="p-4 border-b border-slate-ui bg-white flex items-start justify-between">
            <h3 className="text-lg font-garamond font-bold text-midnight">Issue Details</h3>
            <button
              onClick={() => setSelectedIssue(null)}
              className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
            >
              ×
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Issue Header */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{getSeverityIcon(selectedIssue.severity)}</span>
                <span
                  className="text-xs font-sans px-2 py-1 text-white"
                  style={{
                    backgroundColor: getSeverityColor(selectedIssue.severity),
                    borderRadius: '2px',
                  }}
                >
                  {selectedIssue.severity}
                </span>
                <span className="text-xs font-sans text-faded-ink uppercase">
                  {selectedIssue.inconsistency_type.replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-sm font-serif text-midnight">
                {selectedIssue.description}
              </p>
            </div>

            {/* Suggestions */}
            {selectedIssue.suggestion && (
              <div className="border border-slate-ui bg-white p-3" style={{ borderRadius: '2px' }}>
                <h4 className="text-sm font-sans font-semibold text-bronze mb-2">💡 Suggestions</h4>
                <p className="text-sm font-serif text-midnight whitespace-pre-line">
                  {selectedIssue.suggestion}
                </p>
              </div>
            )}

            {/* Teaching Point */}
            {showTeachingMoments && selectedIssue.teaching_point && (
              <div className="border border-bronze bg-white p-3" style={{ borderRadius: '2px' }}>
                <h4 className="text-sm font-sans font-semibold text-bronze mb-2">📚 Why This Matters</h4>
                <p className="text-sm font-serif text-midnight whitespace-pre-line">
                  {selectedIssue.teaching_point}
                </p>
              </div>
            )}

            {/* Resolution Notes (if already resolved) */}
            {selectedIssue.is_resolved && selectedIssue.resolution_notes && (
              <div className="border border-green-200 bg-green-50 p-3" style={{ borderRadius: '2px' }}>
                <h4 className="text-sm font-sans font-semibold text-green-800 mb-2">✓ Resolution</h4>
                <p className="text-sm font-serif text-midnight whitespace-pre-line">
                  {selectedIssue.resolution_notes}
                </p>
                {selectedIssue.resolved_at && (
                  <p className="text-xs text-faded-ink font-sans mt-2">
                    Resolved: {new Date(selectedIssue.resolved_at).toLocaleString()}
                  </p>
                )}
              </div>
            )}

            {/* Resolution Form (if not resolved) */}
            {!selectedIssue.is_resolved && (
              <div className="border border-slate-ui bg-white p-3" style={{ borderRadius: '2px' }}>
                <h4 className="text-sm font-sans font-semibold text-midnight mb-2">Mark as Resolved</h4>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="How did you address this issue? (optional)"
                  className="w-full border border-slate-ui p-2 text-sm font-serif text-midnight resize-none"
                  style={{ borderRadius: '2px' }}
                  rows={3}
                />
                <button
                  onClick={handleResolve}
                  disabled={resolving}
                  className="w-full mt-2 bg-bronze text-white px-4 py-2 text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  {resolving ? 'Resolving...' : 'Mark as Resolved'}
                </button>
              </div>
            )}

            {/* Metadata */}
            <div className="text-xs text-faded-ink font-sans space-y-1">
              <p>Detected: {new Date(selectedIssue.created_at).toLocaleString()}</p>
              {selectedIssue.affected_event_ids.length > 0 && (
                <p>Affects {selectedIssue.affected_event_ids.length} event{selectedIssue.affected_event_ids.length > 1 ? 's' : ''}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
