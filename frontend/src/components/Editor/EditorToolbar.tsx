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
  FORMAT_ELEMENT_COMMAND,
} from 'lexical';
import { $setBlocksType } from '@lexical/selection';
import { $createHeadingNode, $createQuoteNode, HeadingTagType } from '@lexical/rich-text';
import { $createParagraphNode, $insertNodes } from 'lexical';
import { INSERT_UNORDERED_LIST_COMMAND, INSERT_ORDERED_LIST_COMMAND } from '@lexical/list';
import { $createSceneBreakNode } from './nodes/SceneBreakNode';
import { codexApi, timelineApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import ChapterRecapModal from '@/components/Chapter/ChapterRecapModal';

interface EditorToolbarProps {
  manuscriptId?: string;
  chapterId?: string;
  chapterTitle?: string;
}

export default function EditorToolbar({ manuscriptId, chapterId, chapterTitle }: EditorToolbarProps = {}) {
  const [editor] = useLexicalComposerContext();
  const { setAnalyzing, setSidebarOpen, setActiveTab } = useCodexStore();
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);
  const [blockType, setBlockType] = useState('paragraph');
  const [fontFamily, setFontFamily] = useState('EB Garamond');
  const [fontSize, setFontSize] = useState('16px');
  const [textAlign, setTextAlign] = useState('left');
  const [showRecapModal, setShowRecapModal] = useState(false);

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

  // List formatting
  const formatBulletList = () => {
    editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
  };

  const formatNumberedList = () => {
    editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
  };

  // Text alignment
  const formatTextAlign = (alignment: 'left' | 'center' | 'right' | 'justify') => {
    editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, alignment);
    setTextAlign(alignment);
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

      // Call both analyze APIs in parallel
      await Promise.all([
        codexApi.analyzeText({
          manuscript_id: manuscriptId,
          text: text.trim(),
        }),
        timelineApi.analyzeTimeline({
          manuscript_id: manuscriptId,
          text: text.trim(),
        }),
      ]);

      // Show success and open Codex sidebar to Intel tab
      alert('✅ Analysis complete! Check the Intel tab for entities and the Timeline tab for events.');
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

      {/* Font family */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <select
          className="px-2 py-1 bg-white border border-slate-ui text-midnight text-sm font-sans"
          style={{ borderRadius: '2px' }}
          value={fontFamily}
          onChange={(e) => setFontFamily(e.target.value)}
        >
          <option value="EB Garamond">EB Garamond</option>
          <option value="Georgia">Georgia</option>
          <option value="Inter">Inter</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Arial">Arial</option>
        </select>
      </div>

      {/* Font size */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <select
          className="px-2 py-1 bg-white border border-slate-ui text-midnight text-sm font-sans"
          style={{ borderRadius: '2px' }}
          value={fontSize}
          onChange={(e) => setFontSize(e.target.value)}
        >
          <option value="12px">12px</option>
          <option value="14px">14px</option>
          <option value="16px">16px</option>
          <option value="18px">18px</option>
          <option value="20px">20px</option>
          <option value="24px">24px</option>
          <option value="28px">28px</option>
          <option value="32px">32px</option>
          <option value="36px">36px</option>
          <option value="48px">48px</option>
        </select>
      </div>

      {/* Text alignment */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <ToolbarButton
          onClick={() => formatTextAlign('left')}
          active={textAlign === 'left'}
          title="Align Left"
        >
          ≡
        </ToolbarButton>
        <ToolbarButton
          onClick={() => formatTextAlign('center')}
          active={textAlign === 'center'}
          title="Align Center"
        >
          ≡
        </ToolbarButton>
        <ToolbarButton
          onClick={() => formatTextAlign('right')}
          active={textAlign === 'right'}
          title="Align Right"
        >
          ≡
        </ToolbarButton>
        <ToolbarButton
          onClick={() => formatTextAlign('justify')}
          active={textAlign === 'justify'}
          title="Justify"
        >
          ≡
        </ToolbarButton>
      </div>

      {/* Lists */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <ToolbarButton onClick={formatBulletList} title="Bullet List">
          • List
        </ToolbarButton>
        <ToolbarButton onClick={formatNumberedList} title="Numbered List">
          1. List
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
        <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
          <ToolbarButton
            onClick={handleAnalyze}
            title="Analyze manuscript text to detect characters, locations, items, and lore using NLP"
          >
            🔍 Analyze
          </ToolbarButton>
        </div>
      )}

      {/* Chapter Recap button */}
      {chapterId && (
        <div className="toolbar-group flex gap-1">
          <ToolbarButton
            onClick={() => setShowRecapModal(true)}
            title="Generate an AI-powered chapter recap with themes, events, and character developments"
          >
            📖 Recap
          </ToolbarButton>
        </div>
      )}

      {/* Recap Modal */}
      {showRecapModal && chapterId && (
        <ChapterRecapModal
          chapterId={chapterId}
          chapterTitle={chapterTitle || 'Chapter'}
          onClose={() => setShowRecapModal(false)}
        />
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
