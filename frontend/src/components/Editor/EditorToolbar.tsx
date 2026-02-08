/**
 * EditorToolbar Component
 * Streamlined toolbar with essential writing controls
 * Format dropdown consolidates alignment, lists, and font options
 */

import { useCallback, useEffect, useState, useRef } from 'react';
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
import { useOutlineStore } from '@/stores/outlineStore';

interface EditorToolbarProps {
  manuscriptId?: string;
  chapterId?: string;
  chapterTitle?: string;
}

export default function EditorToolbar(_props: EditorToolbarProps = {}) {
  const [editor] = useLexicalComposerContext();
  const { outline, toggleOutlineReferenceSidebar, outlineReferenceSidebarOpen } = useOutlineStore();
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);
  const [blockType, setBlockType] = useState('paragraph');
  const [textAlign, setTextAlign] = useState('left');
  const [showFormatMenu, setShowFormatMenu] = useState(false);
  const formatMenuRef = useRef<HTMLDivElement>(null);
  const [focusMode, setFocusMode] = useState(() => {
    const saved = localStorage.getItem('maxwell-focus-mode');
    return saved === 'true';
  });

  // Persist focus mode preference
  const toggleFocusMode = () => {
    const newMode = !focusMode;
    setFocusMode(newMode);
    localStorage.setItem('maxwell-focus-mode', String(newMode));
  };

  // Close format menu when clicking outside
  useEffect(() => {
    if (!showFormatMenu) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (formatMenuRef.current && !formatMenuRef.current.contains(e.target as Node)) {
        setShowFormatMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showFormatMenu]);

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
  const formatBold = () => editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
  const formatItalic = () => editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'italic');
  const formatUnderline = () => editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'underline');

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

  const undo = () => editor.dispatchCommand(UNDO_COMMAND, undefined);
  const redo = () => editor.dispatchCommand(REDO_COMMAND, undefined);

  const insertSceneBreak = () => {
    editor.update(() => {
      const sceneBreakNode = $createSceneBreakNode();
      $insertNodes([sceneBreakNode]);
    });
  };

  const formatBulletList = () => editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
  const formatNumberedList = () => editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);

  const formatTextAlign = (alignment: 'left' | 'center' | 'right' | 'justify') => {
    editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, alignment);
    setTextAlign(alignment);
  };

  // Focus mode: show minimal toolbar
  if (focusMode) {
    return (
      <div className="toolbar flex items-center justify-between p-2 bg-vellum/50">
        <div className="flex items-center gap-2 text-xs text-faded-ink">
          <span>Focus Mode</span>
          <span className="text-midnight/30">|</span>
          <span>Cmd+B bold</span>
          <span>Cmd+I italic</span>
        </div>
        <ToolbarButton
          onClick={toggleFocusMode}
          active={focusMode}
          title="Exit focus mode"
        >
          Show Toolbar
        </ToolbarButton>
      </div>
    );
  }

  return (
    <div className="toolbar flex items-center gap-1 p-2 flex-wrap">
      {/* Undo/Redo */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <ToolbarButton onClick={undo} title="Undo (Ctrl+Z)">
          &larrhk;
        </ToolbarButton>
        <ToolbarButton onClick={redo} title="Redo (Ctrl+Y)">
          &rarrhk;
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
        <ToolbarButton onClick={formatBold} active={isBold} title="Bold (Ctrl+B)">
          <strong>B</strong>
        </ToolbarButton>
        <ToolbarButton onClick={formatItalic} active={isItalic} title="Italic (Ctrl+I)">
          <em>I</em>
        </ToolbarButton>
        <ToolbarButton onClick={formatUnderline} active={isUnderline} title="Underline (Ctrl+U)">
          <span className="underline">U</span>
        </ToolbarButton>
      </div>

      {/* Format dropdown (alignment + lists) */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2 relative" ref={formatMenuRef}>
        <ToolbarButton
          onClick={() => setShowFormatMenu(!showFormatMenu)}
          title="Paragraph formatting"
        >
          &para; Format
        </ToolbarButton>

        {showFormatMenu && (
          <div className="absolute top-full left-0 mt-1 bg-white border border-slate-ui shadow-lg rounded-sm z-50 py-1 min-w-[160px]">
            <div className="px-3 py-1 text-xs text-faded-ink font-semibold">Alignment</div>
            <button
              onClick={() => { formatTextAlign('left'); setShowFormatMenu(false); }}
              className={`w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 ${textAlign === 'left' ? 'bg-bronze/10 text-bronze' : 'text-midnight'}`}
            >
              Align Left
            </button>
            <button
              onClick={() => { formatTextAlign('center'); setShowFormatMenu(false); }}
              className={`w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 ${textAlign === 'center' ? 'bg-bronze/10 text-bronze' : 'text-midnight'}`}
            >
              Center
            </button>
            <button
              onClick={() => { formatTextAlign('right'); setShowFormatMenu(false); }}
              className={`w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 ${textAlign === 'right' ? 'bg-bronze/10 text-bronze' : 'text-midnight'}`}
            >
              Align Right
            </button>
            <button
              onClick={() => { formatTextAlign('justify'); setShowFormatMenu(false); }}
              className={`w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 ${textAlign === 'justify' ? 'bg-bronze/10 text-bronze' : 'text-midnight'}`}
            >
              Justify
            </button>
            <hr className="my-1 border-slate-ui" />
            <div className="px-3 py-1 text-xs text-faded-ink font-semibold">Lists</div>
            <button
              onClick={() => { formatBulletList(); setShowFormatMenu(false); }}
              className="w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 text-midnight"
            >
              &bull; Bullet List
            </button>
            <button
              onClick={() => { formatNumberedList(); setShowFormatMenu(false); }}
              className="w-full text-left px-4 py-1.5 text-sm hover:bg-slate-ui/20 text-midnight"
            >
              1. Numbered List
            </button>
          </div>
        )}
      </div>

      {/* Scene break button */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <ToolbarButton onClick={insertSceneBreak} title="Insert Scene Break">
          * * *
        </ToolbarButton>
      </div>

      {/* Outline Reference Sidebar Toggle — icon-only */}
      {outline && (
        <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
          <ToolbarButton
            onClick={toggleOutlineReferenceSidebar}
            active={outlineReferenceSidebarOpen}
            title={outlineReferenceSidebarOpen ? "Hide outline reference" : "Show outline reference while writing"}
          >
            &#x1F4CB;
          </ToolbarButton>
        </div>
      )}

      {/* Spacer to push focus mode right */}
      <div className="flex-1" />

      {/* Focus Mode Toggle */}
      <div className="toolbar-group flex gap-1">
        <ToolbarButton
          onClick={toggleFocusMode}
          active={focusMode}
          title="Enter focus mode (hide toolbar for distraction-free writing)"
        >
          &#x1F3AF; Focus
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
