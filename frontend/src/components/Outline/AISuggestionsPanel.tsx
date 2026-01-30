/**
 * AISuggestionsPanel Component
 * Side panel for AI-powered outline analysis and suggestions
 * Powered by Claude 3.5 Sonnet via OpenRouter (BYOK pattern)
 */

import { useState, useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import type { Outline } from '@/types/outline';
import { Z_INDEX } from '@/lib/zIndex';

interface AISuggestionsPanelProps {
  outline: Outline;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'settings' | 'beat_ideas' | 'plot_holes' | 'pacing';

export default function AISuggestionsPanel({ outline, isOpen, onClose }: AISuggestionsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('settings');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [selectedAnalyses, setSelectedAnalyses] = useState<string[]>([
    'beat_descriptions',
    'plot_holes',
    'pacing',
  ]);
  const [severityFilter, setSeverityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [expandedFeedback, setExpandedFeedback] = useState<string | null>(null);

  const {
    aiSuggestions,
    isAnalyzing,
    apiKey,
    setApiKey,
    getApiKey,
    runAIAnalysis,
    runAIAnalysisWithFeedback,
    updateBeat,
    clearAISuggestions,
    markPlotHoleResolved,
    beatFeedback,
    addBeatFeedbackLike,
    addBeatFeedbackDislike,
    setBeatFeedbackNotes,
    clearBeatFeedback,
    hasFeedback,
  } = useOutlineStore();

  // Check for existing API key on mount and switch to beat ideas tab if found
  useEffect(() => {
    const existingKey = getApiKey();
    if (existingKey && existingKey.trim()) {
      // User already has an API key, show them the beat ideas tab
      setActiveTab('beat_ideas');
    }
  }, []);

  if (!isOpen) return null;

  const hasApiKey = !!getApiKey();
  const hasResults = !!aiSuggestions;

  const handleSaveApiKey = () => {
    if (apiKeyInput.trim()) {
      setApiKey(apiKeyInput.trim());
      setApiKeyInput('');
      // Auto-switch to beat ideas tab after setting key
      if (!hasResults) {
        setActiveTab('beat_ideas');
      }
    }
  };

  const handleRunAnalysis = async () => {
    if (!hasApiKey) {
      setActiveTab('settings');
      return;
    }

    try {
      await runAIAnalysis(outline.id, selectedAnalyses);
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  const handleApplyBeatDescription = async (beatName: string, description: string) => {
    const beat = outline.plot_beats.find((b) => b.beat_name === beatName);
    if (!beat) return;

    try {
      await updateBeat(beat.id, { beat_description: description });
    } catch (error) {
      console.error('Failed to apply description:', error);
    }
  };

  const filteredPlotHoles =
    aiSuggestions?.plot_holes?.filter((hole) => {
      if (severityFilter === 'all') return !hole.resolved;
      return hole.severity === severityFilter && !hole.resolved;
    }) || [];

  const resolvedCount = aiSuggestions?.plot_holes?.filter((h) => h.resolved).length || 0;

  return (
    <div
      className="fixed right-0 top-0 h-full bg-white border-l-2 border-slate-ui shadow-2xl flex flex-col transition-transform duration-300"
      style={{
        width: '420px',
        transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
        zIndex: Z_INDEX.SLIDE_PANEL,
      }}
    >
      {/* Header */}
      <div className="flex-shrink-0 border-b-2 border-slate-ui bg-vellum p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🤖</span>
            <h2 className="font-serif font-bold text-xl text-midnight">AI Insights</h2>
          </div>
          <div className="flex items-center gap-2">
            {hasResults && (
              <button
                onClick={handleRunAnalysis}
                disabled={isAnalyzing}
                className="px-3 py-1 text-xs font-sans font-medium uppercase tracking-button bg-bronze hover:bg-bronze-dark text-white transition-colors disabled:opacity-50"
                style={{ borderRadius: '2px' }}
                title="Refresh AI analysis"
              >
                {isAnalyzing ? '⏳' : '🔄'}
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center hover:bg-slate-ui/30 text-faded-ink hover:text-midnight transition-colors"
              style={{ borderRadius: '2px' }}
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 border-b border-slate-ui bg-white">
        <div className="flex">
          {[
            { id: 'settings', label: '⚙️ Settings', enabled: true },
            { id: 'beat_ideas', label: '💡 Beat Ideas', enabled: hasApiKey },
            { id: 'plot_holes', label: '🔍 Plot Holes', enabled: hasApiKey },
            { id: 'pacing', label: '📈 Pacing', enabled: hasApiKey },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => tab.enabled && setActiveTab(tab.id as TabType)}
              disabled={!tab.enabled}
              className={`flex-1 px-3 py-3 text-xs font-sans font-semibold uppercase tracking-wider transition-colors ${
                activeTab === tab.id
                  ? 'bg-bronze text-white border-b-2 border-bronze'
                  : tab.enabled
                  ? 'text-faded-ink hover:text-midnight hover:bg-slate-ui/20'
                  : 'text-slate-ui/50 cursor-not-allowed'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto relative">
        {/* Loading Overlay */}
        {isAnalyzing && (
          <div
            className="absolute inset-0 bg-white/95 flex items-center justify-center z-50"
            style={{ borderRadius: '2px' }}
          >
            <div className="text-center max-w-sm p-6">
              <div className="text-6xl mb-4 animate-pulse">🤖</div>
              <h3 className="font-serif text-xl font-bold text-midnight mb-2">
                Analyzing Your Outline...
              </h3>
              <p className="text-sm font-sans text-faded-ink mb-4">
                This may take 30-60 seconds
              </p>
              <div className="w-full h-2 bg-slate-ui/30 rounded-full overflow-hidden">
                <div className="h-full bg-bronze animate-pulse" style={{ width: '60%' }} />
              </div>
              <p className="text-xs font-sans text-faded-ink mt-3">
                Estimated cost: $0.01-0.05
              </p>
              <p className="text-xs font-sans text-purple-600 mt-2 font-medium">
                {selectedAnalyses.length === 0
                  ? 'Running all analysis types'
                  : `Running: ${selectedAnalyses.join(', ')}`}
              </p>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="p-6 space-y-6">
            <div>
              <h3 className="font-serif text-lg font-bold text-midnight mb-2">OpenRouter API Key</h3>
              <p className="text-sm font-sans text-faded-ink mb-4">
                Maxwell uses your own API key (BYOK pattern). Get one at{' '}
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-bronze hover:underline"
                >
                  openrouter.ai/keys
                </a>
              </p>

              {hasApiKey ? (
                <div className="p-4 bg-green-500/10 border-l-4 border-green-500" style={{ borderRadius: '2px' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green-600 text-lg">✓</span>
                    <span className="font-sans font-semibold text-green-700">API Key Saved</span>
                  </div>
                  <p className="text-sm text-green-600 mb-3">
                    Key: {apiKey?.substring(0, 12)}...{apiKey?.substring(apiKey.length - 4)}
                  </p>
                  <button
                    onClick={() => {
                      setApiKey('');
                      localStorage.removeItem('openrouter_api_key');
                    }}
                    className="text-sm font-sans text-red-600 hover:text-red-800"
                  >
                    Remove Key
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <input
                    type="password"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder="sk-or-v1-..."
                    className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-mono text-sm"
                    style={{ borderRadius: '2px' }}
                  />
                  <button
                    onClick={handleSaveApiKey}
                    disabled={!apiKeyInput.trim()}
                    className="w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50"
                    style={{ borderRadius: '2px' }}
                  >
                    Save API Key
                  </button>
                </div>
              )}
            </div>

            {hasApiKey && (
              <>
                <div className="border-t border-slate-ui pt-6">
                  <h4 className="font-sans font-semibold text-midnight text-sm mb-3">Analysis Options</h4>
                  <div className="space-y-2">
                    {[
                      { id: 'beat_descriptions', label: 'Beat Descriptions', desc: 'AI-generated plot beat details' },
                      { id: 'plot_holes', label: 'Plot Hole Detection', desc: 'Find inconsistencies and gaps' },
                      { id: 'pacing', label: 'Pacing Analysis', desc: 'Evaluate story structure balance' },
                    ].map((option) => (
                      <label key={option.id} className="flex items-start gap-3 cursor-pointer group">
                        <input
                          type="checkbox"
                          checked={selectedAnalyses.includes(option.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedAnalyses([...selectedAnalyses, option.id]);
                            } else {
                              setSelectedAnalyses(selectedAnalyses.filter((id) => id !== option.id));
                            }
                          }}
                          className="mt-0.5 w-4 h-4"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-sans font-medium text-midnight group-hover:text-bronze">
                            {option.label}
                          </div>
                          <div className="text-xs font-sans text-faded-ink">{option.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleRunAnalysis}
                  disabled={isAnalyzing || selectedAnalyses.length === 0}
                  className="w-full px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-bold uppercase tracking-button transition-colors shadow-book disabled:opacity-50"
                  style={{ borderRadius: '2px' }}
                >
                  {isAnalyzing ? 'Analyzing...' : `Run AI Analysis (Est. $0.01-0.05)`}
                </button>

                {hasResults && aiSuggestions?.cost && (
                  <div className="p-3 bg-green-50 border-l-4 border-green-500 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-sans font-semibold text-green-800 flex items-center gap-2">
                        <span>💰</span>
                        <span>Last Analysis Cost</span>
                      </span>
                      <span className="text-lg font-mono text-green-900 font-bold">
                        {aiSuggestions.cost.formatted}
                      </span>
                    </div>
                    {aiSuggestions.usage && (
                      <div className="text-xs font-sans text-green-700 flex items-center justify-between">
                        <span>
                          {aiSuggestions.usage.total_tokens.toLocaleString()} total tokens
                        </span>
                        <span className="text-faded-ink">
                          ({aiSuggestions.usage.prompt_tokens.toLocaleString()} prompt +
                          {aiSuggestions.usage.completion_tokens.toLocaleString()} completion)
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Beat Ideas Tab */}
        {activeTab === 'beat_ideas' && (
          <div className="p-4 space-y-4">
            {!hasResults ? (
              <div className="text-center py-12 px-4">
                <div className="text-6xl mb-4">💡</div>
                <h3 className="font-serif text-xl font-bold text-midnight mb-2">No AI Analysis Yet</h3>
                <p className="text-sm font-sans text-faded-ink mb-6">
                  {!hasApiKey
                    ? 'Enter your OpenRouter API key to get started with AI analysis'
                    : 'Run AI analysis to get beat ideas and suggestions'}
                </p>

                {/* Inline API Key Input */}
                {!hasApiKey && (
                  <div className="mb-6 p-4 bg-vellum border border-bronze/30" style={{ borderRadius: '2px' }}>
                    <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                      OpenRouter API Key
                      <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-xs text-bronze hover:underline font-normal"
                      >
                        (Get key)
                      </a>
                    </label>
                    <input
                      type="password"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder="sk-or-..."
                      className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
                      style={{ borderRadius: '2px' }}
                    />
                    <button
                      onClick={handleSaveApiKey}
                      disabled={!apiKeyInput.trim()}
                      className="mt-3 w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ borderRadius: '2px' }}
                    >
                      Save API Key
                    </button>
                  </div>
                )}

                {hasApiKey && (
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing}
                    className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ borderRadius: '2px' }}
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Feedback Summary Banner */}
                {hasFeedback() && (
                  <div className="p-3 bg-purple-50 border-2 border-purple-300" style={{ borderRadius: '2px' }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">💬</span>
                        <span className="text-sm font-sans font-semibold text-purple-800">
                          Feedback collected - ready to refine suggestions
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => clearBeatFeedback()}
                          className="px-3 py-1 text-xs font-sans font-medium text-purple-600 hover:text-purple-800"
                        >
                          Clear
                        </button>
                        <button
                          onClick={() => runAIAnalysisWithFeedback(outline.id, selectedAnalyses)}
                          disabled={isAnalyzing}
                          className="px-4 py-1.5 text-xs font-sans font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors disabled:opacity-50"
                          style={{ borderRadius: '2px' }}
                        >
                          {isAnalyzing ? 'Regenerating...' : 'Regenerate with Feedback'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {outline.plot_beats.sort((a, b) => a.order_index - b.order_index).map((beat) => {
                  const aiDescription = aiSuggestions?.beat_descriptions?.[beat.beat_name];
                  const feedback = beatFeedback.get(beat.beat_name);
                  const isLiked = feedback?.liked?.includes(aiDescription || '') || false;
                  const isDisliked = feedback?.disliked?.includes(aiDescription || '') || false;
                  const isFeedbackExpanded = expandedFeedback === beat.beat_name;

                  return (
                    <div key={beat.id} className="border-2 border-slate-ui p-4" style={{ borderRadius: '2px' }}>
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                            {beat.beat_name}
                          </div>
                          <h4 className="font-serif font-bold text-base text-midnight">{beat.beat_label}</h4>
                        </div>
                        <span className="text-xs font-sans text-faded-ink">
                          {Math.round(beat.target_position_percent * 100)}%
                        </span>
                      </div>

                      {aiDescription && (
                        <div className="mt-3 p-3 bg-bronze/5 border-l-2 border-bronze" style={{ borderRadius: '2px' }}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-sans font-semibold text-bronze uppercase">
                              AI Suggestion
                            </span>
                            <div className="flex items-center gap-2">
                              {/* Feedback buttons */}
                              <button
                                onClick={() => addBeatFeedbackLike(beat.beat_name, aiDescription)}
                                className={`p-1.5 rounded transition-colors ${
                                  isLiked
                                    ? 'bg-green-100 text-green-600'
                                    : 'text-gray-400 hover:bg-green-50 hover:text-green-500'
                                }`}
                                title="Like this suggestion"
                              >
                                <svg className="w-4 h-4" fill={isLiked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                              </button>
                              <button
                                onClick={() => {
                                  addBeatFeedbackDislike(beat.beat_name, aiDescription);
                                  // Auto-expand feedback area when disliking
                                  setExpandedFeedback(beat.beat_name);
                                }}
                                className={`p-1.5 rounded transition-colors ${
                                  isDisliked
                                    ? 'bg-red-100 text-red-600'
                                    : 'text-gray-400 hover:bg-red-50 hover:text-red-500'
                                }`}
                                title="Dislike - add feedback for better suggestions"
                              >
                                <svg className="w-4 h-4" fill={isDisliked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                </svg>
                              </button>
                              <button
                                onClick={() => setExpandedFeedback(isFeedbackExpanded ? null : beat.beat_name)}
                                className="p-1.5 text-gray-400 hover:bg-gray-100 rounded transition-colors"
                                title="Add notes"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleApplyBeatDescription(beat.beat_name, aiDescription)}
                                className="px-2 py-1 text-xs font-sans font-medium bg-bronze hover:bg-bronze-dark text-white transition-colors"
                                style={{ borderRadius: '2px' }}
                              >
                                Use This
                              </button>
                            </div>
                          </div>
                          <p className="text-sm font-sans text-midnight leading-relaxed">{aiDescription}</p>

                          {/* Expanded feedback notes */}
                          {isFeedbackExpanded && (
                            <div className="mt-3 pt-3 border-t border-bronze/30 bg-amber-50/50 p-3 -mx-3 -mb-3">
                              <label className="block text-xs font-sans font-semibold text-midnight mb-2">
                                ✏️ Help improve this suggestion
                              </label>
                              <textarea
                                value={feedback?.notes || ''}
                                onChange={(e) => setBeatFeedbackNotes(beat.beat_name, e.target.value)}
                                placeholder="What would make this better? e.g., 'Make it more action-focused', 'The brothers should be in conflict here', 'Include the mentor character'..."
                                className="w-full px-2 py-1.5 text-sm border border-bronze/40 focus:border-bronze focus:outline-none font-sans bg-white"
                                style={{ borderRadius: '2px' }}
                                rows={3}
                                autoFocus
                              />
                              <p className="text-xs text-faded-ink mt-1">
                                Your feedback will be used when you click "Refine Suggestions" to generate better ideas.
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {beat.beat_description && !aiDescription && (
                        <div className="mt-2 text-sm font-sans text-faded-ink">{beat.beat_description}</div>
                      )}
                    </div>
                  );
                })}
              </>
            )}
          </div>
        )}

        {/* Plot Holes Tab */}
        {activeTab === 'plot_holes' && (
          <div className="p-4 space-y-4">
            {!hasResults ? (
              <div className="text-center py-12 px-4">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="font-serif text-xl font-bold text-midnight mb-2">No Analysis Yet</h3>
                <p className="text-sm font-sans text-faded-ink mb-6">
                  {!hasApiKey
                    ? 'Enter your OpenRouter API key to get started with AI analysis'
                    : 'Run AI analysis to detect plot holes and inconsistencies'}
                </p>

                {/* Inline API Key Input */}
                {!hasApiKey && (
                  <div className="mb-6 p-4 bg-vellum border border-bronze/30" style={{ borderRadius: '2px' }}>
                    <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                      OpenRouter API Key
                      <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-xs text-bronze hover:underline font-normal"
                      >
                        (Get key)
                      </a>
                    </label>
                    <input
                      type="password"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder="sk-or-..."
                      className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
                      style={{ borderRadius: '2px' }}
                    />
                    <button
                      onClick={handleSaveApiKey}
                      disabled={!apiKeyInput.trim()}
                      className="mt-3 w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ borderRadius: '2px' }}
                    >
                      Save API Key
                    </button>
                  </div>
                )}

                {hasApiKey && (
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing}
                    className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ borderRadius: '2px' }}
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Overall Assessment */}
                {aiSuggestions?.overall_assessment && (
                  <div className="p-4 bg-blue-500/10 border-l-4 border-blue-500" style={{ borderRadius: '2px' }}>
                    <div className="font-sans font-semibold text-blue-800 text-sm mb-1">Overall Assessment</div>
                    <p className="text-sm font-sans text-blue-700">{aiSuggestions.overall_assessment}</p>
                  </div>
                )}

                {/* Severity Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-sans font-semibold text-faded-ink uppercase">Filter:</span>
                  {['all', 'high', 'medium', 'low'].map((severity) => (
                    <button
                      key={severity}
                      onClick={() => setSeverityFilter(severity as any)}
                      className={`px-3 py-1 text-xs font-sans font-medium uppercase tracking-wider transition-colors ${
                        severityFilter === severity
                          ? 'bg-bronze text-white'
                          : 'bg-slate-ui/20 text-faded-ink hover:bg-slate-ui/40'
                      }`}
                      style={{ borderRadius: '2px' }}
                    >
                      {severity}
                    </button>
                  ))}
                </div>

                {/* Plot Holes List */}
                {filteredPlotHoles.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-3">✅</div>
                    <p className="text-sm font-sans text-faded-ink">
                      {resolvedCount > 0
                        ? `All issues resolved! (${resolvedCount} marked as fixed)`
                        : 'No plot holes detected! Great work!'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredPlotHoles.map((hole, index) => {
                      const globalIndex = aiSuggestions?.plot_holes?.indexOf(hole) ?? index;

                      return (
                        <div
                          key={index}
                          className={`p-4 border-l-4 ${
                            hole.severity === 'high'
                              ? 'border-red-500 bg-red-500/10'
                              : hole.severity === 'medium'
                              ? 'border-yellow-500 bg-yellow-500/10'
                              : 'border-gray-500 bg-gray-500/10'
                          }`}
                          style={{ borderRadius: '2px' }}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <span
                              className={`px-2 py-0.5 text-xs font-sans font-bold uppercase ${
                                hole.severity === 'high'
                                  ? 'bg-red-500 text-white'
                                  : hole.severity === 'medium'
                                  ? 'bg-yellow-500 text-white'
                                  : 'bg-gray-500 text-white'
                              }`}
                              style={{ borderRadius: '2px' }}
                            >
                              {hole.severity}
                            </span>
                            <button
                              onClick={() => markPlotHoleResolved(globalIndex)}
                              className="text-xs font-sans text-faded-ink hover:text-bronze"
                            >
                              Mark Resolved
                            </button>
                          </div>
                          <div className="text-xs font-sans text-faded-ink mb-1">Location: {hole.location}</div>
                          <div className="text-sm font-sans text-midnight font-semibold mb-2">{hole.issue}</div>
                          <div className="text-sm font-sans text-faded-ink italic">{hole.suggestion}</div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Pacing Tab */}
        {activeTab === 'pacing' && (
          <div className="p-4 space-y-4">
            {!hasResults || !aiSuggestions?.pacing_analysis ? (
              <div className="text-center py-12 px-4">
                <div className="text-6xl mb-4">📈</div>
                <h3 className="font-serif text-xl font-bold text-midnight mb-2">No Pacing Analysis</h3>
                <p className="text-sm font-sans text-faded-ink mb-6">
                  {!hasApiKey
                    ? 'Enter your OpenRouter API key to get started with AI analysis'
                    : 'Run AI analysis to get pacing feedback and recommendations'}
                </p>

                {/* Inline API Key Input */}
                {!hasApiKey && (
                  <div className="mb-6 p-4 bg-vellum border border-bronze/30" style={{ borderRadius: '2px' }}>
                    <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                      OpenRouter API Key
                      <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-xs text-bronze hover:underline font-normal"
                      >
                        (Get key)
                      </a>
                    </label>
                    <input
                      type="password"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder="sk-or-..."
                      className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
                      style={{ borderRadius: '2px' }}
                    />
                    <button
                      onClick={handleSaveApiKey}
                      disabled={!apiKeyInput.trim()}
                      className="mt-3 w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ borderRadius: '2px' }}
                    >
                      Save API Key
                    </button>
                  </div>
                )}

                {hasApiKey && (
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isAnalyzing}
                    className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ borderRadius: '2px' }}
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Overall Score */}
                <div className="p-6 bg-gradient-to-r from-bronze/20 to-green-500/20 border-2 border-bronze">
                  <div className="text-center">
                    <div className="text-xs font-sans font-semibold text-faded-ink uppercase mb-2">
                      Overall Pacing Score
                    </div>
                    <div className="text-6xl font-serif font-bold text-bronze mb-2">
                      {aiSuggestions.pacing_analysis.overall_score.toFixed(1)}
                    </div>
                    <div className="text-sm font-sans text-faded-ink">out of 10</div>
                  </div>
                </div>

                {/* Act Balance */}
                {aiSuggestions.pacing_analysis.act_balance && (
                  <div>
                    <h4 className="font-sans font-semibold text-midnight text-sm mb-3">Act Distribution</h4>
                    <div className="space-y-2">
                      {Object.entries(aiSuggestions.pacing_analysis.act_balance).map(([act, percent]) => (
                        <div key={act}>
                          <div className="flex items-center justify-between text-xs font-sans mb-1">
                            <span className="text-faded-ink capitalize">
                              {act.replace('_', ' ')} ({Math.round(percent * 100)}%)
                            </span>
                          </div>
                          <div className="h-2 bg-slate-ui/30" style={{ borderRadius: '2px' }}>
                            <div
                              className="h-full bg-bronze"
                              style={{ width: `${percent * 100}%`, borderRadius: '2px' }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Issues */}
                {aiSuggestions.pacing_analysis.issues.length > 0 && (
                  <div>
                    <h4 className="font-sans font-semibold text-midnight text-sm mb-3">Issues to Address</h4>
                    <div className="space-y-2">
                      {aiSuggestions.pacing_analysis.issues.map((issue, i) => (
                        <div
                          key={i}
                          className="p-3 bg-yellow-500/10 border-l-2 border-yellow-500 text-sm font-sans text-midnight"
                          style={{ borderRadius: '2px' }}
                        >
                          {issue}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {aiSuggestions.pacing_analysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-sans font-semibold text-midnight text-sm mb-3">Recommendations</h4>
                    <div className="space-y-2">
                      {aiSuggestions.pacing_analysis.recommendations.map((rec, i) => (
                        <div
                          key={i}
                          className="p-3 bg-blue-500/10 border-l-2 border-blue-500 text-sm font-sans text-midnight"
                          style={{ borderRadius: '2px' }}
                        >
                          {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strengths */}
                {aiSuggestions.pacing_analysis.strengths && aiSuggestions.pacing_analysis.strengths.length > 0 && (
                  <div>
                    <h4 className="font-sans font-semibold text-midnight text-sm mb-3">Strengths</h4>
                    <div className="space-y-2">
                      {aiSuggestions.pacing_analysis.strengths.map((strength, i) => (
                        <div
                          key={i}
                          className="p-3 bg-green-500/10 border-l-2 border-green-500 text-sm font-sans text-green-700"
                          style={{ borderRadius: '2px' }}
                        >
                          ✓ {strength}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      {hasResults && (
        <div className="flex-shrink-0 border-t-2 border-slate-ui bg-vellum p-4 text-center">
          <button
            onClick={() => {
              if (confirm('Clear all AI suggestions? This cannot be undone.')) {
                clearAISuggestions();
                setActiveTab('settings');
              }
            }}
            className="text-sm font-sans text-red-600 hover:text-red-800"
          >
            Clear All Suggestions
          </button>
        </div>
      )}
    </div>
  );
}
