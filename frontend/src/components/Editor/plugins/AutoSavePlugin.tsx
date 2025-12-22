/**
 * AutoSavePlugin - Automatically saves manuscript content to store
 * Debounced to avoid excessive saves (5 second delay)
 * Optionally creates version snapshots every 5 minutes
 */

import { useEffect, useRef, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, EditorState } from 'lexical';
import { useManuscriptStore } from '@/stores/manuscriptStore';
import { versioningApi } from '@/lib/api';

interface AutoSavePluginProps {
  manuscriptId: string;
  onSaveStatusChange?: (status: 'saved' | 'saving' | 'unsaved') => void;
  enableSnapshots?: boolean; // Create version snapshots
  snapshotInterval?: number; // Minutes between auto-snapshots (default: 5)
}

export default function AutoSavePlugin({
  manuscriptId,
  onSaveStatusChange,
  enableSnapshots = false,
  snapshotInterval = 5,
}: AutoSavePluginProps) {
  const [editor] = useLexicalComposerContext();
  const { updateManuscript } = useManuscriptStore();
  const saveTimeoutRef = useRef<number | null>(null);
  const lastSnapshotTimeRef = useRef<number>(Date.now());
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

  const saveManuscript = async (editorState: EditorState) => {
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

    // Create snapshot if enabled and enough time has passed
    if (enableSnapshots) {
      const now = Date.now();
      const timeSinceLastSnapshot = now - lastSnapshotTimeRef.current;
      const intervalMs = snapshotInterval * 60 * 1000; // Convert minutes to milliseconds

      if (timeSinceLastSnapshot >= intervalMs) {
        try {
          await versioningApi.createSnapshot({
            manuscript_id: manuscriptId,
            content: serializedState,
            trigger_type: 'AUTO',
            label: 'Auto-save snapshot',
            word_count: wordCount,
          });
          lastSnapshotTimeRef.current = now;
          console.log(`Created auto-snapshot for manuscript ${manuscriptId}`);
        } catch (error) {
          console.error('Failed to create snapshot:', error);
        }
      }
    }

    // Mark as saved
    setSaveStatus('saved');
    console.log(`Auto-saved manuscript ${manuscriptId}: ${wordCount} words`);
  };

  // This plugin doesn't render anything
  return null;
}
