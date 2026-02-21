/**
 * CharacterSheetEditor - Form-based editor for character sheet documents
 * Displays and edits character data linked to Codex entities
 */

import { useState, useEffect, useCallback } from 'react';
import { chaptersApi, codexApi, type Chapter } from '@/lib/api';
import type { Entity } from '@/types/codex';
import { toast } from '@/stores/toastStore';
import { confirm } from '@/stores/confirmStore';
import { getErrorMessage } from '@/lib/retry';
import EntityPickerModal from './EntityPickerModal';

interface CharacterSheetEditorProps {
  chapterId: string;
  manuscriptId?: string;
  onTitleChange?: (title: string) => void;
}

interface CharacterData {
  name: string;
  aliases: string[];
  attributes: {
    role?: string;
    physical?: {
      age?: string;
      appearance?: string;
      distinguishing_features?: string;
    };
    personality?: {
      traits?: string[];
      strengths?: string;
      flaws?: string;
    };
    backstory?: {
      origin?: string;
      key_events?: string;
      secrets?: string;
    };
    motivation?: {
      want?: string;
      need?: string;
    };
  };
  template_data?: Record<string, unknown>;
  notes?: string;
  synced_at?: string;
}

const ROLE_OPTIONS = [
  'Protagonist',
  'Antagonist',
  'Supporting',
  'Minor',
  'Mentor',
  'Love Interest',
  'Comic Relief',
  'Other',
];

export default function CharacterSheetEditor({ chapterId, manuscriptId, onTitleChange: _onTitleChange }: CharacterSheetEditorProps) {
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showEntityPicker, setShowEntityPicker] = useState(false);
  const [generatingField, setGeneratingField] = useState<string | null>(null);
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);

  // Load API key on mount
  useEffect(() => {
    const key = localStorage.getItem('openrouter_api_key');
    setStoredApiKey(key);
  }, []);

  // Character data from document_metadata
  const [characterData, setCharacterData] = useState<CharacterData>({
    name: '',
    aliases: [],
    attributes: {},
    notes: '',
  });

  // Load chapter data and auto-sync if linked to entity
  useEffect(() => {
    const loadChapter = async () => {
      try {
        setLoading(true);
        const data = await chaptersApi.getChapter(chapterId);

        // If linked to an entity, auto-sync to get latest data
        if (data.linked_entity_id) {
          try {
            const result = await chaptersApi.syncEntity(chapterId, 'from_entity');
            setChapter(result.chapter);

            // Use synced data
            const metadata = result.chapter.document_metadata || {};
            setCharacterData({
              name: (metadata.name as string) || '',
              aliases: (metadata.aliases as string[]) || [],
              attributes: (metadata.attributes as Record<string, unknown>) || {},
              template_data: metadata.template_data as Record<string, unknown>,
              notes: (metadata.notes as string) || '',
              synced_at: metadata.synced_at as string,
            });
            return; // Exit early, we've set everything
          } catch (syncErr) {
            // If sync fails, continue with local data
            console.warn('Auto-sync failed, using local data:', syncErr);
          }
        }

        // No linked entity or sync failed - use local data
        setChapter(data);
        const metadata = data.document_metadata || {};
        setCharacterData({
          name: (metadata.name as string) || '',
          aliases: (metadata.aliases as string[]) || [],
          attributes: (metadata.attributes as Record<string, unknown>) || {},
          template_data: metadata.template_data as Record<string, unknown>,
          notes: (metadata.notes as string) || '',
          synced_at: metadata.synced_at as string,
        });
      } catch (err) {
        toast.error(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadChapter();
  }, [chapterId]);

  // Auto-save debounce
  const saveChanges = useCallback(async () => {
    if (!chapter || !hasUnsavedChanges) return;

    try {
      setSaving(true);
      await chaptersApi.updateChapter(chapterId, {
        document_metadata: {
          ...chapter.document_metadata,
          name: characterData.name,
          aliases: characterData.aliases,
          attributes: characterData.attributes,
          notes: characterData.notes,
        },
      });
      setHasUnsavedChanges(false);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }, [chapter, chapterId, characterData, hasUnsavedChanges]);

  // Auto-save after 2 seconds of inactivity
  useEffect(() => {
    if (!hasUnsavedChanges) return;

    const timer = setTimeout(() => {
      saveChanges();
    }, 2000);

    return () => clearTimeout(timer);
  }, [hasUnsavedChanges, saveChanges]);

  // Update a nested field
  const updateField = (path: string, value: unknown) => {
    setCharacterData((prev) => {
      const parts = path.split('.');
      const newData = { ...prev };

      if (parts.length === 1) {
        (newData as unknown as Record<string, unknown>)[parts[0]] = value;
      } else if (parts.length === 2) {
        const [section, field] = parts;
        if (section === 'attributes') {
          newData.attributes = { ...newData.attributes, [field]: value };
        }
      } else if (parts.length === 3) {
        const [, section, field] = parts;
        const sectionData = (newData.attributes as Record<string, Record<string, unknown>>)[section] || {};
        newData.attributes = {
          ...newData.attributes,
          [section]: { ...sectionData, [field]: value },
        };
      }

      return newData;
    });
    setHasUnsavedChanges(true);
  };

  // Get nested field value
  const getField = (path: string): string => {
    const parts = path.split('.');
    if (parts.length === 1) {
      const value = (characterData as unknown as Record<string, unknown>)[parts[0]];
      return typeof value === 'string' ? value : '';
    } else if (parts.length === 2) {
      const [section, field] = parts;
      if (section === 'attributes') {
        const value = (characterData.attributes as Record<string, unknown>)?.[field];
        return typeof value === 'string' ? value : '';
      }
    } else if (parts.length === 3) {
      const [, section, field] = parts;
      const sectionData = (characterData.attributes as Record<string, Record<string, unknown>>)?.[section];
      const value = sectionData?.[field];
      return typeof value === 'string' ? value : '';
    }
    return '';
  };

  // Sync with Codex entity
  const handleSyncFromEntity = async () => {
    if (!chapter?.linked_entity_id) {
      toast.error('No linked entity');
      return;
    }

    try {
      setSyncing(true);
      const result = await chaptersApi.syncEntity(chapterId, 'from_entity');
      setChapter(result.chapter);

      const metadata = result.chapter.document_metadata || {};
      setCharacterData({
        name: (metadata.name as string) || '',
        aliases: (metadata.aliases as string[]) || [],
        attributes: (metadata.attributes as Record<string, unknown>) || {},
        template_data: metadata.template_data as Record<string, unknown>,
        notes: (metadata.notes as string) || '',
        synced_at: metadata.synced_at as string,
      });

      toast.success(`Synced from ${result.entity.name}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncToEntity = async () => {
    if (!chapter?.linked_entity_id) {
      toast.error('No linked entity');
      return;
    }

    // Save current changes first
    if (hasUnsavedChanges) {
      await saveChanges();
    }

    try {
      setSyncing(true);
      const result = await chaptersApi.syncEntity(chapterId, 'to_entity');
      setChapter(result.chapter);
      toast.success(`Pushed changes to ${result.entity.name}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  // Handle linking to an entity
  const handleLinkEntity = async (entity: Entity) => {
    try {
      setSyncing(true);
      setShowEntityPicker(false);

      // Update chapter with linked_entity_id
      await chaptersApi.updateChapter(chapterId, {
        linked_entity_id: entity.id,
      });

      // Sync from entity to populate data
      const result = await chaptersApi.syncEntity(chapterId, 'from_entity');
      setChapter(result.chapter);

      // Update character data from synced result
      const metadata = result.chapter.document_metadata || {};
      setCharacterData({
        name: (metadata.name as string) || '',
        aliases: (metadata.aliases as string[]) || [],
        attributes: (metadata.attributes as Record<string, unknown>) || {},
        template_data: metadata.template_data as Record<string, unknown>,
        notes: (metadata.notes as string) || '',
        synced_at: metadata.synced_at as string,
      });

      toast.success(`Linked to ${entity.name}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  // Handle unlinking from entity
  const handleUnlinkEntity = async () => {
    if (!(await confirm({ title: 'Unlink Entity', message: 'Unlink this character sheet from the Codex entity? The sheet data will be preserved.', variant: 'warning', confirmLabel: 'Unlink' }))) {
      return;
    }

    try {
      setSyncing(true);

      // Update chapter to remove linked_entity_id
      const updatedChapter = await chaptersApi.updateChapter(chapterId, {
        linked_entity_id: null as unknown as string, // Clear the link
      });

      setChapter(updatedChapter);
      toast.success('Unlinked from Codex entity');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  // AI Generate handler
  const handleAIGenerate = async (fieldPath: string, fieldLabel: string) => {
    if (!storedApiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    if (!characterData.name) {
      toast.error('Please enter a character name first');
      return;
    }

    try {
      setGeneratingField(fieldPath);

      // Get manuscript context from linked entity appearances
      let manuscript_context: string | undefined;
      if (chapter?.linked_entity_id) {
        try {
          const contexts = await codexApi.getEntityAppearanceContexts(chapter.linked_entity_id);
          if (contexts && contexts.length > 0) {
            manuscript_context = contexts.slice(0, 5).map((ctx: { chapter_title: string; context_text: string | null; summary: string }) =>
              `${ctx.chapter_title}: ${ctx.context_text || ctx.summary || 'N/A'}`
            ).join('\n\n');
          }
        } catch {
          // Silently fail - context is optional
        }
      }

      const result = await codexApi.generateFieldSuggestion({
        api_key: storedApiKey,
        entity_name: characterData.name,
        entity_type: 'CHARACTER',
        template_type: 'CHARACTER',
        field_path: fieldPath,
        existing_data: characterData.attributes,
        manuscript_context,
      });

      // Apply the suggestion
      const suggestion = typeof result.suggestion === 'string'
        ? result.suggestion
        : Array.isArray(result.suggestion)
          ? result.suggestion.join(', ')
          : '';

      updateField(fieldPath, suggestion);
      toast.success(`Generated ${fieldLabel}` + (manuscript_context ? ' (using manuscript context)' : ''));
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setGeneratingField(null);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-faded-ink">Loading character sheet...</div>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-red-600">Character sheet not found</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-vellum overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👤</span>
            <div>
              <h1 className="font-garamond text-xl font-semibold text-midnight">
                {characterData.name || 'Unnamed Character'}
              </h1>
              <p className="text-xs text-faded-ink">Character Sheet</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Sync status */}
            {characterData.synced_at && (
              <span className="text-xs text-faded-ink">
                Last synced: {new Date(characterData.synced_at).toLocaleString()}
              </span>
            )}

            {/* Unsaved changes indicator */}
            {hasUnsavedChanges && (
              <span className="text-xs text-amber-600 font-medium">Unsaved changes</span>
            )}
            {saving && (
              <span className="text-xs text-bronze">Saving...</span>
            )}

            {/* Link/Sync buttons */}
            {chapter.linked_entity_id ? (
              <>
                {/* Linked: show sync and unlink buttons */}
                <button
                  onClick={handleSyncFromEntity}
                  disabled={syncing}
                  className="px-3 py-1.5 text-xs font-sans bg-white border border-slate-ui text-midnight hover:bg-slate-ui/20 disabled:opacity-50 rounded-sm"
                >
                  {syncing ? '...' : 'Pull from Codex'}
                </button>
                <button
                  onClick={handleSyncToEntity}
                  disabled={syncing}
                  className="px-3 py-1.5 text-xs font-sans bg-bronze text-white hover:bg-bronze/90 disabled:opacity-50 rounded-sm"
                >
                  {syncing ? '...' : 'Push to Codex'}
                </button>
                <button
                  onClick={handleUnlinkEntity}
                  disabled={syncing}
                  className="px-3 py-1.5 text-xs font-sans bg-white border border-red-300 text-red-600 hover:bg-red-50 disabled:opacity-50 rounded-sm"
                  title="Unlink from Codex entity"
                >
                  Unlink
                </button>
              </>
            ) : manuscriptId ? (
              /* Not linked: show link button */
              <button
                onClick={() => setShowEntityPicker(true)}
                disabled={syncing}
                className="px-3 py-1.5 text-xs font-sans bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 rounded-sm flex items-center gap-1"
              >
                <span>🔗</span>
                Link to Entity
              </button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Form content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-8">
          {/* Basic Info Section */}
          <FormSection title="Basic Information" icon="📋">
            <FormField
              label="Name"
              value={characterData.name}
              onChange={(v) => updateField('name', v)}
              placeholder="Character's full name"
            />
            <FormField
              label="Aliases / Nicknames"
              value={characterData.aliases.join(', ')}
              onChange={(v) => updateField('aliases', v.split(',').map((s) => s.trim()).filter(Boolean))}
              placeholder="Comma-separated nicknames"
            />
            <FormSelect
              label="Role in Story"
              value={getField('attributes.role')}
              options={ROLE_OPTIONS}
              onChange={(v) => updateField('attributes.role', v)}
            />
          </FormSection>

          {/* Physical Appearance Section */}
          <FormSection title="Physical Appearance" icon="👁">
            <FormField
              label="Age"
              value={getField('attributes.physical.age')}
              onChange={(v) => updateField('attributes.physical.age', v)}
              placeholder="e.g., 32, early 40s, immortal"
            />
            <FormTextarea
              label="General Appearance"
              value={getField('attributes.physical.appearance')}
              onChange={(v) => updateField('attributes.physical.appearance', v)}
              placeholder="Height, build, hair, eyes, skin tone..."
              rows={3}
              onAIGenerate={() => handleAIGenerate('attributes.physical.appearance', 'appearance')}
              isGenerating={generatingField === 'attributes.physical.appearance'}
            />
            <FormTextarea
              label="Distinguishing Features"
              value={getField('attributes.physical.distinguishing_features')}
              onChange={(v) => updateField('attributes.physical.distinguishing_features', v)}
              placeholder="Scars, birthmarks, unique traits..."
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.physical.distinguishing_features', 'distinguishing features')}
              isGenerating={generatingField === 'attributes.physical.distinguishing_features'}
            />
          </FormSection>

          {/* Personality Section */}
          <FormSection title="Personality" icon="🧠">
            <FormField
              label="Key Traits"
              value={
                Array.isArray(
                  (characterData.attributes?.personality as Record<string, unknown>)?.traits
                )
                  ? ((characterData.attributes?.personality as Record<string, unknown>)?.traits as string[]).join(', ')
                  : ''
              }
              onChange={(v) =>
                updateField(
                  'attributes.personality.traits',
                  v.split(',').map((s) => s.trim()).filter(Boolean)
                )
              }
              placeholder="Comma-separated traits (e.g., brave, stubborn, kind)"
            />
            <FormTextarea
              label="Strengths"
              value={getField('attributes.personality.strengths')}
              onChange={(v) => updateField('attributes.personality.strengths', v)}
              placeholder="What are they good at?"
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.personality.strengths', 'strengths')}
              isGenerating={generatingField === 'attributes.personality.strengths'}
            />
            <FormTextarea
              label="Flaws"
              value={getField('attributes.personality.flaws')}
              onChange={(v) => updateField('attributes.personality.flaws', v)}
              placeholder="What holds them back?"
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.personality.flaws', 'flaws')}
              isGenerating={generatingField === 'attributes.personality.flaws'}
            />
          </FormSection>

          {/* Backstory Section */}
          <FormSection title="Backstory" icon="📖">
            <FormTextarea
              label="Origin"
              value={getField('attributes.backstory.origin')}
              onChange={(v) => updateField('attributes.backstory.origin', v)}
              placeholder="Where are they from? What was their childhood like?"
              rows={3}
              onAIGenerate={() => handleAIGenerate('attributes.backstory.origin', 'origin story')}
              isGenerating={generatingField === 'attributes.backstory.origin'}
            />
            <FormTextarea
              label="Key Life Events"
              value={getField('attributes.backstory.key_events')}
              onChange={(v) => updateField('attributes.backstory.key_events', v)}
              placeholder="Formative experiences that shaped them"
              rows={3}
              onAIGenerate={() => handleAIGenerate('attributes.backstory.key_events', 'key life events')}
              isGenerating={generatingField === 'attributes.backstory.key_events'}
            />
            <FormTextarea
              label="Secrets"
              value={getField('attributes.backstory.secrets')}
              onChange={(v) => updateField('attributes.backstory.secrets', v)}
              placeholder="What are they hiding?"
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.backstory.secrets', 'secrets')}
              isGenerating={generatingField === 'attributes.backstory.secrets'}
            />
          </FormSection>

          {/* Motivation Section */}
          <FormSection title="Motivation" icon="🎯">
            <FormTextarea
              label="What They Want"
              value={getField('attributes.motivation.want')}
              onChange={(v) => updateField('attributes.motivation.want', v)}
              placeholder="Their conscious goal or desire"
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.motivation.want', 'character want')}
              isGenerating={generatingField === 'attributes.motivation.want'}
            />
            <FormTextarea
              label="What They Need"
              value={getField('attributes.motivation.need')}
              onChange={(v) => updateField('attributes.motivation.need', v)}
              placeholder="What they actually need (often different from want)"
              rows={2}
              onAIGenerate={() => handleAIGenerate('attributes.motivation.need', 'character need')}
              isGenerating={generatingField === 'attributes.motivation.need'}
            />
          </FormSection>

          {/* Notes Section */}
          <FormSection title="Notes" icon="📝">
            <FormTextarea
              label="Additional Notes"
              value={characterData.notes || ''}
              onChange={(v) => updateField('notes', v)}
              placeholder="Any other details about this character..."
              rows={5}
            />
          </FormSection>
        </div>
      </div>

      {/* Entity Picker Modal */}
      {showEntityPicker && manuscriptId && (
        <EntityPickerModal
          manuscriptId={manuscriptId}
          entityType="CHARACTER"
          title="Link to Character Entity"
          onSelect={handleLinkEntity}
          onCancel={() => setShowEntityPicker(false)}
        />
      )}
    </div>
  );
}

// Helper Components

interface FormSectionProps {
  title: string;
  icon: string;
  children: React.ReactNode;
}

function FormSection({ title, icon, children }: FormSectionProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-ui p-5">
      <h2 className="font-garamond text-lg font-semibold text-midnight mb-4 flex items-center gap-2">
        <span>{icon}</span>
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

interface FormFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

function FormField({ label, value, onChange, placeholder }: FormFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-midnight mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze bg-vellum"
      />
    </div>
  );
}

interface FormTextareaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  onAIGenerate?: () => void;
  isGenerating?: boolean;
}

function FormTextarea({ label, value, onChange, placeholder, rows = 3, onAIGenerate, isGenerating }: FormTextareaProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="block text-sm font-medium text-midnight">{label}</label>
        {onAIGenerate && (
          <button
            type="button"
            onClick={onAIGenerate}
            disabled={isGenerating}
            className="px-2 py-0.5 text-xs font-sans bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm flex items-center gap-1 transition-all"
            title="Generate with AI"
          >
            {isGenerating ? (
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
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze bg-vellum resize-none"
      />
    </div>
  );
}

interface FormSelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}

function FormSelect({ label, value, options, onChange }: FormSelectProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-midnight mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze bg-vellum"
      >
        <option value="">Select...</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
