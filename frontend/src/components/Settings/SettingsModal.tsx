/**
 * SettingsModal - User settings including OpenRouter API key
 * Implements BYOK (Bring Your Own Key) for AI features
 * Includes entity extraction settings for real-time NLP
 */

import { useState, useEffect } from 'react';
import { toast } from '@/stores/toastStore';
import type { ExtractionSettings } from '@/hooks/useRealtimeNLP';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AI_MODELS = [
  { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', cost: 'Medium', quality: 'Excellent' },
  { id: 'anthropic/claude-3-haiku', name: 'Claude 3 Haiku', cost: 'Low', quality: 'Good' },
  { id: 'openai/gpt-4-turbo', name: 'GPT-4 Turbo', cost: 'High', quality: 'Excellent' },
  { id: 'openai/gpt-3.5-turbo', name: 'GPT-3.5 Turbo', cost: 'Very Low', quality: 'Good' },
  { id: 'meta-llama/llama-3.1-70b-instruct', name: 'Llama 3.1 70B', cost: 'Low', quality: 'Very Good' },
];

const DEFAULT_EXTRACTION_SETTINGS: ExtractionSettings = {
  enabled: true,
  debounce_delay: 2,
  confidence_threshold: 'medium',
  entity_types: ['CHARACTER', 'LOCATION', 'ITEM', 'LORE'],
};

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('anthropic/claude-3.5-sonnet');
  const [showKey, setShowKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [usage, setUsage] = useState<{tokens: number; cost: number} | null>(null);
  const [extractionSettings, setExtractionSettings] = useState<ExtractionSettings>(DEFAULT_EXTRACTION_SETTINGS);

  // Load saved settings on mount
  useEffect(() => {
    if (isOpen) {
      const savedKey = localStorage.getItem('openrouter_api_key');
      if (savedKey) {
        setOpenRouterKey(savedKey);
      }

      const savedModel = localStorage.getItem('openrouter_model');
      if (savedModel) {
        setSelectedModel(savedModel);
      }

      // Load usage stats
      const savedUsage = localStorage.getItem('ai_usage_stats');
      if (savedUsage) {
        try {
          setUsage(JSON.parse(savedUsage));
        } catch (e) {
          console.error('Failed to parse usage stats:', e);
        }
      }

      // Load extraction settings
      const savedExtraction = localStorage.getItem('maxwell_extraction_settings');
      if (savedExtraction) {
        try {
          setExtractionSettings({ ...DEFAULT_EXTRACTION_SETTINGS, ...JSON.parse(savedExtraction) });
        } catch (e) {
          console.error('Failed to parse extraction settings:', e);
        }
      }
    }
  }, [isOpen]);

  // Toggle entity type in extraction settings
  const toggleEntityType = (type: 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE') => {
    setExtractionSettings(prev => {
      const types = prev.entity_types.includes(type)
        ? prev.entity_types.filter(t => t !== type)
        : [...prev.entity_types, type];
      return { ...prev, entity_types: types };
    });
  };

  const handleSave = () => {
    setIsSaving(true);

    try {
      if (openRouterKey.trim()) {
        // Save API key to localStorage
        localStorage.setItem('openrouter_api_key', openRouterKey.trim());
        toast.success('Settings saved! AI features enabled.');
      } else {
        // Remove key
        localStorage.removeItem('openrouter_api_key');
        toast.info('Settings saved. AI features disabled (no API key).');
      }

      // Save selected model
      localStorage.setItem('openrouter_model', selectedModel);

      // Save extraction settings
      localStorage.setItem('maxwell_extraction_settings', JSON.stringify(extractionSettings));

      // Close modal after brief delay
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestKey = async () => {
    if (!openRouterKey.trim()) {
      toast.error('Please enter an API key first');
      return;
    }

    try {
      toast.info('Testing API key...');

      const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
        headers: {
          'Authorization': `Bearer ${openRouterKey.trim()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`✅ API key valid! Credits: $${data.data.limit || 'unlimited'}`);
      } else {
        toast.error('❌ API key invalid or expired');
      }
    } catch (error) {
      console.error('API key test failed:', error);
      toast.error('Failed to test API key. Check your connection.');
    }
  };

  const resetUsageStats = () => {
    localStorage.removeItem('ai_usage_stats');
    setUsage(null);
    toast.success('Usage stats reset');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[300] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-ui bg-white">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-garamond font-bold text-midnight">Settings</h2>
            <button
              onClick={onClose}
              className="text-faded-ink hover:text-midnight text-3xl leading-none"
              title="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* AI Features Section */}
          <div>
            <h3 className="text-lg font-garamond font-semibold text-midnight mb-2">
              🤖 AI Features
            </h3>
            <p className="text-sm font-sans text-faded-ink mb-4">
              Enable AI-powered writing suggestions using OpenRouter. Bring your own API key (BYOK) for
              full control over costs.
            </p>

            {/* API Key Input */}
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-sans font-semibold text-midnight mb-1 block">
                  OpenRouter API Key
                </span>
                <div className="flex gap-2">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={openRouterKey}
                    onChange={(e) => setOpenRouterKey(e.target.value)}
                    placeholder="sk-or-v1-..."
                    className="flex-1 px-3 py-2 border border-slate-ui rounded-sm font-mono text-sm focus:outline-none focus:ring-2 focus:ring-bronze"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="px-3 py-2 border border-slate-ui rounded-sm hover:bg-white transition-colors text-sm font-sans"
                    title={showKey ? 'Hide key' : 'Show key'}
                  >
                    {showKey ? '🙈' : '👁️'}
                  </button>
                </div>
              </label>

              <div className="flex gap-2">
                <button
                  onClick={handleTestKey}
                  className="px-4 py-2 border border-slate-ui rounded-sm hover:bg-white transition-colors text-sm font-sans font-medium"
                >
                  Test Key
                </button>
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-sm hover:bg-blue-700 transition-colors text-sm font-sans font-medium"
                >
                  Get API Key →
                </a>
              </div>

              {/* Info Box */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-sm">
                <p className="text-sm font-sans text-blue-900 mb-2">
                  <strong>💡 Why OpenRouter?</strong>
                </p>
                <ul className="text-xs font-sans text-blue-800 space-y-1 ml-4 list-disc">
                  <li>Access to 100+ AI models (Claude, GPT-4, Llama, etc.)</li>
                  <li>Pay only for what you use (starts at ~$0.01 per suggestion)</li>
                  <li>Your key, your data - full privacy and control</li>
                  <li>$5 credit gets you ~500 AI suggestions</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Usage Stats */}
          {usage && (
            <div className="p-4 bg-white border border-slate-ui rounded-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-sans font-semibold text-midnight">
                  📊 AI Usage This Month
                </h4>
                <button
                  onClick={resetUsageStats}
                  className="text-xs font-sans text-bronze hover:underline"
                >
                  Reset
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-sans text-faded-ink">Tokens Used</p>
                  <p className="text-2xl font-garamond font-bold text-midnight">
                    {usage.tokens.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-sans text-faded-ink">Estimated Cost</p>
                  <p className="text-2xl font-garamond font-bold text-bronze">
                    ${usage.cost.toFixed(4)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Model Selection */}
          <div>
            <h3 className="text-lg font-garamond font-semibold text-midnight mb-2">
              🎛️ Model Selection
            </h3>
            <p className="text-sm font-sans text-faded-ink mb-4">
              Choose from different AI models. Balance quality and cost for your needs.
            </p>

            <label className="block">
              <span className="text-sm font-sans font-semibold text-midnight mb-2 block">
                AI Model
              </span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 border border-slate-ui rounded-sm font-sans text-sm focus:outline-none focus:ring-2 focus:ring-bronze bg-white"
              >
                {AI_MODELS.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} - Cost: {model.cost}, Quality: {model.quality}
                  </option>
                ))}
              </select>
            </label>

            {/* Model Info */}
            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-sm">
              <p className="text-xs font-sans text-blue-900 mb-1">
                <strong>Selected: {AI_MODELS.find(m => m.id === selectedModel)?.name}</strong>
              </p>
              <p className="text-xs font-sans text-blue-800">
                {selectedModel === 'anthropic/claude-3.5-sonnet' && '✨ Best overall quality. Great for creative writing and nuanced feedback. ~$0.01 per suggestion.'}
                {selectedModel === 'anthropic/claude-3-haiku' && '⚡ Fast and affordable. Good for quick suggestions. ~$0.001 per suggestion.'}
                {selectedModel === 'openai/gpt-4-turbo' && '🚀 Excellent quality, higher cost. Very creative. ~$0.02 per suggestion.'}
                {selectedModel === 'openai/gpt-3.5-turbo' && '💰 Very affordable. Great for drafting. ~$0.0005 per suggestion.'}
                {selectedModel === 'meta-llama/llama-3.1-70b-instruct' && '🦙 Open-source, good quality, low cost. ~$0.003 per suggestion.'}
              </p>
            </div>
          </div>

          {/* Entity Extraction Settings */}
          <div>
            <h3 className="text-lg font-garamond font-semibold text-midnight mb-2">
              🔍 Entity Extraction
            </h3>
            <p className="text-sm font-sans text-faded-ink mb-4">
              Configure how Maxwell detects characters, locations, and other entities as you write.
            </p>

            {/* Enable/Disable Toggle */}
            <div className="space-y-4">
              <label className="flex items-center justify-between p-3 bg-white border border-slate-ui rounded-sm cursor-pointer hover:bg-vellum transition-colors">
                <div>
                  <span className="text-sm font-sans font-semibold text-midnight">
                    Enable Real-time Extraction
                  </span>
                  <p className="text-xs font-sans text-faded-ink mt-0.5">
                    Automatically detect entities while you write
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={extractionSettings.enabled}
                  onChange={(e) => setExtractionSettings(prev => ({ ...prev, enabled: e.target.checked }))}
                  className="w-5 h-5 text-bronze border-slate-ui rounded focus:ring-bronze cursor-pointer"
                />
              </label>

              {/* Debounce Delay */}
              <div className="p-3 bg-white border border-slate-ui rounded-sm">
                <span className="text-sm font-sans font-semibold text-midnight block mb-2">
                  Detection Delay
                </span>
                <p className="text-xs font-sans text-faded-ink mb-3">
                  How long to wait after you stop typing before analyzing text
                </p>
                <div className="flex gap-2">
                  {[2, 5, 10].map((delay) => (
                    <button
                      key={delay}
                      onClick={() => setExtractionSettings(prev => ({ ...prev, debounce_delay: delay }))}
                      className={`px-4 py-2 border rounded-sm text-sm font-sans transition-colors ${
                        extractionSettings.debounce_delay === delay
                          ? 'bg-bronze text-white border-bronze'
                          : 'border-slate-ui hover:bg-vellum'
                      }`}
                    >
                      {delay}s
                    </button>
                  ))}
                </div>
              </div>

              {/* Confidence Threshold */}
              <div className="p-3 bg-white border border-slate-ui rounded-sm">
                <span className="text-sm font-sans font-semibold text-midnight block mb-2">
                  Detection Sensitivity
                </span>
                <p className="text-xs font-sans text-faded-ink mb-3">
                  Higher sensitivity means more entities detected, but also more false positives
                </p>
                <div className="flex gap-2">
                  {(['low', 'medium', 'high'] as const).map((threshold) => (
                    <button
                      key={threshold}
                      onClick={() => setExtractionSettings(prev => ({ ...prev, confidence_threshold: threshold }))}
                      className={`px-4 py-2 border rounded-sm text-sm font-sans capitalize transition-colors ${
                        extractionSettings.confidence_threshold === threshold
                          ? 'bg-bronze text-white border-bronze'
                          : 'border-slate-ui hover:bg-vellum'
                      }`}
                    >
                      {threshold}
                    </button>
                  ))}
                </div>
              </div>

              {/* Entity Types */}
              <div className="p-3 bg-white border border-slate-ui rounded-sm">
                <span className="text-sm font-sans font-semibold text-midnight block mb-2">
                  Entity Types to Detect
                </span>
                <p className="text-xs font-sans text-faded-ink mb-3">
                  Choose which types of entities to look for in your writing
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { type: 'CHARACTER' as const, label: 'Characters', icon: '👤' },
                    { type: 'LOCATION' as const, label: 'Locations', icon: '📍' },
                    { type: 'ITEM' as const, label: 'Items', icon: '⚔️' },
                    { type: 'LORE' as const, label: 'Lore', icon: '📜' },
                  ].map(({ type, label, icon }) => (
                    <label
                      key={type}
                      className={`flex items-center gap-2 p-2 border rounded-sm cursor-pointer transition-colors ${
                        extractionSettings.entity_types.includes(type)
                          ? 'bg-bronze/10 border-bronze'
                          : 'border-slate-ui hover:bg-vellum'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={extractionSettings.entity_types.includes(type)}
                        onChange={() => toggleEntityType(type)}
                        className="w-4 h-4 text-bronze border-slate-ui rounded focus:ring-bronze cursor-pointer"
                      />
                      <span className="text-sm font-sans">
                        {icon} {label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-ui bg-white flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-slate-ui rounded-sm hover:bg-vellum transition-colors text-sm font-sans font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-bronze text-white rounded-sm hover:bg-bronze/90 transition-colors text-sm font-sans font-medium disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
