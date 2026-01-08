/**
 * OutlineCompletionDonut - Visual progress indicator for story outline
 *
 * Pure SVG donut chart showing completed vs incomplete plot beats.
 * Uses stroke-dasharray and stroke-dashoffset to create animated progress arc.
 *
 * Features:
 * - Smooth 700ms animation on progress changes
 * - Bronze/slate-ui color scheme matching Maxwell design system
 * - Center text displaying percentage and beat counts
 * - Handles edge cases (0%, 100%, no beats)
 * - Zero dependencies (pure SVG + CSS)
 */

import { useMemo } from 'react';

interface OutlineCompletionDonutProps {
  completed: number;    // Completed beats count
  total: number;        // Total beats count
  percentage: number;   // 0-100
  size?: number;       // Optional: diameter in px (default 140)
}

export default function OutlineCompletionDonut({
  completed,
  total,
  percentage,
  size = 140,
}: OutlineCompletionDonutProps) {
  // Calculate donut dimensions
  const radius = size / 2;
  const strokeWidth = size * 0.128; // ~18px for 140px (ratio maintains consistency)
  const innerRadius = radius - strokeWidth;
  const circumference = 2 * Math.PI * innerRadius;

  // Calculate arc length for completed portion
  // Uses useMemo to avoid recalculation on every render
  const completedArcLength = useMemo(() => {
    return (percentage / 100) * circumference;
  }, [percentage, circumference]);

  // SVG center point
  const center = radius;

  // Edge case handling
  const displayPercentage = Math.max(0, Math.min(100, percentage)); // Clamp to 0-100
  const isComplete = percentage === 100;
  const isEmpty = percentage === 0 || total === 0;

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Donut Chart SVG */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-90" // Start at top (12 o'clock) instead of right (3 o'clock)
        >
          {/* Background Circle (incomplete segment - slate-ui) */}
          <circle
            cx={center}
            cy={center}
            r={innerRadius}
            fill="none"
            stroke="#E2E8F0"  // slate-ui
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Foreground Circle (completed segment - bronze) */}
          {/* Only render if there's progress > 0% */}
          {!isEmpty && (
            <circle
              cx={center}
              cy={center}
              r={innerRadius}
              fill="none"
              stroke="#B48E55"  // bronze
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circumference}  // Full circle length
              strokeDashoffset={circumference - completedArcLength}  // Hide uncompleted portion
              className="transition-all duration-700 ease-in-out"  // Smooth animation
            />
          )}
        </svg>

        {/* Center Text Overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {/* Percentage - Large, bold, changes to bronze when 100% complete */}
          <div
            className="text-4xl font-serif font-bold"
            style={{ color: isComplete ? '#B48E55' : '#1E293B' }}  // bronze if complete, midnight otherwise
          >
            {displayPercentage}%
          </div>

          {/* Beat Count - Small, faded */}
          <div className="text-xs font-sans text-faded-ink mt-0.5">
            {completed} of {total} beats
          </div>
        </div>
      </div>

      {/* Optional Label */}
      <p className="text-xs font-sans text-faded-ink uppercase tracking-wider">
        Completion
      </p>
    </div>
  );
}
