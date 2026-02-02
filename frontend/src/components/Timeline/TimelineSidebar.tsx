/**
 * TimelineSidebar - Main timeline sidebar component
 * Tabbed interface for Events and Timeline Graph
 * Note: Issues/Inconsistencies moved to Coach section
 */

import { useTimelineStore } from '@/stores/timelineStore';
import EventList from './EventList';
import InteractiveTimeline from './InteractiveTimeline';
import TimelineHeatmap from './TimelineHeatmap';
import CharacterNetwork from './CharacterNetwork';
import EmotionalArc from './EmotionalArc';
import CharacterLocationTracker from './CharacterLocationTracker';
import ConflictTracker from './ConflictTracker';
import TimelineOrchestrator from './TimelineOrchestrator';
import ForeshadowingTracker from './ForeshadowingTracker';
import { FeatureErrorBoundary } from '@/components/Common';

interface TimelineSidebarProps {
  manuscriptId: string;
  isOpen: boolean;
  onToggle: () => void;
}

export default function TimelineSidebar({
  manuscriptId,
  isOpen,
  onToggle,
}: TimelineSidebarProps) {
  const { activeTab, setActiveTab } = useTimelineStore();

  const tabs: Array<{ id: typeof activeTab; label: string; icon: string; badge?: number }> = [
    { id: 'visual', label: 'Visual', icon: '📜' },
    { id: 'events', label: 'Events', icon: '🎬' },
    { id: 'orchestrator', label: 'Orchestrator', icon: '🎭' },
    { id: 'locations', label: 'Locations', icon: '🗺️' },
    { id: 'conflicts', label: 'Conflicts', icon: '⚔️' },
    { id: 'foreshadow', label: 'Foreshadow', icon: '🔮' },
    { id: 'heatmap', label: 'Heatmap', icon: '🔥' },
    { id: 'network', label: 'Network', icon: '🕸️' },
    { id: 'emotion', label: 'Emotion', icon: '💭' },
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
            title="Open Timeline"
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
                <span className="absolute -top-1 -right-1 bg-redline text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 border-l border-slate-ui bg-vellum flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-slate-ui bg-white p-4 flex items-center justify-between">
        <h2 className="text-xl font-garamond font-bold text-midnight">Timeline</h2>
        <button
          onClick={onToggle}
          className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
          title="Close Timeline"
        >
          ×
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-ui bg-white overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex-shrink-0 px-3 py-3 text-xs font-sans flex items-center justify-center gap-1 relative transition-colors min-w-[70px]
              ${activeTab === tab.id
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            <span className="text-base">{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {tab.badge && tab.badge > 0 && (
              <span className="absolute top-1 right-1 bg-redline text-white text-xs w-4 h-4 flex items-center justify-center rounded-full">
                {tab.badge > 9 ? '9+' : tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'visual' && <InteractiveTimeline manuscriptId={manuscriptId} />}
        {activeTab === 'events' && <EventList manuscriptId={manuscriptId} />}
        {activeTab === 'orchestrator' && <TimelineOrchestrator manuscriptId={manuscriptId} />}
        {activeTab === 'locations' && <CharacterLocationTracker manuscriptId={manuscriptId} />}
        {activeTab === 'conflicts' && <ConflictTracker manuscriptId={manuscriptId} />}
        {activeTab === 'foreshadow' && (
          <FeatureErrorBoundary featureName="Foreshadowing">
            <ForeshadowingTracker manuscriptId={manuscriptId} />
          </FeatureErrorBoundary>
        )}
        {activeTab === 'heatmap' && <TimelineHeatmap manuscriptId={manuscriptId} />}
        {activeTab === 'network' && <CharacterNetwork manuscriptId={manuscriptId} />}
        {activeTab === 'emotion' && <EmotionalArc manuscriptId={manuscriptId} />}
      </div>
    </div>
  );
}
