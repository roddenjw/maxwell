/**
 * AI Suggestions Panel - OpenRouter-powered writing suggestions
 * Displays AI-enhanced feedback using user's API key (BYOK)
 */

import { useState, useEffect } from 'react';
import { toast } from '@/stores/toastStore';
import { useFastCoachStore } from '@/stores/fastCoachStore';

interface AISuggestionsPanelProps {
  manuscriptId: string;
}

interface AIUsage {
  tokens: number;
  cost: number;
}

export default function AISuggestionsPanel({ manuscriptId }: AISuggestionsPanelProps) {
  const { currentEditorText } = useFastCoachStore();
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [_selectedModel, setSelectedModel] = useState('anthropic/claude-3.5-sonnet');
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<AIUsage | null>(null);

  // Load API key and model from localStorage
  useEffect(() => {
    const savedKey = localStorage.getItem('openrouter_api_key');
    setApiKey(savedKey);

    const savedModel = localStorage.getItem('openrouter_model');
    if (savedModel) {
      setSelectedModel(savedModel);
    }
  }, []);

  // Load usage stats from localStorage
  useEffect(() => {
    const savedUsage = localStorage.getItem('ai_usage_stats');
    if (savedUsage) {
      try {
        setUsage(JSON.parse(savedUsage));
      } catch (e) {
        console.error('Failed to parse usage stats:', e);
      }
    }
  }, []);

  const handleGetSuggestion = async () => {
    if (!apiKey) {
      toast.error('Please add your OpenRouter API key in Settings first');
      return;
    }

    if (!currentEditorText || currentEditorText.length < 50) {
      toast.error('Please write at least 50 characters to get AI suggestions');
      return;
    }

    try {
      setLoading(true);
      setSuggestion(null);

      const response = await fetch('http://localhost:8000/api/fast-coach/ai-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: currentEditorText.slice(-1000), // Analyze last 1000 chars
          api_key: apiKey,
          manuscript_id: manuscriptId,
          context: `Fiction manuscript writing session`,
          suggestion_type: 'general'
        }),
      });

      const data = await response.json();

      if (!data.success) {
        toast.error(`AI suggestion failed: ${data.error || 'Unknown error'}`);
        return;
      }

      setSuggestion(data.suggestion);

      // Update usage tracking
      if (data.usage && data.cost) {
        const currentUsage = usage || { tokens: 0, cost: 0 };
        const newUsage = {
          tokens: currentUsage.tokens + data.usage.total_tokens,
          cost: currentUsage.cost + data.cost
        };
        setUsage(newUsage);
        localStorage.setItem('ai_usage_stats', JSON.stringify(newUsage));

        toast.success(`AI suggestion generated! Cost: $${data.cost.toFixed(4)}`);
      }

    } catch (error) {
      console.error('AI suggestion error:', error);
      toast.error('Failed to get AI suggestion. Check your connection.');
    } finally {
      setLoading(false);
    }
  };

  if (!apiKey) {
    return (
      <div className="p-4 border-b border-slate-ui bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex items-start gap-3">
          <span className="text-2xl">🤖</span>
          <div className="flex-1">
            <h3 className="font-garamond text-lg font-semibold text-midnight mb-1">
              AI Writing Coach
            </h3>
            <p className="text-sm font-sans text-faded-ink mb-3">
              Get AI-powered suggestions using your own OpenRouter API key
            </p>
            <button
              onClick={() => {
                // This will be opened via settings
                const event = new CustomEvent('open-settings');
                window.dispatchEvent(event);
              }}
              className="text-sm font-sans text-white bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition-colors"
            >
              Add API Key in Settings
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 border-b border-slate-ui bg-gradient-to-r from-purple-50 to-blue-50">
      <div className="flex items-start gap-3 mb-3">
        <span className="text-2xl">🤖</span>
        <div className="flex-1">
          <h3 className="font-garamond text-lg font-semibold text-midnight mb-1">
            AI Writing Coach
          </h3>
          <p className="text-xs font-sans text-faded-ink">
            Powered by Claude 3.5 Sonnet via OpenRouter
          </p>
        </div>
        <button
          onClick={handleGetSuggestion}
          disabled={loading || !currentEditorText || currentEditorText.length < 50}
          className="px-4 py-2 bg-purple-600 text-white text-sm font-sans font-medium rounded hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '🔄 Analyzing...' : '✨ Get AI Suggestion'}
        </button>
      </div>

      {/* Usage Stats */}
      {usage && (
        <div className="mb-3 p-2 bg-white/50 rounded border border-purple-200">
          <div className="flex justify-between text-xs font-sans text-faded-ink">
            <span>Usage this month: {usage.tokens.toLocaleString()} tokens</span>
            <span className="font-semibold text-purple-700">${usage.cost.toFixed(4)}</span>
          </div>
        </div>
      )}

      {/* AI Suggestion Display */}
      {suggestion && (
        <div className="bg-white p-4 rounded border border-purple-300 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm">✨</span>
            <span className="text-xs font-sans font-semibold text-purple-700 uppercase tracking-wide">
              AI Suggestion
            </span>
          </div>
          <div className="text-sm font-sans text-midnight whitespace-pre-wrap leading-relaxed">
            {suggestion}
          </div>
        </div>
      )}

      {/* Info */}
      <div className="mt-3 text-xs font-sans text-faded-ink">
        💡 Tip: AI analyzes your last 1000 characters. Keep writing to get contextual feedback!
      </div>
    </div>
  );
}
