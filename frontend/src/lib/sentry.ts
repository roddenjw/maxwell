/**
 * Sentry Error Tracking Integration
 * Captures and reports errors for debugging
 */

import * as Sentry from '@sentry/react';

export const initSentry = () => {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  const environment = import.meta.env.MODE || 'development';

  if (sentryDsn) {
    Sentry.init({
      dsn: sentryDsn,
      environment,
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      // Performance Monitoring
      tracesSampleRate: environment === 'production' ? 0.1 : 1.0, // 10% in prod, 100% in dev
      // Session Replay
      replaysSessionSampleRate: 0.1, // Sample 10% of sessions
      replaysOnErrorSampleRate: 1.0, // Capture 100% of sessions with errors
      // Don't send errors in development
      enabled: environment === 'production' || import.meta.env.VITE_SENTRY_ENABLED === 'true',
      beforeSend(event, hint) {
        // Filter out errors we don't care about
        const error = hint.originalException;

        // Ignore ResizeObserver errors (common, harmless)
        if (error && typeof error === 'object' && 'message' in error) {
          const message = String(error.message);
          if (message.includes('ResizeObserver')) {
            return null;
          }
        }

        return event;
      },
    });

    if (import.meta.env.DEV) {
      console.log('🐛 Sentry error tracking initialized');
    }
  } else if (import.meta.env.DEV) {
    console.warn('⚠️  Sentry not configured. Set VITE_SENTRY_DSN to enable error tracking.');
  }
};

// Manually capture exceptions
export const captureException = (error: Error, context?: Record<string, any>) => {
  Sentry.captureException(error, {
    extra: context,
  });
};

// Capture custom messages
export const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info') => {
  Sentry.captureMessage(message, level);
};

// Add breadcrumb for debugging
export const addBreadcrumb = (category: string, message: string, data?: Record<string, any>) => {
  Sentry.addBreadcrumb({
    category,
    message,
    data,
    level: 'info',
  });
};

// Set user context (when you add authentication)
export const setUserContext = (userId: string, email?: string, username?: string) => {
  Sentry.setUser({
    id: userId,
    email,
    username,
  });
};

// Clear user context (on logout)
export const clearUserContext = () => {
  Sentry.setUser(null);
};

// Create error boundary component
export const ErrorBoundary = Sentry.ErrorBoundary;

export default Sentry;
