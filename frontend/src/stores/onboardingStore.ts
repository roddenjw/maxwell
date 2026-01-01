/**
 * Onboarding Store
 * Manages onboarding state and progress
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingState {
  hasCompletedWelcome: boolean;
  hasCompletedTour: boolean;
  hasCreatedFirstManuscript: boolean;
  lastShownDate: string | null;

  // Actions
  markWelcomeComplete: () => void;
  markTourComplete: () => void;
  markFirstManuscriptCreated: () => void;
  resetOnboarding: () => void;
  shouldShowOnboarding: () => boolean;
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      hasCompletedWelcome: false,
      hasCompletedTour: false,
      hasCreatedFirstManuscript: false,
      lastShownDate: null,

      markWelcomeComplete: () => {
        set({
          hasCompletedWelcome: true,
          lastShownDate: new Date().toISOString()
        });
      },

      markTourComplete: () => {
        set({
          hasCompletedTour: true,
          lastShownDate: new Date().toISOString()
        });
      },

      markFirstManuscriptCreated: () => {
        set({ hasCreatedFirstManuscript: true });
      },

      resetOnboarding: () => {
        set({
          hasCompletedWelcome: false,
          hasCompletedTour: false,
          hasCreatedFirstManuscript: false,
          lastShownDate: null
        });
      },

      shouldShowOnboarding: () => {
        const state = get();
        return !state.hasCompletedWelcome && !state.hasCreatedFirstManuscript;
      },
    }),
    {
      name: 'maxwell-onboarding-storage',
    }
  )
);
