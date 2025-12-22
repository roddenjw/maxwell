/**
 * Diff Viewer - Shows differences between two versions
 */

interface DiffViewerProps {
  diffHtml: string;
  oldLabel: string;
  newLabel: string;
  onClose: () => void;
}

export default function DiffViewer({
  diffHtml,
  oldLabel,
  newLabel,
  onClose,
}: DiffViewerProps) {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-garamond font-bold text-midnight">Version Comparison</h3>
          <p className="text-sm text-faded-ink font-sans mt-1">
            {oldLabel} → {newLabel}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-faded-ink hover:text-midnight transition-colors font-sans text-sm"
        >
          Close Diff
        </button>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-sm font-sans">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 border border-green-300 rounded" />
          <span className="text-faded-ink">Added</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-100 border border-red-300 rounded" />
          <span className="text-faded-ink">Removed</span>
        </div>
      </div>

      {/* Diff Content */}
      <div className="bg-white rounded-lg border border-slate-ui p-6 overflow-x-auto">
        <div
          className="diff-content font-mono text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: diffHtml }}
          style={{
            wordBreak: 'break-word',
          }}
        />
      </div>

      {/* Diff styles */}
      <style>{`
        .diff-content {
          white-space: pre-wrap;
        }

        .diff-content ins {
          background-color: #dcfce7;
          border: 1px solid #86efac;
          text-decoration: none;
          padding: 0 2px;
          border-radius: 2px;
        }

        .diff-content del {
          background-color: #fee2e2;
          border: 1px solid #fca5a5;
          text-decoration: line-through;
          padding: 0 2px;
          border-radius: 2px;
        }

        .diff-content mark {
          background-color: #fef3c7;
          border: 1px solid #fcd34d;
          padding: 0 2px;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
}
