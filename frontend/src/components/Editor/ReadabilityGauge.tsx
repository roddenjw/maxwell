/**
 * ReadabilityGauge Component
 *
 * Displays readability metrics in a visual gauge format.
 * Shows grade level and reading ease with genre targets.
 */

import React from 'react';

interface ReadabilityMetrics {
  flesch_kincaid_grade: number;
  flesch_reading_ease: number;
  gunning_fog: number;
  coleman_liau: number;
  ari: number;
  average_grade: number;
  sentence_count: number;
  word_count: number;
  avg_words_per_sentence: number;
  avg_syllables_per_word: number;
  complex_word_percentage: number;
}

interface ReadabilityGaugeProps {
  metrics: ReadabilityMetrics;
  genre?: string;
  className?: string;
}

// Genre target ranges (min, max, ideal)
const GENRE_TARGETS: Record<string, [number, number, number]> = {
  young_adult: [5, 8, 6],
  middle_grade: [4, 6, 5],
  adult_fiction: [7, 11, 8],
  literary_fiction: [9, 14, 11],
  thriller: [5, 9, 7],
  romance: [5, 8, 6],
  fantasy: [7, 12, 9],
  sci_fi: [8, 13, 10],
  horror: [6, 10, 8],
  mystery: [6, 10, 8],
  historical: [8, 12, 10],
};

// Reading ease level descriptions
const EASE_LEVELS: Array<{ min: number; max: number; label: string; grade: string }> = [
  { min: 90, max: 100, label: 'Very Easy', grade: '5th grade' },
  { min: 80, max: 89, label: 'Easy', grade: '6th grade' },
  { min: 70, max: 79, label: 'Fairly Easy', grade: '7th grade' },
  { min: 60, max: 69, label: 'Standard', grade: '8th-9th grade' },
  { min: 50, max: 59, label: 'Fairly Difficult', grade: '10th-12th grade' },
  { min: 30, max: 49, label: 'Difficult', grade: 'College' },
  { min: 0, max: 29, label: 'Very Difficult', grade: 'College graduate' },
];

function getEaseLevel(ease: number): { label: string; grade: string } {
  for (const level of EASE_LEVELS) {
    if (ease >= level.min && ease <= level.max) {
      return { label: level.label, grade: level.grade };
    }
  }
  return { label: 'Unknown', grade: '' };
}

function getGradeColor(grade: number, target: [number, number, number]): string {
  const [min, max] = target;
  if (grade >= min && grade <= max) {
    return 'text-green-600';
  } else if (grade < min - 2 || grade > max + 2) {
    return 'text-amber-600';
  }
  return 'text-amber-500';
}

function getEaseColor(ease: number): string {
  if (ease >= 60) return 'text-green-600';
  if (ease >= 40) return 'text-amber-500';
  return 'text-amber-600';
}

export const ReadabilityGauge: React.FC<ReadabilityGaugeProps> = ({
  metrics,
  genre = 'adult_fiction',
  className = '',
}) => {
  const target = GENRE_TARGETS[genre] || GENRE_TARGETS.adult_fiction;
  const [targetMin, targetMax, targetIdeal] = target;
  const easeLevel = getEaseLevel(metrics.flesch_reading_ease);

  // Calculate percentage position on gauge (0-100 mapped to grade 0-20)
  const gaugePosition = Math.min(100, Math.max(0, (metrics.average_grade / 20) * 100));
  const targetMinPos = (targetMin / 20) * 100;
  const targetMaxPos = (targetMax / 20) * 100;

  return (
    <div className={`readability-gauge ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-midnight">Readability</h4>
        <span className="text-xs text-gray-500 capitalize">
          {genre.replace('_', ' ')}
        </span>
      </div>

      {/* Main Grade Display */}
      <div className="flex items-center gap-4 mb-4">
        <div className="text-center">
          <div className={`text-3xl font-bold ${getGradeColor(metrics.average_grade, target)}`}>
            {metrics.average_grade.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">Grade Level</div>
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-midnight">{easeLevel.label}</div>
          <div className="text-xs text-gray-500">{easeLevel.grade}</div>
        </div>
      </div>

      {/* Visual Gauge */}
      <div className="relative h-6 mb-4">
        {/* Background track */}
        <div className="absolute inset-0 bg-gray-100 rounded-full overflow-hidden">
          {/* Target zone */}
          <div
            className="absolute top-0 bottom-0 bg-green-100"
            style={{
              left: `${targetMinPos}%`,
              width: `${targetMaxPos - targetMinPos}%`,
            }}
          />
        </div>
        {/* Current position indicator */}
        <div
          className="absolute top-0 w-1 h-6 bg-bronze rounded-full transition-all duration-300"
          style={{ left: `${gaugePosition}%`, transform: 'translateX(-50%)' }}
        />
        {/* Grade labels */}
        <div className="absolute -bottom-4 left-0 text-xs text-gray-400">0</div>
        <div className="absolute -bottom-4 left-1/4 text-xs text-gray-400">5</div>
        <div className="absolute -bottom-4 left-1/2 text-xs text-gray-400 -translate-x-1/2">10</div>
        <div className="absolute -bottom-4 left-3/4 text-xs text-gray-400">15</div>
        <div className="absolute -bottom-4 right-0 text-xs text-gray-400">20</div>
      </div>

      {/* Target indicator */}
      <div className="text-center text-xs text-gray-500 mb-4">
        Target: {targetMin}-{targetMax} (ideal: {targetIdeal})
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs border-t border-gray-100 pt-3">
        <div className="flex justify-between">
          <span className="text-gray-500">Reading Ease</span>
          <span className={getEaseColor(metrics.flesch_reading_ease)}>
            {metrics.flesch_reading_ease.toFixed(0)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Flesch-Kincaid</span>
          <span>{metrics.flesch_kincaid_grade.toFixed(1)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Gunning Fog</span>
          <span>{metrics.gunning_fog.toFixed(1)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Coleman-Liau</span>
          <span>{metrics.coleman_liau.toFixed(1)}</span>
        </div>
        <div className="flex justify-between col-span-2 border-t border-gray-100 pt-2 mt-1">
          <span className="text-gray-500">Words/Sentence</span>
          <span>{metrics.avg_words_per_sentence.toFixed(1)}</span>
        </div>
        <div className="flex justify-between col-span-2">
          <span className="text-gray-500">Complex Words</span>
          <span>{metrics.complex_word_percentage.toFixed(1)}%</span>
        </div>
      </div>

      {/* Teaching tip */}
      <div className="mt-3 p-2 bg-vellum-50 rounded text-xs text-gray-600 italic">
        {metrics.average_grade > targetMax + 2
          ? 'Consider shorter sentences and simpler vocabulary for this genre.'
          : metrics.average_grade < targetMin - 2
          ? 'You might add more sentence variety and descriptive depth.'
          : 'Your prose complexity matches genre expectations well.'}
      </div>
    </div>
  );
};

export default ReadabilityGauge;
