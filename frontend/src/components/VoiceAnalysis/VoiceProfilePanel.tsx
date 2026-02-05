/**
 * VoiceProfilePanel - Character Voice Analysis Dashboard
 *
 * Shows voice profiles for characters, detected inconsistencies,
 * and voice comparisons between characters.
 */

import React, { useState, useEffect } from 'react';

interface VoiceProfile {
  id: string;
  character_id: string;
  character_name: string;
  confidence_score: number;
  profile_data: {
    avg_sentence_length: number;
    vocabulary_complexity: number;
    vocabulary_richness: number;
    contraction_rate: number;
    question_rate: number;
    exclamation_rate: number;
    formality_score: number;
    common_phrases: [string, number][];
    signature_words: string[];
    filler_words: Record<string, number>;
    dialogue_samples: number;
    total_words: number;
  };
}

interface VoiceInconsistency {
  id: string;
  character_id: string;
  character_name: string;
  chapter_id: string;
  inconsistency_type: string;
  severity: string;
  description: string;
  dialogue_excerpt: string;
  suggestion: string;
  teaching_point: string;
  is_resolved: number;
}

interface VoiceComparison {
  character_a_name: string;
  character_b_name: string;
  overall_similarity: number;
  vocabulary_similarity: number;
  structure_similarity: number;
  formality_similarity: number;
  distinguishing_features_a: string[];
  distinguishing_features_b: string[];
  recommendations: string[];
}

interface VoiceProfilePanelProps {
  manuscriptId: string;
  selectedCharacterId?: string;
  onNavigateToIssue?: (chapterId: string, offset: number) => void;
}

export const VoiceProfilePanel: React.FC<VoiceProfilePanelProps> = ({
  manuscriptId,
  selectedCharacterId,
  onNavigateToIssue,
}) => {
  const [activeTab, setActiveTab] = useState<'profiles' | 'inconsistencies' | 'compare'>('profiles');
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [inconsistencies, setInconsistencies] = useState<VoiceInconsistency[]>([]);
  const [comparison, setComparison] = useState<VoiceComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [compareCharA, setCompareCharA] = useState<string>('');
  const [compareCharB, setCompareCharB] = useState<string>('');
  const [characters, setCharacters] = useState<Array<{ id: string; name: string }>>([]);

  // Fetch voice summary on mount
  useEffect(() => {
    fetchVoiceSummary();
  }, [manuscriptId]);

  // Fetch profile when character selected
  useEffect(() => {
    if (selectedCharacterId) {
      fetchProfile(selectedCharacterId);
    }
  }, [selectedCharacterId]);

  const fetchVoiceSummary = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/summary/${manuscriptId}`
      );
      const data = await response.json();
      if (data.success) {
        setCharacters(data.data.characters.map((c: any) => ({
          id: c.character_id,
          name: c.character_name,
        })));
      }
    } catch (error) {
      console.error('Failed to fetch voice summary:', error);
    }
  };

  const fetchProfile = async (characterId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/profile/${characterId}?manuscript_id=${manuscriptId}`
      );
      const data = await response.json();
      if (data.success) {
        setSelectedProfile(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchInconsistencies = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/inconsistencies/${manuscriptId}`
      );
      const data = await response.json();
      if (data.success) {
        setInconsistencies(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch inconsistencies:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/analyze/${manuscriptId}`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.success) {
        setInconsistencies(data.data.inconsistencies);
        setActiveTab('inconsistencies');
      }
    } catch (error) {
      console.error('Failed to run analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const buildAllProfiles = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/profiles/build-all/${manuscriptId}`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.success) {
        fetchVoiceSummary();
      }
    } catch (error) {
      console.error('Failed to build profiles:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const compareVoices = async () => {
    if (!compareCharA || !compareCharB || compareCharA === compareCharB) return;

    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/voice-analysis/compare/${compareCharA}/${compareCharB}?manuscript_id=${manuscriptId}`
      );
      const data = await response.json();
      if (data.success) {
        setComparison(data.data);
      }
    } catch (error) {
      console.error('Failed to compare voices:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resolveIssue = async (issueId: string) => {
    try {
      await fetch(
        `http://localhost:8000/api/voice-analysis/inconsistencies/${issueId}/resolve`,
        { method: 'PUT' }
      );
      setInconsistencies(prev => prev.filter(i => i.id !== issueId));
    } catch (error) {
      console.error('Failed to resolve issue:', error);
    }
  };

  const dismissIssue = async (issueId: string) => {
    try {
      await fetch(
        `http://localhost:8000/api/voice-analysis/inconsistencies/${issueId}/dismiss`,
        { method: 'PUT' }
      );
      setInconsistencies(prev => prev.filter(i => i.id !== issueId));
    } catch (error) {
      console.error('Failed to dismiss issue:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-amber-600 bg-amber-50';
      case 'low': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;

  return (
    <div className="voice-profile-panel h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-ui">
        <h2 className="text-lg font-garamond font-semibold text-midnight flex items-center gap-2">
          <span>🎭</span>
          Voice Analysis
        </h2>
        <p className="text-sm text-faded-ink mt-1">
          Analyze character dialogue patterns for consistency
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-ui">
        <button
          onClick={() => setActiveTab('profiles')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'profiles'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          Profiles
        </button>
        <button
          onClick={() => { setActiveTab('inconsistencies'); fetchInconsistencies(); }}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'inconsistencies'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          Issues
        </button>
        <button
          onClick={() => setActiveTab('compare')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'compare'
              ? 'text-bronze border-b-2 border-bronze'
              : 'text-faded-ink hover:text-midnight'
          }`}
        >
          Compare
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin h-8 w-8 border-2 border-bronze border-t-transparent rounded-full" />
          </div>
        )}

        {/* Profiles Tab */}
        {activeTab === 'profiles' && !isLoading && (
          <div className="space-y-4">
            <button
              onClick={buildAllProfiles}
              className="w-full px-4 py-2 bg-bronze text-white rounded-lg hover:bg-bronze/90 transition-colors text-sm font-medium"
            >
              Build Voice Profiles
            </button>

            {/* Character List */}
            <div className="space-y-2">
              {characters.map(char => (
                <button
                  key={char.id}
                  onClick={() => fetchProfile(char.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg border transition-colors ${
                    selectedProfile?.character_id === char.id
                      ? 'border-bronze bg-bronze/5'
                      : 'border-slate-ui hover:border-bronze/50'
                  }`}
                >
                  <span className="font-medium text-midnight">{char.name}</span>
                </button>
              ))}
            </div>

            {/* Selected Profile Details */}
            {selectedProfile && selectedProfile.profile_data && (
              <div className="mt-4 p-4 bg-vellum rounded-lg">
                <h3 className="font-garamond font-semibold text-midnight mb-3">
                  {selectedProfile.character_name}'s Voice
                </h3>

                <div className="text-xs text-faded-ink mb-3">
                  Based on {selectedProfile.profile_data.dialogue_samples} dialogue samples
                  ({selectedProfile.profile_data.total_words} words)
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-faded-ink">Sentence Length</span>
                    <div className="font-medium text-midnight">
                      {selectedProfile.profile_data.avg_sentence_length.toFixed(1)} words
                    </div>
                  </div>
                  <div>
                    <span className="text-faded-ink">Formality</span>
                    <div className="font-medium text-midnight">
                      {formatPercent(selectedProfile.profile_data.formality_score)}
                    </div>
                  </div>
                  <div>
                    <span className="text-faded-ink">Contractions</span>
                    <div className="font-medium text-midnight">
                      {formatPercent(selectedProfile.profile_data.contraction_rate)}
                    </div>
                  </div>
                  <div>
                    <span className="text-faded-ink">Questions</span>
                    <div className="font-medium text-midnight">
                      {formatPercent(selectedProfile.profile_data.question_rate)}
                    </div>
                  </div>
                </div>

                {/* Signature Words */}
                {selectedProfile.profile_data.signature_words.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm text-faded-ink">Signature Words</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedProfile.profile_data.signature_words.slice(0, 8).map(word => (
                        <span
                          key={word}
                          className="px-2 py-0.5 bg-bronze/10 text-bronze rounded text-xs"
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Common Phrases */}
                {selectedProfile.profile_data.common_phrases.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm text-faded-ink">Common Phrases</span>
                    <ul className="mt-1 space-y-1">
                      {selectedProfile.profile_data.common_phrases.slice(0, 5).map(([phrase, count]) => (
                        <li key={phrase} className="text-sm text-midnight">
                          "{phrase}" <span className="text-faded-ink">({count}x)</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Inconsistencies Tab */}
        {activeTab === 'inconsistencies' && !isLoading && (
          <div className="space-y-4">
            <button
              onClick={runAnalysis}
              className="w-full px-4 py-2 bg-bronze text-white rounded-lg hover:bg-bronze/90 transition-colors text-sm font-medium"
            >
              Run Voice Analysis
            </button>

            {inconsistencies.length === 0 ? (
              <div className="text-center py-8 text-faded-ink">
                <div className="text-3xl mb-2">✅</div>
                <p>No voice inconsistencies detected</p>
                <p className="text-sm mt-1">
                  Run analysis to check for voice consistency issues
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {inconsistencies.map(issue => (
                  <div
                    key={issue.id}
                    className={`p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-medium">{issue.character_name}</span>
                        <span className="mx-2 text-faded-ink">•</span>
                        <span className="text-sm capitalize">{issue.inconsistency_type.toLowerCase()}</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded capitalize ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                    </div>

                    <p className="text-sm mt-2">{issue.description}</p>

                    {issue.dialogue_excerpt && (
                      <blockquote className="mt-2 pl-3 border-l-2 border-current/20 text-sm italic">
                        "{issue.dialogue_excerpt.slice(0, 100)}..."
                      </blockquote>
                    )}

                    {issue.suggestion && (
                      <p className="text-sm mt-2 text-faded-ink">
                        <strong>Suggestion:</strong> {issue.suggestion}
                      </p>
                    )}

                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => resolveIssue(issue.id)}
                        className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Resolved
                      </button>
                      <button
                        onClick={() => dismissIssue(issue.id)}
                        className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                      >
                        Dismiss
                      </button>
                      {onNavigateToIssue && (
                        <button
                          onClick={() => onNavigateToIssue(issue.chapter_id, 0)}
                          className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          Go to Chapter
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === 'compare' && !isLoading && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <select
                value={compareCharA}
                onChange={(e) => setCompareCharA(e.target.value)}
                className="px-3 py-2 border border-slate-ui rounded-lg text-sm"
              >
                <option value="">Select character...</option>
                {characters.map(char => (
                  <option key={char.id} value={char.id}>{char.name}</option>
                ))}
              </select>
              <select
                value={compareCharB}
                onChange={(e) => setCompareCharB(e.target.value)}
                className="px-3 py-2 border border-slate-ui rounded-lg text-sm"
              >
                <option value="">Select character...</option>
                {characters.map(char => (
                  <option key={char.id} value={char.id}>{char.name}</option>
                ))}
              </select>
            </div>

            <button
              onClick={compareVoices}
              disabled={!compareCharA || !compareCharB || compareCharA === compareCharB}
              className="w-full px-4 py-2 bg-bronze text-white rounded-lg hover:bg-bronze/90 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Compare Voices
            </button>

            {comparison && (
              <div className="p-4 bg-vellum rounded-lg">
                <h3 className="font-garamond font-semibold text-midnight mb-3">
                  {comparison.character_a_name} vs {comparison.character_b_name}
                </h3>

                {/* Similarity Score */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-faded-ink">Overall Similarity</span>
                    <span className={`font-medium ${
                      comparison.overall_similarity > 0.7 ? 'text-amber-600' : 'text-green-600'
                    }`}>
                      {formatPercent(comparison.overall_similarity)}
                    </span>
                  </div>
                  <div className="mt-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        comparison.overall_similarity > 0.7 ? 'bg-amber-500' : 'bg-green-500'
                      }`}
                      style={{ width: formatPercent(comparison.overall_similarity) }}
                    />
                  </div>
                </div>

                {/* Detailed Similarities */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-faded-ink">Vocabulary</span>
                    <span>{formatPercent(comparison.vocabulary_similarity)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-faded-ink">Sentence Structure</span>
                    <span>{formatPercent(comparison.structure_similarity)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-faded-ink">Formality</span>
                    <span>{formatPercent(comparison.formality_similarity)}</span>
                  </div>
                </div>

                {/* Distinguishing Features */}
                {comparison.distinguishing_features_a.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm font-medium text-midnight">
                      {comparison.character_a_name}'s distinctive traits:
                    </span>
                    <ul className="mt-1 text-sm text-faded-ink list-disc list-inside">
                      {comparison.distinguishing_features_a.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {comparison.distinguishing_features_b.length > 0 && (
                  <div className="mt-3">
                    <span className="text-sm font-medium text-midnight">
                      {comparison.character_b_name}'s distinctive traits:
                    </span>
                    <ul className="mt-1 text-sm text-faded-ink list-disc list-inside">
                      {comparison.distinguishing_features_b.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {comparison.recommendations.length > 0 && (
                  <div className="mt-4 p-3 bg-amber-50 rounded border border-amber-200">
                    <span className="text-sm font-medium text-amber-800">Recommendations:</span>
                    <ul className="mt-1 text-sm text-amber-700 space-y-1">
                      {comparison.recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceProfilePanel;
