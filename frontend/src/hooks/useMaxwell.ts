/**
 * useMaxwell Hook
 *
 * Provides easy access to Maxwell functionality from any component.
 * Handles API calls, state management, and common operations.
 */

import { useCallback, useMemo } from 'react';
import { useAgentStore } from '@/stores/agentStore';
import { agentApi } from '@/lib/api';

interface UseMaxwellOptions {
  userId: string;
  apiKey: string;
  manuscriptId?: string;
  chapterId?: string;
}

export function useMaxwell({ userId, apiKey, manuscriptId, chapterId }: UseMaxwellOptions) {
  const {
    // Panel state
    isCoachPanelOpen,
    setCoachPanelOpen,
    // Maxwell state
    maxwellResponse,
    setMaxwellResponse,
    isMaxwellLoading,
    setIsMaxwellLoading,
    maxwellError,
    setMaxwellError,
    addMaxwellMessage,
    maxwellConversationHistory,
    clearMaxwellHistory,
    resetMaxwellState,
    // Model settings
    selectedModel,
  } = useAgentStore();

  /**
   * Open the Maxwell panel
   */
  const openPanel = useCallback(() => {
    setCoachPanelOpen(true);
  }, [setCoachPanelOpen]);

  /**
   * Close the Maxwell panel
   */
  const closePanel = useCallback(() => {
    setCoachPanelOpen(false);
  }, [setCoachPanelOpen]);

  /**
   * Toggle the Maxwell panel
   */
  const togglePanel = useCallback(() => {
    setCoachPanelOpen(!isCoachPanelOpen);
  }, [isCoachPanelOpen, setCoachPanelOpen]);

  /**
   * Chat with Maxwell (stateless, auto-routes to agents)
   */
  const chat = useCallback(
    async (message: string, selectedText?: string) => {
      if (!apiKey) {
        setMaxwellError('API key not configured');
        return null;
      }

      setIsMaxwellLoading(true);
      setMaxwellError(null);
      addMaxwellMessage('user', message);

      try {
        const response = await agentApi.maxwellChat({
          api_key: apiKey,
          user_id: userId,
          message,
          manuscript_id: manuscriptId,
          context: {
            chapter_id: chapterId,
            selected_text: selectedText,
          },
          auto_analyze: true,
          model_provider: selectedModel.provider,
          model_name: selectedModel.name,
        });

        if (response.success) {
          addMaxwellMessage('assistant', response.data.content);
          setMaxwellResponse(response.data);
          return response.data;
        }
        return null;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Chat failed';
        setMaxwellError(errorMessage);
        return null;
      } finally {
        setIsMaxwellLoading(false);
      }
    },
    [
      apiKey,
      userId,
      manuscriptId,
      chapterId,
      selectedModel,
      setIsMaxwellLoading,
      setMaxwellError,
      addMaxwellMessage,
      setMaxwellResponse,
    ]
  );

  /**
   * Run full analysis on text
   */
  const analyze = useCallback(
    async (text: string, tone: 'encouraging' | 'direct' | 'teaching' | 'celebratory' = 'encouraging') => {
      if (!apiKey) {
        setMaxwellError('API key not configured');
        return null;
      }

      setIsMaxwellLoading(true);
      setMaxwellError(null);

      try {
        const response = await agentApi.maxwellAnalyze({
          api_key: apiKey,
          user_id: userId,
          text,
          manuscript_id: manuscriptId || '',
          chapter_id: chapterId,
          tone,
          model_provider: selectedModel.provider,
          model_name: selectedModel.name,
        });

        if (response.success) {
          setMaxwellResponse(response.data);
          return response.data;
        }
        return null;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
        setMaxwellError(errorMessage);
        return null;
      } finally {
        setIsMaxwellLoading(false);
      }
    },
    [apiKey, userId, manuscriptId, chapterId, selectedModel, setIsMaxwellLoading, setMaxwellError, setMaxwellResponse]
  );

  /**
   * Run quick check on text
   */
  const quickCheck = useCallback(
    async (text: string, focus: string) => {
      if (!apiKey) {
        setMaxwellError('API key not configured');
        return null;
      }

      setIsMaxwellLoading(true);
      setMaxwellError(null);

      try {
        const response = await agentApi.maxwellQuickCheck({
          api_key: apiKey,
          user_id: userId,
          text,
          focus,
          manuscript_id: manuscriptId,
          model_provider: selectedModel.provider,
          model_name: selectedModel.name,
        });

        if (response.success) {
          setMaxwellResponse(response.data);
          addMaxwellMessage('assistant', response.data.content);
          return response.data;
        }
        return null;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Quick check failed';
        setMaxwellError(errorMessage);
        return null;
      } finally {
        setIsMaxwellLoading(false);
      }
    },
    [
      apiKey,
      userId,
      manuscriptId,
      selectedModel,
      setIsMaxwellLoading,
      setMaxwellError,
      setMaxwellResponse,
      addMaxwellMessage,
    ]
  );

  /**
   * Get explanation of a writing concept
   */
  const explain = useCallback(
    async (topic: string, contextText?: string) => {
      if (!apiKey) {
        setMaxwellError('API key not configured');
        return null;
      }

      setIsMaxwellLoading(true);
      setMaxwellError(null);

      try {
        const response = await agentApi.maxwellExplain({
          api_key: apiKey,
          user_id: userId,
          topic,
          context: contextText,
          model_provider: selectedModel.provider,
          model_name: selectedModel.name,
        });

        if (response.success) {
          setMaxwellResponse(response.data);
          addMaxwellMessage('assistant', response.data.content);
          return response.data;
        }
        return null;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Explanation failed';
        setMaxwellError(errorMessage);
        return null;
      } finally {
        setIsMaxwellLoading(false);
      }
    },
    [
      apiKey,
      userId,
      selectedModel,
      setIsMaxwellLoading,
      setMaxwellError,
      setMaxwellResponse,
      addMaxwellMessage,
    ]
  );

  /**
   * Clear conversation and response state
   */
  const clear = useCallback(() => {
    resetMaxwellState();
  }, [resetMaxwellState]);

  return useMemo(
    () => ({
      // Panel controls
      isOpen: isCoachPanelOpen,
      openPanel,
      closePanel,
      togglePanel,

      // State
      response: maxwellResponse,
      isLoading: isMaxwellLoading,
      error: maxwellError,
      conversationHistory: maxwellConversationHistory,

      // Actions
      chat,
      analyze,
      quickCheck,
      explain,
      clear,

      // Computed
      hasFeedback: !!maxwellResponse?.feedback,
      hasError: !!maxwellError,
    }),
    [
      isCoachPanelOpen,
      openPanel,
      closePanel,
      togglePanel,
      maxwellResponse,
      isMaxwellLoading,
      maxwellError,
      maxwellConversationHistory,
      chat,
      analyze,
      quickCheck,
      explain,
      clear,
    ]
  );
}

export default useMaxwell;
