/**
 * WelcomeModal - First-time user welcome experience
 * Introduces Maxwell's features and creates sample manuscript
 */

import { useState } from 'react';
import { toast } from '@/stores/toastStore';

interface WelcomeModalProps {
  onComplete: (manuscriptId?: string, manuscriptData?: {title: string; wordCount: number}) => void;
  onSkip: () => void;
}

export default function WelcomeModal({ onComplete, onSkip }: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const steps = [
    {
      title: "Welcome to Maxwell",
      icon: "✨",
      description: "The fiction writing IDE that feels magical",
      content: (
        <div className="space-y-4">
          <p className="text-midnight font-sans leading-relaxed">
            Maxwell is a professional writing environment designed for novelists,
            with powerful features that work invisibly in the background.
          </p>
          <p className="text-midnight font-sans leading-relaxed">
            Let's take a quick tour to help you get started!
          </p>
        </div>
      )
    },
    {
      title: "Your Writing Workspace",
      icon: "📑",
      description: "Organize chapters like a pro",
      content: (
        <div className="space-y-4">
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <h4 className="font-sans font-semibold text-midnight mb-2">Chapters & Folders</h4>
            <p className="text-sm text-faded-ink">
              Organize your manuscript with intuitive drag-and-drop chapters and folders.
              Keep your story structure exactly how you envision it.
            </p>
          </div>
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <h4 className="font-sans font-semibold text-midnight mb-2">Rich Text Editor</h4>
            <p className="text-sm text-faded-ink">
              Beautiful, distraction-free writing with all the formatting tools you need.
            </p>
          </div>
        </div>
      )
    },
    {
      title: "Smart Features",
      icon: "🧠",
      description: "AI-powered writing assistance",
      content: (
        <div className="space-y-4">
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📖</span>
              <div>
                <h4 className="font-sans font-semibold text-midnight">Codex</h4>
                <p className="text-sm text-faded-ink">
                  Automatic character and world tracking. Never forget a detail again.
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📜</span>
              <div>
                <h4 className="font-sans font-semibold text-midnight">Timeline</h4>
                <p className="text-sm text-faded-ink">
                  Track events and maintain consistency across your story.
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">✨</span>
              <div>
                <h4 className="font-sans font-semibold text-midnight">Fast Coach</h4>
                <p className="text-sm text-faded-ink">
                  Real-time writing suggestions to polish your prose.
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Analytics & Export",
      icon: "📊",
      description: "Track progress and share your work",
      content: (
        <div className="space-y-4">
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📊</span>
              <div>
                <h4 className="font-sans font-semibold text-midnight">Writing Analytics</h4>
                <p className="text-sm text-faded-ink">
                  Track your writing streaks, daily progress, and productivity trends.
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white border-2 border-bronze/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📥</span>
              <div>
                <h4 className="font-sans font-semibold text-midnight">Professional Export</h4>
                <p className="text-sm text-faded-ink">
                  Export to DOCX and PDF with industry-standard formatting.
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Ready to Write?",
      icon: "🚀",
      description: "Start with a sample or create your own",
      content: (
        <div className="space-y-4">
          <p className="text-midnight font-sans leading-relaxed">
            We've prepared a sample manuscript to help you explore Maxwell's features.
            It includes three chapters with characters, dialogue, and a mysterious plot!
          </p>
          <div className="bg-bronze/10 border-2 border-bronze/30 rounded-sm p-4">
            <h4 className="font-sans font-semibold text-midnight mb-2">Sample Manuscript</h4>
            <ul className="text-sm text-faded-ink space-y-1">
              <li>• 3 complete chapters</li>
              <li>• Pre-filled with engaging content</li>
              <li>• Try all features immediately</li>
              <li>• Delete anytime and start fresh</li>
            </ul>
          </div>
          <p className="text-sm text-faded-ink font-sans italic">
            Or skip the sample and start with a blank manuscript.
          </p>
        </div>
      )
    }
  ];

  const currentStepData = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      handleCreateSample();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleCreateSample = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/onboarding/create-sample-manuscript', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to create sample manuscript');
      }

      const data = await response.json();
      toast.success('Sample manuscript created! Explore and enjoy.');

      // Pass both manuscript ID and metadata to onComplete
      onComplete(data.data.manuscript_id, {
        title: data.data.title,
        wordCount: data.data.total_words
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to create sample';
      toast.error(errorMsg);
      console.error('Sample creation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipToBlank = () => {
    onComplete();
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[300] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-2xl w-full">
        {/* Header */}
        <div className="px-6 py-4 border-b-2 border-bronze/30 bg-gradient-to-r from-bronze/5 to-white">
          <div className="flex items-center gap-4">
            <div className="text-5xl">{currentStepData.icon}</div>
            <div className="flex-1">
              <h2 className="font-garamond text-3xl font-semibold text-midnight">
                {currentStepData.title}
              </h2>
              <p className="text-faded-ink font-sans text-sm mt-1">
                {currentStepData.description}
              </p>
            </div>
            <button
              onClick={onSkip}
              className="text-faded-ink hover:text-midnight transition-colors text-sm font-sans"
            >
              Skip tour
            </button>
          </div>

          {/* Progress indicator */}
          <div className="flex gap-2 mt-4">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`flex-1 h-1 rounded-full transition-all ${
                  index <= currentStep ? 'bg-bronze' : 'bg-slate-ui/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 min-h-[300px]">
          {currentStepData.content}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t-2 border-slate-ui/30 flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="px-4 py-2 text-faded-ink hover:text-midnight transition-colors font-sans disabled:opacity-0"
          >
            ← Back
          </button>

          <div className="flex gap-3">
            {isLastStep && (
              <button
                onClick={handleSkipToBlank}
                className="px-6 py-2 bg-white border-2 border-slate-ui text-midnight rounded-sm font-sans hover:border-bronze transition-colors"
              >
                Start Blank
              </button>
            )}
            <button
              onClick={handleNext}
              disabled={loading}
              className="px-6 py-2 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Creating...</span>
                </>
              ) : isLastStep ? (
                <>
                  <span>Create Sample</span>
                  <span>→</span>
                </>
              ) : (
                <>
                  <span>Next</span>
                  <span>→</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
