/**
 * ManuscriptLibrary Component
 * Displays all saved manuscripts with create/open/delete functionality
 */

import { useState } from 'react';
import { useManuscriptStore } from '../stores/manuscriptStore';
import analytics from '../lib/analytics';

interface ManuscriptLibraryProps {
  onOpenManuscript: (manuscriptId: string) => void;
  onSettingsClick?: () => void;
}

export default function ManuscriptLibrary({ onOpenManuscript, onSettingsClick }: ManuscriptLibraryProps) {
  const { manuscripts, createManuscript, deleteManuscript } = useManuscriptStore();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const handleCreate = () => {
    const title = newTitle || 'Untitled Manuscript';
    const manuscript = createManuscript(title);

    // Track manuscript creation
    analytics.manuscriptCreated(manuscript.id, title);

    setNewTitle('');
    setShowCreateDialog(false);
    onOpenManuscript(manuscript.id);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleDelete = (id: string, title: string) => {
    if (confirm(`Delete "${title}"? This cannot be undone.`)) {
      deleteManuscript(id);

      // Track manuscript deletion
      analytics.manuscriptDeleted(id);
    }
  };

  return (
    <div className="min-h-screen bg-vellum">
      {/* Header */}
      <header className="border-b border-slate-ui bg-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-serif font-bold text-midnight tracking-tight">
              MAXWELL
            </h1>
            <span className="text-sm text-faded-ink font-sans">
              The Author's Study
            </span>
          </div>
          {onSettingsClick && (
            <button
              onClick={onSettingsClick}
              className="flex items-center gap-2 px-4 py-2 text-faded-ink hover:text-midnight hover:bg-slate-ui/20 transition-colors rounded-sm"
              title="Settings"
            >
              <span className="text-xl">⚙️</span>
              <span className="font-sans text-sm font-medium">Settings</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Header with Create Button */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-serif font-bold text-midnight mb-2">
              Your Manuscripts
            </h2>
            <p className="text-faded-ink font-sans">
              {manuscripts.length === 0
                ? 'Begin your first manuscript'
                : `${manuscripts.length} ${manuscripts.length === 1 ? 'manuscript' : 'manuscripts'}`}
            </p>
          </div>
          <button
            onClick={() => setShowCreateDialog(true)}
            className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
            style={{ borderRadius: '2px' }}
          >
            + New Manuscript
          </button>
        </div>

        {/* Manuscript Grid */}
        {manuscripts.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-6 text-bronze">📝</div>
            <h3 className="text-2xl font-serif font-bold text-midnight mb-3">
              No Manuscripts Yet
            </h3>
            <p className="text-faded-ink font-sans mb-8">
              Create your first manuscript to begin writing
            </p>
            <button
              onClick={() => setShowCreateDialog(true)}
              className="px-8 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
              style={{ borderRadius: '2px' }}
            >
              Begin Writing
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {manuscripts.map((manuscript) => (
              <div
                key={manuscript.id}
                className="bg-white border border-slate-ui p-6 hover:shadow-book transition-shadow cursor-pointer group"
                style={{ borderRadius: '2px' }}
                onClick={() => onOpenManuscript(manuscript.id)}
              >
                <h3 className="text-xl font-serif font-bold text-midnight mb-2 group-hover:text-bronze transition-colors">
                  {manuscript.title}
                </h3>
                <div className="space-y-1 text-sm font-sans text-faded-ink mb-4">
                  <p>{manuscript.wordCount.toLocaleString()} words</p>
                  <p>Updated {formatDate(manuscript.updatedAt)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenManuscript(manuscript.id);
                    }}
                    className="flex-1 px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
                    style={{ borderRadius: '2px' }}
                  >
                    Open
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(manuscript.id, manuscript.title);
                    }}
                    className="px-4 py-2 border border-redline text-redline hover:bg-redline hover:text-white font-sans text-sm font-medium uppercase tracking-button transition-colors"
                    style={{ borderRadius: '2px' }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white p-8 max-w-md w-full shadow-book"
            style={{ borderRadius: '2px' }}
          >
            <h3 className="text-2xl font-serif font-bold text-midnight mb-4">
              New Manuscript
            </h3>
            <p className="text-faded-ink font-sans mb-6 text-sm">
              Give your manuscript a title. You can always change it later.
            </p>
            <input
              type="text"
              placeholder="Untitled Manuscript"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              className="w-full px-4 py-3 border border-slate-ui text-midnight font-sans mb-6 focus:outline-none focus:border-bronze"
              style={{ borderRadius: '2px' }}
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={handleCreate}
                className="flex-1 px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setNewTitle('');
                }}
                className="px-6 py-3 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
