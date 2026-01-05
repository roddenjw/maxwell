/**
 * IdeaCard - Display individual brainstorm idea with selection and editing
 */

import { useState } from 'react';
import type { BrainstormIdea, CharacterMetadata } from '@/types/brainstorm';
import { useBrainstormStore } from '@/stores/brainstormStore';

interface IdeaCardProps {
  idea: BrainstormIdea;
}

export default function IdeaCard({ idea }: IdeaCardProps) {
  const { selectedIdeaIds, toggleIdeaSelection, updateIdea } = useBrainstormStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notes, setNotes] = useState(idea.user_notes || '');

  const isSelected = selectedIdeaIds.has(idea.id);
  const metadata = idea.idea_metadata as CharacterMetadata;

  const handleSaveNotes = () => {
    updateIdea(idea.id, { user_notes: notes });
    setIsEditingNotes(false);
  };

  const handleCancelNotes = () => {
    setNotes(idea.user_notes || '');
    setIsEditingNotes(false);
  };

  return (
    <div
      className={`border rounded-lg p-4 transition-all ${
        isSelected
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        {/* Selection Checkbox */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleIdeaSelection(idea.id)}
          className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title & Role */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="font-semibold text-gray-900">{metadata.name}</h4>
              <p className="text-sm text-gray-600">{metadata.role}</p>
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-gray-600 p-1"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              <svg
                className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Hook (Always visible) */}
          <p className="text-sm text-gray-700 mt-2 italic">"{metadata.hook}"</p>

          {/* Expanded Details */}
          {isExpanded && (
            <div className="mt-4 space-y-3 border-t border-gray-200 pt-3">
              {/* WANT */}
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase">Want</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.want}</p>
              </div>

              {/* NEED */}
              <div>
                <span className="text-xs font-semibold text-green-600 uppercase">Need</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.need}</p>
              </div>

              {/* FLAW */}
              <div>
                <span className="text-xs font-semibold text-red-600 uppercase">Flaw</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.flaw}</p>
              </div>

              {/* STRENGTH */}
              <div>
                <span className="text-xs font-semibold text-purple-600 uppercase">Strength</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.strength}</p>
              </div>

              {/* ARC */}
              <div>
                <span className="text-xs font-semibold text-orange-600 uppercase">Character Arc</span>
                <p className="text-sm text-gray-700 mt-1">{metadata.arc}</p>
              </div>

              {/* Relationships */}
              {metadata.relationships && (
                <div>
                  <span className="text-xs font-semibold text-gray-600 uppercase">Relationships</span>
                  <p className="text-sm text-gray-700 mt-1">{metadata.relationships}</p>
                </div>
              )}

              {/* Story Potential */}
              {metadata.story_potential && (
                <div>
                  <span className="text-xs font-semibold text-gray-600 uppercase">Story Potential</span>
                  <p className="text-sm text-gray-700 mt-1">{metadata.story_potential}</p>
                </div>
              )}

              {/* User Notes Section */}
              <div className="border-t border-gray-200 pt-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-600 uppercase">Your Notes</span>
                  {!isEditingNotes && (
                    <button
                      onClick={() => setIsEditingNotes(true)}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      {notes ? 'Edit' : 'Add notes'}
                    </button>
                  )}
                </div>

                {isEditingNotes ? (
                  <div className="space-y-2">
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add your thoughts, modifications, or reminders..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveNotes}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={handleCancelNotes}
                        className="px-3 py-1 bg-gray-200 text-gray-700 text-xs rounded-md hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : notes ? (
                  <p className="text-sm text-gray-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                    {notes}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">No notes yet</p>
                )}
              </div>
            </div>
          )}

          {/* Footer Metadata */}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            <span>Cost: ${idea.ai_cost.toFixed(4)}</span>
            <span>Tokens: {idea.ai_tokens.toLocaleString()}</span>
            <span>Model: {idea.ai_model}</span>
            {idea.integrated_to_codex && (
              <span className="text-green-600 font-medium">✓ In Codex</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
