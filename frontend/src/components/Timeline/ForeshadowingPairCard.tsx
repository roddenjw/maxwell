/**
 * ForeshadowingPairCard - Display a single foreshadowing setup/payoff pair
 */

import { useState } from 'react';
import type { ForeshadowingPair, ForeshadowingType } from '@/types/foreshadowing';
import {
  FORESHADOWING_TYPE_LABELS,
  FORESHADOWING_TYPE_ICONS,
  FORESHADOWING_TYPE_DESCRIPTIONS,
} from '@/types/foreshadowing';
import { useTimelineStore } from '@/stores/timelineStore';
import { confirm } from '@/stores/confirmStore';

interface ForeshadowingPairCardProps {
  pair: ForeshadowingPair;
  onEdit?: (pair: ForeshadowingPair) => void;
  onDelete?: (pairId: string) => void;
  onLinkPayoff?: (pairId: string) => void;
  onUnlinkPayoff?: (pairId: string) => void;
}

export default function ForeshadowingPairCard({
  pair,
  onEdit,
  onDelete,
  onLinkPayoff,
  onUnlinkPayoff,
}: ForeshadowingPairCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { events } = useTimelineStore();

  // Get event details
  const setupEvent = events.find(e => e.id === pair.foreshadowing_event_id);
  const payoffEvent = pair.payoff_event_id
    ? events.find(e => e.id === pair.payoff_event_id)
    : null;

  const typeIcon = FORESHADOWING_TYPE_ICONS[pair.foreshadowing_type as ForeshadowingType] || '💡';
  const typeLabel = FORESHADOWING_TYPE_LABELS[pair.foreshadowing_type as ForeshadowingType] || pair.foreshadowing_type;
  const typeDescription = FORESHADOWING_TYPE_DESCRIPTIONS[pair.foreshadowing_type as ForeshadowingType] || '';

  return (
    <div
      className={`
        border bg-white p-4 transition-all
        ${pair.is_resolved ? 'border-sage/50' : 'border-bronze'}
      `}
      style={{ borderRadius: '2px' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl" title={typeDescription}>
            {typeIcon}
          </span>
          <div>
            <span className="text-xs font-sans text-faded-ink uppercase">
              {typeLabel}
            </span>
            {!pair.is_resolved && (
              <span className="ml-2 text-xs font-sans px-2 py-0.5 bg-bronze/20 text-bronze rounded-full">
                Unresolved
              </span>
            )}
            {pair.is_resolved && (
              <span className="ml-2 text-xs font-sans px-2 py-0.5 bg-sage/20 text-sage rounded-full">
                Resolved
              </span>
            )}
          </div>
        </div>

        {/* Confidence indicator */}
        <div className="flex items-center gap-1" title={`Confidence: ${pair.confidence}/10`}>
          {[...Array(10)].map((_, i) => (
            <div
              key={i}
              className={`w-1.5 h-3 ${i < pair.confidence ? 'bg-bronze' : 'bg-slate-ui'}`}
              style={{ borderRadius: '1px' }}
            />
          ))}
        </div>
      </div>

      {/* Setup */}
      <div className="mt-3">
        <p className="text-xs font-sans text-faded-ink uppercase mb-1">Setup</p>
        <p className="text-sm font-serif text-midnight">
          {pair.foreshadowing_text}
        </p>
        {setupEvent && (
          <p className="text-xs font-sans text-faded-ink mt-1">
            Event #{setupEvent.order_index}: {setupEvent.description.slice(0, 50)}...
          </p>
        )}
      </div>

      {/* Payoff (if resolved) */}
      {pair.is_resolved && pair.payoff_text && (
        <div className="mt-3 pt-3 border-t border-slate-ui">
          <p className="text-xs font-sans text-faded-ink uppercase mb-1">Payoff</p>
          <p className="text-sm font-serif text-midnight">
            {pair.payoff_text}
          </p>
          {payoffEvent && (
            <p className="text-xs font-sans text-faded-ink mt-1">
              Event #{payoffEvent.order_index}: {payoffEvent.description.slice(0, 50)}...
            </p>
          )}
        </div>
      )}

      {/* Expand/Collapse for notes */}
      {pair.notes && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-xs font-sans text-bronze hover:underline"
        >
          {expanded ? '− Hide notes' : '+ Show notes'}
        </button>
      )}

      {expanded && pair.notes && (
        <div className="mt-2 p-2 bg-vellum text-sm font-sans text-faded-ink">
          {pair.notes}
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 pt-3 border-t border-slate-ui flex items-center gap-2">
        {!pair.is_resolved && onLinkPayoff && (
          <button
            onClick={() => onLinkPayoff(pair.id)}
            className="px-3 py-1.5 bg-bronze text-white text-xs font-sans hover:bg-opacity-90 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Link Payoff
          </button>
        )}

        {pair.is_resolved && onUnlinkPayoff && (
          <button
            onClick={() => onUnlinkPayoff(pair.id)}
            className="px-3 py-1.5 bg-slate-ui text-midnight text-xs font-sans hover:bg-opacity-80 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Unlink Payoff
          </button>
        )}

        {onEdit && (
          <button
            onClick={() => onEdit(pair)}
            className="px-3 py-1.5 border border-slate-ui text-midnight text-xs font-sans hover:bg-vellum transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Edit
          </button>
        )}

        {onDelete && (
          <button
            onClick={async () => {
              if (await confirm({ title: 'Delete Pair', message: 'Delete this foreshadowing pair?', variant: 'danger', confirmLabel: 'Delete' })) {
                onDelete(pair.id);
              }
            }}
            className="px-3 py-1.5 text-redline text-xs font-sans hover:bg-redline/10 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
