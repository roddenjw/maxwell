/**
 * QuickEntityModal Component
 * Minimal modal for quickly creating an entity from selected text.
 * Pre-fills the entity name with the selection.
 * Supports AI-powered entity extraction from surrounding context.
 */

import { useState, useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection, $getRoot } from 'lexical';
import { $createEntityMentionNode } from './nodes/EntityMentionNode';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import { toast } from '@/stores/toastStore';
import { Z_INDEX } from '@/lib/zIndex';
import { EntityType } from '@/types/codex';
import { getErrorMessage } from '@/lib/retry';

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
  { value: EntityType.CULTURE, label: 'Culture', icon: '🏛️' },
  { value: EntityType.CREATURE, label: 'Creature', icon: '🐉' },
  { value: EntityType.RACE, label: 'Race', icon: '👥' },
  { value: EntityType.ORGANIZATION, label: 'Organization', icon: '🏰' },
  { value: EntityType.EVENT, label: 'Event', icon: '📅' },
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
  const [aliases, setAliases] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [insertMention, setInsertMention] = useState(true);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);
  const [aiConfidence, setAiConfidence] = useState<'high' | 'medium' | 'low' | null>(null);

  const modalRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Load API key on mount
  useEffect(() => {
    const key = localStorage.getItem('openrouter_api_key');
    setStoredApiKey(key);
  }, []);

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
      // Parse aliases
      const aliasesList = aliases
        ? aliases.split(',').map((a) => a.trim()).filter((a) => a.length > 0)
        : [];

      // Create the entity
      const entity = await codexApi.createEntity({
        manuscript_id: manuscriptId,
        name: name.trim(),
        type,
        aliases: aliasesList.length > 0 ? aliasesList : undefined,
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

  // Get surrounding context from the editor
  const getSurroundingContext = (): string => {
    let context = '';
    editor.getEditorState().read(() => {
      const root = $getRoot();
      const fullText = root.getTextContent();

      // Find the selected text position
      const selectedIndex = fullText.indexOf(selectedText);
      if (selectedIndex === -1) {
        // If we can't find the exact text, just use a portion of the document
        context = fullText.slice(0, 2000);
        return;
      }

      // Get ~500 chars before and after the selection
      const contextRadius = 500;
      const start = Math.max(0, selectedIndex - contextRadius);
      const end = Math.min(fullText.length, selectedIndex + selectedText.length + contextRadius);

      context = fullText.slice(start, end);
    });
    return context;
  };

  // AI Analyze - extract entity info from context
  const handleAIAnalyze = async () => {
    if (!storedApiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    setIsAnalyzing(true);

    try {
      const surroundingContext = getSurroundingContext();

      const result = await codexApi.extractEntityFromSelection({
        api_key: storedApiKey,
        selected_text: selectedText,
        surrounding_context: surroundingContext,
      });

      // Populate form with extracted data
      if (result.name) {
        setName(result.name);
      }

      if (result.type && Object.values(EntityType).includes(result.type as EntityType)) {
        setType(result.type as EntityType);
      }

      if (result.description) {
        setDescription(result.description);
      }

      if (result.suggested_aliases && result.suggested_aliases.length > 0) {
        setAliases(result.suggested_aliases.join(', '));
      }

      setAiConfidence(result.confidence);

      toast.success(`AI analyzed "${selectedText}" (${result.confidence} confidence)`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsAnalyzing(false);
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
          <div>
            <h3 className="font-serif font-bold text-lg text-midnight">
              Quick Create Entity
            </h3>
            {aiConfidence && (
              <span className={`text-xs font-sans ${
                aiConfidence === 'high' ? 'text-green-600' :
                aiConfidence === 'medium' ? 'text-amber-600' : 'text-faded-ink'
              }`}>
                AI confidence: {aiConfidence}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center text-faded-ink hover:text-midnight transition-colors"
          >
            ✕
          </button>
        </div>

        {/* AI Analyze Button */}
        {storedApiKey && (
          <button
            onClick={handleAIAnalyze}
            disabled={isAnalyzing}
            className="w-full mb-4 px-4 py-2 text-sm font-sans font-semibold bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style={{ borderRadius: '2px' }}
          >
            {isAnalyzing ? (
              <>
                <span className="animate-spin">⟳</span>
                Analyzing context...
              </>
            ) : (
              <>
                <span>✨</span>
                AI Analyze Selection
              </>
            )}
          </button>
        )}

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
            <div className="grid grid-cols-3 gap-2">
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

          {/* Aliases (optional) */}
          <div>
            <label className="block text-sm font-sans font-semibold text-midnight mb-1">
              Aliases <span className="text-faded-ink font-normal">(optional, comma-separated)</span>
            </label>
            <input
              type="text"
              value={aliases}
              onChange={(e) => setAliases(e.target.value)}
              placeholder="e.g., The Dark Knight, Bruce"
              className="w-full px-3 py-2 border border-slate-ui focus:border-bronze focus:outline-none font-sans text-sm"
              style={{ borderRadius: '2px' }}
            />
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
