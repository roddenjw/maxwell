/**
 * ImportModal - 3-step wizard for importing manuscripts from various formats
 *
 * Steps:
 * 1. File Upload - Drag & drop or select file
 * 2. Preview & Configure - Review detected chapters, edit titles, exclude chapters
 * 3. Confirm & Create - Summary and final import
 */

import { useState, useCallback, useRef } from 'react';
import { importApi } from '@/lib/api';
import analytics from '@/lib/analytics';
import { toast } from '@/stores/toastStore';
import type {
  ImportPreview,
  SupportedFormat,
  DetectionMode,
  ChapterAdjustment,
} from '@/types/import';
import { DETECTION_MODES } from '@/types/import';

interface ImportModalProps {
  onClose: () => void;
  onImportComplete: (manuscriptId: string) => void;
  seriesId?: string;
}

type Step = 'upload' | 'preview' | 'confirm';

// Accepted file extensions
const ACCEPTED_EXTENSIONS = '.docx,.rtf,.odt,.txt,.md,.pdf';

export default function ImportModal({
  onClose,
  onImportComplete,
  seriesId,
}: ImportModalProps) {
  const [step, setStep] = useState<Step>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [detectionMode, setDetectionMode] = useState<DetectionMode>('auto');
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [formats, setFormats] = useState<SupportedFormat[]>([]);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedAuthor, setEditedAuthor] = useState('');
  const [chapterStates, setChapterStates] = useState<Map<number, { title: string; included: boolean }>>(new Map());
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load supported formats on mount
  useState(() => {
    importApi.getSupportedFormats().then(setFormats).catch(console.error);
  });

  // File drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const validExtensions = ACCEPTED_EXTENSIONS.split(',');
    if (!validExtensions.includes(ext)) {
      toast.error(`Unsupported file format: ${ext}`);
      return;
    }

    setSelectedFile(file);
  };

  // Parse the document
  const handleParse = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    const ext = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    analytics.importStarted(ext);

    try {
      const result = await importApi.parseFile(selectedFile, detectionMode);
      setPreview(result);
      setEditedTitle(result.title);
      setEditedAuthor(result.author || '');

      // Initialize chapter states
      const states = new Map<number, { title: string; included: boolean }>();
      result.chapters.forEach((ch) => {
        states.set(ch.index, { title: ch.title, included: true });
      });
      setChapterStates(states);

      setStep('preview');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to parse document';
      toast.error(message);
      analytics.importFailed(ext, message);
    } finally {
      setIsLoading(false);
    }
  };

  // Re-parse with different detection mode
  const handleRedetect = async (newMode: DetectionMode) => {
    if (!selectedFile) return;

    setDetectionMode(newMode);
    setIsLoading(true);

    try {
      const result = await importApi.parseFile(selectedFile, newMode);
      setPreview(result);

      // Reset chapter states
      const states = new Map<number, { title: string; included: boolean }>();
      result.chapters.forEach((ch) => {
        states.set(ch.index, { title: ch.title, included: true });
      });
      setChapterStates(states);
    } catch (error) {
      toast.error('Failed to re-detect chapters');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle chapter inclusion
  const toggleChapter = (index: number) => {
    setChapterStates((prev) => {
      const newStates = new Map(prev);
      const current = newStates.get(index);
      if (current) {
        newStates.set(index, { ...current, included: !current.included });
      }
      return newStates;
    });
  };

  // Update chapter title
  const updateChapterTitle = (index: number, title: string) => {
    setChapterStates((prev) => {
      const newStates = new Map(prev);
      const current = newStates.get(index);
      if (current) {
        newStates.set(index, { ...current, title });
      }
      return newStates;
    });
  };

  // Create the manuscript
  const handleCreate = async () => {
    if (!preview) return;

    setIsLoading(true);

    try {
      // Build chapter adjustments
      const adjustments: ChapterAdjustment[] = [];
      chapterStates.forEach((state, index) => {
        const original = preview.chapters.find((ch) => ch.index === index);
        if (original) {
          // Only include adjustment if something changed
          if (!state.included || state.title !== original.title) {
            adjustments.push({
              index,
              title: state.title !== original.title ? state.title : undefined,
              included: state.included,
            });
          }
        }
      });

      const result = await importApi.createFromImport({
        parse_id: preview.parse_id,
        title: editedTitle !== preview.title ? editedTitle : undefined,
        author: editedAuthor !== (preview.author || '') ? editedAuthor : undefined,
        chapter_adjustments: adjustments.length > 0 ? adjustments : undefined,
        series_id: seriesId,
      });

      analytics.importCompleted(
        result.manuscript_id,
        preview.source_format,
        result.total_words,
        result.chapter_count
      );

      toast.success(`Imported "${result.title}" with ${result.chapter_count} chapters`);
      onImportComplete(result.manuscript_id);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import manuscript';
      toast.error(message);
      analytics.importFailed(preview.source_format, message);
    } finally {
      setIsLoading(false);
    }
  };

  // Get included chapters count
  const includedCount = Array.from(chapterStates.values()).filter((s) => s.included).length;
  const totalWords = preview?.chapters
    .filter((ch) => chapterStates.get(ch.index)?.included)
    .reduce((sum, ch) => sum + ch.word_count, 0) || 0;

  // Get format info for selected file
  const getFormatInfo = (filename: string): SupportedFormat | undefined => {
    const ext = '.' + filename.split('.').pop()?.toLowerCase();
    return formats.find((f) => f.extension === ext);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-vellum rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui flex items-center justify-between">
          <div>
            <h2 className="font-garamond text-2xl font-semibold text-midnight">
              Import Manuscript
            </h2>
            <p className="text-sm text-faded-ink font-sans">
              {step === 'upload' && 'Step 1: Select a document to import'}
              {step === 'preview' && 'Step 2: Review and configure chapters'}
              {step === 'confirm' && 'Step 3: Confirm and create manuscript'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight transition-colors"
            disabled={isLoading}
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Upload */}
          {step === 'upload' && (
            <div className="space-y-6">
              {/* Drop zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
                  transition-colors
                  ${isDragging
                    ? 'border-bronze bg-bronze/5'
                    : selectedFile
                    ? 'border-green-500 bg-green-50'
                    : 'border-slate-ui hover:border-bronze hover:bg-bronze/5'
                  }
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_EXTENSIONS}
                  onChange={handleFileInputChange}
                  className="hidden"
                />

                {selectedFile ? (
                  <div>
                    <div className="text-4xl mb-4">&#x1F4C4;</div>
                    <p className="font-sans text-midnight font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-faded-ink mt-1">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                    {getFormatInfo(selectedFile.name) && (
                      <p className="text-sm text-bronze mt-2">
                        {getFormatInfo(selectedFile.name)?.name} - {getFormatInfo(selectedFile.name)?.formatting_support} formatting support
                      </p>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                      }}
                      className="mt-3 text-sm text-faded-ink hover:text-midnight underline"
                    >
                      Choose different file
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-4">&#x1F4E5;</div>
                    <p className="font-sans text-midnight font-medium">
                      Drop your document here or click to browse
                    </p>
                    <p className="text-sm text-faded-ink mt-2">
                      Supports Word (.docx), OpenDocument (.odt), RTF, Markdown, PDF, and plain text
                    </p>
                  </div>
                )}
              </div>

              {/* Detection mode selector */}
              <div>
                <label className="block text-sm font-medium text-midnight mb-2 font-sans">
                  Chapter Detection
                </label>
                <select
                  value={detectionMode}
                  onChange={(e) => setDetectionMode(e.target.value as DetectionMode)}
                  className="w-full px-3 py-2 border border-slate-ui rounded-lg font-sans text-midnight bg-white focus:outline-none focus:ring-2 focus:ring-bronze"
                >
                  {DETECTION_MODES.map((mode) => (
                    <option key={mode.value} value={mode.value}>
                      {mode.label} - {mode.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Format cards */}
              {formats.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-midnight mb-3 font-sans">Supported Formats</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {formats.map((format) => (
                      <div
                        key={format.extension}
                        className="border border-slate-ui rounded-lg p-3 bg-white"
                      >
                        <div className="font-medium text-midnight font-sans">{format.name}</div>
                        <div className="text-xs text-faded-ink mt-1">{format.extension}</div>
                        <div className={`text-xs mt-1 ${
                          format.formatting_support === 'full'
                            ? 'text-green-600'
                            : format.formatting_support === 'partial'
                            ? 'text-amber-600'
                            : 'text-faded-ink'
                        }`}>
                          {format.formatting_support === 'full' && 'Full formatting'}
                          {format.formatting_support === 'partial' && 'Partial formatting'}
                          {format.formatting_support === 'none' && 'Plain text only'}
                        </div>
                        {format.warning && (
                          <div className="text-xs text-amber-600 mt-1">
                            {format.warning}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Preview */}
          {step === 'preview' && preview && (
            <div className="space-y-6">
              {/* Format warnings */}
              {preview.format_warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="font-medium text-amber-800 font-sans mb-2">Import Notes</h4>
                  <ul className="text-sm text-amber-700 space-y-1">
                    {preview.format_warnings.map((warning, i) => (
                      <li key={i}>&#x26A0; {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Manuscript details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-midnight mb-1 font-sans">
                    Title
                  </label>
                  <input
                    type="text"
                    value={editedTitle}
                    onChange={(e) => setEditedTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-ui rounded-lg font-sans text-midnight bg-white focus:outline-none focus:ring-2 focus:ring-bronze"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-midnight mb-1 font-sans">
                    Author
                  </label>
                  <input
                    type="text"
                    value={editedAuthor}
                    onChange={(e) => setEditedAuthor(e.target.value)}
                    placeholder="(optional)"
                    className="w-full px-3 py-2 border border-slate-ui rounded-lg font-sans text-midnight bg-white focus:outline-none focus:ring-2 focus:ring-bronze"
                  />
                </div>
              </div>

              {/* Detection mode changer */}
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-midnight font-sans">
                  Detection mode:
                </label>
                <select
                  value={detectionMode}
                  onChange={(e) => handleRedetect(e.target.value as DetectionMode)}
                  disabled={isLoading}
                  className="px-3 py-1.5 border border-slate-ui rounded-lg font-sans text-midnight bg-white focus:outline-none focus:ring-2 focus:ring-bronze text-sm"
                >
                  {DETECTION_MODES.map((mode) => (
                    <option key={mode.value} value={mode.value}>
                      {mode.label}
                    </option>
                  ))}
                </select>
                {isLoading && (
                  <span className="text-sm text-faded-ink">Re-detecting...</span>
                )}
              </div>

              {/* Chapter list */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-midnight font-sans">
                    Detected Chapters ({preview.chapters.length})
                  </h3>
                  <span className="text-sm text-faded-ink">
                    {includedCount} selected - {totalWords.toLocaleString()} words
                  </span>
                </div>

                <div className="border border-slate-ui rounded-lg divide-y divide-slate-ui max-h-80 overflow-y-auto">
                  {preview.chapters.map((chapter) => {
                    const state = chapterStates.get(chapter.index);
                    const isIncluded = state?.included ?? true;
                    const title = state?.title ?? chapter.title;

                    return (
                      <div
                        key={chapter.index}
                        className={`p-4 ${!isIncluded ? 'bg-gray-50 opacity-60' : 'bg-white'}`}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={isIncluded}
                            onChange={() => toggleChapter(chapter.index)}
                            className="mt-1 h-4 w-4 rounded border-slate-ui text-bronze focus:ring-bronze"
                          />
                          <div className="flex-1 min-w-0">
                            <input
                              type="text"
                              value={title}
                              onChange={(e) => updateChapterTitle(chapter.index, e.target.value)}
                              disabled={!isIncluded}
                              className="w-full font-medium text-midnight font-sans bg-transparent border-0 border-b border-transparent hover:border-slate-ui focus:border-bronze focus:outline-none py-0.5 -my-0.5"
                            />
                            <p className="text-sm text-faded-ink mt-1">
                              {chapter.word_count.toLocaleString()} words
                            </p>
                            <p className="text-sm text-faded-ink mt-1 line-clamp-2">
                              {chapter.preview_text}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Confirm */}
          {step === 'confirm' && preview && (
            <div className="space-y-6">
              <div className="bg-bronze/5 rounded-lg p-6 text-center">
                <div className="text-4xl mb-4">&#x1F4D6;</div>
                <h3 className="font-garamond text-2xl font-semibold text-midnight">
                  {editedTitle}
                </h3>
                {editedAuthor && (
                  <p className="text-faded-ink mt-1">by {editedAuthor}</p>
                )}
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white rounded-lg border border-slate-ui p-4">
                  <div className="text-2xl font-garamond font-semibold text-bronze">
                    {includedCount}
                  </div>
                  <div className="text-sm text-faded-ink">Chapters</div>
                </div>
                <div className="bg-white rounded-lg border border-slate-ui p-4">
                  <div className="text-2xl font-garamond font-semibold text-bronze">
                    {totalWords.toLocaleString()}
                  </div>
                  <div className="text-sm text-faded-ink">Words</div>
                </div>
                <div className="bg-white rounded-lg border border-slate-ui p-4">
                  <div className="text-2xl font-garamond font-semibold text-bronze">
                    {preview.source_format.toUpperCase().replace('.', '')}
                  </div>
                  <div className="text-sm text-faded-ink">Format</div>
                </div>
              </div>

              {seriesId && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <p className="text-green-700 font-sans text-sm">
                    This manuscript will be added to your series
                  </p>
                </div>
              )}

              <p className="text-center text-faded-ink text-sm">
                Click "Import" to create your manuscript with all chapters and formatting preserved.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-ui flex items-center justify-between">
          <div>
            {step !== 'upload' && (
              <button
                onClick={() => setStep(step === 'confirm' ? 'preview' : 'upload')}
                disabled={isLoading}
                className="px-4 py-2 text-faded-ink hover:text-midnight font-sans transition-colors"
              >
                &larr; Back
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border border-slate-ui rounded-lg font-sans text-midnight hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>

            {step === 'upload' && (
              <button
                onClick={handleParse}
                disabled={!selectedFile || isLoading}
                className="px-6 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Parsing...' : 'Continue'}
              </button>
            )}

            {step === 'preview' && (
              <button
                onClick={() => setStep('confirm')}
                disabled={includedCount === 0 || isLoading}
                className="px-6 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
              </button>
            )}

            {step === 'confirm' && (
              <button
                onClick={handleCreate}
                disabled={isLoading}
                className="px-6 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Importing...' : 'Import'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
