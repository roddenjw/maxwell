/**
 * WorldWikiBrowser Component
 * Main browser for exploring and managing World Wiki entries
 */

import { useState, useEffect, useCallback } from 'react';
import type { World } from '../../types/world';
import type {
  WikiEntry,
  WikiEntryType,
  WikiEntryCreate,
  WikiFilters,
  WikiReferenceType,
} from '../../types/wiki';
import { WIKI_REFERENCE_TYPE_INFO } from '../../types/wiki';
import { WikiEntryCard } from './WikiEntryCard';
import { WikiEntryEditor } from './WikiEntryEditor';
import { WikiChangeQueue } from './WikiChangeQueue';
import { CultureLinkManager } from './CultureLinkManager';
import { cultureApi } from '../../lib/api';

const API_BASE = 'http://localhost:8000';

// Category groups for sidebar
const CATEGORY_GROUPS = [
  {
    name: 'Characters',
    types: ['character', 'character_arc', 'character_relationship'] as WikiEntryType[],
    icon: '👥',
  },
  {
    name: 'Locations',
    types: ['location', 'location_history'] as WikiEntryType[],
    icon: '🗺️',
  },
  {
    name: 'World Building',
    types: ['magic_system', 'world_rule', 'technology', 'culture', 'religion'] as WikiEntryType[],
    icon: '🌍',
  },
  {
    name: 'Organizations',
    types: ['faction'] as WikiEntryType[],
    icon: '🏛️',
  },
  {
    name: 'Items & Creatures',
    types: ['artifact', 'creature'] as WikiEntryType[],
    icon: '🎒',
  },
  {
    name: 'Events & Timeline',
    types: ['event', 'timeline_fact'] as WikiEntryType[],
    icon: '📅',
  },
  {
    name: 'Meta',
    types: ['theme'] as WikiEntryType[],
    icon: '💡',
  },
];

interface WorldWikiBrowserProps {
  world: World;
  manuscriptId?: string;
  onClose?: () => void;
}

export default function WorldWikiBrowser({ world, manuscriptId, onClose }: WorldWikiBrowserProps) {
  // State
  const [entries, setEntries] = useState<WikiEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<WikiEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<WikiFilters>({});
  const [showEditor, setShowEditor] = useState(false);
  const [showChangeQueue, setShowChangeQueue] = useState(false);
  const [pendingChangesCount, setPendingChangesCount] = useState(0);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [showCultureLinks, setShowCultureLinks] = useState(false);
  const [cultureMembers, setCultureMembers] = useState<any[]>([]);
  const [entityCultures, setEntityCultures] = useState<any[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<{ total_changes: number } | null>(null);

  // Fetch entries
  const fetchEntries = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      let url = `${API_BASE}/wiki/worlds/${world.id}/entries?limit=500`;

      if (filters.entryType) {
        url += `&entry_type=${filters.entryType}`;
      }
      if (filters.status) {
        url += `&status=${filters.status}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch wiki entries');

      const data = await response.json();
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load wiki');
    } finally {
      setIsLoading(false);
    }
  }, [world.id, filters]);

  // Fetch pending changes count
  const fetchPendingChanges = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/wiki/worlds/${world.id}/changes?limit=1`);
      if (response.ok) {
        const data = await response.json();
        setPendingChangesCount(data.length);
      }
    } catch (err) {
      console.error('Failed to fetch pending changes:', err);
    }
  }, [world.id]);

  // Search entries
  const searchEntries = useCallback(async () => {
    if (!searchQuery.trim()) {
      fetchEntries();
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/wiki/worlds/${world.id}/search?q=${encodeURIComponent(searchQuery)}`
      );
      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsLoading(false);
    }
  }, [world.id, searchQuery, fetchEntries]);

  // Initial fetch
  useEffect(() => {
    fetchEntries();
    fetchPendingChanges();
  }, [fetchEntries, fetchPendingChanges]);

  // Load culture data for selected entry
  useEffect(() => {
    if (!selectedEntry) {
      setCultureMembers([]);
      setEntityCultures([]);
      return;
    }

    if (selectedEntry.entry_type === 'culture') {
      cultureApi.getCultureMembers(selectedEntry.id).then(setCultureMembers).catch(() => setCultureMembers([]));
    } else {
      setCultureMembers([]);
    }

    cultureApi.getEntityCultures(selectedEntry.id).then(setEntityCultures).catch(() => setEntityCultures([]));
  }, [selectedEntry?.id]);

  // Handle search
  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery) {
        searchEntries();
      }
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchQuery, searchEntries]);

  // Create new entry
  const handleCreateEntry = async (data: WikiEntryCreate) => {
    try {
      const response = await fetch(`${API_BASE}/wiki/entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error('Failed to create entry');

      const newEntry = await response.json();
      setEntries((prev) => [...prev, newEntry]);
      setSelectedEntry(newEntry);
      setShowEditor(false);
    } catch (err) {
      throw err;
    }
  };

  // Update entry
  const handleUpdateEntry = async (entryId: string, updates: Partial<WikiEntry>) => {
    try {
      const response = await fetch(`${API_BASE}/wiki/entries/${entryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error('Failed to update entry');

      const updatedEntry = await response.json();
      setEntries((prev) =>
        prev.map((e) => (e.id === entryId ? updatedEntry : e))
      );
      setSelectedEntry(updatedEntry);
    } catch (err) {
      throw err;
    }
  };

  // Delete entry
  const handleDeleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to delete this entry?')) return;

    try {
      const response = await fetch(`${API_BASE}/wiki/entries/${entryId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete entry');

      setEntries((prev) => prev.filter((e) => e.id !== entryId));
      if (selectedEntry?.id === entryId) {
        setSelectedEntry(null);
      }
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  // Scan manuscript for wiki entries
  const handleScanManuscript = async () => {
    if (!manuscriptId) return;
    setIsScanning(true);
    setScanResult(null);
    try {
      const response = await fetch(`${API_BASE}/wiki/auto-populate/manuscript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manuscript_id: manuscriptId, world_id: world.id }),
      });
      if (!response.ok) throw new Error('Scan failed');
      const result = await response.json();
      setScanResult(result);
      await fetchPendingChanges();
      if (result.total_changes > 0) {
        setShowChangeQueue(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  // Filter entries by category
  const getFilteredEntries = () => {
    let filtered = entries;

    if (filters.entryType) {
      filtered = filtered.filter((e) => e.entry_type === filters.entryType);
    }

    return filtered;
  };

  // Get counts by type
  const getTypeCounts = () => {
    const counts: Record<string, number> = {};
    entries.forEach((e) => {
      counts[e.entry_type] = (counts[e.entry_type] || 0) + 1;
    });
    return counts;
  };

  const filteredEntries = getFilteredEntries();
  const typeCounts = getTypeCounts();

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-gray-800">World Wiki</h2>
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            )}
          </div>
          <p className="text-sm text-gray-500">{world.name}</p>
        </div>

        {/* Search */}
        <div className="p-3 border-b border-gray-200">
          <input
            type="text"
            placeholder="Search wiki..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Categories */}
        <div className="flex-1 overflow-y-auto">
          <button
            onClick={() => setFilters({})}
            className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 ${
              !filters.entryType
                ? 'bg-blue-50 text-blue-700 font-medium'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span>📚</span>
            <span>All Entries</span>
            <span className="ml-auto text-xs text-gray-400">
              {entries.length}
            </span>
          </button>

          {CATEGORY_GROUPS.map((group) => (
            <div key={group.name} className="border-t border-gray-100">
              <div className="px-4 py-2 text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <span>{group.icon}</span>
                <span>{group.name}</span>
              </div>
              {group.types.map((type) => (
                <button
                  key={type}
                  onClick={() => setFilters({ entryType: type })}
                  className={`w-full px-4 py-1.5 pl-8 text-left text-sm flex items-center justify-between ${
                    filters.entryType === type
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <span className="capitalize">
                    {type.replace(/_/g, ' ')}
                  </span>
                  {typeCounts[type] > 0 && (
                    <span className="text-xs text-gray-400">
                      {typeCounts[type]}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Bottom Actions */}
        <div className="p-3 border-t border-gray-200 space-y-2">
          {manuscriptId && (
            <button
              onClick={handleScanManuscript}
              disabled={isScanning}
              className="w-full px-3 py-2 text-sm text-left flex items-center gap-2 text-amber-700 hover:bg-amber-50 rounded disabled:opacity-50"
            >
              <span>{isScanning ? '...' : '🔍'}</span>
              <span>{isScanning ? 'Scanning...' : 'Scan Manuscript'}</span>
              {scanResult && scanResult.total_changes > 0 && (
                <span className="ml-auto bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">
                  +{scanResult.total_changes}
                </span>
              )}
            </button>
          )}
          <button
            onClick={() => setShowChangeQueue(true)}
            className="w-full px-3 py-2 text-sm text-left flex items-center gap-2 text-gray-700 hover:bg-gray-50 rounded"
          >
            <span>📥</span>
            <span>Approval Queue</span>
            {pendingChangesCount > 0 && (
              <span className="ml-auto bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full text-xs">
                {pendingChangesCount}
              </span>
            )}
          </button>
          <button
            onClick={() => {
              setSelectedEntry(null);
              setShowEditor(true);
            }}
            className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center justify-center gap-2"
          >
            <span>+</span>
            <span>New Entry</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              {filteredEntries.length} entries
              {filters.entryType && ` in ${filters.entryType.replace(/_/g, ' ')}`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'
              }`}
              title="List view"
            >
              ☰
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'
              }`}
              title="Grid view"
            >
              ⊞
            </button>
          </div>
        </div>

        {/* Entry List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading wiki...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-500">{error}</div>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <span className="text-4xl mb-2">📚</span>
              <p>No wiki entries yet</p>
              <button
                onClick={() => setShowEditor(true)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Create First Entry
              </button>
            </div>
          ) : (
            <div
              className={
                viewMode === 'grid'
                  ? 'grid grid-cols-2 lg:grid-cols-3 gap-4'
                  : 'space-y-3'
              }
            >
              {filteredEntries.map((entry) => (
                <WikiEntryCard
                  key={entry.id}
                  entry={entry}
                  viewMode={viewMode}
                  isSelected={selectedEntry?.id === entry.id}
                  onClick={() => setSelectedEntry(entry)}
                  onEdit={() => {
                    setSelectedEntry(entry);
                    setShowEditor(true);
                  }}
                  onDelete={() => handleDeleteEntry(entry.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedEntry && !showEditor && (
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-medium text-gray-800">{selectedEntry.title}</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowEditor(true)}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                Edit
              </button>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {selectedEntry.summary && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-1">
                  Summary
                </h4>
                <p className="text-sm text-gray-600">{selectedEntry.summary}</p>
              </div>
            )}
            {selectedEntry.content && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-1">
                  Content
                </h4>
                <div className="prose prose-sm max-w-none">
                  {selectedEntry.content}
                </div>
              </div>
            )}
            {selectedEntry.aliases && selectedEntry.aliases.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-1">
                  Aliases
                </h4>
                <div className="flex flex-wrap gap-1">
                  {selectedEntry.aliases.map((alias, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {selectedEntry.tags && selectedEntry.tags.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-1">
                  Tags
                </h4>
                <div className="flex flex-wrap gap-1">
                  {selectedEntry.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Culture Members (shown when viewing a culture entry) */}
            {selectedEntry.entry_type === 'culture' && cultureMembers.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-2">
                  Members ({cultureMembers.length})
                </h4>
                <div className="space-y-1.5">
                  {(() => {
                    const grouped: Record<string, any[]> = {};
                    cultureMembers.forEach((m: any) => {
                      const t = m.entity_type || 'other';
                      if (!grouped[t]) grouped[t] = [];
                      grouped[t].push(m);
                    });
                    return Object.entries(grouped).map(([type, members]) => (
                      <div key={type}>
                        <div className="text-xs font-medium text-gray-500 capitalize mb-1">
                          {type.replace(/_/g, ' ')}
                        </div>
                        {members.map((m: any) => {
                          const refInfo = WIKI_REFERENCE_TYPE_INFO[m.reference_type as WikiReferenceType];
                          return (
                            <div
                              key={m.reference_id}
                              className="flex items-center gap-2 pl-2 py-0.5 cursor-pointer hover:bg-gray-50 rounded"
                              onClick={() => {
                                const entry = entries.find(e => e.id === m.entity_id);
                                if (entry) setSelectedEntry(entry);
                              }}
                            >
                              <span className="text-sm text-gray-700">{m.entity_title}</span>
                              <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                                {refInfo?.reverseLabel || m.reference_type.replace(/_/g, ' ')}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    ));
                  })()}
                </div>
              </div>
            )}

            {/* Culture Links (shown for non-culture entries that have culture links) */}
            {selectedEntry.entry_type !== 'culture' && entityCultures.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-400 uppercase mb-2">
                  Cultures
                </h4>
                <div className="space-y-1.5">
                  {entityCultures.map((c: any) => {
                    const refInfo = WIKI_REFERENCE_TYPE_INFO[c.reference_type as WikiReferenceType];
                    return (
                      <div
                        key={c.reference_id}
                        className="flex items-center gap-2 p-2 bg-orange-50 rounded-lg border border-orange-200 cursor-pointer hover:bg-orange-100"
                        onClick={() => {
                          const entry = entries.find(e => e.id === c.culture_id);
                          if (entry) setSelectedEntry(entry);
                        }}
                      >
                        <span className="text-lg">🎭</span>
                        <span className="text-sm font-medium text-gray-700">{c.culture_title}</span>
                        <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                          {refInfo?.label || c.reference_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Link to Culture button */}
            {selectedEntry.entry_type !== 'culture' && (
              <div className="mb-4">
                <button
                  onClick={() => setShowCultureLinks(true)}
                  className="w-full px-3 py-2 text-sm border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 flex items-center justify-center gap-2"
                >
                  <span>🎭</span>
                  <span>Link to Culture</span>
                </button>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="text-xs text-gray-400 space-y-1">
                <div>Type: {selectedEntry.entry_type.replace(/_/g, ' ')}</div>
                <div>Status: {selectedEntry.status}</div>
                <div>
                  Created: {new Date(selectedEntry.created_at).toLocaleDateString()}
                </div>
                {selectedEntry.confidence_score < 1 && (
                  <div>
                    Confidence: {Math.round(selectedEntry.confidence_score * 100)}%
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Editor Modal */}
      {showEditor && (
        <WikiEntryEditor
          entry={selectedEntry}
          worldId={world.id}
          onSave={
            selectedEntry
              ? (updates) => handleUpdateEntry(selectedEntry.id, updates)
              : handleCreateEntry
          }
          onClose={() => {
            setShowEditor(false);
            if (!selectedEntry) {
              setSelectedEntry(null);
            }
          }}
        />
      )}

      {/* Change Queue Modal */}
      {showChangeQueue && (
        <WikiChangeQueue
          worldId={world.id}
          manuscriptId={manuscriptId}
          onClose={() => {
            setShowChangeQueue(false);
            fetchPendingChanges();
            fetchEntries();
          }}
        />
      )}

      {/* Culture Link Manager Modal */}
      {showCultureLinks && selectedEntry && (
        <CultureLinkManager
          entryId={selectedEntry.id}
          worldId={world.id}
          entryTitle={selectedEntry.title}
          onClose={() => setShowCultureLinks(false)}
          onLinksChanged={() => {
            // Reload culture data for the selected entry
            cultureApi.getEntityCultures(selectedEntry.id).then(setEntityCultures).catch(() => {});
          }}
        />
      )}
    </div>
  );
}
