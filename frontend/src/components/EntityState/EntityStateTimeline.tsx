/**
 * EntityStateTimeline Component
 * Visual timeline showing how an entity changes across narrative points
 */

import React, { useEffect } from 'react';
import { entityStateApi } from '@/lib/api';
import { useEntityStateStore } from '@/stores/entityStateStore';
import StateSnapshotCard from './StateSnapshotCard';

interface EntityStateTimelineProps {
  entityId: string;
  entityName: string;
  manuscriptId?: string;
  onAddSnapshot?: () => void;
}

const EntityStateTimeline: React.FC<EntityStateTimelineProps> = ({
  entityId,
  entityName,
  manuscriptId,
  onAddSnapshot,
}) => {
  const {
    statesByEntity,
    setEntityStates,
    selectedStateId,
    setSelectedState,
    isLoading,
    setLoading,
    error,
    setError,
  } = useEntityStateStore();

  const states = statesByEntity[entityId] || [];

  useEffect(() => {
    const fetchStates = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await entityStateApi.listEntityStates(entityId, manuscriptId);
        setEntityStates(entityId, data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load entity states');
      } finally {
        setLoading(false);
      }
    };

    fetchStates();
  }, [entityId, manuscriptId, setEntityStates, setLoading, setError]);

  const handleSelectState = (stateId: string) => {
    setSelectedState(selectedStateId === stateId ? null : stateId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bronze-600"></div>
        <span className="ml-3 text-midnight-600">Loading state timeline...</span>
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-midnight-800">
          {entityName}'s Timeline
        </h3>
        {onAddSnapshot && (
          <button
            onClick={onAddSnapshot}
            className="px-3 py-1.5 text-sm bg-bronze-600 text-white rounded-md hover:bg-bronze-700 transition-colors"
          >
            + Add State Snapshot
          </button>
        )}
      </div>

      {states.length === 0 ? (
        <div className="text-center py-8 text-midnight-500 bg-vellum-50 rounded-lg border border-vellum-200">
          <p>No state snapshots yet.</p>
          <p className="text-sm mt-1">
            Track how {entityName} changes throughout your story.
          </p>
          {onAddSnapshot && (
            <button
              onClick={onAddSnapshot}
              className="mt-4 px-4 py-2 text-sm bg-bronze-100 text-bronze-700 rounded-md hover:bg-bronze-200 transition-colors"
            >
              Create First Snapshot
            </button>
          )}
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-bronze-200"></div>

          {/* Timeline points */}
          <div className="space-y-4">
            {states.map((state, index) => (
              <div key={state.id} className="relative pl-10">
                {/* Timeline dot */}
                <div
                  className={`absolute left-2 top-4 w-5 h-5 rounded-full border-2 cursor-pointer transition-colors ${
                    selectedStateId === state.id
                      ? 'bg-bronze-600 border-bronze-600'
                      : 'bg-white border-bronze-400 hover:border-bronze-600'
                  }`}
                  onClick={() => handleSelectState(state.id)}
                >
                  <span className="absolute -left-1 -top-1 w-7 h-7 flex items-center justify-center text-xs font-bold text-bronze-600">
                    {index + 1}
                  </span>
                </div>

                <StateSnapshotCard
                  state={state}
                  isSelected={selectedStateId === state.id}
                  onClick={() => handleSelectState(state.id)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityStateTimeline;
