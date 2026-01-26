/**
 * RealtimeNLPPlugin
 * Detects text changes and sends context window to WebSocket for real-time entity detection
 */

import { useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot } from 'lexical';
import { useRealtimeNLP } from '../../../hooks/useRealtimeNLP';

interface RealtimeNLPPluginProps {
  manuscriptId: string;
}

// Size of context window to send for NLP analysis
const CONTEXT_WINDOW_SIZE = 2000;

export default function RealtimeNLPPlugin({ manuscriptId }: RealtimeNLPPluginProps) {
  const [editor] = useLexicalComposerContext();
  const previousTextRef = useRef<string>('');
  const lastSentContextRef = useRef<string>('');

  // Set up WebSocket connection
  const { sendTextDelta } = useRealtimeNLP({
    manuscriptId,
    enabled: true,
  });

  useEffect(() => {
    // Register update listener
    const removeUpdateListener = editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        // Get current text content
        const root = $getRoot();
        const currentText = root.getTextContent();

        // Only process if text has changed
        const previousText = previousTextRef.current;
        if (currentText === previousText) {
          return;
        }

        // Check if text grew (user is typing/adding content)
        if (currentText.length > previousText.length) {
          // Get context window (last N chars for spaCy context)
          const contextWindow = currentText.slice(-CONTEXT_WINDOW_SIZE);

          // Only send if context has meaningfully changed
          // (avoids redundant sends when just cursor moves or minor edits)
          if (contextWindow !== lastSentContextRef.current) {
            // Check if there's meaningful new content (not just whitespace)
            const newContent = currentText.substring(previousText.length);
            if (newContent.trim().length > 0) {
              sendTextDelta(contextWindow);
              lastSentContextRef.current = contextWindow;
            }
          }
        }

        // Update previous text reference
        previousTextRef.current = currentText;
      });
    });

    return () => {
      removeUpdateListener();
    };
  }, [editor, sendTextDelta]);

  return null; // This plugin doesn't render anything
}
