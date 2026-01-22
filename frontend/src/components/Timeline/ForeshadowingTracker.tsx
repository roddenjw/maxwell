/**
 * ForeshadowingTracker - Track setup/payoff pairs for narrative foreshadowing
 *
 * Features:
 * - List all foreshadowing pairs (resolved/unresolved tabs)
 * - Create new foreshadowing setups
 * - Link payoffs to existing setups
 * - Warning badges for Chekhov violations (unresolved setups)
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { foreshadowingApi } from '@/lib/api';
import type {
  ForeshadowingPair,
  ForeshadowingType,
  ForeshadowingStats,
} from '@/types/foreshadowing';
import {
  FORESHADOWING_TYPE_LABELS,
  FORESHADOWING_TYPE_ICONS,
} from '@/types/foreshadowing';
import ForeshadowingPairCard from './ForeshadowingPairCard';

interface ForeshadowingTrackerProps {
  manuscriptId: string;
}

type TabType = 'all' | 'unresolved' | 'resolved';

export default function ForeshadowingTracker({ manuscriptId }: ForeshadowingTrackerProps) {
  const { events } = useTimelineStore();
  const [pairs, setPairs] = useState<ForeshadowingPair[]>([]);
  const [stats, setStats] = useState<ForeshadowingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('all');

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [selectedPairId, setSelectedPairId] = useState<string | null>(null);

  // Create form state
  const [createForm, setCreateForm] = useState({
    foreshadowing_event_id: '',
    foreshadowing_type: 'HINT' as ForeshadowingType,
    foreshadowing_text: '',
    confidence: 5,
    notes: '',
  });

  // Link payoff form state
  const [linkForm, setLinkForm] = useState({
    payoff_event_id: '',
    payoff_text: '',
  });

  // Load data
  useEffect(() => {
    loadData();
  }, [manuscriptId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pairsData, statsData] = await Promise.all([
        foreshadowingApi.getPairs(manuscriptId),
        foreshadowingApi.getStats(manuscriptId),
      ]);
      setPairs(pairsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load foreshadowing data');
    } finally {
      setLoading(false);
    }
  };

  // Filter pairs by tab
  const filteredPairs = pairs.filter(pair => {
    if (activeTab === 'unresolved') return !pair.is_resolved;
    if (activeTab === 'resolved') return pair.is_resolved;
    return true;
  });

  // Handle create
  const handleCreate = async () => {
    if (!createForm.foreshadowing_event_id || !createForm.foreshadowing_text) {
      alert('Please select an event and enter description');
      return;
    }

    try {
      const newPair = await foreshadowingApi.createPair({
        manuscript_id: manuscriptId,
        foreshadowing_event_id: createForm.foreshadowing_event_id,
        foreshadowing_type: createForm.foreshadowing_type,
        foreshadowing_text: createForm.foreshadowing_text,
        confidence: createForm.confidence,
        notes: createForm.notes || undefined,
      });
      setPairs([newPair, ...pairs]);
      setShowCreateModal(false);
      setCreateForm({
        foreshadowing_event_id: '',
        foreshadowing_type: 'HINT',
        foreshadowing_text: '',
        confidence: 5,
        notes: '',
      });
      // Reload stats
      const statsData = await foreshadowingApi.getStats(manuscriptId);
      setStats(statsData);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create foreshadowing pair');
    }
  };

  // Handle link payoff
  const handleLinkPayoff = async () => {
    if (!selectedPairId || !linkForm.payoff_event_id || !linkForm.payoff_text) {
      alert('Please select an event and enter description');
      return;
    }

    try {
      const updatedPair = await foreshadowingApi.linkPayoff(selectedPairId, {
        payoff_event_id: linkForm.payoff_event_id,
        payoff_text: linkForm.payoff_text,
      });
      setPairs(pairs.map(p => p.id === selectedPairId ? updatedPair : p));
      setShowLinkModal(false);
      setSelectedPairId(null);
      setLinkForm({ payoff_event_id: '', payoff_text: '' });
      // Reload stats
      const statsData = await foreshadowingApi.getStats(manuscriptId);
      setStats(statsData);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to link payoff');
    }
  };

  // Handle unlink payoff
  const handleUnlinkPayoff = async (pairId: string) => {
    try {
      const updatedPair = await foreshadowingApi.unlinkPayoff(pairId);
      setPairs(pairs.map(p => p.id === pairId ? updatedPair : p));
      // Reload stats
      const statsData = await foreshadowingApi.getStats(manuscriptId);
      setStats(statsData);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to unlink payoff');
    }
  };

  // Handle delete
  const handleDelete = async (pairId: string) => {
    try {
      await foreshadowingApi.deletePair(pairId);
      setPairs(pairs.filter(p => p.id !== pairId));
      // Reload stats
      const statsData = await foreshadowingApi.getStats(manuscriptId);
      setStats(statsData);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete pair');
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-slate-ui bg-white">
          <div className="h-6 w-48 bg-slate-ui/30 animate-pulse rounded mb-2" />
          <div className="h-4 w-64 bg-slate-ui/20 animate-pulse rounded" />
        </div>
        <div className="p-4 space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-4 border border-slate-ui bg-white animate-pulse">
              <div className="h-4 w-24 bg-slate-ui/30 rounded mb-3" />
              <div className="h-16 w-full bg-slate-ui/20 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <span className="text-4xl mb-4 block">⚠️</span>
          <p className="text-redline font-sans text-sm">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-opacity-90 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-garamond text-lg text-midnight">
            Foreshadowing Tracker
          </h3>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3 py-1.5 bg-bronze text-white text-sm font-sans hover:bg-opacity-90 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            + Add Setup
          </button>
        </div>
        <p className="text-sm font-sans text-faded-ink">
          Track setup/payoff pairs to ensure narrative promises are fulfilled
        </p>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="p-3 border-b border-slate-ui bg-vellum flex items-center gap-6">
          <div className="text-center">
            <p className="text-lg font-garamond text-midnight font-semibold">{stats.total}</p>
            <p className="text-xs font-sans text-faded-ink">Total</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-garamond text-sage font-semibold">{stats.resolved}</p>
            <p className="text-xs font-sans text-faded-ink">Resolved</p>
          </div>
          <div className="text-center">
            <p className={`text-lg font-garamond font-semibold ${stats.unresolved > 0 ? 'text-bronze' : 'text-midnight'}`}>
              {stats.unresolved}
            </p>
            <p className="text-xs font-sans text-faded-ink">Unresolved</p>
          </div>
          {stats.unresolved > 0 && (
            <div className="ml-auto px-3 py-1 bg-bronze/20 text-bronze text-xs font-sans rounded-full">
              ⚠️ {stats.unresolved} Chekhov {stats.unresolved === 1 ? 'violation' : 'violations'}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-ui bg-white">
        {(['all', 'unresolved', 'resolved'] as TabType[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`
              flex-1 px-4 py-2 text-sm font-sans capitalize transition-colors
              ${activeTab === tab
                ? 'text-bronze border-b-2 border-bronze'
                : 'text-faded-ink hover:text-midnight'
              }
            `}
          >
            {tab}
            {tab === 'unresolved' && stats && stats.unresolved > 0 && (
              <span className="ml-1 text-xs bg-bronze text-white px-1.5 rounded-full">
                {stats.unresolved}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {filteredPairs.length === 0 ? (
          <div className="text-center py-12">
            <span className="text-5xl mb-4 block">🔮</span>
            <p className="text-midnight font-garamond text-lg font-semibold mb-2">
              {activeTab === 'all'
                ? 'No foreshadowing pairs yet'
                : activeTab === 'unresolved'
                  ? 'All setups are resolved!'
                  : 'No resolved pairs yet'
              }
            </p>
            <p className="text-sm font-sans text-faded-ink max-w-sm mx-auto">
              {activeTab === 'all'
                ? "Track your story's setups and payoffs to ensure narrative promises are kept."
                : activeTab === 'unresolved'
                  ? "Great job! You've resolved all your foreshadowing setups."
                  : 'Link payoffs to your setups to see them here.'
              }
            </p>
          </div>
        ) : (
          filteredPairs.map(pair => (
            <ForeshadowingPairCard
              key={pair.id}
              pair={pair}
              onDelete={handleDelete}
              onLinkPayoff={(pairId) => {
                setSelectedPairId(pairId);
                setShowLinkModal(true);
              }}
              onUnlinkPayoff={handleUnlinkPayoff}
            />
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 w-full max-w-lg mx-4" style={{ borderRadius: '4px' }}>
            <h3 className="font-garamond text-xl text-midnight mb-4">
              Add Foreshadowing Setup
            </h3>

            <div className="space-y-4">
              {/* Event selection */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Setup Event *
                </label>
                <select
                  value={createForm.foreshadowing_event_id}
                  onChange={(e) => setCreateForm({ ...createForm, foreshadowing_event_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans bg-white"
                  style={{ borderRadius: '2px' }}
                >
                  <option value="">Select an event...</option>
                  {events.map(event => (
                    <option key={event.id} value={event.id}>
                      #{event.order_index}: {event.description.slice(0, 60)}...
                    </option>
                  ))}
                </select>
              </div>

              {/* Type selection */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Type *
                </label>
                <select
                  value={createForm.foreshadowing_type}
                  onChange={(e) => setCreateForm({ ...createForm, foreshadowing_type: e.target.value as ForeshadowingType })}
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans bg-white"
                  style={{ borderRadius: '2px' }}
                >
                  {Object.entries(FORESHADOWING_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {FORESHADOWING_TYPE_ICONS[value as ForeshadowingType]} {label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Setup Description *
                </label>
                <textarea
                  value={createForm.foreshadowing_text}
                  onChange={(e) => setCreateForm({ ...createForm, foreshadowing_text: e.target.value })}
                  placeholder="Describe what is being set up..."
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans resize-none"
                  style={{ borderRadius: '2px' }}
                  rows={3}
                />
              </div>

              {/* Confidence */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Confidence ({createForm.confidence}/10)
                </label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={createForm.confidence}
                  onChange={(e) => setCreateForm({ ...createForm, confidence: parseInt(e.target.value) })}
                  className="w-full"
                />
                <p className="text-xs font-sans text-faded-ink">
                  How obvious is this foreshadowing to readers?
                </p>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Notes (Optional)
                </label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  placeholder="Your notes about this setup..."
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans resize-none"
                  style={{ borderRadius: '2px' }}
                  rows={2}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-slate-ui text-midnight text-sm font-sans hover:bg-vellum transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-opacity-90 transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Create Setup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Link Payoff Modal */}
      {showLinkModal && selectedPairId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 w-full max-w-lg mx-4" style={{ borderRadius: '4px' }}>
            <h3 className="font-garamond text-xl text-midnight mb-4">
              Link Payoff Event
            </h3>

            <div className="space-y-4">
              {/* Event selection */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Payoff Event *
                </label>
                <select
                  value={linkForm.payoff_event_id}
                  onChange={(e) => setLinkForm({ ...linkForm, payoff_event_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans bg-white"
                  style={{ borderRadius: '2px' }}
                >
                  <option value="">Select an event...</option>
                  {events.map(event => (
                    <option key={event.id} value={event.id}>
                      #{event.order_index}: {event.description.slice(0, 60)}...
                    </option>
                  ))}
                </select>
              </div>

              {/* Payoff description */}
              <div>
                <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
                  Payoff Description *
                </label>
                <textarea
                  value={linkForm.payoff_text}
                  onChange={(e) => setLinkForm({ ...linkForm, payoff_text: e.target.value })}
                  placeholder="Describe how the setup pays off..."
                  className="w-full px-3 py-2 border border-slate-ui text-sm font-sans resize-none"
                  style={{ borderRadius: '2px' }}
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowLinkModal(false);
                  setSelectedPairId(null);
                  setLinkForm({ payoff_event_id: '', payoff_text: '' });
                }}
                className="px-4 py-2 border border-slate-ui text-midnight text-sm font-sans hover:bg-vellum transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
              <button
                onClick={handleLinkPayoff}
                className="px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-opacity-90 transition-colors"
                style={{ borderRadius: '2px' }}
              >
                Link Payoff
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
