/**
 * Brainstorming Store - State management for AI-powered ideation
 * Using Zustand for lightweight state management
 */

import { create } from 'zustand';
import type {
  BrainstormSession,
  BrainstormIdea,
  BrainstormSessionType,
  BrainstormTechnique,
  BrainstormContext,
} from '@/types/brainstorm';
import { brainstormingApi, manuscriptApi } from '@/lib/api';

interface BrainstormStore {
  // State
  currentSession: BrainstormSession | null;
  sessions: BrainstormSession[];
  ideas: Map<string, BrainstormIdea[]>; // session_id -> ideas
  selectedIdeaIds: Set<string>;
  isGenerating: boolean;
  currentTechnique: BrainstormTechnique | null;
  manuscriptContext: BrainstormContext | null; // Auto-loaded outline + entities
  totalCost: number;
  totalTokens: number;

  // Modal state
  isModalOpen: boolean;
  modalManuscriptId: string | null;
  modalOutlineId: string | null;

  // Session Actions
  createSession: (manuscriptId: string, sessionType: BrainstormSessionType, context: any, outlineId?: string) => Promise<BrainstormSession>;
  loadSession: (sessionId: string) => Promise<void>;
  loadManuscriptSessions: (manuscriptId: string) => Promise<void>;
  loadManuscriptContext: (manuscriptId: string) => Promise<void>; // NEW
  setCurrentSession: (session: BrainstormSession | null) => void;
  updateSessionStatus: (sessionId: string, status: string) => Promise<void>;

  // Idea Actions
  addIdeas: (sessionId: string, ideas: BrainstormIdea[]) => void;
  updateIdea: (ideaId: string, updates: Partial<BrainstormIdea>) => void;
  removeIdea: (ideaId: string) => void;

  // Selection Actions
  selectIdea: (ideaId: string) => void;
  deselectIdea: (ideaId: string) => void;
  toggleIdeaSelection: (ideaId: string) => void;
  selectAllIdeas: (sessionId: string) => void;
  deselectAllIdeas: () => void;

  // Generation Actions
  setGenerating: (isGenerating: boolean) => void;
  setTechnique: (technique: BrainstormTechnique | null) => void;

  // Cost Tracking
  addCost: (cost: number, tokens: number) => void;
  resetCost: () => void;

  // Modal Actions
  openModal: (manuscriptId: string, outlineId?: string, technique?: BrainstormTechnique) => void;
  closeModal: () => void;

  // Premise persistence
  savePremise: (premise: string, source: 'user_written' | 'ai_generated') => Promise<void>;

  // Utility Actions
  clearAll: () => void;
  getSessionIdeas: (sessionId: string) => BrainstormIdea[];
  getSelectedIdeas: () => BrainstormIdea[];
  calculateSessionCost: (sessionId: string) => number;
}

export const useBrainstormStore = create<BrainstormStore>((set, get) => ({
  // Initial State
  currentSession: null,
  sessions: [],
  ideas: new Map(),
  selectedIdeaIds: new Set(),
  isGenerating: false,
  currentTechnique: null,
  manuscriptContext: null,
  totalCost: 0,
  totalTokens: 0,
  isModalOpen: false,
  modalManuscriptId: null,
  modalOutlineId: null,

  // Session Actions
  createSession: async (manuscriptId, sessionType, context, outlineId) => {
    try {
      const session = await brainstormingApi.createSession({
        manuscript_id: manuscriptId,
        outline_id: outlineId,
        session_type: sessionType,
        context_data: context,
      });

      set((state) => ({
        currentSession: session,
        sessions: [...state.sessions, session],
      }));

      return session;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  },

  loadSession: async (sessionId) => {
    try {
      const session = await brainstormingApi.getSession(sessionId);
      const ideas = await brainstormingApi.listSessionIdeas(sessionId);

      set((state) => {
        const newIdeas = new Map(state.ideas);
        newIdeas.set(sessionId, ideas);

        return {
          currentSession: session,
          ideas: newIdeas,
        };
      });
    } catch (error) {
      console.error('Failed to load session:', error);
      throw error;
    }
  },

  loadManuscriptSessions: async (manuscriptId) => {
    try {
      const sessions = await brainstormingApi.listManuscriptSessions(manuscriptId);
      set({ sessions });
    } catch (error) {
      console.error('Failed to load manuscript sessions:', error);
      throw error;
    }
  },

  loadManuscriptContext: async (manuscriptId) => {
    try {
      const context = await brainstormingApi.getBrainstormContext(manuscriptId);
      set({ manuscriptContext: context });
    } catch (error) {
      console.error('Failed to load manuscript context:', error);
      // Don't throw - context loading is optional, app should still work
      set({ manuscriptContext: null });
    }
  },

  savePremise: async (premise, source) => {
    const manuscriptId = get().modalManuscriptId;
    if (!manuscriptId || !premise.trim()) return;
    try {
      await manuscriptApi.update(manuscriptId, {
        premise,
        premise_source: source,
      } as any);
      // Update local context so it's available immediately
      const ctx = get().manuscriptContext;
      if (ctx) {
        set({
          manuscriptContext: {
            ...ctx,
            outline: { ...ctx.outline, premise },
          },
        });
      }
    } catch (error) {
      console.error('Failed to save premise:', error);
    }
  },

  setCurrentSession: (session) => set({ currentSession: session }),

  updateSessionStatus: async (sessionId, status) => {
    try {
      await brainstormingApi.updateSessionStatus(sessionId, status);

      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, status: status as any } : s
        ),
        currentSession:
          state.currentSession?.id === sessionId
            ? { ...state.currentSession, status: status as any }
            : state.currentSession,
      }));
    } catch (error) {
      console.error('Failed to update session status:', error);
      throw error;
    }
  },

  // Idea Actions
  addIdeas: (sessionId, ideas) => {
    set((state) => {
      const newIdeas = new Map(state.ideas);
      const existingIdeas = newIdeas.get(sessionId) || [];
      newIdeas.set(sessionId, [...existingIdeas, ...ideas]);

      // Update cost tracking
      const totalCost = ideas.reduce((sum, idea) => sum + idea.ai_cost, state.totalCost);
      const totalTokens = ideas.reduce((sum, idea) => sum + idea.ai_tokens, state.totalTokens);

      return {
        ideas: newIdeas,
        totalCost,
        totalTokens,
      };
    });
  },

  updateIdea: (ideaId, updates) => {
    set((state) => {
      const newIdeas = new Map(state.ideas);

      for (const [sessionId, ideas] of newIdeas.entries()) {
        const updatedIdeas = ideas.map((idea) =>
          idea.id === ideaId ? { ...idea, ...updates } : idea
        );

        if (updatedIdeas !== ideas) {
          newIdeas.set(sessionId, updatedIdeas);
          break;
        }
      }

      return { ideas: newIdeas };
    });
  },

  removeIdea: (ideaId) => {
    set((state) => {
      const newIdeas = new Map(state.ideas);
      const newSelectedIds = new Set(state.selectedIdeaIds);

      for (const [sessionId, ideas] of newIdeas.entries()) {
        newIdeas.set(
          sessionId,
          ideas.filter((idea) => idea.id !== ideaId)
        );
      }

      newSelectedIds.delete(ideaId);

      return {
        ideas: newIdeas,
        selectedIdeaIds: newSelectedIds,
      };
    });
  },

  // Selection Actions
  selectIdea: (ideaId) => {
    set((state) => {
      const newSelectedIds = new Set(state.selectedIdeaIds);
      newSelectedIds.add(ideaId);
      return { selectedIdeaIds: newSelectedIds };
    });
  },

  deselectIdea: (ideaId) => {
    set((state) => {
      const newSelectedIds = new Set(state.selectedIdeaIds);
      newSelectedIds.delete(ideaId);
      return { selectedIdeaIds: newSelectedIds };
    });
  },

  toggleIdeaSelection: (ideaId) => {
    const { selectedIdeaIds } = get();
    if (selectedIdeaIds.has(ideaId)) {
      get().deselectIdea(ideaId);
    } else {
      get().selectIdea(ideaId);
    }
  },

  selectAllIdeas: (sessionId) => {
    const ideas = get().getSessionIdeas(sessionId);
    set({
      selectedIdeaIds: new Set(ideas.map((idea) => idea.id)),
    });
  },

  deselectAllIdeas: () => {
    set({ selectedIdeaIds: new Set() });
  },

  // Generation Actions
  setGenerating: (isGenerating) => set({ isGenerating }),

  setTechnique: (technique) => set({ currentTechnique: technique }),

  // Cost Tracking
  addCost: (cost, tokens) => {
    set((state) => ({
      totalCost: state.totalCost + cost,
      totalTokens: state.totalTokens + tokens,
    }));
  },

  resetCost: () => set({ totalCost: 0, totalTokens: 0 }),

  // Modal Actions
  openModal: (manuscriptId, outlineId, technique) => {
    set({
      isModalOpen: true,
      modalManuscriptId: manuscriptId,
      modalOutlineId: outlineId,
      currentTechnique: technique || null,
    });
  },

  closeModal: () => {
    set({
      isModalOpen: false,
      modalManuscriptId: null,
      modalOutlineId: null,
      currentTechnique: null,
      currentSession: null,
      selectedIdeaIds: new Set(),
    });
  },

  // Utility Actions
  clearAll: () => {
    set({
      currentSession: null,
      sessions: [],
      ideas: new Map(),
      selectedIdeaIds: new Set(),
      isGenerating: false,
      currentTechnique: null,
      manuscriptContext: null,
      totalCost: 0,
      totalTokens: 0,
      isModalOpen: false,
      modalManuscriptId: null,
      modalOutlineId: null,
    });
  },

  getSessionIdeas: (sessionId) => {
    const { ideas } = get();
    return ideas.get(sessionId) || [];
  },

  getSelectedIdeas: () => {
    const { ideas, selectedIdeaIds } = get();
    const allIdeas: BrainstormIdea[] = [];

    for (const sessionIdeas of ideas.values()) {
      allIdeas.push(...sessionIdeas.filter((idea) => selectedIdeaIds.has(idea.id)));
    }

    return allIdeas;
  },

  calculateSessionCost: (sessionId) => {
    const ideas = get().getSessionIdeas(sessionId);
    return ideas.reduce((sum, idea) => sum + idea.ai_cost, 0);
  },
}));
