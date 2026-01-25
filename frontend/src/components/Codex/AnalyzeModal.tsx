/**
 * AnalyzeModal - Modal for selecting analysis scope (current chapter vs entire manuscript)
 */

import { useState } from 'react';
import { codexApi, timelineApi, chaptersApi, type Chapter } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';

interface AnalyzeModalProps {
  manuscriptId: string;
  currentChapterContent: string;
  onClose: () => void;
}

type AnalysisScope = 'current' | 'manuscript';

interface AnalysisProgress {
  status: 'idle' | 'loading' | 'analyzing' | 'complete' | 'error';
  currentChapter: number;
  totalChapters: number;
  message: string;
}

export default function AnalyzeModal({
  manuscriptId,
  currentChapterContent,
  onClose,
}: AnalyzeModalProps) {
  const [scope, setScope] = useState<AnalysisScope>('current');
  const [progress, setProgress] = useState<AnalysisProgress>({
    status: 'idle',
    currentChapter: 0,
    totalChapters: 0,
    message: '',
  });
  const { setAnalyzing, setSidebarOpen, setActiveTab } = useCodexStore();

  // Recursively collect all non-folder chapters from tree
  const collectChapters = (chapters: Chapter[]): Chapter[] => {
    const result: Chapter[] = [];
    for (const chapter of chapters) {
      if (!chapter.is_folder) {
        result.push(chapter);
      }
      if (chapter.children && chapter.children.length > 0) {
        result.push(...collectChapters(chapter.children as Chapter[]));
      }
    }
    return result;
  };

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);

      if (scope === 'current') {
        // Analyze current chapter only
        if (!currentChapterContent.trim()) {
          alert('No text to analyze. Start writing first!');
          setAnalyzing(false);
          return;
        }

        setProgress({
          status: 'analyzing',
          currentChapter: 1,
          totalChapters: 1,
          message: 'Analyzing current chapter...',
        });

        await Promise.all([
          codexApi.analyzeText({
            manuscript_id: manuscriptId,
            text: currentChapterContent.trim(),
          }),
          timelineApi.analyzeTimeline({
            manuscript_id: manuscriptId,
            text: currentChapterContent.trim(),
          }),
        ]);

        setProgress({
          status: 'complete',
          currentChapter: 1,
          totalChapters: 1,
          message: 'Analysis complete!',
        });
      } else {
        // Analyze entire manuscript
        setProgress({
          status: 'loading',
          currentChapter: 0,
          totalChapters: 0,
          message: 'Loading chapters...',
        });

        // Get chapter tree
        const chapterTree = await chaptersApi.getChapterTree(manuscriptId);
        const allChapters = collectChapters(chapterTree as unknown as Chapter[]);

        if (allChapters.length === 0) {
          alert('No chapters found in manuscript.');
          setAnalyzing(false);
          setProgress({ status: 'idle', currentChapter: 0, totalChapters: 0, message: '' });
          return;
        }

        setProgress({
          status: 'loading',
          currentChapter: 0,
          totalChapters: allChapters.length,
          message: `Found ${allChapters.length} chapters. Loading content...`,
        });

        // Fetch content for all chapters
        const chapterContents: string[] = [];
        for (let i = 0; i < allChapters.length; i++) {
          setProgress({
            status: 'loading',
            currentChapter: i + 1,
            totalChapters: allChapters.length,
            message: `Loading chapter ${i + 1} of ${allChapters.length}: ${allChapters[i].title}`,
          });

          const fullChapter = await chaptersApi.getChapter(allChapters[i].id);
          if (fullChapter.content && fullChapter.content.trim()) {
            chapterContents.push(fullChapter.content.trim());
          }
        }

        const combinedText = chapterContents.join('\n\n---\n\n');

        if (!combinedText.trim()) {
          alert('No text found in any chapters. Start writing first!');
          setAnalyzing(false);
          setProgress({ status: 'idle', currentChapter: 0, totalChapters: 0, message: '' });
          return;
        }

        setProgress({
          status: 'analyzing',
          currentChapter: allChapters.length,
          totalChapters: allChapters.length,
          message: `Analyzing ${chapterContents.length} chapters (${combinedText.split(/\s+/).length} words)...`,
        });

        // Analyze combined text
        await Promise.all([
          codexApi.analyzeText({
            manuscript_id: manuscriptId,
            text: combinedText,
          }),
          timelineApi.analyzeTimeline({
            manuscript_id: manuscriptId,
            text: combinedText,
          }),
        ]);

        setProgress({
          status: 'complete',
          currentChapter: allChapters.length,
          totalChapters: allChapters.length,
          message: `Analysis complete! Processed ${chapterContents.length} chapters.`,
        });
      }

      // Show success after a short delay so user sees "complete" message
      setTimeout(() => {
        setSidebarOpen(true);
        setActiveTab('intel');
        onClose();
      }, 1000);
    } catch (err) {
      console.error('Analyze error:', err);
      setProgress({
        status: 'error',
        currentChapter: 0,
        totalChapters: 0,
        message: 'Analysis failed: ' + (err instanceof Error ? err.message : 'Unknown error'),
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const isAnalyzing = progress.status === 'loading' || progress.status === 'analyzing';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div
        className="bg-white max-w-md w-full mx-4 p-6 shadow-xl"
        style={{ borderRadius: '4px' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-garamond text-xl font-semibold text-midnight">
            Analyze Manuscript
          </h2>
          <button
            onClick={onClose}
            disabled={isAnalyzing}
            className="text-faded-ink hover:text-midnight disabled:opacity-50"
            title="Close"
          >
            x
          </button>
        </div>

        {/* Description */}
        <p className="text-sm text-faded-ink font-sans mb-4">
          Extract characters, locations, items, lore, and timeline events from your manuscript using NLP analysis.
        </p>

        {/* Scope Selection */}
        <div className="space-y-3 mb-6">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="current"
              checked={scope === 'current'}
              onChange={() => setScope('current')}
              disabled={isAnalyzing}
              className="mt-1 accent-bronze"
            />
            <div>
              <span className="font-sans font-medium text-midnight">Current Chapter</span>
              <p className="text-xs text-faded-ink">Analyze only the chapter you're currently editing</p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="radio"
              name="scope"
              value="manuscript"
              checked={scope === 'manuscript'}
              onChange={() => setScope('manuscript')}
              disabled={isAnalyzing}
              className="mt-1 accent-bronze"
            />
            <div>
              <span className="font-sans font-medium text-midnight">Entire Manuscript</span>
              <p className="text-xs text-faded-ink">Analyze all chapters for a comprehensive entity extraction</p>
            </div>
          </label>
        </div>

        {/* Progress Indicator */}
        {progress.status !== 'idle' && (
          <div className="mb-4 p-3 bg-vellum rounded" style={{ borderRadius: '2px' }}>
            <div className="flex items-center gap-2">
              {isAnalyzing && (
                <div className="w-4 h-4 border-2 border-bronze border-t-transparent rounded-full animate-spin" />
              )}
              {progress.status === 'complete' && <span className="text-green-600">Done!</span>}
              {progress.status === 'error' && <span className="text-redline">Error</span>}
              <span className="text-sm text-midnight font-sans">{progress.message}</span>
            </div>

            {/* Progress bar for manuscript-wide analysis */}
            {scope === 'manuscript' && progress.totalChapters > 0 && isAnalyzing && (
              <div className="mt-2">
                <div className="h-2 bg-slate-ui rounded overflow-hidden">
                  <div
                    className="h-full bg-bronze transition-all duration-300"
                    style={{
                      width: `${(progress.currentChapter / progress.totalChapters) * 100}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-faded-ink mt-1">
                  {progress.currentChapter} of {progress.totalChapters} chapters
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={isAnalyzing}
            className="px-4 py-2 text-sm font-sans text-midnight bg-slate-ui hover:bg-slate-ui/80 transition-colors disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="px-4 py-2 text-sm font-sans text-white bg-bronze hover:bg-bronze/90 transition-colors disabled:opacity-50 flex items-center gap-2"
            style={{ borderRadius: '2px' }}
          >
            {isAnalyzing && (
              <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
          </button>
        </div>
      </div>
    </div>
  );
}
