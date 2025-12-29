/**
 * ExportModal - Export manuscript to various formats
 * Supports DOCX and PDF export with chapter selection
 */

import { useState, useEffect } from 'react';
import { toast } from '@/stores/toastStore';

interface ExportModalProps {
  manuscriptId: string;
  onClose: () => void;
}

interface ExportPreview {
  manuscript_id: string;
  title: string;
  author: string | null;
  total_chapters: number;
  total_words: number;
  chapters: Array<{
    id: string;
    title: string;
    word_count: number;
    order_index: number;
  }>;
}

export default function ExportModal({ manuscriptId, onClose }: ExportModalProps) {
  const [preview, setPreview] = useState<ExportPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<'docx' | 'pdf'>('docx');
  const [selectedChapters, setSelectedChapters] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(true);

  useEffect(() => {
    loadPreview();
  }, [manuscriptId]);

  const loadPreview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/export/preview/${manuscriptId}`);

      if (!response.ok) {
        throw new Error('Failed to load export preview');
      }

      const data = await response.json();
      setPreview(data.data);

      // Select all chapters by default
      const allIds = new Set<string>(data.data.chapters.map((ch: any) => ch.id));
      setSelectedChapters(allIds);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to load preview';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChapter = (chapterId: string) => {
    const newSelected = new Set(selectedChapters);
    if (newSelected.has(chapterId)) {
      newSelected.delete(chapterId);
    } else {
      newSelected.add(chapterId);
    }
    setSelectedChapters(newSelected);
    setSelectAll(newSelected.size === preview?.chapters.length);
  };

  const handleToggleAll = () => {
    if (selectAll) {
      setSelectedChapters(new Set<string>());
    } else {
      const allIds = new Set<string>(preview?.chapters.map(ch => ch.id) || []);
      setSelectedChapters(allIds);
    }
    setSelectAll(!selectAll);
  };

  const handleExport = async () => {
    if (selectedChapters.size === 0) {
      toast.error('Please select at least one chapter to export');
      return;
    }

    try {
      setExporting(true);
      const endpoint = selectedFormat === 'docx'
        ? `http://localhost:8000/api/export/docx/${manuscriptId}`
        : `http://localhost:8000/api/export/pdf/${manuscriptId}`;

      const requestBody = selectAll
        ? { chapter_ids: null, include_folders: false }
        : { chapter_ids: Array.from(selectedChapters), include_folders: false };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/);
      const filename = filenameMatch?.[1] || `manuscript.${selectedFormat}`;

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Exported to ${selectedFormat.toUpperCase()} successfully!`);
      onClose();
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Export failed';
      toast.error(errorMsg);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[200] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b-2 border-bronze/30 bg-gradient-to-r from-vellum to-white flex items-center justify-between sticky top-0 z-10">
          <h2 className="font-garamond text-3xl font-semibold text-midnight">
            Export Manuscript
          </h2>
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight transition-colors text-3xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-16 h-16 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : preview ? (
            <div className="space-y-6">
              {/* Manuscript Info */}
              <div className="bg-white border-2 border-slate-ui/30 rounded-sm p-4">
                <h3 className="font-garamond text-xl font-semibold text-midnight mb-2">
                  {preview.title}
                </h3>
                {preview.author && (
                  <p className="text-faded-ink font-sans text-sm mb-3">by {preview.author}</p>
                )}
                <div className="flex gap-6 text-sm font-sans">
                  <div>
                    <span className="text-faded-ink">Chapters:</span>
                    <span className="ml-2 font-semibold text-midnight">{preview.total_chapters}</span>
                  </div>
                  <div>
                    <span className="text-faded-ink">Total Words:</span>
                    <span className="ml-2 font-semibold text-midnight">
                      {preview.total_words.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Format Selection */}
              <div>
                <label className="block text-sm font-sans font-semibold text-midnight mb-2">
                  Export Format
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setSelectedFormat('docx')}
                    className={`flex-1 px-4 py-3 rounded-sm font-sans transition-all ${
                      selectedFormat === 'docx'
                        ? 'bg-bronze text-white shadow-md'
                        : 'bg-white border-2 border-slate-ui text-midnight hover:border-bronze'
                    }`}
                  >
                    <div className="text-2xl mb-1">📄</div>
                    <div className="font-semibold">DOCX</div>
                    <div className="text-xs opacity-80">Microsoft Word</div>
                  </button>
                  <button
                    onClick={() => setSelectedFormat('pdf')}
                    className={`flex-1 px-4 py-3 rounded-sm font-sans transition-all ${
                      selectedFormat === 'pdf'
                        ? 'bg-bronze text-white shadow-md'
                        : 'bg-white border-2 border-slate-ui text-midnight hover:border-bronze'
                    }`}
                  >
                    <div className="text-2xl mb-1">📋</div>
                    <div className="font-semibold">PDF</div>
                    <div className="text-xs opacity-80">Portable Document</div>
                  </button>
                </div>
              </div>

              {/* Chapter Selection */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-sans font-semibold text-midnight">
                    Select Chapters
                  </label>
                  <button
                    onClick={handleToggleAll}
                    className="text-sm font-sans text-bronze hover:text-bronze/80 transition-colors"
                  >
                    {selectAll ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                <div className="bg-white border-2 border-slate-ui/30 rounded-sm max-h-64 overflow-y-auto">
                  {preview.chapters.map((chapter) => (
                    <label
                      key={chapter.id}
                      className="flex items-center gap-3 px-4 py-3 hover:bg-slate-ui/10 cursor-pointer border-b border-slate-ui/20 last:border-b-0"
                    >
                      <input
                        type="checkbox"
                        checked={selectedChapters.has(chapter.id)}
                        onChange={() => handleToggleChapter(chapter.id)}
                        className="w-4 h-4 text-bronze border-slate-ui rounded focus:ring-2 focus:ring-bronze"
                      />
                      <div className="flex-1">
                        <div className="font-sans text-sm text-midnight font-medium">
                          {chapter.title}
                        </div>
                        <div className="font-sans text-xs text-faded-ink">
                          {chapter.word_count.toLocaleString()} words
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                <p className="text-xs text-faded-ink font-sans mt-2">
                  {selectedChapters.size} of {preview.chapters.length} chapters selected
                </p>
              </div>

              {/* Export Button */}
              <div className="flex gap-3 justify-end pt-4 border-t-2 border-slate-ui/30">
                <button
                  onClick={onClose}
                  className="px-6 py-3 bg-slate-ui text-midnight rounded-sm font-semibold font-sans hover:bg-slate-ui/70 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExport}
                  disabled={exporting || selectedChapters.size === 0}
                  className="px-6 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {exporting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Exporting...</span>
                    </>
                  ) : (
                    <>
                      <span>📥</span>
                      <span>Export to {selectedFormat.toUpperCase()}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
