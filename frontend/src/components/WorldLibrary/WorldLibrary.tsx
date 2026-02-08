/**
 * WorldLibrary Component
 * Main library view showing all worlds with navigation to series and manuscripts
 */

import { useState, useEffect, lazy, Suspense } from 'react';
import { useWorldStore } from '../../stores/worldStore';
import { toast } from '../../stores/toastStore';
import type { World, Series } from '../../types/world';
import WorldCard from './WorldCard';
import CreateWorldModal from './CreateWorldModal';
import SeriesExplorer from './SeriesExplorer';
import MoveManuscriptModal from './MoveManuscriptModal';

const WorldWikiBrowser = lazy(() => import('../Wiki/WorldWikiBrowser'));

interface WorldLibraryProps {
  onOpenManuscript: (manuscriptId: string) => void;
  onSettingsClick?: () => void;
  onCreateWithWizard?: () => void;
  onBackToManuscripts?: () => void;
  embedded?: boolean;
}

type ViewMode = 'worlds' | 'series' | 'manuscripts';

export default function WorldLibrary({
  onOpenManuscript,
  onSettingsClick,
  onCreateWithWizard,
  onBackToManuscripts,
  embedded = false,
}: WorldLibraryProps) {
  const {
    worlds,
    currentWorldId,
    currentSeriesId,
    fetchWorlds,
    fetchSeries,
    fetchSeriesManuscripts,
    setCurrentWorld,
    setCurrentSeries,
    getCurrentWorld,
    getCurrentSeries,
    getSeriesForWorld,
    getManuscriptsForSeries,
    isLoading,
    error,
    clearError,
  } = useWorldStore();

  const [showCreateWorldModal, setShowCreateWorldModal] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('worlds');
  const [worldTab, setWorldTab] = useState<'series' | 'wiki'>('series');
  const [moveManuscriptId, setMoveManuscriptId] = useState<string | null>(null);

  // Fetch worlds on mount
  useEffect(() => {
    fetchWorlds();
  }, [fetchWorlds]);

  // Fetch series when a world is selected
  useEffect(() => {
    if (currentWorldId) {
      fetchSeries(currentWorldId);
    }
  }, [currentWorldId, fetchSeries]);

  // Fetch manuscripts when a series is selected
  useEffect(() => {
    if (currentSeriesId) {
      fetchSeriesManuscripts(currentSeriesId);
    }
  }, [currentSeriesId, fetchSeriesManuscripts]);

  const handleSelectWorld = (world: World) => {
    setCurrentWorld(world.id);
    setWorldTab('series');
    setViewMode('series');
  };

  const handleSelectSeries = (series: Series) => {
    setCurrentSeries(series.id);
    setViewMode('manuscripts');
  };

  const handleBackToWorlds = () => {
    setCurrentWorld(null);
    setViewMode('worlds');
  };

  const handleBackToSeries = () => {
    setCurrentSeries(null);
    setViewMode('series');
  };

  const currentWorld = getCurrentWorld();
  const currentSeries = getCurrentSeries();
  const seriesInWorld = currentWorldId ? getSeriesForWorld(currentWorldId) : [];
  const manuscriptsInSeries = currentSeriesId ? getManuscriptsForSeries(currentSeriesId) : [];

  // Format date helper
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Breadcrumb component
  const Breadcrumb = () => (
    <nav className="flex items-center gap-2 text-sm font-sans text-faded-ink mb-6">
      <button
        onClick={handleBackToWorlds}
        className={`hover:text-bronze transition-colors ${viewMode === 'worlds' ? 'text-midnight font-medium' : ''}`}
      >
        Library
      </button>
      {currentWorld && (
        <>
          <span className="text-slate-ui">/</span>
          <button
            onClick={handleBackToSeries}
            className={`hover:text-bronze transition-colors ${viewMode === 'series' ? 'text-midnight font-medium' : ''}`}
          >
            {currentWorld.name}
          </button>
        </>
      )}
      {currentSeries && (
        <>
          <span className="text-slate-ui">/</span>
          <span className="text-midnight font-medium">{currentSeries.name}</span>
        </>
      )}
    </nav>
  );

  return (
    <div className={embedded ? 'bg-vellum' : 'min-h-screen bg-vellum'}>
      {/* Header — hidden in embedded mode */}
      {!embedded && (
        <header className="border-b border-slate-ui bg-white px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-serif font-bold text-midnight tracking-tight">
                MAXWELL
              </h1>
              <span className="text-sm text-faded-ink font-sans">World Library</span>
            </div>
            <div className="flex items-center gap-4">
              {onBackToManuscripts && (
                <button
                  onClick={onBackToManuscripts}
                  className="flex items-center gap-2 px-4 py-2 text-faded-ink hover:text-midnight hover:bg-slate-ui/20 transition-colors rounded-sm"
                >
                  <span className="text-lg">&#x1F4DA;</span>
                  <span className="font-sans text-sm font-medium">All Manuscripts</span>
                </button>
              )}
              {onSettingsClick && (
                <button
                  onClick={onSettingsClick}
                  className="flex items-center gap-2 px-4 py-2 text-faded-ink hover:text-midnight hover:bg-slate-ui/20 transition-colors rounded-sm"
                  title="Settings"
                >
                  <span className="text-xl">&#x2699;&#xFE0F;</span>
                  <span className="font-sans text-sm font-medium">Settings</span>
                </button>
              )}
            </div>
          </div>
        </header>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        <Breadcrumb />

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-redline/10 border border-redline rounded-sm">
            <div className="flex items-center justify-between">
              <p className="text-redline font-sans">{error}</p>
              <button
                onClick={clearError}
                className="text-redline hover:text-redline/70 transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Worlds View */}
        {viewMode === 'worlds' && (
          <>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-serif font-bold text-midnight mb-2">Your Worlds</h2>
                <p className="text-faded-ink font-sans">
                  {worlds.length === 0
                    ? 'Create your first world to organize your writing'
                    : `${worlds.length} ${worlds.length === 1 ? 'world' : 'worlds'}`}
                </p>
              </div>
              <button
                onClick={() => setShowCreateWorldModal(true)}
                className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                style={{ borderRadius: '2px' }}
              >
                + New World
              </button>
            </div>

            {isLoading ? (
              <div className="text-center py-20">
                <div className="text-4xl mb-4 text-bronze">&#x23F3;</div>
                <p className="text-faded-ink font-sans">Loading worlds...</p>
              </div>
            ) : worlds.length === 0 ? (
              <div className="text-center py-20">
                <div className="text-6xl mb-6 text-bronze">&#x1F30D;</div>
                <h3 className="text-2xl font-serif font-bold text-midnight mb-3">No Worlds Yet</h3>
                <p className="text-faded-ink font-sans mb-8 max-w-md mx-auto">
                  Worlds help you organize manuscripts that share the same universe, characters, and
                  lore. Create one to get started.
                </p>
                <button
                  onClick={() => setShowCreateWorldModal(true)}
                  className="px-8 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                  style={{ borderRadius: '2px' }}
                >
                  Create Your First World
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {worlds.map((world) => (
                  <WorldCard key={world.id} world={world} onSelect={() => handleSelectWorld(world)} />
                ))}
              </div>
            )}
          </>
        )}

        {/* Series/Wiki View (when a world is selected but no series yet) */}
        {viewMode === 'series' && currentWorld && (
          <>
            {/* Tab Bar */}
            <div className="flex gap-1 mb-6 border-b border-slate-ui">
              <button
                onClick={() => setWorldTab('series')}
                className={`px-6 py-3 font-sans text-sm font-medium transition-colors border-b-2 -mb-px ${
                  worldTab === 'series'
                    ? 'border-bronze text-bronze'
                    : 'border-transparent text-faded-ink hover:text-midnight'
                }`}
              >
                Series
              </button>
              <button
                onClick={() => setWorldTab('wiki')}
                className={`px-6 py-3 font-sans text-sm font-medium transition-colors border-b-2 -mb-px ${
                  worldTab === 'wiki'
                    ? 'border-bronze text-bronze'
                    : 'border-transparent text-faded-ink hover:text-midnight'
                }`}
              >
                Wiki
              </button>
            </div>

            {worldTab === 'series' ? (
              <SeriesExplorer
                world={currentWorld}
                series={seriesInWorld}
                onSelectSeries={handleSelectSeries}
                onBack={handleBackToWorlds}
                isLoading={isLoading}
              />
            ) : (
              <Suspense fallback={
                <div className="text-center py-20">
                  <div className="text-4xl mb-4 text-bronze">&#x23F3;</div>
                  <p className="text-faded-ink font-sans">Loading Wiki...</p>
                </div>
              }>
                <WorldWikiBrowser world={currentWorld} />
              </Suspense>
            )}
          </>
        )}

        {/* Manuscripts View */}
        {viewMode === 'manuscripts' && currentWorld && currentSeries && (
          <>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-serif font-bold text-midnight mb-2">
                  {currentSeries.name}
                </h2>
                <p className="text-faded-ink font-sans">
                  {manuscriptsInSeries.length === 0
                    ? 'No manuscripts in this series yet'
                    : `${manuscriptsInSeries.length} ${
                        manuscriptsInSeries.length === 1 ? 'manuscript' : 'manuscripts'
                      }`}
                </p>
              </div>
              {onCreateWithWizard && (
                <button
                  onClick={onCreateWithWizard}
                  className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                  style={{ borderRadius: '2px' }}
                >
                  + New Manuscript
                </button>
              )}
            </div>

            {isLoading ? (
              <div className="text-center py-20">
                <div className="text-4xl mb-4 text-bronze">&#x23F3;</div>
                <p className="text-faded-ink font-sans">Loading manuscripts...</p>
              </div>
            ) : manuscriptsInSeries.length === 0 ? (
              <div className="text-center py-20">
                <div className="text-6xl mb-6 text-bronze">&#x1F4D6;</div>
                <h3 className="text-2xl font-serif font-bold text-midnight mb-3">
                  No Manuscripts Yet
                </h3>
                <p className="text-faded-ink font-sans mb-8 max-w-md mx-auto">
                  This series is empty. Create a new manuscript or assign existing ones to this
                  series.
                </p>
                {onCreateWithWizard && (
                  <button
                    onClick={onCreateWithWizard}
                    className="px-8 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                    style={{ borderRadius: '2px' }}
                  >
                    Create Manuscript
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {manuscriptsInSeries.map((manuscript) => (
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
                      <p>{(manuscript.word_count || 0).toLocaleString()} words</p>
                      <p>Updated {formatDate(manuscript.updated_at)}</p>
                    </div>
                    <div className="flex gap-2">
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
                          setMoveManuscriptId(manuscript.id);
                        }}
                        className="px-3 py-2 border border-slate-ui text-faded-ink hover:text-midnight hover:border-bronze font-sans text-sm transition-colors"
                        style={{ borderRadius: '2px' }}
                        title="Move to another world/series"
                      >
                        Move
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Create World Modal */}
      {showCreateWorldModal && (
        <CreateWorldModal
          onClose={() => setShowCreateWorldModal(false)}
          onCreated={(world) => {
            toast.success(`World "${world.name}" created!`);
            handleSelectWorld(world);
          }}
        />
      )}

      {/* Move Manuscript Modal */}
      {moveManuscriptId && (
        <MoveManuscriptModal
          manuscriptId={moveManuscriptId}
          currentWorldId={currentWorldId}
          onClose={() => setMoveManuscriptId(null)}
          onMoved={(result) => {
            setMoveManuscriptId(null);
            if (result.cross_world) {
              toast.success(
                `Manuscript moved! ${result.entries_copied} entries copied, ${result.entries_merged} merged.`
              );
            } else {
              toast.success('Manuscript moved to new series.');
            }
            // Refresh data
            if (currentSeriesId) fetchSeriesManuscripts(currentSeriesId);
          }}
        />
      )}
    </div>
  );
}
