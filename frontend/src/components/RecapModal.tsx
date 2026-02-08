/**
 * RecapModal - "Spotify Wrapped" style writing stats recap
 * Generates and displays shareable cards with writing statistics
 */

import { useState, useEffect } from 'react';
import { RecapCardGenerator, type WritingStats, type TemplateType } from '@/services/recapCardGenerator';
import { toast } from '@/stores/toastStore';

interface RecapModalProps {
  manuscriptId: string;
  onClose: () => void;
  embedded?: boolean;
}

export default function RecapModal({ manuscriptId, onClose, embedded = false }: RecapModalProps) {
  const [stats, setStats] = useState<WritingStats | null>(null);
  const [template, setTemplate] = useState<TemplateType>('dark');
  const [timeframe, setTimeframe] = useState<string>('week');
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [sharing, setSharing] = useState(false);

  const cardGen = new RecapCardGenerator();

  // Fetch stats when timeframe changes
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        console.log('Fetching stats for manuscript:', manuscriptId);
        const response = await fetch(
          `http://localhost:8000/api/stats/recap/${manuscriptId}?timeframe=${timeframe}`
        );

        if (!response.ok) {
          const errorData = await response.json();
          console.error('Stats API error:', errorData);
          throw new Error(errorData.detail || 'Failed to fetch stats');
        }

        const data = await response.json();
        console.log('Stats received:', data);
        setStats(data.data);
      } catch (error) {
        console.error('Failed to load stats:', error);
        toast.error(`Failed to load writing stats: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [manuscriptId, timeframe]);

  // Generate preview when stats or template changes
  useEffect(() => {
    if (!stats) return;

    const generatePreview = async () => {
      try {
        setGenerating(true);
        const blob = await cardGen.generateCard(stats, template);
        const url = URL.createObjectURL(blob);

        // Cleanup previous URL
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl);
        }

        setPreviewUrl(url);
      } catch (error) {
        console.error('Failed to generate preview:', error);
        toast.error('Failed to generate preview');
      } finally {
        setGenerating(false);
      }
    };

    generatePreview();

    // Cleanup on unmount
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [stats, template]);

  const handleShare = async () => {
    if (!stats) return;

    try {
      setSharing(true);
      const blob = await cardGen.generateCard(stats, template);
      await cardGen.shareToSocial(blob, stats);
      toast.success('Shared successfully!');
    } catch (error) {
      console.error('Failed to share:', error);
      // Don't show error if user just cancelled
      if ((error as Error).name !== 'AbortError') {
        toast.info('Image downloaded to your device');
      }
    } finally {
      setSharing(false);
    }
  };

  const handleCopy = async () => {
    if (!stats) return;

    try {
      const blob = await cardGen.generateCard(stats, template);
      await cardGen.copyToClipboard(blob);
      toast.success('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
      toast.error('Failed to copy to clipboard');
    }
  };

  const content = (
        <div className={embedded ? '' : 'p-6'}>
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-12 h-12 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <>
              {/* Timeframe selector */}
              <div className="mb-6">
                <label className="block text-sm font-sans text-faded-ink mb-2">
                  Time Period
                </label>
                <div className="flex gap-2 flex-wrap">
                  {[
                    { value: 'day', label: 'Today' },
                    { value: 'week', label: 'This Week' },
                    { value: 'month', label: 'This Month' },
                    { value: 'all_time', label: 'All Time' }
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setTimeframe(option.value)}
                      className={`px-4 py-2 rounded-sm font-sans text-sm transition-colors ${
                        timeframe === option.value
                          ? 'bg-bronze text-white'
                          : 'bg-slate-ui text-midnight hover:bg-slate-ui/70'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Template selector */}
              <div className="mb-6">
                <label className="block text-sm font-sans text-faded-ink mb-2">
                  Style
                </label>
                <div className="flex gap-3">
                  {(['dark', 'vintage', 'neon'] as TemplateType[]).map((t) => (
                    <button
                      key={t}
                      onClick={() => setTemplate(t)}
                      className={`px-4 py-2 rounded-sm font-sans text-sm transition-colors ${
                        template === t
                          ? 'bg-bronze text-white'
                          : 'bg-slate-ui text-midnight hover:bg-slate-ui/70'
                      }`}
                    >
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Preview */}
              <div className="mb-6 relative">
                {generating && (
                  <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
                    <div className="w-8 h-8 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
                {previewUrl && (
                  <div className="bg-slate-ui/20 rounded-sm p-4 flex justify-center">
                    <img
                      src={previewUrl}
                      alt="Recap card preview"
                      className="max-w-md w-full shadow-2xl rounded-sm"
                      style={{ aspectRatio: '9/16' }}
                    />
                  </div>
                )}
              </div>

              {/* Stats summary */}
              {stats && (
                <div className="mb-6 p-4 bg-white border border-slate-ui rounded-sm">
                  <p className="font-sans text-sm text-faded-ink mb-2">
                    Quick Stats for {stats.timeframe_label}:
                  </p>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-2xl font-bold text-midnight">
                        {stats.word_count.toLocaleString()}
                      </p>
                      <p className="text-xs text-faded-ink">Words</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-midnight">
                        {stats.session_count}
                      </p>
                      <p className="text-xs text-faded-ink">Sessions</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-midnight">
                        {stats.longest_streak}
                      </p>
                      <p className="text-xs text-faded-ink">Day Streak</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 justify-center flex-wrap">
                <button
                  onClick={handleShare}
                  disabled={!stats || sharing}
                  className="px-6 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors"
                >
                  {sharing ? 'Sharing...' : 'Share / Download'}
                </button>
                <button
                  onClick={handleCopy}
                  disabled={!stats}
                  className="px-6 py-3 bg-white border border-slate-ui text-midnight rounded-sm font-sans hover:bg-slate-ui/20 disabled:opacity-50 transition-colors"
                >
                  Copy to Clipboard
                </button>
                {!embedded && (
                  <button
                    onClick={onClose}
                    className="px-6 py-3 bg-slate-ui text-midnight rounded-sm font-sans hover:bg-slate-ui/70 transition-colors"
                  >
                    Close
                  </button>
                )}
              </div>
            </>
          )}
        </div>
  );

  if (embedded) {
    return content;
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[200] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-slate-ui bg-white flex items-center justify-between">
          <h2 className="font-garamond text-3xl font-semibold text-midnight">
            Your Writing Wrapped
          </h2>
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
            aria-label="Close"
          >
            &times;
          </button>
        </div>
        <div className="p-6">
          {content}
        </div>
      </div>
    </div>
  );
}
