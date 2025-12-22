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
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';

interface EditorToolbarProps {
  manuscriptId?: string;
}

export default function EditorToolbar({ manuscriptId }: EditorToolbarProps = {}) {
  const [editor] = useLexicalComposerContext();
  const { setAnalyzing, setSidebarOpen, setActiveTab } = useCodexStore();
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

  const handleAnalyze = async () => {
    if (!manuscriptId) {
      alert('No manuscript selected');
      return;
    }

    try {
      // Extract text from editor
      const editorState = editor.getEditorState();
      let text = '';

      editorState.read(() => {
        const root = editorState._nodeMap;
        root.forEach((node) => {
          if ('__text' in node) {
            text += node.__text + ' ';
          }
        });
      });

      if (!text.trim()) {
        alert('No text to analyze. Start writing first!');
        return;
      }

      setAnalyzing(true);

      // Call analyze API
      await codexApi.analyzeText({
        manuscript_id: manuscriptId,
        text: text.trim(),
      });

      // Show success and open Codex sidebar to Intel tab
      alert('✅ Analysis started! Check the Intel tab for detected entities.');
      setSidebarOpen(true);
      setActiveTab('intel');
    } catch (err) {
      alert('Failed to analyze: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setAnalyzing(false);
    }
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
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <select
          className="px-2 py-1 bg-white border border-slate-ui text-midnight text-sm font-sans"
          style={{ borderRadius: '2px' }}
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
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
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
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <ToolbarButton onClick={insertSceneBreak} title="Insert Scene Break">
          * * *
        </ToolbarButton>
      </div>

      {/* Codex Analyze button */}
      {manuscriptId && (
        <div className="toolbar-group flex gap-1">
          <ToolbarButton
            onClick={handleAnalyze}
            title="Analyze manuscript text to detect characters, locations, items, and lore using NLP"
          >
            🔍 Analyze
          </ToolbarButton>
        </div>
      )}
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
        px-3 py-1.5 font-sans font-medium text-sm
        transition-colors
        ${
          active
            ? 'bg-bronze text-white'
            : 'bg-slate-ui text-midnight hover:bg-bronze hover:bg-opacity-20'
        }
      `}
      style={{ borderRadius: '2px' }}
    >
      {children}
    </button>
  );
}
