/**
 * ChapterCorkboard - Card-based chapter view (Scrivener-like corkboard)
 * Displays chapters as visual cards in a grid layout with drag-and-drop reordering
 */

import { useState, useEffect, useCallback } from 'react';
import { useChapterStore } from '@/stores/chapterStore';
import { chaptersApi, type ChapterTree, type DocumentType } from '@/lib/api';

// Icons for different document types
const DOCUMENT_TYPE_ICONS: Record<DocumentType, string> = {
  CHAPTER: '📄',
  FOLDER: '📁',
  CHARACTER_SHEET: '👤',
  NOTES: '📝',
  TITLE_PAGE: '📜',
};

// Get icon for a chapter tree node
function getDocumentIcon(node: ChapterTree): string {
  const docType = node.document_type || (node.is_folder ? 'FOLDER' : 'CHAPTER');
  return DOCUMENT_TYPE_ICONS[docType] || '📄';
}
import { toast } from '@/stores/toastStore';
import { confirm } from '@/stores/confirmStore';
import { retry, getErrorMessage } from '@/lib/retry';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  closestCenter,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface ChapterCorkboardProps {
  manuscriptId: string;
  onChapterSelect?: (chapterId: string) => void;
  hideHeader?: boolean;
}

interface ChapterCardProps {
  node: ChapterTree;
  isActive: boolean;
  onClick: () => void;
  onRename: (newTitle: string) => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

function ChapterCard({
  node,
  isActive,
  onClick,
  onRename,
  onDelete,
  onDuplicate,
}: ChapterCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: node.id,
    data: { type: 'chapter', node },
  });

  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(node.title);
  const [showMenu, setShowMenu] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleRenameSubmit = () => {
    if (renameValue.trim() && renameValue !== node.title) {
      onRename(renameValue.trim());
    } else {
      setRenameValue(node.title);
    }
    setIsRenaming(false);
  };

  // Calculate color based on word count
  const getProgressColor = () => {
    if (node.word_count === 0) return 'bg-slate-200';
    if (node.word_count < 500) return 'bg-amber-300';
    if (node.word_count < 2000) return 'bg-bronze/60';
    return 'bg-green-500/60';
  };

  // Close menu when clicking outside
  useEffect(() => {
    if (showMenu) {
      const handleClick = () => setShowMenu(false);
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [showMenu]);

  if (node.is_folder) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        className="bg-amber-50 border-2 border-amber-300 rounded-lg p-4 min-h-[140px] cursor-pointer hover:shadow-md transition-shadow"
        onClick={onClick}
        {...attributes}
        {...listeners}
      >
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl relative">
            {getDocumentIcon(node)}
            {node.linked_entity_id && (
              <span className="absolute -bottom-1 -right-1 text-xs" title="Linked to Codex">🔗</span>
            )}
          </span>
          <h3 className="font-garamond font-semibold text-midnight truncate flex-1">
            {node.title}
          </h3>
        </div>
        <p className="text-xs text-faded-ink">
          {node.children?.length || 0} items
        </p>
      </div>
    );
  }

  // Special styling for different document types
  const docType = node.document_type || 'CHAPTER';
  const isSpecialDocument = docType !== 'CHAPTER';
  const cardBgClass = isSpecialDocument ? 'bg-blue-50' : 'bg-vellum';
  const borderClass = isActive
    ? 'border-bronze ring-2 ring-bronze/30'
    : isSpecialDocument
    ? 'border-blue-200 hover:border-blue-400'
    : 'border-slate-ui hover:border-bronze/50';

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        relative ${cardBgClass} border-2 rounded-lg overflow-hidden min-h-[160px]
        transition-all cursor-pointer
        ${borderClass}
        ${isDragging ? 'shadow-xl z-10' : 'hover:shadow-md'}
      `}
      {...attributes}
      {...listeners}
    >
      {/* Progress indicator bar at top */}
      <div className={`h-1.5 ${getProgressColor()}`} />

      {/* Card content */}
      <div className="p-3" onClick={onClick}>
        {/* Header with title and document type icon */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {isSpecialDocument && (
              <span className="text-base flex-shrink-0 relative" title={docType.replace('_', ' ')}>
                {getDocumentIcon(node)}
                {node.linked_entity_id && (
                  <span className="absolute -bottom-1 -right-1 text-[10px]" title="Linked to Codex">🔗</span>
                )}
              </span>
            )}
            {isRenaming ? (
              <input
                type="text"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={handleRenameSubmit}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRenameSubmit();
                  if (e.key === 'Escape') {
                    setRenameValue(node.title);
                    setIsRenaming(false);
                  }
                }}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 px-2 py-1 text-sm border border-bronze rounded focus:outline-none focus:ring-2 focus:ring-bronze bg-white text-midnight"
                autoFocus
              />
            ) : (
              <h3
                className="font-garamond font-semibold text-midnight text-sm line-clamp-2 flex-1"
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  setIsRenaming(true);
                }}
              >
                {node.title}
              </h3>
            )}
          </div>

          {/* Menu button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
            className="p-1 text-faded-ink hover:text-midnight rounded"
          >
            <span className="text-xs">•••</span>
          </button>
        </div>

        {/* Word count */}
        <div className="flex items-center gap-2 text-xs text-faded-ink mb-2">
          <span className="font-mono">{node.word_count.toLocaleString()}</span>
          <span>words</span>
        </div>

        {/* Visual placeholder for summary */}
        <div className="space-y-1.5">
          <div className="h-2 bg-slate-ui/30 rounded w-full" />
          <div className="h-2 bg-slate-ui/30 rounded w-4/5" />
          <div className="h-2 bg-slate-ui/30 rounded w-3/5" />
        </div>
      </div>

      {/* Dropdown menu */}
      {showMenu && (
        <div
          className="absolute top-8 right-2 bg-white border border-slate-ui shadow-lg rounded-sm z-50 py-1 min-w-[140px]"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              setShowMenu(false);
              setIsRenaming(true);
            }}
            className="w-full text-left px-4 py-2 text-sm hover:bg-slate-ui/20 text-midnight"
          >
            Rename
          </button>
          <button
            onClick={() => {
              setShowMenu(false);
              onDuplicate();
            }}
            className="w-full text-left px-4 py-2 text-sm hover:bg-slate-ui/20 text-midnight"
          >
            Duplicate
          </button>
          <hr className="my-1 border-slate-ui" />
          <button
            onClick={() => {
              setShowMenu(false);
              onDelete();
            }}
            className="w-full text-left px-4 py-2 text-sm hover:bg-red-50 text-red-600"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}

export default function ChapterCorkboard({
  manuscriptId,
  onChapterSelect,
  hideHeader = false,
}: ChapterCorkboardProps) {
  const {
    chapterTree,
    setChapterTree,
    currentChapterId,
    setCurrentChapter,
  } = useChapterStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creatingChapter, setCreatingChapter] = useState(false);
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Sensors for drag-and-drop
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Load chapter tree
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

  useEffect(() => {
    loadChapterTree();
  }, [manuscriptId]);

  // Flatten tree for corkboard (only show root-level items)
  const flattenedChapters = chapterTree;
  const chapterIds = flattenedChapters.map((ch) => ch.id);

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
      toast.success('Chapter created');
      setCurrentChapter(newChapter.id);
      onChapterSelect?.(newChapter.id);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setCreatingChapter(false);
    }
  };

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
      toast.success('Folder created');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setCreatingFolder(false);
    }
  };

  const handleRename = async (chapterId: string, newTitle: string) => {
    try {
      await chaptersApi.updateChapter(chapterId, { title: newTitle });
      await loadChapterTree();
      toast.success('Renamed');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleDelete = async (chapterId: string) => {
    const node = flattenedChapters.find((ch) => ch.id === chapterId);
    if (!node) return;

    const confirmMessage = node.is_folder
      ? `Delete "${node.title}" and all its contents?`
      : `Delete "${node.title}"?`;

    if (!(await confirm({ title: 'Delete', message: confirmMessage, variant: 'danger', confirmLabel: 'Delete' }))) return;

    try {
      await chaptersApi.deleteChapter(chapterId);

      // Clear current chapter if it was the deleted one
      if (currentChapterId === chapterId) {
        setCurrentChapter(null);
      }

      await loadChapterTree();
      toast.success('Deleted');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleDuplicate = async (chapterId: string) => {
    const node = flattenedChapters.find((ch) => ch.id === chapterId);
    if (!node) return;

    try {
      const chapter = await chaptersApi.getChapter(chapterId);
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
      toast.success('Duplicated');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleDragStart = (event: DragEndEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) return;

    const oldIndex = flattenedChapters.findIndex((ch) => ch.id === active.id);
    const newIndex = flattenedChapters.findIndex((ch) => ch.id === over.id);

    if (oldIndex === -1 || newIndex === -1) return;

    // Optimistic update
    const newTree = [...flattenedChapters];
    const [movedItem] = newTree.splice(oldIndex, 1);
    newTree.splice(newIndex, 0, movedItem);
    setChapterTree(newTree);

    try {
      await chaptersApi.updateChapter(active.id as string, {
        order_index: newIndex,
      });
      await loadChapterTree();
    } catch (err) {
      toast.error(getErrorMessage(err));
      await loadChapterTree();
    }
  };

  const handleChapterClick = (chapterId: string, isFolder: boolean) => {
    if (!isFolder) {
      setCurrentChapter(chapterId);
      onChapterSelect?.(chapterId);
    }
  };

  const activeNode = activeId
    ? flattenedChapters.find((ch) => ch.id === activeId)
    : null;

  // Loading state
  if (loading && chapterTree.length === 0) {
    return (
      <div className="p-4 bg-white border-r border-slate-ui h-full">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-ui/30 rounded w-1/2" />
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-slate-ui/30 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col ${hideHeader ? '' : 'bg-white border-r border-slate-ui'}`}>
      {/* Header - shown only when not embedded */}
      {!hideHeader && (
        <div className="p-4 border-b border-slate-ui">
          <h2 className="font-garamond font-semibold text-midnight mb-3">
            Corkboard
          </h2>

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
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={loadChapterTree}
            className="mt-2 px-3 py-1 text-xs bg-red-600 text-white rounded-sm"
          >
            Retry
          </button>
        </div>
      )}

      {/* Corkboard grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {flattenedChapters.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-sm text-faded-ink mb-2">No chapters yet</p>
            <p className="text-xs text-faded-ink/70">
              Create your first chapter to start writing
            </p>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={chapterIds}
              strategy={rectSortingStrategy}
            >
              <div className="grid grid-cols-2 gap-3">
                {flattenedChapters.map((node) => (
                  <ChapterCard
                    key={node.id}
                    node={node}
                    isActive={currentChapterId === node.id}
                    onClick={() => handleChapterClick(node.id, node.is_folder)}
                    onRename={(title) => handleRename(node.id, title)}
                    onDelete={() => handleDelete(node.id)}
                    onDuplicate={() => handleDuplicate(node.id)}
                  />
                ))}
              </div>
            </SortableContext>

            {/* Drag overlay */}
            <DragOverlay>
              {activeNode ? (
                <div className="bg-vellum border-2 border-bronze shadow-xl rounded-lg p-3 min-h-[100px] opacity-90">
                  <div className="flex items-center gap-2">
                    <span>{getDocumentIcon(activeNode)}</span>
                    <span className="font-garamond font-semibold text-sm">
                      {activeNode.title}
                    </span>
                  </div>
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {/* Footer stats */}
      <div className="px-4 py-2 border-t border-slate-ui bg-slate-ui/10">
        <div className="flex justify-between text-xs text-faded-ink">
          <span>
            {flattenedChapters.filter((ch) => !ch.is_folder).length} chapters
          </span>
          <span>
            {flattenedChapters
              .reduce((sum, ch) => sum + ch.word_count, 0)
              .toLocaleString()}{' '}
            words
          </span>
        </div>
      </div>
    </div>
  );
}
