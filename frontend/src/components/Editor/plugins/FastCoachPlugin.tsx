/**
 * FastCoachPlugin - Real-time writing suggestions
 * Provides instant feedback as you type without AI API calls
 */

import { useEffect, useCallback, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot } from 'lexical';
import { useFastCoachStore, type Suggestion } from '@/stores/fastCoachStore';

interface FastCoachProps {
  manuscriptId?: string;
  enabled?: boolean;
}

export default function FastCoachPlugin({ manuscriptId, enabled = true }: FastCoachProps) {
  const [editor] = useLexicalComposerContext();
  const { setSuggestions, setIsAnalyzing } = useFastCoachStore();

  // Debounced analysis
  const analyzText = useCallback(
    async (text: string) => {
      if (!enabled || text.length < 50) {
        setSuggestions([]);
        return;
      }

      try {
        setIsAnalyzing(true);

        const response = await fetch('http://localhost:8000/api/fast-coach/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text,
            manuscript_id: manuscriptId || null,
            check_consistency: !!manuscriptId,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setSuggestions(data.suggestions || []);
        }
      } catch (error) {
        console.error('Fast Coach analysis failed:', error);
        setSuggestions([]);
      } finally {
        setIsAnalyzing(false);
      }
    },
    [manuscriptId, enabled]
  );

  // Register editor update listener
  useEffect(() => {
    if (!enabled) {
      setSuggestions([]);
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;

    const removeUpdateListener = editor.registerUpdateListener(({ editorState }) => {
      // Clear previous timeout
      clearTimeout(timeoutId);

      // Debounce: wait 1 second after typing stops
      timeoutId = setTimeout(() => {
        editorState.read(() => {
          const root = $getRoot();
          const text = root.getTextContent();
          analyzText(text);
        });
      }, 1000);
    });

    return () => {
      removeUpdateListener();
      clearTimeout(timeoutId);
    };
  }, [editor, analyzText, enabled]);

  // Don't render anything in the editor - suggestions shown in sidebar
  // This plugin only handles the analysis logic
  return null;
}

/**
 * FastCoachSidebar - Display suggestions in a sidebar
 * Separate component to show the suggestions
 */
interface FastCoachSidebarProps {
  suggestions: Suggestion[];
  onDismiss?: (index: number) => void;
}

export function FastCoachSidebar({ suggestions, onDismiss }: FastCoachSidebarProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (suggestions.length === 0) {
    return (
      <div className="p-4 text-center">
        <div className="text-faded-ink text-sm font-sans">
          ✨ No suggestions yet. Keep writing!
        </div>
      </div>
    );
  }

  // Group by type (requested by user)
  const groupedByType = suggestions.reduce((acc, suggestion) => {
    const type = suggestion.type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(suggestion);
    return acc;
  }, {} as Record<string, Suggestion[]>);

  // Sort groups by severity priority (ERROR > WARNING > INFO)
  const sortedTypes = Object.keys(groupedByType).sort((a, b) => {
    const severityOrder = { ERROR: 0, WARNING: 1, INFO: 2 };
    const aSeverity = groupedByType[a][0]?.severity || 'INFO';
    const bSeverity = groupedByType[b][0]?.severity || 'INFO';
    return severityOrder[aSeverity as keyof typeof severityOrder] - severityOrder[bSeverity as keyof typeof severityOrder];
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-ui bg-white sticky top-0 z-10">
        <h3 className="font-garamond text-lg font-semibold text-midnight">
          Writing Coach
        </h3>
        <p className="text-xs font-sans text-faded-ink mt-1">
          {suggestions.length} {suggestions.length === 1 ? 'suggestion' : 'suggestions'}
        </p>
      </div>

      <div className="p-4 space-y-4">
        {/* Group by type of tip */}
        {sortedTypes.map((type, typeIdx) => {
          const typeSuggestions = groupedByType[type];
          const firstSeverity = typeSuggestions[0]?.severity || 'INFO';

          // Icon and color based on severity
          const severityConfig = {
            ERROR: { icon: '🔴', color: 'text-red-600', label: 'Issues' },
            WARNING: { icon: '⚡', color: 'text-orange-600', label: 'Warnings' },
            INFO: { icon: '💡', color: 'text-blue-600', label: 'Tips' },
          };

          const config = severityConfig[firstSeverity as keyof typeof severityConfig];
          const typeLabel = type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

          // Calculate global index offset for this group
          const globalOffset = sortedTypes
            .slice(0, typeIdx)
            .reduce((sum, t) => sum + groupedByType[t].length, 0);

          return (
            <div key={type}>
              <div className={`text-xs font-sans font-semibold ${config.color} mb-2 flex items-center gap-1`}>
                <span>{config.icon}</span>
                <span>{typeLabel}</span>
                <span className="text-faded-ink">({typeSuggestions.length})</span>
              </div>
              {typeSuggestions.map((suggestion, idx) => {
                const globalIdx = globalOffset + idx;
                return (
                  <SuggestionCard
                    key={`${type}-${idx}`}
                    suggestion={suggestion}
                    index={globalIdx}
                    isExpanded={expandedIndex === globalIdx}
                    onToggle={() => setExpandedIndex(expandedIndex === globalIdx ? null : globalIdx)}
                    onDismiss={onDismiss}
                  />
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface SuggestionCardProps {
  suggestion: Suggestion;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  onDismiss?: (index: number) => void;
}

function SuggestionCard({ suggestion, index, isExpanded, onToggle, onDismiss }: SuggestionCardProps) {
  const severityColors = {
    ERROR: 'border-red-200 bg-red-50',
    WARNING: 'border-orange-200 bg-orange-50',
    INFO: 'border-blue-200 bg-blue-50',
  };

  const severityIcons = {
    ERROR: '🔴',
    WARNING: '🟠',
    INFO: '🔵',
  };

  return (
    <div
      className={`border ${severityColors[suggestion.severity as keyof typeof severityColors]} rounded p-3 mb-2 cursor-pointer transition-all hover:shadow-sm`}
      onClick={onToggle}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{severityIcons[suggestion.severity as keyof typeof severityIcons]}</span>
            <span className="text-xs font-sans font-semibold text-midnight capitalize">
              {suggestion.type.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-sm font-sans text-midnight font-medium">
            {suggestion.message}
          </p>
        </div>

        {onDismiss && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDismiss(index);
            }}
            className="text-faded-ink hover:text-midnight ml-2"
            title="Dismiss"
          >
            ×
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          {suggestion.suggestion && (
            <p className="text-sm font-sans text-faded-ink italic mb-3">
              💡 {suggestion.suggestion}
            </p>
          )}

          {suggestion.highlight_word && (
            <div className="mt-2 text-xs font-mono bg-white px-2 py-1 rounded border border-gray-200 inline-block">
              Flagged text: <span className="font-semibold text-bronze">{suggestion.highlight_word}</span>
            </div>
          )}

          {suggestion.metadata && Object.keys(suggestion.metadata).length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-sans font-semibold text-faded-ink mb-1">
                Additional Details:
              </div>
              <div className="text-xs font-sans bg-white p-2 rounded border border-gray-200 space-y-1">
                {Object.entries(suggestion.metadata).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="font-semibold text-midnight capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-faded-ink">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TODO: Add "Jump to text" button here once we implement text location tracking */}
          <div className="mt-3 text-xs text-faded-ink italic">
            💭 Click the suggestion to view details. Text location tracking coming soon.
          </div>
        </div>
      )}
    </div>
  );
}
