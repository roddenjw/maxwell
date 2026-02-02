/**
 * EntityMentionsPlugin - Autocomplete for @mentions of entities
 * Allows typing "@" to bring up a menu of characters, locations, items, and lore
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  LexicalTypeaheadMenuPlugin,
  MenuOption,
  useBasicTypeaheadTriggerMatch,
} from '@lexical/react/LexicalTypeaheadMenuPlugin';
import { $createTextNode, TextNode } from 'lexical';
import { $createEntityMentionNode } from '../nodes/EntityMentionNode';
import { codexApi } from '@/lib/api';
import type { Entity } from '@/types/codex';
import { EntityType } from '@/types/codex';

class EntityMentionOption extends MenuOption {
  entity: Entity;
  description: string;
  isCreateNew: boolean;

  constructor(entity: Entity, isCreateNew: boolean = false) {
    super(entity.name);
    this.entity = entity;
    this.isCreateNew = isCreateNew;
    // Extract description from attributes or use empty string
    this.description = entity.attributes?.description || '';
  }
}

interface EntityMentionsPluginProps {
  manuscriptId?: string;
}

export default function EntityMentionsPlugin({ manuscriptId }: EntityMentionsPluginProps) {
  const [editor] = useLexicalComposerContext();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [queryString, setQueryString] = useState<string | null>(null);

  // Load entities from Codex
  useEffect(() => {
    if (!manuscriptId) return;

    const loadEntities = async () => {
      try {
        const response = await codexApi.listEntities(manuscriptId);
        setEntities(response);
      } catch (error) {
        console.error('Failed to load entities:', error);
      }
    };

    loadEntities();
  }, [manuscriptId]);

  // Filter entities based on query
  const options = useMemo(() => {
    const baseOptions: EntityMentionOption[] = [];

    if (!queryString) {
      // No search query - show first 10 entities
      baseOptions.push(...entities.slice(0, 10).map((entity) => new EntityMentionOption(entity)));
    } else {
      // Filter by search query
      const search = queryString.toLowerCase();
      const filtered = entities
        .filter((entity) => entity.name.toLowerCase().includes(search))
        .slice(0, 10);

      baseOptions.push(...filtered.map((entity) => new EntityMentionOption(entity)));

      // Add "Create new entity" option if query doesn't exactly match any entity
      const exactMatch = entities.some(
        (entity) => entity.name.toLowerCase() === search
      );

      if (!exactMatch && queryString.trim()) {
        // Create a temporary entity object for the "Create new" option
        const newEntityPlaceholder: Entity = {
          id: 'new',
          manuscript_id: manuscriptId || '',
          type: EntityType.CHARACTER, // Default type, will be selected in creation
          name: queryString.trim(),
          aliases: [],
          attributes: {},
          appearance_history: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        baseOptions.push(new EntityMentionOption(newEntityPlaceholder, true));
      }
    }

    return baseOptions;
  }, [entities, queryString, manuscriptId]);

  // Trigger match - detect "@" character
  const checkForMentionMatch = useBasicTypeaheadTriggerMatch('@', {
    minLength: 0,
  });

  // Handle selection of an entity
  const onSelectOption = useCallback(
    async (
      selectedOption: EntityMentionOption,
      nodeToReplace: TextNode | null,
      closeMenu: () => void,
    ) => {
      // If this is the "Create new entity" option
      if (selectedOption.isCreateNew && manuscriptId) {
        try {
          // Prompt for entity type
          const typeChoice = prompt(
            `Create new entity "${selectedOption.entity.name}".\n\nSelect type (1-7):\n1. CHARACTER (person)\n2. LOCATION (place)\n3. ITEM (object)\n4. LORE (concept)\n5. CULTURE (society/customs)\n6. CREATURE (species/monster)\n7. RACE (people/species)`,
            '1'
          );

          if (!typeChoice) {
            closeMenu();
            return;
          }

          // Map choice to entity type
          const typeMap: Record<string, EntityType> = {
            '1': EntityType.CHARACTER,
            '2': EntityType.LOCATION,
            '3': EntityType.ITEM,
            '4': EntityType.LORE,
            '5': EntityType.CULTURE,
            '6': EntityType.CREATURE,
            '7': EntityType.RACE,
          };

          const entityType = typeMap[typeChoice] || EntityType.CHARACTER;

          // Create the entity in Codex
          const newEntity = await codexApi.createEntity({
            manuscript_id: manuscriptId,
            type: entityType,
            name: selectedOption.entity.name,
            aliases: [],
            attributes: {},
          });

          // Update local entities list
          setEntities((prev) => [...prev, newEntity]);

          // Insert mention node with new entity
          editor.update(() => {
            const mentionNode = $createEntityMentionNode(
              newEntity.id,
              newEntity.name,
              newEntity.type as EntityType,
            );

            if (nodeToReplace) {
              nodeToReplace.replace(mentionNode);
            }

            // Add a space after the mention
            mentionNode.insertAfter($createTextNode(' '));

            closeMenu();
          });
        } catch (error) {
          console.error('Failed to create entity:', error);
          alert('Failed to create entity: ' + (error instanceof Error ? error.message : 'Unknown error'));
          closeMenu();
        }
      } else {
        // Existing entity - just insert the mention
        editor.update(() => {
          const mentionNode = $createEntityMentionNode(
            selectedOption.entity.id,
            selectedOption.entity.name,
            selectedOption.entity.type,
          );

          if (nodeToReplace) {
            nodeToReplace.replace(mentionNode);
          }

          // Add a space after the mention
          mentionNode.insertAfter($createTextNode(' '));

          closeMenu();
        });
      }
    },
    [editor, manuscriptId],
  );

  return (
    <LexicalTypeaheadMenuPlugin<EntityMentionOption>
      onQueryChange={setQueryString}
      onSelectOption={onSelectOption}
      triggerFn={checkForMentionMatch}
      options={options}
      menuRenderFn={(
        anchorElementRef,
        { selectedIndex, selectOptionAndCleanUp, setHighlightedIndex },
      ) =>
        anchorElementRef.current && options.length > 0 ? (
          <EntityMentionsTypeaheadMenu
            anchorElementRef={anchorElementRef}
            options={options}
            selectedIndex={selectedIndex}
            onSelectOption={(index) => {
              setHighlightedIndex(index);
              selectOptionAndCleanUp(options[index]);
            }}
            onMouseEnter={setHighlightedIndex}
          />
        ) : null
      }
    />
  );
}

// Typeahead menu component
interface EntityMentionsTypeaheadMenuProps {
  anchorElementRef: React.RefObject<HTMLElement>;
  options: EntityMentionOption[];
  selectedIndex: number | null;
  onSelectOption: (index: number) => void;
  onMouseEnter: (index: number) => void;
}

function EntityMentionsTypeaheadMenu({
  options,
  selectedIndex,
  onSelectOption,
  onMouseEnter,
}: EntityMentionsTypeaheadMenuProps) {
  const getEntityIcon = (type: EntityType) => {
    switch (type) {
      case 'CHARACTER':
        return '👤';
      case 'LOCATION':
        return '📍';
      case 'ITEM':
        return '🔮';
      case 'LORE':
        return '📜';
      case 'CULTURE':
        return '🏛️';
      case 'CREATURE':
        return '🐉';
      case 'RACE':
        return '👥';
      default:
        return '•';
    }
  };

  const getTypeColor = (type: EntityType) => {
    switch (type) {
      case 'CHARACTER':
        return 'text-bronze';
      case 'LOCATION':
        return 'text-green-600';
      case 'ITEM':
        return 'text-yellow-700';
      case 'LORE':
        return 'text-purple-600';
      case 'CULTURE':
        return 'text-amber-600';
      case 'CREATURE':
        return 'text-red-500';
      case 'RACE':
        return 'text-pink-500';
      default:
        return 'text-faded-ink';
    }
  };

  return (
    <div className="fixed z-50 bg-white border border-slate-ui shadow-lg rounded-sm overflow-hidden min-w-[250px] max-w-[400px]">
      {options.map((option, index) => {
        if (option.isCreateNew) {
          // "Create new entity" option
          return (
            <div
              key={option.entity.id}
              className={`
                px-4 py-2 cursor-pointer flex items-center gap-3 transition-colors border-t border-slate-ui
                ${index === selectedIndex ? 'bg-bronze/10' : 'hover:bg-slate-ui/20'}
              `}
              onClick={() => onSelectOption(index)}
              onMouseEnter={() => onMouseEnter(index)}
            >
              <span className="text-lg">✨</span>
              <div className="flex-1 min-w-0">
                <div className="font-sans text-sm text-bronze font-semibold">
                  Create "{option.entity.name}"
                </div>
                <div className="font-sans text-xs text-faded-ink">
                  Add to Codex as new entity
                </div>
              </div>
            </div>
          );
        }

        // Regular entity option
        return (
          <div
            key={option.entity.id}
            className={`
              px-4 py-2 cursor-pointer flex items-center gap-3 transition-colors
              ${index === selectedIndex ? 'bg-bronze/10' : 'hover:bg-slate-ui/20'}
            `}
            onClick={() => onSelectOption(index)}
            onMouseEnter={() => onMouseEnter(index)}
          >
            <span className="text-lg">{getEntityIcon(option.entity.type)}</span>
            <div className="flex-1 min-w-0">
              <div className="font-sans text-sm text-midnight truncate">
                {option.entity.name}
              </div>
              {option.description && (
                <div className="font-sans text-xs text-faded-ink truncate">
                  {option.description}
                </div>
              )}
            </div>
            <div className={`text-xs font-sans ${getTypeColor(option.entity.type)}`}>
              {option.entity.type}
            </div>
          </div>
        );
      })}

      {options.length === 0 && (
        <div className="px-4 py-3 text-sm text-faded-ink font-sans text-center">
          No entities found. Type to create one!
        </div>
      )}
    </div>
  );
}
