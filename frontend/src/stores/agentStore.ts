/**
 * Agent Store - Zustand
 * Manages state for AI agents: Smart Coach, Writing Assistant, and Author Insights
 */

import { create } from 'zustand';

// ========================================
// Types
// ========================================

export interface CoachMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_used?: string[];
  cost?: number;
  tokens?: number;
  created_at: string;
}

export interface CoachSession {
  id: string;
  title: string;
  manuscript_id?: string;
  message_count: number;
  total_cost: number;
  total_tokens?: number;
  status: 'active' | 'archived';
  initial_context?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  last_message_at?: string;
}

export interface AgentRecommendation {
  type: string;
  severity: 'high' | 'medium' | 'low' | 'positive';
  text: string;
  suggestion?: string;
  teaching_point?: string;
  source_agent?: string;
  aspect?: string;
}

export interface AgentIssue {
  type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  location?: string;
  suggestion?: string;
  source_agent?: string;
}

export interface AgentAnalysisResult {
  recommendations: AgentRecommendation[];
  issues: AgentIssue[];
  teaching_points: string[];
  praise: AgentRecommendation[];
  agent_results: Record<string, any>;
  total_cost: number;
  total_tokens: number;
  execution_time_ms: number;
  author_insights?: AuthorInsights;
}

export interface IssueCategory {
  category: string;
  display_name: string;
  total_occurrences: number;
  recent_occurrences: number;
  improvement_score: number; // 0-100, higher is better improvement
  trend: 'improving' | 'stable' | 'declining';
  first_seen: string;
  last_seen: string;
}

export interface StrengthArea {
  area: string;
  display_name: string;
  consistency_score: number; // 0-100
  examples: string[];
}

export interface AuthorInsights {
  common_issues: IssueCategory[];
  strengths: StrengthArea[];
  improvement_areas: Array<{
    area: string;
    current_level: string;
    target_level: string;
    suggestions: string[];
  }>;
  progress: {
    overall_improvement: number;
    issues_resolved: number;
    sessions_count: number;
    feedback_count: number;
  };
  personalization: {
    suppressed_suggestion_types: string[];
    preferred_feedback_style: string;
    learning_pace: string;
  };
}

// Maxwell Unified Interface Types
export interface MaxwellFeedback {
  narrative: string;
  highlights: Array<{ aspect: string; text: string }>;
  priorities: Array<{
    type: string;
    severity: 'high' | 'medium' | 'low';
    text: string;
    why_it_matters?: string;
    suggestion?: string;
  }>;
  teaching_moments: string[];
  summary: string;
  total_issues: number;
  total_praise: number;
}

export interface MaxwellResponse {
  content: string;
  response_type: 'conversation' | 'analysis' | 'quick_check' | 'explanation';
  feedback?: MaxwellFeedback;
  agents_consulted: string[];
  routing_reasoning: string;
  cost: number;
  tokens: number;
  execution_time_ms: number;
}

// ========================================
// Store State
// ========================================

interface AgentStore {
  // Smart Coach State
  coachSessions: CoachSession[];
  currentSession: CoachSession | null;
  currentMessages: CoachMessage[];
  isCoachLoading: boolean;
  isCoachPanelOpen: boolean;

  // Analysis State
  analysisResult: AgentAnalysisResult | null;
  isAnalyzing: boolean;
  analysisError: string | null;

  // Maxwell Unified State
  maxwellResponse: MaxwellResponse | null;
  isMaxwellLoading: boolean;
  maxwellError: string | null;
  maxwellConversationHistory: Array<{ role: 'user' | 'assistant'; content: string }>;

  // Author Insights
  authorInsights: AuthorInsights | null;
  isLoadingInsights: boolean;

  // Settings
  selectedApiKey: string;
  selectedModel: {
    provider: string;
    name: string;
  };

  // Coach Actions
  setCoachSessions: (sessions: CoachSession[]) => void;
  setCurrentSession: (session: CoachSession | null) => void;
  setCurrentMessages: (messages: CoachMessage[]) => void;
  addMessage: (message: CoachMessage) => void;
  setCoachLoading: (loading: boolean) => void;
  setCoachPanelOpen: (open: boolean) => void;
  toggleCoachPanel: () => void;

  // Analysis Actions
  setAnalysisResult: (result: AgentAnalysisResult | null) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
  setAnalysisError: (error: string | null) => void;
  clearAnalysis: () => void;

  // Maxwell Actions
  setMaxwellResponse: (response: MaxwellResponse | null) => void;
  setIsMaxwellLoading: (loading: boolean) => void;
  setMaxwellError: (error: string | null) => void;
  addMaxwellMessage: (role: 'user' | 'assistant', content: string) => void;
  clearMaxwellHistory: () => void;

  // Insights Actions
  setAuthorInsights: (insights: AuthorInsights | null) => void;
  setIsLoadingInsights: (loading: boolean) => void;

  // Settings Actions
  setApiKey: (key: string) => void;
  setSelectedModel: (provider: string, name: string) => void;

  // Reset
  resetCoachState: () => void;
  resetMaxwellState: () => void;
}

// ========================================
// Store Implementation
// ========================================

export const useAgentStore = create<AgentStore>((set) => ({
  // Initial State
  coachSessions: [],
  currentSession: null,
  currentMessages: [],
  isCoachLoading: false,
  isCoachPanelOpen: false,

  analysisResult: null,
  isAnalyzing: false,
  analysisError: null,

  // Maxwell Unified State
  maxwellResponse: null,
  isMaxwellLoading: false,
  maxwellError: null,
  maxwellConversationHistory: [],

  authorInsights: null,
  isLoadingInsights: false,

  selectedApiKey: '',
  selectedModel: {
    provider: 'anthropic',
    name: 'claude-3-haiku-20240307',
  },

  // Coach Actions
  setCoachSessions: (sessions) => set({ coachSessions: sessions }),

  setCurrentSession: (session) => set({ currentSession: session }),

  setCurrentMessages: (messages) => set({ currentMessages: messages }),

  addMessage: (message) =>
    set((state) => ({
      currentMessages: [...state.currentMessages, message],
    })),

  setCoachLoading: (loading) => set({ isCoachLoading: loading }),

  setCoachPanelOpen: (open) => set({ isCoachPanelOpen: open }),

  toggleCoachPanel: () =>
    set((state) => ({ isCoachPanelOpen: !state.isCoachPanelOpen })),

  // Analysis Actions
  setAnalysisResult: (result) => set({ analysisResult: result }),

  setIsAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),

  setAnalysisError: (error) => set({ analysisError: error }),

  clearAnalysis: () =>
    set({
      analysisResult: null,
      analysisError: null,
    }),

  // Maxwell Actions
  setMaxwellResponse: (response) => set({ maxwellResponse: response }),

  setIsMaxwellLoading: (loading) => set({ isMaxwellLoading: loading }),

  setMaxwellError: (error) => set({ maxwellError: error }),

  addMaxwellMessage: (role, content) =>
    set((state) => ({
      maxwellConversationHistory: [
        ...state.maxwellConversationHistory,
        { role, content },
      ],
    })),

  clearMaxwellHistory: () => set({ maxwellConversationHistory: [] }),

  // Insights Actions
  setAuthorInsights: (insights) => set({ authorInsights: insights }),

  setIsLoadingInsights: (loading) => set({ isLoadingInsights: loading }),

  // Settings Actions
  setApiKey: (key) => set({ selectedApiKey: key }),

  setSelectedModel: (provider, name) =>
    set({
      selectedModel: { provider, name },
    }),

  // Reset
  resetCoachState: () =>
    set({
      currentSession: null,
      currentMessages: [],
      isCoachLoading: false,
    }),

  resetMaxwellState: () =>
    set({
      maxwellResponse: null,
      maxwellError: null,
      maxwellConversationHistory: [],
      isMaxwellLoading: false,
    }),
}));

// ========================================
// Selectors
// ========================================

/**
 * Get active (non-archived) coach sessions
 */
export const selectActiveSessions = (state: AgentStore) =>
  state.coachSessions.filter((s) => s.status === 'active');

/**
 * Get high-severity recommendations from analysis
 */
export const selectHighPriorityRecommendations = (state: AgentStore) =>
  state.analysisResult?.recommendations.filter((r) => r.severity === 'high') ?? [];

/**
 * Get issues grouped by source agent
 */
export const selectIssuesByAgent = (state: AgentStore) => {
  const issues = state.analysisResult?.issues ?? [];
  return issues.reduce<Record<string, AgentIssue[]>>((acc, issue) => {
    const agent = issue.source_agent ?? 'general';
    if (!acc[agent]) {
      acc[agent] = [];
    }
    acc[agent].push(issue);
    return acc;
  }, {});
};

/**
 * Get improvement score for a specific category
 */
export const selectCategoryImprovement = (state: AgentStore, category: string) =>
  state.authorInsights?.common_issues.find((i) => i.category === category)?.improvement_score ?? 0;
