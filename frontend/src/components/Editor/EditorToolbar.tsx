/**
 * EditorToolbar Component
 * Toolbar with formatting buttons for the Lexical editor
 */

import { useCallback, useEffect, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  REDO_COMMAND,
  UNDO_COMMAND,
} from 'lexical';
import { $setBlocksType } from '@lexical/selection';
import { $createHeadingNode, $createQuoteNode, HeadingTagType } from '@lexical/rich-text';
import { $createParagraphNode, $insertNodes } from 'lexical';
import { $createSceneBreakNode } from './nodes/SceneBreakNode';

export default function EditorToolbar() {
  const [editor] = useLexicalComposerContext();
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);
  const [blockType, setBlockType] = useState('paragraph');

  // Update toolbar state based on selection
  const updateToolbar = useCallback(() => {
    const selection = $getSelection();
    if ($isRangeSelection(selection)) {
      setIsBold(selection.hasFormat('bold'));
      setIsItalic(selection.hasFormat('italic'));
      setIsUnderline(selection.hasFormat('underline'));
    }
  }, []);

  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        updateToolbar();
      });
    });
  }, [editor, updateToolbar]);

  // Format text commands
  const formatBold = () => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
  };

  const formatItalic = () => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'italic');
  };

  const formatUnderline = () => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'underline');
  };

  const formatHeading = (headingSize: HeadingTagType) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createHeadingNode(headingSize));
      }
    });
  };

  const formatQuote = () => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createQuoteNode());
      }
    });
  };

  const formatParagraph = () => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createParagraphNode());
      }
    });
  };

  const undo = () => {
    editor.dispatchCommand(UNDO_COMMAND, undefined);
  };

  const redo = () => {
    editor.dispatchCommand(REDO_COMMAND, undefined);
  };

  const insertSceneBreak = () => {
    editor.update(() => {
      const sceneBreakNode = $createSceneBreakNode();
      $insertNodes([sceneBreakNode]);
    });
  };

  return (
    <div className="toolbar flex items-center gap-1 p-2 flex-wrap">
      {/* Undo/Redo */}
      <div className="toolbar-group flex gap-1 border-r border-gray-300 dark:border-gray-700 pr-2 mr-2">
        <ToolbarButton onClick={undo} title="Undo (Ctrl+Z)">
          ↶
        </ToolbarButton>
        <ToolbarButton onClick={redo} title="Redo (Ctrl+Y)">
          ↷
        </ToolbarButton>
      </div>

      {/* Block type */}
      <div className="toolbar-group flex gap-1 border-r border-gray-300 dark:border-gray-700 pr-2 mr-2">
        <select
          className="px-2 py-1 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-sm"
          value={blockType}
          onChange={(e) => {
            const value = e.target.value;
            setBlockType(value);
            if (value === 'paragraph') {
              formatParagraph();
            } else if (value === 'quote') {
              formatQuote();
            } else if (value.startsWith('h')) {
              formatHeading(value as HeadingTagType);
            }
          }}
        >
          <option value="paragraph">Normal</option>
          <option value="h1">Heading 1</option>
          <option value="h2">Heading 2</option>
          <option value="h3">Heading 3</option>
          <option value="quote">Quote</option>
        </select>
      </div>

      {/* Text formatting */}
      <div className="toolbar-group flex gap-1 border-r border-gray-300 dark:border-gray-700 pr-2 mr-2">
        <ToolbarButton
          onClick={formatBold}
          active={isBold}
          title="Bold (Ctrl+B)"
        >
          <strong>B</strong>
        </ToolbarButton>
        <ToolbarButton
          onClick={formatItalic}
          active={isItalic}
          title="Italic (Ctrl+I)"
        >
          <em>I</em>
        </ToolbarButton>
        <ToolbarButton
          onClick={formatUnderline}
          active={isUnderline}
          title="Underline (Ctrl+U)"
        >
          <span className="underline">U</span>
        </ToolbarButton>
      </div>

      {/* Scene break button */}
      <div className="toolbar-group flex gap-1">
        <ToolbarButton onClick={insertSceneBreak} title="Insert Scene Break">
          * * *
        </ToolbarButton>
      </div>
    </div>
  );
}

// Toolbar button component
interface ToolbarButtonProps {
  onClick: () => void;
  active?: boolean;
  title?: string;
  children: React.ReactNode;
}

function ToolbarButton({ onClick, active = false, title, children }: ToolbarButtonProps) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`
        px-3 py-1.5 rounded
        transition-colors
        ${
          active
            ? 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100'
            : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
        }
        text-sm font-medium
      `}
    >
      {children}
    </button>
  );
}
