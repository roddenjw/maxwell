/**
 * WorldWikiBrowser Component
 * Main browser for exploring and managing World Wiki entries
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { World } from '../../types/world';
import type {
  WikiEntry,
  WikiEntryType,
  WikiEntryStatus,
  WikiEntryCreate,
  WikiEntryUpdate,
  WikiReferenceType,
} from '../../types/wiki';
import { WIKI_REFERENCE_TYPE_INFO, WIKI_ENTRY_TYPE_INFO } from '../../types/wiki';
import { WikiEntryEditor } from './WikiEntryEditor';
import { WikiChangeQueue } from './WikiChangeQueue';
import { CultureLinkManager } from './CultureLinkManager';
import { cultureApi } from '../../lib/api';
import { toast } from '../../stores/toastStore';

const API_BASE = 'http://localhost:8000';

// Category groups for sidebar tree
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

// ==================== StatusSelector ====================

const STATUS_CONFIG: Record<WikiEntryStatus, { label: string; bg: string; text: string; dot: string }> = {
  draft: { label: 'Draft', bg: 'bg-gray-100', text: 'text-gray-700', dot: 'bg-gray-400' },
  published: { label: 'Published', bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' },
  archived: { label: 'Archived', bg: 'bg-amber-100', text: 'text-amber-700', dot: 'bg-amber-500' },
};

function StatusSelector({
  status,
  onChange,
}: {
  status: WikiEntryStatus;
  onChange: (status: WikiEntryStatus) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const config = STATUS_CONFIG[status];

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text} hover:opacity-80 transition-opacity`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
        {config.label}
        <span className="text-[10px] opacity-60">▾</span>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 min-w-[120px]">
          {(Object.keys(STATUS_CONFIG) as WikiEntryStatus[]).map((s) => {
            const c = STATUS_CONFIG[s];
            return (
              <button
                key={s}
                onClick={() => {
                  onChange(s);
                  setOpen(false);
                }}
                className={`w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-gray-50 ${
                  s === status ? 'font-medium' : ''
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
                {c.label}
                {s === status && <span className="ml-auto text-blue-500">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ==================== Type icon helper ====================

const TYPE_ICONS: Partial<Record<WikiEntryType, string>> = {
  character: '👤',
  character_arc: '📈',
  character_relationship: '💬',
  location: '📍',
  location_history: '🏚️',
  magic_system: '✨',
  world_rule: '📜',
  technology: '⚙️',
  culture: '🎭',
  religion: '🕯️',
  faction: '🏛️',
  artifact: '💎',
  creature: '🐉',
  event: '⚡',
  timeline_fact: '📅',
  theme: '💡',
};

// ==================== Main Component ====================

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
  const [showEditor, setShowEditor] = useState(false);
  const [showChangeQueue, setShowChangeQueue] = useState(false);
  const [pendingChangesCount, setPendingChangesCount] = useState(0);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    () => new Set(CATEGORY_GROUPS.map((g) => g.name))
  );
  const [showCultureLinks, setShowCultureLinks] = useState(false);
  const [cultureMembers, setCultureMembers] = useState<any[]>([]);
  const [entityCultures, setEntityCultures] = useState<any[]>([]);

  // Background scan state
  const [activeScanTaskId, setActiveScanTaskId] = useState<string | null>(null);
  const [scanProgress, setScanProgress] = useState<{
    status: string;
    progress_percent: number;
    current_manuscript_title: string;
    current_stage: string;
    manuscripts_completed: number;
    total_manuscripts: number;
    total_changes: number;
    error?: string;
  } | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Merge state
  const [showMergePicker, setShowMergePicker] = useState(false);
  const [mergeSearchQuery, setMergeSearchQuery] = useState('');
  const [isMerging, setIsMerging] = useState(false);

  // Inline editing state
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editSummary, setEditSummary] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editEntryType, setEditEntryType] = useState<WikiEntryType | ''>('');
  const [editAliases, setEditAliases] = useState<string[]>([]);
  const [editTags, setEditTags] = useState<string[]>([]);
  const [editNewAlias, setEditNewAlias] = useState('');
  const [editNewTag, setEditNewTag] = useState('');
  const [editParentCultureId, setEditParentCultureId] = useState('');
  const [editAvailableCultures, setEditAvailableCultures] = useState<Array<{ id: string; title: string }>>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const startEditing = () => {
    if (!selectedEntry) return;
    setEditTitle(selectedEntry.title);
    setEditSummary(selectedEntry.summary || '');
    setEditContent(selectedEntry.content || '');
    setEditEntryType(selectedEntry.entry_type);
    setEditAliases(selectedEntry.aliases || []);
    setEditTags(selectedEntry.tags || []);
    setEditNewAlias('');
    setEditNewTag('');
    setEditParentCultureId(selectedEntry.parent_id || '');
    setEditError(null);
    setIsEditing(true);
    // Load cultures for parent dropdown
    cultureApi.getWorldCultures(world.id)
      .then((cultures: any[]) => setEditAvailableCultures(cultures.map(c => ({ id: c.id, title: c.title }))))
      .catch(() => setEditAvailableCultures([]));
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditError(null);
  };

  const saveEditing = async () => {
    if (!selectedEntry || !editTitle.trim()) {
      setEditError('Title is required');
      return;
    }
    setIsSaving(true);
    setEditError(null);
    try {
      const updates: WikiEntryUpdate = {
        title: editTitle.trim(),
        summary: editSummary.trim() || undefined,
        content: editContent.trim() || undefined,
        aliases: editAliases.length > 0 ? editAliases : undefined,
        tags: editTags.length > 0 ? editTags : undefined,
        parent_id: editParentCultureId || undefined,
        entry_type: editEntryType && editEntryType !== selectedEntry.entry_type
          ? editEntryType as WikiEntryType
          : undefined,
      };
      await handleUpdateEntry(selectedEntry.id, updates);
      setIsEditing(false);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  // Cancel editing when switching entries
  useEffect(() => {
    setIsEditing(false);
  }, [selectedEntry?.id]);

  // Fetch all entries (no server-side filtering)
  const fetchEntries = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE}/wiki/worlds/${world.id}/entries?limit=500`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch wiki entries');

      const data = await response.json();
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load wiki');
    } finally {
      setIsLoading(false);
    }
  }, [world.id]);

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

  // Poll for scan progress
  const startPolling = useCallback((taskId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/wiki/scan-tasks/${taskId}`);
        if (!res.ok) return;
        const data = await res.json();
        setScanProgress(data);
        if (data.status === 'completed') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setActiveScanTaskId(null);
          fetchEntries();
          fetchPendingChanges();
          toast.success(`Scan complete: ${data.total_changes} changes found`, {
            action: data.total_changes > 0
              ? { label: 'Review Changes', onClick: () => setShowChangeQueue(true) }
              : undefined,
          });
        } else if (data.status === 'failed') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setActiveScanTaskId(null);
          toast.error(`Scan failed: ${data.error || 'Unknown error'}`);
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);
  }, [fetchEntries, fetchPendingChanges]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Initial fetch + check for active scan
  useEffect(() => {
    fetchEntries();
    fetchPendingChanges();
    // Reconnect to active scan
    fetch(`${API_BASE}/wiki/worlds/${world.id}/active-scan`)
      .then((r) => r.json())
      .then((data) => {
        if (data.active && data.task_id) {
          setActiveScanTaskId(data.task_id);
          setScanProgress({
            status: data.status,
            progress_percent: data.progress_percent,
            current_manuscript_title: data.current_manuscript_title || '',
            current_stage: data.current_stage || '',
            manuscripts_completed: 0,
            total_manuscripts: 0,
            total_changes: 0,
          });
          startPolling(data.task_id);
        }
      })
      .catch(() => {});
  }, [fetchEntries, fetchPendingChanges, world.id, startPolling]);

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

  // Client-side filtered + grouped category tree
  const categoryTree = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();

    return CATEGORY_GROUPS.map((group) => {
      // Group entries by entry_type within this category
      const typeMap = new Map<WikiEntryType, WikiEntry[]>();

      for (const type of group.types) {
        const matching = entries
          .filter((e) => {
            if (e.entry_type !== type) return false;
            if (!query) return true;
            return (
              e.title.toLowerCase().includes(query) ||
              e.summary?.toLowerCase().includes(query) ||
              e.aliases?.some((a) => a.toLowerCase().includes(query))
            );
          })
          .sort((a, b) => a.title.localeCompare(b.title));

        if (matching.length > 0) {
          typeMap.set(type, matching);
        }
      }

      const totalCount = Array.from(typeMap.values()).reduce((sum, arr) => sum + arr.length, 0);

      return {
        ...group,
        typeMap,
        totalCount,
      };
    }).filter((g) => g.totalCount > 0);
  }, [entries, searchQuery]);

  // Toggle category expansion
  const toggleCategory = (name: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  // During search, auto-expand all categories with matches
  const isCategoryExpanded = (name: string) => {
    if (searchQuery.trim()) return true;
    return expandedCategories.has(name);
  };

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
      toast.success('Entry deleted');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete entry');
    }
  };

  // Start background scan
  const handleStartScan = async (type: 'manuscript' | 'world') => {
    if (activeScanTaskId) return;
    try {
      const url = type === 'world'
        ? `${API_BASE}/wiki/auto-populate/world`
        : `${API_BASE}/wiki/auto-populate/manuscript-async`;
      const body = type === 'world'
        ? { world_id: world.id }
        : { manuscript_id: manuscriptId, world_id: world.id };

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed to start scan');
      const data = await res.json();
      setActiveScanTaskId(data.task_id);
      setScanProgress({
        status: 'running',
        progress_percent: 0,
        current_manuscript_title: '',
        current_stage: 'Starting...',
        manuscripts_completed: 0,
        total_manuscripts: data.total_manuscripts || 1,
        total_changes: 0,
      });
      startPolling(data.task_id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Scan failed to start');
    }
  };

  // Merge entries
  const handleMerge = async (targetId: string) => {
    if (!selectedEntry) return;
    setIsMerging(true);
    try {
      const res = await fetch(`${API_BASE}/wiki/entries/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_entry_id: selectedEntry.id,
          target_entry_id: targetId,
        }),
      });
      if (!res.ok) throw new Error('Merge failed');
      const mergedEntry = await res.json();

      // Remove source from list, update target
      setEntries((prev) =>
        prev.filter((e) => e.id !== selectedEntry.id).map((e) => e.id === targetId ? mergedEntry : e)
      );
      setSelectedEntry(mergedEntry);
      setShowMergePicker(false);
      toast.success(`Merged into "${mergedEntry.title}"`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Merge failed');
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* ==================== Sidebar Tree ==================== */}
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

        {/* Category Tree */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-sm text-gray-400">Loading...</div>
          ) : categoryTree.length === 0 ? (
            <div className="p-4 text-sm text-gray-400">
              {searchQuery ? 'No matches' : 'No entries yet'}
            </div>
          ) : (
            categoryTree.map((group) => {
              const expanded = isCategoryExpanded(group.name);
              // If only one entry_type has entries, skip the sub-type header
              const singleType = group.typeMap.size === 1;

              return (
                <div key={group.name} className="border-b border-gray-100">
                  {/* Category header */}
                  <button
                    onClick={() => toggleCategory(group.name)}
                    className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-50 font-medium text-gray-700"
                  >
                    <span className="text-[10px] text-gray-400 w-3">
                      {expanded ? '▾' : '▸'}
                    </span>
                    <span>{group.icon}</span>
                    <span>{group.name}</span>
                    <span className="ml-auto text-xs text-gray-400 font-normal">
                      {group.totalCount}
                    </span>
                  </button>

                  {/* Expanded children */}
                  {expanded && (
                    <div className="pb-1">
                      {Array.from(group.typeMap.entries()).map(([type, typeEntries]) => (
                        <div key={type}>
                          {/* Sub-type header (skip if only one type in this category) */}
                          {!singleType && (
                            <div className="px-8 py-1 text-[11px] font-medium text-gray-400 uppercase tracking-wider">
                              {type.replace(/_/g, ' ')}
                            </div>
                          )}
                          {/* Entry names */}
                          {typeEntries.map((entry) => (
                            <button
                              key={entry.id}
                              onClick={() => setSelectedEntry(entry)}
                              className={`w-full text-left text-sm flex items-center gap-1.5 py-1 ${
                                singleType ? 'px-8' : 'px-10'
                              } ${
                                selectedEntry?.id === entry.id
                                  ? 'bg-blue-50 text-blue-700 font-medium'
                                  : 'text-gray-600 hover:bg-gray-50'
                              }`}
                            >
                              <span className="truncate flex-1">{entry.title}</span>
                              {entry.status === 'draft' && (
                                <span className="w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0" title="Draft" />
                              )}
                              {entry.status === 'archived' && (
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" title="Archived" />
                              )}
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Scan Progress */}
        {activeScanTaskId && scanProgress && (
          <div className="px-3 py-2 border-t border-gray-200 bg-amber-50">
            <div className="flex items-center gap-2 mb-1">
              <span className="animate-spin text-xs">⏳</span>
              <span className="text-xs font-medium text-amber-800 truncate">
                {scanProgress.current_manuscript_title || 'Scanning...'}
              </span>
            </div>
            <div className="text-[11px] text-amber-600 mb-1 truncate">
              {scanProgress.current_stage}
              {scanProgress.total_manuscripts > 1 && (
                <> ({scanProgress.manuscripts_completed}/{scanProgress.total_manuscripts})</>
              )}
            </div>
            <div className="w-full bg-amber-200 rounded-full h-1.5">
              <div
                className="bg-amber-600 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(scanProgress.progress_percent, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Bottom Actions */}
        <div className="p-3 border-t border-gray-200 space-y-2">
          <button
            onClick={() => handleStartScan('world')}
            disabled={!!activeScanTaskId}
            className="w-full px-3 py-2 text-sm text-left flex items-center gap-2 text-amber-700 hover:bg-amber-50 rounded disabled:opacity-50"
          >
            <span>{activeScanTaskId ? '...' : '🌍'}</span>
            <span>{activeScanTaskId ? 'Scanning...' : 'Scan World'}</span>
          </button>
          {manuscriptId && (
            <button
              onClick={() => handleStartScan('manuscript')}
              disabled={!!activeScanTaskId}
              className="w-full px-3 py-2 text-sm text-left flex items-center gap-2 text-amber-700 hover:bg-amber-50 rounded disabled:opacity-50"
            >
              <span>{activeScanTaskId ? '...' : '🔍'}</span>
              <span>{activeScanTaskId ? 'Scanning...' : 'Scan Manuscript'}</span>
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

      {/* ==================== Main Content Area ==================== */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500">Loading wiki...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-red-500">{error}</div>
          </div>
        ) : !selectedEntry ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <span className="text-4xl mb-3">📚</span>
            <p className="text-lg font-medium text-gray-700 mb-1">{world.name}</p>
            {entries.length === 0 ? (
              <>
                <p className="text-sm mb-4">No wiki entries yet</p>
                <button
                  onClick={() => setShowEditor(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create First Entry
                </button>
              </>
            ) : (
              <p className="text-sm">Select an entry from the sidebar</p>
            )}
          </div>
        ) : isEditing ? (
          /* Inline edit mode */
          <div className="max-w-3xl mx-auto p-6">
            {/* Header row */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{TYPE_ICONS[selectedEntry.entry_type] || '📄'}</span>
                <span className="text-lg font-medium text-gray-500">Editing</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={cancelEditing}
                  disabled={isSaving}
                  className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveEditing}
                  disabled={isSaving || !editTitle.trim()}
                  className="px-3 py-1.5 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>

            {editError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
                {editError}
              </div>
            )}

            {/* Title */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Title</label>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full px-3 py-2 text-lg font-bold border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>

            {/* Entry Type */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Type</label>
              <select
                value={editEntryType}
                onChange={(e) => setEditEntryType(e.target.value as WikiEntryType)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                {(Object.keys(WIKI_ENTRY_TYPE_INFO) as WikiEntryType[]).map((t) => (
                  <option key={t} value={t}>
                    {WIKI_ENTRY_TYPE_INFO[t].icon} {WIKI_ENTRY_TYPE_INFO[t].label}
                  </option>
                ))}
              </select>
              {editEntryType && selectedEntry && editEntryType !== selectedEntry.entry_type && (
                <p className="mt-1 text-xs text-amber-600">
                  Linked codex entities will be updated to match the new type.
                </p>
              )}
            </div>

            {/* Summary */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Summary</label>
              <textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                placeholder="Brief summary..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Content */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Content</label>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="Detailed content..."
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              />
            </div>

            {/* Aliases */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Aliases</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={editNewAlias}
                  onChange={(e) => setEditNewAlias(e.target.value)}
                  placeholder="Add alias..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (editNewAlias.trim() && !editAliases.includes(editNewAlias.trim())) {
                        setEditAliases([...editAliases, editNewAlias.trim()]);
                        setEditNewAlias('');
                      }
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={() => {
                    if (editNewAlias.trim() && !editAliases.includes(editNewAlias.trim())) {
                      setEditAliases([...editAliases, editNewAlias.trim()]);
                      setEditNewAlias('');
                    }
                  }}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                >
                  Add
                </button>
              </div>
              {editAliases.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {editAliases.map((alias, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 text-gray-700 text-sm rounded-md"
                    >
                      {alias}
                      <button
                        type="button"
                        onClick={() => setEditAliases(editAliases.filter((a) => a !== alias))}
                        className="text-gray-400 hover:text-gray-600 ml-0.5"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="mb-5">
              <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Tags</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={editNewTag}
                  onChange={(e) => setEditNewTag(e.target.value)}
                  placeholder="Add tag..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (editNewTag.trim() && !editTags.includes(editNewTag.trim())) {
                        setEditTags([...editTags, editNewTag.trim()]);
                        setEditNewTag('');
                      }
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={() => {
                    if (editNewTag.trim() && !editTags.includes(editNewTag.trim())) {
                      setEditTags([...editTags, editNewTag.trim()]);
                      setEditNewTag('');
                    }
                  }}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                >
                  Add
                </button>
              </div>
              {editTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {editTags.map((tag, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 text-sm rounded-md"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => setEditTags(editTags.filter((t) => t !== tag))}
                        className="text-blue-400 hover:text-blue-600 ml-0.5"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Parent Culture */}
            {selectedEntry.entry_type !== 'culture' && editAvailableCultures.length > 0 && (
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                  Parent Culture
                </label>
                <select
                  value={editParentCultureId}
                  onChange={(e) => setEditParentCultureId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value="">None</option>
                  {editAvailableCultures.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        ) : (
          /* Read-only detail view */
          <div className="max-w-3xl mx-auto p-6">
            {/* Header row */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{TYPE_ICONS[selectedEntry.entry_type] || '📄'}</span>
                <h2 className="text-2xl font-bold text-gray-900">{selectedEntry.title}</h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={startEditing}
                  className="px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => {
                    setMergeSearchQuery('');
                    setShowMergePicker(true);
                  }}
                  className="px-3 py-1.5 text-sm text-purple-600 border border-purple-300 rounded-md hover:bg-purple-50"
                >
                  Merge Into...
                </button>
                <button
                  onClick={() => handleDeleteEntry(selectedEntry.id)}
                  className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Sub-header */}
            <div className="flex items-center gap-3 mb-6 text-sm text-gray-500 flex-wrap">
              <span className="capitalize">{selectedEntry.entry_type.replace(/_/g, ' ')}</span>
              <span className="text-gray-300">|</span>
              <StatusSelector
                status={selectedEntry.status as WikiEntryStatus}
                onChange={(status) => handleUpdateEntry(selectedEntry.id, { status })}
              />
              <span className="text-gray-300">|</span>
              <span>Created {new Date(selectedEntry.created_at).toLocaleDateString()}</span>
              {selectedEntry.confidence_score < 1 && (
                <>
                  <span className="text-gray-300">|</span>
                  <span>Confidence: {Math.round(selectedEntry.confidence_score * 100)}%</span>
                </>
              )}
            </div>

            {/* Summary */}
            {selectedEntry.summary && (
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Summary</h3>
                <p className="text-base text-gray-700 leading-relaxed">{selectedEntry.summary}</p>
              </div>
            )}

            {/* Content */}
            {selectedEntry.content && (
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Content</h3>
                <div className="prose prose-gray max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {selectedEntry.content}
                </div>
              </div>
            )}

            {/* Aliases */}
            {selectedEntry.aliases && selectedEntry.aliases.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Aliases</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedEntry.aliases.map((alias, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 bg-gray-100 text-gray-600 text-sm rounded-md"
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {selectedEntry.tags && selectedEntry.tags.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedEntry.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 bg-blue-100 text-blue-700 text-sm rounded-md"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Culture Members (shown when viewing a culture entry) */}
            {selectedEntry.entry_type === 'culture' && cultureMembers.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                  Members ({cultureMembers.length})
                </h3>
                <div className="space-y-2">
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
                              className="flex items-center gap-2 pl-2 py-1 cursor-pointer hover:bg-gray-50 rounded"
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
              <div className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                  Cultures
                </h3>
                <div className="space-y-2">
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
              <div className="mb-6">
                <button
                  onClick={() => setShowCultureLinks(true)}
                  className="px-4 py-2 text-sm border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 flex items-center gap-2"
                >
                  <span>🎭</span>
                  <span>Link to Culture</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ==================== Modals ==================== */}

      {/* Editor Modal (new entries only) */}
      {showEditor && !selectedEntry && (
        <WikiEntryEditor
          entry={null}
          worldId={world.id}
          onSave={handleCreateEntry as (data: WikiEntryCreate | WikiEntryUpdate) => Promise<void>}
          onClose={() => setShowEditor(false)}
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
            cultureApi.getEntityCultures(selectedEntry.id).then(setEntityCultures).catch(() => {});
          }}
        />
      )}

      {/* Merge Picker Modal */}
      {showMergePicker && selectedEntry && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Merge "{selectedEntry.title}" into...
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Select the target entry. The current entry will be deleted and its data merged into the target.
              </p>
            </div>
            <div className="p-4">
              <input
                type="text"
                placeholder="Search entries..."
                value={mergeSearchQuery}
                onChange={(e) => setMergeSearchQuery(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 mb-3"
                autoFocus
              />
              <div className="max-h-64 overflow-y-auto space-y-1">
                {entries
                  .filter((e) => {
                    if (e.id === selectedEntry.id) return false;
                    if (!mergeSearchQuery.trim()) return true;
                    const q = mergeSearchQuery.toLowerCase();
                    return (
                      e.title.toLowerCase().includes(q) ||
                      e.aliases?.some((a) => a.toLowerCase().includes(q))
                    );
                  })
                  .sort((a, b) => {
                    // Same type first
                    const aMatch = a.entry_type === selectedEntry.entry_type ? 0 : 1;
                    const bMatch = b.entry_type === selectedEntry.entry_type ? 0 : 1;
                    if (aMatch !== bMatch) return aMatch - bMatch;
                    return a.title.localeCompare(b.title);
                  })
                  .slice(0, 50)
                  .map((e) => (
                    <button
                      key={e.id}
                      onClick={() => handleMerge(e.id)}
                      disabled={isMerging}
                      className="w-full text-left px-3 py-2 text-sm rounded hover:bg-purple-50 flex items-center gap-2 disabled:opacity-50"
                    >
                      <span>{TYPE_ICONS[e.entry_type] || '📄'}</span>
                      <span className="flex-1 truncate">{e.title}</span>
                      <span className="text-xs text-gray-400 capitalize">
                        {e.entry_type.replace(/_/g, ' ')}
                      </span>
                    </button>
                  ))}
                {entries.filter((e) => e.id !== selectedEntry.id).length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No other entries to merge into</p>
                )}
              </div>
            </div>
            <div className="p-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowMergePicker(false)}
                disabled={isMerging}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
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
