/**
 * NotesEditor - Simplified editor for notes documents
 * Basic text editing with tags/category support
 */

import { useState, useEffect, useCallback } from 'react';
import { chaptersApi, type Chapter } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import { getErrorMessage } from '@/lib/retry';

interface NotesEditorProps {
  chapterId: string;
  onTitleChange?: (title: string) => void;
}

interface NotesMetadata {
  tags: string[];
  category: string;
}

export default function NotesEditor({ chapterId, onTitleChange }: NotesEditorProps) {
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Notes content
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState<NotesMetadata>({
    tags: [],
    category: '',
  });

  // Tag input
  const [tagInput, setTagInput] = useState('');

  // Load chapter data
  useEffect(() => {
    const loadChapter = async () => {
      try {
        setLoading(true);
        const data = await chaptersApi.getChapter(chapterId);
        setChapter(data);
        setTitle(data.title);
        setContent(data.content || '');

        // Extract metadata
        const meta = data.document_metadata || {};
        setMetadata({
          tags: (meta.tags as string[]) || [],
          category: (meta.category as string) || '',
        });
      } catch (err) {
        toast.error(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadChapter();
  }, [chapterId]);

  // Auto-save
  const saveChanges = useCallback(async () => {
    if (!chapter || !hasUnsavedChanges) return;

    try {
      setSaving(true);
      await chaptersApi.updateChapter(chapterId, {
        title,
        content,
        document_metadata: {
          ...chapter.document_metadata,
          tags: metadata.tags,
          category: metadata.category,
        },
      });
      setHasUnsavedChanges(false);
      onTitleChange?.(title);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }, [chapter, chapterId, title, content, metadata, hasUnsavedChanges, onTitleChange]);

  // Auto-save after 2 seconds of inactivity
  useEffect(() => {
    if (!hasUnsavedChanges) return;

    const timer = setTimeout(() => {
      saveChanges();
    }, 2000);

    return () => clearTimeout(timer);
  }, [hasUnsavedChanges, saveChanges]);

  // Add tag
  const handleAddTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !metadata.tags.includes(tag)) {
      setMetadata((prev) => ({ ...prev, tags: [...prev.tags, tag] }));
      setHasUnsavedChanges(true);
    }
    setTagInput('');
  };

  // Remove tag
  const handleRemoveTag = (tagToRemove: string) => {
    setMetadata((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tagToRemove),
    }));
    setHasUnsavedChanges(true);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-faded-ink">Loading notes...</div>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-red-600">Notes not found</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-vellum overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📝</span>
            <input
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setHasUnsavedChanges(true);
              }}
              placeholder="Note title..."
              className="font-garamond text-xl font-semibold text-midnight bg-transparent border-none focus:outline-none focus:ring-0"
            />
          </div>

          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <span className="text-xs text-amber-600 font-medium">Unsaved changes</span>
            )}
            {saving && <span className="text-xs text-bronze">Saving...</span>}

            <button
              onClick={saveChanges}
              disabled={saving || !hasUnsavedChanges}
              className="px-3 py-1.5 text-xs font-sans bg-bronze text-white hover:bg-bronze/90 disabled:opacity-50 rounded-sm"
            >
              Save
            </button>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          {/* Category */}
          <select
            value={metadata.category}
            onChange={(e) => {
              setMetadata((prev) => ({ ...prev, category: e.target.value }));
              setHasUnsavedChanges(true);
            }}
            className="text-xs px-2 py-1 border border-slate-ui rounded-sm bg-vellum focus:outline-none focus:ring-1 focus:ring-bronze"
          >
            <option value="">No Category</option>
            <option value="research">Research</option>
            <option value="worldbuilding">Worldbuilding</option>
            <option value="plot">Plot Ideas</option>
            <option value="character">Character Notes</option>
            <option value="reference">Reference</option>
            <option value="todo">To-Do</option>
          </select>

          {/* Tags */}
          {metadata.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full"
            >
              #{tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="hover:text-red-600"
              >
                ×
              </button>
            </span>
          ))}

          {/* Add tag input */}
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddTag();
              }
            }}
            placeholder="Add tag..."
            className="text-xs px-2 py-1 border border-dashed border-slate-ui rounded-sm bg-transparent focus:outline-none focus:border-bronze w-24"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          <textarea
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              setHasUnsavedChanges(true);
            }}
            placeholder="Write your notes here..."
            className="w-full h-full min-h-[500px] p-4 text-base font-sans leading-relaxed bg-white border border-slate-ui rounded-lg focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze resize-none"
          />
        </div>
      </div>

      {/* Footer with word count */}
      <div className="px-6 py-2 border-t border-slate-ui bg-white/50">
        <div className="flex justify-between text-xs text-faded-ink">
          <span>{metadata.tags.length} tags</span>
          <span>{content.split(/\s+/).filter(Boolean).length} words</span>
        </div>
      </div>
    </div>
  );
}
