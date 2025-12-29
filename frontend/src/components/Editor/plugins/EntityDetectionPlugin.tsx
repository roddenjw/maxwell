/**
 * EntityDetectionPlugin - Auto-detect entities while writing
 * Analyzes text and suggests new entities for the Codex
 */

import { useEffect, useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot } from 'lexical';
import { useCodexStore } from '@/stores/codexStore';

interface EntityDetectionPluginProps {
  manuscriptId?: string;
  enabled?: boolean;
}

export default function EntityDetectionPlugin({
  manuscriptId,
  enabled = true,
}: EntityDetectionPluginProps) {
  const [editor] = useLexicalComposerContext();
  const { setAnalyzing } = useCodexStore();

  // Debounced entity analysis
  const analyzeText = useCallback(
    async (text: string) => {
      if (!enabled || !manuscriptId || text.length < 100) {
        // Don't analyze very short text
        return;
      }

      try {
        setAnalyzing(true);

        const response = await fetch('http://localhost:8000/api/codex/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            manuscript_id: manuscriptId,
            text,
          }),
        });

        if (response.ok) {
          // Analysis happens in background
          // Suggestions will be loaded when Codex sidebar is opened
          console.log('Entity analysis started');
        }
      } catch (error) {
        console.error('Entity detection failed:', error);
      } finally {
        setAnalyzing(false);
      }
    },
    [manuscriptId, enabled, setAnalyzing]
  );

  // Register editor update listener
  useEffect(() => {
    if (!enabled || !manuscriptId) {
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    let lastAnalyzedText = '';

    const removeUpdateListener = editor.registerUpdateListener(({ editorState }) => {
      // Clear previous timeout
      clearTimeout(timeoutId);

      // Debounce: wait 5 seconds after typing stops
      timeoutId = setTimeout(() => {
        editorState.read(() => {
          const root = $getRoot();
          const text = root.getTextContent();

          // Only analyze if text has changed significantly (>50 characters)
          if (Math.abs(text.length - lastAnalyzedText.length) > 50) {
            lastAnalyzedText = text;
            analyzeText(text);
          }
        });
      }, 5000); // 5 second delay to avoid over-analyzing
    });

    return () => {
      removeUpdateListener();
      clearTimeout(timeoutId);
    };
  }, [editor, analyzeText, enabled, manuscriptId]);

  // This plugin doesn't render anything
  return null;
}
