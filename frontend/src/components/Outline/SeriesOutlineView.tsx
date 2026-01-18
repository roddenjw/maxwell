/**
 * SeriesOutlineView Component
 * Displays and manages series-level outlines spanning multiple books
 */

import React, { useEffect, useState } from 'react';
import { useOutlineStore } from '@/stores/outlineStore';
import type { PlotBeat } from '@/types/outline';

interface SeriesOutlineViewProps {
  seriesId: string;
  seriesName: string;
}

const SeriesOutlineView: React.FC<SeriesOutlineViewProps> = ({
  seriesId,
  seriesName,
}) => {
  const {
    seriesOutline,
    seriesStructures,
    seriesStructureWithManuscripts,
    isLoadingSeriesOutline,
    loadSeriesOutline,
    loadSeriesStructures,
    loadSeriesStructureWithManuscripts,
    createSeriesOutline,
  } = useOutlineStore();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedStructure, setSelectedStructure] = useState<string>('');

  useEffect(() => {
    loadSeriesOutline(seriesId);
    loadSeriesStructures();
    loadSeriesStructureWithManuscripts(seriesId);
  }, [seriesId, loadSeriesOutline, loadSeriesStructures, loadSeriesStructureWithManuscripts]);

  const handleCreateOutline = async () => {
    if (!selectedStructure) return;
    await createSeriesOutline(seriesId, selectedStructure);
    setShowCreateModal(false);
    loadSeriesStructureWithManuscripts(seriesId);
  };

  // Group beats by book index
  const beatsByBook = seriesOutline?.plot_beats.reduce((acc, beat) => {
    const bookIndex = beat.target_book_index || 1;
    if (!acc[bookIndex]) acc[bookIndex] = [];
    acc[bookIndex].push(beat);
    return acc;
  }, {} as Record<number, PlotBeat[]>) || {};

  if (isLoadingSeriesOutline) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bronze-600"></div>
        <span className="ml-3 text-midnight-600">Loading series outline...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-midnight-800">{seriesName} Series Arc</h2>
          {seriesOutline && seriesOutline.arc_type && (
            <p className="text-sm text-midnight-600 mt-1">
              {seriesOutline.arc_type.charAt(0).toUpperCase() + seriesOutline.arc_type.slice(1)} Structure
              {seriesOutline.book_count && ` (${seriesOutline.book_count} books)`}
            </p>
          )}
        </div>
        {!seriesOutline && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-bronze-600 text-white rounded-lg hover:bg-bronze-700 transition-colors"
          >
            Create Series Outline
          </button>
        )}
      </div>

      {/* No outline state */}
      {!seriesOutline && !showCreateModal && (
        <div className="text-center py-12 bg-vellum-50 rounded-lg border border-vellum-200">
          <svg
            className="mx-auto h-12 w-12 text-bronze-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-midnight-800">No Series Outline</h3>
          <p className="mt-2 text-midnight-600">
            Create a series-level outline to plan story arcs across multiple books.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 px-4 py-2 bg-bronze-100 text-bronze-700 rounded-md hover:bg-bronze-200 transition-colors"
          >
            Get Started
          </button>
        </div>
      )}

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-midnight-800 mb-4">
              Create Series Outline
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-midnight-700 mb-2">
                  Choose a structure template:
                </label>
                <div className="space-y-2">
                  {seriesStructures.map((structure) => (
                    <label
                      key={structure.type}
                      className={`flex items-start p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedStructure === structure.type
                          ? 'border-bronze-500 bg-bronze-50'
                          : 'border-vellum-200 hover:border-bronze-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="structure"
                        value={structure.type}
                        checked={selectedStructure === structure.type}
                        onChange={(e) => setSelectedStructure(e.target.value)}
                        className="mt-1 text-bronze-600 focus:ring-bronze-500"
                      />
                      <div className="ml-3">
                        <p className="font-medium text-midnight-800">{structure.name}</p>
                        <p className="text-sm text-midnight-600">{structure.description}</p>
                        <p className="text-xs text-bronze-600 mt-1">
                          {structure.book_count ? `${structure.book_count} books` : 'Open-ended'}
                          {' '}&bull;{' '}
                          {structure.beat_count} story beats
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-midnight-600 hover:text-midnight-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateOutline}
                disabled={!selectedStructure}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedStructure
                    ? 'bg-bronze-600 text-white hover:bg-bronze-700'
                    : 'bg-vellum-200 text-midnight-400 cursor-not-allowed'
                }`}
              >
                Create Outline
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Series outline display */}
      {seriesOutline && (
        <div className="space-y-6">
          {/* Overview */}
          {seriesOutline.premise && (
            <div className="p-4 bg-vellum-50 rounded-lg border border-vellum-200">
              <h4 className="text-sm font-medium text-midnight-700 mb-2">Series Premise</h4>
              <p className="text-midnight-800">{seriesOutline.premise}</p>
            </div>
          )}

          {/* Books timeline */}
          <div className="space-y-6">
            {Object.entries(beatsByBook)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(([bookIndex, beats]) => {
                // Find corresponding manuscript if available
                const manuscript = seriesStructureWithManuscripts?.manuscripts.find(
                  (m) => m.order_index === Number(bookIndex) - 1
                );

                return (
                  <div key={bookIndex} className="border border-vellum-200 rounded-lg overflow-hidden">
                    {/* Book header */}
                    <div className="px-4 py-3 bg-bronze-50 border-b border-vellum-200">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-midnight-800">
                          Book {bookIndex}
                          {manuscript && (
                            <span className="ml-2 font-normal text-midnight-600">
                              - {manuscript.title}
                            </span>
                          )}
                        </h3>
                        {manuscript?.outline && (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                            Outline linked
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Book beats */}
                    <div className="p-4 space-y-3">
                      {beats.map((beat) => (
                        <div
                          key={beat.id}
                          className={`p-3 rounded-lg border ${
                            beat.is_completed
                              ? 'border-green-200 bg-green-50'
                              : 'border-vellum-200 bg-white'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium text-midnight-800">{beat.beat_label}</h4>
                              <p className="text-sm text-midnight-600 mt-1">
                                {beat.beat_description}
                              </p>
                            </div>
                            <div className="text-right text-xs text-midnight-500">
                              <p>{Math.round(beat.target_position_percent * 100)}% of series</p>
                              {beat.linked_manuscript_outline_id && (
                                <p className="text-green-600 mt-1">Linked to manuscript</p>
                              )}
                            </div>
                          </div>
                          {beat.user_notes && (
                            <div className="mt-2 p-2 bg-vellum-50 rounded text-sm text-midnight-700">
                              {beat.user_notes}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SeriesOutlineView;
