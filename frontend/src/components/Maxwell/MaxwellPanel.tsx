/**
 * MaxwellPanel - Unified AI Writing Assistant
 *
 * A single cohesive panel for all Maxwell interactions:
 * - Conversational coaching (chat)
 * - Writing analysis with synthesized feedback
 * - Quick checks and explanations
 * - Feedback history and session management
 *
 * Maxwell presents as ONE entity - warm, knowledgeable, teaching-focused.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAgentStore, type MaxwellResponse, type MaxwellFeedback } from '@/stores/agentStore';
import { agentApi } from '@/lib/api';

// Icons
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
  </svg>
);

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);

const ChatIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const AnalyzeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z" />
  </svg>
);

const LightbulbIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V16a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-1.3A7 7 0 0 0 12 2z" />
  </svg>
);

const SparkleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
  </svg>
);

const HistoryIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" />
  </svg>
);

type TabType = 'chat' | 'feedback';

interface MaxwellPanelProps {
  manuscriptId?: string;
  chapterId?: string;
  chapterTitle?: string;
  selectedText?: string;
  userId: string;
  apiKey: string;
  onClose?: () => void;
}

export const MaxwellPanel: React.FC<MaxwellPanelProps> = ({
  manuscriptId,
  chapterId,
  chapterTitle,
  selectedText,
  userId,
  apiKey,
  onClose,
}) => {
  const {
    // Coach state (for session-based chat)
    isCoachPanelOpen,
    setCoachPanelOpen,
    currentSession,
    setCurrentSession,
    currentMessages,
    setCurrentMessages,
    addMessage,
    isCoachLoading,
    setCoachLoading,
    coachSessions,
    setCoachSessions,
    // Maxwell unified state
    maxwellResponse,
    setMaxwellResponse,
    isMaxwellLoading,
    setIsMaxwellLoading,
    maxwellError,
    setMaxwellError,
    addMaxwellMessage,
    maxwellConversationHistory,
    clearMaxwellHistory,
  } = useAgentStore();

  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [inputMessage, setInputMessage] = useState('');
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages, maxwellConversationHistory]);

  // Load sessions on mount
  useEffect(() => {
    if (isCoachPanelOpen && userId && apiKey) {
      loadSessions();
    }
  }, [isCoachPanelOpen, userId, manuscriptId]);

  // Auto-switch to feedback tab when analysis completes
  useEffect(() => {
    if (maxwellResponse?.response_type === 'analysis' && maxwellResponse.feedback) {
      setActiveTab('feedback');
    }
  }, [maxwellResponse]);

  const loadSessions = async () => {
    try {
      const response = await agentApi.listCoachSessions(userId, manuscriptId);
      if (response.success) {
        setCoachSessions(
          response.data.map((s) => ({
            ...s,
            status: s.status as 'active' | 'archived',
          }))
        );
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const startNewSession = async () => {
    if (!apiKey) {
      setError('Please configure your API key in Settings');
      return;
    }

    setCoachLoading(true);
    setError(null);

    try {
      const response = await agentApi.startCoachSession({
        api_key: apiKey,
        user_id: userId,
        manuscript_id: manuscriptId,
        title: chapterTitle ? `Coaching: ${chapterTitle}` : 'New Session',
        initial_context: {
          chapter_id: chapterId,
          chapter_title: chapterTitle,
        },
      });

      if (response.success) {
        setCurrentSession({
          id: response.data.id,
          title: response.data.title,
          manuscript_id: response.data.manuscript_id,
          message_count: 0,
          total_cost: 0,
          status: 'active',
          created_at: response.data.created_at,
        });
        setCurrentMessages([]);
        setShowHistory(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session');
    } finally {
      setCoachLoading(false);
    }
  };

  const loadSession = async (sessionId: string) => {
    setCoachLoading(true);
    setError(null);

    try {
      const response = await agentApi.getCoachSession(sessionId);
      if (response.success) {
        setCurrentSession({
          id: response.data.session.id,
          title: response.data.session.title,
          manuscript_id: response.data.session.manuscript_id,
          message_count: response.data.session.message_count,
          total_cost: response.data.session.total_cost,
          total_tokens: response.data.session.total_tokens,
          status: response.data.session.status as 'active' | 'archived',
          initial_context: response.data.session.initial_context,
          created_at: response.data.session.created_at,
          updated_at: response.data.session.updated_at,
        });
        setCurrentMessages(
          response.data.messages.map((m) => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            tools_used: m.tools_used,
            cost: m.cost,
            tokens: m.tokens,
            created_at: m.created_at,
          }))
        );
        setShowHistory(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session');
    } finally {
      setCoachLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isCoachLoading || isMaxwellLoading) return;
    if (!apiKey) {
      setError('Please configure your API key in Settings');
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // If we have a current session, use the coach API
    if (currentSession) {
      addMessage({
        id: `temp-${Date.now()}`,
        role: 'user',
        content: userMessage,
        created_at: new Date().toISOString(),
      });

      setCoachLoading(true);

      try {
        const response = await agentApi.coachChat({
          api_key: apiKey,
          user_id: userId,
          session_id: currentSession.id,
          message: userMessage,
          context: {
            chapter_id: chapterId,
            chapter_title: chapterTitle,
            selected_text: selectedText,
          },
        });

        if (response.success) {
          addMessage({
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.data.content,
            tools_used: response.data.tools_used,
            cost: response.data.cost,
            tokens: response.data.tokens,
            created_at: new Date().toISOString(),
          });

          setCurrentSession({
            ...currentSession,
            message_count: currentSession.message_count + 2,
            total_cost: currentSession.total_cost + response.data.cost,
          });

          // If analysis was performed, also update Maxwell state
          if (response.data.analysis_performed && response.data.synthesized_feedback) {
            setMaxwellResponse({
              content: response.data.content,
              response_type: 'analysis',
              feedback: response.data.synthesized_feedback as MaxwellFeedback,
              agents_consulted: response.data.agents_consulted || [],
              routing_reasoning: 'Routed via Smart Coach',
              cost: response.data.cost,
              tokens: response.data.tokens,
              execution_time_ms: 0,
            });
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
      } finally {
        setCoachLoading(false);
      }
    } else {
      // No session - use Maxwell unified chat (stateless)
      addMaxwellMessage('user', userMessage);
      setIsMaxwellLoading(true);

      try {
        const response = await agentApi.maxwellChat({
          api_key: apiKey,
          user_id: userId,
          message: userMessage,
          manuscript_id: manuscriptId,
          context: {
            chapter_id: chapterId,
            chapter_title: chapterTitle,
            selected_text: selectedText,
          },
          auto_analyze: true,
        });

        if (response.success) {
          addMaxwellMessage('assistant', response.data.content);
          setMaxwellResponse(response.data);
        }
      } catch (err) {
        setMaxwellError(err instanceof Error ? err.message : 'Failed to chat');
      } finally {
        setIsMaxwellLoading(false);
      }
    }
  };

  const runFullAnalysis = async () => {
    if (!selectedText || !apiKey) {
      setError(selectedText ? 'Please configure your API key' : 'Select some text first');
      return;
    }

    setIsMaxwellLoading(true);
    setError(null);
    setActiveTab('feedback');

    try {
      const response = await agentApi.maxwellAnalyze({
        api_key: apiKey,
        user_id: userId,
        text: selectedText,
        manuscript_id: manuscriptId || '',
        chapter_id: chapterId,
        tone: 'encouraging',
      });

      if (response.success) {
        setMaxwellResponse(response.data);
      }
    } catch (err) {
      setMaxwellError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsMaxwellLoading(false);
    }
  };

  const runQuickCheck = async (focus: string) => {
    if (!selectedText || !apiKey) {
      setError(selectedText ? 'Please configure your API key' : 'Select some text first');
      return;
    }

    setIsMaxwellLoading(true);
    setError(null);

    try {
      const response = await agentApi.maxwellQuickCheck({
        api_key: apiKey,
        user_id: userId,
        text: selectedText,
        focus,
        manuscript_id: manuscriptId,
      });

      if (response.success) {
        setMaxwellResponse(response.data);
        // Add to conversation
        addMaxwellMessage('assistant', response.data.content);
      }
    } catch (err) {
      setMaxwellError(err instanceof Error ? err.message : 'Quick check failed');
    } finally {
      setIsMaxwellLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleClose = () => {
    setCoachPanelOpen(false);
    onClose?.();
  };

  if (!isCoachPanelOpen) return null;

  const isLoading = isCoachLoading || isMaxwellLoading;
  const displayError = error || maxwellError;

  return (
    <div
      className="fixed right-0 top-0 h-full w-[420px] bg-[var(--color-vellum)] border-l border-[var(--color-bronze)]/30 shadow-xl z-50 flex flex-col"
      style={{ fontFamily: 'var(--font-sans)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-bronze)]/20 bg-gradient-to-r from-[var(--color-vellum-darker)] to-[var(--color-vellum)]">
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-bronze)]">
            <SparkleIcon />
          </span>
          <span className="text-lg font-semibold text-[var(--color-midnight)]">Maxwell</span>
          {currentSession && (
            <span className="text-xs text-[var(--color-bronze)] bg-[var(--color-bronze)]/10 px-2 py-0.5 rounded">
              ${currentSession.total_cost.toFixed(4)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-1.5 rounded hover:bg-[var(--color-bronze)]/10 text-[var(--color-bronze)]"
            title="Session History"
          >
            <HistoryIcon />
          </button>
          <button
            onClick={handleClose}
            className="p-1.5 rounded hover:bg-[var(--color-bronze)]/10 text-[var(--color-midnight)]"
          >
            <CloseIcon />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--color-bronze)]/20">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
            activeTab === 'chat'
              ? 'text-[var(--color-bronze)] border-b-2 border-[var(--color-bronze)]'
              : 'text-gray-500 hover:text-[var(--color-midnight)]'
          }`}
        >
          <ChatIcon />
          Chat
        </button>
        <button
          onClick={() => setActiveTab('feedback')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
            activeTab === 'feedback'
              ? 'text-[var(--color-bronze)] border-b-2 border-[var(--color-bronze)]'
              : 'text-gray-500 hover:text-[var(--color-midnight)]'
          }`}
        >
          <AnalyzeIcon />
          Feedback
          {maxwellResponse?.feedback && (
            <span className="w-2 h-2 bg-[var(--color-bronze)] rounded-full" />
          )}
        </button>
      </div>

      {/* Session History Dropdown */}
      {showHistory && (
        <div className="border-b border-[var(--color-bronze)]/20 bg-white p-2 max-h-48 overflow-y-auto">
          <div className="flex justify-between items-center mb-2 px-2">
            <span className="text-xs text-[var(--color-bronze)]">Recent Sessions</span>
            <button
              onClick={startNewSession}
              className="text-xs text-[var(--color-bronze)] hover:underline"
            >
              + New
            </button>
          </div>
          {coachSessions.length === 0 ? (
            <div className="text-sm text-gray-500 px-2 py-4 text-center">No sessions yet</div>
          ) : (
            coachSessions.slice(0, 5).map((session) => (
              <button
                key={session.id}
                onClick={() => loadSession(session.id)}
                className={`w-full text-left px-2 py-2 rounded text-sm hover:bg-[var(--color-bronze)]/10 ${
                  currentSession?.id === session.id ? 'bg-[var(--color-bronze)]/15' : ''
                }`}
              >
                <div className="font-medium text-[var(--color-midnight)] truncate">
                  {session.title}
                </div>
                <div className="text-xs text-gray-500">{session.message_count} messages</div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Quick Actions (when text is selected) */}
      {selectedText && showQuickActions && activeTab === 'chat' && (
        <div className="px-4 py-3 border-b border-[var(--color-bronze)]/10 bg-[var(--color-bronze)]/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[var(--color-bronze)] font-medium">
              Text selected ({selectedText.length} chars)
            </span>
            <button
              onClick={() => setShowQuickActions(false)}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Hide
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={runFullAnalysis}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[var(--color-bronze)] text-white rounded-full hover:bg-[var(--color-bronze)]/90 disabled:opacity-50"
            >
              <AnalyzeIcon />
              Full Analysis
            </button>
            <button
              onClick={() => runQuickCheck('style')}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs border border-[var(--color-bronze)]/30 text-[var(--color-bronze)] rounded-full hover:bg-[var(--color-bronze)]/10 disabled:opacity-50"
            >
              Style
            </button>
            <button
              onClick={() => runQuickCheck('dialogue')}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs border border-[var(--color-bronze)]/30 text-[var(--color-bronze)] rounded-full hover:bg-[var(--color-bronze)]/10 disabled:opacity-50"
            >
              Dialogue
            </button>
            <button
              onClick={() => runQuickCheck('continuity')}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs border border-[var(--color-bronze)]/30 text-[var(--color-bronze)] rounded-full hover:bg-[var(--color-bronze)]/10 disabled:opacity-50"
            >
              Continuity
            </button>
          </div>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'chat' ? (
          <ChatView
            currentSession={currentSession}
            currentMessages={currentMessages}
            maxwellHistory={maxwellConversationHistory}
            isLoading={isLoading}
            messagesEndRef={messagesEndRef}
            onStartSession={startNewSession}
            apiKey={apiKey}
          />
        ) : (
          <FeedbackView
            feedback={maxwellResponse?.feedback}
            response={maxwellResponse}
            isLoading={isMaxwellLoading}
            selectedText={selectedText}
            onAnalyze={runFullAnalysis}
            apiKey={apiKey}
          />
        )}
      </div>

      {/* Error Display */}
      {displayError && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200 text-red-600 text-sm">
          {displayError}
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-[var(--color-bronze)]/20 p-3 bg-white">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              currentSession
                ? 'Ask Maxwell anything...'
                : 'Chat with Maxwell (or start a session for history)'
            }
            className="flex-1 resize-none rounded-lg border border-[var(--color-bronze)]/30 px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-bronze)] min-h-[44px] max-h-[120px]"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-3 py-2 bg-[var(--color-bronze)] text-white rounded-lg hover:bg-[var(--color-bronze)]/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <SendIcon />
          </button>
        </div>
        {!currentSession && (
          <button
            onClick={startNewSession}
            className="mt-2 text-xs text-[var(--color-bronze)] hover:underline"
          >
            Start a session to save conversation history
          </button>
        )}
      </div>
    </div>
  );
};

// Chat View Component
interface ChatViewProps {
  currentSession: any;
  currentMessages: any[];
  maxwellHistory: Array<{ role: 'user' | 'assistant'; content: string }>;
  isLoading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  onStartSession: () => void;
  apiKey: string;
}

const ChatView: React.FC<ChatViewProps> = ({
  currentSession,
  currentMessages,
  maxwellHistory,
  isLoading,
  messagesEndRef,
  onStartSession,
  apiKey,
}) => {
  const messages = currentSession ? currentMessages : maxwellHistory;

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="text-[var(--color-bronze)] text-4xl mb-4">
          <SparkleIcon />
        </div>
        <h3 className="text-lg font-medium text-[var(--color-midnight)] mb-2">
          Hi, I'm Maxwell
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Your writing coach and editor. Ask me about your story, get feedback on passages, or
          explore craft concepts together.
        </p>
        <div className="space-y-2 text-sm text-gray-500">
          <p>"Is this dialogue working?"</p>
          <p>"Explain show vs tell"</p>
          <p>"Who is my main character?"</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div
          key={msg.id || idx}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              msg.role === 'user'
                ? 'bg-[var(--color-bronze)] text-white'
                : 'bg-white border border-[var(--color-bronze)]/20 text-[var(--color-midnight)]'
            }`}
          >
            <div className="whitespace-pre-wrap">{msg.content}</div>
            {msg.role === 'assistant' && msg.cost > 0 && (
              <div className="text-xs text-gray-400 mt-1">${msg.cost.toFixed(4)}</div>
            )}
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-white border border-[var(--color-bronze)]/20 rounded-lg px-4 py-2">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce" />
              <div
                className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce"
                style={{ animationDelay: '0.1s' }}
              />
              <div
                className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce"
                style={{ animationDelay: '0.2s' }}
              />
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

// Feedback View Component
interface FeedbackViewProps {
  feedback?: MaxwellFeedback;
  response?: MaxwellResponse | null;
  isLoading: boolean;
  selectedText?: string;
  onAnalyze: () => void;
  apiKey: string;
}

const FeedbackView: React.FC<FeedbackViewProps> = ({
  feedback,
  response,
  isLoading,
  selectedText,
  onAnalyze,
  apiKey,
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="w-8 h-8 border-2 border-[var(--color-bronze)] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm text-gray-600">Maxwell is analyzing your writing...</p>
      </div>
    );
  }

  if (!feedback) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="text-[var(--color-bronze)] text-4xl mb-4">
          <AnalyzeIcon />
        </div>
        <h3 className="text-lg font-medium text-[var(--color-midnight)] mb-2">Writing Feedback</h3>
        <p className="text-sm text-gray-600 mb-4">
          {selectedText
            ? 'Click "Full Analysis" to get comprehensive feedback on your selected text.'
            : 'Select some text in the editor, then ask Maxwell for feedback.'}
        </p>
        {selectedText && (
          <button
            onClick={onAnalyze}
            disabled={!apiKey}
            className="px-4 py-2 bg-[var(--color-bronze)] text-white rounded-lg hover:bg-[var(--color-bronze)]/90 disabled:opacity-50"
          >
            Analyze Selection
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Narrative Summary */}
      <div className="bg-white rounded-lg border border-[var(--color-bronze)]/20 p-4">
        <div className="text-sm text-[var(--color-midnight)] whitespace-pre-wrap">
          {feedback.narrative}
        </div>
        {response && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
            <span>
              {response.agents_consulted.length} agents consulted
            </span>
            <span>·</span>
            <span>${response.cost.toFixed(4)}</span>
            <span>·</span>
            <span>{response.execution_time_ms}ms</span>
          </div>
        )}
      </div>

      {/* Highlights */}
      {feedback.highlights.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-[var(--color-midnight)] mb-2 flex items-center gap-2">
            <span className="text-green-500">✓</span> What's Working
          </h4>
          <div className="space-y-2">
            {feedback.highlights.map((h, i) => (
              <div key={i} className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
                <span className="font-medium text-green-700">{h.aspect}:</span>{' '}
                <span className="text-green-800">{h.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Priorities */}
      {feedback.priorities.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-[var(--color-midnight)] mb-2">Suggestions</h4>
          <div className="space-y-2">
            {feedback.priorities.map((p, i) => (
              <div
                key={i}
                className={`rounded-lg p-3 text-sm border ${
                  p.severity === 'high'
                    ? 'bg-orange-50 border-orange-200'
                    : p.severity === 'medium'
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="font-medium mb-1">{p.text}</div>
                {p.why_it_matters && (
                  <div className="text-xs text-gray-600 mb-1">
                    <strong>Why:</strong> {p.why_it_matters}
                  </div>
                )}
                {p.suggestion && (
                  <div className="text-xs text-gray-600">
                    <strong>Try:</strong> {p.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Teaching Moments */}
      {feedback.teaching_moments.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-[var(--color-midnight)] mb-2 flex items-center gap-2">
            <LightbulbIcon /> Craft Tips
          </h4>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <ul className="text-sm text-purple-800 space-y-1">
              {feedback.teaching_moments.map((tip, i) => (
                <li key={i}>• {tip}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {feedback.summary && (
        <div className="text-center text-sm text-gray-500 pt-2 border-t border-gray-100">
          {feedback.summary}
        </div>
      )}
    </div>
  );
};

export default MaxwellPanel;
