/**
 * Confirm Store - Global confirmation modal system
 * Replaces browser confirm() with styled async modals
 */

import { create } from 'zustand';

export interface ConfirmOptions {
  title: string;
  message: string;
  variant?: 'danger' | 'warning' | 'info';
  confirmLabel?: string;
}

interface ConfirmState {
  isOpen: boolean;
  title: string;
  message: string;
  variant: 'danger' | 'warning' | 'info';
  confirmLabel: string;
  resolve: ((value: boolean) => void) | null;
}

interface ConfirmStore extends ConfirmState {
  open: (options: ConfirmOptions, resolve: (value: boolean) => void) => void;
  close: (result: boolean) => void;
}

export const useConfirmStore = create<ConfirmStore>((set, get) => ({
  isOpen: false,
  title: '',
  message: '',
  variant: 'info',
  confirmLabel: 'Confirm',
  resolve: null,

  open: (options, resolve) =>
    set({
      isOpen: true,
      title: options.title,
      message: options.message,
      variant: options.variant ?? 'info',
      confirmLabel: options.confirmLabel ?? 'Confirm',
      resolve,
    }),

  close: (result) => {
    const { resolve } = get();
    resolve?.(result);
    set({ isOpen: false, resolve: null });
  },
}));

/** Show a confirmation modal and return a promise that resolves to true/false. */
export function confirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    useConfirmStore.getState().open(options, resolve);
  });
}
