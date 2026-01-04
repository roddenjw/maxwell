/**
 * FastCoachPlugin - Real-time writing suggestions
 * Provides instant feedback as you type without AI API calls
 */

import { useEffect, useCallback, useState, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useFastCoachStore, type Suggestion, getSuggestionId } from '@/stores/fastCoachStore';
import { jumpToTextPosition, getEditorPlainText, replaceTextAtPosition } from '@/lib/editorUtils';

interface FastCoachProps {
  manuscriptId?: string;
  enabled?: boolean;
}

export default function FastCoachPlugin({ manuscriptId, enabled = true }: FastCoachProps) {
  const [editor] = useLexicalComposerContext();
  const {
    setSuggestions,
    setIsAnalyzing,
    setCurrentEditorText,
    jumpRequest,
    clearJumpRequest,
    isSidebarOpen,
    applyReplacementRequest,
    clearApplyReplacementRequest
  } = useFastCoachStore();

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
    [manuscriptId, enabled, setSuggestions, setIsAnalyzing]
  );

  // Auto-analyze when sidebar opens (only once when it first opens)
  const hasAnalyzedOnOpen = useRef(false);

  useEffect(() => {
    // Add a small delay to ensure editor content is fully rendered
    if (enabled && isSidebarOpen && !hasAnalyzedOnOpen.current) {
      const timeoutId = setTimeout(() => {
        try {
          const text = getEditorPlainText(editor);
          if (text.length >= 50) {
            analyzText(text);
            hasAnalyzedOnOpen.current = true;
          }
        } catch (error) {
          console.error('Fast Coach auto-analysis error:', error);
        }
      }, 100); // 100ms delay to ensure content is loaded

      return () => clearTimeout(timeoutId);
    }

    // Reset when sidebar closes
    if (!isSidebarOpen) {
      hasAnalyzedOnOpen.current = false;
    }
  }, [enabled, isSidebarOpen, editor, analyzText]);

  // Register editor update listener
  useEffect(() => {
    if (!enabled) {
      setSuggestions([]);
      setCurrentEditorText('');
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;

    const removeUpdateListener = editor.registerUpdateListener(() => {
      // Extract text immediately for AI panel
      const text = getEditorPlainText(editor);
      setCurrentEditorText(text);

      // Clear previous timeout
      clearTimeout(timeoutId);

      // Debounce: wait 1 second after typing stops for analysis
      timeoutId = setTimeout(() => {
        analyzText(text);
      }, 1000);
    });

    return () => {
      removeUpdateListener();
      clearTimeout(timeoutId);
    };
  }, [editor, analyzText, enabled, setCurrentEditorText]);

  // Handle jump-to-text requests from Fast Coach UI
  useEffect(() => {
    if (
      jumpRequest &&
      jumpRequest.startChar !== undefined &&
      jumpRequest.endChar !== undefined &&
      typeof jumpRequest.startChar === 'number' &&
      typeof jumpRequest.endChar === 'number' &&
      jumpRequest.startChar >= 0 &&
      jumpRequest.endChar > jumpRequest.startChar
    ) {
      // Execute the jump
      jumpToTextPosition(editor, jumpRequest.startChar, jumpRequest.endChar);

      // Clear the request after handling
      clearJumpRequest();
    }
  }, [jumpRequest, editor, clearJumpRequest]);

  // Handle apply replacement requests from Fast Coach UI
  useEffect(() => {
    if (
      applyReplacementRequest &&
      applyReplacementRequest.startChar !== undefined &&
      applyReplacementRequest.endChar !== undefined &&
      applyReplacementRequest.replacement !== undefined &&
      typeof applyReplacementRequest.startChar === 'number' &&
      typeof applyReplacementRequest.endChar === 'number' &&
      applyReplacementRequest.startChar >= 0 &&
      applyReplacementRequest.endChar > applyReplacementRequest.startChar
    ) {
      try {
        // Execute the replacement
        replaceTextAtPosition(
          editor,
          applyReplacementRequest.startChar,
          applyReplacementRequest.endChar,
          applyReplacementRequest.replacement
        );
      } catch (error) {
        console.error('Fast Coach replacement error:', error);
      } finally {
        // Always clear the request
        clearApplyReplacementRequest();
      }
    }
  }, [applyReplacementRequest, editor, clearApplyReplacementRequest]);

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
}

export function FastCoachSidebar({ suggestions }: FastCoachSidebarProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const {
    filterTypes,
    filterSeverities,
    collapsedSections,
    sortBy,
    dismissedSuggestionIds,
    toggleFilterType,
    toggleFilterSeverity,
    clearFilters,
    toggleSectionCollapsed,
    setSortBy,
    clearDismissed,
  } = useFastCoachStore();

  // Apply filters (including dismissed suggestions)
  const filteredSuggestions = suggestions.filter((suggestion) => {
    // Check if dismissed
    const id = getSuggestionId(suggestion);
    if (dismissedSuggestionIds.has(id)) {
      return false;
    }

    // Type filter
    if (filterTypes.size > 0 && !filterTypes.has(suggestion.type)) {
      return false;
    }
    // Severity filter
    if (filterSeverities.size > 0 && !filterSeverities.has(suggestion.severity)) {
      return false;
    }
    return true;
  });

  // Get unique types and severities for filter controls
  const availableTypes = Array.from(new Set(suggestions.map(s => s.type)));
  const availableSeverities = ['ERROR', 'WARNING', 'INFO'].filter(sev =>
    suggestions.some(s => s.severity === sev)
  );

  // Calculate stats
  const dismissedCount = suggestions.filter(s => dismissedSuggestionIds.has(getSuggestionId(s))).length;
  const stats = {
    total: suggestions.length,
    filtered: filteredSuggestions.length,
    dismissed: dismissedCount,
    byType: suggestions.reduce((acc, s) => {
      acc[s.type] = (acc[s.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    bySeverity: suggestions.reduce((acc, s) => {
      acc[s.severity] = (acc[s.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
  };

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
  const groupedByType = filteredSuggestions.reduce((acc, suggestion) => {
    const type = suggestion.type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(suggestion);
    return acc;
  }, {} as Record<string, Suggestion[]>);

  // Sort groups based on sortBy setting
  const sortedTypes = Object.keys(groupedByType).sort((a, b) => {
    if (sortBy === 'severity') {
      const severityOrder = { ERROR: 0, WARNING: 1, INFO: 2 };
      const aSeverity = groupedByType[a][0]?.severity || 'INFO';
      const bSeverity = groupedByType[b][0]?.severity || 'INFO';
      return severityOrder[aSeverity as keyof typeof severityOrder] - severityOrder[bSeverity as keyof typeof severityOrder];
    } else if (sortBy === 'type') {
      return a.localeCompare(b);
    } else {
      // position - keep original order
      return 0;
    }
  });

  return (
    <div className="h-full overflow-y-auto">
      {/* Stats Summary Panel */}
      <div className="p-4 border-b border-slate-ui bg-gradient-to-r from-bronze/5 to-transparent sticky top-0 z-20">
        <h3 className="font-garamond text-lg font-semibold text-midnight mb-2">
          Writing Coach
        </h3>

        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="bg-white rounded p-2 border border-slate-ui">
            <div className="text-xs font-sans text-faded-ink">Total</div>
            <div className="text-lg font-garamond font-semibold text-midnight">{stats.total}</div>
          </div>
          <div className="bg-white rounded p-2 border border-slate-ui">
            <div className="text-xs font-sans text-faded-ink">Showing</div>
            <div className="text-lg font-garamond font-semibold text-bronze">{stats.filtered}</div>
          </div>
          <div className="bg-white rounded p-2 border border-slate-ui">
            <div className="text-xs font-sans text-faded-ink">Dismissed</div>
            <div className="text-lg font-garamond font-semibold text-faded-ink">{stats.dismissed}</div>
          </div>
        </div>

        {/* Clear dismissed button */}
        {stats.dismissed > 0 && (
          <div className="mb-2">
            <button
              onClick={clearDismissed}
              className="w-full text-xs font-sans text-bronze hover:text-bronze/80 bg-bronze/10 hover:bg-bronze/20 rounded px-3 py-2 transition-colors"
            >
              Restore {stats.dismissed} dismissed suggestion{stats.dismissed !== 1 ? 's' : ''}
            </button>
          </div>
        )}

        {/* Severity badges */}
        <div className="flex gap-2 mb-2">
          {stats.bySeverity.ERROR && (
            <span className="text-xs font-sans bg-red-100 text-red-700 px-2 py-1 rounded">
              🔴 {stats.bySeverity.ERROR} errors
            </span>
          )}
          {stats.bySeverity.WARNING && (
            <span className="text-xs font-sans bg-orange-100 text-orange-700 px-2 py-1 rounded">
              ⚡ {stats.bySeverity.WARNING} warnings
            </span>
          )}
          {stats.bySeverity.INFO && (
            <span className="text-xs font-sans bg-blue-100 text-blue-700 px-2 py-1 rounded">
              💡 {stats.bySeverity.INFO} tips
            </span>
          )}
        </div>
      </div>

      {/* Filter Controls */}
      <div className="p-4 border-b border-slate-ui bg-white sticky top-[180px] z-10">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-sans font-semibold text-midnight uppercase tracking-wide">Filters</h4>
          {(filterTypes.size > 0 || filterSeverities.size > 0) && (
            <button
              onClick={clearFilters}
              className="text-xs font-sans text-bronze hover:text-bronze/80 underline"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Sort options */}
        <div className="mb-3">
          <label className="text-xs font-sans text-faded-ink block mb-1">Sort by:</label>
          <div className="flex gap-1">
            {(['severity', 'type', 'position'] as const).map((option) => (
              <button
                key={option}
                onClick={() => setSortBy(option)}
                className={`text-xs font-sans px-2 py-1 rounded transition-colors ${
                  sortBy === option
                    ? 'bg-bronze text-white'
                    : 'bg-slate-100 text-faded-ink hover:bg-slate-200'
                }`}
              >
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Severity filters */}
        {availableSeverities.length > 0 && (
          <div className="mb-3">
            <label className="text-xs font-sans text-faded-ink block mb-1">Severity:</label>
            <div className="flex flex-wrap gap-1">
              {availableSeverities.map((severity) => {
                const isSelected = filterSeverities.has(severity);
                const severityConfig = {
                  ERROR: { bg: 'bg-red-100', text: 'text-red-700', icon: '🔴' },
                  WARNING: { bg: 'bg-orange-100', text: 'text-orange-700', icon: '⚡' },
                  INFO: { bg: 'bg-blue-100', text: 'text-blue-700', icon: '💡' },
                };
                const config = severityConfig[severity as keyof typeof severityConfig];
                return (
                  <button
                    key={severity}
                    onClick={() => toggleFilterSeverity(severity)}
                    className={`text-xs font-sans px-2 py-1 rounded transition-all ${
                      isSelected
                        ? `${config.bg} ${config.text} ring-2 ring-offset-1 ring-current`
                        : 'bg-slate-100 text-faded-ink hover:bg-slate-200'
                    }`}
                  >
                    <span className="mr-1">{config.icon}</span>
                    {severity}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Type filters */}
        {availableTypes.length > 0 && (
          <div>
            <label className="text-xs font-sans text-faded-ink block mb-1">Type:</label>
            <div className="flex flex-wrap gap-1">
              {availableTypes.map((type) => {
                const isSelected = filterTypes.has(type);
                const typeLabel = type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <button
                    key={type}
                    onClick={() => toggleFilterType(type)}
                    className={`text-xs font-sans px-2 py-1 rounded transition-all ${
                      isSelected
                        ? 'bg-bronze text-white ring-2 ring-offset-1 ring-bronze'
                        : 'bg-slate-100 text-faded-ink hover:bg-slate-200'
                    }`}
                  >
                    {typeLabel}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Suggestions List */}
      <div className="p-4 space-y-4">
        {filteredSuggestions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm font-sans text-faded-ink">
              No suggestions match your filters.
            </p>
          </div>
        ) : (
          <>
            {/* Group by type of tip */}
            {sortedTypes.map((type, typeIdx) => {
              const typeSuggestions = groupedByType[type];
              const firstSeverity = typeSuggestions[0]?.severity || 'INFO';
              const isCollapsed = collapsedSections.has(type);

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
                  {/* Collapsible Section Header */}
                  <button
                    onClick={() => toggleSectionCollapsed(type)}
                    className={`w-full text-xs font-sans font-semibold ${config.color} mb-2 flex items-center gap-2 hover:opacity-70 transition-opacity`}
                  >
                    <span className="transform transition-transform" style={{ display: 'inline-block', transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>
                      ▼
                    </span>
                    <span>{config.icon}</span>
                    <span>{typeLabel}</span>
                    <span className="text-faded-ink">({typeSuggestions.length})</span>
                  </button>

                  {!isCollapsed && typeSuggestions.map((suggestion, idx) => {
                    const globalIdx = globalOffset + idx;
                    return (
                      <SuggestionCard
                        key={`${type}-${idx}`}
                        suggestion={suggestion}
                        index={globalIdx}
                        isExpanded={expandedIndex === globalIdx}
                        onToggle={() => setExpandedIndex(expandedIndex === globalIdx ? null : globalIdx)}
                      />
                    );
                  })}
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}

interface SuggestionCardProps {
  suggestion: Suggestion;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function SuggestionCard({ suggestion, isExpanded, onToggle }: SuggestionCardProps) {
  const { requestJumpToText, dismissSuggestion, requestApplyReplacement } = useFastCoachStore();

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

  const handleJumpToText = (e: React.MouseEvent) => {
    e.stopPropagation(); // Don't trigger card toggle
    if (
      suggestion.start_char !== undefined &&
      suggestion.end_char !== undefined &&
      suggestion.start_char !== null &&
      suggestion.end_char !== null &&
      typeof suggestion.start_char === 'number' &&
      typeof suggestion.end_char === 'number' &&
      suggestion.start_char >= 0 &&
      suggestion.end_char > suggestion.start_char
    ) {
      requestJumpToText(suggestion.start_char, suggestion.end_char);
    }
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

        <button
          onClick={(e) => {
            e.stopPropagation();
            dismissSuggestion(suggestion);
          }}
          className="text-faded-ink hover:text-midnight ml-2"
          title="Dismiss"
        >
          ×
        </button>
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

          {/* Action buttons */}
          <div className="mt-3 space-y-2">
            {/* Apply Replacement button - only show if we have replacement text */}
            {suggestion.replacement !== undefined &&
             suggestion.replacement !== null &&
             suggestion.start_char !== undefined &&
             suggestion.end_char !== undefined &&
             suggestion.start_char !== null &&
             suggestion.end_char !== null &&
             typeof suggestion.start_char === 'number' &&
             typeof suggestion.end_char === 'number' &&
             suggestion.start_char >= 0 &&
             suggestion.end_char > suggestion.start_char && (
              <div className="bg-slate-50 border border-slate-200 rounded p-3">
                <div className="text-xs font-sans font-semibold text-midnight mb-1">
                  Suggested replacement:
                </div>
                <div className="text-sm font-mono bg-white px-2 py-1 rounded border border-slate-200 mb-2 text-midnight">
                  {suggestion.replacement === '' ? <span className="text-faded-ink italic">(remove)</span> : suggestion.replacement}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (suggestion.start_char !== undefined && suggestion.end_char !== undefined && suggestion.replacement !== undefined) {
                      requestApplyReplacement(suggestion.start_char, suggestion.end_char, suggestion.replacement);
                      dismissSuggestion(suggestion);
                    }
                  }}
                  className="w-full px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm font-sans font-medium flex items-center justify-center gap-2"
                >
                  <span>✓</span>
                  <span>Apply Suggestion</span>
                </button>
              </div>
            )}

            {/* Jump to Text button - only show if we have valid position data */}
            {suggestion.start_char !== undefined &&
             suggestion.end_char !== undefined &&
             suggestion.start_char !== null &&
             suggestion.end_char !== null &&
             typeof suggestion.start_char === 'number' &&
             typeof suggestion.end_char === 'number' &&
             suggestion.start_char >= 0 &&
             suggestion.end_char > suggestion.start_char && (
              <button
                onClick={handleJumpToText}
                className="w-full px-3 py-2 bg-bronze text-white rounded hover:bg-bronze/90 transition-colors text-sm font-sans font-medium flex items-center justify-center gap-2"
              >
                <span>📍</span>
                <span>Jump to Text</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
