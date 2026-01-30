/**
 * Manuscript Store - Zustand
 * Manages manuscript state with localStorage persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { manuscriptApi } from '../lib/api';

export interface Manuscript {
  id: string;
  title: string;
  content: string; // JSON stringified Lexical editor state
  wordCount: number;
  // Story metadata for AI context
  premise?: string;          // Story premise/logline
  premiseSource?: string;    // 'ai_generated' or 'user_written'
  genre?: string;            // e.g., 'Fantasy', 'Mystery', 'Romance'
  createdAt: string;
  updatedAt: string;
}

interface ManuscriptStore {
  manuscripts: Manuscript[];
  currentManuscriptId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchManuscripts: () => Promise<void>;
  createManuscript: (title: string) => Promise<Manuscript>;
  addManuscript: (manuscript: Manuscript) => void;
  updateManuscript: (id: string, updates: Partial<Manuscript>) => void;
  deleteManuscript: (id: string) => void;
  getManuscript: (id: string) => Manuscript | undefined;
  setCurrentManuscript: (id: string | null) => void;
  getCurrentManuscript: () => Manuscript | undefined;
}

export const useManuscriptStore = create<ManuscriptStore>()(
  persist(
    (set, get) => ({
      manuscripts: [],
      currentManuscriptId: null,
      isLoading: false,
      error: null,

      fetchManuscripts: async () => {
        try {
          set({ isLoading: true, error: null });
          const rawManuscripts = await manuscriptApi.list();

          console.log('Raw manuscripts from API:', rawManuscripts);

          // Map backend snake_case to frontend camelCase
          const manuscripts = rawManuscripts.map((m: any) => {
            const mapped = {
              id: m.id,
              title: m.title,
              content: '', // List endpoint doesn't return content
              wordCount: Number(m.word_count) || 0,
              // Story metadata
              premise: m.premise || '',
              premiseSource: m.premise_source || '',
              genre: m.genre || '',
              createdAt: m.created_at,
              updatedAt: m.updated_at,
            };
            console.log('Mapped manuscript:', mapped);
            return mapped;
          });

          console.log('All manuscripts mapped:', manuscripts);

          set({
            manuscripts,
            isLoading: false,
          });
        } catch (error) {
          console.error('fetchManuscripts error:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch manuscripts',
            isLoading: false,
          });
        }
      },

      createManuscript: async (title: string) => {
        // Call backend API to create manuscript in database
        const response = await fetch('http://localhost:8000/api/manuscripts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: title || 'Untitled Manuscript' })
        });

        if (!response.ok) {
          throw new Error('Failed to create manuscript');
        }

        const data = await response.json();

        // Add manuscript with real UUID from database
        const newManuscript: Manuscript = {
          id: data.id,
          title: data.title,
          content: '',
          wordCount: data.word_count || 0,
          // Story metadata
          premise: data.premise || '',
          premiseSource: data.premise_source || '',
          genre: data.genre || '',
          createdAt: data.created_at,
          updatedAt: data.updated_at,
        };

        set((state) => ({
          manuscripts: [...state.manuscripts, newManuscript],
          currentManuscriptId: newManuscript.id,
        }));

        return newManuscript;
      },

      addManuscript: (manuscript: Manuscript) => {
        set((state) => {
          // Check if manuscript already exists
          const exists = state.manuscripts.some((ms) => ms.id === manuscript.id);
          if (exists) {
            // Update existing manuscript
            return {
              manuscripts: state.manuscripts.map((ms) =>
                ms.id === manuscript.id ? manuscript : ms
              ),
            };
          } else {
            // Add new manuscript
            return {
              manuscripts: [...state.manuscripts, manuscript],
            };
          }
        });
      },

      updateManuscript: (id: string, updates: Partial<Manuscript>) => {
        set((state) => ({
          manuscripts: state.manuscripts.map((ms) =>
            ms.id === id
              ? { ...ms, ...updates, updatedAt: new Date().toISOString() }
              : ms
          ),
        }));
      },

      deleteManuscript: (id: string) => {
        set((state) => ({
          manuscripts: state.manuscripts.filter((ms) => ms.id !== id),
          currentManuscriptId:
            state.currentManuscriptId === id ? null : state.currentManuscriptId,
        }));
      },

      getManuscript: (id: string) => {
        return get().manuscripts.find((ms) => ms.id === id);
      },

      setCurrentManuscript: (id: string | null) => {
        set({ currentManuscriptId: id });
      },

      getCurrentManuscript: () => {
        const { manuscripts, currentManuscriptId } = get();
        if (!currentManuscriptId) return undefined;
        return manuscripts.find((ms) => ms.id === currentManuscriptId);
      },
    }),
    {
      name: 'maxwell-manuscripts', // localStorage key
    }
  )
);
