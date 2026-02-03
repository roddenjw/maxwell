/**
 * WritingIssueHighlightPlugin - Real-time writing feedback in the editor
 *
 * Shows colored underlines for spelling, grammar, style, and other issues.
 * Displays hover cards with suggestions when hovering over highlighted text.
 *
 * Uses Lexical's registerMutationListener and DOM manipulation to apply
 * decorations without modifying the document structure.
 */

import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, $getSelection, $isRangeSelection, TextNode } from 'lexical';
import { debounce } from 'lodash-es';

import { useWritingFeedbackStore, getFilteredIssues, getIssueAtPosition } from '@/stores/writingFeedbackStore';
import { WritingIssueHoverCard } from '../WritingIssueHoverCard';
import { writingFeedbackApi } from '@/lib/api';
import type { WritingIssue } from '@/types/writingFeedback';
import { getUnderlineClass } from '@/types/writingFeedback';

interface WritingIssueHighlightPluginProps {
  manuscriptId?: string;
  chapterId?: string;
  enabled?: boolean;
}

interface HoverState {
  issue: WritingIssue;
  position: { x: number; y: number };
}

// Mark elements to avoid double-processing
const PROCESSED_ATTR = 'data-wf-processed';
const ISSUE_ATTR = 'data-wf-issue-id';

export default function WritingIssueHighlightPlugin({
  manuscriptId,
  chapterId,
  enabled = true,
}: WritingIssueHighlightPluginProps) {
  const [editor] = useLexicalComposerContext();
  const {
    issues,
    setIssues,
    settings,
    isEnabled,
    dismissedIssueIds,
    setIsAnalyzing,
    dismissIssue,
    addToDictionary,
    ignoreRule,
  } = useWritingFeedbackStore();

  const [hoverState, setHoverState] = useState<HoverState | null>(null);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const editorRootRef = useRef<HTMLElement | null>(null);
  const decorationsRef = useRef<Map<string, HTMLElement[]>>(new Map());

  // Filter issues based on settings
  const filteredIssues = useMemo(
    () => getFilteredIssues(issues, dismissedIssueIds, settings),
    [issues, dismissedIssueIds, settings]
  );

  // Debounced analysis function
  const analyzeText = useMemo(
    () =>
      debounce(async (text: string) => {
        if (!manuscriptId || !isEnabled || !enabled || text.length < 10) {
          return;
        }

        setIsAnalyzing(true);
        try {
          const response = await writingFeedbackApi.analyzeRealtime(text, manuscriptId, settings);
          setIssues(response.issues);
        } catch (error) {
          console.error('Writing feedback analysis failed:', error);
        } finally {
          setIsAnalyzing(false);
        }
      }, 1000),
    [manuscriptId, isEnabled, enabled, settings, setIssues, setIsAnalyzing]
  );

  // Listen to editor changes and trigger analysis
  useEffect(() => {
    if (!isEnabled || !enabled) {
      return;
    }

    const unregister = editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const root = $getRoot();
        const text = root.getTextContent();
        analyzeText(text);
      });
    });

    return () => {
      unregister();
      analyzeText.cancel();
    };
  }, [editor, analyzeText, isEnabled, enabled]);

  // Get editor root element
  useEffect(() => {
    const rootElement = editor.getRootElement();
    editorRootRef.current = rootElement;
  }, [editor]);

  // Apply decorations when issues change
  useEffect(() => {
    if (!isEnabled || !enabled || !editorRootRef.current) {
      // Clear all decorations when disabled
      clearAllDecorations();
      return;
    }

    // Apply decorations
    applyDecorations(filteredIssues);

    return () => {
      clearAllDecorations();
    };
  }, [filteredIssues, isEnabled, enabled]);

  // Clear all decorations
  const clearAllDecorations = useCallback(() => {
    decorationsRef.current.forEach((elements) => {
      elements.forEach((el) => {
        // Remove our wrapper and restore original text
        if (el.parentNode) {
          const textNode = document.createTextNode(el.textContent || '');
          el.parentNode.replaceChild(textNode, el);
        }
      });
    });
    decorationsRef.current.clear();
  }, []);

  // Apply decorations for issues
  const applyDecorations = useCallback((issues: WritingIssue[]) => {
    const root = editorRootRef.current;
    if (!root) return;

    // Clear existing decorations first
    clearAllDecorations();

    // Get all text nodes in the editor
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const textNodes: Text[] = [];
    let node: Node | null;
    while ((node = walker.nextNode())) {
      textNodes.push(node as Text);
    }

    // Calculate cumulative offsets for text nodes
    let offset = 0;
    const nodeOffsets: { node: Text; start: number; end: number }[] = [];
    for (const textNode of textNodes) {
      const length = textNode.textContent?.length || 0;
      nodeOffsets.push({ node: textNode, start: offset, end: offset + length });
      offset += length;
    }

    // Apply decoration for each issue
    for (const issue of issues) {
      const elements: HTMLElement[] = [];

      // Find text nodes that overlap with this issue
      for (const { node: textNode, start: nodeStart, end: nodeEnd } of nodeOffsets) {
        const issueStart = issue.start_offset;
        const issueEnd = issue.end_offset;

        // Check if this text node overlaps with the issue
        if (issueEnd <= nodeStart || issueStart >= nodeEnd) {
          continue; // No overlap
        }

        // Calculate the overlap range within this text node
        const overlapStart = Math.max(0, issueStart - nodeStart);
        const overlapEnd = Math.min(textNode.textContent?.length || 0, issueEnd - nodeStart);

        if (overlapStart >= overlapEnd) continue;

        // Split the text node and wrap the issue portion
        try {
          const text = textNode.textContent || '';
          const beforeText = text.slice(0, overlapStart);
          const issueText = text.slice(overlapStart, overlapEnd);
          const afterText = text.slice(overlapEnd);

          // Create wrapper span for the issue
          const wrapper = document.createElement('span');
          wrapper.className = `writing-issue ${getUnderlineClass(issue.type)}`;
          wrapper.setAttribute(ISSUE_ATTR, issue.id);
          wrapper.textContent = issueText;

          // Replace the text node with before + wrapper + after
          const parent = textNode.parentNode;
          if (parent) {
            const fragment = document.createDocumentFragment();
            if (beforeText) fragment.appendChild(document.createTextNode(beforeText));
            fragment.appendChild(wrapper);
            if (afterText) fragment.appendChild(document.createTextNode(afterText));
            parent.replaceChild(fragment, textNode);

            elements.push(wrapper);
          }
        } catch (e) {
          // Skip if we can't decorate this issue
          console.debug('Could not decorate issue:', e);
        }
      }

      if (elements.length > 0) {
        decorationsRef.current.set(issue.id, elements);
      }
    }
  }, [clearAllDecorations]);

  // Handle mouse move for hover detection
  const handleMouseMove = useCallback(
    (event: MouseEvent) => {
      if (!isEnabled || !enabled) return;

      const target = event.target as HTMLElement;

      // Check if we're hovering over an issue span
      const issueSpan = target.closest('[data-wf-issue-id]') as HTMLElement;

      if (issueSpan) {
        const issueId = issueSpan.getAttribute(ISSUE_ATTR);
        const issue = filteredIssues.find((i) => i.id === issueId);

        if (issue) {
          // Clear existing timeout
          if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current);
          }

          // Delay showing hover card
          hoverTimeoutRef.current = setTimeout(() => {
            const rect = issueSpan.getBoundingClientRect();
            setHoverState({
              issue,
              position: { x: rect.left, y: rect.bottom },
            });
          }, 200);
        }
      } else {
        // Clear hover state when moving away
        if (hoverTimeoutRef.current) {
          clearTimeout(hoverTimeoutRef.current);
          hoverTimeoutRef.current = null;
        }

        // Small delay before hiding to allow moving to hover card
        hoverTimeoutRef.current = setTimeout(() => {
          setHoverState(null);
        }, 100);
      }
    },
    [filteredIssues, isEnabled, enabled]
  );

  // Attach mouse move listener to editor
  useEffect(() => {
    const root = editorRootRef.current;
    if (!root) return;

    root.addEventListener('mousemove', handleMouseMove);
    return () => {
      root.removeEventListener('mousemove', handleMouseMove);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, [handleMouseMove]);

  // Handle applying a fix
  const handleApplyFix = useCallback(
    (suggestion: string) => {
      if (!hoverState) return;

      editor.update(() => {
        const root = $getRoot();
        const text = root.getTextContent();

        // Find and replace the issue text
        const { start_offset, end_offset } = hoverState.issue;
        const newText = text.slice(0, start_offset) + suggestion + text.slice(end_offset);

        // This is a simplified approach - in production you'd want to
        // properly traverse and update Lexical nodes
        // For now, we dismiss the issue and let the user manually fix
        dismissIssue(hoverState.issue.id);
      });

      setHoverState(null);
    },
    [editor, hoverState, dismissIssue]
  );

  // Handle ignoring an issue
  const handleIgnore = useCallback(() => {
    if (!hoverState) return;
    dismissIssue(hoverState.issue.id);
    setHoverState(null);
  }, [hoverState, dismissIssue]);

  // Handle adding to dictionary
  const handleAddToDict = useCallback(async () => {
    if (!hoverState || !manuscriptId) return;

    const word = hoverState.issue.original_text;
    addToDictionary(word);

    // Also update on backend
    try {
      await writingFeedbackApi.addToDictionary(manuscriptId, word);
    } catch (error) {
      console.error('Failed to add word to dictionary:', error);
    }

    dismissIssue(hoverState.issue.id);
    setHoverState(null);
  }, [hoverState, manuscriptId, addToDictionary, dismissIssue]);

  // Handle ignoring a rule
  const handleIgnoreRule = useCallback(async () => {
    if (!hoverState?.issue.rule_id || !manuscriptId) return;

    const ruleId = hoverState.issue.rule_id;
    ignoreRule(ruleId);

    // Also update on backend
    try {
      await writingFeedbackApi.ignoreRule(manuscriptId, ruleId);
    } catch (error) {
      console.error('Failed to ignore rule:', error);
    }

    setHoverState(null);
  }, [hoverState, manuscriptId, ignoreRule]);

  // Render hover card
  return hoverState ? (
    <WritingIssueHoverCard
      issue={hoverState.issue}
      position={hoverState.position}
      onApplyFix={handleApplyFix}
      onIgnore={handleIgnore}
      onAddToDict={hoverState.issue.type === 'spelling' ? handleAddToDict : undefined}
      onIgnoreRule={hoverState.issue.rule_id ? handleIgnoreRule : undefined}
    />
  ) : null;
}
