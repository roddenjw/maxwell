/**
 * FastCoachSidebar - Sidebar displaying real-time writing suggestions
 * Shows style, word usage, consistency feedback, and story issues
 * Enhanced with AI-powered suggestions via OpenRouter
 */

import { useState } from 'react';
import { FastCoachSidebar as SuggestionsPanel } from '../Editor/plugins/FastCoachPlugin';
import { useFastCoachStore } from '@/stores/fastCoachStore';
import { useTimelineStore } from '@/stores/timelineStore';
import AISuggestionsPanel from './AISuggestionsPanel';
import { InconsistencyList } from '../Timeline';

interface FastCoachSidebarProps {
  manuscriptId: string;
  isOpen: boolean;
  onToggle: () => void;
  onNavigateToChapter?: (chapterId: string) => void;
}

type CoachTab = 'suggestions' | 'issues';

export default function FastCoachSidebar({ manuscriptId, isOpen, onToggle, onNavigateToChapter }: FastCoachSidebarProps) {
  const { suggestions } = useFastCoachStore();
  const { inconsistencies } = useTimelineStore();
  const [activeTab, setActiveTab] = useState<CoachTab>('suggestions');

  if (!isOpen) {
    return null;
  }

  return (
    <div className="w-96 border-l border-slate-ui bg-vellum flex-shrink-0 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white flex items-center justify-between">
        <div>
          <h2 className="font-garamond text-xl font-semibold text-midnight">
            Writing Coach
          </h2>
          <p className="text-xs font-sans text-faded-ink mt-1">
            Real-time suggestions & story analysis
          </p>
        </div>
        <button
          onClick={onToggle}
          className="text-faded-ink hover:text-midnight transition-colors p-2"
          title="Close sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-ui bg-white">
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`flex-1 px-4 py-2 text-sm font-sans font-medium transition-colors ${
            activeTab === 'suggestions'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          ✏️ Suggestions
          {suggestions.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-bronze/10 text-bronze rounded">
              {suggestions.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('issues')}
          className={`flex-1 px-4 py-2 text-sm font-sans font-medium transition-colors ${
            activeTab === 'issues'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          ⚠️ Issues
          {inconsistencies.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-redline/10 text-redline rounded">
              {inconsistencies.length}
            </span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'suggestions' && (
        <>
          {/* AI Suggestions Panel */}
          <div className="overflow-y-auto border-b-2 border-purple-200">
            <AISuggestionsPanel
              manuscriptId={manuscriptId}
            />
          </div>

          {/* Rule-based Suggestions panel */}
          <div className="flex-1 overflow-y-auto">
            <SuggestionsPanel
              suggestions={suggestions}
            />
          </div>
        </>
      )}

      {activeTab === 'issues' && (
        <div className="flex-1 overflow-y-auto">
          <InconsistencyList
            manuscriptId={manuscriptId}
            onNavigateToChapter={onNavigateToChapter}
          />
        </div>
      )}

      {/* Footer with stats */}
      <div className="p-3 border-t border-slate-ui bg-white text-xs font-sans text-faded-ink">
        <div className="flex items-center justify-between">
          <span>Powered by Writing Coach</span>
          <span>
            {activeTab === 'suggestions'
              ? `${suggestions.length} suggestions`
              : `${inconsistencies.length} issues`
            }
          </span>
        </div>
      </div>
    </div>
  );
}
