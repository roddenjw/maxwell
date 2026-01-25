/**
 * ChapterRecapModal - Beautiful AI-generated chapter summaries
 * Displays structured recaps with themes, events, and character developments
 * Includes sharing functionality with visual recap cards
 */

import { useState, useEffect } from 'react';
import { recapApi, chaptersApi, shareApi, type ChapterRecap } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import {
  chapterRecapCardGenerator,
  type ChapterRecapData,
  type ChapterTemplateType,
  type CardFormat
} from '@/services/chapterRecapCardGenerator';
import analytics from '@/lib/analytics';

interface ChapterRecapModalProps {
  chapterId: string;
  chapterTitle?: string;
  manuscriptId?: string;
  onClose: () => void;
}

export default function ChapterRecapModal({
  chapterId,
  chapterTitle,
  manuscriptId,
  onClose,
}: ChapterRecapModalProps) {
  const [recap, setRecap] = useState<ChapterRecap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [title, setTitle] = useState(chapterTitle || 'Chapter');
  const [wordCount, setWordCount] = useState(0);

  // Sharing state
  const [showSharePanel, setShowSharePanel] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ChapterTemplateType>('dark');
  const [selectedFormat, setSelectedFormat] = useState<CardFormat>('story');
  const [generatingCard, setGeneratingCard] = useState(false);
  const [cardPreview, setCardPreview] = useState<string | null>(null);
  const [cardBlob, setCardBlob] = useState<Blob | null>(null);

  useEffect(() => {
    // Fetch chapter info (title and word count)
    chaptersApi.getChapter(chapterId)
      .then(chapter => {
        if (!chapterTitle) {
          setTitle(chapter.title);
        }
        setWordCount(chapter.word_count || 0);
      })
      .catch(() => {
        if (!chapterTitle) setTitle('Chapter');
      });
    loadRecap();
  }, [chapterId, chapterTitle]);

  const loadRecap = async (forceRegenerate = false) => {
    try {
      setLoading(true);
      setError(null);

      const data = await recapApi.generateChapterRecap(chapterId, forceRegenerate);
      setRecap(data);

      if (data.is_cached && !forceRegenerate) {
        toast.success('Recap loaded from cache');
      } else {
        toast.success('Recap generated successfully');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load recap';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    await loadRecap(true);
  };

  // Generate recap card preview
  const generateCardPreview = async () => {
    if (!recap) return;

    try {
      setGeneratingCard(true);

      const recapData: ChapterRecapData = {
        chapter_title: title,
        word_count: wordCount,
        summary: recap.content.summary,
        key_events: recap.content.key_events,
        emotional_tone: recap.content.emotional_tone,
        memorable_quote: recap.content.memorable_moments?.[0],
        themes: recap.content.themes,
      };

      const blob = await chapterRecapCardGenerator.generateCard(
        recapData,
        selectedTemplate,
        selectedFormat
      );

      // Create preview URL
      const url = URL.createObjectURL(blob);
      setCardPreview(url);
      setCardBlob(blob);

      analytics.recapCardGenerated('chapter', selectedTemplate);
    } catch (err) {
      toast.error('Failed to generate card preview');
      console.error(err);
    } finally {
      setGeneratingCard(false);
    }
  };

  // Handle share to platform
  const handleShare = async (platform: 'twitter' | 'facebook' | 'instagram' | 'download' | 'copy') => {
    if (!cardBlob || !recap) {
      toast.error('Please generate a card first');
      return;
    }

    try {
      const recapData: ChapterRecapData = {
        chapter_title: title,
        word_count: wordCount,
        summary: recap.content.summary,
      };

      await chapterRecapCardGenerator.shareToSocial(cardBlob, recapData, platform);

      // Track share
      if (manuscriptId) {
        try {
          const shareResult = await shareApi.createShare({
            manuscript_id: manuscriptId,
            chapter_id: chapterId,
            recap_type: 'chapter',
            title: title,
            description: recap.content.summary,
            template: selectedTemplate,
            recap_content: recap.content,
          });

          await shareApi.trackShare(shareResult.share_id, platform);
        } catch (e) {
          // Non-critical, just log
          console.error('Failed to track share:', e);
        }
      }

      if (platform === 'copy') {
        toast.success('Image copied to clipboard!');
      } else if (platform === 'download') {
        toast.success('Image downloaded!');
      } else {
        toast.success(`Sharing to ${platform}...`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to share');
    }
  };

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (cardPreview) {
        URL.revokeObjectURL(cardPreview);
      }
    };
  }, [cardPreview]);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[200] p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b-2 border-bronze/30 bg-gradient-to-r from-vellum to-white flex items-center justify-between sticky top-0 z-10">
          <div>
            <h2 className="font-garamond text-3xl font-semibold text-midnight">
              Chapter Recap
            </h2>
            <p className="text-sm text-faded-ink font-sans mt-1">{title}</p>
          </div>
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
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="w-16 h-16 border-4 border-bronze border-t-transparent rounded-full animate-spin"></div>
              <p className="text-faded-ink font-sans text-sm">
                {regenerating ? 'Regenerating recap...' : 'Generating your chapter recap...'}
              </p>
              <p className="text-faded-ink/60 font-sans text-xs">
                This may take 10-20 seconds
              </p>
            </div>
          ) : error ? (
            <div className="text-center py-20">
              <div className="text-red-600 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-midnight font-sans text-lg mb-2">Failed to generate recap</p>
              <p className="text-faded-ink font-sans text-sm mb-6">{error}</p>
              <button
                onClick={() => loadRecap()}
                className="px-6 py-2 bg-bronze text-white rounded-sm font-sans hover:bg-bronze/90 transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : recap ? (
            <div className="space-y-6">
              {/* Cache indicator */}
              {recap.is_cached && (
                <div className="flex items-center gap-2 text-xs text-faded-ink bg-slate-ui/30 px-3 py-2 rounded-sm">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Loaded from cache - Generated {new Date(recap.created_at).toLocaleDateString()}</span>
                </div>
              )}

              {/* Summary */}
              <section className="bg-white border-l-4 border-bronze p-6 rounded-sm shadow-sm">
                <h3 className="font-garamond text-2xl font-semibold text-midnight mb-3 flex items-center gap-2">
                  <span className="text-bronze">📖</span> Summary
                </h3>
                <p className="text-midnight font-sans leading-relaxed text-base">
                  {recap.content.summary}
                </p>
              </section>

              {/* Key Events */}
              {recap.content.key_events && recap.content.key_events.length > 0 && (
                <section className="bg-white border-l-4 border-bronze/70 p-6 rounded-sm shadow-sm">
                  <h3 className="font-garamond text-xl font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-bronze">🎯</span> Key Events
                  </h3>
                  <ul className="space-y-3">
                    {recap.content.key_events.map((event, index) => (
                      <li key={index} className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-bronze/10 text-bronze text-sm flex items-center justify-center font-semibold">
                          {index + 1}
                        </span>
                        <span className="text-midnight font-sans flex-1">{event}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Character Developments */}
              {recap.content.character_developments && recap.content.character_developments.length > 0 && (
                <section className="bg-white border-l-4 border-bronze/70 p-6 rounded-sm shadow-sm">
                  <h3 className="font-garamond text-xl font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-bronze">👥</span> Character Developments
                  </h3>
                  <div className="space-y-4">
                    {recap.content.character_developments.map((dev, index) => (
                      <div key={index} className="bg-vellum/50 p-4 rounded-sm">
                        <p className="font-semibold text-bronze mb-1">{dev.character}</p>
                        <p className="text-midnight font-sans text-sm">{dev.development}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Themes */}
              {recap.content.themes && recap.content.themes.length > 0 && (
                <section className="bg-white border-l-4 border-bronze/70 p-6 rounded-sm shadow-sm">
                  <h3 className="font-garamond text-xl font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-bronze">🎨</span> Themes
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {recap.content.themes.map((theme, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-bronze/10 text-bronze border border-bronze/30 rounded-full font-sans text-sm"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Emotional Tone & Narrative Arc - Side by side */}
              <div className="grid md:grid-cols-2 gap-4">
                {recap.content.emotional_tone && (
                  <section className="bg-white border-l-4 border-bronze/70 p-6 rounded-sm shadow-sm">
                    <h3 className="font-garamond text-lg font-semibold text-midnight mb-3 flex items-center gap-2">
                      <span className="text-bronze">💭</span> Emotional Tone
                    </h3>
                    <p className="text-midnight font-sans text-sm italic">
                      {recap.content.emotional_tone}
                    </p>
                  </section>
                )}

                {recap.content.narrative_arc && (
                  <section className="bg-white border-l-4 border-bronze/70 p-6 rounded-sm shadow-sm">
                    <h3 className="font-garamond text-lg font-semibold text-midnight mb-3 flex items-center gap-2">
                      <span className="text-bronze">📈</span> Narrative Arc
                    </h3>
                    <p className="text-midnight font-sans text-sm italic">
                      {recap.content.narrative_arc}
                    </p>
                  </section>
                )}
              </div>

              {/* Memorable Moments */}
              {recap.content.memorable_moments && recap.content.memorable_moments.length > 0 && (
                <section className="bg-gradient-to-br from-bronze/5 to-bronze/10 border-l-4 border-bronze p-6 rounded-sm shadow-sm">
                  <h3 className="font-garamond text-xl font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-bronze">✨</span> Memorable Moments
                  </h3>
                  <div className="space-y-3">
                    {recap.content.memorable_moments.map((moment, index) => (
                      <blockquote key={index} className="border-l-4 border-bronze pl-4 py-2 italic text-midnight font-sans">
                        {moment}
                      </blockquote>
                    ))}
                  </div>
                </section>
              )}

              {/* Actions */}
              <div className="flex gap-3 justify-center flex-wrap pt-4 border-t-2 border-slate-ui/30">
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="px-6 py-3 bg-white border-2 border-bronze text-bronze rounded-sm font-semibold font-sans hover:bg-bronze hover:text-white disabled:opacity-50 transition-colors"
                >
                  {regenerating ? 'Regenerating...' : 'Regenerate Recap'}
                </button>
                <button
                  onClick={() => setShowSharePanel(!showSharePanel)}
                  className="px-6 py-3 bg-white border-2 border-bronze text-bronze rounded-sm font-semibold font-sans hover:bg-bronze hover:text-white transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                  Share
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 transition-colors"
                >
                  Close
                </button>
              </div>

              {/* Share Panel */}
              {showSharePanel && (
                <div className="mt-6 p-6 bg-gradient-to-br from-bronze/5 to-bronze/10 border border-bronze/20 rounded-sm">
                  <h4 className="font-garamond text-xl font-semibold text-midnight mb-4 flex items-center gap-2">
                    <span className="text-bronze">🎨</span> Create Shareable Card
                  </h4>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Options */}
                    <div className="space-y-4">
                      {/* Template Selection */}
                      <div>
                        <label className="text-sm font-sans font-semibold text-midnight block mb-2">
                          Template Style
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          {chapterRecapCardGenerator.getTemplates().map((template) => (
                            <button
                              key={template.id}
                              onClick={() => setSelectedTemplate(template.id)}
                              className={`px-3 py-2 text-sm font-sans rounded-sm border transition-colors ${
                                selectedTemplate === template.id
                                  ? 'bg-bronze text-white border-bronze'
                                  : 'border-slate-ui hover:bg-white'
                              }`}
                              title={template.description}
                            >
                              {template.name}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Format Selection */}
                      <div>
                        <label className="text-sm font-sans font-semibold text-midnight block mb-2">
                          Format
                        </label>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setSelectedFormat('story')}
                            className={`px-4 py-2 text-sm font-sans rounded-sm border transition-colors ${
                              selectedFormat === 'story'
                                ? 'bg-bronze text-white border-bronze'
                                : 'border-slate-ui hover:bg-white'
                            }`}
                          >
                            Story (9:16)
                          </button>
                          <button
                            onClick={() => setSelectedFormat('post')}
                            className={`px-4 py-2 text-sm font-sans rounded-sm border transition-colors ${
                              selectedFormat === 'post'
                                ? 'bg-bronze text-white border-bronze'
                                : 'border-slate-ui hover:bg-white'
                            }`}
                          >
                            Post (1:1)
                          </button>
                        </div>
                      </div>

                      {/* Generate Button */}
                      <button
                        onClick={generateCardPreview}
                        disabled={generatingCard}
                        className="w-full px-4 py-3 bg-bronze text-white rounded-sm font-semibold font-sans hover:bg-bronze/90 disabled:opacity-50 transition-colors"
                      >
                        {generatingCard ? 'Generating...' : 'Generate Preview'}
                      </button>
                    </div>

                    {/* Preview */}
                    <div className="flex flex-col items-center justify-center">
                      {cardPreview ? (
                        <div className="space-y-4">
                          <img
                            src={cardPreview}
                            alt="Card preview"
                            className="max-h-80 rounded-sm shadow-lg"
                          />

                          {/* Share Buttons */}
                          <div className="flex flex-wrap gap-2 justify-center">
                            <button
                              onClick={() => handleShare('twitter')}
                              className="px-4 py-2 bg-[#1DA1F2] text-white rounded-sm text-sm font-sans hover:bg-[#1a8cd8] transition-colors"
                            >
                              Twitter/X
                            </button>
                            <button
                              onClick={() => handleShare('facebook')}
                              className="px-4 py-2 bg-[#4267B2] text-white rounded-sm text-sm font-sans hover:bg-[#365899] transition-colors"
                            >
                              Facebook
                            </button>
                            <button
                              onClick={() => handleShare('instagram')}
                              className="px-4 py-2 bg-gradient-to-r from-[#f09433] via-[#e6683c] to-[#bc1888] text-white rounded-sm text-sm font-sans hover:opacity-90 transition-opacity"
                            >
                              Instagram
                            </button>
                            <button
                              onClick={() => handleShare('copy')}
                              className="px-4 py-2 bg-midnight text-white rounded-sm text-sm font-sans hover:bg-midnight/90 transition-colors"
                            >
                              Copy
                            </button>
                            <button
                              onClick={() => handleShare('download')}
                              className="px-4 py-2 bg-bronze text-white rounded-sm text-sm font-sans hover:bg-bronze/90 transition-colors"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-faded-ink font-sans text-sm p-8">
                          <div className="text-4xl mb-3">🖼️</div>
                          <p>Select a template and click "Generate Preview"</p>
                          <p className="text-xs mt-2 opacity-70">
                            Creates a beautiful shareable image of your chapter recap
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
