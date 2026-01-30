/**
 * EntityHighlightPlugin - Detect entity names on hover
 * Shows hover cards when hovering over text that matches entity names
 * Uses an event-based approach that doesn't modify Lexical's DOM
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { useCodexStore } from '@/stores/codexStore';
import { EntityHoverCard } from '../EntityHoverCard';
import type { Entity, EntityType } from '@/types/codex';

interface EntityHighlightPluginProps {
  manuscriptId?: string;
  enabled?: boolean;
}

interface HoverState {
  entity: Entity;
  position: { x: number; y: number };
  matchedText: string;
}

export default function EntityHighlightPlugin({
  manuscriptId,
  enabled = true,
}: EntityHighlightPluginProps) {
  const [editor] = useLexicalComposerContext();
  const { entities, setSidebarOpen, setActiveTab, setSelectedEntity } = useCodexStore();
  const [hoverState, setHoverState] = useState<HoverState | null>(null);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastCheckRef = useRef<{ x: number; y: number; time: number } | null>(null);

  // Build a map of entity names/aliases to entities for fast lookup
  const getEntityMap = useCallback(() => {
    const map = new Map<string, Entity>();

    for (const entity of entities) {
      // Add main name (case-insensitive)
      const nameLower = entity.name.toLowerCase();
      if (!map.has(nameLower)) {
        map.set(nameLower, entity);
      }

      // Add aliases
      for (const alias of entity.aliases || []) {
        const aliasLower = alias.toLowerCase();
        if (!map.has(aliasLower)) {
          map.set(aliasLower, entity);
        }
      }
    }

    return map;
  }, [entities]);

  // Get word at position using caretRangeFromPoint
  const getWordAtPoint = useCallback((x: number, y: number): { word: string; rect: DOMRect } | null => {
    // Use caretRangeFromPoint to find text at cursor position
    const range = document.caretRangeFromPoint(x, y);
    if (!range) return null;

    const node = range.startContainer;
    if (node.nodeType !== Node.TEXT_NODE) return null;

    const text = node.textContent || '';
    const offset = range.startOffset;

    // Find word boundaries
    let start = offset;
    let end = offset;

    // Move start backwards to find word start
    while (start > 0 && /\w/.test(text[start - 1])) {
      start--;
    }

    // Move end forwards to find word end
    while (end < text.length && /\w/.test(text[end])) {
      end++;
    }

    if (start === end) return null;

    const word = text.slice(start, end);

    // Get bounding rect for the word
    const wordRange = document.createRange();
    wordRange.setStart(node, start);
    wordRange.setEnd(node, end);
    const rect = wordRange.getBoundingClientRect();

    return { word, rect };
  }, []);

  // Check if we're hovering over an entity name
  const checkForEntity = useCallback((x: number, y: number) => {
    // Skip if inside an entity-mention node (already has hover card)
    const element = document.elementFromPoint(x, y);
    if (element?.closest('.entity-mention')) {
      return null;
    }

    // Get the word at cursor position
    const wordInfo = getWordAtPoint(x, y);
    if (!wordInfo) return null;

    const wordLower = wordInfo.word.toLowerCase();
    const entityMap = getEntityMap();

    // Check if word matches an entity name
    const entity = entityMap.get(wordLower);
    if (entity) {
      return {
        entity,
        matchedText: wordInfo.word,
        rect: wordInfo.rect,
      };
    }

    // Check for multi-word entity names by expanding the search
    // Look at surrounding words
    const range = document.caretRangeFromPoint(x, y);
    if (!range) return null;

    const node = range.startContainer;
    if (node.nodeType !== Node.TEXT_NODE) return null;

    const fullText = node.textContent || '';
    const offset = range.startOffset;

    // Try to find multi-word matches
    for (const [name, entity] of entityMap) {
      if (name.includes(' ')) {
        // Multi-word entity name
        const nameIndex = fullText.toLowerCase().indexOf(name);
        if (nameIndex !== -1 && offset >= nameIndex && offset <= nameIndex + name.length) {
          // Cursor is within this multi-word match
          const wordRange = document.createRange();
          wordRange.setStart(node, nameIndex);
          wordRange.setEnd(node, nameIndex + name.length);
          const rect = wordRange.getBoundingClientRect();

          return {
            entity,
            matchedText: fullText.slice(nameIndex, nameIndex + name.length),
            rect,
          };
        }
      }
    }

    return null;
  }, [getWordAtPoint, getEntityMap]);

  // Handle mouse move on editor
  useEffect(() => {
    if (!enabled || entities.length === 0) return;

    const editorElement = editor.getRootElement();
    if (!editorElement) return;

    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      // Throttle checks to avoid performance issues
      const now = Date.now();
      if (lastCheckRef.current) {
        const { x: lastX, y: lastY, time } = lastCheckRef.current;
        const distance = Math.sqrt((x - lastX) ** 2 + (y - lastY) ** 2);
        const timeDiff = now - time;

        // Skip if mouse hasn't moved much and it was checked recently
        if (distance < 5 && timeDiff < 100) {
          return;
        }
      }
      lastCheckRef.current = { x, y, time: now };

      // Clear existing timeout
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
        hoverTimeoutRef.current = null;
      }

      // Delay the check to avoid flickering
      hoverTimeoutRef.current = setTimeout(() => {
        const result = checkForEntity(x, y);

        if (result) {
          setHoverState({
            entity: result.entity,
            position: { x: result.rect.left, y: result.rect.bottom },
            matchedText: result.matchedText,
          });
        } else {
          setHoverState(null);
        }
      }, 300);
    };

    const handleMouseLeave = () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
        hoverTimeoutRef.current = null;
      }
      setHoverState(null);
    };

    editorElement.addEventListener('mousemove', handleMouseMove);
    editorElement.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      editorElement.removeEventListener('mousemove', handleMouseMove);
      editorElement.removeEventListener('mouseleave', handleMouseLeave);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, [editor, entities, enabled, checkForEntity]);

  const handleViewInCodex = useCallback(() => {
    if (hoverState) {
      setSelectedEntity(hoverState.entity.id);
      setActiveTab('entities');
      setSidebarOpen(true);
      setHoverState(null);
    }
  }, [hoverState, setSelectedEntity, setActiveTab, setSidebarOpen]);

  // Render hover card if hovering over an entity
  if (!hoverState) return null;

  return (
    <EntityHoverCard
      entity={hoverState.entity}
      entityName={hoverState.entity.name}
      entityType={hoverState.entity.type as EntityType}
      position={hoverState.position}
      onViewInCodex={handleViewInCodex}
    />
  );
}
