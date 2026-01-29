/**
 * SelectionToolbar Component
 * Floating toolbar that appears when text is selected in the editor.
 * Provides quick actions like creating entities from selected text.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  SELECTION_CHANGE_COMMAND,
  COMMAND_PRIORITY_LOW,
} from 'lexical';
import { Z_INDEX } from '@/lib/zIndex';

interface SelectionToolbarProps {
  manuscriptId?: string;
  onCreateEntity: (selectedText: string, position: { x: number; y: number }) => void;
}

export default function SelectionToolbar({ manuscriptId, onCreateEntity }: SelectionToolbarProps) {
  const [editor] = useLexicalComposerContext();
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [selectedText, setSelectedText] = useState('');
  const toolbarRef = useRef<HTMLDivElement>(null);

  const updateToolbar = useCallback(() => {
    const selection = window.getSelection();
    const nativeSelection = selection;

    if (!nativeSelection || nativeSelection.rangeCount === 0) {
      setIsVisible(false);
      return;
    }

    const range = nativeSelection.getRangeAt(0);
    const text = nativeSelection.toString().trim();

    // Only show toolbar if there's meaningful text selected (3+ characters)
    if (text.length < 3) {
      setIsVisible(false);
      return;
    }

    // Don't show for very long selections (probably not entity names)
    if (text.length > 100) {
      setIsVisible(false);
      return;
    }

    // Get bounding rect of selection
    const rect = range.getBoundingClientRect();

    // Position toolbar above the selection, centered
    const toolbarWidth = 180; // Approximate width
    const x = rect.left + (rect.width / 2) - (toolbarWidth / 2);
    const y = rect.top - 50; // Above selection

    // Keep toolbar on screen
    const adjustedX = Math.max(10, Math.min(x, window.innerWidth - toolbarWidth - 10));
    const adjustedY = y < 10 ? rect.bottom + 10 : y; // Below if no room above

    setPosition({ x: adjustedX, y: adjustedY + window.scrollY });
    setSelectedText(text);
    setIsVisible(true);
  }, []);

  useEffect(() => {
    // Listen for selection changes in Lexical
    const unregister = editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        // Use setTimeout to ensure DOM selection is updated
        setTimeout(updateToolbar, 10);
        return false;
      },
      COMMAND_PRIORITY_LOW
    );

    // Also listen for native selection changes (for mouse up events)
    const handleMouseUp = () => {
      setTimeout(updateToolbar, 10);
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      // Update on shift+arrow keys (text selection via keyboard)
      if (e.shiftKey && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
        setTimeout(updateToolbar, 10);
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keyup', handleKeyUp);

    // Hide toolbar when clicking outside
    const handleClickOutside = (e: MouseEvent) => {
      if (toolbarRef.current && !toolbarRef.current.contains(e.target as Node)) {
        // Check if we're still inside the editor
        const editorRoot = document.querySelector('.editor-content');
        if (!editorRoot?.contains(e.target as Node)) {
          setIsVisible(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      unregister();
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [editor, updateToolbar]);

  const handleCreateEntity = () => {
    if (selectedText && manuscriptId) {
      onCreateEntity(selectedText, position);
      setIsVisible(false);
    }
  };

  if (!isVisible || !manuscriptId) return null;

  return (
    <div
      ref={toolbarRef}
      className="fixed bg-white border-2 border-bronze shadow-book px-2 py-1.5 flex items-center gap-2 animate-fadeIn"
      style={{
        left: position.x,
        top: position.y,
        zIndex: Z_INDEX.TOOLTIP,
        borderRadius: '2px',
      }}
    >
      <button
        onClick={handleCreateEntity}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-sans font-medium text-midnight hover:bg-bronze hover:text-white transition-colors"
        style={{ borderRadius: '2px' }}
        title={`Create entity from "${selectedText.substring(0, 20)}${selectedText.length > 20 ? '...' : ''}"`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        <span>Create Entity</span>
      </button>

      {/* Small indicator of selected text */}
      <span className="text-xs text-faded-ink border-l border-slate-ui pl-2 max-w-[100px] truncate">
        "{selectedText.substring(0, 15)}{selectedText.length > 15 ? '...' : ''}"
      </span>
    </div>
  );
}
