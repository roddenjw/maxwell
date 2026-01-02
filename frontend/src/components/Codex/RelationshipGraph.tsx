/**
 * RelationshipGraph - Visual network diagram of entity relationships
 * Enhanced with PNG export and improved visualization
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { toPng } from 'html-to-image';
import { getEntityTypeColor, getRelationshipTypeLabel } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { useCodexStore } from '@/stores/codexStore';
import { toast } from '@/stores/toastStore';
import analytics from '@/lib/analytics';

interface RelationshipGraphProps {
  manuscriptId: string;
}

interface GraphNode {
  id: string;
  name: string;
  type: string;
  color: string;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
  strength: number;
}

export default function RelationshipGraph({ manuscriptId }: RelationshipGraphProps) {
  const { entities, relationships, setRelationships } = useCodexStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [nodeSize, setNodeSize] = useState(6);
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({
    nodes: [],
    links: [],
  });

  // Load relationships on mount
  useEffect(() => {
    loadRelationships();
  }, [manuscriptId]);

  // Update graph when entities or relationships change
  useEffect(() => {
    updateGraphData();
  }, [entities, relationships]);

  const loadRelationships = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await codexApi.listRelationships(manuscriptId);
      setRelationships(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load relationships');
    } finally {
      setLoading(false);
    }
  };

  const updateGraphData = () => {
    // Create entity lookup map
    const entityMap = new Map(entities.map((e) => [e.id, e]));

    // Build nodes from entities
    const nodes: GraphNode[] = entities.map((entity) => ({
      id: entity.id,
      name: entity.name,
      type: entity.type,
      color: getEntityTypeColor(entity.type),
    }));

    // Build links from relationships
    const links: GraphLink[] = relationships
      .map((rel) => {
        const source = entityMap.get(rel.source_entity_id);
        const target = entityMap.get(rel.target_entity_id);

        // Skip if either entity doesn't exist
        if (!source || !target) return null;

        return {
          source: rel.source_entity_id,
          target: rel.target_entity_id,
          label: getRelationshipTypeLabel(rel.relationship_type),
          strength: rel.strength,
        };
      })
      .filter((link): link is GraphLink => link !== null);

    setGraphData({ nodes, links });
  };

  const handleNodeClick = useCallback((node: any) => {
    // Could select entity when node is clicked
    console.log('Node clicked:', node);
  }, []);

  const exportToPNG = async () => {
    if (!containerRef.current) return;

    try {
      setExporting(true);
      toast.info('Generating image...');

      // Wait a bit for any animations to settle
      await new Promise(resolve => setTimeout(resolve, 500));

      const dataUrl = await toPng(containerRef.current, {
        quality: 1.0,
        pixelRatio: 2, // Higher quality
        backgroundColor: '#F9F7F1', // Maxwell vellum color
      });

      // Download the image
      const link = document.createElement('a');
      link.download = `relationship-graph-${new Date().getTime()}.png`;
      link.href = dataUrl;
      link.click();

      // Track export
      analytics.exportCompleted(manuscriptId, 'png', entities.length);
      toast.success('Graph exported as PNG!');
    } catch (err) {
      console.error('Failed to export graph:', err);
      toast.error('Failed to export graph. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const centerGraph = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  const resetView = () => {
    if (graphRef.current) {
      graphRef.current.zoom(1);
      graphRef.current.centerAt(0, 0);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-faded-ink font-sans text-sm">Loading relationships...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-redline/10 border-l-4 border-redline p-3 text-sm font-sans text-redline">
          {error}
        </div>
        <button
          onClick={loadRelationships}
          className="mt-2 text-sm font-sans text-bronze hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (entities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center h-full">
        <div className="text-4xl mb-3">🕸️</div>
        <p className="text-midnight font-garamond font-semibold mb-2">
          No entities to visualize
        </p>
        <p className="text-sm text-faded-ink font-sans max-w-xs">
          Create entities or analyze your manuscript to see relationship connections
        </p>
      </div>
    );
  }

  if (relationships.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center h-full">
        <div className="text-4xl mb-3">🔗</div>
        <p className="text-midnight font-garamond font-semibold mb-2">
          No relationships yet
        </p>
        <p className="text-sm text-faded-ink font-sans max-w-xs">
          Analyze your manuscript to detect relationships between entities
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-garamond font-semibold text-midnight">
            Relationship Network
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={loadRelationships}
              className="text-sm font-sans text-bronze hover:underline"
              title="Reload relationships from server"
            >
              Refresh
            </button>
            <button
              onClick={exportToPNG}
              disabled={exporting}
              className="px-3 py-1 bg-bronze text-white text-sm font-sans hover:bg-bronze/90 transition-colors disabled:opacity-50"
              style={{ borderRadius: '2px' }}
              title="Export as PNG image"
            >
              {exporting ? 'Exporting...' : '📸 Export PNG'}
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <button
              onClick={centerGraph}
              className="text-xs font-sans text-faded-ink hover:text-bronze transition-colors"
            >
              Center Graph
            </button>
            <button
              onClick={resetView}
              className="text-xs font-sans text-faded-ink hover:text-bronze transition-colors"
            >
              Reset Zoom
            </button>
            <label className="flex items-center gap-2 text-xs font-sans text-faded-ink">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
                className="rounded"
              />
              Show Labels
            </label>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-sans text-faded-ink">Node Size:</span>
            <input
              type="range"
              min="4"
              max="10"
              value={nodeSize}
              onChange={(e) => setNodeSize(Number(e.target.value))}
              className="w-20"
            />
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 text-xs font-sans">
          {Array.from(new Set(entities.map((e) => e.type))).map((type) => (
            <div key={type} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getEntityTypeColor(type) }}
              />
              <span className="text-faded-ink">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Graph */}
      <div ref={containerRef} className="flex-1 bg-white relative">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor="color"
          nodeRelSize={nodeSize}
          linkLabel="label"
          linkWidth={(link: any) => Math.sqrt(link.strength)}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            // Draw node
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Inter`;

            // Draw circle
            ctx.fillStyle = node.color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
            ctx.fill();

            // Draw border
            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 2 / globalScale;
            ctx.stroke();

            // Draw label if enabled
            if (showLabels) {
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillStyle = '#1E293B'; // midnight
              ctx.fillText(label, node.x, node.y + nodeSize + 2);
            }
          }}
          linkCanvasObject={(link: any, ctx) => {
            // Draw link with label
            const start = link.source;
            const end = link.target;

            if (typeof start !== 'object' || typeof end !== 'object') return;

            // Draw line
            ctx.strokeStyle = '#94A3B8'; // slate
            ctx.lineWidth = Math.max(1, Math.sqrt(link.strength));
            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.stroke();

            // Draw label at midpoint if labels are enabled
            if (showLabels) {
              const midX = (start.x + end.x) / 2;
              const midY = (start.y + end.y) / 2;

              ctx.font = '10px Inter';
              ctx.fillStyle = '#64748B'; // faded-ink
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';

              // Background for label
              const text = link.label;
              const textWidth = ctx.measureText(text).width;
              ctx.fillStyle = '#FFFFFF';
              ctx.fillRect(midX - textWidth / 2 - 2, midY - 6, textWidth + 4, 12);

              // Text
              ctx.fillStyle = '#64748B';
              ctx.fillText(text, midX, midY);
            }
          }}
          cooldownTicks={100}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          backgroundColor="#F9F7F1"
        />
      </div>

      {/* Stats */}
      <div className="p-4 border-t border-slate-ui bg-white">
        <div className="flex justify-around text-center">
          <div>
            <p className="text-2xl font-garamond font-bold text-bronze">
              {entities.length}
            </p>
            <p className="text-xs text-faded-ink font-sans">Entities</p>
          </div>
          <div>
            <p className="text-2xl font-garamond font-bold text-bronze">
              {relationships.length}
            </p>
            <p className="text-xs text-faded-ink font-sans">Relationships</p>
          </div>
        </div>
      </div>
    </div>
  );
}
