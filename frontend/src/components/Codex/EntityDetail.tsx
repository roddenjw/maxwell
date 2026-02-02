/**
 * EntityDetail - Detailed view and editing for selected entity
 */

import { useState, useEffect } from 'react';
import type { Entity } from '@/types/codex';
import { EntityType, getEntityTypeColor, getEntityTypeIcon } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import { getErrorMessage } from '@/lib/retry';
import {
  CHARACTER_ROLES,
  CHARACTER_TROPES,
  getRoleById,
  getTropeById,
} from '@/lib/characterArchetypes';

interface EntityDetailProps {
  entity: Entity;
  onUpdate: (updates: Partial<Entity>) => void;
  onDelete?: (entityId: string) => void;
  onClose: () => void;
  onAddToBinder?: (entityId: string) => void;
  onMerge?: (entityId: string) => void;
}

export default function EntityDetail({
  entity,
  onUpdate,
  onDelete,
  onClose,
  onAddToBinder,
  onMerge,
}: EntityDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(entity.name);
  const [editedType, setEditedType] = useState(entity.type);
  const [editedAliases, setEditedAliases] = useState(entity.aliases.join(', '));
  const [editedAttributes, setEditedAttributes] = useState(() => {
    // Convert attributes to editable format
    const attrs = entity.attributes || {};
    return {
      description: attrs.description || '',
      notes: attrs.notes || '',
      // Character development fields (Sanderson methodology)
      want: attrs.want || '',
      need: attrs.need || '',
      flaw: attrs.flaw || '',
      strength: attrs.strength || '',
      arc: attrs.arc || '',
      // Character archetype fields
      character_role: attrs.character_role || '',
      character_tropes: attrs.character_tropes || [] as string[],
    };
  });
  const [generatingField, setGeneratingField] = useState<string | null>(null);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);
  const [isAIFilling, setIsAIFilling] = useState(false);
  const [appearanceSummary, setAppearanceSummary] = useState<{
    first_appearance: { chapter_id: string; chapter_title: string; summary: string } | null;
    last_appearance: { chapter_id: string; chapter_title: string; summary: string } | null;
    total_appearances: number;
  } | null>(null);

  // Load API key on mount
  useEffect(() => {
    const key = localStorage.getItem('openrouter_api_key');
    setStoredApiKey(key);
  }, []);

  // Load appearance summary
  useEffect(() => {
    const loadAppearanceSummary = async () => {
      try {
        const summary = await codexApi.getEntityAppearanceSummary(entity.id);
        setAppearanceSummary(summary);
      } catch (error) {
        // Silently fail - appearance summary is optional
        console.error('Failed to load appearance summary:', error);
      }
    };
    loadAppearanceSummary();
  }, [entity.id]);

  const typeColor = getEntityTypeColor(isEditing ? editedType : entity.type);
  const typeIcon = getEntityTypeIcon(isEditing ? editedType : entity.type);

  const handleSave = () => {
    // Parse aliases
    const aliases = editedAliases
      .split(',')
      .map((a) => a.trim())
      .filter((a) => a.length > 0);

    // Update attributes
    const attributes = {
      ...entity.attributes,
      ...editedAttributes,
    };

    onUpdate({
      name: editedName,
      type: editedType,
      aliases,
      attributes,
    });

    setIsEditing(false);
  };

  const handleCancel = () => {
    // Reset to original values
    setEditedName(entity.name);
    setEditedType(entity.type);
    setEditedAliases(entity.aliases.join(', '));
    const attrs = entity.attributes || {};
    setEditedAttributes({
      description: attrs.description || '',
      notes: attrs.notes || '',
      want: attrs.want || '',
      need: attrs.need || '',
      flaw: attrs.flaw || '',
      strength: attrs.strength || '',
      arc: attrs.arc || '',
      character_role: attrs.character_role || '',
      character_tropes: attrs.character_tropes || [],
    });
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (confirm(`Delete "${entity.name}"? This cannot be undone.`)) {
      onDelete?.(entity.id);
      onClose();
    }
  };

  // AI Generate handler - pulls real manuscript context
  const handleAIGenerate = async (field: 'description' | 'notes' | 'want' | 'need' | 'flaw' | 'strength' | 'arc', fieldLabel: string) => {
    if (!storedApiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    try {
      setGeneratingField(field);

      // Build manuscript context from appearance summary
      let manuscript_context = '';
      if (appearanceSummary && appearanceSummary.total_appearances > 0) {
        const contextParts = [];
        if (appearanceSummary.first_appearance) {
          contextParts.push(`First appears in "${appearanceSummary.first_appearance.chapter_title}": ${appearanceSummary.first_appearance.summary}`);
        }
        if (appearanceSummary.last_appearance && appearanceSummary.last_appearance.chapter_id !== appearanceSummary.first_appearance?.chapter_id) {
          contextParts.push(`Last seen in "${appearanceSummary.last_appearance.chapter_title}": ${appearanceSummary.last_appearance.summary}`);
        }
        manuscript_context = contextParts.join('\n\n');
      }

      // If no appearances, try to get full contexts for better AI generation
      if (!manuscript_context) {
        try {
          const contexts = await codexApi.getEntityAppearanceContexts(entity.id);
          if (contexts && contexts.length > 0) {
            manuscript_context = contexts.slice(0, 5).map((ctx: any) =>
              `${ctx.chapter_title}: ${ctx.context_text || ctx.summary || 'N/A'}`
            ).join('\n\n');
          }
        } catch {
          // Silently fail
        }
      }

      const result = await codexApi.generateFieldSuggestion({
        api_key: storedApiKey,
        entity_name: editedName || entity.name,
        entity_type: editedType || entity.type,
        template_type: editedType || entity.type,
        field_path: field,
        existing_data: entity.attributes,
        manuscript_context: manuscript_context || undefined,
      });

      // Apply the suggestion
      const suggestion = typeof result.suggestion === 'string'
        ? result.suggestion
        : Array.isArray(result.suggestion)
          ? result.suggestion.join(', ')
          : '';

      setEditedAttributes(prev => ({ ...prev, [field]: suggestion }));
      toast.success(`Generated ${fieldLabel}` + (manuscript_context ? ' (using manuscript context)' : ' (no appearances found)'));
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setGeneratingField(null);
    }
  };

  // AI Fill - analyze all appearances and generate comprehensive content
  const handleAIFill = async () => {
    if (!storedApiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    if (!appearanceSummary || appearanceSummary.total_appearances === 0) {
      toast.error('No appearances found. AI Fill requires at least one appearance in the manuscript.');
      return;
    }

    try {
      setIsAIFilling(true);

      const result = await codexApi.aiEntityFill({
        api_key: storedApiKey,
        entity_id: entity.id,
      });

      // Update entity with AI-generated content
      const newAttributes = {
        ...entity.attributes,
        ...result.attributes,
        description: result.description,
      };

      // If we got suggested aliases, merge them
      let newAliases = entity.aliases;
      if (result.suggested_aliases && result.suggested_aliases.length > 0) {
        const aliasSet = new Set([...entity.aliases, ...result.suggested_aliases]);
        newAliases = Array.from(aliasSet);
      }

      onUpdate({
        attributes: newAttributes,
        aliases: newAliases,
      });

      // Update local state to reflect changes
      setEditedAttributes(prev => ({
        ...prev,
        description: result.description || '',
        notes: entity.attributes?.notes || '',
      }));
      setEditedAliases(newAliases.join(', '));

      toast.success('AI filled entity from appearances');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsAIFilling(false);
    }
  };

  return (
    <div className="bg-vellum h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-slate-ui p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{typeIcon}</span>
          <div>
            {isEditing ? (
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="text-xl font-garamond font-bold text-midnight bg-white border border-slate-ui px-2 py-1"
                style={{ borderRadius: '2px' }}
              />
            ) : (
              <h2 className="text-xl font-garamond font-bold text-midnight">
                {entity.name}
              </h2>
            )}
            {isEditing ? (
              <select
                value={editedType}
                onChange={(e) => setEditedType(e.target.value as EntityType)}
                className="mt-1 bg-white border border-slate-ui px-2 py-1 text-xs font-sans"
                style={{ borderRadius: '2px' }}
              >
                <option value={EntityType.CHARACTER}>Character</option>
                <option value={EntityType.LOCATION}>Location</option>
                <option value={EntityType.ITEM}>Item</option>
                <option value={EntityType.LORE}>Lore</option>
                <option value={EntityType.CULTURE}>Culture</option>
                <option value={EntityType.CREATURE}>Creature</option>
                <option value={EntityType.RACE}>Race</option>
              </select>
            ) : (
              <span
                className="inline-block mt-1 px-2 py-0.5 text-xs font-sans text-white"
                style={{
                  backgroundColor: typeColor,
                  borderRadius: '2px',
                }}
              >
                {entity.type}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90"
                style={{ borderRadius: '2px' }}
              >
                Save
              </button>
              <button
                onClick={handleCancel}
                className="bg-slate-ui text-midnight px-3 py-1.5 text-sm font-sans hover:bg-slate-ui/80"
                style={{ borderRadius: '2px' }}
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              {/* Add to Binder button - only for CHARACTER entities */}
              {onAddToBinder && entity.type === EntityType.CHARACTER && (
                <button
                  onClick={() => onAddToBinder(entity.id)}
                  className="bg-blue-600 text-white px-3 py-1.5 text-sm font-sans hover:bg-blue-700 flex items-center gap-1"
                  style={{ borderRadius: '2px' }}
                  title="Create character sheet in Binder"
                >
                  <span>📄</span>
                  Add to Binder
                </button>
              )}
              <button
                onClick={() => setIsEditing(true)}
                className="bg-bronze text-white px-3 py-1.5 text-sm font-sans hover:bg-bronze/90"
                style={{ borderRadius: '2px' }}
              >
                Edit
              </button>
              {onMerge && (
                <button
                  onClick={() => onMerge(entity.id)}
                  className="bg-purple-600 text-white px-3 py-1.5 text-sm font-sans hover:bg-purple-700 flex items-center gap-1"
                  style={{ borderRadius: '2px' }}
                  title="Merge with another entity"
                >
                  <span>🔗</span>
                  Merge
                </button>
              )}
              {onDelete && (
                <button
                  onClick={handleDelete}
                  className="bg-red-600 text-white px-3 py-1.5 text-sm font-sans hover:bg-red-700"
                  style={{ borderRadius: '2px' }}
                  title="Delete entity"
                >
                  Delete
                </button>
              )}
            </>
          )}
          <button
            onClick={onClose}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Appearance Summary */}
        {appearanceSummary && appearanceSummary.total_appearances > 0 && (
          <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-sans text-faded-ink uppercase">
                Appearances <span className="text-bronze">({appearanceSummary.total_appearances} total)</span>
              </label>
              {storedApiKey && (
                <button
                  onClick={handleAIFill}
                  disabled={isAIFilling}
                  className="px-3 py-1 text-xs font-sans font-semibold bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1 transition-all"
                  title="Analyze all appearances and generate comprehensive entity content"
                >
                  {isAIFilling ? (
                    <>
                      <span className="animate-spin">⟳</span>
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>AI Fill from Appearances</span>
                    </>
                  )}
                </button>
              )}
            </div>
            <div className="space-y-2">
              {appearanceSummary.first_appearance && (
                <div className="text-sm">
                  <span className="text-faded-ink">First appears:</span>{' '}
                  <span className="font-semibold text-midnight">
                    {appearanceSummary.first_appearance.chapter_title}
                  </span>
                  <p className="text-xs text-faded-ink mt-0.5 italic">
                    {appearanceSummary.first_appearance.summary}
                  </p>
                </div>
              )}
              {appearanceSummary.last_appearance && appearanceSummary.total_appearances > 1 && (
                <div className="text-sm">
                  <span className="text-faded-ink">Last appears:</span>{' '}
                  <span className="font-semibold text-midnight">
                    {appearanceSummary.last_appearance.chapter_title}
                  </span>
                  <p className="text-xs text-faded-ink mt-0.5 italic">
                    {appearanceSummary.last_appearance.summary}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Aliases */}
        <div>
          <label className="block text-xs font-sans text-faded-ink uppercase mb-1">
            Aliases (comma-separated)
          </label>
          {isEditing ? (
            <input
              type="text"
              value={editedAliases}
              onChange={(e) => setEditedAliases(e.target.value)}
              placeholder="e.g., John, Johnny, The Smith"
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-sans text-midnight">
              {entity.aliases.length > 0 ? entity.aliases.join(', ') : 'None'}
            </p>
          )}
        </div>

        {/* Description */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-sans text-faded-ink uppercase">
              Description
            </label>
            {isEditing && (
              <button
                type="button"
                onClick={() => handleAIGenerate('description', 'description')}
                disabled={generatingField !== null}
                className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1 transition-all"
                title="Generate with AI"
              >
                {generatingField === 'description' ? (
                  <>
                    <span className="animate-spin">⟳</span>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>✨</span>
                    <span>Generate</span>
                  </>
                )}
              </button>
            )}
          </div>
          {isEditing ? (
            <textarea
              value={editedAttributes.description}
              onChange={(e) =>
                setEditedAttributes({ ...editedAttributes, description: e.target.value })
              }
              placeholder="Enter description..."
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif text-midnight min-h-[100px]"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-serif text-midnight whitespace-pre-wrap">
              {editedAttributes.description || 'No description'}
            </p>
          )}
        </div>

        {/* Notes */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-sans text-faded-ink uppercase">
              Notes
            </label>
            {isEditing && (
              <button
                type="button"
                onClick={() => handleAIGenerate('notes', 'notes')}
                disabled={generatingField !== null}
                className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1 transition-all"
                title="Generate with AI"
              >
                {generatingField === 'notes' ? (
                  <>
                    <span className="animate-spin">⟳</span>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>✨</span>
                    <span>Generate</span>
                  </>
                )}
              </button>
            )}
          </div>
          {isEditing ? (
            <textarea
              value={editedAttributes.notes}
              onChange={(e) =>
                setEditedAttributes({ ...editedAttributes, notes: e.target.value })
              }
              placeholder="Enter notes..."
              className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-serif text-midnight min-h-[100px]"
              style={{ borderRadius: '2px' }}
            />
          ) : (
            <p className="text-sm font-serif text-midnight whitespace-pre-wrap">
              {editedAttributes.notes || 'No notes'}
            </p>
          )}
        </div>

        {/* Character Development Fields (Sanderson Methodology) - Only for CHARACTER type */}
        {(isEditing ? editedType : entity.type) === EntityType.CHARACTER && (
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 p-4 space-y-4" style={{ borderRadius: '2px' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎭</span>
              <label className="text-sm font-sans font-semibold text-purple-800">
                Character Development
              </label>
              <span className="text-xs text-purple-600">(Sanderson Methodology)</span>
            </div>

            {/* Want */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-sans text-purple-700 uppercase">
                  Want <span className="text-purple-500 normal-case">(Surface goal)</span>
                </label>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleAIGenerate('want', 'want')}
                    disabled={generatingField !== null}
                    className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1"
                  >
                    {generatingField === 'want' ? <span className="animate-spin">⟳</span> : <span>✨</span>}
                    <span>Generate</span>
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editedAttributes.want}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, want: e.target.value })}
                  placeholder="What does this character consciously want?"
                  className="w-full bg-white border border-purple-200 px-3 py-2 text-sm font-sans text-midnight min-h-[60px]"
                  style={{ borderRadius: '2px' }}
                />
              ) : (
                <p className="text-sm font-sans text-midnight">{editedAttributes.want || 'Not defined'}</p>
              )}
            </div>

            {/* Need */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-sans text-purple-700 uppercase">
                  Need <span className="text-purple-500 normal-case">(Deep emotional need)</span>
                </label>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleAIGenerate('need', 'need')}
                    disabled={generatingField !== null}
                    className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1"
                  >
                    {generatingField === 'need' ? <span className="animate-spin">⟳</span> : <span>✨</span>}
                    <span>Generate</span>
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editedAttributes.need}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, need: e.target.value })}
                  placeholder="What do they actually need (often unknown to them)?"
                  className="w-full bg-white border border-purple-200 px-3 py-2 text-sm font-sans text-midnight min-h-[60px]"
                  style={{ borderRadius: '2px' }}
                />
              ) : (
                <p className="text-sm font-sans text-midnight">{editedAttributes.need || 'Not defined'}</p>
              )}
            </div>

            {/* Flaw */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-sans text-purple-700 uppercase">
                  Flaw <span className="text-purple-500 normal-case">(Fatal weakness)</span>
                </label>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleAIGenerate('flaw', 'flaw')}
                    disabled={generatingField !== null}
                    className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1"
                  >
                    {generatingField === 'flaw' ? <span className="animate-spin">⟳</span> : <span>✨</span>}
                    <span>Generate</span>
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editedAttributes.flaw}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, flaw: e.target.value })}
                  placeholder="What personal weakness holds them back?"
                  className="w-full bg-white border border-purple-200 px-3 py-2 text-sm font-sans text-midnight min-h-[60px]"
                  style={{ borderRadius: '2px' }}
                />
              ) : (
                <p className="text-sm font-sans text-midnight">{editedAttributes.flaw || 'Not defined'}</p>
              )}
            </div>

            {/* Strength */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-sans text-purple-700 uppercase">
                  Strength <span className="text-purple-500 normal-case">(Key ability)</span>
                </label>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleAIGenerate('strength', 'strength')}
                    disabled={generatingField !== null}
                    className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1"
                  >
                    {generatingField === 'strength' ? <span className="animate-spin">⟳</span> : <span>✨</span>}
                    <span>Generate</span>
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editedAttributes.strength}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, strength: e.target.value })}
                  placeholder="What unique ability or trait defines them?"
                  className="w-full bg-white border border-purple-200 px-3 py-2 text-sm font-sans text-midnight min-h-[60px]"
                  style={{ borderRadius: '2px' }}
                />
              ) : (
                <p className="text-sm font-sans text-midnight">{editedAttributes.strength || 'Not defined'}</p>
              )}
            </div>

            {/* Arc */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-sans text-purple-700 uppercase">
                  Arc <span className="text-purple-500 normal-case">(Transformation)</span>
                </label>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleAIGenerate('arc', 'arc')}
                    disabled={generatingField !== null}
                    className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1"
                  >
                    {generatingField === 'arc' ? <span className="animate-spin">⟳</span> : <span>✨</span>}
                    <span>Generate</span>
                  </button>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editedAttributes.arc}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, arc: e.target.value })}
                  placeholder="How will they change from beginning to end?"
                  className="w-full bg-white border border-purple-200 px-3 py-2 text-sm font-sans text-midnight min-h-[60px]"
                  style={{ borderRadius: '2px' }}
                />
              ) : (
                <p className="text-sm font-sans text-midnight">{editedAttributes.arc || 'Not defined'}</p>
              )}
            </div>
          </div>
        )}

        {/* Character Archetype & Tropes - Only for CHARACTER type */}
        {(isEditing ? editedType : entity.type) === EntityType.CHARACTER && (
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-4 space-y-4" style={{ borderRadius: '2px' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎪</span>
              <label className="text-sm font-sans font-semibold text-amber-800">
                Character Archetype
              </label>
              <span className="text-xs text-amber-600">(Story Role & Tropes)</span>
            </div>

            {/* Story Role */}
            <div>
              <label className="block text-xs font-sans text-amber-700 uppercase mb-1">
                Story Role
              </label>
              {isEditing ? (
                <select
                  value={editedAttributes.character_role}
                  onChange={(e) => setEditedAttributes({ ...editedAttributes, character_role: e.target.value })}
                  className="w-full bg-white border border-amber-200 px-3 py-2 text-sm font-sans text-midnight"
                  style={{ borderRadius: '2px' }}
                >
                  <option value="">Select a role...</option>
                  {CHARACTER_ROLES.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.icon} {role.label}
                    </option>
                  ))}
                </select>
              ) : (
                <div>
                  {editedAttributes.character_role ? (
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getRoleById(editedAttributes.character_role)?.icon}</span>
                      <span className="text-sm font-sans text-midnight font-medium">
                        {getRoleById(editedAttributes.character_role)?.label}
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-faded-ink italic">No role assigned</span>
                  )}
                </div>
              )}
              {editedAttributes.character_role && (
                <p className="text-xs text-amber-600 mt-1">
                  {getRoleById(editedAttributes.character_role)?.description}
                </p>
              )}
            </div>

            {/* Character Tropes */}
            <div>
              <label className="block text-xs font-sans text-amber-700 uppercase mb-1">
                Character Tropes
              </label>
              {isEditing ? (
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {(editedAttributes.character_tropes || []).map((tropeId: string) => {
                      const trope = getTropeById(tropeId);
                      if (!trope) return null;
                      return (
                        <span
                          key={tropeId}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full"
                        >
                          {trope.label}
                          <button
                            type="button"
                            onClick={() => {
                              setEditedAttributes({
                                ...editedAttributes,
                                character_tropes: (editedAttributes.character_tropes || []).filter((id: string) => id !== tropeId),
                              });
                            }}
                            className="text-amber-600 hover:text-amber-800 ml-1"
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                  </div>
                  <select
                    value=""
                    onChange={(e) => {
                      if (e.target.value && !(editedAttributes.character_tropes || []).includes(e.target.value)) {
                        setEditedAttributes({
                          ...editedAttributes,
                          character_tropes: [...(editedAttributes.character_tropes || []), e.target.value],
                        });
                      }
                    }}
                    className="w-full bg-white border border-amber-200 px-3 py-2 text-sm font-sans text-midnight"
                    style={{ borderRadius: '2px' }}
                  >
                    <option value="">Add a trope...</option>
                    {CHARACTER_TROPES.map((trope) => (
                      <option
                        key={trope.id}
                        value={trope.id}
                        disabled={(editedAttributes.character_tropes || []).includes(trope.id)}
                      >
                        {trope.label} ({trope.genres.join(', ')})
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  {(editedAttributes.character_tropes || []).length > 0 ? (
                    <div className="space-y-2">
                      {(editedAttributes.character_tropes || []).map((tropeId: string) => {
                        const trope = getTropeById(tropeId);
                        if (!trope) return null;
                        return (
                          <div key={tropeId} className="bg-white p-2 border border-amber-100" style={{ borderRadius: '2px' }}>
                            <span className="text-sm font-sans text-midnight font-medium">{trope.label}</span>
                            <p className="text-xs text-amber-600 mt-0.5">{trope.description}</p>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <span className="text-sm text-faded-ink italic">No tropes assigned</span>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Auto-Extracted Information */}
        {!isEditing && (
          <>
            {/* Appearance */}
            {entity.attributes?.appearance && entity.attributes.appearance.length > 0 && (
              <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">👤</span>
                  <label className="text-xs font-sans text-faded-ink uppercase">
                    Appearance <span className="text-bronze">(Auto-detected)</span>
                  </label>
                </div>
                <ul className="space-y-1.5">
                  {entity.attributes.appearance.map((item: string, index: number) => (
                    <li key={index} className="text-sm font-serif text-midnight pl-6 relative">
                      <span className="absolute left-0 top-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Personality */}
            {entity.attributes?.personality && entity.attributes.personality.length > 0 && (
              <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">💭</span>
                  <label className="text-xs font-sans text-faded-ink uppercase">
                    Personality <span className="text-bronze">(Auto-detected)</span>
                  </label>
                </div>
                <ul className="space-y-1.5">
                  {entity.attributes.personality.map((item: string, index: number) => (
                    <li key={index} className="text-sm font-serif text-midnight pl-6 relative">
                      <span className="absolute left-0 top-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Background */}
            {entity.attributes?.background && entity.attributes.background.length > 0 && (
              <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">📜</span>
                  <label className="text-xs font-sans text-faded-ink uppercase">
                    Background <span className="text-bronze">(Auto-detected)</span>
                  </label>
                </div>
                <ul className="space-y-1.5">
                  {entity.attributes.background.map((item: string, index: number) => (
                    <li key={index} className="text-sm font-serif text-midnight pl-6 relative">
                      <span className="absolute left-0 top-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            {entity.attributes?.actions && entity.attributes.actions.length > 0 && (
              <div className="bg-white border border-slate-ui p-3" style={{ borderRadius: '2px' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">⚡</span>
                  <label className="text-xs font-sans text-faded-ink uppercase">
                    Actions <span className="text-bronze">(Auto-detected)</span>
                  </label>
                </div>
                <ul className="space-y-1.5">
                  {entity.attributes.actions.map((item: string, index: number) => (
                    <li key={index} className="text-sm font-serif text-midnight pl-6 relative">
                      <span className="absolute left-0 top-0">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {/* Appearance History */}
        {entity.appearance_history && entity.appearance_history.length > 0 && (
          <div>
            <label className="block text-xs font-sans text-faded-ink uppercase mb-2">
              Appearance History ({entity.appearance_history.length})
            </label>
            <div className="space-y-2">
              {entity.appearance_history.map((appearance, index) => (
                <div
                  key={index}
                  className="bg-white border border-slate-ui p-2"
                  style={{ borderRadius: '2px' }}
                >
                  <p className="text-sm font-serif text-midnight">
                    {appearance.description}
                  </p>
                  {appearance.timestamp && (
                    <p className="text-xs text-faded-ink font-sans mt-1">
                      {new Date(appearance.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="pt-4 border-t border-slate-ui">
          <p className="text-xs text-faded-ink font-sans">
            Created: {new Date(entity.created_at).toLocaleString()}
          </p>
          <p className="text-xs text-faded-ink font-sans">
            Updated: {new Date(entity.updated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
