/**
 * useRealtimeNLP Hook
 * Manages WebSocket connection for real-time entity detection with database persistence
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { toast } from '../stores/toastStore';
import { useCodexStore } from '../stores/codexStore';
import { EntityType, SuggestionStatus } from '../types/codex';
import analytics from '../lib/analytics';

interface DetectedEntity {
  name: string;
  type: string;
  context: string;
  confidence: string;
  suggestion_id?: string;
  is_new?: boolean;
  already_in_codex?: boolean;
}

interface EntitySuggestionMessage {
  type: 'entities' | 'pong' | 'config_ack';
  new_entities?: DetectedEntity[];
  timestamp?: string;
  settings?: ExtractionSettings;
}

export interface ExtractionSettings {
  enabled: boolean;
  debounce_delay: number;  // seconds: 2, 5, or 10
  confidence_threshold: 'low' | 'medium' | 'high';
  entity_types: string[];
}

interface UseRealtimeNLPOptions {
  manuscriptId: string;
  onEntityDetected?: (entities: DetectedEntity[]) => void;
  enabled?: boolean;
  settings?: Partial<ExtractionSettings>;
}

const DEFAULT_SETTINGS: ExtractionSettings = {
  enabled: true,
  debounce_delay: 2,
  confidence_threshold: 'medium',
  entity_types: ['CHARACTER', 'LOCATION', 'ITEM', 'LORE', 'CULTURE', 'CREATURE', 'RACE', 'ORGANIZATION', 'EVENT'],
};

// Load settings from localStorage
function loadSettings(): ExtractionSettings {
  try {
    const saved = localStorage.getItem('maxwell_extraction_settings');
    if (saved) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
    }
  } catch (e) {
    console.error('Failed to load extraction settings:', e);
  }
  return DEFAULT_SETTINGS;
}

// Save settings to localStorage
function saveSettings(settings: ExtractionSettings) {
  try {
    localStorage.setItem('maxwell_extraction_settings', JSON.stringify(settings));
  } catch (e) {
    console.error('Failed to save extraction settings:', e);
  }
}

export function useRealtimeNLP({
  manuscriptId,
  onEntityDetected,
  enabled = true,
  settings: initialSettings
}: UseRealtimeNLPOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const processingTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const [settings, setSettingsState] = useState<ExtractionSettings>(() => ({
    ...loadSettings(),
    ...initialSettings
  }));

  const { addSuggestion, setSidebarOpen, setActiveTab } = useCodexStore();

  // Update settings (local and server)
  const updateSettings = useCallback((newSettings: Partial<ExtractionSettings>) => {
    const updated = { ...settings, ...newSettings };
    setSettingsState(updated);
    saveSettings(updated);

    // Send config update to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'config',
        settings: updated
      }));
    }
  }, [settings]);

  // Send text delta to server
  const sendTextDelta = useCallback((textDelta: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && settings.enabled) {
      wsRef.current.send(JSON.stringify({ text_delta: textDelta }));

      // Set processing state (will be cleared when response arrives or times out)
      setIsProcessing(true);

      // Clear any existing timeout
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }

      // Auto-clear processing after debounce delay + buffer (server debounce is 2s)
      processingTimeoutRef.current = setTimeout(() => {
        setIsProcessing(false);
      }, (settings.debounce_delay * 1000) + 1000);
    }
  }, [settings.enabled, settings.debounce_delay]);

  // Send keep-alive ping
  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  // Open Codex sidebar with Intel tab
  const openSuggestionQueue = useCallback(() => {
    setSidebarOpen(true);
    setActiveTab('intel');
  }, [setSidebarOpen, setActiveTab]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || !manuscriptId || !settings.enabled) return;

    try {
      const wsUrl = `ws://localhost:8000/api/realtime/nlp/${manuscriptId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Real-time NLP WebSocket connected');
        setIsConnected(true);

        // Send initial config
        ws.send(JSON.stringify({
          type: 'config',
          settings
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: EntitySuggestionMessage = JSON.parse(event.data);

          if (message.type === 'pong') {
            // Keep-alive response
            return;
          }

          if (message.type === 'config_ack') {
            console.log('Extraction settings confirmed:', message.settings);
            return;
          }

          // Handle entity suggestions
          if (message.type === 'entities' && message.new_entities && message.new_entities.length > 0) {
            console.log(`Received ${message.new_entities.length} entity suggestions`);

            // Clear processing state
            setIsProcessing(false);
            if (processingTimeoutRef.current) {
              clearTimeout(processingTimeoutRef.current);
            }

            // Filter to only new suggestions (not already in codex)
            const newEntities = message.new_entities.filter(e => !e.already_in_codex);

            if (newEntities.length === 0) return;

            // Trigger callback
            onEntityDetected?.(newEntities);

            // Track entity detection
            newEntities.forEach((entity) => {
              analytics.entityAnalyzed(manuscriptId, entity.type);
            });

            // Add to codex store for immediate UI update
            newEntities.forEach((entity) => {
              if (entity.suggestion_id && entity.is_new) {
                addSuggestion({
                  id: entity.suggestion_id,
                  manuscript_id: manuscriptId,
                  name: entity.name,
                  type: entity.type as EntityType,
                  context: entity.context,
                  status: SuggestionStatus.PENDING,
                  created_at: message.timestamp || new Date().toISOString(),
                });
              }
            });

            // Show toast notification for detected entities
            if (newEntities.length === 1) {
              const entity = newEntities[0];
              toast.info(
                `New ${entity.type.toLowerCase()} detected: "${entity.name}"`,
                {
                  duration: 5000,
                  action: {
                    label: 'View in Queue',
                    onClick: () => {
                      openSuggestionQueue();
                    }
                  },
                  data: entity,
                }
              );
            } else {
              // Multiple entities detected
              const types = [...new Set(newEntities.map(e => e.type.toLowerCase()))];
              toast.info(
                `${newEntities.length} new entities detected (${types.join(', ')})`,
                {
                  duration: 5000,
                  action: {
                    label: 'View in Queue',
                    onClick: () => {
                      openSuggestionQueue();
                    }
                  },
                }
              );
            }
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        // Auto-reconnect after 5 seconds
        if (enabled && settings.enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Reconnecting WebSocket...');
            connect();
          }, 5000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [manuscriptId, enabled, settings, onEntityDetected, addSuggestion, openSuggestionQueue]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Connect/disconnect based on enabled state
  useEffect(() => {
    if (enabled && settings.enabled) {
      connect();
    } else {
      disconnect();
    }

    // Set up keep-alive ping every 30 seconds
    const pingInterval = setInterval(sendPing, 30000);

    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, disconnect, sendPing, enabled, settings.enabled]);

  return {
    sendTextDelta,
    isConnected,
    isProcessing,
    settings,
    updateSettings,
    disconnect,
    reconnect: connect,
  };
}
