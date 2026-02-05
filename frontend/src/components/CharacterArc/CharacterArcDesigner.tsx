/**
 * CharacterArcDesigner Component
 * Visual arc planning and tracking for characters
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  CharacterArc,
  ArcTemplate,
  ArcTemplateInfo,
  ArcStage,
  ArcComparison,
  ARC_TEMPLATE_INFO,
} from '../../types/characterArc';

const API_BASE = 'http://localhost:8000';

interface CharacterArcDesignerProps {
  characterWikiId: string;
  characterName: string;
  manuscriptId: string;
  onClose?: () => void;
}

export default function CharacterArcDesigner({
  characterWikiId,
  characterName,
  manuscriptId,
  onClose,
}: CharacterArcDesignerProps) {
  // State
  const [arc, setArc] = useState<CharacterArc | null>(null);
  const [templates, setTemplates] = useState<ArcTemplateInfo[]>([]);
  const [comparison, setComparison] = useState<ArcComparison | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'design' | 'compare' | 'timeline'>('design');
  const [selectedTemplate, setSelectedTemplate] = useState<ArcTemplate>('redemption');
  const [plannedArc, setPlannedArc] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  // Fetch arc and templates
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch templates
      const templatesRes = await fetch(`${API_BASE}/character-arcs/templates/all`);
      if (templatesRes.ok) {
        const templatesData = await templatesRes.json();
        setTemplates(templatesData);
      }

      // Fetch existing arc
      const arcRes = await fetch(
        `${API_BASE}/character-arcs/character/${characterWikiId}?manuscript_id=${manuscriptId}`
      );
      if (arcRes.ok) {
        const arcs = await arcRes.json();
        if (arcs.length > 0) {
          setArc(arcs[0]);
          setSelectedTemplate(arcs[0].arc_template as ArcTemplate);
          setPlannedArc(arcs[0].planned_arc || {});
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, [characterWikiId, manuscriptId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch comparison when arc exists
  useEffect(() => {
    if (arc && activeTab === 'compare') {
      fetchComparison();
    }
  }, [arc, activeTab]);

  const fetchComparison = async () => {
    if (!arc) return;

    try {
      const res = await fetch(`${API_BASE}/character-arcs/${arc.id}/compare`);
      if (res.ok) {
        const data = await res.json();
        setComparison(data);
      }
    } catch (err) {
      console.error('Failed to fetch comparison:', err);
    }
  };

  // Create or update arc
  const handleSaveArc = async () => {
    setIsSaving(true);
    setError(null);

    try {
      if (arc) {
        // Update existing
        const res = await fetch(`${API_BASE}/character-arcs/${arc.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            arc_template: selectedTemplate,
            planned_arc: plannedArc,
          }),
        });

        if (!res.ok) throw new Error('Failed to update arc');
        const updated = await res.json();
        setArc(updated);
      } else {
        // Create new
        const res = await fetch(`${API_BASE}/character-arcs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            wiki_entry_id: characterWikiId,
            manuscript_id: manuscriptId,
            arc_template: selectedTemplate,
            planned_arc: plannedArc,
          }),
        });

        if (!res.ok) throw new Error('Failed to create arc');
        const created = await res.json();
        setArc(created);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  // Get current template stages
  const getCurrentStages = (): ArcStage[] => {
    const template = templates.find((t) => t.id === selectedTemplate);
    return template?.stages || [];
  };

  // Get health color
  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'at_risk':
        return 'text-amber-600 bg-amber-100';
      case 'broken':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'matched':
        return 'bg-green-100 text-green-700 border-green-300';
      case 'missing':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'unexpected':
        return 'bg-amber-100 text-amber-700 border-amber-300';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-300';
    }
  };

  const stages = getCurrentStages();
  const templateInfo = templates.find((t) => t.id === selectedTemplate);

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-gray-500">Loading arc designer...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Character Arc: {characterName}
            </h2>
            {arc && (
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`px-2 py-0.5 text-xs rounded ${getHealthColor(
                    arc.arc_health
                  )}`}
                >
                  {arc.arc_health}
                </span>
                <span className="text-sm text-gray-500">
                  {Math.round(arc.arc_completion * 100)}% complete
                </span>
              </div>
            )}
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="px-6 border-b border-gray-200">
          <div className="flex gap-4">
            {(['design', 'compare', 'timeline'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  py-3 px-1 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                  }
                `}
              >
                {tab === 'design' && '📝 Design Arc'}
                {tab === 'compare' && '📊 Compare'}
                {tab === 'timeline' && '📅 Timeline'}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
              {error}
            </div>
          )}

          {activeTab === 'design' && (
            <div className="space-y-6">
              {/* Template Selection */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Arc Template
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {templates.map((template) => {
                    const info = ARC_TEMPLATE_INFO[template.id as ArcTemplate];
                    return (
                      <button
                        key={template.id}
                        onClick={() => {
                          setSelectedTemplate(template.id as ArcTemplate);
                          setPlannedArc({});
                        }}
                        className={`
                          p-3 rounded-lg border text-left transition-all
                          ${selectedTemplate === template.id
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                            : 'border-gray-200 hover:border-gray-300'
                          }
                        `}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{info?.icon || '📈'}</span>
                          <span className="font-medium text-gray-800">
                            {template.name}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">
                          {template.description}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {template.stage_count} stages
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Stage Planning */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Plan Arc Stages
                </h3>
                <div className="space-y-4">
                  {stages.map((stage, index) => (
                    <div
                      key={stage.id}
                      className="flex gap-4 items-start p-4 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-800 mb-1">
                          {stage.name}
                        </div>
                        <p className="text-sm text-gray-500 mb-2">
                          {stage.description}
                        </p>
                        <textarea
                          value={plannedArc[stage.id] || ''}
                          onChange={(e) =>
                            setPlannedArc({
                              ...plannedArc,
                              [stage.id]: e.target.value,
                            })
                          }
                          placeholder={`Describe how ${characterName} will experience this stage...`}
                          rows={2}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'compare' && (
            <div className="space-y-6">
              {!arc ? (
                <div className="text-center py-8 text-gray-500">
                  Save an arc first to compare planned vs detected
                </div>
              ) : !comparison ? (
                <div className="text-center py-8 text-gray-500">
                  Loading comparison...
                </div>
              ) : (
                <>
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-gray-800">
                        {comparison.matched_stages}
                      </div>
                      <div className="text-sm text-gray-500">Matched</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-gray-800">
                        {comparison.total_planned_stages}
                      </div>
                      <div className="text-sm text-gray-500">Planned</div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div
                        className={`text-2xl font-bold ${
                          comparison.health === 'healthy'
                            ? 'text-green-600'
                            : comparison.health === 'at_risk'
                            ? 'text-amber-600'
                            : 'text-red-600'
                        }`}
                      >
                        {comparison.health}
                      </div>
                      <div className="text-sm text-gray-500">Health</div>
                    </div>
                  </div>

                  {/* Stage Comparison */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      Stage Comparison
                    </h3>
                    <div className="space-y-2">
                      {comparison.comparison.map((stage) => (
                        <div
                          key={stage.stage_id}
                          className={`
                            p-3 rounded-lg border
                            ${getStatusColor(stage.status)}
                          `}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{stage.stage_name}</span>
                            <span className="text-xs uppercase">
                              {stage.status}
                            </span>
                          </div>
                          {stage.planned && (
                            <p className="text-sm mt-1 opacity-75">
                              Planned: {stage.planned}
                            </p>
                          )}
                          {stage.detected && (
                            <p className="text-sm mt-1">
                              Detected ({Math.round(stage.detection_confidence * 100)}%
                              confidence)
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Deviations */}
                  {comparison.deviations.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-3">
                        ⚠️ Deviations
                      </h3>
                      <div className="space-y-2">
                        {comparison.deviations.map((dev, i) => (
                          <div
                            key={i}
                            className="p-3 bg-amber-50 border border-amber-200 rounded"
                          >
                            <div className="font-medium text-amber-800">
                              {dev.stage_name}
                            </div>
                            <p className="text-sm text-amber-700">{dev.issue}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="space-y-6">
              {!arc ? (
                <div className="text-center py-8 text-gray-500">
                  Save an arc first to view timeline
                </div>
              ) : (
                <>
                  {/* Visual Timeline */}
                  <div className="relative">
                    <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                    <div className="space-y-4">
                      {stages.map((stage, index) => {
                        const beat = arc.arc_beats.find(
                          (b) => b.arc_stage === stage.id
                        );
                        const isCompleted = beat?.is_detected || beat?.is_planned;

                        return (
                          <div key={stage.id} className="relative flex gap-4 pl-8">
                            <div
                              className={`
                                absolute left-2.5 w-3 h-3 rounded-full border-2
                                ${isCompleted
                                  ? 'bg-green-500 border-green-500'
                                  : 'bg-white border-gray-300'
                                }
                              `}
                            />
                            <div
                              className={`
                                flex-1 p-3 rounded-lg border
                                ${isCompleted
                                  ? 'bg-green-50 border-green-200'
                                  : 'bg-gray-50 border-gray-200'
                                }
                              `}
                            >
                              <div className="font-medium text-gray-800">
                                {index + 1}. {stage.name}
                              </div>
                              {beat?.description && (
                                <p className="text-sm text-gray-600 mt-1">
                                  {beat.description}
                                </p>
                              )}
                              {!isCompleted && (
                                <p className="text-xs text-gray-400 mt-1">
                                  Not yet reached
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {arc ? 'Last updated: ' + new Date(arc.updated_at || arc.created_at).toLocaleDateString() : 'No arc created yet'}
          </div>
          <div className="flex items-center gap-3">
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Close
              </button>
            )}
            <button
              onClick={handleSaveArc}
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : arc ? 'Update Arc' : 'Create Arc'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
