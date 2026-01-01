/**
 * FeatureTour - Interactive feature discovery tour
 * Shows tooltips pointing to key features in the app
 */

import { useState, useEffect } from 'react';

interface FeatureTourProps {
  onComplete: () => void;
  onSkip: () => void;
}

interface TourStep {
  id: string;
  title: string;
  description: string;
  targetSelector: string;
  position: 'top' | 'right' | 'bottom' | 'left';
  highlightPadding?: number;
}

export default function FeatureTour({ onComplete, onSkip }: FeatureTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const [highlightPosition, setHighlightPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });

  const steps: TourStep[] = [
    {
      id: 'chapters',
      title: 'Chapter Navigator',
      description: 'Create and organize chapters. Drag to reorder, right-click for options.',
      targetSelector: '[data-tour="chapters-nav"]',
      position: 'right',
      highlightPadding: 8
    },
    {
      id: 'editor',
      title: 'Writing Editor',
      description: 'Your distraction-free writing space. Auto-saves every 5 seconds.',
      targetSelector: '[data-tour="editor"]',
      position: 'left',
      highlightPadding: 16
    },
    {
      id: 'codex',
      title: 'The Codex',
      description: 'Track characters, locations, and lore automatically as you write.',
      targetSelector: '[data-tour="codex-button"]',
      position: 'right',
      highlightPadding: 8
    },
    {
      id: 'timeline',
      title: 'Timeline',
      description: 'Visualize story events and maintain chronological consistency.',
      targetSelector: '[data-tour="timeline-button"]',
      position: 'right',
      highlightPadding: 8
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'Track your writing progress, streaks, and productivity.',
      targetSelector: '[data-tour="analytics-button"]',
      position: 'right',
      highlightPadding: 8
    },
    {
      id: 'coach',
      title: 'Fast Coach',
      description: 'Get real-time writing suggestions to improve your prose.',
      targetSelector: '[data-tour="coach-button"]',
      position: 'right',
      highlightPadding: 8
    }
  ];

  const currentStepData = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;

  useEffect(() => {
    updatePosition();
    window.addEventListener('resize', updatePosition);
    return () => window.removeEventListener('resize', updatePosition);
  }, [currentStep]);

  const updatePosition = () => {
    if (!currentStepData) return;

    const element = document.querySelector(currentStepData.targetSelector);
    if (!element) {
      console.warn(`Tour target not found: ${currentStepData.targetSelector}`);
      return;
    }

    const rect = element.getBoundingClientRect();
    const padding = currentStepData.highlightPadding || 8;

    // Set highlight position
    setHighlightPosition({
      top: rect.top - padding,
      left: rect.left - padding,
      width: rect.width + (padding * 2),
      height: rect.height + (padding * 2)
    });

    // Calculate tooltip position based on position prop
    let tooltipTop = 0;
    let tooltipLeft = 0;
    const tooltipWidth = 320; // approximate
    const tooltipHeight = 150; // approximate

    switch (currentStepData.position) {
      case 'right':
        tooltipTop = rect.top + (rect.height / 2) - (tooltipHeight / 2);
        tooltipLeft = rect.right + 20;
        break;
      case 'left':
        tooltipTop = rect.top + (rect.height / 2) - (tooltipHeight / 2);
        tooltipLeft = rect.left - tooltipWidth - 20;
        break;
      case 'bottom':
        tooltipTop = rect.bottom + 20;
        tooltipLeft = rect.left + (rect.width / 2) - (tooltipWidth / 2);
        break;
      case 'top':
        tooltipTop = rect.top - tooltipHeight - 20;
        tooltipLeft = rect.left + (rect.width / 2) - (tooltipWidth / 2);
        break;
    }

    setTooltipPosition({ top: tooltipTop, left: tooltipLeft });
  };

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  if (!currentStepData) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/60 z-[250]" onClick={onSkip} />

      {/* Highlight ring around target element */}
      <div
        className="fixed z-[251] rounded-sm pointer-events-none transition-all duration-300"
        style={{
          top: `${highlightPosition.top}px`,
          left: `${highlightPosition.left}px`,
          width: `${highlightPosition.width}px`,
          height: `${highlightPosition.height}px`,
          boxShadow: '0 0 0 4px rgba(205, 127, 50, 0.8), 0 0 0 9999px rgba(0, 0, 0, 0.6)',
        }}
      />

      {/* Tooltip */}
      <div
        className="fixed z-[252] bg-white rounded-sm shadow-2xl border-2 border-bronze transition-all duration-300"
        style={{
          top: `${tooltipPosition.top}px`,
          left: `${tooltipPosition.left}px`,
          width: '320px',
        }}
      >
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-garamond text-xl font-semibold text-midnight">
              {currentStepData.title}
            </h3>
            <button
              onClick={onSkip}
              className="text-faded-ink hover:text-midnight transition-colors text-sm font-sans"
            >
              Skip
            </button>
          </div>

          {/* Description */}
          <p className="text-faded-ink font-sans text-sm leading-relaxed mb-4">
            {currentStepData.description}
          </p>

          {/* Progress */}
          <div className="flex items-center gap-2 mb-4">
            <div className="flex gap-1 flex-1">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`h-1 flex-1 rounded-full transition-all ${
                    index <= currentStep ? 'bg-bronze' : 'bg-slate-ui/30'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-faded-ink font-sans">
              {currentStep + 1}/{steps.length}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="px-4 py-2 text-faded-ink hover:text-midnight transition-colors font-sans text-sm disabled:opacity-30"
            >
              ← Back
            </button>
            <button
              onClick={handleNext}
              className="px-5 py-2 bg-bronze text-white rounded-sm font-semibold font-sans text-sm hover:bg-bronze/90 transition-colors"
            >
              {isLastStep ? 'Finish' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
