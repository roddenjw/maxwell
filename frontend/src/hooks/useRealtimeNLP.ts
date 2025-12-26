/**
 * useRealtimeNLP Hook
 * Manages WebSocket connection for real-time entity detection
 */

import { useEffect, useRef, useCallback } from 'react';
import { toast } from '../stores/toastStore';

interface DetectedEntity {
  name: string;
  type: 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';
  context: string;
  confidence: string;
}

interface EntitySuggestion {
  new_entities: DetectedEntity[];
  timestamp: string;
}

interface UseRealtimeNLPOptions {
  manuscriptId: string;
  onEntityDetected?: (entities: DetectedEntity[]) => void;
  enabled?: boolean;
}

export function useRealtimeNLP({
  manuscriptId,
  onEntityDetected,
  enabled = true
}: UseRealtimeNLPOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isConnectedRef = useRef(false);

  // Send text delta to server
  const sendTextDelta = useCallback((textDelta: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text_delta: textDelta }));
    }
  }, []);

  // Send keep-alive ping
  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || !manuscriptId) return;

    try {
      const wsUrl = `ws://localhost:8000/api/realtime/nlp/${manuscriptId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✅ Real-time NLP WebSocket connected');
        isConnectedRef.current = true;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'pong') {
            // Keep-alive response
            return;
          }

          // Handle entity suggestions
          const suggestion: EntitySuggestion = message;
          if (suggestion.new_entities && suggestion.new_entities.length > 0) {
            console.log(`📤 Received ${suggestion.new_entities.length} entity suggestions`);

            // Trigger callback
            onEntityDetected?.(suggestion.new_entities);

            // Show toast notification for each detected entity
            suggestion.new_entities.forEach((entity) => {
              toast.info(
                `Detected ${entity.type.toLowerCase()}: "${entity.name}"`,
                {
                  duration: 8000,
                  action: {
                    label: 'Add to Codex',
                    onClick: async () => {
                      try {
                        // Add entity to Codex
                        const response = await fetch('http://localhost:8000/api/codex/entities', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            manuscript_id: manuscriptId,
                            name: entity.name,
                            type: entity.type,
                            description: entity.context,
                            aliases: [],
                          }),
                        });

                        if (response.ok) {
                          toast.success(`Added "${entity.name}" to Codex`);
                        } else {
                          const errorData = await response.json();
                          toast.error(`Failed to add entity: ${errorData.detail || 'Unknown error'}`);
                        }
                      } catch (error) {
                        console.error('Failed to add entity to codex:', error);
                        toast.error('Failed to add entity to Codex');
                      }
                    }
                  },
                  data: entity,
                }
              );
            });
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        isConnectedRef.current = false;

        // Auto-reconnect after 5 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Reconnecting WebSocket...');
            connect();
          }, 5000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [manuscriptId, enabled, onEntityDetected]);

  // Cleanup on unmount
  useEffect(() => {
    connect();

    // Set up keep-alive ping every 30 seconds
    const pingInterval = setInterval(sendPing, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, sendPing]);

  return {
    sendTextDelta,
    isConnected: isConnectedRef.current,
  };
}
