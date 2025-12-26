/**
 * ToastContainer - Displays toast notifications
 * Beautiful Maxwell-styled notifications
 */

import { useToastStore, type Toast, type ToastType } from '@/stores/toastStore';

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-500 text-green-900';
      case 'error':
        return 'bg-red-50 border-red-500 text-red-900';
      case 'warning':
        return 'bg-yellow-50 border-yellow-500 text-yellow-900';
      case 'info':
        return 'bg-blue-50 border-blue-500 text-blue-900';
      default:
        return 'bg-slate-ui border-midnight text-midnight';
    }
  };

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return '•';
    }
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-md">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
          getStyles={getToastStyles}
          getIcon={getToastIcon}
        />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onClose: () => void;
  getStyles: (type: ToastType) => string;
  getIcon: (type: ToastType) => string;
}

function ToastItem({ toast, onClose, getStyles, getIcon }: ToastItemProps) {
  const handleAction = () => {
    if (toast.action) {
      toast.action.onClick();
      onClose(); // Close toast after action
    }
  };

  return (
    <div
      className={`
        ${getStyles(toast.type)}
        border-l-4 px-4 py-3 shadow-lg rounded-sm
        flex flex-col gap-2
        animate-slide-in-right
        font-sans text-sm
      `}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <span className="text-lg font-bold mt-0.5">{getIcon(toast.type)}</span>
        <p className="flex-1">{toast.message}</p>
        <button
          onClick={onClose}
          className="text-lg leading-none opacity-60 hover:opacity-100 transition-opacity"
          aria-label="Close notification"
        >
          ×
        </button>
      </div>

      {/* Action button */}
      {toast.action && (
        <button
          onClick={handleAction}
          className="ml-8 px-3 py-1.5 bg-bronze text-white font-sans text-xs rounded hover:bg-bronze/90 transition-colors self-start"
        >
          {toast.action.label}
        </button>
      )}
    </div>
  );
}
