/**
 * SwitchStructureModal Component
 * Modal for switching an outline to a different story structure
 * Shows intelligent beat mapping suggestions for user review
 */

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { toast } from '@/stores/toastStore';
import { outlineApi } from '@/lib/api';
import { Z_INDEX } from '@/lib/zIndex';

interface StoryStructure {
  id: string;
  name: string;
  description: string;
  beat_count: number;
  recommended_for: string[];
  word_count_range: [number, number];
}

interface BeatMapping {
  old_beat_id: string;
  old_beat_name: string;
  old_beat_label: string;
  old_position: number;
  suggested_new_beat: string;
  has_notes: boolean;
  has_chapter: boolean;
  is_completed: boolean;
  confidence: number;
}

interface SwitchStructureModalProps {
  outlineId: string;
  currentStructureType: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function SwitchStructureModal({
  outlineId,
  currentStructureType,
  isOpen,
  onClose,
  onSuccess,
}: SwitchStructureModalProps) {
  const [structures, setStructures] = useState<StoryStructure[]>([]);
  const [selectedStructure, setSelectedStructure] = useState<string>('');
  const [beatMappings, setBeatMappings] = useState<BeatMapping[]>([]);
  const [newBeats, setNewBeats] = useState<any[]>([]);
  const [userMappings, setUserMappings] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<'structure' | 'mappings'>('structure');

  useEffect(() => {
    if (isOpen) {
      fetchStructures();
    }
  }, [isOpen]);

  const fetchStructures = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/outlines/structures');
      const data = await response.json();
      if (data.success) {
        // Filter out current structure
        setStructures(data.structures.filter((s: StoryStructure) => s.id !== currentStructureType));
      }
    } catch (error) {
      console.error('Failed to fetch structures:', error);
      toast.error('Failed to load story structures');
    }
  };

  const handleGetMappings = async () => {
    if (!selectedStructure) {
      toast.error('Please select a story structure');
      return;
    }

    setIsLoading(true);
    try {
      const result = await outlineApi.switchStructure({
        current_outline_id: outlineId,
        new_structure_type: selectedStructure,
      });

      if (result.requires_mapping) {
        setBeatMappings(result.suggested_mappings);
        setNewBeats(result.new_beats);

        // Initialize user mappings with suggestions
        const initialMappings: Record<string, string> = {};
        result.suggested_mappings.forEach((mapping: BeatMapping) => {
          initialMappings[mapping.old_beat_id] = mapping.suggested_new_beat;
        });
        setUserMappings(initialMappings);

        setStep('mappings');
      }
    } catch (error: any) {
      console.error('Failed to get mappings:', error);
      toast.error(error.message || 'Failed to analyze structure switch');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplySwitch = async () => {
    setIsLoading(true);
    try {
      await outlineApi.switchStructure({
        current_outline_id: outlineId,
        new_structure_type: selectedStructure,
        beat_mappings: userMappings,
      });

      toast.success('Story structure switched successfully!');
      onSuccess();
      handleClose();
    } catch (error: any) {
      console.error('Failed to switch structure:', error);
      toast.error(error.message || 'Failed to switch structure');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setStep('structure');
    setSelectedStructure('');
    setBeatMappings([]);
    setNewBeats([]);
    setUserMappings({});
    onClose();
  };

  if (!isOpen) return null;

  const selectedStructureData = structures.find((s) => s.id === selectedStructure);

  return createPortal(
    <div
      className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4"
      style={{ zIndex: Z_INDEX.MODAL_BACKDROP }}
    >
      <div
        className="bg-white max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-book"
        style={{ borderRadius: '2px', zIndex: Z_INDEX.MODAL }}
      >
        {/* Header */}
        <div className="border-b-2 border-slate-ui p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-serif font-bold text-midnight mb-2">
                {step === 'structure' ? 'Choose New Structure' : 'Review Beat Mappings'}
              </h2>
              <p className="text-faded-ink font-sans">
                {step === 'structure'
                  ? 'Your progress and notes will be preserved'
                  : 'Review how your beats will be transferred to the new structure'}
              </p>
            </div>
            <button
              onClick={handleClose}
              className="w-8 h-8 flex items-center justify-center hover:bg-slate-ui/30 text-faded-ink hover:text-midnight transition-colors"
              style={{ borderRadius: '2px' }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 'structure' && (
            <div className="space-y-4">
              <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
                <p className="text-sm font-sans text-midnight">
                  <strong>Current Structure:</strong> {currentStructureType.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </p>
                <p className="text-xs font-sans text-faded-ink mt-1">
                  Your user notes, chapter links, and completion status will be intelligently transferred to matching beats in the new structure.
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {structures.map((structure) => (
                  <button
                    key={structure.id}
                    onClick={() => setSelectedStructure(structure.id)}
                    className={`p-6 border-2 text-left transition-all ${
                      selectedStructure === structure.id
                        ? 'border-bronze bg-bronze/5 shadow-lg'
                        : 'border-slate-ui hover:border-bronze/50 hover:shadow-md'
                    }`}
                    style={{ borderRadius: '2px' }}
                  >
                    <h3 className="font-serif font-bold text-xl text-midnight mb-2">
                      {structure.name}
                    </h3>
                    <p className="text-sm font-sans text-faded-ink mb-3">
                      {structure.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs font-sans text-faded-ink">
                      <span className="font-bold text-bronze">{structure.beat_count} beats</span>
                      <span>
                        {structure.word_count_range[0].toLocaleString()}-
                        {structure.word_count_range[1].toLocaleString()} words
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 'mappings' && (
            <div className="space-y-4">
              <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
                <p className="text-sm font-sans text-midnight mb-2">
                  <strong>Switching to:</strong> {selectedStructureData?.name}
                </p>
                <p className="text-xs font-sans text-faded-ink">
                  Review the suggested mappings below. You can change which new beat each old beat maps to, or select "Don't Transfer" to skip a beat.
                </p>
              </div>

              <div className="space-y-3">
                {beatMappings.map((mapping) => (
                  <div
                    key={mapping.old_beat_id}
                    className="p-4 bg-white border-2 border-slate-ui"
                    style={{ borderRadius: '2px' }}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-sans font-bold text-faded-ink uppercase">
                            {mapping.old_beat_name}
                          </span>
                          {mapping.is_completed && <span className="text-xs">✓</span>}
                          {mapping.has_notes && <span className="text-xs" title="Has notes">📝</span>}
                          {mapping.has_chapter && <span className="text-xs" title="Linked to chapter">📄</span>}
                        </div>
                        <p className="font-serif font-bold text-sm text-midnight">
                          {mapping.old_beat_label}
                        </p>
                      </div>

                      <div className="flex-shrink-0 flex items-center gap-2">
                        <span className="text-faded-ink">→</span>
                        <select
                          value={userMappings[mapping.old_beat_id] || ''}
                          onChange={(e) => setUserMappings({
                            ...userMappings,
                            [mapping.old_beat_id]: e.target.value
                          })}
                          className="px-3 py-1.5 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
                          style={{ borderRadius: '2px' }}
                        >
                          <option value="">Don't Transfer</option>
                          {newBeats.map((beat) => (
                            <option key={beat.beat_name} value={beat.beat_name}>
                              {beat.beat_label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-ui/30" style={{ borderRadius: '2px' }}>
                        <div
                          className="h-full bg-bronze"
                          style={{ width: `${mapping.confidence}%`, borderRadius: '2px' }}
                        />
                      </div>
                      <span className="text-xs font-sans text-faded-ink">
                        {mapping.confidence}% confidence
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t-2 border-slate-ui p-6 flex justify-between">
          <button
            onClick={step === 'mappings' ? () => setStep('structure') : handleClose}
            className="px-6 py-3 border-2 border-slate-ui text-midnight hover:bg-slate-ui/20 font-sans font-medium uppercase tracking-button transition-colors"
            style={{ borderRadius: '2px' }}
            disabled={isLoading}
          >
            {step === 'mappings' ? '← Back' : 'Cancel'}
          </button>

          {step === 'structure' ? (
            <button
              onClick={handleGetMappings}
              disabled={!selectedStructure || isLoading}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ borderRadius: '2px' }}
            >
              {isLoading ? 'Analyzing...' : 'Continue →'}
            </button>
          ) : (
            <button
              onClick={handleApplySwitch}
              disabled={isLoading}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ borderRadius: '2px' }}
            >
              {isLoading ? 'Switching...' : 'Switch Structure'}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
