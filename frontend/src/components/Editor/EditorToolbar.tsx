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
import { useOutlineStore } from '@/stores/outlineStore';
import ChapterRecapModal from '@/components/Chapter/ChapterRecapModal';
import AnalyzeModal from '@/components/Codex/AnalyzeModal';
import { BalanceWidget } from '@/components/Common';

interface EditorToolbarProps {
  manuscriptId?: string;
  chapterId?: string;
  chapterTitle?: string;
}

export default function EditorToolbar({ manuscriptId, chapterId, chapterTitle }: EditorToolbarProps = {}) {
  const [editor] = useLexicalComposerContext();
  const { outline, getCompletionPercentage, toggleOutlineReferenceSidebar, outlineReferenceSidebarOpen } = useOutlineStore();
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);
  const [blockType, setBlockType] = useState('paragraph');
  const [fontFamily, setFontFamily] = useState('EB Garamond');
  const [fontSize, setFontSize] = useState('16px');
  const [textAlign, setTextAlign] = useState('left');
  const [showRecapModal, setShowRecapModal] = useState(false);
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const [focusMode, setFocusMode] = useState(() => {
    const saved = localStorage.getItem('maxwell-focus-mode');
    return saved === 'true';
  });
  const [showFormatMenu, setShowFormatMenu] = useState(false);

  // Persist focus mode preference
  const toggleFocusMode = () => {
    const newMode = !focusMode;
    setFocusMode(newMode);
    localStorage.setItem('maxwell-focus-mode', String(newMode));
  };

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

  // Extract current editor text for analysis
  const getCurrentEditorText = (): string => {
    const editorState = editor.getEditorState();
    let text = '';

    editorState.read(() => {
      const root = editorState._nodeMap.get('root');
      if (root && '__cachedText' in root && typeof root.__cachedText === 'string') {
        text = root.__cachedText;
      } else {
        // Fallback: manually build text from all text nodes
        const allNodes = Array.from(editorState._nodeMap.values());
        text = allNodes
          .filter((node: any) => node.__type === 'text')
          .map((node: any) => node.__text || '')
          .join(' ');
      }
    });

    return text;
  };

  const handleAnalyzeClick = () => {
    if (!manuscriptId) {
      alert('No manuscript selected');
      return;
    }
    setShowAnalyzeModal(true);
  };

  // Focus mode: show minimal toolbar with just focus toggle and essential actions
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
          📝 Show Toolbar
        </ToolbarButton>
      </div>
    );
  }

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

      {/* Font family - expanded with writing-friendly fonts */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
        <select
          className="px-2 py-1 bg-white border border-slate-ui text-midnight text-sm font-sans max-w-[140px]"
          style={{ borderRadius: '2px' }}
          value={fontFamily}
          onChange={(e) => setFontFamily(e.target.value)}
        >
          <optgroup label="Serif (Traditional)">
            <option value="EB Garamond">EB Garamond</option>
            <option value="Georgia">Georgia</option>
            <option value="Times New Roman">Times New Roman</option>
            <option value="Palatino Linotype">Palatino</option>
            <option value="Baskerville">Baskerville</option>
            <option value="Cambria">Cambria</option>
          </optgroup>
          <optgroup label="Serif (Modern)">
            <option value="Merriweather">Merriweather</option>
            <option value="Lora">Lora</option>
            <option value="Libre Baskerville">Libre Baskerville</option>
            <option value="Crimson Text">Crimson Text</option>
          </optgroup>
          <optgroup label="Sans-Serif">
            <option value="Inter">Inter</option>
            <option value="Arial">Arial</option>
            <option value="Helvetica">Helvetica</option>
            <option value="Verdana">Verdana</option>
            <option value="Open Sans">Open Sans</option>
          </optgroup>
          <optgroup label="Monospace">
            <option value="Courier New">Courier New</option>
            <option value="Consolas">Consolas</option>
          </optgroup>
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

      {/* Paragraph formatting dropdown (alignment + lists) */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2 relative">
        <ToolbarButton
          onClick={() => setShowFormatMenu(!showFormatMenu)}
          title="Paragraph formatting"
        >
          ¶ Format
        </ToolbarButton>

        {showFormatMenu && (
          <div
            className="absolute top-full left-0 mt-1 bg-white border border-slate-ui shadow-lg rounded-sm z-50 py-1 min-w-[160px]"
            onMouseLeave={() => setShowFormatMenu(false)}
          >
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
              • Bullet List
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

      {/* Codex Analyze button */}
      {manuscriptId && (
        <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
          <ToolbarButton
            onClick={handleAnalyzeClick}
            title="Analyze manuscript text to detect characters, locations, items, and lore using NLP"
          >
            🔍 Analyze
          </ToolbarButton>
        </div>
      )}

      {/* Chapter Recap button */}
      {chapterId && (
        <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
          <ToolbarButton
            onClick={() => setShowRecapModal(true)}
            title="Generate an AI-powered chapter recap with themes, events, and character developments"
          >
            📖 Recap
          </ToolbarButton>
        </div>
      )}

      {/* Outline Reference Sidebar Toggle */}
      {outline && (
        <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2">
          <ToolbarButton
            onClick={toggleOutlineReferenceSidebar}
            active={outlineReferenceSidebarOpen}
            title={outlineReferenceSidebarOpen ? "Hide outline reference" : "Show outline reference while writing"}
          >
            📋 Outline {getCompletionPercentage()}%
          </ToolbarButton>
        </div>
      )}

      {/* AI Balance Widget */}
      <div className="toolbar-group flex gap-1 border-r border-slate-ui pr-2 mr-2 ml-auto">
        <BalanceWidget onOpenSettings={() => window.dispatchEvent(new CustomEvent('openSettings'))} />
      </div>

      {/* Focus Mode Toggle */}
      <div className="toolbar-group flex gap-1">
        <ToolbarButton
          onClick={toggleFocusMode}
          active={focusMode}
          title={focusMode ? "Exit focus mode (show full toolbar)" : "Enter focus mode (hide toolbar for distraction-free writing)"}
        >
          {focusMode ? '📝 Show Toolbar' : '🎯 Focus'}
        </ToolbarButton>
      </div>

      {/* Recap Modal */}
      {showRecapModal && chapterId && (
        <ChapterRecapModal
          chapterId={chapterId}
          chapterTitle={chapterTitle || 'Chapter'}
          onClose={() => setShowRecapModal(false)}
        />
      )}

      {/* Analyze Modal */}
      {showAnalyzeModal && manuscriptId && (
        <AnalyzeModal
          manuscriptId={manuscriptId}
          currentChapterContent={getCurrentEditorText()}
          onClose={() => setShowAnalyzeModal(false)}
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
