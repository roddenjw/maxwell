/**
 * ManuscriptLibrary Component
 * Displays all saved manuscripts with create/open/delete functionality
 * Features: Tabbed view (Manuscripts/Worlds), Search, Sort, Inline Create, Styled Delete
 */

import { useState, useEffect, useMemo } from 'react';
import { useManuscriptStore } from '../stores/manuscriptStore';
import { toast } from '../stores/toastStore';
import analytics from '../lib/analytics';
import { ImportModal } from './Import';
import { WorldLibrary } from './WorldLibrary';

interface ManuscriptLibraryProps {
  onOpenManuscript: (manuscriptId: string) => void;
  onSettingsClick?: () => void;
  onCreateWithWizard?: () => void;
}

type LibraryTab = 'manuscripts' | 'worlds';
type SortOption = 'updated' | 'title' | 'wordCount';

export default function ManuscriptLibrary({ onOpenManuscript, onSettingsClick, onCreateWithWizard }: ManuscriptLibraryProps) {
  const { manuscripts, fetchManuscripts, createManuscript, deleteManuscript, isLoading, error } = useManuscriptStore();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [activeTab, setActiveTab] = useState<LibraryTab>('manuscripts');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('updated');

  // Inline quick create state
  const [showInlineCreate, setShowInlineCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Delete confirmation modal state
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);

  const handleImportComplete = async (manuscriptId: string) => {
    setShowImportModal(false);
    await fetchManuscripts();
    onOpenManuscript(manuscriptId);
  };

  // Fetch manuscripts from backend on mount
  useEffect(() => {
    fetchManuscripts();
  }, [fetchManuscripts]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleDelete = (id: string, title: string) => {
    setDeleteTarget({ id, title });
  };

  const confirmDelete = () => {
    if (deleteTarget) {
      deleteManuscript(deleteTarget.id);
      analytics.manuscriptDeleted(deleteTarget.id);
      setDeleteTarget(null);
    }
  };

  const handleQuickCreate = async () => {
    if (isCreating) return;
    try {
      setIsCreating(true);
      const manuscript = await createManuscript(newTitle.trim() || 'Untitled Manuscript');
      analytics.manuscriptCreated(manuscript.id, manuscript.title);
      setNewTitle('');
      setShowInlineCreate(false);
      onOpenManuscript(manuscript.id);
    } catch (error) {
      console.error('Failed to create manuscript:', error);
      toast.error('Failed to create manuscript. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  // Filter and sort manuscripts
  const filteredManuscripts = useMemo(() => {
    let result = [...manuscripts];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(m => m.title.toLowerCase().includes(query));
    }

    // Sort
    switch (sortBy) {
      case 'title':
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case 'wordCount':
        result.sort((a, b) => (b.wordCount || 0) - (a.wordCount || 0));
        break;
      case 'updated':
      default:
        result.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
        break;
    }

    return result;
  }, [manuscripts, searchQuery, sortBy]);

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
          <div className="flex items-center gap-3">
            {/* Tab Bar */}
            <div className="flex border-b-0">
              <button
                onClick={() => setActiveTab('manuscripts')}
                className={`px-4 py-2 font-sans text-sm font-medium transition-colors border-b-2 ${
                  activeTab === 'manuscripts'
                    ? 'border-bronze text-bronze'
                    : 'border-transparent text-faded-ink hover:text-midnight'
                }`}
              >
                All Manuscripts
                {activeTab === 'manuscripts' && manuscripts.length > 0 && (
                  <span className="ml-1.5 text-xs opacity-70">({manuscripts.length})</span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('worlds')}
                className={`px-4 py-2 font-sans text-sm font-medium transition-colors border-b-2 ${
                  activeTab === 'worlds'
                    ? 'border-bronze text-bronze'
                    : 'border-transparent text-faded-ink hover:text-midnight'
                }`}
              >
                Worlds
              </button>
            </div>
            {onSettingsClick && (
              <button
                onClick={onSettingsClick}
                className="flex items-center gap-2 px-4 py-2 text-faded-ink hover:text-midnight hover:bg-slate-ui/20 transition-colors rounded-sm ml-2"
                title="Settings"
              >
                <span className="text-xl">&#x2699;&#xFE0F;</span>
                <span className="font-sans text-sm font-medium">Settings</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Manuscripts Tab */}
      {activeTab === 'manuscripts' && (
        <main className="max-w-6xl mx-auto px-6 py-12">
          {/* Header with Create Button */}
          <div className="flex items-center justify-between mb-6">
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
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowImportModal(true)}
                className="px-6 py-3 border border-bronze text-bronze hover:bg-bronze hover:text-white font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Import
              </button>
              <button
                onClick={() => setShowCreateDialog(true)}
                className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                style={{ borderRadius: '2px' }}
              >
                + New Manuscript
              </button>
            </div>
          </div>

          {/* Search and Sort Bar */}
          {manuscripts.length > 0 && (
            <div className="flex items-center gap-4 mb-8">
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search manuscripts..."
                  className="w-full bg-white border border-slate-ui px-3 py-2 pl-9 text-sm font-sans"
                  style={{ borderRadius: '2px' }}
                />
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-faded-ink"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
              >
                <option value="updated">Last Updated</option>
                <option value="title">Title A-Z</option>
                <option value="wordCount">Word Count</option>
              </select>
            </div>
          )}

          {/* Manuscript Grid */}
          {isLoading ? (
            <div className="text-center py-20">
              <div className="text-4xl mb-4 text-bronze">&#x23F3;</div>
              <p className="text-faded-ink font-sans">Loading manuscripts...</p>
            </div>
          ) : error ? (
            <div className="text-center py-20">
              <div className="text-4xl mb-4 text-red-600">&#x26A0;&#xFE0F;</div>
              <h3 className="text-xl font-serif font-bold text-midnight mb-2">
                Failed to Load Manuscripts
              </h3>
              <p className="text-faded-ink font-sans mb-4">{error}</p>
              <button
                onClick={() => fetchManuscripts()}
                className="px-6 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Try Again
              </button>
            </div>
          ) : manuscripts.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-6 text-bronze">&#x1F4DD;</div>
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
          ) : filteredManuscripts.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-4xl mb-4 text-faded-ink">&#x1F50D;</div>
              <p className="text-faded-ink font-sans">
                No manuscripts match "{searchQuery}"
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredManuscripts.map((manuscript) => (
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
                    <p>{(manuscript.wordCount || 0).toLocaleString()} words</p>
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
      )}

      {/* Worlds Tab */}
      {activeTab === 'worlds' && (
        <WorldLibrary
          onOpenManuscript={onOpenManuscript}
          onCreateWithWizard={onCreateWithWizard}
          embedded
        />
      )}

      {/* Create Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-white p-8 max-w-2xl w-full shadow-book"
            style={{ borderRadius: '2px' }}
          >
            <h3 className="text-2xl font-serif font-bold text-midnight mb-4">
              Create New Manuscript
            </h3>
            <p className="text-faded-ink font-sans mb-6 text-sm">
              Choose how you'd like to start your manuscript
            </p>

            <div className="grid md:grid-cols-3 gap-4 mb-6">
              {/* Quick Create — Inline Form */}
              {showInlineCreate ? (
                <div className="p-6 border-2 border-bronze bg-bronze/5 rounded-sm">
                  <div className="text-4xl mb-3">&#x26A1;</div>
                  <h4 className="font-sans font-bold text-midnight text-lg mb-3">
                    Quick Create
                  </h4>
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleQuickCreate();
                      if (e.key === 'Escape') {
                        setShowInlineCreate(false);
                        setNewTitle('');
                      }
                    }}
                    placeholder="Manuscript title..."
                    className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans mb-3"
                    style={{ borderRadius: '2px' }}
                    autoFocus
                    disabled={isCreating}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleQuickCreate}
                      disabled={isCreating}
                      className="flex-1 px-3 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium transition-colors disabled:opacity-50"
                      style={{ borderRadius: '2px' }}
                    >
                      {isCreating ? 'Creating...' : 'Create'}
                    </button>
                    <button
                      onClick={() => {
                        setShowInlineCreate(false);
                        setNewTitle('');
                      }}
                      disabled={isCreating}
                      className="px-3 py-2 border border-slate-ui text-midnight font-sans text-sm transition-colors hover:bg-slate-ui/20"
                      style={{ borderRadius: '2px' }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowInlineCreate(true)}
                  className="p-6 border-2 border-slate-ui hover:border-bronze hover:shadow-lg transition-all text-left rounded-sm"
                >
                  <div className="text-4xl mb-3">&#x26A1;</div>
                  <h4 className="font-sans font-bold text-midnight text-lg mb-2">
                    Quick Create
                  </h4>
                  <p className="text-sm text-faded-ink">
                    Start with a blank manuscript. Perfect for experienced writers.
                  </p>
                </button>
              )}

              {/* Guided Setup */}
              {onCreateWithWizard && (
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    onCreateWithWizard();
                  }}
                  className="p-6 border-2 border-bronze bg-bronze/5 hover:border-bronze-dark hover:shadow-lg transition-all text-left rounded-sm"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="text-4xl">&#x1F3AF;</div>
                    <div className="text-xs bg-bronze text-white px-2 py-1 rounded-sm font-semibold">
                      RECOMMENDED
                    </div>
                  </div>
                  <h4 className="font-sans font-bold text-midnight text-lg mb-2">
                    Guided Setup
                  </h4>
                  <p className="text-sm text-faded-ink">
                    Create with story structure templates. Get plot beats and guidance.
                  </p>
                </button>
              )}

              {/* Import Existing */}
              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setShowImportModal(true);
                }}
                className="p-6 border-2 border-slate-ui hover:border-bronze hover:shadow-lg transition-all text-left rounded-sm"
              >
                <div className="text-4xl mb-3">&#x1F4E5;</div>
                <h4 className="font-sans font-bold text-midnight text-lg mb-2">
                  Import Existing
                </h4>
                <p className="text-sm text-faded-ink">
                  Import from Word, PDF, Markdown, or other formats.
                </p>
              </button>
            </div>

            <button
              onClick={() => {
                setShowCreateDialog(false);
                setShowInlineCreate(false);
                setNewTitle('');
              }}
              className="w-full px-6 py-3 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors"
              style={{ borderRadius: '2px' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-midnight bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div
            className="bg-vellum p-8 max-w-md w-full shadow-book"
            style={{ borderRadius: '2px' }}
          >
            <h3 className="text-xl font-serif font-bold text-midnight mb-3">
              Delete Manuscript
            </h3>
            <p className="text-faded-ink font-sans mb-6">
              Are you sure you want to delete <strong className="text-midnight">"{deleteTarget.title}"</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 px-6 py-3 border border-slate-ui text-midnight hover:bg-slate-ui font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-6 py-3 bg-redline hover:bg-redline/90 text-white font-sans font-medium uppercase tracking-button transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <ImportModal
          onClose={() => setShowImportModal(false)}
          onImportComplete={handleImportComplete}
        />
      )}
    </div>
  );
}
