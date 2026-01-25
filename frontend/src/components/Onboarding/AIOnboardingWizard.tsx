/**
 * AIOnboardingWizard - 60-second BYOK tutorial
 * Guides users through setting up their AI API key
 */

import { useState, useEffect } from 'react';
import { toast } from '@/stores/toastStore';
import analytics from '@/lib/analytics';

interface AIOnboardingWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

type Step = 'intro' | 'explanation' | 'get-key' | 'paste-test' | 'choose-model' | 'success';

const MODEL_RECOMMENDATIONS = [
  {
    id: 'anthropic/claude-3.5-sonnet',
    name: 'Claude 3.5 Sonnet',
    use: 'Best Overall',
    description: 'Excellent writing quality, great for chapter recaps and detailed feedback',
    cost: '~$0.01/suggestion',
    recommended: true,
  },
  {
    id: 'anthropic/claude-3-haiku',
    name: 'Claude 3 Haiku',
    use: 'Fast Coach',
    description: 'Quick suggestions while you write, very affordable',
    cost: '~$0.001/suggestion',
    recommended: false,
  },
  {
    id: 'meta-llama/llama-3.1-70b-instruct',
    name: 'Llama 3.1 70B',
    use: 'Brainstorming',
    description: 'Creative and affordable, great for generating ideas',
    cost: '~$0.003/suggestion',
    recommended: false,
  },
];

export default function AIOnboardingWizard({
  isOpen,
  onClose,
  onComplete,
}: AIOnboardingWizardProps) {
  const [step, setStep] = useState<Step>('intro');
  const [apiKey, setApiKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('anthropic/claude-3.5-sonnet');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; credits?: string } | null>(null);
  const [showKey, setShowKey] = useState(false);

  // Track wizard start
  useEffect(() => {
    if (isOpen) {
      analytics.onboardingStarted();
    }
  }, [isOpen]);

  const handleTestKey = async () => {
    if (!apiKey.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
        headers: {
          'Authorization': `Bearer ${apiKey.trim()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTestResult({
          success: true,
          credits: data.data?.limit ? `$${data.data.limit}` : 'Unlimited',
        });
        toast.success('API key is valid!');
      } else {
        setTestResult({ success: false });
        toast.error('API key is invalid or expired');
      }
    } catch (error) {
      setTestResult({ success: false });
      toast.error('Failed to test API key');
    } finally {
      setTesting(false);
    }
  };

  const handleComplete = () => {
    // Save settings
    localStorage.setItem('openrouter_api_key', apiKey.trim());
    localStorage.setItem('openrouter_model', selectedModel);

    // Mark onboarding as complete
    localStorage.setItem('ai_onboarding_complete', 'true');

    // Track completion
    analytics.apiKeyConfigured('openrouter');
    analytics.onboardingCompleted(true);

    toast.success('AI features are now enabled!');
    onComplete();
    onClose();
  };

  const handleSkip = () => {
    localStorage.setItem('ai_onboarding_skipped', 'true');
    analytics.onboardingSkipped();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[400] p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-xl w-full overflow-hidden">
        {/* Progress bar */}
        <div className="h-1 bg-slate-ui">
          <div
            className="h-full bg-bronze transition-all duration-300"
            style={{
              width: step === 'intro' ? '0%' :
                     step === 'explanation' ? '20%' :
                     step === 'get-key' ? '40%' :
                     step === 'paste-test' ? '60%' :
                     step === 'choose-model' ? '80%' : '100%'
            }}
          />
        </div>

        <div className="p-8">
          {/* Step 1: Introduction */}
          {step === 'intro' && (
            <div className="text-center space-y-6">
              <div className="text-6xl">🤖</div>
              <h2 className="text-2xl font-garamond font-bold text-midnight">
                Enable AI Features
              </h2>
              <p className="text-faded-ink font-sans">
                Maxwell uses AI to help you write better. This takes about 60 seconds to set up.
              </p>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-4 bg-bronze/5 rounded-lg">
                  <div className="text-2xl mb-2">📝</div>
                  <p className="text-sm font-sans text-midnight font-semibold">Chapter Recaps</p>
                </div>
                <div className="p-4 bg-bronze/5 rounded-lg">
                  <div className="text-2xl mb-2">💡</div>
                  <p className="text-sm font-sans text-midnight font-semibold">Writing Coach</p>
                </div>
                <div className="p-4 bg-bronze/5 rounded-lg">
                  <div className="text-2xl mb-2">🧠</div>
                  <p className="text-sm font-sans text-midnight font-semibold">Brainstorming</p>
                </div>
              </div>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleSkip}
                  className="px-6 py-3 text-faded-ink font-sans text-sm hover:underline"
                >
                  Skip for now
                </button>
                <button
                  onClick={() => setStep('explanation')}
                  className="px-8 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 transition-colors"
                >
                  Let's Go!
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Explanation (What is BYOK?) */}
          {step === 'explanation' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-garamond font-bold text-midnight text-center">
                What is BYOK?
              </h2>
              <p className="text-faded-ink font-sans text-center">
                <strong>Bring Your Own Key</strong> means you use your own API key for AI features.
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border border-green-200 bg-green-50 rounded-lg">
                  <h3 className="font-semibold text-green-800 mb-2">Benefits</h3>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>+ Full control over costs</li>
                    <li>+ Your data, your privacy</li>
                    <li>+ Pay only for what you use</li>
                    <li>+ $5 gets ~500 suggestions</li>
                  </ul>
                </div>
                <div className="p-4 border border-bronze/30 bg-bronze/5 rounded-lg">
                  <h3 className="font-semibold text-midnight mb-2">Cost Comparison</h3>
                  <ul className="text-sm text-faded-ink space-y-1">
                    <li>Monthly subscription: $20/mo</li>
                    <li><strong className="text-bronze">BYOK (typical): $2-5/mo</strong></li>
                    <li>Per recap: ~$0.01</li>
                    <li>Per suggestion: ~$0.001</li>
                  </ul>
                </div>
              </div>

              <div className="flex gap-3 justify-between">
                <button
                  onClick={() => setStep('intro')}
                  className="px-6 py-3 text-faded-ink font-sans hover:underline"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('get-key')}
                  className="px-8 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 transition-colors"
                >
                  Got it, continue
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Get Your API Key */}
          {step === 'get-key' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-garamond font-bold text-midnight text-center">
                Get Your API Key
              </h2>
              <p className="text-faded-ink font-sans text-center">
                We use OpenRouter for AI access. It's free to create an account.
              </p>

              <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg text-center">
                <p className="text-sm font-sans text-blue-800 mb-4">
                  Click the button below to open OpenRouter and create your API key:
                </p>
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg font-sans font-semibold hover:bg-blue-700 transition-colors"
                >
                  Open OpenRouter →
                </a>
                <p className="text-xs font-sans text-blue-600 mt-4">
                  1. Click "Create Key" <br />
                  2. Copy the key (starts with sk-or-...)
                </p>
              </div>

              <div className="flex gap-3 justify-between">
                <button
                  onClick={() => setStep('explanation')}
                  className="px-6 py-3 text-faded-ink font-sans hover:underline"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('paste-test')}
                  className="px-8 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 transition-colors"
                >
                  I have my key
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Paste & Test */}
          {step === 'paste-test' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-garamond font-bold text-midnight text-center">
                Paste & Test Your Key
              </h2>

              <div className="space-y-3">
                <label className="block">
                  <span className="text-sm font-sans font-semibold text-midnight mb-1 block">
                    OpenRouter API Key
                  </span>
                  <div className="flex gap-2">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-or-v1-..."
                      className="flex-1 px-4 py-3 border border-slate-ui rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-bronze"
                    />
                    <button
                      onClick={() => setShowKey(!showKey)}
                      className="px-4 py-3 border border-slate-ui rounded-lg hover:bg-vellum transition-colors"
                      title={showKey ? 'Hide key' : 'Show key'}
                    >
                      {showKey ? '🙈' : '👁️'}
                    </button>
                  </div>
                </label>

                <button
                  onClick={handleTestKey}
                  disabled={testing || !apiKey.trim()}
                  className="w-full px-4 py-3 border-2 border-bronze text-bronze rounded-lg font-sans font-semibold hover:bg-bronze hover:text-white disabled:opacity-50 transition-colors"
                >
                  {testing ? 'Testing...' : 'Test Key'}
                </button>

                {testResult && (
                  <div className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    {testResult.success ? (
                      <p className="text-green-800 font-sans text-sm">
                        ✅ Key is valid! Credits available: {testResult.credits}
                      </p>
                    ) : (
                      <p className="text-red-800 font-sans text-sm">
                        ❌ Key is invalid. Please check and try again.
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="flex gap-3 justify-between">
                <button
                  onClick={() => setStep('get-key')}
                  className="px-6 py-3 text-faded-ink font-sans hover:underline"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('choose-model')}
                  disabled={!testResult?.success}
                  className="px-8 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 disabled:opacity-50 transition-colors"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 5: Choose Model */}
          {step === 'choose-model' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-garamond font-bold text-midnight text-center">
                Choose Your AI Model
              </h2>
              <p className="text-faded-ink font-sans text-center text-sm">
                You can change this anytime in Settings
              </p>

              <div className="space-y-3">
                {MODEL_RECOMMENDATIONS.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => setSelectedModel(model.id)}
                    className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                      selectedModel === model.id
                        ? 'border-bronze bg-bronze/5'
                        : 'border-slate-ui hover:border-bronze/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-midnight">{model.name}</span>
                      <span className="text-xs px-2 py-1 bg-bronze/10 text-bronze rounded-full">
                        {model.use}
                      </span>
                    </div>
                    <p className="text-sm text-faded-ink">{model.description}</p>
                    <p className="text-xs text-bronze mt-1">{model.cost}</p>
                    {model.recommended && (
                      <span className="inline-block text-xs text-green-600 mt-2">
                        ✓ Recommended for most writers
                      </span>
                    )}
                  </button>
                ))}
              </div>

              <div className="flex gap-3 justify-between">
                <button
                  onClick={() => setStep('paste-test')}
                  className="px-6 py-3 text-faded-ink font-sans hover:underline"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('success')}
                  className="px-8 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 transition-colors"
                >
                  Finish Setup
                </button>
              </div>
            </div>
          )}

          {/* Step 6: Success */}
          {step === 'success' && (
            <div className="text-center space-y-6">
              <div className="text-6xl animate-bounce">🎉</div>
              <h2 className="text-2xl font-garamond font-bold text-midnight">
                You're All Set!
              </h2>
              <p className="text-faded-ink font-sans">
                AI features are now enabled. Try generating a chapter recap or using the writing coach!
              </p>

              <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                <p className="text-sm text-green-800 font-sans">
                  <strong>Pro tip:</strong> Press <kbd className="px-2 py-1 bg-white rounded border">Cmd+Shift+R</kbd> to generate a recap for any chapter.
                </p>
              </div>

              <button
                onClick={handleComplete}
                className="px-8 py-4 bg-bronze text-white rounded-lg font-sans font-semibold text-lg hover:bg-bronze/90 transition-colors"
              >
                Start Writing!
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
