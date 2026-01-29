/**
 * EntityPickerModal - Modal for selecting a Codex entity to link
 */

import { useState, useEffect } from 'react';
import { codexApi } from '@/lib/api';
import type { Entity } from '@/types/codex';
import { getEntityTypeIcon } from '@/types/codex';
import { toast } from '@/stores/toastStore';
import { getErrorMessage } from '@/lib/retry';

interface EntityPickerModalProps {
  manuscriptId: string;
  entityType?: string; // Filter by type (e.g., 'CHARACTER')
  title?: string;
  onSelect: (entity: Entity) => void;
  onCancel: () => void;
}

export default function EntityPickerModal({
  manuscriptId,
  entityType = 'CHARACTER',
  title = 'Select Entity',
  onSelect,
  onCancel,
}: EntityPickerModalProps) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const loadEntities = async () => {
      try {
        setLoading(true);
        const data = await codexApi.listEntities(manuscriptId, entityType);
        setEntities(data);
      } catch (err) {
        toast.error(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadEntities();
  }, [manuscriptId, entityType]);

  const filteredEntities = entities.filter((entity) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      entity.name.toLowerCase().includes(query) ||
      entity.aliases.some((alias) => alias.toLowerCase().includes(query))
    );
  });

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-ui flex items-center justify-between">
          <h2 className="font-garamond text-xl font-semibold text-midnight">{title}</h2>
          <button
            onClick={onCancel}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Search */}
        <div className="px-6 py-3 border-b border-slate-ui">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or alias..."
            className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze"
            autoFocus
          />
        </div>

        {/* Entity List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-faded-ink">Loading entities...</div>
            </div>
          ) : filteredEntities.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-3">📭</div>
              <p className="text-sm text-faded-ink">
                {searchQuery
                  ? 'No matching entities found'
                  : `No ${entityType.toLowerCase()}s in Codex yet`}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredEntities.map((entity) => (
                <button
                  key={entity.id}
                  onClick={() => onSelect(entity)}
                  className="w-full text-left p-3 border border-slate-ui rounded-sm hover:border-bronze hover:bg-bronze/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{getEntityTypeIcon(entity.type)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-midnight truncate">
                        {entity.name}
                      </div>
                      {entity.aliases.length > 0 && (
                        <div className="text-xs text-faded-ink truncate">
                          aka {entity.aliases.slice(0, 3).join(', ')}
                          {entity.aliases.length > 3 && '...'}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-ui bg-slate-ui/10">
          <button
            onClick={onCancel}
            className="w-full px-4 py-2 text-sm font-sans bg-slate-ui text-midnight hover:bg-slate-ui/80 rounded-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
