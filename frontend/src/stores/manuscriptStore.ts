/**
 * Manuscript Store - Zustand
 * Manages manuscript state with localStorage persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Manuscript {
  id: string;
  title: string;
  content: string; // JSON stringified Lexical editor state
  wordCount: number;
  createdAt: string;
  updatedAt: string;
}

interface ManuscriptStore {
  manuscripts: Manuscript[];
  currentManuscriptId: string | null;

  // Actions
  createManuscript: (title: string) => Manuscript;
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

      createManuscript: (title: string) => {
        const newManuscript: Manuscript = {
          id: `ms-${Date.now()}`,
          title: title || 'Untitled Manuscript',
          content: '',
          wordCount: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
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
