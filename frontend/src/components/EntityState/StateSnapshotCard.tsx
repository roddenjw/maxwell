/**
 * StateSnapshotCard Component
 * Displays a single entity state snapshot with its data
 */

import React from 'react';
import type { EntityTimelineState } from '@/types/entityState';

interface StateSnapshotCardProps {
  state: EntityTimelineState;
  isSelected?: boolean;
  onClick?: () => void;
  showFullDetails?: boolean;
}

const StateSnapshotCard: React.FC<StateSnapshotCardProps> = ({
  state,
  isSelected = false,
  onClick,
  showFullDetails = false,
}) => {
  const { state_data, label, narrative_timestamp, is_canonical, created_at } = state;

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const renderStateValue = (_key: string, value: unknown): React.ReactNode => {
    if (value === null || value === undefined) return <span className="text-midnight-400">-</span>;

    if (Array.isArray(value)) {
      return (
        <div className="flex flex-wrap gap-1">
          {value.map((item, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-bronze-100 text-bronze-700 text-xs rounded-full"
            >
              {String(item)}
            </span>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      return (
        <pre className="text-xs bg-vellum-50 p-2 rounded overflow-x-auto">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }

    return <span>{String(value)}</span>;
  };

  const importantFields = ['age', 'status', 'power_level', 'notes'];
  const displayFields = showFullDetails
    ? Object.entries(state_data)
    : Object.entries(state_data).filter(([key]) => importantFields.includes(key));

  return (
    <div
      className={`p-4 rounded-lg border transition-all cursor-pointer ${
        isSelected
          ? 'border-bronze-500 bg-bronze-50 shadow-md'
          : 'border-vellum-200 bg-white hover:border-bronze-300 hover:shadow-sm'
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-midnight-800">
            {label || `State #${state.order_index + 1}`}
          </h4>
          {narrative_timestamp && (
            <p className="text-sm text-bronze-600 mt-0.5">
              {narrative_timestamp}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!is_canonical && (
            <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
              Draft
            </span>
          )}
          <span className="text-xs text-midnight-400">
            {formatDate(created_at)}
          </span>
        </div>
      </div>

      {/* State Data */}
      {displayFields.length > 0 ? (
        <div className="space-y-2">
          {displayFields.map(([key, value]) => (
            <div key={key} className="flex items-start gap-2">
              <span className="text-sm font-medium text-midnight-600 capitalize min-w-20">
                {key.replace(/_/g, ' ')}:
              </span>
              <div className="text-sm text-midnight-700 flex-1">
                {renderStateValue(key, value)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-midnight-500 italic">No state data recorded</p>
      )}

      {/* Show more indicator */}
      {!showFullDetails && Object.keys(state_data).length > displayFields.length && (
        <p className="text-xs text-bronze-600 mt-2">
          +{Object.keys(state_data).length - displayFields.length} more fields
        </p>
      )}
    </div>
  );
};

export default StateSnapshotCard;
