/**
 * MindMapCanvas - Visual brainstorming canvas with draggable nodes and connections
 * Allows users to visualize relationships between ideas
 */

import { useState, useCallback, useRef, useEffect } from 'react';

interface MindMapNode {
  id: string;
  type: 'character' | 'plot' | 'location' | 'theme' | 'conflict' | 'idea';
  label: string;
  description?: string;
  x: number;
  y: number;
  color: string;
}

interface MindMapConnection {
  id: string;
  sourceId: string;
  targetId: string;
  label?: string;
  type: 'relates_to' | 'conflicts_with' | 'supports' | 'happens_in' | 'leads_to';
}

interface MindMapCanvasProps {
  manuscriptId: string;
  onSave?: (nodes: MindMapNode[], connections: MindMapConnection[]) => void;
}

const NODE_COLORS = {
  character: '#3B82F6', // blue
  plot: '#10B981', // green
  location: '#14B8A6', // teal
  theme: '#8B5CF6', // purple
  conflict: '#F97316', // orange
  idea: '#6B7280', // gray
};

const CONNECTION_COLORS = {
  relates_to: '#6B7280',
  conflicts_with: '#EF4444',
  supports: '#10B981',
  happens_in: '#14B8A6',
  leads_to: '#3B82F6',
};

export default function MindMapCanvas({ onSave }: MindMapCanvasProps) {
  const [nodes, setNodes] = useState<MindMapNode[]>([
    { id: 'center', type: 'idea', label: 'Story Concept', x: 400, y: 300, color: NODE_COLORS.idea },
  ]);
  const [connections, setConnections] = useState<MindMapConnection[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<{ sourceId: string; mouseX: number; mouseY: number } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newNodeType, setNewNodeType] = useState<MindMapNode['type']>('idea');
  const [newNodeLabel, setNewNodeLabel] = useState('');
  const [newNodeDescription, setNewNodeDescription] = useState('');
  const [connectionType, setConnectionType] = useState<MindMapConnection['type']>('relates_to');

  const canvasRef = useRef<HTMLDivElement>(null);
  const dragOffset = useRef({ x: 0, y: 0 });

  // Handle mouse move for dragging
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (draggingNode && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left - dragOffset.current.x;
      const y = e.clientY - rect.top - dragOffset.current.y;

      setNodes(prev => prev.map(node =>
        node.id === draggingNode
          ? { ...node, x: Math.max(50, Math.min(rect.width - 50, x)), y: Math.max(30, Math.min(rect.height - 30, y)) }
          : node
      ));
    }

    if (connecting && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      setConnecting(prev => prev ? {
        ...prev,
        mouseX: e.clientX - rect.left,
        mouseY: e.clientY - rect.top,
      } : null);
    }
  }, [draggingNode, connecting]);

  // Handle mouse up for dragging
  const handleMouseUp = useCallback(() => {
    setDraggingNode(null);
    if (connecting) {
      setConnecting(null);
    }
  }, [connecting]);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  // Start dragging a node
  const handleNodeMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    const node = nodes.find(n => n.id === nodeId);
    if (node && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      dragOffset.current = {
        x: e.clientX - rect.left - node.x,
        y: e.clientY - rect.top - node.y,
      };
      setDraggingNode(nodeId);
      setSelectedNode(nodeId);
    }
  };

  // Start creating a connection
  const handleConnectionStart = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      setConnecting({
        sourceId: nodeId,
        mouseX: e.clientX - rect.left,
        mouseY: e.clientY - rect.top,
      });
    }
  };

  // Complete a connection
  const handleNodeClick = (nodeId: string) => {
    if (connecting && connecting.sourceId !== nodeId) {
      // Check if connection already exists
      const exists = connections.some(
        c => (c.sourceId === connecting.sourceId && c.targetId === nodeId) ||
             (c.sourceId === nodeId && c.targetId === connecting.sourceId)
      );

      if (!exists) {
        setConnections(prev => [...prev, {
          id: `conn-${Date.now()}`,
          sourceId: connecting.sourceId,
          targetId: nodeId,
          type: connectionType,
        }]);
      }
      setConnecting(null);
    } else {
      setSelectedNode(nodeId);
    }
  };

  // Add a new node
  const handleAddNode = () => {
    if (!newNodeLabel.trim()) return;

    const newNode: MindMapNode = {
      id: `node-${Date.now()}`,
      type: newNodeType,
      label: newNodeLabel.trim(),
      description: newNodeDescription.trim() || undefined,
      x: 200 + Math.random() * 400,
      y: 150 + Math.random() * 300,
      color: NODE_COLORS[newNodeType],
    };

    setNodes(prev => [...prev, newNode]);
    setNewNodeLabel('');
    setNewNodeDescription('');
    setShowAddModal(false);
  };

  // Delete a node
  const handleDeleteNode = (nodeId: string) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    setConnections(prev => prev.filter(c => c.sourceId !== nodeId && c.targetId !== nodeId));
    setSelectedNode(null);
  };

  // Delete a connection
  const handleDeleteConnection = (connId: string) => {
    setConnections(prev => prev.filter(c => c.id !== connId));
  };

  // Save the mind map
  const handleSave = () => {
    if (onSave) {
      onSave(nodes, connections);
    }
  };

  // Get node position for connection line
  const getNodeCenter = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    return node ? { x: node.x, y: node.y } : { x: 0, y: 0 };
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Node
          </button>

          <div className="h-4 border-l border-gray-300 mx-2" />

          <label className="flex items-center gap-2 text-sm text-gray-600">
            Connection Type:
            <select
              value={connectionType}
              onChange={(e) => setConnectionType(e.target.value as MindMapConnection['type'])}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value="relates_to">Relates To</option>
              <option value="conflicts_with">Conflicts With</option>
              <option value="supports">Supports</option>
              <option value="happens_in">Happens In</option>
              <option value="leads_to">Leads To</option>
            </select>
          </label>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            Drag nodes to move | Right-click node edge to connect
          </span>
          <button
            onClick={handleSave}
            className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
          >
            Save Map
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        className="flex-1 relative bg-gray-50 overflow-hidden"
        style={{ cursor: draggingNode ? 'grabbing' : 'default' }}
      >
        {/* Grid pattern */}
        <svg className="absolute inset-0 w-full h-full">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Connections */}
          {connections.map(conn => {
            const source = getNodeCenter(conn.sourceId);
            const target = getNodeCenter(conn.targetId);
            return (
              <g key={conn.id}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={CONNECTION_COLORS[conn.type]}
                  strokeWidth={2}
                  strokeDasharray={conn.type === 'conflicts_with' ? '5,5' : undefined}
                  className="cursor-pointer hover:stroke-red-500"
                  onClick={() => handleDeleteConnection(conn.id)}
                />
                {/* Connection label */}
                <text
                  x={(source.x + target.x) / 2}
                  y={(source.y + target.y) / 2 - 5}
                  textAnchor="middle"
                  className="text-xs fill-gray-500 pointer-events-none"
                >
                  {conn.type.replace('_', ' ')}
                </text>
              </g>
            );
          })}

          {/* Active connection line */}
          {connecting && (
            <line
              x1={getNodeCenter(connecting.sourceId).x}
              y1={getNodeCenter(connecting.sourceId).y}
              x2={connecting.mouseX}
              y2={connecting.mouseY}
              stroke="#3B82F6"
              strokeWidth={2}
              strokeDasharray="5,5"
            />
          )}
        </svg>

        {/* Nodes */}
        {nodes.map(node => (
          <div
            key={node.id}
            className={`absolute transform -translate-x-1/2 -translate-y-1/2 select-none ${
              selectedNode === node.id ? 'ring-2 ring-blue-500 ring-offset-2' : ''
            }`}
            style={{ left: node.x, top: node.y }}
          >
            <div
              className="relative px-4 py-2 rounded-lg shadow-md cursor-move"
              style={{ backgroundColor: node.color }}
              onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
              onClick={() => handleNodeClick(node.id)}
            >
              <span className="text-white font-medium text-sm whitespace-nowrap">
                {node.label}
              </span>
              <span className="block text-white/70 text-xs capitalize">
                {node.type}
              </span>

              {/* Connection handle */}
              <div
                className="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white border-2 cursor-crosshair hover:bg-blue-100"
                style={{ borderColor: node.color }}
                onMouseDown={(e) => handleConnectionStart(e, node.id)}
                title="Drag to connect"
              />

              {/* Delete button (when selected) */}
              {selectedNode === node.id && node.id !== 'center' && (
                <button
                  className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center hover:bg-red-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteNode(node.id);
                  }}
                >
                  x
                </button>
              )}
            </div>

            {/* Description tooltip */}
            {node.description && selectedNode === node.id && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 bg-white rounded-lg shadow-lg border border-gray-200 max-w-xs z-10">
                <p className="text-xs text-gray-600">{node.description}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="p-3 border-t border-gray-200 bg-white">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-xs font-medium text-gray-500">Node Types:</span>
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-600 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Add Node Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Node</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={newNodeType}
                  onChange={(e) => setNewNodeType(e.target.value as MindMapNode['type'])}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="character">Character</option>
                  <option value="plot">Plot Element</option>
                  <option value="location">Location</option>
                  <option value="theme">Theme</option>
                  <option value="conflict">Conflict</option>
                  <option value="idea">Idea</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Label *</label>
                <input
                  type="text"
                  value={newNodeLabel}
                  onChange={(e) => setNewNodeLabel(e.target.value)}
                  placeholder="Enter node label..."
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newNodeDescription}
                  onChange={(e) => setNewNodeDescription(e.target.value)}
                  placeholder="Optional description..."
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddNode}
                  disabled={!newNodeLabel.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
                >
                  Add Node
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
