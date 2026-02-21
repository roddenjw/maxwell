/**
 * FillFromManuscriptModal Component
 *
 * Review modal for the "Fill from Manuscript" AI feature.
 * Shows the AI's beat-to-chapter mappings, gaps, pacing notes,
 * and allows per-mapping refinement via RefinementPanel.
 */

import { createPortal } from 'react-dom';
import { useState } from 'react';
import { Z_INDEX } from '@/lib/zIndex';
import RefinementPanel from '../shared/RefinementPanel';
import type { Outline } from '@/types/outline';

interface FillResult {
  outline: Outline;
  suggested_structure: string;
  structure_rationale: string;
  gaps: Array<{
    beat_name: string;
    position_percent: number;
    description: string;
    severity: 'high' | 'medium' | 'low';
    suggestion: string;
  }>;
  pacing_notes: string;
  beats_created: number;
  scenes_created: number;
}

interface FillFromManuscriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: FillResult;
  cost?: { formatted: string };
  onReload: () => void;
}

export default function FillFromManuscriptModal({
  isOpen,
  onClose,
  result,
  cost,
  onReload,
}: FillFromManuscriptModalProps) {
  const [refiningBeatIndex, setRefiningBeatIndex] = useState<number | null>(null);

  if (!isOpen) return null;

  const sortedBeats = result.outline.plot_beats
    ? [...result.outline.plot_beats].sort((a, b) => a.order_index - b.order_index)
    : [];

  const handleDone = () => {
    onReload();
    onClose();
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-700 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-300';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 bg-midnight/50 flex items-center justify-center p-4"
      style={{ zIndex: Z_INDEX.MODAL_BACKDROP }}
    >
      <div
        className="bg-white max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-book"
        style={{ borderRadius: '2px', zIndex: Z_INDEX.MODAL }}
      >
        {/* Header */}
        <div className="flex-shrink-0 border-b-2 border-slate-ui p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-serif text-2xl font-bold text-midnight mb-1">
                Structure Mapped from Manuscript
              </h2>
              <div className="flex items-center gap-3 flex-wrap">
                {result.suggested_structure && (
                  <span
                    className="px-2 py-0.5 bg-bronze/10 text-bronze font-sans text-sm font-medium"
                    style={{ borderRadius: '2px' }}
                  >
                    {result.suggested_structure}
                  </span>
                )}
                <span className="font-sans text-sm text-faded-ink">
                  {result.beats_created} beats, {result.scenes_created} scenes created
                </span>
                {cost && (
                  <span className="font-sans text-sm text-green-600 font-medium">
                    Cost: {cost.formatted}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center hover:bg-slate-ui/30 text-faded-ink hover:text-midnight transition-colors"
              style={{ borderRadius: '2px' }}
            >
              ✕
            </button>
          </div>

          {/* Structure Rationale */}
          {result.structure_rationale && (
            <p className="mt-3 text-sm font-sans text-faded-ink italic">
              {result.structure_rationale}
            </p>
          )}
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Beat Mappings */}
          <div>
            <h3 className="font-sans font-semibold text-midnight text-sm uppercase tracking-wider mb-3">
              Beat Mappings
            </h3>
            <div className="space-y-2">
              {sortedBeats.filter(b => b.item_type === 'BEAT').map((beat, idx) => (
                <div
                  key={beat.id}
                  className="p-3 border border-slate-ui hover:border-bronze/30 transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-sans font-bold text-bronze uppercase tracking-wider">
                          {beat.beat_name}
                        </span>
                        <span className="text-xs font-sans text-faded-ink">
                          {Math.round(beat.target_position_percent * 100)}%
                        </span>
                      </div>
                      <h4 className="font-serif font-bold text-base text-midnight mb-1">
                        {beat.beat_label}
                      </h4>
                      {beat.beat_description && (
                        <p className="text-sm font-sans text-faded-ink leading-snug">
                          {beat.beat_description}
                        </p>
                      )}
                      {beat.chapter_id && (
                        <div className="mt-1 flex items-center gap-1.5 text-xs text-bronze">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.102m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          <span className="font-medium">Linked to chapter</span>
                        </div>
                      )}
                    </div>

                    {/* Refine button */}
                    <button
                      onClick={() => setRefiningBeatIndex(refiningBeatIndex === idx ? null : idx)}
                      className={`flex-shrink-0 px-2 py-1 text-xs font-sans font-medium transition-colors flex items-center gap-1 ${
                        refiningBeatIndex === idx
                          ? 'bg-purple-100 text-purple-700 border border-purple-300'
                          : 'text-purple-600 hover:bg-purple-50 border border-transparent'
                      }`}
                      style={{ borderRadius: '2px' }}
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Refine
                    </button>
                  </div>

                  {/* Inline refinement */}
                  {refiningBeatIndex === idx && (
                    <RefinementPanel
                      suggestion={{
                        beat_name: beat.beat_name,
                        beat_label: beat.beat_label,
                        description: beat.beat_description || '',
                        chapter_id: beat.chapter_id || null,
                      }}
                      domain="beat_mapping"
                      context={{
                        beat_name: beat.beat_name,
                        beat_label: beat.beat_label,
                        position: `${Math.round(beat.target_position_percent * 100)}% through story`,
                        structure: result.suggested_structure || '',
                      }}
                      renderSuggestion={(s) => (
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-sans font-bold text-bronze uppercase">
                              {s.beat_name}
                            </span>
                            <span className="font-serif font-bold text-sm text-midnight">
                              {s.beat_label}
                            </span>
                          </div>
                          <p className="text-sm font-sans text-faded-ink">{s.description}</p>
                        </div>
                      )}
                      onAccept={() => {
                        // The refinement result is noted; user can re-run fill or manually edit
                        setRefiningBeatIndex(null);
                      }}
                      onCancel={() => setRefiningBeatIndex(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <div>
              <h3 className="font-sans font-semibold text-midnight text-sm uppercase tracking-wider mb-3">
                Structural Gaps
              </h3>
              <div className="space-y-2">
                {result.gaps.map((gap, i) => (
                  <div
                    key={i}
                    className="p-3 border-l-4 border border-slate-ui"
                    style={{
                      borderLeftColor: gap.severity === 'high' ? '#ef4444' : gap.severity === 'medium' ? '#f59e0b' : '#3b82f6',
                      borderRadius: '2px',
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`px-1.5 py-0.5 text-xs font-sans font-bold uppercase border ${severityColor(gap.severity)}`}
                        style={{ borderRadius: '2px' }}
                      >
                        {gap.severity}
                      </span>
                      <span className="text-xs font-sans text-faded-ink">
                        {gap.beat_name} ({Math.round(gap.position_percent * 100)}%)
                      </span>
                    </div>
                    <p className="text-sm font-sans text-midnight mb-1">{gap.description}</p>
                    {gap.suggestion && (
                      <p className="text-xs font-sans text-bronze italic">
                        Suggestion: {gap.suggestion}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pacing Notes */}
          {result.pacing_notes && (
            <div>
              <h3 className="font-sans font-semibold text-midnight text-sm uppercase tracking-wider mb-3">
                Pacing Notes
              </h3>
              <div
                className="p-3 bg-vellum border border-slate-ui"
                style={{ borderRadius: '2px' }}
              >
                <p className="text-sm font-sans text-midnight leading-relaxed">
                  {result.pacing_notes}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 border-t-2 border-slate-ui p-4">
          <div className="flex justify-end gap-3">
            <button
              onClick={handleDone}
              className="px-6 py-2.5 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
