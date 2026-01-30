/**
 * AIGenerationProgress Component
 * Shows a visually engaging progress indicator during AI generation
 */

import { useState, useEffect } from 'react';

interface AIGenerationProgressProps {
  isGenerating: boolean;
  message?: string;
  estimatedSeconds?: number; // Optional estimate
}

export function AIGenerationProgress({
  isGenerating,
  message = 'Generating...',
  estimatedSeconds,
}: AIGenerationProgressProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [animationPhase, setAnimationPhase] = useState(0);

  // Reset and track elapsed time
  useEffect(() => {
    if (!isGenerating) {
      setElapsedSeconds(0);
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isGenerating]);

  // Animate phases
  useEffect(() => {
    if (!isGenerating) return;

    const interval = setInterval(() => {
      setAnimationPhase((prev) => (prev + 1) % 4);
    }, 500);

    return () => clearInterval(interval);
  }, [isGenerating]);

  if (!isGenerating) return null;

  // Format elapsed time
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  // Progress estimation (if provided)
  const progressPercent = estimatedSeconds
    ? Math.min((elapsedSeconds / estimatedSeconds) * 100, 95) // Cap at 95% to show it's still working
    : null;

  // Fun phrases that cycle
  const phrases = [
    'Brainstorming ideas...',
    'Exploring possibilities...',
    'Crafting concepts...',
    'Weaving narratives...',
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-midnight/50 backdrop-blur-sm">
      <div className="bg-white p-8 shadow-book max-w-md w-full mx-4" style={{ borderRadius: '4px' }}>
        {/* Animated Icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            {/* Outer spinning ring */}
            <div className="w-20 h-20 rounded-full border-4 border-bronze/20 animate-pulse" />
            {/* Inner spinning element */}
            <div
              className="absolute inset-0 w-20 h-20 rounded-full border-4 border-transparent border-t-bronze animate-spin"
              style={{ animationDuration: '1s' }}
            />
            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center text-3xl">
              {['✨', '🎭', '📝', '💡'][animationPhase]}
            </div>
          </div>
        </div>

        {/* Message */}
        <h3 className="font-serif text-xl font-bold text-midnight text-center mb-2">
          {message}
        </h3>

        {/* Animated phrase */}
        <p className="text-sm font-sans text-faded-ink text-center mb-4">
          {phrases[animationPhase]}
        </p>

        {/* Progress bar (if estimate provided) */}
        {progressPercent !== null && (
          <div className="mb-4">
            <div className="h-2 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
              <div
                className="h-full bg-bronze transition-all duration-500 ease-out"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}

        {/* Elapsed time */}
        <div className="flex items-center justify-center gap-2 text-sm font-sans text-faded-ink">
          <span>Elapsed:</span>
          <span className="font-semibold text-midnight">{formatTime(elapsedSeconds)}</span>
          {estimatedSeconds && elapsedSeconds < estimatedSeconds && (
            <span className="text-faded-ink">
              (est. {formatTime(estimatedSeconds)})
            </span>
          )}
        </div>

        {/* Tip */}
        <p className="text-xs font-sans text-faded-ink text-center mt-4 italic">
          AI generation typically takes 10-30 seconds depending on complexity
        </p>
      </div>
    </div>
  );
}

export default AIGenerationProgress;
