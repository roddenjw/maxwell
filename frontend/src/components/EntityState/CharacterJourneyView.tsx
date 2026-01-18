/**
 * CharacterJourneyView Component
 * Visualizes a character's journey through the narrative with state changes
 */

import React, { useEffect, useState } from 'react';
import { entityStateApi } from '@/lib/api';
import { useEntityStateStore } from '@/stores/entityStateStore';
import type { StateChange } from '@/types/entityState';

interface CharacterJourneyViewProps {
  entityId: string;
  entityName: string;
  manuscriptId?: string;
}

const CharacterJourneyView: React.FC<CharacterJourneyViewProps> = ({
  entityId,
  entityName,
  manuscriptId,
}) => {
  const { journeysByEntity, setEntityJourney, isLoading, setLoading, error, setError } =
    useEntityStateStore();

  const journey = journeysByEntity[entityId] || [];
  const [expandedPoints, setExpandedPoints] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchJourney = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await entityStateApi.getCharacterJourney(entityId, manuscriptId);
        setEntityJourney(entityId, data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load character journey');
      } finally {
        setLoading(false);
      }
    };

    fetchJourney();
  }, [entityId, manuscriptId, setEntityJourney, setLoading, setError]);

  const toggleExpand = (stateId: string) => {
    const newExpanded = new Set(expandedPoints);
    if (newExpanded.has(stateId)) {
      newExpanded.delete(stateId);
    } else {
      newExpanded.add(stateId);
    }
    setExpandedPoints(newExpanded);
  };

  const renderChange = (key: string, change: StateChange) => {
    const getChangeIcon = () => {
      switch (change.type) {
        case 'added':
          return <span className="text-green-600">+</span>;
        case 'removed':
          return <span className="text-red-600">-</span>;
        case 'changed':
          return <span className="text-amber-600">~</span>;
        default:
          return null;
      }
    };

    const getChangeDescription = () => {
      switch (change.type) {
        case 'added':
          return (
            <span className="text-green-700">
              {key}: <strong>{String(change.value)}</strong>
            </span>
          );
        case 'removed':
          return (
            <span className="text-red-700 line-through">
              {key}: {String(change.value)}
            </span>
          );
        case 'changed':
          return (
            <span className="text-amber-700">
              {key}: {String(change.from)} &rarr; <strong>{String(change.to)}</strong>
            </span>
          );
        default:
          return null;
      }
    };

    return (
      <div key={key} className="flex items-center gap-2 text-sm">
        {getChangeIcon()}
        {getChangeDescription()}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bronze-600"></div>
        <span className="ml-3 text-midnight-600">Loading character journey...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        {error}
      </div>
    );
  }

  if (journey.length === 0) {
    return (
      <div className="text-center py-8 text-midnight-500 bg-vellum-50 rounded-lg border border-vellum-200">
        <p>No journey data available.</p>
        <p className="text-sm mt-1">
          Add state snapshots to track {entityName}'s journey through your story.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-midnight-800">
        {entityName}'s Journey
      </h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-bronze-400 via-bronze-300 to-bronze-200"></div>

        <div className="space-y-6">
          {journey.map((point, index) => {
            const isExpanded = expandedPoints.has(point.state_id);
            const hasChanges = point.changes && Object.keys(point.changes).length > 0;

            return (
              <div key={point.state_id} className="relative pl-14">
                {/* Journey marker */}
                <div
                  className={`absolute left-3 top-2 w-7 h-7 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                    hasChanges ? 'bg-bronze-600' : 'bg-bronze-400'
                  }`}
                >
                  {index + 1}
                </div>

                <div
                  className={`p-4 rounded-lg border transition-all ${
                    hasChanges
                      ? 'border-bronze-300 bg-white shadow-sm'
                      : 'border-vellum-200 bg-vellum-50'
                  }`}
                >
                  {/* Point header */}
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => toggleExpand(point.state_id)}
                  >
                    <div>
                      <h4 className="font-medium text-midnight-800">
                        {point.label || `Point ${index + 1}`}
                      </h4>
                      {point.narrative_timestamp && (
                        <p className="text-sm text-bronze-600">{point.narrative_timestamp}</p>
                      )}
                    </div>
                    <button className="text-midnight-400 hover:text-midnight-600">
                      {isExpanded ? (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </button>
                  </div>

                  {/* Changes summary */}
                  {hasChanges && !isExpanded && (
                    <div className="mt-2 text-sm text-midnight-600">
                      {Object.keys(point.changes!).length} change(s) at this point
                    </div>
                  )}

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="mt-4 space-y-4">
                      {/* Changes */}
                      {hasChanges && (
                        <div className="p-3 bg-vellum-50 rounded-md">
                          <h5 className="text-sm font-medium text-midnight-700 mb-2">Changes:</h5>
                          <div className="space-y-1">
                            {Object.entries(point.changes!).map(([key, change]) =>
                              renderChange(key, change)
                            )}
                          </div>
                        </div>
                      )}

                      {/* Current state */}
                      <div className="p-3 bg-white border border-vellum-200 rounded-md">
                        <h5 className="text-sm font-medium text-midnight-700 mb-2">State at this point:</h5>
                        <div className="space-y-1 text-sm">
                          {Object.entries(point.state_data).map(([key, value]) => (
                            <div key={key} className="flex gap-2">
                              <span className="text-midnight-500 capitalize">
                                {key.replace(/_/g, ' ')}:
                              </span>
                              <span className="text-midnight-700">
                                {typeof value === 'object'
                                  ? JSON.stringify(value)
                                  : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CharacterJourneyView;
