/**
 * Toast Store - Notification system
 * Manages toast notifications across the app
 */

import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
  action?: ToastAction;
  data?: any; // Additional data for the action
}

interface ToastStore {
  toasts: Toast[];
  addToast: (message: string, type: ToastType, options?: { duration?: number; action?: ToastAction; data?: any }) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  addToast: (message, type, options = {}) => {
    const { duration = 5000, action, data } = options;
    const id = `toast-${Date.now()}-${Math.random()}`;
    const toast: Toast = { id, message, type, duration, action, data };

    set((state) => ({
      toasts: [...state.toasts, toast],
    }));

    // Auto-remove after duration (longer if there's an action)
    const autoRemoveDuration = action ? duration * 2 : duration;
    if (autoRemoveDuration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, autoRemoveDuration);
    }
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  clearAll: () => set({ toasts: [] }),
}));

// Convenience functions
export const toast = {
  success: (message: string, options?: { duration?: number; action?: ToastAction; data?: any }) =>
    useToastStore.getState().addToast(message, 'success', options),
  error: (message: string, options?: { duration?: number; action?: ToastAction; data?: any }) =>
    useToastStore.getState().addToast(message, 'error', options),
  info: (message: string, options?: { duration?: number; action?: ToastAction; data?: any }) =>
    useToastStore.getState().addToast(message, 'info', options),
  warning: (message: string, options?: { duration?: number; action?: ToastAction; data?: any }) =>
    useToastStore.getState().addToast(message, 'warning', options),
};
