/**
 * CodexSidebar - Main sidebar component for The Codex
 * Tabbed interface for Entities, Intel (suggestions), and Links (relationships)
 */

import type { CodexTab } from '@/types/codex';
import { useCodexStore } from '@/stores/codexStore';
import { useTimelineStore } from '@/stores/timelineStore';
import EntityList from './EntityList';
import SuggestionQueue from './SuggestionQueue';
import RelationshipGraph from './RelationshipGraph';
import { EventList, InconsistencyList, TimelineGraph } from '../Timeline';

interface CodexSidebarProps {
  manuscriptId: string;
  isOpen: boolean;
  onToggle: () => void;
}

export default function CodexSidebar({
  manuscriptId,
  isOpen,
  onToggle,
}: CodexSidebarProps) {
  const {
    activeTab,
    setActiveTab,
    getPendingSuggestionsCount,
  } = useCodexStore();

  const { inconsistencies } = useTimelineStore();

  const pendingCount = getPendingSuggestionsCount();
  const inconsistencyCount = inconsistencies.length;

  const tabs: { id: CodexTab; label: string; icon: string; badge?: number }[] = [
    { id: 'entities', label: 'Entities', icon: '📝' },
    { id: 'intel', label: 'Intel', icon: '🔍', badge: pendingCount },
    { id: 'links', label: 'Links', icon: '🕸️' },
    { id: 'timeline', label: 'Events', icon: '🎬' },
    { id: 'timeline-issues', label: 'Issues', icon: '⚠️', badge: inconsistencyCount },
    { id: 'timeline-graph', label: 'Timeline', icon: '📅' },
  ];

  if (!isOpen) {
    return (
      <div className="border-l border-slate-ui bg-vellum">
        {/* Collapsed state - vertical tab buttons */}
        <div className="flex flex-col items-center gap-2 p-2">
          <button
            onClick={onToggle}
            className="w-10 h-10 flex items-center justify-center text-bronze hover:bg-white transition-colors"
            style={{ borderRadius: '2px' }}
            title="Open Codex"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                onToggle();
              }}
              className="w-10 h-10 flex items-center justify-center relative hover:bg-white transition-colors"
              style={{ borderRadius: '2px' }}
              title={tab.label}
            >
              <span className="text-xl">{tab.icon}</span>
              {tab.badge && tab.badge > 0 && (
                <span className="absolute -top-1 -right-1 bg-bronze text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  }

  const handleExport = async (format: 'markdown' | 'json') => {
    try {
      const url = `/api/codex/export/${manuscriptId}?format=${format}`;
      window.open(`http://localhost:8000${url}`, '_blank');
    } catch (err) {
      alert('Failed to export: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  return (
    <div className="w-96 border-l border-slate-ui bg-vellum flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-slate-ui bg-white p-4 flex items-center justify-between">
        <h2 className="text-xl font-garamond font-bold text-midnight">The Codex</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('markdown')}
            className="text-sm font-sans text-bronze hover:underline"
            title="Export Codex as Markdown"
          >
            📥 Export
          </button>
          <button
            onClick={onToggle}
            className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
            title="Close Codex"
          >
            ×
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-ui bg-white">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex-1 px-4 py-3 text-sm font-sans flex items-center justify-center gap-2 relative transition-colors
              ${activeTab === tab.id
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.badge && tab.badge > 0 && (
              <span className="absolute top-1 right-1 bg-bronze text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'entities' && <EntityList manuscriptId={manuscriptId} />}
        {activeTab === 'intel' && <SuggestionQueue manuscriptId={manuscriptId} />}
        {activeTab === 'links' && <RelationshipGraph manuscriptId={manuscriptId} />}
        {activeTab === 'timeline' && <EventList manuscriptId={manuscriptId} />}
        {activeTab === 'timeline-issues' && <InconsistencyList manuscriptId={manuscriptId} />}
        {activeTab === 'timeline-graph' && <TimelineGraph manuscriptId={manuscriptId} />}
      </div>
    </div>
  );
}
