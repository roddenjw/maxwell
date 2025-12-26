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

  // Count character appearances
  const characterAppearances = new Map<string, number>();
  events.forEach(event => {
    event.character_ids.forEach(charId => {
      characterAppearances.set(charId, (characterAppearances.get(charId) || 0) + 1);
    });
  });

  // Build co-occurrence matrix (characters appearing together)
  const coOccurrences = new Map<string, number>();
  events.forEach(event => {
    const chars = event.character_ids;
    for (let i = 0; i < chars.length; i++) {
      for (let j = i + 1; j < chars.length; j++) {
        const key = [chars[i], chars[j]].sort().join('-');
        coOccurrences.set(key, (coOccurrences.get(key) || 0) + 1);
      }
    }
  });

  // Filter to characters that appear in timeline
  const activeCharacters = characters.filter(c => characterAppearances.has(c.id));

  if (activeCharacters.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-center">
        <div>
          <p className="text-midnight font-garamond font-semibold mb-2">
            No character data
          </p>
          <p className="text-sm text-faded-ink font-sans">
            Add characters to events to see relationships
          </p>
        </div>
      </div>
    );
  }

  // Create network nodes with circular layout
  const centerX = 300;
  const centerY = 300;
  const radius = 200;

  const nodes: NetworkNode[] = activeCharacters.map((char, index) => {
    const angle = (index / activeCharacters.length) * 2 * Math.PI;
    const appearances = characterAppearances.get(char.id) || 0;

    return {
      id: char.id,
      name: char.name,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      appearances,
      color: `hsl(${(index * 360 / activeCharacters.length)}, 70%, 60%)`
    };
  });

  // Create edges
  const edges: NetworkEdge[] = [];
  for (let i = 0; i < activeCharacters.length; i++) {
    for (let j = i + 1; j < activeCharacters.length; j++) {
      const key = [activeCharacters[i].id, activeCharacters[j].id].sort().join('-');
      const weight = coOccurrences.get(key) || 0;
      if (weight > 0) {
        edges.push({
          source: activeCharacters[i].id,
          target: activeCharacters[j].id,
          weight
        });
      }
    }
  }

  // Get node by id
  const getNode = (id: string) => nodes.find(n => n.id === id);

  // Get selected node info
  const selectedNodeData = selectedNode ? getNode(selectedNode) : null;
  const selectedCharacter = selectedNodeData ? entities.find(e => e.id === selectedNode) : null;

  // Get relationships for selected character
  const getRelationships = (charId: string) => {
    return edges
      .filter(e => e.source === charId || e.target === charId)
      .map(e => {
        const otherId = e.source === charId ? e.target : e.source;
        return {
          character: entities.find(en => en.id === otherId),
          interactions: e.weight
        };
      })
      .filter(r => r.character);
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
                    {/* Node circle */}
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={nodeRadius}
                      fill={node.color}
                      stroke={isSelected ? '#9a6f47' : 'white'}
                      strokeWidth={isSelected ? 4 : 2}
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
          </div>
        </div>

        {/* Details panel */}
        {selectedNodeData && selectedCharacter && (
          <div className="w-80 border-l border-slate-ui bg-white overflow-y-auto">
            <div className="p-4 border-b border-slate-ui">
              <h3 className="font-garamond text-lg text-midnight mb-1">
                {selectedCharacter.name}
              </h3>
              <p className="text-sm font-sans text-faded-ink">
                {selectedNodeData.appearances} appearance{selectedNodeData.appearances !== 1 ? 's' : ''}
              </p>
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
                        {rel.character!.name}
                      </span>
                      <span className="text-xs font-sans text-bronze font-semibold">
                        {rel.interactions} {rel.interactions === 1 ? 'scene' : 'scenes'}
                      </span>
                    </div>
                    {rel.character!.attributes?.description && (
                      <p className="text-xs font-sans text-faded-ink">
                        {rel.character!.attributes.description}
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
