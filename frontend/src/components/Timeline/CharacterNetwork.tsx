/**
 * CharacterNetwork - Network graph visualization of character relationships
 * Shows character connections based on co-occurrence in events
 */

import { useState, useEffect } from 'react';
import { useTimelineStore } from '@/stores/timelineStore';
import { useCodexStore } from '@/stores/codexStore';
import { timelineApi } from '@/lib/api';

interface CharacterNetworkProps {
  manuscriptId: string;
}

interface NetworkNode {
  id: string;
  name: string;
  x: number;
  y: number;
  appearances: number;
  color: string;
  isDetected?: boolean; // True if from NER detection, not registered in Codex
}

interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
}

export default function CharacterNetwork({ manuscriptId }: CharacterNetworkProps) {
  const { events, setEvents } = useTimelineStore();
  const { entities } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    loadEvents();
  }, [manuscriptId]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await timelineApi.listEvents(manuscriptId);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || events.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-faded-ink font-sans text-sm">
          {loading ? 'Loading...' : 'No events to visualize'}
        </p>
      </div>
    );
  }

  // Build character network from events
  const characters = entities.filter(e => e.type === 'CHARACTER');

  // Count character appearances (registered)
  const characterAppearances = new Map<string, number>();
  events.forEach(event => {
    event.character_ids.forEach(charId => {
      characterAppearances.set(charId, (characterAppearances.get(charId) || 0) + 1);
    });
  });

  // Count detected person appearances (NER fallback)
  const detectedPersonAppearances = new Map<string, number>();
  events.forEach(event => {
    const detectedPersons = event.event_metadata?.detected_persons || [];
    detectedPersons.forEach((personName: string) => {
      detectedPersonAppearances.set(personName, (detectedPersonAppearances.get(personName) || 0) + 1);
    });
  });

  // Build co-occurrence matrix for both registered and detected characters
  const coOccurrences = new Map<string, number>();
  events.forEach(event => {
    // Combine registered character IDs and detected person names
    const registeredIds = event.character_ids;
    const detectedNames = event.event_metadata?.detected_persons || [];
    const allCharacters = [...registeredIds, ...detectedNames];

    for (let i = 0; i < allCharacters.length; i++) {
      for (let j = i + 1; j < allCharacters.length; j++) {
        const key = [allCharacters[i], allCharacters[j]].sort().join('-');
        coOccurrences.set(key, (coOccurrences.get(key) || 0) + 1);
      }
    }
  });

  // Filter to characters that appear in timeline
  const activeCharacters = characters.filter(c => characterAppearances.has(c.id));
  const activeDetectedPersons = Array.from(detectedPersonAppearances.keys());

  if (activeCharacters.length === 0 && activeDetectedPersons.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-center">
        <div>
          <p className="text-midnight font-garamond font-semibold mb-2">
            No character data
          </p>
          <p className="text-sm text-faded-ink font-sans">
            Characters will appear automatically as you write
          </p>
        </div>
      </div>
    );
  }

  // Create network nodes with circular layout
  const centerX = 300;
  const centerY = 300;
  const radius = 200;

  // Total nodes = registered + detected
  const totalNodes = activeCharacters.length + activeDetectedPersons.length;

  // Nodes for registered characters
  const registeredNodes: NetworkNode[] = activeCharacters.map((char, index) => {
    const angle = (index / totalNodes) * 2 * Math.PI;
    const appearances = characterAppearances.get(char.id) || 0;

    return {
      id: char.id,
      name: char.name,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      appearances,
      color: `hsl(${(index * 360 / totalNodes)}, 70%, 60%)`,
      isDetected: false
    };
  });

  // Nodes for detected persons (use person name as ID)
  const detectedNodes: NetworkNode[] = activeDetectedPersons.map((personName, index) => {
    const angle = ((activeCharacters.length + index) / totalNodes) * 2 * Math.PI;
    const appearances = detectedPersonAppearances.get(personName) || 0;

    return {
      id: `detected:${personName}`,
      name: personName,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      appearances,
      color: `hsl(${((activeCharacters.length + index) * 360 / totalNodes)}, 70%, 60%)`,
      isDetected: true
    };
  });

  const nodes: NetworkNode[] = [...registeredNodes, ...detectedNodes];

  // Create edges for all character pairs
  const edges: NetworkEdge[] = [];

  // All character identifiers (IDs for registered, names for detected)
  const allCharacterIds = [
    ...activeCharacters.map(c => c.id),
    ...activeDetectedPersons
  ];

  for (let i = 0; i < allCharacterIds.length; i++) {
    for (let j = i + 1; j < allCharacterIds.length; j++) {
      const key = [allCharacterIds[i], allCharacterIds[j]].sort().join('-');
      const weight = coOccurrences.get(key) || 0;
      if (weight > 0) {
        // Map IDs to node IDs (add 'detected:' prefix for detected persons)
        const sourceId = activeCharacters.find(c => c.id === allCharacterIds[i])
          ? allCharacterIds[i]
          : `detected:${allCharacterIds[i]}`;
        const targetId = activeCharacters.find(c => c.id === allCharacterIds[j])
          ? allCharacterIds[j]
          : `detected:${allCharacterIds[j]}`;

        edges.push({
          source: sourceId,
          target: targetId,
          weight
        });
      }
    }
  }

  // Get node by id
  const getNode = (id: string) => nodes.find(n => n.id === id);

  // Get selected node info
  const selectedNodeData = selectedNode ? getNode(selectedNode) : null;
  const isDetectedPerson = selectedNodeData?.isDetected || false;

  // Get relationships for selected character (works for both registered and detected)
  const getRelationships = (charId: string) => {
    return edges
      .filter(e => e.source === charId || e.target === charId)
      .map(e => {
        const otherId = e.source === charId ? e.target : e.source;
        // Try to find in entities, or get detected person name
        const entityChar = entities.find(en => en.id === otherId);
        if (entityChar) {
          return {
            character: entityChar,
            name: entityChar.name,
            interactions: e.weight,
            isDetected: false
          };
        }
        // Must be a detected person
        const detectedName = otherId.replace('detected:', '');
        return {
          character: null,
          name: detectedName,
          interactions: e.weight,
          isDetected: true
        };
      });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h3 className="font-garamond text-lg text-midnight mb-2">
          Character Relationship Network
        </h3>
        <p className="text-sm font-sans text-faded-ink">
          Click on characters to see their connections
        </p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Network visualization */}
        <div className="flex-1 overflow-auto p-4 bg-vellum">
          <svg
            width="600"
            height="600"
            viewBox="0 0 600 600"
            className="mx-auto"
          >
            {/* Draw edges */}
            <g className="edges">
              {edges.map((edge, idx) => {
                const sourceNode = getNode(edge.source);
                const targetNode = getNode(edge.target);
                if (!sourceNode || !targetNode) return null;

                const isHighlighted = selectedNode === edge.source || selectedNode === edge.target;
                const opacity = selectedNode ? (isHighlighted ? 0.8 : 0.1) : 0.4;
                const strokeWidth = Math.min(edge.weight * 2, 8);

                return (
                  <line
                    key={`edge-${idx}`}
                    x1={sourceNode.x}
                    y1={sourceNode.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke="#94a3b8"
                    strokeWidth={strokeWidth}
                    opacity={opacity}
                  />
                );
              })}
            </g>

            {/* Draw nodes */}
            <g className="nodes">
              {nodes.map(node => {
                const isSelected = selectedNode === node.id;
                const isConnected = selectedNode
                  ? edges.some(e => (e.source === selectedNode && e.target === node.id) ||
                                   (e.target === selectedNode && e.source === node.id))
                  : false;

                const opacity = selectedNode ? (isSelected || isConnected ? 1 : 0.3) : 1;
                const nodeRadius = 15 + (node.appearances * 2);

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer hover:opacity-100 transition-opacity"
                    onClick={() => setSelectedNode(isSelected ? null : node.id)}
                  >
                    {/* Node circle - dashed for detected persons */}
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={nodeRadius}
                      fill={node.color}
                      stroke={isSelected ? '#9a6f47' : 'white'}
                      strokeWidth={isSelected ? 4 : 2}
                      strokeDasharray={node.isDetected ? '5,3' : 'none'}
                      opacity={opacity}
                    />

                    {/* Appearance count */}
                    <text
                      x={node.x}
                      y={node.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="12"
                      fontWeight="bold"
                      fill="white"
                      opacity={opacity}
                    >
                      {node.appearances}
                    </text>

                    {/* Name label */}
                    <text
                      x={node.x}
                      y={node.y + nodeRadius + 15}
                      textAnchor="middle"
                      fontSize="11"
                      fontFamily="serif"
                      fill="#0f172a"
                      opacity={opacity}
                    >
                      {node.name}
                    </text>

                    {/* "New" indicator for detected persons */}
                    {node.isDetected && (
                      <text
                        x={node.x}
                        y={node.y + nodeRadius + 28}
                        textAnchor="middle"
                        fontSize="9"
                        fontFamily="sans-serif"
                        fill="#9a6f47"
                        opacity={opacity}
                        fontWeight="600"
                      >
                        (auto-detected)
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          </svg>

          {/* Legend */}
          <div className="mt-4 p-3 bg-white border border-slate-ui max-w-md mx-auto" style={{ borderRadius: '2px' }}>
            <p className="text-xs font-sans text-faded-ink mb-2">
              Node size = appearance count | Line thickness = interactions
            </p>
            {activeDetectedPersons.length > 0 && (
              <p className="text-xs font-sans text-bronze">
                Dashed border = auto-detected character (click to add to Codex)
              </p>
            )}
          </div>
        </div>

        {/* Details panel - for both registered and detected characters */}
        {selectedNodeData && (
          <div className="w-80 border-l border-slate-ui bg-white overflow-y-auto">
            <div className="p-4 border-b border-slate-ui">
              <h3 className="font-garamond text-lg text-midnight mb-1">
                {selectedNodeData.name}
              </h3>
              <p className="text-sm font-sans text-faded-ink mb-2">
                {selectedNodeData.appearances} appearance{selectedNodeData.appearances !== 1 ? 's' : ''}
              </p>

              {/* Add to Codex button for detected persons */}
              {isDetectedPerson && (
                <button
                  className="w-full px-3 py-2 bg-bronze text-white text-sm font-sans hover:bg-opacity-90 transition-colors"
                  style={{ borderRadius: '2px' }}
                  onClick={() => {
                    // TODO: Implement add to Codex functionality
                    alert(`Add "${selectedNodeData.name}" to Codex - Feature coming soon!`);
                  }}
                >
                  + Add to Codex
                </button>
              )}

              {isDetectedPerson && (
                <p className="text-xs font-sans text-faded-ink mt-2 italic">
                  Auto-detected from your manuscript
                </p>
              )}
            </div>

            <div className="p-4">
              <h4 className="text-xs font-sans text-faded-ink uppercase mb-3">
                Relationships
              </h4>
              <div className="space-y-2">
                {getRelationships(selectedNode!).map((rel, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-vellum border border-slate-ui"
                    style={{ borderRadius: '2px' }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-serif text-sm text-midnight">
                        {rel.name}
                        {rel.isDetected && <span className="text-xs text-bronze ml-1">(detected)</span>}
                      </span>
                      <span className="text-xs font-sans text-bronze font-semibold">
                        {rel.interactions} {rel.interactions === 1 ? 'scene' : 'scenes'}
                      </span>
                    </div>
                    {rel.character?.attributes?.description && (
                      <p className="text-xs font-sans text-faded-ink">
                        {rel.character.attributes.description}
                      </p>
                    )}
                  </div>
                ))}
                {getRelationships(selectedNode!).length === 0 && (
                  <p className="text-sm text-faded-ink font-sans italic">
                    No shared scenes with other characters
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
