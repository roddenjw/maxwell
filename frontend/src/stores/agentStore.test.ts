/**
 * Tests for Agent Store
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import {
  useAgentStore,
  selectActiveSessions,
  selectHighPriorityRecommendations,
  selectIssuesByAgent,
  selectCategoryImprovement,
  type CoachSession,
  type CoachMessage,
  type AgentAnalysisResult,
  type AuthorInsights,
} from './agentStore';

describe('AgentStore', () => {
  beforeEach(() => {
    useAgentStore.setState({
      coachSessions: [],
      currentSession: null,
      currentMessages: [],
      isCoachLoading: false,
      isCoachPanelOpen: false,
      analysisResult: null,
      isAnalyzing: false,
      analysisError: null,
      authorInsights: null,
      isLoadingInsights: false,
      selectedApiKey: '',
      selectedModel: {
        provider: 'anthropic',
        name: 'claude-3-haiku-20240307',
      },
    });
  });

  describe('Initial State', () => {
    it('should have empty coach sessions', () => {
      const { coachSessions } = useAgentStore.getState();
      expect(coachSessions).toEqual([]);
    });

    it('should have null current session', () => {
      const { currentSession } = useAgentStore.getState();
      expect(currentSession).toBeNull();
    });

    it('should have default model selection', () => {
      const { selectedModel } = useAgentStore.getState();
      expect(selectedModel.provider).toBe('anthropic');
      expect(selectedModel.name).toBe('claude-3-haiku-20240307');
    });

    it('should not be analyzing', () => {
      const { isAnalyzing } = useAgentStore.getState();
      expect(isAnalyzing).toBe(false);
    });
  });

  describe('Coach Actions', () => {
    const mockSession: CoachSession = {
      id: 'session-1',
      title: 'Test Session',
      manuscript_id: 'ms-1',
      message_count: 5,
      total_cost: 0.01,
      total_tokens: 500,
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
    };

    const mockMessage: CoachMessage = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello, coach!',
      created_at: '2024-01-01T00:00:00Z',
    };

    describe('setCoachSessions', () => {
      it('should set coach sessions', () => {
        act(() => {
          useAgentStore.getState().setCoachSessions([mockSession]);
        });

        const { coachSessions } = useAgentStore.getState();
        expect(coachSessions).toHaveLength(1);
        expect(coachSessions[0].title).toBe('Test Session');
      });
    });

    describe('setCurrentSession', () => {
      it('should set current session', () => {
        act(() => {
          useAgentStore.getState().setCurrentSession(mockSession);
        });

        const { currentSession } = useAgentStore.getState();
        expect(currentSession).toEqual(mockSession);
      });

      it('should allow setting to null', () => {
        act(() => {
          useAgentStore.getState().setCurrentSession(mockSession);
          useAgentStore.getState().setCurrentSession(null);
        });

        const { currentSession } = useAgentStore.getState();
        expect(currentSession).toBeNull();
      });
    });

    describe('setCurrentMessages', () => {
      it('should set messages', () => {
        act(() => {
          useAgentStore.getState().setCurrentMessages([mockMessage]);
        });

        const { currentMessages } = useAgentStore.getState();
        expect(currentMessages).toHaveLength(1);
        expect(currentMessages[0].content).toBe('Hello, coach!');
      });
    });

    describe('addMessage', () => {
      it('should add message to list', () => {
        act(() => {
          useAgentStore.getState().addMessage(mockMessage);
        });

        const { currentMessages } = useAgentStore.getState();
        expect(currentMessages).toHaveLength(1);
      });

      it('should append to existing messages', () => {
        const secondMessage: CoachMessage = {
          ...mockMessage,
          id: 'msg-2',
          role: 'assistant',
          content: 'Hello! How can I help?',
        };

        act(() => {
          useAgentStore.getState().addMessage(mockMessage);
          useAgentStore.getState().addMessage(secondMessage);
        });

        const { currentMessages } = useAgentStore.getState();
        expect(currentMessages).toHaveLength(2);
        expect(currentMessages[1].role).toBe('assistant');
      });
    });

    describe('setCoachLoading', () => {
      it('should set loading state', () => {
        act(() => {
          useAgentStore.getState().setCoachLoading(true);
        });

        const { isCoachLoading } = useAgentStore.getState();
        expect(isCoachLoading).toBe(true);
      });
    });

    describe('setCoachPanelOpen', () => {
      it('should set panel open state', () => {
        act(() => {
          useAgentStore.getState().setCoachPanelOpen(true);
        });

        const { isCoachPanelOpen } = useAgentStore.getState();
        expect(isCoachPanelOpen).toBe(true);
      });
    });

    describe('toggleCoachPanel', () => {
      it('should toggle panel state', () => {
        const initial = useAgentStore.getState().isCoachPanelOpen;

        act(() => {
          useAgentStore.getState().toggleCoachPanel();
        });

        expect(useAgentStore.getState().isCoachPanelOpen).toBe(!initial);

        act(() => {
          useAgentStore.getState().toggleCoachPanel();
        });

        expect(useAgentStore.getState().isCoachPanelOpen).toBe(initial);
      });
    });

    describe('resetCoachState', () => {
      it('should reset coach state', () => {
        act(() => {
          useAgentStore.getState().setCurrentSession(mockSession);
          useAgentStore.getState().addMessage(mockMessage);
          useAgentStore.getState().setCoachLoading(true);
          useAgentStore.getState().resetCoachState();
        });

        const state = useAgentStore.getState();
        expect(state.currentSession).toBeNull();
        expect(state.currentMessages).toHaveLength(0);
        expect(state.isCoachLoading).toBe(false);
      });
    });
  });

  describe('Analysis Actions', () => {
    const mockAnalysisResult: AgentAnalysisResult = {
      recommendations: [
        { type: 'style', severity: 'high', text: 'Vary sentence length' },
        { type: 'voice', severity: 'medium', text: 'Strengthen character voice' },
      ],
      issues: [
        { type: 'continuity', severity: 'high', description: 'Eye color changed', source_agent: 'continuity' },
        { type: 'structure', severity: 'low', description: 'Long chapter', source_agent: 'structure' },
      ],
      teaching_points: ['Show vs tell', 'Pacing techniques'],
      praise: [{ type: 'positive', severity: 'positive', text: 'Great dialogue' }],
      agent_results: {},
      total_cost: 0.005,
      total_tokens: 1000,
      execution_time_ms: 2500,
    };

    describe('setAnalysisResult', () => {
      it('should set analysis result', () => {
        act(() => {
          useAgentStore.getState().setAnalysisResult(mockAnalysisResult);
        });

        const { analysisResult } = useAgentStore.getState();
        expect(analysisResult).toEqual(mockAnalysisResult);
        expect(analysisResult?.recommendations).toHaveLength(2);
      });
    });

    describe('setIsAnalyzing', () => {
      it('should set analyzing state', () => {
        act(() => {
          useAgentStore.getState().setIsAnalyzing(true);
        });

        const { isAnalyzing } = useAgentStore.getState();
        expect(isAnalyzing).toBe(true);
      });
    });

    describe('setAnalysisError', () => {
      it('should set error message', () => {
        act(() => {
          useAgentStore.getState().setAnalysisError('API error');
        });

        const { analysisError } = useAgentStore.getState();
        expect(analysisError).toBe('API error');
      });
    });

    describe('clearAnalysis', () => {
      it('should clear analysis result and error', () => {
        act(() => {
          useAgentStore.getState().setAnalysisResult(mockAnalysisResult);
          useAgentStore.getState().setAnalysisError('Some error');
          useAgentStore.getState().clearAnalysis();
        });

        const state = useAgentStore.getState();
        expect(state.analysisResult).toBeNull();
        expect(state.analysisError).toBeNull();
      });
    });
  });

  describe('Insights Actions', () => {
    const mockInsights: AuthorInsights = {
      common_issues: [
        {
          category: 'passive_voice',
          display_name: 'Passive Voice',
          total_occurrences: 50,
          recent_occurrences: 5,
          improvement_score: 75,
          trend: 'improving',
          first_seen: '2024-01-01',
          last_seen: '2024-01-10',
        },
      ],
      strengths: [
        {
          area: 'dialogue',
          display_name: 'Dialogue',
          consistency_score: 90,
          examples: ['Great character voices'],
        },
      ],
      improvement_areas: [
        {
          area: 'pacing',
          current_level: 'intermediate',
          target_level: 'advanced',
          suggestions: ['Vary chapter lengths'],
        },
      ],
      progress: {
        overall_improvement: 25,
        issues_resolved: 15,
        sessions_count: 10,
        feedback_count: 50,
      },
      personalization: {
        suppressed_suggestion_types: ['show_vs_tell'],
        preferred_feedback_style: 'detailed',
        learning_pace: 'moderate',
      },
    };

    describe('setAuthorInsights', () => {
      it('should set author insights', () => {
        act(() => {
          useAgentStore.getState().setAuthorInsights(mockInsights);
        });

        const { authorInsights } = useAgentStore.getState();
        expect(authorInsights).toEqual(mockInsights);
        expect(authorInsights?.strengths).toHaveLength(1);
      });
    });

    describe('setIsLoadingInsights', () => {
      it('should set loading state', () => {
        act(() => {
          useAgentStore.getState().setIsLoadingInsights(true);
        });

        const { isLoadingInsights } = useAgentStore.getState();
        expect(isLoadingInsights).toBe(true);
      });
    });
  });

  describe('Settings Actions', () => {
    describe('setApiKey', () => {
      it('should set API key', () => {
        act(() => {
          useAgentStore.getState().setApiKey('test-api-key');
        });

        const { selectedApiKey } = useAgentStore.getState();
        expect(selectedApiKey).toBe('test-api-key');
      });
    });

    describe('setSelectedModel', () => {
      it('should set selected model', () => {
        act(() => {
          useAgentStore.getState().setSelectedModel('openai', 'gpt-4o');
        });

        const { selectedModel } = useAgentStore.getState();
        expect(selectedModel.provider).toBe('openai');
        expect(selectedModel.name).toBe('gpt-4o');
      });
    });
  });

  describe('Selectors', () => {
    describe('selectActiveSessions', () => {
      it('should filter active sessions', () => {
        const activeSession: CoachSession = {
          id: 'session-1',
          title: 'Active',
          message_count: 5,
          total_cost: 0.01,
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        };

        const archivedSession: CoachSession = {
          id: 'session-2',
          title: 'Archived',
          message_count: 3,
          total_cost: 0.005,
          status: 'archived',
          created_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useAgentStore.getState().setCoachSessions([activeSession, archivedSession]);
        });

        const result = selectActiveSessions(useAgentStore.getState());
        expect(result).toHaveLength(1);
        expect(result[0].title).toBe('Active');
      });
    });

    describe('selectHighPriorityRecommendations', () => {
      it('should return high severity recommendations', () => {
        const result: AgentAnalysisResult = {
          recommendations: [
            { type: 'style', severity: 'high', text: 'High priority' },
            { type: 'voice', severity: 'medium', text: 'Medium priority' },
            { type: 'structure', severity: 'low', text: 'Low priority' },
          ],
          issues: [],
          teaching_points: [],
          praise: [],
          agent_results: {},
          total_cost: 0.01,
          total_tokens: 500,
          execution_time_ms: 1000,
        };

        act(() => {
          useAgentStore.getState().setAnalysisResult(result);
        });

        const highPriority = selectHighPriorityRecommendations(useAgentStore.getState());
        expect(highPriority).toHaveLength(1);
        expect(highPriority[0].text).toBe('High priority');
      });

      it('should return empty array if no analysis result', () => {
        const highPriority = selectHighPriorityRecommendations(useAgentStore.getState());
        expect(highPriority).toEqual([]);
      });
    });

    describe('selectIssuesByAgent', () => {
      it('should group issues by source agent', () => {
        const result: AgentAnalysisResult = {
          recommendations: [],
          issues: [
            { type: 'continuity', severity: 'high', description: 'Issue 1', source_agent: 'continuity' },
            { type: 'continuity', severity: 'medium', description: 'Issue 2', source_agent: 'continuity' },
            { type: 'style', severity: 'low', description: 'Issue 3', source_agent: 'style' },
            { type: 'general', severity: 'medium', description: 'Issue 4' }, // No source_agent
          ],
          teaching_points: [],
          praise: [],
          agent_results: {},
          total_cost: 0.01,
          total_tokens: 500,
          execution_time_ms: 1000,
        };

        act(() => {
          useAgentStore.getState().setAnalysisResult(result);
        });

        const grouped = selectIssuesByAgent(useAgentStore.getState());
        expect(grouped.continuity).toHaveLength(2);
        expect(grouped.style).toHaveLength(1);
        expect(grouped.general).toHaveLength(1);
      });
    });

    describe('selectCategoryImprovement', () => {
      it('should return improvement score for category', () => {
        const insights: AuthorInsights = {
          common_issues: [
            {
              category: 'passive_voice',
              display_name: 'Passive Voice',
              total_occurrences: 50,
              recent_occurrences: 5,
              improvement_score: 75,
              trend: 'improving',
              first_seen: '2024-01-01',
              last_seen: '2024-01-10',
            },
          ],
          strengths: [],
          improvement_areas: [],
          progress: {
            overall_improvement: 0,
            issues_resolved: 0,
            sessions_count: 0,
            feedback_count: 0,
          },
          personalization: {
            suppressed_suggestion_types: [],
            preferred_feedback_style: '',
            learning_pace: '',
          },
        };

        act(() => {
          useAgentStore.getState().setAuthorInsights(insights);
        });

        const score = selectCategoryImprovement(useAgentStore.getState(), 'passive_voice');
        expect(score).toBe(75);
      });

      it('should return 0 for unknown category', () => {
        const score = selectCategoryImprovement(useAgentStore.getState(), 'unknown');
        expect(score).toBe(0);
      });
    });
  });
});
