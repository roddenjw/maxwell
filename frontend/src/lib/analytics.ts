/**
 * PostHog Analytics Integration
 * Tracks key user actions and product usage
 */

import posthog from 'posthog-js';

// Initialize PostHog
export const initAnalytics = () => {
  const posthogKey = import.meta.env.VITE_POSTHOG_KEY;
  const posthogHost = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com';

  if (posthogKey) {
    posthog.init(posthogKey, {
      api_host: posthogHost,
      autocapture: false, // We'll manually track important events
      capture_pageview: true,
      capture_pageleave: true,
      loaded: () => {
        if (import.meta.env.DEV) {
          console.log('📊 PostHog analytics initialized');
        }
      },
    });
  } else if (import.meta.env.DEV) {
    console.warn('⚠️  PostHog not configured. Set VITE_POSTHOG_KEY to enable analytics.');
  }
};

// Track events
export const analytics = {
  // Manuscript events
  manuscriptCreated: (manuscriptId: string, title: string) => {
    posthog.capture('manuscript_created', {
      manuscript_id: manuscriptId,
      title,
    });
  },

  manuscriptOpened: (manuscriptId: string, title: string) => {
    posthog.capture('manuscript_opened', {
      manuscript_id: manuscriptId,
      title,
    });
  },

  manuscriptDeleted: (manuscriptId: string) => {
    posthog.capture('manuscript_deleted', {
      manuscript_id: manuscriptId,
    });
  },

  // Chapter events
  chapterCreated: (chapterId: string, manuscriptId: string, isFolder: boolean) => {
    posthog.capture('chapter_created', {
      chapter_id: chapterId,
      manuscript_id: manuscriptId,
      is_folder: isFolder,
    });
  },

  chapterDeleted: (chapterId: string, manuscriptId: string) => {
    posthog.capture('chapter_deleted', {
      chapter_id: chapterId,
      manuscript_id: manuscriptId,
    });
  },

  // Writing events
  wordsWritten: (manuscriptId: string, chapterId: string, wordCount: number, sessionDuration: number) => {
    posthog.capture('words_written', {
      manuscript_id: manuscriptId,
      chapter_id: chapterId,
      word_count: wordCount,
      session_duration_seconds: sessionDuration,
    });
  },

  // Feature usage
  codexOpened: (manuscriptId: string) => {
    posthog.capture('codex_opened', {
      manuscript_id: manuscriptId,
    });
  },

  timelineOpened: (manuscriptId: string) => {
    posthog.capture('timeline_opened', {
      manuscript_id: manuscriptId,
    });
  },

  analyticsOpened: (manuscriptId: string) => {
    posthog.capture('analytics_opened', {
      manuscript_id: manuscriptId,
    });
  },

  fastCoachOpened: (manuscriptId: string) => {
    posthog.capture('fast_coach_opened', {
      manuscript_id: manuscriptId,
    });
  },

  recapOpened: (manuscriptId: string) => {
    posthog.capture('recap_opened', {
      manuscript_id: manuscriptId,
    });
  },

  timeMachineOpened: (manuscriptId: string) => {
    posthog.capture('time_machine_opened', {
      manuscript_id: manuscriptId,
    });
  },

  // Export events
  exportStarted: (manuscriptId: string, format: 'docx' | 'pdf' | 'png') => {
    posthog.capture('export_started', {
      manuscript_id: manuscriptId,
      format,
    });
  },

  exportCompleted: (manuscriptId: string, format: 'docx' | 'pdf' | 'png', wordCount: number) => {
    posthog.capture('export_completed', {
      manuscript_id: manuscriptId,
      format,
      word_count: wordCount,
    });
  },

  // Entity events
  entityAnalyzed: (manuscriptId: string, entityType: string) => {
    posthog.capture('entity_analyzed', {
      manuscript_id: manuscriptId,
      entity_type: entityType,
    });
  },

  entityApproved: (manuscriptId: string, entityType: string) => {
    posthog.capture('entity_approved', {
      manuscript_id: manuscriptId,
      entity_type: entityType,
    });
  },

  // Onboarding events
  onboardingStarted: () => {
    posthog.capture('onboarding_started');
  },

  onboardingCompleted: (createdSample: boolean) => {
    posthog.capture('onboarding_completed', {
      created_sample: createdSample,
    });
  },

  onboardingSkipped: () => {
    posthog.capture('onboarding_skipped');
  },

  tourCompleted: () => {
    posthog.capture('tour_completed');
  },

  tourSkipped: () => {
    posthog.capture('tour_skipped');
  },

  // Snapshot events
  snapshotCreated: (manuscriptId: string) => {
    posthog.capture('snapshot_created', {
      manuscript_id: manuscriptId,
    });
  },

  snapshotRestored: (manuscriptId: string, snapshotId: string) => {
    posthog.capture('snapshot_restored', {
      manuscript_id: manuscriptId,
      snapshot_id: snapshotId,
    });
  },

  // Session tracking
  sessionStarted: () => {
    posthog.capture('session_started');
  },

  sessionEnded: (durationSeconds: number) => {
    posthog.capture('session_ended', {
      duration_seconds: durationSeconds,
    });
  },
};

// Identify user (call this when you add user authentication)
export const identifyUser = (userId: string, traits?: Record<string, any>) => {
  posthog.identify(userId, traits);
};

// Reset user (call on logout)
export const resetUser = () => {
  posthog.reset();
};

export default analytics;
