/**
 * Views Index
 * Re-exports lazy-loaded view components for better code splitting
 */

import { lazy } from 'react';

// Lazy-loaded components for views that aren't immediately needed
// Using inline import for components with named exports
export const LazyAnalyticsDashboard = lazy(() => import('@/components/Analytics/AnalyticsDashboard'));
export const LazyTimeMachine = lazy(() =>
  import('@/components/TimeMachine').then(module => ({ default: module.TimeMachine }))
);
export const LazyExportModal = lazy(() => import('@/components/Export/ExportModal'));
export const LazyRecapModal = lazy(() => import('@/components/RecapModal'));
export const LazyManuscriptWizard = lazy(() => import('@/components/Outline/ManuscriptWizard'));
export const LazyWelcomeModal = lazy(() => import('@/components/Onboarding/WelcomeModal'));
export const LazyFeatureTour = lazy(() => import('@/components/Onboarding/FeatureTour'));
export const LazySettingsModal = lazy(() => import('@/components/Settings/SettingsModal'));
export const LazyCodexMainView = lazy(() => import('@/components/Codex/CodexMainView'));
export const LazyMaxwellPanel = lazy(() =>
  import('@/components/Maxwell/MaxwellPanel').then(m => ({ default: m.MaxwellPanel }))
);
export const LazyOutlineMainView = lazy(() => import('@/components/Outline/OutlineMainView'));
export const LazyBrainstormingModal = lazy(() => import('@/components/Brainstorming/BrainstormingModal'));
