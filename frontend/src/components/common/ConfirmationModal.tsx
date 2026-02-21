/**
 * ConfirmationModal - Global confirmation dialog
 * Replaces browser confirm() with a styled modal
 */

import { useEffect } from 'react';
import { useConfirmStore } from '@/stores/confirmStore';

export default function ConfirmationModal() {
  const { isOpen, title, message, variant, confirmLabel, close } = useConfirmStore();

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, close]);

  if (!isOpen) return null;

  const confirmColor = variant === 'danger'
    ? 'bg-redline hover:bg-redline/90'
    : 'bg-bronze hover:bg-bronze-dark';

  return (
    <div className="fixed inset-0 bg-black/50 z-[300] flex items-center justify-center p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-md w-full overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-ui bg-white">
          <h2 className="font-garamond text-xl font-semibold text-midnight">{title}</h2>
        </div>
        <div className="px-6 py-5">
          <p className="font-sans text-sm text-midnight leading-relaxed">{message}</p>
        </div>
        <div className="px-6 py-4 border-t border-slate-ui bg-slate-ui/10 flex justify-end gap-3">
          <button
            onClick={() => close(false)}
            className="px-4 py-2 bg-slate-ui text-midnight font-sans text-sm font-medium hover:bg-slate-ui/80 transition-colors"
            style={{ borderRadius: '2px' }}
          >
            Cancel
          </button>
          <button
            onClick={() => close(true)}
            className={`px-4 py-2 ${confirmColor} text-white font-sans text-sm font-medium transition-colors`}
            style={{ borderRadius: '2px' }}
            autoFocus
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
