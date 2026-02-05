/**
 * WritingIssueHoverCard - Floating tooltip for writing issues
 * Shows issue details, suggestions, and quick-fix buttons when hovering
 * over highlighted text in the editor.
 */

import { createPortal } from 'react-dom';
import type { WritingIssue } from '@/types/writingFeedback';
import { getIssueTypeConfig } from '@/types/writingFeedback';
import { Z_INDEX } from '@/lib/zIndex';

interface WritingIssueHoverCardProps {
  issue: WritingIssue;
  position: { x: number; y: number };
  onApplyFix: (suggestion: string) => void;
  onIgnore: () => void;
  onAddToDict?: () => void;
  onIgnoreRule?: () => void;
}

export function WritingIssueHoverCard({
  issue,
  position,
  onApplyFix,
  onIgnore,
  onAddToDict,
  onIgnoreRule,
}: WritingIssueHoverCardProps) {
  const config = getIssueTypeConfig(issue.type);

  // Calculate position - flip above if near bottom of viewport
  const viewportHeight = window.innerHeight;
  const cardHeight = 200; // Approximate max card height
  const shouldFlipUp = position.y + cardHeight > viewportHeight - 20;

  // Keep card within horizontal bounds
  const viewportWidth = window.innerWidth;
  const cardWidth = 320;
  let adjustedX = position.x;
  if (adjustedX + cardWidth > viewportWidth - 20) {
    adjustedX = viewportWidth - cardWidth - 20;
  }
  if (adjustedX < 20) {
    adjustedX = 20;
  }

  const style: React.CSSProperties = {
    position: 'fixed',
    left: adjustedX,
    top: shouldFlipUp ? 'auto' : position.y + 8,
    bottom: shouldFlipUp ? viewportHeight - position.y + 8 : 'auto',
    zIndex: Z_INDEX.HOVER_CARD,
    width: cardWidth,
    maxWidth: 'calc(100vw - 40px)',
  };

  const card = (
    <div
      style={style}
      className="bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden animate-in fade-in-0 zoom-in-95 duration-100"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-base flex-shrink-0">{config.icon}</span>
          <span className={`font-medium ${config.headerClass}`}>
            {config.label}
          </span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${config.badgeClass}`}
        >
          {issue.severity}
        </span>
      </div>

      {/* Message */}
      <div className="px-3 py-2 border-b border-slate-50">
        <p className="text-sm text-midnight">{issue.message}</p>
        {issue.original_text && (
          <p className="text-xs text-faded-ink mt-1">
            <span className="font-medium">Found:</span>{' '}
            <span className="bg-red-50 px-1 rounded">{issue.original_text}</span>
          </p>
        )}
      </div>

      {/* Suggestions */}
      {issue.suggestions.length > 0 && (
        <div className="px-3 py-2 border-b border-slate-50">
          <p className="text-xs text-faded-ink mb-1.5">Suggestions:</p>
          <div className="flex flex-wrap gap-1.5">
            {issue.suggestions.slice(0, 5).map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => onApplyFix(suggestion)}
                className="px-2 py-1 text-sm bg-green-50 text-green-700 hover:bg-green-100 rounded border border-green-200 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Teaching Point */}
      {issue.teaching_point && (
        <div className="px-3 py-2 bg-amber-50/50 border-b border-slate-50">
          <div className="flex items-start gap-2">
            <span className="text-amber-500 flex-shrink-0">💡</span>
            <p className="text-xs text-amber-800 leading-relaxed">
              {issue.teaching_point}
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="px-3 py-2 flex items-center gap-2 bg-slate-50">
        {issue.suggestions[0] && (
          <button
            onClick={() => onApplyFix(issue.suggestions[0])}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-bronze text-white hover:bg-bronze/90 rounded transition-colors"
          >
            <span>✓</span>
            <span>Fix</span>
          </button>
        )}

        {issue.type === 'spelling' && onAddToDict && (
          <button
            onClick={onAddToDict}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
          >
            <span>+</span>
            <span>Add to Dictionary</span>
          </button>
        )}

        <button
          onClick={onIgnore}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
        >
          <span>Ignore</span>
        </button>

        {issue.rule_id && onIgnoreRule && (
          <button
            onClick={onIgnoreRule}
            className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
            title={`Ignore all "${issue.rule_id}" issues`}
          >
            <span>Ignore Rule</span>
          </button>
        )}
      </div>
    </div>
  );

  return createPortal(card, document.body);
}
