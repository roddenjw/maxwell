/**
 * SessionHistoryPanel - Browse and resume previous brainstorming sessions
 * Shows session history grouped by type with metadata and actions
 */

import { useEffect, useState } from 'react';
import { useBrainstormStore } from '@/stores/brainstormStore';
import type { BrainstormSession } from '@/types/brainstorm';

interface SessionHistoryPanelProps {
  manuscriptId: string;
  onResumeSession?: (session: BrainstormSession) => void;
}

export default function SessionHistoryPanel({ manuscriptId, onResumeSession }: SessionHistoryPanelProps) {
  const {
    sessions,
    loadManuscriptSessions,
    setCurrentSession,
    getSessionIdeas,
  } = useBrainstormStore();

  const [isLoading, setIsLoading] = useState(true);
  const [groupBy, setGroupBy] = useState<'type' | 'date'>('type');

  // Load sessions on mount
  useEffect(() => {
    const loadSessions = async () => {
      try {
        setIsLoading(true);
        await loadManuscriptSessions(manuscriptId);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSessions();
  }, [manuscriptId, loadManuscriptSessions]);

  const handleResumeSession = (session: BrainstormSession) => {
    setCurrentSession(session);
    onResumeSession?.(session);
  };

  // Group sessions by type
  const sessionsByType = sessions.reduce((acc, session) => {
    const type = session.session_type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(session);
    return acc;
  }, {} as Record<string, BrainstormSession[]>);

  // Sort sessions by date (newest first)
  const sortedSessions = [...sessions].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'CHARACTER':
        return '👤 Characters';
      case 'PLOT_BEAT':
        return '📖 Plots';
      case 'WORLD':
        return '🌍 Locations';
      case 'CONFLICT':
        return '⚔️ Conflicts';
      default:
        return type;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const SessionCard = ({ session }: { session: BrainstormSession }) => {
    const ideas = getSessionIdeas(session.id);

    return (
      <div className="p-3 bg-white border border-gray-200 rounded-md hover:border-blue-300 transition-colors">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium text-gray-900">
                {getTypeLabel(session.session_type)}
              </span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                session.status === 'IN_PROGRESS'
                  ? 'bg-blue-100 text-blue-700'
                  : session.status === 'COMPLETED'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {session.status}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              {formatDate(session.created_at)} • {ideas.length} idea{ideas.length !== 1 ? 's' : ''}
            </div>
          </div>
          <button
            onClick={() => handleResumeSession(session)}
            className="px-3 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
          >
            Continue
          </button>
        </div>

        {/* Context preview */}
        {session.context_data?.technique && (
          <div className="text-xs text-gray-600 truncate">
            {session.context_data.technique}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Loading sessions...</p>
        </div>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-4xl mb-2">💭</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No Sessions Yet</h3>
          <p className="text-sm text-gray-600">
            Start generating ideas to create your first brainstorming session
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Session History
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setGroupBy('type')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              groupBy === 'type'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            By Type
          </button>
          <button
            onClick={() => setGroupBy('date')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              groupBy === 'date'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            By Date
          </button>
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {groupBy === 'type' ? (
          // Group by type
          Object.entries(sessionsByType).map(([type, typeSessions]) => (
            <div key={type}>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">
                {getTypeLabel(type)}
              </h4>
              <div className="space-y-2">
                {typeSessions
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .map((session) => (
                    <SessionCard key={session.id} session={session} />
                  ))}
              </div>
            </div>
          ))
        ) : (
          // Show all by date
          <div className="space-y-2">
            {sortedSessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
