/**
 * ManuscriptWizard - Multi-step wizard for creating manuscripts with story structure
 * Guides users through genre, structure, and story details
 */

import { useState } from 'react';
import { toast } from '@/stores/toastStore';

interface ManuscriptWizardProps {
  onComplete: (manuscriptId: string, outlineId: string) => void;
  onCancel: () => void;
}

interface StoryStructure {
  id: string;
  name: string;
  description: string;
  beat_count: number;
  recommended_for: string[];
  word_count_range: [number, number];
}

const GENRES = [
  { id: 'fantasy', name: 'Fantasy', icon: '🐉', description: 'Epic quests, magic systems, world-building' },
  { id: 'sci-fi', name: 'Science Fiction', icon: '🚀', description: 'Future tech, space exploration, speculation' },
  { id: 'thriller', name: 'Thriller', icon: '🔪', description: 'Suspense, danger, high stakes' },
  { id: 'mystery', name: 'Mystery', icon: '🔍', description: 'Puzzles, investigation, revelation' },
  { id: 'romance', name: 'Romance', icon: '💕', description: 'Love stories, relationships, emotional journeys' },
  { id: 'literary', name: 'Literary Fiction', icon: '📚', description: 'Character-driven, thematic, artistic' },
  { id: 'historical', name: 'Historical Fiction', icon: '⏳', description: 'Past eras, real events, period detail' },
  { id: 'horror', name: 'Horror', icon: '👻', description: 'Fear, supernatural, psychological terror' },
];

export default function ManuscriptWizard({ onComplete, onCancel }: ManuscriptWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Form state
  const [selectedGenre, setSelectedGenre] = useState<string>('');
  const [selectedStructure, setSelectedStructure] = useState<string>('');
  const [structures, setStructures] = useState<StoryStructure[]>([]);
  const [title, setTitle] = useState('');
  const [targetWordCount, setTargetWordCount] = useState(80000);
  const [premise, setPremise] = useState('');
  const [logline, setLogline] = useState('');

  const steps = [
    { title: 'Choose Your Genre', icon: '🎭' },
    { title: 'Select Story Structure', icon: '📐' },
    { title: 'Story Details', icon: '✍️' },
    { title: 'Review & Create', icon: '🚀' },
  ];

  // Fetch structures when moving to structure selection step
  const handleNext = async () => {
    if (currentStep === 0 && !selectedGenre) {
      toast.error('Please select a genre');
      return;
    }

    if (currentStep === 0) {
      // Fetch story structures
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/api/outlines/structures');
        const data = await response.json();
        if (data.success) {
          setStructures(data.structures);
        }
      } catch (error) {
        console.error('Failed to fetch structures:', error);
        toast.error('Failed to load story structures');
      } finally {
        setLoading(false);
      }
    }

    if (currentStep === 1 && !selectedStructure) {
      toast.error('Please select a story structure');
      return;
    }

    if (currentStep === 2) {
      if (!title.trim()) {
        toast.error('Please enter a title');
        return;
      }
      if (targetWordCount < 1000 || targetWordCount > 500000) {
        toast.error('Word count should be between 1,000 and 500,000');
        return;
      }
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleCreate();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCreate = async () => {
    try {
      setLoading(true);

      // 1. Create manuscript
      const manuscriptResponse = await fetch('http://localhost:8000/api/manuscripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title || 'Untitled Manuscript',
          lexical_state: '',
        }),
      });

      if (!manuscriptResponse.ok) {
        throw new Error('Failed to create manuscript');
      }

      const manuscriptData = await manuscriptResponse.json();
      const manuscriptId = manuscriptData.id;

      // 2. Create outline from template
      const outlineResponse = await fetch(
        `http://localhost:8000/api/outlines/from-template?manuscript_id=${manuscriptId}&structure_type=${selectedStructure}&genre=${selectedGenre}&target_word_count=${targetWordCount}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!outlineResponse.ok) {
        throw new Error('Failed to create outline');
      }

      const outlineData = await outlineResponse.json();

      // 3. Update outline with premise and logline
      if (premise || logline) {
        await fetch(`http://localhost:8000/api/outlines/${outlineData.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            premise: premise || '',
            logline: logline || '',
          }),
        });
      }

      toast.success('Manuscript created with story structure!');
      onComplete(manuscriptId, outlineData.id);
    } catch (error) {
      console.error('Manuscript creation error:', error);
      toast.error('Failed to create manuscript. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectedStructureData = structures.find(s => s.id === selectedStructure);

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[300] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 py-6 border-b-2 border-bronze/30 bg-gradient-to-r from-bronze/5 to-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="text-5xl">{steps[currentStep].icon}</div>
              <div>
                <h2 className="font-garamond text-3xl font-semibold text-midnight">
                  {steps[currentStep].title}
                </h2>
                <p className="text-faded-ink font-sans text-sm mt-1">
                  Step {currentStep + 1} of {steps.length}
                </p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="text-faded-ink hover:text-midnight transition-colors text-sm font-sans"
            >
              Cancel
            </button>
          </div>

          {/* Progress indicator */}
          <div className="flex gap-2">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`flex-1 h-1.5 rounded-full transition-all ${
                  index <= currentStep ? 'bg-bronze' : 'bg-slate-ui/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {/* Step 0: Genre Selection */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <h3 className="font-garamond text-2xl font-semibold text-midnight mb-2">
                  What genre are you writing?
                </h3>
                <p className="text-faded-ink font-sans">
                  This helps us recommend the best story structure for your manuscript
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {GENRES.map((genre) => (
                  <button
                    key={genre.id}
                    onClick={() => setSelectedGenre(genre.id)}
                    className={`p-6 rounded-sm border-2 transition-all ${
                      selectedGenre === genre.id
                        ? 'border-bronze bg-bronze/10 shadow-lg'
                        : 'border-slate-ui/30 bg-white hover:border-bronze/50 hover:shadow-md'
                    }`}
                  >
                    <div className="text-4xl mb-2">{genre.icon}</div>
                    <div className="font-sans font-semibold text-midnight text-sm mb-1">
                      {genre.name}
                    </div>
                    <div className="text-xs text-faded-ink">{genre.description}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 1: Structure Selection */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <h3 className="font-garamond text-2xl font-semibold text-midnight mb-2">
                  Choose Your Story Structure
                </h3>
                <p className="text-faded-ink font-sans">
                  Select a proven framework to guide your manuscript
                </p>
              </div>

              <div className="space-y-4">
                {structures.map((structure) => (
                  <button
                    key={structure.id}
                    onClick={() => setSelectedStructure(structure.id)}
                    className={`w-full p-6 rounded-sm border-2 text-left transition-all ${
                      selectedStructure === structure.id
                        ? 'border-bronze bg-bronze/10 shadow-lg'
                        : 'border-slate-ui/30 bg-white hover:border-bronze/50 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-garamond text-xl font-semibold text-midnight">
                          {structure.name}
                        </h4>
                        <p className="text-sm text-faded-ink font-sans mt-1">
                          {structure.beat_count} plot beats
                        </p>
                      </div>
                      {selectedStructure === structure.id && (
                        <div className="text-2xl">✓</div>
                      )}
                    </div>
                    <p className="text-sm text-midnight font-sans mb-3">
                      {structure.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <div className="text-xs bg-white px-3 py-1 rounded-full border border-slate-ui">
                        {structure.word_count_range[0].toLocaleString()} - {structure.word_count_range[1].toLocaleString()} words
                      </div>
                      {structure.recommended_for.slice(0, 3).map((rec) => (
                        <div
                          key={rec}
                          className="text-xs bg-bronze/10 text-bronze px-3 py-1 rounded-full font-semibold"
                        >
                          {rec}
                        </div>
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Story Details */}
          {currentStep === 2 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <h3 className="font-garamond text-2xl font-semibold text-midnight mb-2">
                  Tell Us About Your Story
                </h3>
                <p className="text-faded-ink font-sans">
                  These details will help structure your manuscript
                </p>
              </div>

              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                  Manuscript Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="The Adventures of Maxwell..."
                  className="w-full px-4 py-3 border-2 border-slate-ui rounded-sm text-midnight font-sans focus:outline-none focus:border-bronze"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                  Target Word Count *
                </label>
                <input
                  type="number"
                  value={targetWordCount}
                  onChange={(e) => setTargetWordCount(parseInt(e.target.value) || 80000)}
                  min="1000"
                  max="500000"
                  step="5000"
                  className="w-full px-4 py-3 border-2 border-slate-ui rounded-sm text-midnight font-sans focus:outline-none focus:border-bronze"
                />
                <p className="text-xs text-faded-ink mt-2 font-sans">
                  Recommended: {selectedStructureData?.word_count_range[0].toLocaleString()} - {selectedStructureData?.word_count_range[1].toLocaleString()} words for {selectedStructureData?.name}
                </p>
              </div>

              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                  Premise (Optional)
                </label>
                <textarea
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                  placeholder="A one-sentence summary of your story..."
                  rows={2}
                  className="w-full px-4 py-3 border-2 border-slate-ui rounded-sm text-midnight font-sans focus:outline-none focus:border-bronze resize-none"
                />
                <p className="text-xs text-faded-ink mt-1 font-sans">
                  Example: "A young wizard discovers they're the chosen one and must defeat an ancient evil."
                </p>
              </div>

              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                  Logline (Optional)
                </label>
                <textarea
                  value={logline}
                  onChange={(e) => setLogline(e.target.value)}
                  placeholder="A compelling marketing pitch for your story..."
                  rows={2}
                  className="w-full px-4 py-3 border-2 border-slate-ui rounded-sm text-midnight font-sans focus:outline-none focus:border-bronze resize-none"
                />
                <p className="text-xs text-faded-ink mt-1 font-sans">
                  Example: "When magic awakens in modern London, one teenager must choose between saving the world or protecting their family."
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Review & Create */}
          {currentStep === 3 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <h3 className="font-garamond text-2xl font-semibold text-midnight mb-2">
                  Ready to Begin Your Journey?
                </h3>
                <p className="text-faded-ink font-sans">
                  Review your choices and create your manuscript
                </p>
              </div>

              <div className="space-y-4">
                <div className="bg-white border-2 border-bronze/30 rounded-sm p-6">
                  <h4 className="font-sans font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-2xl">📖</span>
                    Manuscript Details
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-faded-ink">Title:</span>
                      <span className="font-semibold text-midnight">{title || 'Untitled'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-faded-ink">Genre:</span>
                      <span className="font-semibold text-midnight">
                        {GENRES.find(g => g.id === selectedGenre)?.name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-faded-ink">Target Length:</span>
                      <span className="font-semibold text-midnight">
                        {targetWordCount.toLocaleString()} words
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-white border-2 border-bronze/30 rounded-sm p-6">
                  <h4 className="font-sans font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-2xl">📐</span>
                    Story Structure
                  </h4>
                  <div className="space-y-2">
                    <div className="font-semibold text-midnight">
                      {selectedStructureData?.name}
                    </div>
                    <div className="text-sm text-faded-ink">
                      {selectedStructureData?.description}
                    </div>
                    <div className="text-sm text-bronze font-semibold">
                      {selectedStructureData?.beat_count} plot beats will be created
                    </div>
                  </div>
                </div>

                {(premise || logline) && (
                  <div className="bg-white border-2 border-bronze/30 rounded-sm p-6">
                    <h4 className="font-sans font-semibold text-midnight mb-4 flex items-center gap-2">
                      <span className="text-2xl">✨</span>
                      Your Story
                    </h4>
                    {premise && (
                      <div className="mb-3">
                        <div className="text-xs text-faded-ink mb-1">Premise:</div>
                        <div className="text-sm text-midnight italic">"{premise}"</div>
                      </div>
                    )}
                    {logline && (
                      <div>
                        <div className="text-xs text-faded-ink mb-1">Logline:</div>
                        <div className="text-sm text-midnight italic">"{logline}"</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-8 py-6 border-t-2 border-slate-ui/30 bg-white flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 0 || loading}
            className="px-6 py-3 text-faded-ink hover:text-midnight transition-colors font-sans disabled:opacity-0 disabled:cursor-not-allowed"
          >
            ← Back
          </button>

          <button
            onClick={handleNext}
            disabled={loading}
            className="px-8 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Creating...</span>
              </>
            ) : currentStep === steps.length - 1 ? (
              <>
                <span>Create Manuscript</span>
                <span>→</span>
              </>
            ) : (
              <>
                <span>Next</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
