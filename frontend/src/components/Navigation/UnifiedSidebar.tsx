/**
 * UnifiedSidebar - Left sidebar navigation for all main features
 * Groups items into logical sections: Writing, Reference, Coaching, Tools
 */

import { useState } from 'react';

interface UnifiedSidebarProps {
  currentManuscriptId: string | null;
  manuscriptTitle: string;
  onNavigate: (view: 'chapters' | 'codex' | 'timeline' | 'timemachine' | 'coach' | 'analytics' | 'export' | 'outline') => void;
  onCloseEditor: () => void;
  onSettingsClick?: () => void;
  onAchievementsClick?: () => void;
  activeView?: string;
}

interface NavItem {
  id: string;
  label: string;
  icon: string;
  description: string;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const sections: NavSection[] = [
  {
    label: 'WRITING',
    items: [
      { id: 'chapters', label: 'Chapters', icon: '\u{1F4D1}', description: 'Navigate chapters' },
      { id: 'outline', label: 'Outline', icon: '\u{1F4CB}', description: 'Story structure' },
    ],
  },
  {
    label: 'REFERENCE',
    items: [
      { id: 'codex', label: 'Codex', icon: '\u{1F4D6}', description: 'Characters, world & wiki' },
      { id: 'timeline', label: 'Timeline', icon: '\u{1F4DC}', description: 'Event chronology' },
    ],
  },
  {
    label: 'COACHING',
    items: [
      { id: 'coach', label: 'Coach', icon: '\u2728', description: 'Writing assistance' },
    ],
  },
  {
    label: 'TOOLS',
    items: [
      { id: 'analytics', label: 'Analytics', icon: '\u{1F4CA}', description: 'Stats & recap' },
      { id: 'export', label: 'Export', icon: '\u{1F4E5}', description: 'Export to DOCX/PDF' },
      { id: 'timemachine', label: 'Time Machine', icon: '\u23F0', description: 'Version history' },
    ],
  },
];

export default function UnifiedSidebar({
  currentManuscriptId,
  manuscriptTitle,
  onNavigate,
  onCloseEditor,
  onSettingsClick,
  onAchievementsClick,
  activeView
}: UnifiedSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(true);

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
                  &larr; Back to Library
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
            <div className="flex flex-col items-center gap-2 mx-auto">
              <button
                onClick={onCloseEditor}
                className="text-faded-ink hover:text-midnight transition-colors"
                title="Back to Library"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" />
                </svg>
              </button>
              <button
                onClick={() => setIsExpanded(true)}
                className="text-bronze hover:text-midnight transition-colors"
                title="Expand sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Navigation sections */}
      <nav className="flex-1 overflow-y-auto py-2">
        {sections.map((section, sectionIdx) => (
          <div key={section.label}>
            {/* Section divider */}
            {sectionIdx > 0 && (
              isExpanded ? (
                <div className="border-t border-bronze/15 mx-3 mt-2" />
              ) : (
                <div className="border-t border-bronze/15 mx-2 mt-2" />
              )
            )}

            {/* Section label */}
            {isExpanded ? (
              <div className="px-4 pt-3 pb-1">
                <span className="text-[10px] font-sans font-semibold uppercase tracking-widest text-faded-ink/60">
                  {section.label}
                </span>
              </div>
            ) : (
              <div className="pt-2" />
            )}

            {/* Section items */}
            <div className="px-3 space-y-1">
              {section.items.map((item) => {
                const isActive = activeView === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id as any)}
                    data-tour={`${item.id}-button`}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all
                      ${isActive
                        ? 'bg-bronze text-white shadow-md'
                        : 'text-midnight hover:bg-white/50'
                      }
                      ${!isExpanded && 'justify-center'}
                    `}
                    title={!isExpanded ? item.description : undefined}
                  >
                    <span className="text-lg">{item.icon}</span>
                    {isExpanded && (
                      <div className="flex-1 text-left">
                        <div className="font-sans font-semibold text-sm">{item.label}</div>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom items: Achievements & Settings */}
      <div className="border-t-2 border-bronze/30 p-3 space-y-1">
        {onAchievementsClick && (
          <button
            onClick={onAchievementsClick}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all
              text-midnight hover:bg-white/50
              ${!isExpanded && 'justify-center'}
            `}
            title={!isExpanded ? 'Achievements' : undefined}
          >
            <span className="text-lg">{'\u{1F3C6}'}</span>
            {isExpanded && (
              <div className="flex-1 text-left">
                <div className="font-sans font-semibold text-sm">Achievements</div>
              </div>
            )}
          </button>
        )}
        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-sm transition-all
              text-midnight hover:bg-white/50
              ${!isExpanded && 'justify-center'}
            `}
            title={!isExpanded ? 'Settings' : undefined}
          >
            <span className="text-lg">{'\u2699\uFE0F'}</span>
            {isExpanded && (
              <div className="flex-1 text-left">
                <div className="font-sans font-semibold text-sm">Settings</div>
              </div>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
