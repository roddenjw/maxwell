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
  GanttBeat,
  GanttEvent,
} from '@/types/timeline';
import type { PlotBeat } from '@/types/outline';

interface TimelineStore {
  // State
  events: TimelineEvent[];
  inconsistencies: TimelineInconsistency[];
  characterLocations: CharacterLocation[];
  stats: TimelineStats | null;
  selectedEventId: string | null;
  isTimelineOpen: boolean;
  activeTab: 'visual' | 'gantt' | 'events' | 'inconsistencies' | 'orchestrator' | 'locations' | 'conflicts' | 'graph' | 'heatmap' | 'network' | 'emotion' | 'foreshadow';

  // Error handling state
  loadingError: string | null;
  isLoading: boolean;
  retryCount: number;

  // Gantt Timeline State
  plotBeats: PlotBeat[];
  ganttViewData: GanttBeat[] | null;

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
  setActiveTab: (tab: 'visual' | 'gantt' | 'events' | 'inconsistencies' | 'orchestrator' | 'locations' | 'conflicts' | 'graph' | 'heatmap' | 'network' | 'emotion' | 'foreshadow') => void;

  // Error handling actions
  setLoadingError: (error: string | null) => void;
  setIsLoading: (loading: boolean) => void;
  clearError: () => void;

  // Timeline Orchestrator actions
  setTravelLegs: (legs: TravelLeg[]) => void;
  setTravelProfile: (profile: TravelSpeedProfile) => void;
  setLocationDistances: (distances: LocationDistance[]) => void;
  toggleTeachingMoments: () => void;
  setFilterByResolved: (filter: 'all' | 'pending' | 'resolved') => void;
  resolveInconsistency: (id: string, notes: string) => Promise<void>;
  loadComprehensiveData: (manuscriptId: string) => Promise<void>;
  runValidation: (manuscriptId: string) => Promise<void>;

  // Gantt Timeline actions
  loadOutline: (manuscriptId: string) => Promise<void>;
  computeGanttData: () => void;

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

  // Error handling state
  loadingError: null,
  isLoading: false,
  retryCount: 0,

  // Gantt Timeline state
  plotBeats: [],
  ganttViewData: null,

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

  // Error handling actions
  setLoadingError: (error) => set({ loadingError: error }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  clearError: () => set({ loadingError: null, retryCount: 0 }),

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
    const maxRetries = 3;
    const { retryCount } = get();

    set({ isLoading: true, loadingError: null });

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

        // Filter out events with missing or invalid data
        const validEvents = (data.events || []).filter(e => e && e.id && e.description);

        set({
          events: validEvents,
          inconsistencies,
          characterLocations: data.character_locations || [],
          travelLegs: data.travel_legs || [],
          travelProfile: data.travel_profile,
          locationDistances: data.location_distances || [],
          stats: data.stats,
          isLoading: false,
          loadingError: null,
          retryCount: 0,
        });

        // Automatically compute Gantt data after loading events (if outline already loaded)
        get().computeGanttData();
      } else {
        throw new Error('Load returned unsuccessful result');
      }
    } catch (error) {
      console.error('Failed to load comprehensive timeline data:', error);

      // Retry logic
      if (retryCount < maxRetries) {
        set({ retryCount: retryCount + 1 });
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, retryCount) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        return get().loadComprehensiveData(manuscriptId);
      }

      set({
        isLoading: false,
        loadingError: error instanceof Error ? error.message : 'Failed to load timeline data',
      });
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

  // Gantt Timeline actions
  loadOutline: async (manuscriptId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/outlines/manuscript/${manuscriptId}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to load outline: ${response.status} ${errorText}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        const plotBeats = result.data.plot_beats || [];
        set({ plotBeats });

        // Automatically compute Gantt data after loading outline
        get().computeGanttData();
      }
    } catch (error) {
      console.error('Failed to load outline for Gantt view:', error);
      // Don't throw - Gantt view is optional enhancement
    }
  },

  computeGanttData: () => {
    const { plotBeats, events } = get();

    // If no beats, clear gantt data
    if (!plotBeats || plotBeats.length === 0) {
      set({ ganttViewData: null });
      return;
    }

    // Sort beats by target_position_percent (should already be sorted by order_index)
    const sortedBeats = [...plotBeats].sort((a, b) => a.target_position_percent - b.target_position_percent);

    // Calculate total word count for proportional sizing
    const totalWordCount = sortedBeats.reduce((sum, beat) => sum + beat.target_word_count, 0);

    // If no word count, can't compute Gantt
    if (totalWordCount === 0) {
      set({ ganttViewData: null });
      return;
    }

    // Build Gantt beats with computed positions and widths
    let cumulativePercent = 0;
    const ganttBeats: GanttBeat[] = sortedBeats.map((beat, index) => {
      const widthPercent = (beat.target_word_count / totalWordCount) * 100;
      const startPercent = cumulativePercent;
      cumulativePercent += widthPercent;

      // Determine which events fall within this beat
      // Use order_index to map events to beats
      // Assume beats are sequential and events are sorted by order_index
      const beatEvents: GanttEvent[] = [];

      if (events && events.length > 0) {
        // Calculate event range for this beat based on order_index
        // If we have N beats and M events, divide events proportionally
        const eventsPerBeat = events.length / sortedBeats.length;
        const startEventIndex = Math.floor(index * eventsPerBeat);
        const endEventIndex = Math.floor((index + 1) * eventsPerBeat);

        const beatEventsList = events.slice(startEventIndex, endEventIndex);

        beatEventsList.forEach((event, eventIndex) => {
          const positionInBeat = beatEventsList.length > 1
            ? eventIndex / (beatEventsList.length - 1)
            : 0.5;

          // Map narrative_importance (1-10) to 'high' | 'medium' | 'low'
          const importance = event.narrative_importance >= 7
            ? 'high'
            : event.narrative_importance >= 4
            ? 'medium'
            : 'low';

          beatEvents.push({
            id: event.id,
            event_name: event.description,
            narrative_importance: importance,
            positionInBeat,
          });
        });
      }

      return {
        id: beat.id,
        beat_name: beat.beat_name,
        beat_label: beat.beat_label,
        target_word_count: beat.target_word_count,
        actual_word_count: beat.actual_word_count,
        is_completed: beat.is_completed,
        startPercent,
        widthPercent,
        events: beatEvents,
      };
    });

    set({ ganttViewData: ganttBeats });
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
