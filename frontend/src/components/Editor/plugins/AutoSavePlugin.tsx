/**
 * AutoSavePlugin - Automatically saves manuscript content to store
 * Debounced to avoid excessive saves (5 second delay)
 */

import { useEffect, useRef, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, EditorState } from 'lexical';
import { useManuscriptStore } from '@/stores/manuscriptStore';

interface AutoSavePluginProps {
  manuscriptId: string;
  onSaveStatusChange?: (status: 'saved' | 'saving' | 'unsaved') => void;
}

export default function AutoSavePlugin({ manuscriptId, onSaveStatusChange }: AutoSavePluginProps) {
  const [editor] = useLexicalComposerContext();
  const { updateManuscript } = useManuscriptStore();
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');

  useEffect(() => {
    // Update parent component when save status changes
    onSaveStatusChange?.(saveStatus);
  }, [saveStatus, onSaveStatusChange]);

  useEffect(() => {
    // Register listener for editor state changes
    const removeUpdateListener = editor.registerUpdateListener(
      ({ editorState }: { editorState: EditorState }) => {
        // Mark as unsaved
        setSaveStatus('unsaved');

        // Clear existing timeout
        if (saveTimeoutRef.current) {
          clearTimeout(saveTimeoutRef.current);
        }

        // Debounce save for 5 seconds
        saveTimeoutRef.current = setTimeout(() => {
          setSaveStatus('saving');
          saveManuscript(editorState);
        }, 5000);
      }
    );

    // Cleanup
    return () => {
      removeUpdateListener();
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [editor, manuscriptId]);

  const saveManuscript = (editorState: EditorState) => {
    // Serialize editor state to JSON
    const serializedState = JSON.stringify(editorState.toJSON());

    // Calculate word count
    const wordCount = editorState.read(() => {
      const root = $getRoot();
      const text = root.getTextContent();
      const words = text.trim().split(/\s+/).filter((word) => word.length > 0);
      return words.length;
    });

    // Update manuscript in store
    updateManuscript(manuscriptId, {
      content: serializedState,
      wordCount: wordCount,
    });

    // Mark as saved
    setSaveStatus('saved');
    console.log(`Auto-saved manuscript ${manuscriptId}: ${wordCount} words`);
  };

  // This plugin doesn't render anything
  return null;
}
