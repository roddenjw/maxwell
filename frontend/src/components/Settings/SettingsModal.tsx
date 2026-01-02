/**
 * SettingsModal - User settings including OpenRouter API key
 * Implements BYOK (Bring Your Own Key) for AI features
 */

import { useState, useEffect } from 'react';
import { toast } from '@/stores/toastStore';
import analytics from '@/lib/analytics';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [usage, setUsage] = useState<{tokens: number; cost: number} | null>(null);

  // Load saved API key on mount
  useEffect(() => {
    if (isOpen) {
      const savedKey = localStorage.getItem('openrouter_api_key');
      if (savedKey) {
        setOpenRouterKey(savedKey);
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
    }
  }, [isOpen]);

  const handleSave = () => {
    setIsSaving(true);

    try {
      if (openRouterKey.trim()) {
        // Save to localStorage
        localStorage.setItem('openrouter_api_key', openRouterKey.trim());
        analytics.exportCompleted('settings', 'api_key_saved', 0); // Track feature adoption
        toast.success('✅ API key saved! AI features enabled.');
      } else {
        // Remove key
        localStorage.removeItem('openrouter_api_key');
        toast.info('API key removed. AI features disabled.');
      }

      // Close modal after brief delay
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (error) {
      console.error('Failed to save API key:', error);
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

          {/* Model Selection (Future Enhancement) */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-sm">
            <h4 className="text-sm font-sans font-semibold text-midnight mb-2">
              🎛️ Model Selection (Coming Soon)
            </h4>
            <p className="text-xs font-sans text-faded-ink">
              Choose from Claude, GPT-4, Llama, and more. Optimize for quality or cost.
            </p>
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
