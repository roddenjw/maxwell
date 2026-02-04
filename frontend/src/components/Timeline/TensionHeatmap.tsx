/**
 * TensionHeatmap - Visualize story tension and conflict density over time
 *
 * Shows a heatmap where intensity represents conflict/tension levels
 * across the story timeline, helping writers identify pacing issues.
 */

import { useMemo, useState } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';

interface TensionHeatmapProps {
  manuscriptId: string;
}

interface HeatmapCell {
  orderIndex: number;
  tension: number; // 0-1
  conflicts: number;
  eventCount: number;
  sentiment: number;
  keyEvents: string[];
}

// Tension-related keywords
const TENSION_KEYWORDS = {
  high: [
    'death', 'die', 'kill', 'murder', 'attack', 'war', 'battle', 'fight',
    'betray', 'revenge', 'destroy', 'crisis', 'emergency', 'danger'
  ],
  medium: [
    'argue', 'confront', 'threaten', 'accuse', 'suspect', 'chase', 'escape',
    'fear', 'worried', 'anxious', 'conflict', 'tension', 'risk', 'secret'
  ],
  low: [
    'discuss', 'question', 'wonder', 'uneasy', 'nervous', 'hesitate',
    'doubt', 'concern', 'mystery', 'strange', 'unusual'
  ]
};

// Relaxation keywords (reduce tension)
const RELAXATION_KEYWORDS = [
  'peace', 'calm', 'rest', 'happy', 'joy', 'love', 'laugh', 'smile',
  'relief', 'safe', 'comfort', 'celebrate', 'reunion', 'reconcile'
];

export default function TensionHeatmap({ manuscriptId }: TensionHeatmapProps) {
  const { events } = useTimelineStore();
  const { entities } = useCodexStore();
  const [selectedCell, setSelectedCell] = useState<number | null>(null);

  // Build heatmap data
  const heatmapData = useMemo<HeatmapCell[]>(() => {
    if (events.length === 0) return [];

    const maxOrderIndex = Math.max(...events.map(e => e.order_index));
    const characters = entities.filter(e => e.type === 'CHARACTER');

    // Group events by order index windows
    const windowSize = Math.max(1, Math.floor(maxOrderIndex / 20));
    const cells: Map<number, HeatmapCell> = new Map();

    events.forEach(event => {
      const windowIndex = Math.floor(event.order_index / windowSize);

      if (!cells.has(windowIndex)) {
        cells.set(windowIndex, {
          orderIndex: windowIndex * windowSize,
          tension: 0,
          conflicts: 0,
          eventCount: 0,
          sentiment: 0,
          keyEvents: [],
        });
      }

      const cell = cells.get(windowIndex)!;
      cell.eventCount++;

      // Calculate tension from keywords
      const textLower = event.description.toLowerCase();
      let tensionScore = 0;

      TENSION_KEYWORDS.high.forEach(keyword => {
        if (textLower.includes(keyword)) tensionScore += 0.3;
      });
      TENSION_KEYWORDS.medium.forEach(keyword => {
        if (textLower.includes(keyword)) tensionScore += 0.15;
      });
      TENSION_KEYWORDS.low.forEach(keyword => {
        if (textLower.includes(keyword)) tensionScore += 0.05;
      });

      // Reduce for relaxation keywords
      RELAXATION_KEYWORDS.forEach(keyword => {
        if (textLower.includes(keyword)) tensionScore -= 0.1;
      });

      // Add narrative importance factor
      tensionScore += (event.narrative_importance || 5) / 20;

      // Count conflicts (multiple characters + conflict keywords)
      if (event.character_ids.length >= 2) {
        const hasConflict = TENSION_KEYWORDS.high.concat(TENSION_KEYWORDS.medium)
          .some(keyword => textLower.includes(keyword));
        if (hasConflict) {
          cell.conflicts++;
          tensionScore += 0.2;
        }
      }

      // Add sentiment if available
      if (event.event_metadata?.sentiment !== undefined) {
        cell.sentiment += event.event_metadata.sentiment;
        // Negative sentiment increases tension
        if (event.event_metadata.sentiment < 0) {
          tensionScore += Math.abs(event.event_metadata.sentiment) * 0.2;
        }
      }

      cell.tension += Math.min(tensionScore, 1);

      // Track key events
      if (event.narrative_importance && event.narrative_importance > 7) {
        cell.keyEvents.push(event.description.slice(0, 50));
      }
    });

    // Normalize tension values
    const cellArray = Array.from(cells.values());
    cellArray.forEach(cell => {
      cell.tension = Math.min(cell.tension / Math.max(cell.eventCount, 1), 1);
      cell.sentiment = cell.sentiment / Math.max(cell.eventCount, 1);
    });

    return cellArray.sort((a, b) => a.orderIndex - b.orderIndex);
  }, [events, entities]);

  if (events.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <span className="text-6xl mb-4 block">🌡️</span>
          <p className="text-midnight font-garamond text-xl font-semibold mb-2">
            No timeline data for tension analysis
          </p>
          <p className="text-sm text-faded-ink font-sans">
            Add events to your timeline to visualize story tension.
          </p>
        </div>
      </div>
    );
  }

  const getTensionColor = (tension: number): string => {
    // Color gradient from cool (low tension) to hot (high tension)
    if (tension < 0.2) return '#dbeafe'; // light blue
    if (tension < 0.4) return '#bfdbfe'; // blue
    if (tension < 0.5) return '#fef3c7'; // light yellow
    if (tension < 0.6) return '#fde68a'; // yellow
    if (tension < 0.7) return '#fcd34d'; // amber
    if (tension < 0.8) return '#fb923c'; // orange
    if (tension < 0.9) return '#f87171'; // light red
    return '#ef4444'; // red
  };

  const getTensionLabel = (tension: number): string => {
    if (tension < 0.2) return 'Very Low';
    if (tension < 0.4) return 'Low';
    if (tension < 0.5) return 'Building';
    if (tension < 0.6) return 'Moderate';
    if (tension < 0.7) return 'High';
    if (tension < 0.8) return 'Very High';
    if (tension < 0.9) return 'Intense';
    return 'Peak';
  };

  const selectedCellData = selectedCell !== null
    ? heatmapData.find(c => c.orderIndex === selectedCell)
    : null;

  // Calculate overall stats
  const avgTension = heatmapData.length > 0
    ? heatmapData.reduce((sum, c) => sum + c.tension, 0) / heatmapData.length
    : 0;
  const maxTension = Math.max(...heatmapData.map(c => c.tension));
  const totalConflicts = heatmapData.reduce((sum, c) => sum + c.conflicts, 0);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h3 className="font-garamond text-lg text-midnight mb-1">
          Story Tension Heatmap
        </h3>
        <p className="text-sm font-sans text-faded-ink">
          Visualize conflict and tension density across your story
        </p>
      </div>

      {/* Summary stats */}
      <div className="p-3 border-b border-slate-ui bg-vellum flex gap-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-midnight">{(avgTension * 100).toFixed(0)}%</p>
          <p className="text-xs font-sans text-faded-ink">Avg Tension</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-midnight" style={{ color: getTensionColor(maxTension) }}>
            {(maxTension * 100).toFixed(0)}%
          </p>
          <p className="text-xs font-sans text-faded-ink">Peak Tension</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-redline">{totalConflicts}</p>
          <p className="text-xs font-sans text-faded-ink">Conflicts</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-midnight">{events.length}</p>
          <p className="text-xs font-sans text-faded-ink">Events</p>
        </div>
      </div>

      {/* Heatmap visualization */}
      <div className="flex-1 p-6 overflow-auto bg-white">
        <div className="mb-4">
          <p className="text-xs font-sans text-faded-ink uppercase mb-2">Story Timeline</p>

          {/* Heatmap bars */}
          <div className="flex gap-1 h-32 items-end">
            {heatmapData.map((cell, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedCell(
                  selectedCell === cell.orderIndex ? null : cell.orderIndex
                )}
                className={`
                  flex-1 min-w-[20px] transition-all cursor-pointer relative group
                  ${selectedCell === cell.orderIndex ? 'ring-2 ring-bronze ring-offset-2' : ''}
                `}
                style={{
                  height: `${Math.max(cell.tension * 100, 10)}%`,
                  backgroundColor: getTensionColor(cell.tension),
                  borderRadius: '2px 2px 0 0',
                }}
                title={`Events: ${cell.eventCount}, Tension: ${(cell.tension * 100).toFixed(0)}%`}
              >
                {/* Conflict markers */}
                {cell.conflicts > 0 && (
                  <div
                    className="absolute -top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-redline text-white text-[8px] flex items-center justify-center"
                  >
                    {cell.conflicts}
                  </div>
                )}

                {/* Hover tooltip */}
                <div
                  className="
                    absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-midnight text-white
                    text-xs font-sans rounded opacity-0 group-hover:opacity-100 transition-opacity
                    pointer-events-none whitespace-nowrap z-10
                  "
                >
                  {getTensionLabel(cell.tension)} ({(cell.tension * 100).toFixed(0)}%)
                </div>
              </button>
            ))}
          </div>

          {/* X-axis labels */}
          <div className="flex justify-between mt-2 text-xs font-sans text-faded-ink">
            <span>Beginning</span>
            <span>Middle</span>
            <span>End</span>
          </div>
        </div>

        {/* Color legend */}
        <div className="flex items-center gap-2 mt-6">
          <span className="text-xs font-sans text-faded-ink">Tension:</span>
          <div className="flex items-center gap-1">
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#dbeafe' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#bfdbfe' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#fef3c7' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#fde68a' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#fb923c' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#f87171' }} />
            <div className="w-6 h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
          </div>
          <span className="text-xs font-sans text-faded-ink ml-2">Low → High</span>
        </div>

        {/* Pacing recommendations */}
        <div className="mt-6 p-4 bg-vellum border border-slate-ui rounded">
          <h4 className="text-sm font-garamond font-semibold text-midnight mb-2">
            Pacing Analysis
          </h4>
          {getPacingRecommendations(heatmapData, avgTension).map((rec, idx) => (
            <p key={idx} className="text-sm font-sans text-faded-ink mb-1">
              • {rec}
            </p>
          ))}
        </div>
      </div>

      {/* Selected cell details */}
      {selectedCellData && (
        <div className="p-4 border-t border-slate-ui bg-vellum">
          <div className="flex items-center gap-4 mb-3">
            <div
              className="w-6 h-6 rounded"
              style={{ backgroundColor: getTensionColor(selectedCellData.tension) }}
            />
            <h4 className="font-garamond text-lg text-midnight">
              Story Section (Event {selectedCellData.orderIndex}+)
            </h4>
          </div>
          <div className="grid grid-cols-4 gap-4 text-sm font-sans">
            <div>
              <p className="text-faded-ink">Tension Level</p>
              <p className="text-midnight font-semibold">
                {getTensionLabel(selectedCellData.tension)} ({(selectedCellData.tension * 100).toFixed(0)}%)
              </p>
            </div>
            <div>
              <p className="text-faded-ink">Events</p>
              <p className="text-midnight font-semibold">{selectedCellData.eventCount}</p>
            </div>
            <div>
              <p className="text-faded-ink">Conflicts</p>
              <p className="text-redline font-semibold">{selectedCellData.conflicts}</p>
            </div>
            <div>
              <p className="text-faded-ink">Avg Sentiment</p>
              <p className={`font-semibold ${selectedCellData.sentiment >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {selectedCellData.sentiment > 0 ? '+' : ''}{(selectedCellData.sentiment * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          {selectedCellData.keyEvents.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-sans text-faded-ink uppercase mb-1">Key Events</p>
              {selectedCellData.keyEvents.map((event, idx) => (
                <p key={idx} className="text-sm font-serif text-midnight">• {event}...</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper function for pacing recommendations
function getPacingRecommendations(data: HeatmapCell[], avgTension: number): string[] {
  const recommendations: string[] = [];

  if (data.length === 0) return ['Add more events to get pacing recommendations.'];

  // Check for flat tension (no variation)
  const tensionVariance = data.reduce((sum, c) => sum + Math.pow(c.tension - avgTension, 2), 0) / data.length;
  if (tensionVariance < 0.02) {
    recommendations.push('Consider adding more variation in tension levels for better pacing.');
  }

  // Check beginning tension
  const firstQuarter = data.slice(0, Math.ceil(data.length / 4));
  const avgFirstQuarter = firstQuarter.reduce((sum, c) => sum + c.tension, 0) / firstQuarter.length;
  if (avgFirstQuarter > 0.7) {
    recommendations.push('Your story starts with high tension. Consider a slower build-up to let readers settle in.');
  } else if (avgFirstQuarter < 0.2) {
    recommendations.push('The beginning has low tension. Consider adding an early hook to engage readers.');
  }

  // Check for climax
  const lastQuarter = data.slice(-Math.ceil(data.length / 4));
  const maxLastQuarter = Math.max(...lastQuarter.map(c => c.tension));
  if (maxLastQuarter < 0.6) {
    recommendations.push('The ending lacks a clear tension peak. Consider strengthening your climax.');
  }

  // Check for "muddy middle"
  const middleSection = data.slice(Math.ceil(data.length / 3), Math.ceil(data.length * 2 / 3));
  const avgMiddle = middleSection.reduce((sum, c) => sum + c.tension, 0) / middleSection.length;
  if (avgMiddle < avgTension - 0.1 && middleSection.length > 2) {
    recommendations.push('The middle section has lower tension. Add complications or escalating conflicts.');
  }

  // Check for sustained high tension
  const highTensionRun = data.filter(c => c.tension > 0.7).length;
  if (highTensionRun > data.length * 0.5) {
    recommendations.push('Extended high tension can exhaust readers. Add quieter moments for contrast.');
  }

  if (recommendations.length === 0) {
    recommendations.push('Your pacing shows good variation with clear tension peaks and valleys.');
  }

  return recommendations;
}
