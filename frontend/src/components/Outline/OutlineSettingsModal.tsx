/**
 * OutlineSettingsModal - Edit outline metadata (premise, logline, synopsis, genre, notes)
 * Provides a single UI location to view and edit all outline-level settings
 */

import { useState, useEffect } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import { outlineApi } from '@/lib/api';

interface OutlineSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  outlineId: string;
}

export default function OutlineSettingsModal({ isOpen, onClose, outlineId }: OutlineSettingsModalProps) {
  const { outline, loadOutline } = useOutlineStore();

  const [genre, setGenre] = useState('');
  const [premise, setPremise] = useState('');
  const [logline, setLogline] = useState('');
  const [synopsis, setSynopsis] = useState('');
  const [targetWordCount, setTargetWordCount] = useState(80000);
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load current values
  useEffect(() => {
    if (outline) {
      setGenre(outline.genre || '');
      setPremise(outline.premise || '');
      setLogline(outline.logline || '');
      setSynopsis(outline.synopsis || '');
      setTargetWordCount(outline.target_word_count || 80000);
      setNotes(outline.notes || '');
    }
  }, [outline]);

  const handleSave = async () => {
    if (!outlineId) return;

    try {
      setError(null);
      setIsSaving(true);

      await outlineApi.updateOutline(outlineId, {
        genre: genre.trim() || undefined,
        premise: premise.trim() || undefined,
        logline: logline.trim() || undefined,
        synopsis: synopsis.trim() || undefined,
        target_word_count: targetWordCount,
        notes: notes.trim() || undefined,
      });

      // Reload outline to get updated data
      await loadOutline(outlineId);

      onClose();
    } catch (err) {
      console.error('Failed to update outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">Outline Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="space-y-6">
            {/* Genre */}
            <div>
              <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-1">
                Genre
              </label>
              <input
                id="genre"
                type="text"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                placeholder="e.g., Epic Fantasy, Science Fiction, Mystery"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                The genre of your story (used for AI context and brainstorming)
              </p>
            </div>

            {/* Premise */}
            <div>
              <label htmlFor="premise" className="block text-sm font-medium text-gray-700 mb-1">
                Premise <span className="text-red-500">*</span>
              </label>
              <textarea
                id="premise"
                value={premise}
                onChange={(e) => setPremise(e.target.value)}
                placeholder="One-sentence story concept: A young blacksmith discovers ancient magic and must save the kingdom from an evil sorcerer."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                <strong>Premise</strong> is your story's core concept in 1-2 sentences. This is different from chapter content!
              </p>
            </div>

            {/* Logline */}
            <div>
              <label htmlFor="logline" className="block text-sm font-medium text-gray-700 mb-1">
                Logline
              </label>
              <textarea
                id="logline"
                value={logline}
                onChange={(e) => setLogline(e.target.value)}
                placeholder="Marketing-ready one-sentence pitch for your story"
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                A compelling one-sentence pitch for marketing/query letters
              </p>
            </div>

            {/* Synopsis */}
            <div>
              <label htmlFor="synopsis" className="block text-sm font-medium text-gray-700 mb-1">
                Synopsis
              </label>
              <textarea
                id="synopsis"
                value={synopsis}
                onChange={(e) => setSynopsis(e.target.value)}
                placeholder="Full story synopsis (beginning, middle, end including major plot points)"
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Detailed story summary including all major plot points and ending
              </p>
            </div>

            {/* Target Word Count */}
            <div>
              <label htmlFor="targetWordCount" className="block text-sm font-medium text-gray-700 mb-1">
                Target Word Count
              </label>
              <input
                id="targetWordCount"
                type="number"
                value={targetWordCount}
                onChange={(e) => setTargetWordCount(parseInt(e.target.value) || 80000)}
                min="1000"
                max="500000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Your manuscript's target length (affects plot beat calculations)
              </p>
            </div>

            {/* Notes */}
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional notes about your story structure and planning..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
