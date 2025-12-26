/**
 * useUnsavedChanges - Hook to track and warn about unsaved changes
 * Prevents accidental data loss when navigating away
 */

import { useEffect, useRef } from 'react';

export function useUnsavedChanges(hasUnsavedChanges: boolean) {
  const hasChangesRef = useRef(hasUnsavedChanges);

  useEffect(() => {
    hasChangesRef.current = hasUnsavedChanges;
  }, [hasUnsavedChanges]);

  useEffect(() => {
    // Warn before closing browser tab/window
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChangesRef.current) {
        // Modern browsers ignore custom messages, but still show a generic warning
        e.preventDefault();
        e.returnValue = ''; // Chrome requires returnValue to be set
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  /**
   * Check if navigation should be allowed
   * Returns true if safe to navigate, false if user cancels
   */
  const checkNavigateAway = (): boolean => {
    if (!hasChangesRef.current) {
      return true;
    }

    return confirm(
      'You have unsaved changes. Are you sure you want to leave? Your changes will be lost.'
    );
  };

  return { checkNavigateAway, hasUnsavedChanges };
}
