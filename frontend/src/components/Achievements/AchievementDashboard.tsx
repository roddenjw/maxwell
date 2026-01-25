/**
 * AchievementDashboard - Displays all achievements and progress
 */

import { useAchievementStore, ACHIEVEMENTS, type AchievementCategory } from '@/stores/achievementStore';

interface AchievementDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

const CATEGORY_LABELS: Record<AchievementCategory, { name: string; icon: string }> = {
  getting_started: { name: 'Getting Started', icon: '🚀' },
  writing: { name: 'Writing Milestones', icon: '✍️' },
  consistency: { name: 'Consistency', icon: '🔥' },
  codex: { name: 'Codex', icon: '📚' },
  timeline: { name: 'Timeline', icon: '📅' },
  outline: { name: 'Outline', icon: '🏗️' },
  ai: { name: 'AI Features', icon: '🤖' },
  social: { name: 'Social', icon: '🔗' },
  world: { name: 'World Building', icon: '🌍' },
  other: { name: 'Other', icon: '🏅' },
};

const CATEGORIES: AchievementCategory[] = [
  'getting_started',
  'writing',
  'consistency',
  'codex',
  'outline',
  'ai',
  'social',
  'world',
];

export default function AchievementDashboard({ isOpen, onClose }: AchievementDashboardProps) {
  const { earnedAchievements, getTotalPoints, hasAchievement, progress } = useAchievementStore();

  if (!isOpen) return null;

  const totalPoints = getTotalPoints();
  const allAchievementIds = Object.keys(ACHIEVEMENTS);
  const earnedCount = earnedAchievements.length;
  const totalCount = allAchievementIds.length;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[300] p-4">
      <div className="bg-vellum rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-bronze/20 bg-gradient-to-r from-bronze/10 to-transparent">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-garamond font-bold text-midnight">
                Achievements
              </h2>
              <p className="text-sm font-sans text-faded-ink mt-1">
                {earnedCount} of {totalCount} unlocked
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-garamond font-bold text-bronze">
                {totalPoints}
              </div>
              <div className="text-xs font-sans text-faded-ink">
                points earned
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-faded-ink hover:text-midnight text-3xl leading-none ml-4"
            >
              ×
            </button>
          </div>

          {/* Progress stats */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-white/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-garamond font-bold text-midnight">
                {progress.totalWords.toLocaleString()}
              </div>
              <div className="text-xs font-sans text-faded-ink">Total Words</div>
            </div>
            <div className="bg-white/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-garamond font-bold text-midnight flex items-center justify-center gap-1">
                {progress.currentStreak}
                {progress.currentStreak > 0 && <span className="text-orange-500">🔥</span>}
              </div>
              <div className="text-xs font-sans text-faded-ink">Day Streak</div>
            </div>
            <div className="bg-white/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-garamond font-bold text-midnight">
                {progress.entityCount}
              </div>
              <div className="text-xs font-sans text-faded-ink">Entities Created</div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {CATEGORIES.map((category) => {
            const categoryInfo = CATEGORY_LABELS[category];
            const categoryAchievements = Object.entries(ACHIEVEMENTS)
              .filter(([_, a]) => a.category === category);

            if (categoryAchievements.length === 0) return null;

            const earnedInCategory = categoryAchievements.filter(([id]) => hasAchievement(id));

            return (
              <div key={category} className="mb-6">
                <h3 className="text-lg font-garamond font-semibold text-midnight mb-3 flex items-center gap-2">
                  <span>{categoryInfo.icon}</span>
                  {categoryInfo.name}
                  <span className="text-sm font-sans font-normal text-faded-ink ml-2">
                    ({earnedInCategory.length}/{categoryAchievements.length})
                  </span>
                </h3>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {categoryAchievements.map(([id, achievement]) => {
                    const isEarned = hasAchievement(id);
                    const earnedData = earnedAchievements.find(a => a.id === id);

                    return (
                      <div
                        key={id}
                        className={`p-4 rounded-lg border transition-all ${
                          isEarned
                            ? 'bg-white border-bronze/30 shadow-sm'
                            : 'bg-gray-100/50 border-gray-200 opacity-60'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`text-2xl ${isEarned ? '' : 'grayscale opacity-50'}`}>
                            {achievement.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className={`font-semibold text-sm ${isEarned ? 'text-midnight' : 'text-gray-500'}`}>
                              {achievement.name}
                            </div>
                            <div className="text-xs text-faded-ink mt-0.5">
                              {achievement.description}
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                              <span className={`text-xs font-semibold ${isEarned ? 'text-bronze' : 'text-gray-400'}`}>
                                +{achievement.points} pts
                              </span>
                              {isEarned && earnedData && (
                                <span className="text-xs text-faded-ink">
                                  {new Date(earnedData.earnedAt).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-bronze/20 bg-white/50">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-bronze text-white rounded-lg font-sans font-semibold hover:bg-bronze/90 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
