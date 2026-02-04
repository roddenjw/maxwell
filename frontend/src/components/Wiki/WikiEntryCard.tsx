/**
 * WikiEntryCard Component
 * Displays a wiki entry as a card or list item
 */

import type { WikiEntry } from '../../types/wiki';
import { WIKI_ENTRY_TYPE_INFO } from '../../types/wiki';

interface WikiEntryCardProps {
  entry: WikiEntry;
  viewMode: 'list' | 'grid';
  isSelected: boolean;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function WikiEntryCard({
  entry,
  viewMode,
  isSelected,
  onClick,
  onEdit,
  onDelete,
}: WikiEntryCardProps) {
  const typeInfo = WIKI_ENTRY_TYPE_INFO[entry.entry_type] || {
    label: entry.entry_type,
    icon: '📄',
    color: 'text-gray-600',
    category: 'Other',
  };

  if (viewMode === 'grid') {
    return (
      <div
        onClick={onClick}
        className={`
          p-4 rounded-lg border cursor-pointer transition-all
          ${isSelected
            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
          }
        `}
      >
        <div className="flex items-start justify-between mb-2">
          <span className="text-2xl">{typeInfo.icon}</span>
          <div className="flex items-center gap-1">
            {entry.confidence_score < 1 && (
              <span className="text-xs text-amber-600" title="AI-generated">
                🤖
              </span>
            )}
            {entry.status === 'draft' && (
              <span className="text-xs text-gray-400">Draft</span>
            )}
          </div>
        </div>
        <h3 className="font-medium text-gray-800 truncate">{entry.title}</h3>
        <p className="text-xs text-gray-500 mt-1 capitalize">
          {entry.entry_type.replace(/_/g, ' ')}
        </p>
        {entry.summary && (
          <p className="text-sm text-gray-600 mt-2 line-clamp-2">{entry.summary}</p>
        )}
        {entry.tags && entry.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {entry.tags.slice(0, 3).map((tag, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded"
              >
                {tag}
              </span>
            ))}
            {entry.tags.length > 3 && (
              <span className="text-xs text-gray-400">+{entry.tags.length - 3}</span>
            )}
          </div>
        )}
        <div
          className="flex items-center justify-end gap-2 mt-3 pt-3 border-t border-gray-100"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onEdit}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="text-xs text-red-500 hover:text-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    );
  }

  // List view
  return (
    <div
      onClick={onClick}
      className={`
        flex items-center gap-4 p-3 rounded-lg border cursor-pointer transition-all
        ${isSelected
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
      `}
    >
      <span className="text-xl">{typeInfo.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-800 truncate">{entry.title}</h3>
          {entry.confidence_score < 1 && (
            <span className="text-xs text-amber-600" title="AI-generated">
              🤖
            </span>
          )}
          {entry.status === 'draft' && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
              Draft
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={`text-xs ${typeInfo.color}`}>
            {typeInfo.label}
          </span>
          {entry.aliases && entry.aliases.length > 0 && (
            <span className="text-xs text-gray-400">
              aka {entry.aliases[0]}
              {entry.aliases.length > 1 && ` +${entry.aliases.length - 1}`}
            </span>
          )}
        </div>
      </div>
      <div
        className="flex items-center gap-2"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onEdit}
          className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
        >
          Edit
        </button>
        <button
          onClick={onDelete}
          className="px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
