/**
 * FastCoachSidebar - Sidebar displaying real-time writing suggestions
 * Shows style, word usage, and consistency feedback
 * Enhanced with AI-powered suggestions via OpenRouter
 */

import { FastCoachSidebar as SuggestionsPanel } from '../Editor/plugins/FastCoachPlugin';
import { useFastCoachStore } from '@/stores/fastCoachStore';
import AISuggestionsPanel from './AISuggestionsPanel';
import { useState, useEffect } from 'react';

interface FastCoachSidebarProps {
  manuscriptId: string;
  isOpen: boolean;
  onToggle: () => void;
  currentText?: string;
}

export default function FastCoachSidebar({ manuscriptId, isOpen, onToggle, currentText = '' }: FastCoachSidebarProps) {
  const { suggestions } = useFastCoachStore();
  const [editorText, setEditorText] = useState(currentText);

  // Update editor text when currentText changes
  useEffect(() => {
    setEditorText(currentText);
  }, [currentText]);

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

      {/* AI Suggestions Panel */}
      <div className="overflow-y-auto border-b-2 border-purple-200">
        <AISuggestionsPanel
          text={editorText}
          manuscriptId={manuscriptId}
        />
      </div>

      {/* Rule-based Suggestions panel */}
      <div className="flex-1 overflow-y-auto">
        <SuggestionsPanel
          suggestions={suggestions}
        />
      </div>

      {/* Footer with stats */}
      <div className="p-3 border-t border-slate-ui bg-white text-xs font-sans text-faded-ink">
        <div className="flex items-center justify-between">
          <span>Powered by Fast Coach</span>
          <span>{suggestions.length} active</span>
        </div>
      </div>
    </div>
  );
}
