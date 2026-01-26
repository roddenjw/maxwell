/**
 * SmartCoachPanel - Conversational AI Writing Coach
 *
 * A sliding panel that provides conversational coaching for writers.
 * Features:
 * - Session-based conversations with history
 * - Context-aware responses (knows current manuscript, chapter)
 * - Tool-augmented answers (queries Codex, Timeline, etc.)
 * - Cost tracking per session
 */

import React, { useState, useRef, useEffect } from 'react';
import { useAgentStore } from '@/stores/agentStore';
import { agentApi } from '@/lib/api';

// Icons (using simple SVG inline for now)
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

const NewChatIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 5v14M5 12h14" />
  </svg>
);

const HistoryIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" />
  </svg>
);

interface SmartCoachPanelProps {
  manuscriptId?: string;
  chapterId?: string;
  chapterTitle?: string;
  selectedText?: string;
  userId: string;
  apiKey: string;
}

export const SmartCoachPanel: React.FC<SmartCoachPanelProps> = ({
  manuscriptId,
  chapterId,
  chapterTitle,
  selectedText,
  userId,
  apiKey,
}) => {
  const {
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
  } = useAgentStore();

  const [inputMessage, setInputMessage] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages]);

  // Load sessions on mount
  useEffect(() => {
    if (isCoachPanelOpen && userId && apiKey) {
      loadSessions();
    }
  }, [isCoachPanelOpen, userId, manuscriptId]);

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
        title: chapterTitle ? `Coaching: ${chapterTitle}` : 'New Coaching Session',
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
    if (!inputMessage.trim() || !currentSession || isCoachLoading) return;
    if (!apiKey) {
      setError('Please configure your API key in Settings');
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Add user message optimistically
    const userMsg = {
      id: `temp-${Date.now()}`,
      role: 'user' as const,
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    addMessage(userMsg);

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

        // Update session cost
        setCurrentSession({
          ...currentSession,
          message_count: currentSession.message_count + 2,
          total_cost: currentSession.total_cost + response.data.cost,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setCoachLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isCoachPanelOpen) return null;

  return (
    <div
      className="fixed right-0 top-0 h-full w-96 bg-[var(--color-vellum)] border-l border-[var(--color-bronze)]/30 shadow-xl z-50 flex flex-col"
      style={{ fontFamily: 'var(--font-sans)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-bronze)]/20 bg-[var(--color-vellum-darker)]">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-[var(--color-midnight)]">
            Writing Coach
          </span>
          {currentSession && (
            <span className="text-xs text-[var(--color-bronze)]">
              ${currentSession.total_cost.toFixed(4)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-1.5 rounded hover:bg-[var(--color-bronze)]/10 text-[var(--color-bronze)]"
            title="Session History"
          >
            <HistoryIcon />
          </button>
          <button
            onClick={startNewSession}
            className="p-1.5 rounded hover:bg-[var(--color-bronze)]/10 text-[var(--color-bronze)]"
            title="New Session"
          >
            <NewChatIcon />
          </button>
          <button
            onClick={() => setCoachPanelOpen(false)}
            className="p-1.5 rounded hover:bg-[var(--color-bronze)]/10 text-[var(--color-midnight)]"
          >
            <CloseIcon />
          </button>
        </div>
      </div>

      {/* Session History Dropdown */}
      {showHistory && (
        <div className="border-b border-[var(--color-bronze)]/20 bg-white p-2 max-h-60 overflow-y-auto">
          <div className="text-xs text-[var(--color-bronze)] mb-2 px-2">Recent Sessions</div>
          {coachSessions.length === 0 ? (
            <div className="text-sm text-gray-500 px-2 py-4 text-center">
              No sessions yet. Start a new one!
            </div>
          ) : (
            coachSessions.map((session) => (
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
                <div className="text-xs text-gray-500 flex justify-between">
                  <span>{session.message_count} messages</span>
                  <span>${session.total_cost.toFixed(4)}</span>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!currentSession ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-[var(--color-bronze)] text-4xl mb-4">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-[var(--color-midnight)] mb-2">
              Your Writing Coach
            </h3>
            <p className="text-sm text-gray-600 mb-4 px-8">
              Ask questions about your story, get craft advice, or brainstorm ideas.
              I can look up characters, events, and more from your Codex.
            </p>
            <button
              onClick={startNewSession}
              disabled={!apiKey}
              className="px-4 py-2 bg-[var(--color-bronze)] text-white rounded-lg hover:bg-[var(--color-bronze)]/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Coaching Session
            </button>
            {!apiKey && (
              <p className="text-xs text-red-500 mt-2">
                Configure your API key in Settings first
              </p>
            )}
          </div>
        ) : currentMessages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="mb-2">Session started!</p>
            <p className="text-sm">
              Ask me anything about your story or writing craft.
            </p>
          </div>
        ) : (
          currentMessages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 ${
                  message.role === 'user'
                    ? 'bg-[var(--color-bronze)] text-white'
                    : 'bg-white border border-[var(--color-bronze)]/20 text-[var(--color-midnight)]'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                {message.role === 'assistant' && message.tools_used && message.tools_used.length > 0 && (
                  <div className="mt-1 pt-1 border-t border-[var(--color-bronze)]/10">
                    <span className="text-xs text-[var(--color-bronze)]">
                      Used: {message.tools_used.join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isCoachLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-[var(--color-bronze)]/20 rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce" />
                <span
                  className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <span
                  className="w-2 h-2 bg-[var(--color-bronze)] rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Input Area */}
      {currentSession && (
        <div className="border-t border-[var(--color-bronze)]/20 p-4 bg-white">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your story..."
              rows={1}
              className="flex-1 resize-none rounded-lg border border-[var(--color-bronze)]/30 px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-bronze)] bg-[var(--color-vellum)]"
              style={{ minHeight: '40px', maxHeight: '120px' }}
              disabled={isCoachLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isCoachLoading}
              className="p-2 rounded-lg bg-[var(--color-bronze)] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--color-bronze)]/90"
            >
              <SendIcon />
            </button>
          </div>
          {selectedText && (
            <div className="mt-2 text-xs text-gray-500">
              <span className="font-medium">Selected:</span>{' '}
              <span className="italic">"{selectedText.slice(0, 50)}..."</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SmartCoachPanel;
