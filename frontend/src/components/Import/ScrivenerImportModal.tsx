/**
 * ScrivenerImportModal - Import Scrivener projects into Maxwell
 *
 * Two-step flow:
 * 1. Upload and preview - Shows what will be imported
 * 2. Confirm and import - Creates manuscript with chapters and entities
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface ScrivenerPreview {
  title: string;
  author: string | null;
  draft_found: boolean;
  draft_documents: number;
  draft_word_count: number;
  characters_found: boolean;
  characters_count: number;
  locations_found: boolean;
  locations_count: number;
  research_found: boolean;
  research_count: number;
}

interface ImportResult {
  success: boolean;
  manuscript_id: string;
  title: string;
  chapters_imported: number;
  entities_imported: number;
  word_count: number;
  message: string;
}

interface ScrivenerImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (manuscriptId: string) => void;
}

type ImportStep = 'upload' | 'preview' | 'importing' | 'success' | 'error';

export const ScrivenerImportModal: React.FC<ScrivenerImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [step, setStep] = useState<ImportStep>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ScrivenerPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Import options
  const [importCharacters, setImportCharacters] = useState(true);
  const [importLocations, setImportLocations] = useState(true);
  const [importResearch, setImportResearch] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const uploadedFile = acceptedFiles[0];

    if (!uploadedFile.name.endsWith('.zip')) {
      setError('Please upload a .zip file containing your .scriv folder');
      return;
    }

    setFile(uploadedFile);
    setError(null);
    setIsLoading(true);

    try {
      // Preview the import
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('http://localhost:8000/api/import/scrivener/preview', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to parse Scrivener project');
      }

      const previewData = await response.json();
      setPreview(previewData);
      setStep('preview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse project');
      setStep('error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip'],
    },
    multiple: false,
  });

  const handleImport = async () => {
    if (!file) return;

    setStep('importing');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const params = new URLSearchParams({
        import_characters: importCharacters.toString(),
        import_locations: importLocations.toString(),
        import_research: importResearch.toString(),
      });

      const response = await fetch(
        `http://localhost:8000/api/import/scrivener?${params}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to import project');
      }

      const importResult = await response.json();
      setResult(importResult);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import project');
      setStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    // Reset state
    setStep('upload');
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setIsLoading(false);
    onClose();
  };

  const handleOpenManuscript = () => {
    if (result?.manuscript_id) {
      onSuccess(result.manuscript_id);
      handleClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui bg-vellum">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-garamond font-semibold text-midnight">
                Import from Scrivener
              </h2>
              <p className="text-sm text-faded-ink mt-1">
                Import your Scrivener 3 project into Maxwell
              </p>
            </div>
            <button
              onClick={handleClose}
              className="p-2 text-faded-ink hover:text-midnight transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Upload Step */}
          {step === 'upload' && (
            <div>
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                  transition-colors
                  ${isDragActive
                    ? 'border-bronze bg-bronze/5'
                    : 'border-slate-ui hover:border-bronze'
                  }
                `}
              >
                <input {...getInputProps()} />
                <div className="text-4xl mb-4">📚</div>
                {isDragActive ? (
                  <p className="text-bronze font-medium">Drop your project here...</p>
                ) : (
                  <>
                    <p className="text-midnight font-medium mb-2">
                      Drag & drop your Scrivener project
                    </p>
                    <p className="text-sm text-faded-ink">
                      Upload a .zip file containing your .scriv folder
                    </p>
                  </>
                )}
              </div>

              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">
                  How to export from Scrivener:
                </h4>
                <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                  <li>In Scrivener, go to File → Backup → Backup To...</li>
                  <li>Choose "Zip" as the format</li>
                  <li>Upload the resulting .zip file here</li>
                </ol>
              </div>

              {isLoading && (
                <div className="mt-4 flex items-center justify-center gap-2 text-bronze">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  <span>Parsing project...</span>
                </div>
              )}
            </div>
          )}

          {/* Preview Step */}
          {step === 'preview' && preview && (
            <div>
              <div className="mb-6">
                <h3 className="font-garamond text-lg font-semibold text-midnight mb-1">
                  {preview.title}
                </h3>
                {preview.author && (
                  <p className="text-sm text-faded-ink">by {preview.author}</p>
                )}
              </div>

              {/* Content Summary */}
              <div className="space-y-3 mb-6">
                {preview.draft_found && (
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-green-600">📄</span>
                      <span className="text-green-900">Manuscript</span>
                    </div>
                    <div className="text-sm text-green-700">
                      {preview.draft_documents} documents • {preview.draft_word_count.toLocaleString()} words
                    </div>
                  </div>
                )}

                {preview.characters_found && (
                  <label className="flex items-center justify-between p-3 bg-purple-50 rounded-lg cursor-pointer">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={importCharacters}
                        onChange={(e) => setImportCharacters(e.target.checked)}
                        className="rounded border-purple-300 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-purple-600">👤</span>
                      <span className="text-purple-900">Characters</span>
                    </div>
                    <div className="text-sm text-purple-700">
                      {preview.characters_count} characters
                    </div>
                  </label>
                )}

                {preview.locations_found && (
                  <label className="flex items-center justify-between p-3 bg-blue-50 rounded-lg cursor-pointer">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={importLocations}
                        onChange={(e) => setImportLocations(e.target.checked)}
                        className="rounded border-blue-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-blue-600">🌍</span>
                      <span className="text-blue-900">Locations</span>
                    </div>
                    <div className="text-sm text-blue-700">
                      {preview.locations_count} locations
                    </div>
                  </label>
                )}

                {preview.research_found && (
                  <label className="flex items-center justify-between p-3 bg-amber-50 rounded-lg cursor-pointer">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={importResearch}
                        onChange={(e) => setImportResearch(e.target.checked)}
                        className="rounded border-amber-300 text-amber-600 focus:ring-amber-500"
                      />
                      <span className="text-amber-600">🔬</span>
                      <span className="text-amber-900">Research Notes</span>
                    </div>
                    <div className="text-sm text-amber-700">
                      {preview.research_count} documents
                    </div>
                  </label>
                )}
              </div>

              <p className="text-sm text-faded-ink mb-4">
                Characters and locations will be imported into the Codex for easy reference while writing.
              </p>
            </div>
          )}

          {/* Importing Step */}
          {step === 'importing' && (
            <div className="text-center py-8">
              <div className="mb-4">
                <svg className="animate-spin h-12 w-12 text-bronze mx-auto" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              </div>
              <p className="text-midnight font-medium">Importing your project...</p>
              <p className="text-sm text-faded-ink mt-1">This may take a moment</p>
            </div>
          )}

          {/* Success Step */}
          {step === 'success' && result && (
            <div className="text-center py-4">
              <div className="text-5xl mb-4">✅</div>
              <h3 className="font-garamond text-xl font-semibold text-midnight mb-2">
                Import Successful!
              </h3>
              <p className="text-faded-ink mb-6">
                "{result.title}" has been imported into Maxwell.
              </p>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-vellum rounded-lg p-3">
                  <div className="text-2xl font-garamond font-bold text-bronze">
                    {result.chapters_imported}
                  </div>
                  <div className="text-xs text-faded-ink">Chapters</div>
                </div>
                <div className="bg-vellum rounded-lg p-3">
                  <div className="text-2xl font-garamond font-bold text-bronze">
                    {result.entities_imported}
                  </div>
                  <div className="text-xs text-faded-ink">Entities</div>
                </div>
                <div className="bg-vellum rounded-lg p-3">
                  <div className="text-2xl font-garamond font-bold text-bronze">
                    {result.word_count.toLocaleString()}
                  </div>
                  <div className="text-xs text-faded-ink">Words</div>
                </div>
              </div>
            </div>
          )}

          {/* Error Step */}
          {step === 'error' && (
            <div className="text-center py-4">
              <div className="text-5xl mb-4">❌</div>
              <h3 className="font-garamond text-xl font-semibold text-red-600 mb-2">
                Import Failed
              </h3>
              <p className="text-faded-ink mb-4">{error}</p>
              <button
                onClick={() => setStep('upload')}
                className="text-bronze hover:text-bronze/80 font-medium"
              >
                Try again
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-ui bg-gray-50 flex justify-end gap-3">
          {step === 'upload' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 text-faded-ink hover:text-midnight transition-colors"
            >
              Cancel
            </button>
          )}

          {step === 'preview' && (
            <>
              <button
                onClick={() => setStep('upload')}
                className="px-4 py-2 text-faded-ink hover:text-midnight transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleImport}
                className="px-4 py-2 bg-bronze text-white rounded-lg hover:bg-bronze/90 transition-colors font-medium"
              >
                Import Project
              </button>
            </>
          )}

          {step === 'success' && (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-faded-ink hover:text-midnight transition-colors"
              >
                Close
              </button>
              <button
                onClick={handleOpenManuscript}
                className="px-4 py-2 bg-bronze text-white rounded-lg hover:bg-bronze/90 transition-colors font-medium"
              >
                Open Manuscript
              </button>
            </>
          )}

          {step === 'error' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-gray-200 text-midnight rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScrivenerImportModal;
