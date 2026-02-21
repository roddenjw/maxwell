/**
 * InputModal - Global input/prompt dialog
 * Replaces browser prompt() with a styled modal
 */

import { useState, useEffect, useRef } from 'react';
import { useInputModalStore } from '@/stores/inputModalStore';

export default function InputModal() {
  const { isOpen, title, message, placeholder, defaultValue, confirmLabel, inputType, selectOptions, close } = useInputModalStore();
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const selectRef = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    if (isOpen) {
      setValue(defaultValue || (inputType === 'select' && selectOptions.length > 0 ? selectOptions[0].value : ''));
      // Focus after render
      requestAnimationFrame(() => {
        if (inputType === 'select') {
          selectRef.current?.focus();
        } else {
          inputRef.current?.focus();
          inputRef.current?.select();
        }
      });
    }
  }, [isOpen, defaultValue, inputType, selectOptions]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close(null);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, close]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    close(value);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-[300] flex items-center justify-center p-4">
      <div className="bg-vellum rounded-sm shadow-2xl max-w-md w-full overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-ui bg-white">
          <h2 className="font-garamond text-xl font-semibold text-midnight">{title}</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-5">
            {message && (
              <p className="font-sans text-sm text-midnight leading-relaxed mb-3">{message}</p>
            )}
            {inputType === 'select' ? (
              <select
                ref={selectRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
              >
                {selectOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                ref={inputRef}
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={placeholder}
                className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans"
                style={{ borderRadius: '2px' }}
              />
            )}
          </div>
          <div className="px-6 py-4 border-t border-slate-ui bg-slate-ui/10 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => close(null)}
              className="px-4 py-2 bg-slate-ui text-midnight font-sans text-sm font-medium hover:bg-slate-ui/80 transition-colors"
              style={{ borderRadius: '2px' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-bronze hover:bg-bronze-dark text-white font-sans text-sm font-medium transition-colors"
              style={{ borderRadius: '2px' }}
            >
              {confirmLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
