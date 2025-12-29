/**
 * UnifiedSidebar - Left sidebar navigation for all main features
 * Replaces scattered navigation buttons across the app
 */

import { useState } from 'react';

interface UnifiedSidebarProps {
  currentManuscriptId: string | null;
  manuscriptTitle: string;
  onNavigate: (view: 'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'recap' | 'analytics' | 'export') => void;
  onCloseEditor: () => void;
  activeView?: string;
}

export default function UnifiedSidebar({
  currentManuscriptId,
  manuscriptTitle,
  onNavigate,
  onCloseEditor,
  activeView
}: UnifiedSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const navigationItems = [
    { id: 'chapters', label: 'Chapters', icon: '📑', description: 'Navigate chapters' },
    { id: 'codex', label: 'Codex', icon: '📖', description: 'Character & world info' },
    { id: 'timeline', label: 'Timeline', icon: '📜', description: 'Event chronology' },
    { id: 'analytics', label: 'Analytics', icon: '📊', description: 'Writing statistics' },
    { id: 'export', label: 'Export', icon: '📥', description: 'Export to DOCX/PDF' },
    { id: 'timemachine', label: 'Time Machine', icon: '⏰', description: 'Version history' },
    { id: 'coach', label: 'Coach', icon: '✨', description: 'Writing assistance' },
    { id: 'recap', label: 'Recap', icon: '🎯', description: 'Progress summary' },
  ];

  if (!currentManuscriptId) {
    return null;
  }

  return (
    <div
      className={`
        ${isExpanded ? 'w-64' : 'w-16'}
        transition-all duration-300 bg-gradient-to-b from-[#e8dcc8] to-[#f5f1e8]
        border-r-2 border-bronze/30 flex flex-col shadow-lg
      `}
    >
      {/* Header */}
      <div className="border-b-2 border-bronze/30 p-4">
        <div className="flex items-center justify-between">
          {isExpanded ? (
            <>
              <div>
                <h2 className="font-garamond font-bold text-midnight text-lg truncate">
                  {manuscriptTitle}
                </h2>
                <button
                  onClick={onCloseEditor}
                  className="text-xs font-sans text-faded-ink hover:text-midnight transition-colors mt-1"
                >
                  ← Back to Library
                </button>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="text-bronze hover:text-midnight transition-colors"
                title="Collapse sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsExpanded(true)}
              className="text-bronze hover:text-midnight transition-colors mx-auto"
              title="Expand sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 p-3 space-y-2 overflow-y-auto">
        {navigationItems.map((item) => {
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id as any)}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-sm transition-all
                ${isActive
                  ? 'bg-bronze text-white shadow-md'
                  : 'text-midnight hover:bg-white/50'
                }
                ${!isExpanded && 'justify-center'}
              `}
              title={!isExpanded ? item.description : undefined}
            >
              <span className="text-xl">{item.icon}</span>
              {isExpanded && (
                <div className="flex-1 text-left">
                  <div className="font-sans font-semibold text-sm">{item.label}</div>
                  {!isActive && (
                    <div className="text-xs opacity-70">{item.description}</div>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer decoration */}
      <div className="border-t-2 border-bronze/30 p-3">
        {isExpanded ? (
          <div className="text-center">
            <div className="w-16 h-2 bg-bronze/20 rounded-full mx-auto"></div>
          </div>
        ) : (
          <div className="w-8 h-2 bg-bronze/20 rounded-full mx-auto"></div>
        )}
      </div>
    </div>
  );
}
