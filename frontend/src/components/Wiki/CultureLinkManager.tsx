/**
 * CultureLinkManager Component
 * Modal/panel for managing culture-entity links with relationship types.
 */

import { useState, useEffect } from 'react';
import { cultureApi } from '../../lib/api';
import {
  WIKI_REFERENCE_TYPE_INFO,
  CULTURE_REFERENCE_TYPES,
  type WikiReferenceType,
} from '../../types/wiki';

interface CultureLink {
  reference_id: string;
  culture_id: string;
  culture_title: string;
  reference_type: string;
  context: string | null;
  direction: string;
  structured_data: Record<string, any>;
}

interface CultureOption {
  id: string;
  title: string;
  summary: string | null;
  member_count: number;
}

interface CultureLinkManagerProps {
  entryId: string;
  worldId: string;
  entryTitle: string;
  onClose: () => void;
  onLinksChanged?: () => void;
}

export function CultureLinkManager({
  entryId,
  worldId,
  entryTitle,
  onClose,
  onLinksChanged,
}: CultureLinkManagerProps) {
  const [cultures, setCultures] = useState<CultureOption[]>([]);
  const [links, setLinks] = useState<CultureLink[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedCultureId, setSelectedCultureId] = useState('');
  const [selectedRefType, setSelectedRefType] = useState<string>('born_in');
  const [contextText, setContextText] = useState('');

  useEffect(() => {
    loadData();
  }, [entryId, worldId]);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [culturesData, linksData] = await Promise.all([
        cultureApi.getWorldCultures(worldId),
        cultureApi.getEntityCultures(entryId),
      ]);
      setCultures(culturesData);
      setLinks(linksData);
    } catch (err: any) {
      setError(err.message || 'Failed to load culture data');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAddLink() {
    if (!selectedCultureId || !selectedRefType) return;

    setIsSaving(true);
    setError(null);
    try {
      await cultureApi.linkEntityToCulture({
        entity_entry_id: entryId,
        culture_entry_id: selectedCultureId,
        reference_type: selectedRefType,
        context: contextText || undefined,
      });
      // Reload links
      const linksData = await cultureApi.getEntityCultures(entryId);
      setLinks(linksData);
      // Reset form
      setSelectedCultureId('');
      setSelectedRefType('born_in');
      setContextText('');
      onLinksChanged?.();
    } catch (err: any) {
      setError(err.message || 'Failed to create culture link');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemoveLink(referenceId: string) {
    try {
      await cultureApi.unlinkEntityFromCulture(referenceId);
      setLinks(links.filter(l => l.reference_id !== referenceId));
      onLinksChanged?.();
    } catch (err: any) {
      setError(err.message || 'Failed to remove culture link');
    }
  }

  // Filter out cultures that are the entity itself
  const availableCultures = cultures.filter(c => c.id !== entryId);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                Culture Links
              </h2>
              <p className="text-sm text-gray-500 mt-0.5">
                Link "{entryTitle}" to cultures
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-blue-500" />
            </div>
          ) : (
            <>
              {/* Existing Links */}
              {links.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Current Culture Links
                  </h3>
                  <div className="space-y-2">
                    {links.map(link => {
                      const refInfo = WIKI_REFERENCE_TYPE_INFO[link.reference_type as WikiReferenceType];
                      return (
                        <div
                          key={link.reference_id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-lg">🎭</span>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-medium text-gray-800 text-sm truncate">
                                  {link.culture_title}
                                </span>
                                <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full font-medium">
                                  {refInfo?.label || link.reference_type.replace(/_/g, ' ')}
                                </span>
                              </div>
                              {link.context && (
                                <p className="text-xs text-gray-500 mt-0.5 truncate">
                                  {link.context}
                                </p>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleRemoveLink(link.reference_id)}
                            className="ml-2 p-1 text-gray-400 hover:text-red-500 flex-shrink-0"
                            title="Remove link"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Add New Link Form */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-700">
                  Add Culture Link
                </h3>

                {availableCultures.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">
                    No cultures found in this world. Create a culture entry in the Wiki first.
                  </p>
                ) : (
                  <>
                    {/* Culture Select */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Culture</label>
                      <select
                        value={selectedCultureId}
                        onChange={(e) => setSelectedCultureId(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
                      >
                        <option value="">Select a culture...</option>
                        {availableCultures.map(c => (
                          <option key={c.id} value={c.id}>
                            {c.title} ({c.member_count} members)
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Relationship Type Select */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Relationship</label>
                      <select
                        value={selectedRefType}
                        onChange={(e) => setSelectedRefType(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
                      >
                        {CULTURE_REFERENCE_TYPES.map(rt => {
                          const info = WIKI_REFERENCE_TYPE_INFO[rt];
                          return (
                            <option key={rt} value={rt}>
                              {info?.label || rt.replace(/_/g, ' ')}
                            </option>
                          );
                        })}
                      </select>
                    </div>

                    {/* Context */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Context (optional)</label>
                      <input
                        type="text"
                        value={contextText}
                        onChange={(e) => setContextText(e.target.value)}
                        placeholder="e.g., 'Exiled after the rebellion of 1042'"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
                      />
                    </div>

                    {/* Submit */}
                    <button
                      onClick={handleAddLink}
                      disabled={!selectedCultureId || isSaving}
                      className="w-full px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isSaving ? 'Linking...' : 'Link to Culture'}
                    </button>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
