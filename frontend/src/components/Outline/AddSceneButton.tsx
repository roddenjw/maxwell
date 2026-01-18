/**
 * AddSceneButton Component
 * Button to add a scene between beats in the outline
 */

import { useState } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import type { PlotBeat } from '@/types/outline';

interface AddSceneButtonProps {
  afterBeat: PlotBeat;
  nextBeat?: PlotBeat;
}

export default function AddSceneButton({ afterBeat, nextBeat }: AddSceneButtonProps) {
  const { createScene } = useOutlineStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [sceneLabel, setSceneLabel] = useState('');
  const [sceneDescription, setSceneDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sceneLabel.trim()) return;

    setIsCreating(true);
    try {
      await createScene({
        scene_label: sceneLabel.trim(),
        scene_description: sceneDescription.trim(),
        after_beat_id: afterBeat.id,
        target_word_count: 1000,
      });
      setIsOpen(false);
      setSceneLabel('');
      setSceneDescription('');
    } finally {
      setIsCreating(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full py-1.5 px-3 flex items-center justify-center gap-2 text-sm text-faded-ink/60 hover:text-bronze hover:bg-bronze/5 transition-colors border-2 border-dashed border-transparent hover:border-bronze/30 group"
        style={{ borderRadius: '2px' }}
        title={`Add a scene between "${afterBeat.beat_label}" and "${nextBeat?.beat_label || 'end'}"`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        <span className="opacity-0 group-hover:opacity-100 transition-opacity">Add Scene</span>
      </button>
    );
  }

  return (
    <div className="p-3 bg-bronze/5 border-2 border-bronze/30" style={{ borderRadius: '2px' }}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-sans font-semibold text-bronze">
            Add Scene
          </h4>
          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              setSceneLabel('');
              setSceneDescription('');
            }}
            className="text-faded-ink hover:text-midnight transition-colors text-sm"
          >
            Cancel
          </button>
        </div>

        <p className="text-xs text-faded-ink">
          Bridge between <strong>{afterBeat.beat_label}</strong> and <strong>{nextBeat?.beat_label || 'the end'}</strong>
        </p>

        <div>
          <label className="block text-xs font-sans font-medium text-midnight mb-1">
            Scene Title *
          </label>
          <input
            type="text"
            value={sceneLabel}
            onChange={(e) => setSceneLabel(e.target.value)}
            placeholder="e.g., Character meets mentor"
            className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50"
            style={{ borderRadius: '2px' }}
            autoFocus
          />
        </div>

        <div>
          <label className="block text-xs font-sans font-medium text-midnight mb-1">
            Description (optional)
          </label>
          <textarea
            value={sceneDescription}
            onChange={(e) => setSceneDescription(e.target.value)}
            placeholder="What happens in this scene..."
            className="w-full px-2.5 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm text-midnight placeholder:text-faded-ink/50 min-h-[60px] resize-y"
            style={{ borderRadius: '2px' }}
          />
        </div>

        <button
          type="submit"
          disabled={!sceneLabel.trim() || isCreating}
          className="w-full px-3 py-2 bg-bronze hover:bg-bronze-dark disabled:bg-slate-ui/50 text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
          style={{ borderRadius: '2px' }}
        >
          {isCreating ? 'Adding...' : 'Add Scene'}
        </button>
      </form>
    </div>
  );
}
