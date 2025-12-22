/**
 * Time Machine - Version Control UI
 * Allows writers to browse snapshots, compare versions, and restore previous states
 */

import { useState, useEffect } from 'react';
import { versioningApi, type Snapshot } from '../../lib/api';
import HistorySlider from './HistorySlider';
import SnapshotCard from './SnapshotCard';
import DiffViewer from './DiffViewer';

interface TimeMachineProps {
  manuscriptId: string;
  currentContent: string;
  onRestore: (content: string) => void;
  onClose: () => void;
}

export default function TimeMachine({
  manuscriptId,
  currentContent,
  onRestore,
  onClose,
}: TimeMachineProps) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [diffHtml, setDiffHtml] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load snapshots on mount
  useEffect(() => {
    loadSnapshots();
  }, [manuscriptId]);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await versioningApi.listSnapshots(manuscriptId);
      setSnapshots(data.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load snapshots');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSnapshot = (snapshot: Snapshot) => {
    setSelectedSnapshot(snapshot);
    setShowDiff(false);
  };

  const handleShowDiff = async (snapshot: Snapshot) => {
    if (!snapshots.length) return;

    try {
      // Compare with the next snapshot (or current if it's the latest)
      const currentIndex = snapshots.findIndex(s => s.id === snapshot.id);
      const olderSnapshot = snapshots[currentIndex + 1];

      if (!olderSnapshot) {
        alert('No older version to compare with');
        return;
      }

      const diff = await versioningApi.getDiff({
        manuscript_id: manuscriptId,
        snapshot_id_old: olderSnapshot.id,
        snapshot_id_new: snapshot.id,
      });

      if (!diff.diff_html || diff.diff_html.trim().length === 0) {
        alert('No changes detected between these versions');
        return;
      }

      setDiffHtml(diff.diff_html);
      setShowDiff(true);
      setSelectedSnapshot(snapshot);
    } catch (err) {
      alert('Failed to generate diff: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleRestore = async (snapshot: Snapshot) => {
    if (!confirm(`Restore to "${snapshot.label || 'snapshot'}"? Your current work will be backed up.`)) {
      return;
    }

    try {
      const result = await versioningApi.restoreSnapshot({
        manuscript_id: manuscriptId,
        snapshot_id: snapshot.id,
        create_backup: true,
      });

      onRestore(result.content);
      await loadSnapshots(); // Reload to show new backup snapshot
      alert('✅ Snapshot restored! Your previous work was saved as a backup.');
    } catch (err) {
      alert('Failed to restore: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleCreateSnapshot = async () => {
    const label = prompt('Enter a label for this snapshot:');
    if (!label) return;

    try {
      await versioningApi.createSnapshot({
        manuscript_id: manuscriptId,
        content: currentContent,
        trigger_type: 'MANUAL',
        label,
        description: '',
        word_count: currentContent.split(/\s+/).length,
      });

      await loadSnapshots();
      alert('✅ Snapshot created!');
    } catch (err) {
      alert('Failed to create snapshot: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-midnight/50 flex items-center justify-center z-50">
        <div className="bg-vellum p-8 rounded-lg shadow-xl">
          <p className="text-midnight font-sans">Loading snapshots...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-midnight/50 flex items-center justify-center z-50 p-4">
      <div className="bg-vellum rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-slate-ui p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-garamond font-bold text-midnight">Time Machine</h2>
            <p className="text-sm text-faded-ink font-sans mt-1">
              Browse and restore previous versions of your manuscript
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight transition-colors font-sans text-2xl leading-none"
            title="Close Time Machine"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Sidebar - Snapshot List */}
          <div className="w-80 border-r border-slate-ui overflow-y-auto">
            <div className="p-4 border-b border-slate-ui">
              <button
                onClick={handleCreateSnapshot}
                className="w-full bg-bronze text-white px-4 py-2 rounded font-sans text-sm hover:bg-bronze/90 transition-colors"
              >
                + Create Snapshot
              </button>
            </div>

            {error && (
              <div className="p-4 bg-redline/10 border-l-4 border-redline text-redline text-sm font-sans">
                {error}
              </div>
            )}

            {snapshots.length === 0 ? (
              <div className="p-8 text-center text-faded-ink font-sans text-sm">
                No snapshots yet. Create one to start tracking versions!
              </div>
            ) : (
              <div className="p-4 space-y-3">
                {snapshots.map((snapshot) => (
                  <SnapshotCard
                    key={snapshot.id}
                    snapshot={snapshot}
                    isSelected={selectedSnapshot?.id === snapshot.id}
                    onSelect={() => handleSelectSnapshot(snapshot)}
                    onShowDiff={() => handleShowDiff(snapshot)}
                    onRestore={() => handleRestore(snapshot)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Main Area - Timeline or Diff Viewer */}
          <div className="flex-1 overflow-y-auto p-6">
            {showDiff && diffHtml ? (
              <DiffViewer
                diffHtml={diffHtml}
                oldLabel={snapshots.find(s => s.id === selectedSnapshot?.id) ? 'Previous' : 'Older Version'}
                newLabel={selectedSnapshot?.label || 'Selected Version'}
                onClose={() => setShowDiff(false)}
              />
            ) : selectedSnapshot ? (
              <div className="max-w-3xl mx-auto">
                <h3 className="text-xl font-garamond font-bold text-midnight mb-4">
                  Snapshot Details
                </h3>
                <div className="bg-white rounded-lg border border-slate-ui p-6 space-y-4">
                  <div>
                    <label className="text-xs font-sans text-faded-ink uppercase">Label</label>
                    <p className="text-lg font-garamond text-midnight">
                      {selectedSnapshot.label || 'Untitled'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-sans text-faded-ink uppercase">Created</label>
                    <p className="text-sm font-sans text-midnight">
                      {new Date(selectedSnapshot.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-sans text-faded-ink uppercase">Trigger Type</label>
                    <p className="text-sm font-sans text-midnight">
                      {selectedSnapshot.trigger_type.replace('_', ' ')}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-sans text-faded-ink uppercase">Word Count</label>
                    <p className="text-sm font-sans text-midnight">
                      {selectedSnapshot.word_count.toLocaleString()} words
                    </p>
                  </div>
                  {selectedSnapshot.description && (
                    <div>
                      <label className="text-xs font-sans text-faded-ink uppercase">Description</label>
                      <p className="text-sm font-sans text-midnight">
                        {selectedSnapshot.description}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <HistorySlider
                snapshots={snapshots}
                onSelect={handleSelectSnapshot}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
