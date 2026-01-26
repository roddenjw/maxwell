/**
 * ProgressDashboard Component
 * Analytics view showing detailed outline completion metrics
 */

import type { Outline, PlotBeat } from '@/types/outline';

interface ProgressDashboardProps {
  outline: Outline;
}

export default function ProgressDashboard({ outline }: ProgressDashboardProps) {
  const beats = outline.plot_beats || [];
  const totalBeats = beats.length;
  const completedBeats = beats.filter((b) => b.is_completed).length;
  const inProgressBeats = beats.filter(
    (b) => !b.is_completed && (b.user_notes || b.chapter_id || b.actual_word_count > 0)
  ).length;
  const notStartedBeats = totalBeats - completedBeats - inProgressBeats;

  // Word count metrics
  const totalTargetWords = outline.target_word_count;
  const totalActualWords = beats.reduce((sum, b) => sum + b.actual_word_count, 0);
  const wordCountProgress = totalTargetWords > 0 ? (totalActualWords / totalTargetWords) * 100 : 0;

  // Act breakdown (assuming 3-act structure)
  const getActForBeat = (beat: PlotBeat): number => {
    if (beat.target_position_percent <= 0.25) return 1;
    if (beat.target_position_percent <= 0.75) return 2;
    return 3;
  };

  const actStats = [
    {
      act: 1,
      name: 'Act 1: Setup',
      range: '0-25%',
      beats: beats.filter((b) => getActForBeat(b) === 1),
    },
    {
      act: 2,
      name: 'Act 2: Confrontation',
      range: '25-75%',
      beats: beats.filter((b) => getActForBeat(b) === 2),
    },
    {
      act: 3,
      name: 'Act 3: Resolution',
      range: '75-100%',
      beats: beats.filter((b) => getActForBeat(b) === 3),
    },
  ];

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      {/* Header */}
      <div>
        <h3 className="font-serif text-2xl font-bold text-midnight mb-2">
          Progress Analytics
        </h3>
        <p className="font-sans text-sm text-faded-ink">
          Track your outline completion and writing progress
        </p>
      </div>

      {/* Overall Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 bg-bronze/5 border-2 border-bronze" style={{ borderRadius: '2px' }}>
          <div className="text-xs font-sans font-semibold text-faded-ink uppercase tracking-wider mb-1">
            Completion Rate
          </div>
          <div className="text-3xl font-serif font-bold text-bronze">
            {totalBeats > 0 ? Math.round((completedBeats / totalBeats) * 100) : 0}%
          </div>
          <div className="text-xs font-sans text-faded-ink mt-1">
            {completedBeats} of {totalBeats} beats
          </div>
        </div>

        <div className="p-4 bg-green-500/5 border-2 border-green-500" style={{ borderRadius: '2px' }}>
          <div className="text-xs font-sans font-semibold text-faded-ink uppercase tracking-wider mb-1">
            Word Count
          </div>
          <div className="text-3xl font-serif font-bold text-green-600">
            {Math.round(wordCountProgress)}%
          </div>
          <div className="text-xs font-sans text-faded-ink mt-1">
            {totalActualWords.toLocaleString()} / {totalTargetWords.toLocaleString()} words
          </div>
        </div>
      </div>

      {/* Word Count Progress Bar */}
      <div>
        <div className="flex items-center justify-between text-sm font-sans mb-2">
          <span className="font-semibold text-midnight">Overall Writing Progress</span>
          <span className="text-faded-ink">
            {totalActualWords.toLocaleString()} words written
          </span>
        </div>
        <div className="h-6 bg-slate-ui/30 overflow-hidden relative" style={{ borderRadius: '2px' }}>
          <div
            className="h-full bg-gradient-to-r from-bronze to-green-500 transition-all duration-500"
            style={{ width: `${Math.min(100, wordCountProgress)}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center text-xs font-sans font-bold text-midnight">
            {Math.round(wordCountProgress)}%
          </div>
        </div>
      </div>

      {/* Beat Status Breakdown */}
      <div>
        <h4 className="font-sans font-semibold text-midnight text-sm mb-3">
          Beat Status Distribution
        </h4>
        <div className="space-y-2">
          {/* Completed */}
          <div className="flex items-center gap-3">
            <div className="w-20 text-xs font-sans text-faded-ink">Completed</div>
            <div className="flex-1 h-4 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
              <div
                className="h-full bg-green-500"
                style={{ width: `${totalBeats > 0 ? (completedBeats / totalBeats) * 100 : 0}%` }}
              />
            </div>
            <div className="w-12 text-xs font-sans text-right font-semibold text-green-600">
              {completedBeats}
            </div>
          </div>

          {/* In Progress */}
          <div className="flex items-center gap-3">
            <div className="w-20 text-xs font-sans text-faded-ink">In Progress</div>
            <div className="flex-1 h-4 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
              <div
                className="h-full bg-bronze"
                style={{ width: `${totalBeats > 0 ? (inProgressBeats / totalBeats) * 100 : 0}%` }}
              />
            </div>
            <div className="w-12 text-xs font-sans text-right font-semibold text-bronze">
              {inProgressBeats}
            </div>
          </div>

          {/* Not Started */}
          <div className="flex items-center gap-3">
            <div className="w-20 text-xs font-sans text-faded-ink">Not Started</div>
            <div className="flex-1 h-4 bg-slate-ui/30 overflow-hidden" style={{ borderRadius: '2px' }}>
              <div
                className="h-full bg-slate-ui"
                style={{ width: `${totalBeats > 0 ? (notStartedBeats / totalBeats) * 100 : 0}%` }}
              />
            </div>
            <div className="w-12 text-xs font-sans text-right font-semibold text-faded-ink">
              {notStartedBeats}
            </div>
          </div>
        </div>
      </div>

      {/* Act Breakdown */}
      <div>
        <h4 className="font-sans font-semibold text-midnight text-sm mb-3">
          Story Structure Breakdown
        </h4>
        <div className="space-y-4">
          {actStats.map((act) => {
            const actCompleted = act.beats.filter((b) => b.is_completed).length;
            const actWordCount = act.beats.reduce((sum, b) => sum + b.actual_word_count, 0);
            const actTargetWords = act.beats.reduce((sum, b) => sum + b.target_word_count, 0);
            const actCompletionRate = act.beats.length > 0 ? (actCompleted / act.beats.length) * 100 : 0;

            return (
              <div
                key={act.act}
                className="p-4 bg-slate-ui/10 border-l-4 border-bronze"
                style={{ borderRadius: '2px' }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-sans font-bold text-midnight text-sm">
                      {act.name}
                    </div>
                    <div className="text-xs font-sans text-faded-ink">
                      {act.range} • {act.beats.length} beats
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-serif font-bold text-bronze">
                      {Math.round(actCompletionRate)}%
                    </div>
                    <div className="text-xs font-sans text-faded-ink">
                      {actCompleted}/{act.beats.length} done
                    </div>
                  </div>
                </div>

                {/* Act Progress Bar */}
                <div className="h-2 bg-white overflow-hidden mb-2" style={{ borderRadius: '2px' }}>
                  <div
                    className="h-full bg-bronze transition-all duration-300"
                    style={{ width: `${actCompletionRate}%` }}
                  />
                </div>

                {/* Word Count */}
                <div className="flex items-center justify-between text-xs font-sans text-faded-ink">
                  <span>Word Count:</span>
                  <span className="font-semibold text-midnight">
                    {actWordCount.toLocaleString()} / {actTargetWords.toLocaleString()} words
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Insights */}
      <div>
        <h4 className="font-sans font-semibold text-midnight text-sm mb-3">
          Quick Insights
        </h4>
        <div className="space-y-2">
          {completedBeats === totalBeats && (
            <div className="p-3 bg-green-500/10 border-l-4 border-green-500" style={{ borderRadius: '2px' }}>
              <div className="flex items-center gap-2">
                <span className="text-lg">🎉</span>
                <span className="text-sm font-sans text-green-700">
                  All beats completed! Ready for final review.
                </span>
              </div>
            </div>
          )}

          {inProgressBeats > 0 && completedBeats < totalBeats && (
            <div className="p-3 bg-bronze/10 border-l-4 border-bronze" style={{ borderRadius: '2px' }}>
              <div className="flex items-center gap-2">
                <span className="text-lg">✍️</span>
                <span className="text-sm font-sans text-bronze-dark">
                  {inProgressBeats} beat{inProgressBeats !== 1 ? 's' : ''} in progress. Keep writing!
                </span>
              </div>
            </div>
          )}

          {notStartedBeats > 0 && (
            <div className="p-3 bg-slate-ui/20 border-l-4 border-slate-ui" style={{ borderRadius: '2px' }}>
              <div className="flex items-center gap-2">
                <span className="text-lg">📝</span>
                <span className="text-sm font-sans text-faded-ink">
                  {notStartedBeats} beat{notStartedBeats !== 1 ? 's' : ''} waiting to be started.
                </span>
              </div>
            </div>
          )}

          {wordCountProgress >= 100 && (
            <div className="p-3 bg-green-500/10 border-l-4 border-green-500" style={{ borderRadius: '2px' }}>
              <div className="flex items-center gap-2">
                <span className="text-lg">🎯</span>
                <span className="text-sm font-sans text-green-700">
                  Target word count reached! Great work!
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
