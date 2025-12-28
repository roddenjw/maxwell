/**
 * FastCoachSidebar - Sidebar displaying real-time writing suggestions
 * Shows style, word usage, and consistency feedback
 */

import { useState } from 'react';
import { FastCoachSidebar as SuggestionsPanel } from '../Editor/plugins/FastCoachPlugin';
import { useFastCoachStore } from '@/stores/fastCoachStore';

interface FastCoachSidebarProps {
  manuscriptId: string;
  isOpen: boolean;
  onToggle: () => void;
}

export default function FastCoachSidebar({ isOpen, onToggle }: FastCoachSidebarProps) {
  const { suggestions } = useFastCoachStore();
  const [dismissedIndices, setDismissedIndices] = useState<Set<number>>(new Set());

  const handleDismiss = (index: number) => {
    setDismissedIndices(prev => new Set([...prev, index]));
  };

  // Filter out dismissed suggestions
  const visibleSuggestions = suggestions.filter((_, idx) => !dismissedIndices.has(idx));

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
            Real-time suggestions
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

      {/* Suggestions panel */}
      <div className="flex-1 overflow-y-auto">
        <SuggestionsPanel
          suggestions={visibleSuggestions}
          onDismiss={handleDismiss}
        />
      </div>

      {/* Footer with stats */}
      <div className="p-3 border-t border-slate-ui bg-white text-xs font-sans text-faded-ink">
        <div className="flex items-center justify-between">
          <span>Powered by Fast Coach</span>
          <span>{visibleSuggestions.length} active</span>
        </div>
      </div>
    </div>
  );
}
