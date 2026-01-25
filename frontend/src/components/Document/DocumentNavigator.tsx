/**
 * DocumentNavigator - Hierarchical chapter/folder navigation (Scrivener-like)
 * Displays chapters and folders in a tree structure with drag-and-drop reordering
 * Supports both tree view and corkboard (card) view
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useChapterStore } from '@/stores/chapterStore';
import { chaptersApi, type ChapterTree } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import { ChapterTreeSkeleton } from '@/components/Common/SkeletonLoader';
import { retry, getErrorMessage } from '@/lib/retry';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  pointerWithin,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import ChapterCorkboard from './ChapterCorkboard';

export type ViewMode = 'tree' | 'corkboard';

interface DocumentNavigatorProps {
  manuscriptId: string;
  onChapterSelect?: (chapterId: string) => void;
  defaultView?: ViewMode;
}

interface SortableTreeNodeProps {
  node: ChapterTree;
  level: number;
  currentChapterId: string | null;
  expandedFolders: Set<string>;
  onChapterClick: (chapterId: string, isFolder: boolean) => void;
  onToggleFolder: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  onDelete: (id: string) => void;
  onDuplicate?: (id: string) => void;
}

function SortableTreeNode({
  node,
  level,
  currentChapterId,
  expandedFolders,
  onChapterClick,
  onToggleFolder,
  onRename,
  onDelete,
  onDuplicate,
}: SortableTreeNodeProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: node.id,
    data: {
      type: 'chapter',
      node,
    },
  });

  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(node.title);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });
  const inputRef = useRef<HTMLInputElement>(null);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const isExpanded = expandedFolders.has(node.id);
  const isActive = currentChapterId === node.id;
  const childIds = node.children?.map(child => child.id) || [];

  // Focus input when entering rename mode
  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isRenaming]);

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsRenaming(true);
  };

  const handleRenameSubmit = () => {
    if (renameValue.trim() && renameValue !== node.title) {
      onRename(node.id, renameValue.trim());
    } else {
      setRenameValue(node.title);
    }
    setIsRenaming(false);
  };

  const handleRenameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      setRenameValue(node.title);
      setIsRenaming(false);
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenuPos({ x: e.clientX, y: e.clientY });
    setShowContextMenu(true);
  };

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClick = () => setShowContextMenu(false);
    if (showContextMenu) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [showContextMenu]);

  return (
    <div ref={setNodeRef} style={style}>
      <div
        onDoubleClick={handleDoubleClick}
        onContextMenu={handleContextMenu}
        className={`
          w-full text-left px-3 py-2 text-sm font-sans flex items-center gap-2 transition-colors
          ${isActive ? 'bg-bronze text-white' : 'text-midnight hover:bg-slate-ui/20'}
          ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}
        `}
        style={{ paddingLeft: `${12 + level * 16}px` }}
        {...attributes}
        {...listeners}
      >
        {/* Folder icon or chevron */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onChapterClick(node.id, node.is_folder);
          }}
          className="flex items-center gap-2 flex-1"
        >
          {node.is_folder ? (
            <span className="text-base">
              {isExpanded ? '📂' : '📁'}
            </span>
          ) : (
            <span className="text-base">📄</span>
          )}

          {/* Title or rename input */}
          {isRenaming ? (
            <input
              ref={inputRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={handleRenameKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 px-2 py-1 text-sm border border-bronze rounded focus:outline-none focus:ring-2 focus:ring-bronze bg-white text-midnight"
            />
          ) : (
            <span className="flex-1 truncate">{node.title}</span>
          )}
        </button>

        {/* Word count badge for chapters */}
        {!node.is_folder && node.word_count > 0 && (
          <span className="text-xs text-faded-ink opacity-60 ml-auto">
            {node.word_count.toLocaleString()}w
          </span>
        )}
      </div>

      {/* Context Menu */}
      {showContextMenu && (
        <div
          className="fixed bg-white border border-slate-ui shadow-lg rounded-sm z-50 py-1 min-w-[160px]"
          style={{ left: contextMenuPos.x, top: contextMenuPos.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              setShowContextMenu(false);
              setIsRenaming(true);
            }}
            className="w-full text-left px-4 py-2 text-sm hover:bg-slate-ui/20 text-midnight"
          >
            Rename
          </button>
          {onDuplicate && (
            <button
              onClick={() => {
                setShowContextMenu(false);
                onDuplicate(node.id);
              }}
              className="w-full text-left px-4 py-2 text-sm hover:bg-slate-ui/20 text-midnight"
            >
              Duplicate
            </button>
          )}
          <hr className="my-1 border-slate-ui" />
          <button
            onClick={() => {
              setShowContextMenu(false);
              onDelete(node.id);
            }}
            className="w-full text-left px-4 py-2 text-sm hover:bg-red-50 text-red-600"
          >
            Delete
          </button>
        </div>
      )}

      {/* Children (if folder is expanded) */}
      {node.is_folder && isExpanded && node.children && node.children.length > 0 && (
        <SortableContext items={childIds} strategy={verticalListSortingStrategy}>
          <div>
            {node.children.map((child) => (
              <SortableTreeNode
                key={child.id}
                node={child}
                level={level + 1}
                currentChapterId={currentChapterId}
                expandedFolders={expandedFolders}
                onChapterClick={onChapterClick}
                onToggleFolder={onToggleFolder}
                onRename={onRename}
                onDelete={onDelete}
                onDuplicate={onDuplicate}
              />
            ))}
          </div>
        </SortableContext>
      )}
    </div>
  );
}

export default function DocumentNavigator({ manuscriptId, onChapterSelect, defaultView = 'tree' }: DocumentNavigatorProps) {
  const {
    chapterTree,
    setChapterTree,
    currentChapterId,
    setCurrentChapter,
    expandedFolders,
    toggleFolder,
    expandFolder,
  } = useChapterStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [creatingChapter, setCreatingChapter] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  // View mode: tree or corkboard
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem('maxwell-document-view-mode');
    return (saved as ViewMode) || defaultView;
  });

  // Persist view mode preference
  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem('maxwell-document-view-mode', mode);
  };

  // Drag-and-drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Helper: Find parent ID of a node
  const findParentId = (tree: ChapterTree[], nodeId: string, parentId: string | null = null): string | null => {
    for (const node of tree) {
      if (node.id === nodeId) {
        return parentId;
      }
      if (node.children && node.children.length > 0) {
        const found = findParentId(node.children, nodeId, node.id);
        if (found !== undefined) {
          return found;
        }
      }
    }
    return undefined as any;
  };

  // Helper: Find node by ID in tree
  const findNode = (tree: ChapterTree[], nodeId: string): ChapterTree | null => {
    for (const node of tree) {
      if (node.id === nodeId) {
        return node;
      }
      if (node.children && node.children.length > 0) {
        const found = findNode(node.children, nodeId);
        if (found) return found;
      }
    }
    return null;
  };

  // Helper: Remove node from tree
  const removeNode = (tree: ChapterTree[], nodeId: string): ChapterTree[] => {
    return tree.filter(node => {
      if (node.id === nodeId) return false;
      if (node.children && node.children.length > 0) {
        node.children = removeNode(node.children, nodeId);
      }
      return true;
    });
  };

  // Helper: Add node to parent in tree
  const addNodeToParent = (tree: ChapterTree[], node: ChapterTree, parentId: string | null, index: number): ChapterTree[] => {
    if (parentId === null) {
      // Add to root
      const newTree = [...tree];
      newTree.splice(index, 0, node);
      return newTree;
    }

    return tree.map(item => {
      if (item.id === parentId) {
        const newChildren = [...(item.children || [])];
        newChildren.splice(index, 0, node);
        return { ...item, children: newChildren };
      }
      if (item.children && item.children.length > 0) {
        return { ...item, children: addNodeToParent(item.children, node, parentId, index) };
      }
      return item;
    });
  };

  // Load chapter tree on mount and when manuscript changes
  useEffect(() => {
    loadChapterTree();
  }, [manuscriptId]);

  // Memoized chapter tree loading with retry
  const loadChapterTree = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const tree = await retry(() => chaptersApi.getChapterTree(manuscriptId));
      setChapterTree(tree);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [manuscriptId, setChapterTree]);

  const handleCreateFolder = async () => {
    try {
      setCreatingFolder(true);
      await chaptersApi.createChapter({
        manuscript_id: manuscriptId,
        title: 'New Folder',
        is_folder: true,
        order_index: chapterTree.length,
      });
      await loadChapterTree();
      toast.success('Folder created successfully');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setCreatingFolder(false);
    }
  };

  const handleCreateChapter = async () => {
    try {
      setCreatingChapter(true);
      const newChapter = await chaptersApi.createChapter({
        manuscript_id: manuscriptId,
        title: 'Untitled Chapter',
        is_folder: false,
        order_index: chapterTree.length,
      });
      await loadChapterTree();
      toast.success('Chapter created successfully');
      setCurrentChapter(newChapter.id);
      onChapterSelect?.(newChapter.id);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setCreatingChapter(false);
    }
  };

  const handleChapterClick = (chapterId: string, isFolder: boolean) => {
    if (isFolder) {
      toggleFolder(chapterId);
    } else {
      setCurrentChapter(chapterId);
      onChapterSelect?.(chapterId);
    }
  };

  const handleDragStart = (event: DragEndEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const overNode = findNode(chapterTree, over.id as string);

    // Auto-expand folders when dragging over them
    if (overNode && overNode.is_folder && !expandedFolders.has(over.id as string)) {
      setTimeout(() => {
        expandFolder(over.id as string);
      }, 500);
    }
  };

  const handleRename = async (chapterId: string, newTitle: string) => {
    try {
      await chaptersApi.updateChapter(chapterId, { title: newTitle });
      await loadChapterTree();
      toast.success('Renamed successfully');
    } catch (err) {
      console.error('Failed to rename chapter:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const handleDelete = async (chapterId: string) => {
    const node = findNode(chapterTree, chapterId);
    if (!node) return;

    const confirmMessage = node.is_folder
      ? `Delete "${node.title}" and all its contents?`
      : `Delete "${node.title}"?`;

    if (!confirm(confirmMessage)) return;

    try {
      await chaptersApi.deleteChapter(chapterId);
      await loadChapterTree();
      toast.success('Deleted successfully');
    } catch (err) {
      console.error('Failed to delete chapter:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const handleDuplicate = async (chapterId: string) => {
    const node = findNode(chapterTree, chapterId);
    if (!node) return;

    try {
      // Fetch full chapter data
      const chapter = await chaptersApi.getChapter(chapterId);

      // Create duplicate with " (Copy)" suffix
      await chaptersApi.createChapter({
        manuscript_id: manuscriptId,
        title: `${chapter.title} (Copy)`,
        is_folder: chapter.is_folder,
        parent_id: chapter.parent_id || undefined,
        order_index: chapter.order_index + 1,
        lexical_state: chapter.lexical_state,
        content: chapter.content,
      });

      await loadChapterTree();
      toast.success('Duplicated successfully');
    } catch (err) {
      console.error('Failed to duplicate chapter:', err);
      toast.error(getErrorMessage(err));
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const activeNode = findNode(chapterTree, active.id as string);
    const overNode = findNode(chapterTree, over.id as string);

    if (!activeNode || !overNode) {
      return;
    }

    const activeParentId = findParentId(chapterTree, active.id as string);
    const overParentId = findParentId(chapterTree, over.id as string);

    // Prevent dropping a folder into itself or its descendants
    if (activeNode.is_folder) {
      const isDescendant = (node: ChapterTree, ancestorId: string): boolean => {
        if (node.id === ancestorId) return true;
        if (node.children) {
          return node.children.some(child => isDescendant(child, ancestorId));
        }
        return false;
      };
      if (isDescendant(activeNode, over.id as string)) {
        return;
      }
    }

    // Check if we're dropping on a folder or next to an item
    let newParentId: string | null = overParentId;
    let newIndex = 0;

    // If dropping on a folder, place inside it
    if (overNode.is_folder) {
      newParentId = over.id as string;
      newIndex = overNode.children?.length || 0;
    } else {
      // Dropping next to an item - use same parent
      newParentId = overParentId;

      // Find siblings
      const siblings = newParentId === null
        ? chapterTree
        : findNode(chapterTree, newParentId)?.children || [];

      newIndex = siblings.findIndex(node => node.id === over.id);

      // If dragging from same parent, adjust index
      if (activeParentId === newParentId) {
        const activeIndex = siblings.findIndex(node => node.id === active.id);
        if (activeIndex < newIndex) {
          newIndex--;
        }
      }
    }

    // Optimistically update UI
    let newTree = [...chapterTree];
    newTree = removeNode(newTree, active.id as string);
    newTree = addNodeToParent(newTree, activeNode, newParentId, newIndex);
    setChapterTree(newTree);

    try {
      // Update backend with new parent and order
      await chaptersApi.updateChapter(active.id as string, {
        parent_id: newParentId,
        order_index: newIndex,
      });

      // Reload to ensure consistency
      await loadChapterTree();
    } catch (err) {
      console.error('Failed to move chapter:', err);
      toast.error(getErrorMessage(err));
      // Reload to revert optimistic update
      await loadChapterTree();
    }
  };

  // Get all item IDs for drag-and-drop
  const rootItemIds = chapterTree.map((node) => node.id);
  const activeNode = activeId ? findNode(chapterTree, activeId) : null;

  // Show skeleton loader while initially loading
  const showSkeleton = loading && chapterTree.length === 0;

  // If corkboard view is selected, render ChapterCorkboard instead
  if (viewMode === 'corkboard') {
    return (
      <div className="h-full flex flex-col bg-white border-r border-slate-ui">
        {/* Header with view toggle */}
        <div className="p-4 border-b border-slate-ui">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-garamond font-semibold text-midnight">Corkboard</h2>
            <ViewToggle viewMode={viewMode} onChange={handleViewModeChange} />
          </div>
          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleCreateChapter}
              disabled={creatingChapter}
              className="flex-1 px-3 py-2 text-xs font-sans bg-bronze text-white hover:bg-bronze/90 disabled:opacity-50"
              style={{ borderRadius: '2px' }}
            >
              {creatingChapter ? '...' : '+ Chapter'}
            </button>
            <button
              onClick={handleCreateFolder}
              disabled={creatingFolder}
              className="flex-1 px-3 py-2 text-xs font-sans bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20 disabled:opacity-50"
              style={{ borderRadius: '2px' }}
            >
              {creatingFolder ? '...' : '+ Folder'}
            </button>
          </div>
        </div>
        {/* Render corkboard content */}
        <div className="flex-1 overflow-hidden">
          <ChapterCorkboard
            manuscriptId={manuscriptId}
            onChapterSelect={onChapterSelect}
            hideHeader
          />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white border-r border-slate-ui">
      {/* Header with view toggle */}
      <div className="p-4 border-b border-slate-ui">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-garamond font-semibold text-midnight">Manuscript</h2>
          <ViewToggle viewMode={viewMode} onChange={handleViewModeChange} />
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleCreateChapter}
            disabled={creatingChapter}
            className="flex-1 px-3 py-2 text-xs font-sans bg-bronze text-white hover:bg-bronze/90 disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            {creatingChapter ? '...' : '+ Chapter'}
          </button>
          <button
            onClick={handleCreateFolder}
            disabled={creatingFolder}
            className="flex-1 px-3 py-2 text-xs font-sans bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20 disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            {creatingFolder ? '...' : '+ Folder'}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm text-red-600 flex-1">{error}</p>
            <button
              onClick={loadChapterTree}
              disabled={loading}
              className="px-3 py-1 text-xs font-sans bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 rounded-sm"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Tree view */}
      <div className="flex-1 overflow-y-auto">
        {showSkeleton ? (
          <ChapterTreeSkeleton />
        ) : chapterTree.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-faded-ink font-sans mb-3">
              No chapters yet
            </p>
            <p className="text-xs text-faded-ink/70">
              Create a chapter to start writing
            </p>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={pointerWithin}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <SortableContext items={rootItemIds} strategy={verticalListSortingStrategy}>
              <div>
                {chapterTree.map((node) => (
                  <SortableTreeNode
                    key={node.id}
                    node={node}
                    level={0}
                    currentChapterId={currentChapterId}
                    expandedFolders={expandedFolders}
                    onChapterClick={handleChapterClick}
                    onToggleFolder={toggleFolder}
                    onRename={handleRename}
                    onDelete={handleDelete}
                    onDuplicate={handleDuplicate}
                  />
                ))}
              </div>
            </SortableContext>

            {/* Drag overlay for visual feedback */}
            <DragOverlay>
              {activeNode ? (
                <div className="bg-white border-2 border-bronze shadow-lg px-3 py-2 text-sm font-sans flex items-center gap-2">
                  <span className="text-base">
                    {activeNode.is_folder ? '📁' : '📄'}
                  </span>
                  <span>{activeNode.title}</span>
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        )}
      </div>
    </div>
  );
}

/**
 * View Toggle Component
 * Switches between tree and corkboard views
 */
interface ViewToggleProps {
  viewMode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

function ViewToggle({ viewMode, onChange }: ViewToggleProps) {
  return (
    <div className="flex bg-slate-ui/30 rounded-sm p-0.5">
      <button
        onClick={() => onChange('tree')}
        title="Tree View"
        className={`
          px-2 py-1 text-xs font-sans transition-colors rounded-sm
          ${viewMode === 'tree'
            ? 'bg-white text-midnight shadow-sm'
            : 'text-faded-ink hover:text-midnight'
          }
        `}
      >
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 3h14v2H1V3zm2 4h12v2H3V7zm2 4h10v2H5v-2z" />
          </svg>
          <span className="hidden sm:inline">Tree</span>
        </span>
      </button>
      <button
        onClick={() => onChange('corkboard')}
        title="Corkboard View"
        className={`
          px-2 py-1 text-xs font-sans transition-colors rounded-sm
          ${viewMode === 'corkboard'
            ? 'bg-white text-midnight shadow-sm'
            : 'text-faded-ink hover:text-midnight'
          }
        `}
      >
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 1h6v6H1V1zm8 0h6v6H9V1zM1 9h6v6H1V9zm8 0h6v6H9V9z" />
          </svg>
          <span className="hidden sm:inline">Cards</span>
        </span>
      </button>
    </div>
  );
}
