/**
 * Timeline Store
 * State management for timeline events, inconsistencies, and character locations
 */

import { create } from 'zustand';
import type {
  TimelineEvent,
  TimelineInconsistency,
  CharacterLocation,
  TimelineStats,
} from '@/types/timeline';

interface TimelineStore {
  // State
  events: TimelineEvent[];
  inconsistencies: TimelineInconsistency[];
  characterLocations: CharacterLocation[];
  stats: TimelineStats | null;
  selectedEventId: string | null;
  isTimelineOpen: boolean;
  activeTab: 'visual' | 'events' | 'inconsistencies' | 'graph' | 'heatmap' | 'network' | 'emotion';

  // Actions
  setEvents: (events: TimelineEvent[]) => void;
  addEvent: (event: TimelineEvent) => void;
  updateEvent: (eventId: string, updated: TimelineEvent) => void;
  removeEvent: (eventId: string) => void;

  setInconsistencies: (inconsistencies: TimelineInconsistency[]) => void;
  removeInconsistency: (inconsistencyId: string) => void;

  setCharacterLocations: (locations: CharacterLocation[]) => void;
  addCharacterLocation: (location: CharacterLocation) => void;

  setStats: (stats: TimelineStats) => void;
  setSelectedEvent: (eventId: string | null) => void;
  setTimelineOpen: (isOpen: boolean) => void;
  setActiveTab: (tab: 'visual' | 'events' | 'inconsistencies' | 'graph' | 'heatmap' | 'network' | 'emotion') => void;

  // Computed getters
  getEventById: (eventId: string) => TimelineEvent | undefined;
  getEventsByType: (eventType: string) => TimelineEvent[];
  getInconsistenciesBySeverity: (severity: string) => TimelineInconsistency[];
}

export const useTimelineStore = create<TimelineStore>((set, get) => ({
  // Initial state
  events: [],
  inconsistencies: [],
  characterLocations: [],
  stats: null,
  selectedEventId: null,
  isTimelineOpen: false,
  activeTab: 'visual',

  // Actions
  setEvents: (events) => set({ events }),

  addEvent: (event) =>
    set((state) => ({ events: [...state.events, event] })),

  updateEvent: (eventId, updated) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === eventId ? updated : e)),
    })),

  removeEvent: (eventId) =>
    set((state) => ({
      events: state.events.filter((e) => e.id !== eventId),
    })),

  setInconsistencies: (inconsistencies) => set({ inconsistencies }),

  removeInconsistency: (inconsistencyId) =>
    set((state) => ({
      inconsistencies: state.inconsistencies.filter((i) => i.id !== inconsistencyId),
    })),

  setCharacterLocations: (locations) => set({ characterLocations: locations }),

  addCharacterLocation: (location) =>
    set((state) => ({
      characterLocations: [...state.characterLocations, location],
    })),

  setStats: (stats) => set({ stats }),

  setSelectedEvent: (eventId) => set({ selectedEventId: eventId }),

  setTimelineOpen: (isOpen) => set({ isTimelineOpen: isOpen }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  // Computed getters
  getEventById: (eventId) => {
    const { events } = get();
    return events.find((e) => e.id === eventId);
  },

  getEventsByType: (eventType) => {
    const { events } = get();
    return events.filter((e) => e.event_type === eventType);
  },

  getInconsistenciesBySeverity: (severity) => {
    const { inconsistencies } = get();
    return inconsistencies.filter((i) => i.severity === severity);
  },
}));
