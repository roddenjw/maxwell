/**
 * QuickEntityModal Component
 * Minimal modal for quickly creating an entity from selected text.
 * Pre-fills the entity name with the selection.
 */

import { useState, useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection } from 'lexical';
import { $createEntityMentionNode } from './nodes/EntityMentionNode';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import { toast } from '@/stores/toastStore';
import { Z_INDEX } from '@/lib/zIndex';
import { EntityType } from '@/types/codex';

interface QuickEntityModalProps {
  manuscriptId: string;
  selectedText: string;
  position: { x: number; y: number };
  onClose: () => void;
  onCreated?: (entityId: string, entityName: string) => void;
}

const ENTITY_TYPES: { value: EntityType; label: string; icon: string }[] = [
  { value: EntityType.CHARACTER, label: 'Character', icon: '👤' },
  { value: EntityType.LOCATION, label: 'Location', icon: '📍' },
  { value: EntityType.ITEM, label: 'Item', icon: '🔮' },
  { value: EntityType.LORE, label: 'Lore', icon: '📜' },
];

export default function QuickEntityModal({
  manuscriptId,
  selectedText,
  position,
  onClose,
  onCreated,
}: QuickEntityModalProps) {
  const [editor] = useLexicalComposerContext();
  const { addEntity } = useCodexStore();

  const [name, setName] = useState(selectedText);
  const [type, setType] = useState<EntityType>(EntityType.CHARACTER);
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [insertMention, setInsertMention] = useState(true);

  const modalRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Focus name input on mount
  useEffect(() => {
    nameInputRef.current?.focus();
    nameInputRef.current?.select();
  }, []);

  // Close on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Delay adding listener to prevent immediate close
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  const handleCreate = async () => {
    if (!name.trim()) {
      toast.error('Entity name is required');
      return;
    }

    setIsCreating(true);

    try {
      // Create the entity
      const entity = await codexApi.createEntity({
        manuscript_id: manuscriptId,
        name: name.trim(),
        type,
        attributes: description ? { description } : {},
      });

      // Add to store
      addEntity(entity);

      // Insert entity mention at the selection if checkbox is checked
      if (insertMention) {
        editor.update(() => {
          const selection = $getSelection();
          if ($isRangeSelection(selection)) {
            // Delete the selected text and insert entity mention
            selection.removeText();
            const mentionNode = $createEntityMentionNode(entity.id, entity.name, entity.type);
            selection.insertNodes([mentionNode]);
          }
        });
      }

      toast.success(`Created ${type.toLowerCase()} "${name}"`);
      onCreated?.(entity.id, entity.name);
      onClose();
    } catch (error: any) {
      console.error('Failed to create entity:', error);
      toast.error(error.message || 'Failed to create entity');
    } finally {
      setIsCreating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCreate();
    }
  };

  // Calculate modal position (below or above the toolbar position)
  const modalTop = position.y + 60;
  const modalLeft = Math.max(20, Math.min(position.x - 100, window.innerWidth - 340));

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20"
        style={{ zIndex: Z_INDEX.MODAL_BACKDROP }}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className="fixed bg-white border-2 border-bronze shadow-2xl p-4 w-[320px] animate-fadeIn"
        style={{
          left: modalLeft,
          top: Math.min(modalTop, window.innerHeight - 400),
          zIndex: Z_INDEX.MODAL,
          borderRadius: '2px',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-serif font-bold text-lg text-midnight">
            Quick Create Entity
          </h3>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center text-faded-ink hover:text-midnight transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              ref={nameInputRef}
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Entity name"
              className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
              style={{ borderRadius: '2px' }}
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {ENTITY_TYPES.map((entityType) => (
                <button
                  key={entityType.value}
                  onClick={() => setType(entityType.value)}
                  className={`flex flex-col items-center gap-1 p-2 border transition-colors ${
                    type === entityType.value
                      ? 'border-bronze bg-bronze/10 text-bronze'
                      : 'border-slate-ui hover:border-bronze/50 text-midnight'
                  }`}
                  style={{ borderRadius: '2px' }}
                >
                  <span className="text-xl">{entityType.icon}</span>
                  <span className="text-xs font-sans">{entityType.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Description (optional) */}
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Description <span className="text-faded-ink font-normal">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description..."
              rows={2}
              className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm resize-none"
              style={{ borderRadius: '2px' }}
            />
          </div>

          {/* Insert mention checkbox */}
          <label className="flex items-center gap-2 text-sm font-sans text-midnight cursor-pointer">
            <input
              type="checkbox"
              checked={insertMention}
              onChange={(e) => setInsertMention(e.target.checked)}
              className="w-4 h-4"
            />
            <span>Replace selection with entity mention</span>
          </label>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-sans font-medium text-faded-ink hover:text-midnight transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating || !name.trim()}
            className="px-4 py-2 text-sm font-sans font-semibold bg-bronze hover:bg-bronze-dark text-white transition-colors disabled:opacity-50"
            style={{ borderRadius: '2px' }}
          >
            {isCreating ? 'Creating...' : 'Create Entity'}
          </button>
        </div>
      </div>
    </>
  );
}
