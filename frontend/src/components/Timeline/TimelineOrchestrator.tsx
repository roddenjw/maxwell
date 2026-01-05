/**
 * TimelineOrchestrator - Main container for Timeline Orchestrator features
 * Comprehensive timeline validation with teaching-first approach
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import TimelineControls from './TimelineControls';
import TimelineIssuesPanel from './TimelineIssuesPanel';
import TimelineTeachingPanel from './TimelineTeachingPanel';
import TimelineVisualization from './TimelineVisualization';

interface TimelineOrchestratorProps {
  manuscriptId: string;
}

export default function TimelineOrchestrator({ manuscriptId }: TimelineOrchestratorProps) {
  const { loadComprehensiveData, inconsistencies } = useTimelineStore();
  const [activeView, setActiveView] = useState<'timeline' | 'issues' | 'teaching'>('timeline');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        await loadComprehensiveData(manuscriptId);
      } catch (error) {
        console.error('Failed to load timeline data:', error);
        setError(error instanceof Error ? error.message : 'Failed to load timeline data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [manuscriptId, loadComprehensiveData]);

  const pendingIssues = inconsistencies.filter((i) => !i.is_resolved).length;
  const issuesWithTeaching = inconsistencies.filter((i) => i.teaching_point && !i.is_resolved).length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 gap-3">
        <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
        <p className="text-faded-ink font-sans text-sm">Loading Timeline Orchestrator...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 gap-3">
        <div className="text-4xl mb-2">⚠️</div>
        <h3 className="text-lg font-garamond font-bold text-midnight">Error Loading Timeline</h3>
        <p className="text-sm text-faded-ink font-sans text-center max-w-md">
          {error}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-bronze/90 transition-colors"
          style={{ borderRadius: '2px' }}
        >
          Reload Page
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Controls */}
      <TimelineControls
        manuscriptId={manuscriptId}
        onValidate={() => {
          // Optionally switch to issues view after validation
          if (pendingIssues > 0) {
            setActiveView('issues');
          }
        }}
        showTeachingToggle={activeView === 'issues'}
      />

      {/* View Tabs */}
      <div className="flex border-b border-slate-ui bg-white">
        <button
          onClick={() => setActiveView('timeline')}
          className={`px-4 py-3 text-sm font-sans transition-colors flex items-center gap-2 ${
            activeView === 'timeline'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          <span className="text-base">📜</span>
          <span>Timeline</span>
        </button>
        <button
          onClick={() => setActiveView('issues')}
          className={`px-4 py-3 text-sm font-sans transition-colors flex items-center gap-2 relative ${
            activeView === 'issues'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          <span className="text-base">⚠️</span>
          <span>Issues</span>
          {pendingIssues > 0 && (
            <span className="bg-redline text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
              {pendingIssues > 9 ? '9+' : pendingIssues}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveView('teaching')}
          className={`px-4 py-3 text-sm font-sans transition-colors flex items-center gap-2 relative ${
            activeView === 'teaching'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          <span className="text-base">📚</span>
          <span>Teaching</span>
          {issuesWithTeaching > 0 && (
            <span className="bg-bronze text-white text-xs px-2 h-5 flex items-center justify-center" style={{ borderRadius: '10px' }}>
              {issuesWithTeaching}
            </span>
          )}
        </button>
      </div>

      {/* View Content */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'timeline' && <TimelineVisualization manuscriptId={manuscriptId} />}
        {activeView === 'issues' && <TimelineIssuesPanel manuscriptId={manuscriptId} />}
        {activeView === 'teaching' && <TimelineTeachingPanel manuscriptId={manuscriptId} />}
      </div>
    </div>
  );
}
