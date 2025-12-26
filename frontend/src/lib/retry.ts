/**
 * Retry utility - Handles retrying failed API calls with exponential backoff
 */

export interface RetryOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  shouldRetry?: (error: any) => boolean;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  shouldRetry: (error) => {
    // Retry on network errors or 5xx server errors
    if (error?.message?.includes('fetch') || error?.message?.includes('network')) {
      return true;
    }
    if (error?.response?.status >= 500) {
      return true;
    }
    return false;
  },
};

/**
 * Retry a function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: any;
  let delay = opts.initialDelay;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if we shouldn't or if this was the last attempt
      if (!opts.shouldRetry(error) || attempt === opts.maxAttempts) {
        throw error;
      }

      // Wait before retrying with exponential backoff
      await sleep(Math.min(delay, opts.maxDelay));
      delay *= opts.backoffMultiplier;
    }
  }

  throw lastError;
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Get a user-friendly error message
 */
export function getErrorMessage(error: any): string {
  // Network errors
  if (error?.message?.includes('fetch') || error?.message?.includes('Failed to fetch')) {
    return 'Network error. Please check your connection and try again.';
  }

  // API errors with message
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }

  // API errors with detail
  if (error?.response?.data?.detail) {
    return typeof error.response.data.detail === 'string'
      ? error.response.data.detail
      : 'An error occurred. Please try again.';
  }

  // HTTP status errors
  if (error?.response?.status) {
    switch (error.response.status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'A conflict occurred. Please refresh and try again.';
      case 422:
        return 'Validation error. Please check your input.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return `An error occurred (${error.response.status}). Please try again.`;
    }
  }

  // Generic error message
  if (error?.message) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}
