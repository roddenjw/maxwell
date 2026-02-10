/**
 * CreateOutlineModal Component
 * Modal for adding a story structure outline to an existing manuscript
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

interface CreateOutlineModalProps {
  manuscriptId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateOutlineModal({
  manuscriptId,
  isOpen,
  onClose,
  onSuccess,
}: CreateOutlineModalProps) {
  const [structures, setStructures] = useState<StoryStructure[]>([]);
  const [selectedStructure, setSelectedStructure] = useState<string>('');
  const [genre, setGenre] = useState<string>('');
  const [targetWordCount, setTargetWordCount] = useState<number>(80000);
  const [premise, setPremise] = useState<string>('');
  const [logline, setLogline] = useState<string>('');
  const [brainstormText, setBrainstormText] = useState<string>('');
  const [showBrainstorm, setShowBrainstorm] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isFilling, setIsFilling] = useState(false);
  const [step, setStep] = useState<'structure' | 'details'>('structure');

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
        setStructures(data.structures);
      }
    } catch (error) {
      console.error('Failed to fetch structures:', error);
      toast.error('Failed to load story structures');
    }
  };

  const handleGeneratePremise = async () => {
    if (!brainstormText || brainstormText.length < 20) {
      toast.error('Please write at least 20 characters about your story first');
      return;
    }

    // Check for OpenRouter API key (you'll need to add this to settings)
    const apiKey = localStorage.getItem('openrouter_api_key');
    if (!apiKey) {
      toast.error('Please add your OpenRouter API key in Settings to use AI features');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/outlines/generate-premise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brainstorm_text: brainstormText,
          api_key: apiKey,
          genre: genre || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate premise');
      }

      const data = await response.json();
      if (data.success) {
        setPremise(data.premise);
        setLogline(data.logline);
        setShowBrainstorm(false);
        toast.success('Premise and logline generated!');
      }
    } catch (error: any) {
      console.error('Failed to generate premise:', error);
      toast.error(error.message || 'Failed to generate premise');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFillFromManuscript = async () => {
    const apiKey = localStorage.getItem('openrouter_api_key');
    if (!apiKey) {
      toast.error('Please add your OpenRouter API key in Settings to use AI features');
      return;
    }

    setIsFilling(true);
    try {
      // Create a blank outline first
      const response = await fetch(
        `http://localhost:8000/api/outlines/from-template?manuscript_id=${manuscriptId}&structure_type=story-arc-9&genre=${genre}&target_word_count=${targetWordCount}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } }
      );

      if (!response.ok) throw new Error('Failed to create outline');
      const result = await response.json();
      const outline = result.data;

      // Fill it from manuscript
      const fillResponse = await outlineApi.fillFromManuscript(outline.id, {
        manuscript_id: manuscriptId,
        api_key: apiKey,
        structure_type: selectedStructure || undefined,
      });

      if (fillResponse.success) {
        toast.success(`Outline filled: ${fillResponse.data.beats_created} beats, ${fillResponse.data.scenes_created} scenes detected`);
        onSuccess();
        handleClose();
      }
    } catch (error: any) {
      console.error('Fill from manuscript failed:', error);
      toast.error(error.message || 'Failed to fill outline from manuscript');
    } finally {
      setIsFilling(false);
    }
  };

  const handleCreate = async () => {
    if (!selectedStructure) {
      toast.error('Please select a story structure');
      return;
    }

    setIsLoading(true);
    try {
      // Create outline from template
      const response = await fetch(
        `http://localhost:8000/api/outlines/from-template?manuscript_id=${manuscriptId}&structure_type=${selectedStructure}&genre=${genre}&target_word_count=${targetWordCount}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create outline');
      }

      const result = await response.json();
      const outline = result.data;

      // Update with premise/logline if provided
      if (premise || logline) {
        await fetch(`http://localhost:8000/api/outlines/${outline.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ premise, logline }),
        });
      }

      toast.success('Story outline created!');
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Failed to create outline:', error);
      toast.error('Failed to create outline');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setStep('structure');
    setSelectedStructure('');
    setGenre('');
    setPremise('');
    setLogline('');
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
        style={{ borderRadius: '2px' }}
      >
        {/* Header */}
        <div className="border-b-2 border-slate-ui p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-serif font-bold text-midnight mb-2">
                {step === 'structure' ? 'Choose Story Structure' : 'Story Details'}
              </h2>
              <p className="text-faded-ink font-sans">
                {step === 'structure'
                  ? 'Select a proven story structure to guide your writing'
                  : 'Add details about your story (optional)'}
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
            <div>
            {/* Fill from Manuscript option */}
            <div className="mb-6 p-5 border-2 border-amber-300 bg-amber-50/50" style={{ borderRadius: '2px' }}>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-serif font-bold text-lg text-midnight mb-1">
                    Already have content written?
                  </h3>
                  <p className="text-sm font-sans text-faded-ink">
                    AI will analyze your manuscript, detect story structure, and map chapters to beats automatically.
                  </p>
                </div>
                <button
                  onClick={handleFillFromManuscript}
                  disabled={isFilling}
                  className="ml-4 flex-shrink-0 px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50"
                  style={{ borderRadius: '2px' }}
                >
                  {isFilling ? 'Analyzing...' : 'Fill from Manuscript'}
                </button>
              </div>
              {isFilling && (
                <div className="mt-3 flex items-center gap-2 text-sm text-amber-700">
                  <div className="inline-block w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                  <span>AI is reading your chapters and detecting story structure...</span>
                </div>
              )}
            </div>

            <p className="text-sm font-sans text-faded-ink mb-3 uppercase tracking-wider">Or choose a structure template:</p>
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
                  <div className="mt-3 flex flex-wrap gap-1">
                    {structure.recommended_for.slice(0, 3).map((rec, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-slate-ui/30 text-xs font-sans text-midnight"
                        style={{ borderRadius: '2px' }}
                      >
                        {rec}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
            </div>
          )}

          {step === 'details' && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div>
                <label className="block font-sans font-semibold text-midnight mb-2">
                  Selected Structure
                </label>
                <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
                  <p className="font-serif font-bold text-lg text-midnight">
                    {selectedStructureData?.name}
                  </p>
                  <p className="text-sm font-sans text-faded-ink mt-1">
                    {selectedStructureData?.beat_count} plot beats
                  </p>
                </div>
              </div>

              <div>
                <label className="block font-sans font-semibold text-midnight mb-2">
                  Genre (Optional)
                </label>
                <input
                  type="text"
                  value={genre}
                  onChange={(e) => setGenre(e.target.value)}
                  placeholder="e.g., Fantasy, Thriller, Romance"
                  className="w-full px-4 py-2 border-2 border-slate-ui focus:border-bronze focus:outline-none font-sans"
                  style={{ borderRadius: '2px' }}
                />
              </div>

              <div>
                <label className="block font-sans font-semibold text-midnight mb-2">
                  Target Word Count
                </label>
                <input
                  type="number"
                  value={targetWordCount}
                  onChange={(e) => setTargetWordCount(parseInt(e.target.value))}
                  className="w-full px-4 py-2 border-2 border-slate-ui focus:border-bronze focus:outline-none font-sans"
                  style={{ borderRadius: '2px' }}
                />
              </div>

              {/* AI Brainstorm Helper */}
              <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-sans font-semibold text-midnight text-sm">
                      💡 Need help developing your premise?
                    </h4>
                    <p className="font-sans text-xs text-faded-ink mt-1">
                      Write freely about your story ideas, and AI will help distill them into a clear premise
                    </p>
                  </div>
                  <button
                    onClick={() => setShowBrainstorm(!showBrainstorm)}
                    className="px-3 py-1.5 text-xs font-sans font-medium text-bronze hover:bg-bronze/10 transition-colors"
                    style={{ borderRadius: '2px' }}
                  >
                    {showBrainstorm ? 'Hide' : 'Try It'}
                  </button>
                </div>

                {showBrainstorm && (
                  <div className="mt-3 space-y-3">
                    <textarea
                      value={brainstormText}
                      onChange={(e) => setBrainstormText(e.target.value)}
                      placeholder="Write as much as you want about your story... Who are the characters? What's the conflict? What makes it interesting? Don't worry about structure—just brain dump your ideas!"
                      className="w-full px-4 py-3 border-2 border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm min-h-[150px]"
                      style={{ borderRadius: '2px' }}
                    />
                    <button
                      onClick={handleGeneratePremise}
                      disabled={isGenerating || !brainstormText || brainstormText.length < 20}
                      className="w-full px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ borderRadius: '2px' }}
                    >
                      {isGenerating ? 'Generating...' : '✨ Generate Premise & Logline'}
                    </button>
                  </div>
                )}
              </div>

              <div>
                <label className="block font-sans font-semibold text-midnight mb-2">
                  Premise{' '}
                  <span className="text-faded-ink text-sm font-normal">(helps AI generate better analysis)</span>
                </label>
                <textarea
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                  placeholder="Brief description of your story concept..."
                  className="w-full px-4 py-2 border-2 border-slate-ui focus:border-bronze focus:outline-none font-sans min-h-[100px]"
                  style={{ borderRadius: '2px' }}
                />
                <p className="mt-1 text-xs font-sans text-faded-ink">
                  💡 Tip: A clear premise helps AI provide story-specific beat descriptions and detect plot holes
                </p>
              </div>

              <div>
                <label className="block font-sans font-semibold text-midnight mb-2">
                  Logline{' '}
                  <span className="text-faded-ink text-sm font-normal">(helps AI analysis)</span>
                </label>
                <input
                  type="text"
                  value={logline}
                  onChange={(e) => setLogline(e.target.value)}
                  placeholder="One-sentence summary of your story..."
                  className="w-full px-4 py-2 border-2 border-slate-ui focus:border-bronze focus:outline-none font-sans"
                  style={{ borderRadius: '2px' }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t-2 border-slate-ui p-6 flex justify-between">
          <button
            onClick={step === 'details' ? () => setStep('structure') : handleClose}
            className="px-6 py-3 border-2 border-slate-ui text-midnight hover:bg-slate-ui/20 font-sans font-medium uppercase tracking-button transition-colors"
            style={{ borderRadius: '2px' }}
            disabled={isLoading}
          >
            {step === 'details' ? '← Back' : 'Cancel'}
          </button>

          {step === 'structure' ? (
            <button
              onClick={() => setStep('details')}
              disabled={!selectedStructure}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ borderRadius: '2px' }}
            >
              Continue →
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={isLoading}
              className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ borderRadius: '2px' }}
            >
              {isLoading ? 'Creating...' : 'Create Outline'}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
