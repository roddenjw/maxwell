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
  TravelLeg,
  TravelSpeedProfile,
  LocationDistance,
  ComprehensiveTimelineData,
} from '@/types/timeline';

interface TimelineStore {
  // State
  events: TimelineEvent[];
  inconsistencies: TimelineInconsistency[];
  characterLocations: CharacterLocation[];
  stats: TimelineStats | null;
  selectedEventId: string | null;
  isTimelineOpen: boolean;
  activeTab: 'visual' | 'events' | 'inconsistencies' | 'orchestrator' | 'locations' | 'conflicts' | 'graph' | 'heatmap' | 'network' | 'emotion';

  // Timeline Orchestrator state
  travelLegs: TravelLeg[];
  travelProfile: TravelSpeedProfile | null;
  locationDistances: LocationDistance[];
  showTeachingMoments: boolean;
  filterByResolved: 'all' | 'pending' | 'resolved';

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
  setActiveTab: (tab: 'visual' | 'events' | 'inconsistencies' | 'orchestrator' | 'locations' | 'conflicts' | 'graph' | 'heatmap' | 'network' | 'emotion') => void;

  // Timeline Orchestrator actions
  setTravelLegs: (legs: TravelLeg[]) => void;
  setTravelProfile: (profile: TravelSpeedProfile) => void;
  setLocationDistances: (distances: LocationDistance[]) => void;
  toggleTeachingMoments: () => void;
  setFilterByResolved: (filter: 'all' | 'pending' | 'resolved') => void;
  resolveInconsistency: (id: string, notes: string) => Promise<void>;
  loadComprehensiveData: (manuscriptId: string) => Promise<void>;
  runValidation: (manuscriptId: string) => Promise<void>;

  // Computed getters
  getEventById: (eventId: string) => TimelineEvent | undefined;
  getEventsByType: (eventType: string) => TimelineEvent[];
  getInconsistenciesBySeverity: (severity: string) => TimelineInconsistency[];
  getFilteredInconsistencies: () => TimelineInconsistency[];
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

  // Timeline Orchestrator state
  travelLegs: [],
  travelProfile: null,
  locationDistances: [],
  showTeachingMoments: false,
  filterByResolved: 'pending',

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

  // Timeline Orchestrator actions
  setTravelLegs: (legs) => set({ travelLegs: legs }),

  setTravelProfile: (profile) => set({ travelProfile: profile }),

  setLocationDistances: (distances) => set({ locationDistances: distances }),

  toggleTeachingMoments: () =>
    set((state) => ({ showTeachingMoments: !state.showTeachingMoments })),

  setFilterByResolved: (filter) => set({ filterByResolved: filter }),

  resolveInconsistency: async (id: string, notes: string) => {
    try {
      const response = await fetch(`/api/timeline/inconsistencies/${id}/resolve`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution_notes: notes }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to resolve: ${response.status} ${errorText}`);
      }

      const result = await response.json();

      if (result.success) {
        // Update local state
        set((state) => ({
          inconsistencies: state.inconsistencies.map((inc) =>
            inc.id === id
              ? { ...inc, is_resolved: true, resolved_at: new Date().toISOString(), resolution_notes: notes }
              : inc
          ),
        }));
      }
    } catch (error) {
      console.error('Failed to resolve inconsistency:', error);
      throw error;
    }
  },

  loadComprehensiveData: async (manuscriptId: string) => {
    try {
      const response = await fetch(`/api/timeline/comprehensive/${manuscriptId}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to load data: ${response.status} ${errorText}`);
      }

      const result = await response.json();

      if (result.success) {
        const data: ComprehensiveTimelineData = result.data;

        // Convert is_resolved from int (0/1) to boolean if needed
        const inconsistencies = data.inconsistencies.map(inc => ({
          ...inc,
          is_resolved: Boolean(inc.is_resolved)
        }));

        set({
          events: data.events,
          inconsistencies,
          characterLocations: data.character_locations,
          travelLegs: data.travel_legs,
          travelProfile: data.travel_profile,
          locationDistances: data.location_distances,
          stats: data.stats,
        });
      } else {
        throw new Error('Load returned unsuccessful result');
      }
    } catch (error) {
      console.error('Failed to load comprehensive timeline data:', error);
      throw error;
    }
  },

  runValidation: async (manuscriptId: string) => {
    try {
      const response = await fetch(`/api/timeline/validate/${manuscriptId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Validation failed: ${response.status} ${errorText}`);
      }

      const result = await response.json();

      if (result.success) {
        // Convert is_resolved from int (0/1) to boolean if needed
        const inconsistencies = result.data.map((inc: any) => ({
          ...inc,
          is_resolved: Boolean(inc.is_resolved)
        }));

        set({ inconsistencies });
      } else {
        throw new Error('Validation returned unsuccessful result');
      }
    } catch (error) {
      console.error('Failed to run timeline validation:', error);
      throw error;
    }
  },

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

  getFilteredInconsistencies: () => {
    const { inconsistencies, filterByResolved } = get();
    if (filterByResolved === 'pending') {
      return inconsistencies.filter((i) => !i.is_resolved);
    }
    if (filterByResolved === 'resolved') {
      return inconsistencies.filter((i) => i.is_resolved);
    }
    return inconsistencies;
  },
}));
