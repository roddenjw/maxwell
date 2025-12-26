/**
 * RealtimeNLPPlugin
 * Detects text changes and sends deltas to WebSocket for real-time entity detection
 */

import { useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot } from 'lexical';
import { useRealtimeNLP } from '../../../hooks/useRealtimeNLP';

interface RealtimeNLPPluginProps {
  manuscriptId: string;
}

export default function RealtimeNLPPlugin({ manuscriptId }: RealtimeNLPPluginProps) {
  const [editor] = useLexicalComposerContext();
  const previousTextRef = useRef<string>('');

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

        // Calculate delta (new text since last update)
        const previousText = previousTextRef.current;

        // Simple delta detection: if text grew, send the new portion
        if (currentText.length > previousText.length) {
          const textDelta = currentText.substring(previousText.length);

          // Only send if delta is meaningful (not just whitespace)
          if (textDelta.trim().length > 0) {
            sendTextDelta(textDelta);
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
