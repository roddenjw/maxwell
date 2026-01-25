/**
 * ContextualTooltip - Shows helpful tips on first interaction with features
 */

import { useState, useEffect, useRef } from 'react';

interface ContextualTooltipProps {
  /** Unique identifier for this tooltip (used for "don't show again") */
  id: string;
  /** Title of the tooltip */
  title: string;
  /** Description/content */
  content: string;
  /** Whether to show the tooltip */
  show: boolean;
  /** Position relative to the target element */
  position?: 'top' | 'bottom' | 'left' | 'right';
  /** Callback when tooltip is dismissed */
  onDismiss?: () => void;
  /** Additional class name */
  className?: string;
  /** Children to wrap (the element the tooltip points to) */
  children: React.ReactNode;
}

// Check if tooltip has been dismissed
function isTooltipDismissed(id: string): boolean {
  try {
    const dismissed = localStorage.getItem('maxwell_dismissed_tooltips');
    if (dismissed) {
      const list = JSON.parse(dismissed);
      return Array.isArray(list) && list.includes(id);
    }
  } catch (e) {
    // Ignore
  }
  return false;
}

// Mark tooltip as dismissed
function dismissTooltip(id: string): void {
  try {
    const dismissed = localStorage.getItem('maxwell_dismissed_tooltips');
    const list = dismissed ? JSON.parse(dismissed) : [];
    if (!list.includes(id)) {
      list.push(id);
      localStorage.setItem('maxwell_dismissed_tooltips', JSON.stringify(list));
    }
  } catch (e) {
    // Ignore
  }
}

export default function ContextualTooltip({
  id,
  title,
  content,
  show,
  position = 'bottom',
  onDismiss,
  className = '',
  children,
}: ContextualTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const targetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check if already dismissed
    if (isTooltipDismissed(id)) {
      setIsVisible(false);
      return;
    }

    setIsVisible(show);
  }, [id, show]);

  const handleDismiss = () => {
    setIsVisible(false);

    if (dontShowAgain) {
      dismissTooltip(id);
    }

    onDismiss?.();
  };

  // Calculate tooltip position styles
  const getPositionStyles = (): React.CSSProperties => {
    switch (position) {
      case 'top':
        return {
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: '8px',
        };
      case 'bottom':
        return {
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginTop: '8px',
        };
      case 'left':
        return {
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginRight: '8px',
        };
      case 'right':
        return {
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginLeft: '8px',
        };
      default:
        return {};
    }
  };

  // Get arrow styles
  const getArrowStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'absolute',
      width: '0',
      height: '0',
      borderStyle: 'solid',
    };

    switch (position) {
      case 'top':
        return {
          ...base,
          bottom: '-6px',
          left: '50%',
          transform: 'translateX(-50%)',
          borderWidth: '6px 6px 0 6px',
          borderColor: '#b87333 transparent transparent transparent',
        };
      case 'bottom':
        return {
          ...base,
          top: '-6px',
          left: '50%',
          transform: 'translateX(-50%)',
          borderWidth: '0 6px 6px 6px',
          borderColor: 'transparent transparent #b87333 transparent',
        };
      case 'left':
        return {
          ...base,
          right: '-6px',
          top: '50%',
          transform: 'translateY(-50%)',
          borderWidth: '6px 0 6px 6px',
          borderColor: 'transparent transparent transparent #b87333',
        };
      case 'right':
        return {
          ...base,
          left: '-6px',
          top: '50%',
          transform: 'translateY(-50%)',
          borderWidth: '6px 6px 6px 0',
          borderColor: 'transparent #b87333 transparent transparent',
        };
      default:
        return base;
    }
  };

  return (
    <div ref={targetRef} className={`relative inline-block ${className}`}>
      {children}

      {isVisible && (
        <div
          className="absolute z-50 w-64 animate-fade-in"
          style={getPositionStyles()}
        >
          {/* Arrow */}
          <div style={getArrowStyles()} />

          {/* Tooltip content */}
          <div className="bg-bronze text-white rounded-lg shadow-lg p-4">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="font-semibold text-sm">{title}</h4>
              <button
                onClick={handleDismiss}
                className="text-white/70 hover:text-white text-lg leading-none"
              >
                ×
              </button>
            </div>
            <p className="text-sm text-white/90 mb-3">{content}</p>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs text-white/70 cursor-pointer">
                <input
                  type="checkbox"
                  checked={dontShowAgain}
                  onChange={(e) => setDontShowAgain(e.target.checked)}
                  className="w-3 h-3 rounded"
                />
                Don't show again
              </label>
              <button
                onClick={handleDismiss}
                className="text-xs bg-white/20 hover:bg-white/30 px-3 py-1 rounded transition-colors"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Hook to manage contextual help visibility
 */
export function useContextualHelp(featureId: string) {
  const [hasInteracted, setHasInteracted] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    // Check if user has already interacted with this feature
    const interacted = localStorage.getItem(`maxwell_interacted_${featureId}`);
    setHasInteracted(!!interacted);

    // Show tooltip if not interacted and not dismissed
    if (!interacted && !isTooltipDismissed(featureId)) {
      setShowTooltip(true);
    }
  }, [featureId]);

  const markInteracted = () => {
    setHasInteracted(true);
    setShowTooltip(false);
    localStorage.setItem(`maxwell_interacted_${featureId}`, 'true');
  };

  const dismissTooltipHelper = () => {
    setShowTooltip(false);
  };

  return {
    hasInteracted,
    showTooltip,
    markInteracted,
    dismissTooltip: dismissTooltipHelper,
  };
}
