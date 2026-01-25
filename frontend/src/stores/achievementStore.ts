/**
 * Achievement Store - Tracks user achievements and gamification
 */

import { create } from 'zustand';
import { toast } from './toastStore';

export type AchievementCategory =
  | 'getting_started'
  | 'writing'
  | 'consistency'
  | 'codex'
  | 'timeline'
  | 'outline'
  | 'ai'
  | 'social'
  | 'world'
  | 'other';

export interface AchievementInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  points: number;
  category: AchievementCategory;
}

export interface EarnedAchievement extends AchievementInfo {
  earnedAt: string;
  manuscriptId?: string;
}

// Achievement definitions
export const ACHIEVEMENTS: Record<string, AchievementInfo> = {
  FIRST_MANUSCRIPT: {
    id: 'FIRST_MANUSCRIPT',
    name: 'The Journey Begins',
    description: 'Created your first manuscript',
    icon: '📝',
    points: 10,
    category: 'getting_started',
  },
  FIRST_CHAPTER: {
    id: 'FIRST_CHAPTER',
    name: 'Chapter One',
    description: 'Created your first chapter',
    icon: '📖',
    points: 10,
    category: 'getting_started',
  },
  FIRST_ENTITY: {
    id: 'FIRST_ENTITY',
    name: 'Character Creator',
    description: 'Added your first entity to the Codex',
    icon: '👤',
    points: 15,
    category: 'codex',
  },
  FIRST_TIMELINE_EVENT: {
    id: 'FIRST_TIMELINE_EVENT',
    name: 'Time Keeper',
    description: 'Created your first timeline event',
    icon: '📅',
    points: 15,
    category: 'timeline',
  },
  FIRST_OUTLINE: {
    id: 'FIRST_OUTLINE',
    name: 'Story Architect',
    description: 'Created your first outline',
    icon: '🏗️',
    points: 20,
    category: 'outline',
  },
  WORD_MILESTONE_1K: {
    id: 'WORD_MILESTONE_1K',
    name: 'First Thousand',
    description: 'Wrote 1,000 words',
    icon: '✍️',
    points: 25,
    category: 'writing',
  },
  WORD_MILESTONE_5K: {
    id: 'WORD_MILESTONE_5K',
    name: 'Five Thousand Strong',
    description: 'Wrote 5,000 words',
    icon: '📚',
    points: 50,
    category: 'writing',
  },
  WORD_MILESTONE_10K: {
    id: 'WORD_MILESTONE_10K',
    name: 'Ten K Club',
    description: 'Wrote 10,000 words',
    icon: '🏆',
    points: 100,
    category: 'writing',
  },
  WORD_MILESTONE_25K: {
    id: 'WORD_MILESTONE_25K',
    name: 'Quarter Century',
    description: 'Wrote 25,000 words',
    icon: '⭐',
    points: 200,
    category: 'writing',
  },
  WORD_MILESTONE_50K: {
    id: 'WORD_MILESTONE_50K',
    name: 'NaNoWriMo Champion',
    description: 'Wrote 50,000 words',
    icon: '👑',
    points: 500,
    category: 'writing',
  },
  STREAK_3_DAYS: {
    id: 'STREAK_3_DAYS',
    name: 'Getting Started',
    description: 'Wrote for 3 days in a row',
    icon: '🔥',
    points: 30,
    category: 'consistency',
  },
  STREAK_7_DAYS: {
    id: 'STREAK_7_DAYS',
    name: 'Week Warrior',
    description: 'Wrote for 7 days in a row',
    icon: '🔥',
    points: 75,
    category: 'consistency',
  },
  STREAK_14_DAYS: {
    id: 'STREAK_14_DAYS',
    name: 'Two Week Titan',
    description: 'Wrote for 14 days in a row',
    icon: '💪',
    points: 150,
    category: 'consistency',
  },
  STREAK_30_DAYS: {
    id: 'STREAK_30_DAYS',
    name: 'Monthly Master',
    description: 'Wrote for 30 days in a row',
    icon: '🌟',
    points: 300,
    category: 'consistency',
  },
  FIRST_AI_USE: {
    id: 'FIRST_AI_USE',
    name: 'AI Enabled',
    description: 'Used your first AI feature',
    icon: '🤖',
    points: 15,
    category: 'ai',
  },
  FIRST_RECAP: {
    id: 'FIRST_RECAP',
    name: 'Story Recap',
    description: 'Generated your first chapter recap',
    icon: '📋',
    points: 20,
    category: 'ai',
  },
  FIRST_BRAINSTORM: {
    id: 'FIRST_BRAINSTORM',
    name: 'Idea Generator',
    description: 'Completed your first brainstorm session',
    icon: '💡',
    points: 20,
    category: 'ai',
  },
  FIRST_SHARE: {
    id: 'FIRST_SHARE',
    name: 'Sharing is Caring',
    description: 'Shared your first recap card',
    icon: '🔗',
    points: 25,
    category: 'social',
  },
  FIRST_EXPORT: {
    id: 'FIRST_EXPORT',
    name: 'Ready to Publish',
    description: 'Exported your manuscript for the first time',
    icon: '📤',
    points: 25,
    category: 'social',
  },
  CODEX_10_ENTITIES: {
    id: 'CODEX_10_ENTITIES',
    name: 'World Builder',
    description: 'Created 10 entities in the Codex',
    icon: '🌍',
    points: 50,
    category: 'codex',
  },
  CODEX_50_ENTITIES: {
    id: 'CODEX_50_ENTITIES',
    name: 'Master Worldsmith',
    description: 'Created 50 entities in the Codex',
    icon: '🏰',
    points: 150,
    category: 'codex',
  },
  FIRST_RELATIONSHIP: {
    id: 'FIRST_RELATIONSHIP',
    name: 'Relationship Web',
    description: 'Created your first entity relationship',
    icon: '🕸️',
    points: 15,
    category: 'codex',
  },
  OUTLINE_COMPLETE: {
    id: 'OUTLINE_COMPLETE',
    name: 'Planned Perfection',
    description: 'Completed all beats in an outline',
    icon: '✅',
    points: 100,
    category: 'outline',
  },
  ALL_BEATS_WRITTEN: {
    id: 'ALL_BEATS_WRITTEN',
    name: 'Story Complete',
    description: 'Wrote content for all beats in an outline',
    icon: '🎉',
    points: 250,
    category: 'outline',
  },
  FIRST_WORLD: {
    id: 'FIRST_WORLD',
    name: 'World Creator',
    description: 'Created your first world',
    icon: '🌐',
    points: 25,
    category: 'world',
  },
  FIRST_SERIES: {
    id: 'FIRST_SERIES',
    name: 'Series Starter',
    description: 'Created your first series',
    icon: '📚',
    points: 30,
    category: 'world',
  },
};

interface AchievementProgress {
  totalWords: number;
  currentStreak: number;
  lastWritingDate: string | null;
  entityCount: number;
}

interface AchievementStore {
  // State
  earnedAchievements: EarnedAchievement[];
  progress: AchievementProgress;
  showDashboard: boolean;
  recentAchievement: EarnedAchievement | null;

  // Actions
  loadAchievements: () => void;
  earnAchievement: (achievementId: string, manuscriptId?: string) => void;
  checkWordMilestone: (totalWords: number) => void;
  checkStreak: () => void;
  checkEntityCount: (count: number) => void;
  updateProgress: (updates: Partial<AchievementProgress>) => void;
  setShowDashboard: (show: boolean) => void;
  clearRecentAchievement: () => void;
  getTotalPoints: () => number;
  getAchievementsByCategory: (category: AchievementCategory) => EarnedAchievement[];
  hasAchievement: (achievementId: string) => boolean;
}

export const useAchievementStore = create<AchievementStore>((set, get) => ({
  // Initial state
  earnedAchievements: [],
  progress: {
    totalWords: 0,
    currentStreak: 0,
    lastWritingDate: null,
    entityCount: 0,
  },
  showDashboard: false,
  recentAchievement: null,

  // Load achievements from localStorage
  loadAchievements: () => {
    try {
      const savedAchievements = localStorage.getItem('maxwell_achievements');
      const savedProgress = localStorage.getItem('maxwell_achievement_progress');

      if (savedAchievements) {
        set({ earnedAchievements: JSON.parse(savedAchievements) });
      }
      if (savedProgress) {
        set({ progress: { ...get().progress, ...JSON.parse(savedProgress) } });
      }
    } catch (e) {
      console.error('Failed to load achievements:', e);
    }
  },

  // Earn a new achievement
  earnAchievement: (achievementId: string, manuscriptId?: string) => {
    const { earnedAchievements } = get();

    // Check if already earned
    if (earnedAchievements.some(a => a.id === achievementId)) {
      return;
    }

    const achievementInfo = ACHIEVEMENTS[achievementId];
    if (!achievementInfo) {
      console.error('Unknown achievement:', achievementId);
      return;
    }

    const newAchievement: EarnedAchievement = {
      ...achievementInfo,
      earnedAt: new Date().toISOString(),
      manuscriptId,
    };

    const updated = [...earnedAchievements, newAchievement];
    set({
      earnedAchievements: updated,
      recentAchievement: newAchievement,
    });

    // Save to localStorage
    localStorage.setItem('maxwell_achievements', JSON.stringify(updated));

    // Show toast notification
    toast.success(
      `${achievementInfo.icon} Achievement Unlocked: ${achievementInfo.name}`,
      {
        duration: 8000,
        action: {
          label: 'View All',
          onClick: () => set({ showDashboard: true }),
        },
      }
    );
  },

  // Check and award word milestones
  checkWordMilestone: (totalWords: number) => {
    const { earnAchievement, hasAchievement, progress } = get();

    // Update progress
    set({ progress: { ...progress, totalWords } });
    localStorage.setItem('maxwell_achievement_progress', JSON.stringify({ ...progress, totalWords }));

    // Check milestones
    if (totalWords >= 1000 && !hasAchievement('WORD_MILESTONE_1K')) {
      earnAchievement('WORD_MILESTONE_1K');
    }
    if (totalWords >= 5000 && !hasAchievement('WORD_MILESTONE_5K')) {
      earnAchievement('WORD_MILESTONE_5K');
    }
    if (totalWords >= 10000 && !hasAchievement('WORD_MILESTONE_10K')) {
      earnAchievement('WORD_MILESTONE_10K');
    }
    if (totalWords >= 25000 && !hasAchievement('WORD_MILESTONE_25K')) {
      earnAchievement('WORD_MILESTONE_25K');
    }
    if (totalWords >= 50000 && !hasAchievement('WORD_MILESTONE_50K')) {
      earnAchievement('WORD_MILESTONE_50K');
    }
  },

  // Check and update writing streak
  checkStreak: () => {
    const { earnAchievement, hasAchievement, progress } = get();
    const today = new Date().toDateString();
    const lastDate = progress.lastWritingDate;

    let newStreak = progress.currentStreak;

    if (!lastDate) {
      // First writing day
      newStreak = 1;
    } else {
      const lastWriting = new Date(lastDate);
      const daysSince = Math.floor(
        (new Date().getTime() - lastWriting.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysSince === 0) {
        // Same day, no change
        return;
      } else if (daysSince === 1) {
        // Consecutive day
        newStreak = progress.currentStreak + 1;
      } else {
        // Streak broken
        newStreak = 1;
      }
    }

    // Update progress
    const newProgress = {
      ...progress,
      currentStreak: newStreak,
      lastWritingDate: today,
    };
    set({ progress: newProgress });
    localStorage.setItem('maxwell_achievement_progress', JSON.stringify(newProgress));

    // Check streak achievements
    if (newStreak >= 3 && !hasAchievement('STREAK_3_DAYS')) {
      earnAchievement('STREAK_3_DAYS');
    }
    if (newStreak >= 7 && !hasAchievement('STREAK_7_DAYS')) {
      earnAchievement('STREAK_7_DAYS');
    }
    if (newStreak >= 14 && !hasAchievement('STREAK_14_DAYS')) {
      earnAchievement('STREAK_14_DAYS');
    }
    if (newStreak >= 30 && !hasAchievement('STREAK_30_DAYS')) {
      earnAchievement('STREAK_30_DAYS');
    }
  },

  // Check entity count achievements
  checkEntityCount: (count: number) => {
    const { earnAchievement, hasAchievement, progress } = get();

    // Update progress
    set({ progress: { ...progress, entityCount: count } });

    if (count >= 1 && !hasAchievement('FIRST_ENTITY')) {
      earnAchievement('FIRST_ENTITY');
    }
    if (count >= 10 && !hasAchievement('CODEX_10_ENTITIES')) {
      earnAchievement('CODEX_10_ENTITIES');
    }
    if (count >= 50 && !hasAchievement('CODEX_50_ENTITIES')) {
      earnAchievement('CODEX_50_ENTITIES');
    }
  },

  // Update progress manually
  updateProgress: (updates: Partial<AchievementProgress>) => {
    const { progress } = get();
    const newProgress = { ...progress, ...updates };
    set({ progress: newProgress });
    localStorage.setItem('maxwell_achievement_progress', JSON.stringify(newProgress));
  },

  setShowDashboard: (show: boolean) => set({ showDashboard: show }),

  clearRecentAchievement: () => set({ recentAchievement: null }),

  getTotalPoints: () => {
    const { earnedAchievements } = get();
    return earnedAchievements.reduce((sum, a) => sum + a.points, 0);
  },

  getAchievementsByCategory: (category: AchievementCategory) => {
    const { earnedAchievements } = get();
    return earnedAchievements.filter(a => a.category === category);
  },

  hasAchievement: (achievementId: string) => {
    const { earnedAchievements } = get();
    return earnedAchievements.some(a => a.id === achievementId);
  },
}));
