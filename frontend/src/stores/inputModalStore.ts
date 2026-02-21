/**
 * Input Modal Store - Global input/prompt modal system
 * Replaces browser prompt() with styled async modals
 */

import { create } from 'zustand';

export interface InputModalOptions {
  title: string;
  message?: string;
  placeholder?: string;
  defaultValue?: string;
  confirmLabel?: string;
  /** Use 'select' for a dropdown instead of text input */
  inputType?: 'text' | 'select';
  /** Options for select mode */
  selectOptions?: { label: string; value: string }[];
}

interface InputModalState {
  isOpen: boolean;
  title: string;
  message: string;
  placeholder: string;
  defaultValue: string;
  confirmLabel: string;
  inputType: 'text' | 'select';
  selectOptions: { label: string; value: string }[];
  resolve: ((value: string | null) => void) | null;
}

interface InputModalStore extends InputModalState {
  open: (options: InputModalOptions, resolve: (value: string | null) => void) => void;
  close: (result: string | null) => void;
}

export const useInputModalStore = create<InputModalStore>((set, get) => ({
  isOpen: false,
  title: '',
  message: '',
  placeholder: '',
  defaultValue: '',
  confirmLabel: 'OK',
  inputType: 'text',
  selectOptions: [],
  resolve: null,

  open: (options, resolve) =>
    set({
      isOpen: true,
      title: options.title,
      message: options.message ?? '',
      placeholder: options.placeholder ?? '',
      defaultValue: options.defaultValue ?? '',
      confirmLabel: options.confirmLabel ?? 'OK',
      inputType: options.inputType ?? 'text',
      selectOptions: options.selectOptions ?? [],
      resolve,
    }),

  close: (result) => {
    const { resolve } = get();
    resolve?.(result);
    set({ isOpen: false, resolve: null });
  },
}));

/** Show an input modal and return a promise that resolves to the entered string or null. */
export function promptInput(options: InputModalOptions): Promise<string | null> {
  return new Promise((resolve) => {
    useInputModalStore.getState().open(options, resolve);
  });
}
