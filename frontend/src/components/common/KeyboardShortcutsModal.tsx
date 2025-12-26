/**
 * KeyboardShortcutsModal - Shows available keyboard shortcuts
 * Maxwell-styled help modal
 */

import { formatShortcut, type KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';

interface KeyboardShortcutsModalProps {
  shortcuts: KeyboardShortcut[];
  onClose: () => void;
}

export default function KeyboardShortcutsModal({ shortcuts, onClose }: KeyboardShortcutsModalProps) {
  // Group shortcuts by category
  const grouped = {
    'General': shortcuts.filter(s =>
      s.description.includes('shortcuts') ||
      s.description.includes('Save')
    ),
    'Navigation': shortcuts.filter(s =>
      s.description.includes('chapter') ||
      s.description.includes('sidebar') ||
      s.description.includes('timeline')
    ),
    'Editing': shortcuts.filter(s =>
      s.description.includes('New') ||
      s.description.includes('snapshot') ||
      s.description.includes('Focus')
    ),
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-[200] flex items-center justify-center p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui bg-white">
          <div className="flex items-center justify-between">
            <h2 className="font-garamond text-2xl font-semibold text-midnight">
              Keyboard Shortcuts
            </h2>
            <button
              onClick={onClose}
              className="text-faded-ink hover:text-midnight transition-colors text-2xl leading-none"
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
          {Object.entries(grouped).map(([category, categoryShortcuts]) => {
            if (categoryShortcuts.length === 0) return null;

            return (
              <div key={category} className="mb-6 last:mb-0">
                <h3 className="font-sans text-sm font-semibold text-bronze mb-3 uppercase tracking-wide">
                  {category}
                </h3>
                <div className="space-y-2">
                  {categoryShortcuts.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 px-3 hover:bg-slate-ui/20 rounded-sm transition-colors"
                    >
                      <span className="font-sans text-sm text-midnight">
                        {shortcut.description}
                      </span>
                      <kbd className="px-3 py-1 bg-white border border-slate-ui rounded-sm font-mono text-xs text-faded-ink shadow-sm">
                        {formatShortcut(shortcut)}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-ui bg-slate-ui/10">
          <p className="text-xs text-faded-ink font-sans text-center">
            Press <kbd className="px-2 py-0.5 bg-white border border-slate-ui rounded-sm font-mono">Esc</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );
}
