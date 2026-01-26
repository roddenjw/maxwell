/**
 * Tests for Manuscript Store
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import { useManuscriptStore } from './manuscriptStore';

// Mock the API
vi.mock('../lib/api', () => ({
  manuscriptApi: {
    list: vi.fn(),
  },
}));

// Mock fetch for createManuscript
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ManuscriptStore', () => {
  beforeEach(() => {
    // Reset store state
    const store = useManuscriptStore.getState();
    act(() => {
      store.manuscripts.forEach((ms) => store.deleteManuscript(ms.id));
    });
    useManuscriptStore.setState({
      manuscripts: [],
      currentManuscriptId: null,
      isLoading: false,
      error: null,
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have empty manuscripts array', () => {
      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toEqual([]);
    });

    it('should have null currentManuscriptId', () => {
      const { currentManuscriptId } = useManuscriptStore.getState();
      expect(currentManuscriptId).toBeNull();
    });

    it('should have isLoading as false', () => {
      const { isLoading } = useManuscriptStore.getState();
      expect(isLoading).toBe(false);
    });

    it('should have error as null', () => {
      const { error } = useManuscriptStore.getState();
      expect(error).toBeNull();
    });
  });

  describe('addManuscript', () => {
    it('should add a new manuscript', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test Manuscript',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(1);
      expect(manuscripts[0]).toEqual(manuscript);
    });

    it('should update existing manuscript if id matches', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Original Title',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
      });

      const updatedManuscript = {
        ...manuscript,
        title: 'Updated Title',
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(updatedManuscript);
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(1);
      expect(manuscripts[0].title).toBe('Updated Title');
    });
  });

  describe('updateManuscript', () => {
    it('should update manuscript fields', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
        useManuscriptStore.getState().updateManuscript('test-id-1', {
          title: 'New Title',
          wordCount: 500,
        });
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts[0].title).toBe('New Title');
      expect(manuscripts[0].wordCount).toBe(500);
    });

    it('should update the updatedAt timestamp', () => {
      const originalDate = '2024-01-01T00:00:00.000Z';
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: originalDate,
        updatedAt: originalDate,
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
        useManuscriptStore.getState().updateManuscript('test-id-1', {
          title: 'Updated',
        });
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts[0].updatedAt).not.toBe(originalDate);
    });

    it('should not update non-existent manuscript', () => {
      act(() => {
        useManuscriptStore.getState().updateManuscript('non-existent', {
          title: 'New Title',
        });
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(0);
    });
  });

  describe('deleteManuscript', () => {
    it('should remove manuscript from list', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
        useManuscriptStore.getState().deleteManuscript('test-id-1');
      });

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(0);
    });

    it('should clear currentManuscriptId if deleted manuscript was current', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
        useManuscriptStore.getState().setCurrentManuscript('test-id-1');
        useManuscriptStore.getState().deleteManuscript('test-id-1');
      });

      const { currentManuscriptId } = useManuscriptStore.getState();
      expect(currentManuscriptId).toBeNull();
    });

    it('should not affect currentManuscriptId if different manuscript deleted', () => {
      const ms1 = {
        id: 'test-id-1',
        title: 'Test 1',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      const ms2 = {
        id: 'test-id-2',
        title: 'Test 2',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(ms1);
        useManuscriptStore.getState().addManuscript(ms2);
        useManuscriptStore.getState().setCurrentManuscript('test-id-1');
        useManuscriptStore.getState().deleteManuscript('test-id-2');
      });

      const { currentManuscriptId, manuscripts } = useManuscriptStore.getState();
      expect(currentManuscriptId).toBe('test-id-1');
      expect(manuscripts).toHaveLength(1);
    });
  });

  describe('getManuscript', () => {
    it('should return manuscript by id', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
      });

      const result = useManuscriptStore.getState().getManuscript('test-id-1');
      expect(result).toEqual(manuscript);
    });

    it('should return undefined for non-existent manuscript', () => {
      const result = useManuscriptStore.getState().getManuscript('non-existent');
      expect(result).toBeUndefined();
    });
  });

  describe('setCurrentManuscript', () => {
    it('should set currentManuscriptId', () => {
      act(() => {
        useManuscriptStore.getState().setCurrentManuscript('test-id-1');
      });

      const { currentManuscriptId } = useManuscriptStore.getState();
      expect(currentManuscriptId).toBe('test-id-1');
    });

    it('should allow setting to null', () => {
      act(() => {
        useManuscriptStore.getState().setCurrentManuscript('test-id-1');
        useManuscriptStore.getState().setCurrentManuscript(null);
      });

      const { currentManuscriptId } = useManuscriptStore.getState();
      expect(currentManuscriptId).toBeNull();
    });
  });

  describe('getCurrentManuscript', () => {
    it('should return current manuscript', () => {
      const manuscript = {
        id: 'test-id-1',
        title: 'Test',
        content: '',
        wordCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      act(() => {
        useManuscriptStore.getState().addManuscript(manuscript);
        useManuscriptStore.getState().setCurrentManuscript('test-id-1');
      });

      const result = useManuscriptStore.getState().getCurrentManuscript();
      expect(result).toEqual(manuscript);
    });

    it('should return undefined if no current manuscript', () => {
      const result = useManuscriptStore.getState().getCurrentManuscript();
      expect(result).toBeUndefined();
    });

    it('should return undefined if currentManuscriptId does not match any manuscript', () => {
      act(() => {
        useManuscriptStore.getState().setCurrentManuscript('non-existent');
      });

      const result = useManuscriptStore.getState().getCurrentManuscript();
      expect(result).toBeUndefined();
    });
  });

  describe('fetchManuscripts', () => {
    it('should set loading state while fetching', async () => {
      const { manuscriptApi } = await import('../lib/api');
      (manuscriptApi.list as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve([]), 100))
      );

      const promise = useManuscriptStore.getState().fetchManuscripts();

      expect(useManuscriptStore.getState().isLoading).toBe(true);

      await promise;

      expect(useManuscriptStore.getState().isLoading).toBe(false);
    });

    it('should populate manuscripts from API', async () => {
      const { manuscriptApi } = await import('../lib/api');
      const mockData = [
        {
          id: 'ms-1',
          title: 'Manuscript 1',
          word_count: 1000,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
        {
          id: 'ms-2',
          title: 'Manuscript 2',
          word_count: 2000,
          created_at: '2024-02-01T00:00:00Z',
          updated_at: '2024-02-02T00:00:00Z',
        },
      ];

      (manuscriptApi.list as ReturnType<typeof vi.fn>).mockResolvedValue(mockData);

      await useManuscriptStore.getState().fetchManuscripts();

      const { manuscripts } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(2);
      expect(manuscripts[0].title).toBe('Manuscript 1');
      expect(manuscripts[0].wordCount).toBe(1000);
      expect(manuscripts[1].title).toBe('Manuscript 2');
    });

    it('should handle API errors', async () => {
      const { manuscriptApi } = await import('../lib/api');
      (manuscriptApi.list as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      await useManuscriptStore.getState().fetchManuscripts();

      const { error, isLoading } = useManuscriptStore.getState();
      expect(error).toBe('Network error');
      expect(isLoading).toBe(false);
    });
  });

  describe('createManuscript', () => {
    it('should create manuscript via API', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 'new-ms-id',
            title: 'New Manuscript',
            word_count: 0,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          }),
      });

      const result = await useManuscriptStore.getState().createManuscript('New Manuscript');

      expect(result.id).toBe('new-ms-id');
      expect(result.title).toBe('New Manuscript');

      const { manuscripts, currentManuscriptId } = useManuscriptStore.getState();
      expect(manuscripts).toHaveLength(1);
      expect(currentManuscriptId).toBe('new-ms-id');
    });

    it('should use default title if not provided', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 'new-ms-id',
            title: 'Untitled Manuscript',
            word_count: 0,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          }),
      });

      await useManuscriptStore.getState().createManuscript('');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/manuscripts',
        expect.objectContaining({
          body: JSON.stringify({ title: 'Untitled Manuscript' }),
        })
      );
    });

    it('should throw error on API failure', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      });

      await expect(
        useManuscriptStore.getState().createManuscript('Test')
      ).rejects.toThrow('Failed to create manuscript');
    });
  });
});
