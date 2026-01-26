/**
 * Vitest Setup File
 * Configures testing environment with mocks and global utilities
 */

import '@testing-library/jest-dom';
import { vi, beforeEach, afterEach } from 'vitest';

// ========================================
// Mock localStorage
// ========================================

const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// ========================================
// Mock fetch
// ========================================

global.fetch = vi.fn();

// ========================================
// Mock ResizeObserver
// ========================================

global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// ========================================
// Mock IntersectionObserver
// ========================================

global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
}));

// ========================================
// Mock window.matchMedia
// ========================================

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// ========================================
// Mock scrollIntoView
// ========================================

Element.prototype.scrollIntoView = vi.fn();

// ========================================
// API Mock Helpers
// ========================================

/**
 * Create a mock API response
 */
export function createMockResponse<T>(data: T, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
    redirected: false,
    statusText: ok ? 'OK' : 'Error',
    type: 'basic' as ResponseType,
    url: '',
    clone: vi.fn(),
    body: null,
    bodyUsed: false,
    arrayBuffer: vi.fn(),
    blob: vi.fn(),
    formData: vi.fn(),
  } as Response;
}

/**
 * Setup fetch mock to return specified data
 */
export function mockFetch(data: unknown, ok = true, status = 200) {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
    createMockResponse(data, ok, status)
  );
}

/**
 * Setup fetch mock to reject with an error
 */
export function mockFetchError(error: Error) {
  (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);
}

// ========================================
// Zustand Store Reset Helper
// ========================================

/**
 * Reset all Zustand stores between tests
 * Use this in beforeEach to ensure clean state
 */
export function resetStores() {
  // Import stores dynamically to avoid circular dependencies
  // Each store should have a reset method or initial state
}

// ========================================
// Test Data Factories
// ========================================

/**
 * Create mock manuscript data
 */
export function createMockManuscript(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-manuscript-id',
    title: 'Test Manuscript',
    word_count: 1000,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock chapter data
 */
export function createMockChapter(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-chapter-id',
    manuscript_id: 'test-manuscript-id',
    title: 'Test Chapter',
    is_folder: false,
    order_index: 0,
    content: 'Test chapter content.',
    word_count: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock coach session data
 */
export function createMockCoachSession(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-session-id',
    title: 'Test Coach Session',
    manuscript_id: 'test-manuscript-id',
    message_count: 0,
    total_cost: 0,
    total_tokens: 0,
    status: 'active' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock coach message data
 */
export function createMockCoachMessage(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-message-id',
    role: 'user' as const,
    content: 'Test message content',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock agent analysis result
 */
export function createMockAnalysisResult(overrides: Record<string, unknown> = {}) {
  return {
    recommendations: [],
    issues: [],
    teaching_points: [],
    praise: [],
    agent_results: {},
    total_cost: 0.001,
    total_tokens: 150,
    execution_time_ms: 1500,
    ...overrides,
  };
}

/**
 * Create mock codex entity data
 */
export function createMockEntity(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-entity-id',
    manuscript_id: 'test-manuscript-id',
    name: 'Test Character',
    type: 'character',
    description: 'A test character for testing purposes.',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock timeline event data
 */
export function createMockTimelineEvent(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-event-id',
    manuscript_id: 'test-manuscript-id',
    title: 'Test Event',
    description: 'A test timeline event.',
    event_type: 'story',
    position: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock outline beat data
 */
export function createMockOutlineBeat(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test-beat-id',
    manuscript_id: 'test-manuscript-id',
    title: 'Test Beat',
    description: 'A test outline beat.',
    beat_type: 'scene',
    act_number: 1,
    position: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

// ========================================
// Cleanup
// ========================================

beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.getItem.mockReset();
  localStorageMock.setItem.mockReset();
  localStorageMock.removeItem.mockReset();
  localStorageMock.clear.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});
