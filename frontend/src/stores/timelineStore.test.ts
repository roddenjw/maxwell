/**
 * Tests for Timeline Store
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import { useTimelineStore } from './timelineStore';
import type { TimelineEvent, TimelineInconsistency, CharacterLocation, TimelineStats } from '@/types/timeline';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('TimelineStore', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      events: [],
      inconsistencies: [],
      characterLocations: [],
      stats: null,
      selectedEventId: null,
      isTimelineOpen: false,
      activeTab: 'visual',
      loadingError: null,
      isLoading: false,
      retryCount: 0,
      plotBeats: [],
      ganttViewData: null,
      travelLegs: [],
      travelProfile: null,
      locationDistances: [],
      showTeachingMoments: false,
      filterByResolved: 'pending',
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have empty events array', () => {
      const { events } = useTimelineStore.getState();
      expect(events).toEqual([]);
    });

    it('should have empty inconsistencies array', () => {
      const { inconsistencies } = useTimelineStore.getState();
      expect(inconsistencies).toEqual([]);
    });

    it('should have null stats', () => {
      const { stats } = useTimelineStore.getState();
      expect(stats).toBeNull();
    });

    it('should have visual as default active tab', () => {
      const { activeTab } = useTimelineStore.getState();
      expect(activeTab).toBe('visual');
    });

    it('should have timeline closed', () => {
      const { isTimelineOpen } = useTimelineStore.getState();
      expect(isTimelineOpen).toBe(false);
    });

    it('should have pending as default filter', () => {
      const { filterByResolved } = useTimelineStore.getState();
      expect(filterByResolved).toBe('pending');
    });
  });

  describe('Event Actions', () => {
    const mockEvent: TimelineEvent = {
      id: 'event-1',
      manuscript_id: 'ms-1',
      description: 'Important event',
      event_type: 'PLOT',
      datetime_str: '1200 AD',
      parsed_datetime: '1200-01-01T00:00:00Z',
      characters: ['John', 'Jane'],
      location: 'Castle',
      duration_minutes: 60,
      narrative_importance: 8,
      chapter_id: 'ch-1',
      created_at: '2024-01-01T00:00:00Z',
    };

    describe('setEvents', () => {
      it('should set events array', () => {
        act(() => {
          useTimelineStore.getState().setEvents([mockEvent]);
        });

        const { events } = useTimelineStore.getState();
        expect(events).toHaveLength(1);
        expect(events[0].description).toBe('Important event');
      });
    });

    describe('addEvent', () => {
      it('should add event to list', () => {
        act(() => {
          useTimelineStore.getState().addEvent(mockEvent);
        });

        const { events } = useTimelineStore.getState();
        expect(events).toHaveLength(1);
      });

      it('should append to existing events', () => {
        const secondEvent: TimelineEvent = {
          ...mockEvent,
          id: 'event-2',
          description: 'Second event',
        };

        act(() => {
          useTimelineStore.getState().addEvent(mockEvent);
          useTimelineStore.getState().addEvent(secondEvent);
        });

        const { events } = useTimelineStore.getState();
        expect(events).toHaveLength(2);
      });
    });

    describe('updateEvent', () => {
      it('should update event', () => {
        const updatedEvent: TimelineEvent = {
          ...mockEvent,
          description: 'Updated description',
        };

        act(() => {
          useTimelineStore.getState().addEvent(mockEvent);
          useTimelineStore.getState().updateEvent('event-1', updatedEvent);
        });

        const { events } = useTimelineStore.getState();
        expect(events[0].description).toBe('Updated description');
      });
    });

    describe('removeEvent', () => {
      it('should remove event from list', () => {
        act(() => {
          useTimelineStore.getState().addEvent(mockEvent);
          useTimelineStore.getState().removeEvent('event-1');
        });

        const { events } = useTimelineStore.getState();
        expect(events).toHaveLength(0);
      });
    });
  });

  describe('Inconsistency Actions', () => {
    const mockInconsistency: TimelineInconsistency = {
      id: 'inc-1',
      manuscript_id: 'ms-1',
      inconsistency_type: 'TEMPORAL',
      severity: 'high',
      description: 'Timeline conflict detected',
      event_ids: ['event-1', 'event-2'],
      detected_at: '2024-01-01T00:00:00Z',
      is_resolved: false,
    };

    describe('setInconsistencies', () => {
      it('should set inconsistencies array', () => {
        act(() => {
          useTimelineStore.getState().setInconsistencies([mockInconsistency]);
        });

        const { inconsistencies } = useTimelineStore.getState();
        expect(inconsistencies).toHaveLength(1);
        expect(inconsistencies[0].inconsistency_type).toBe('TEMPORAL');
      });
    });

    describe('removeInconsistency', () => {
      it('should remove inconsistency from list', () => {
        act(() => {
          useTimelineStore.getState().setInconsistencies([mockInconsistency]);
          useTimelineStore.getState().removeInconsistency('inc-1');
        });

        const { inconsistencies } = useTimelineStore.getState();
        expect(inconsistencies).toHaveLength(0);
      });
    });
  });

  describe('Character Location Actions', () => {
    const mockLocation: CharacterLocation = {
      id: 'loc-1',
      manuscript_id: 'ms-1',
      character_name: 'John',
      location: 'Castle',
      chapter_id: 'ch-1',
      arrival_time: '2024-01-01T10:00:00Z',
      departure_time: '2024-01-01T12:00:00Z',
    };

    describe('setCharacterLocations', () => {
      it('should set character locations', () => {
        act(() => {
          useTimelineStore.getState().setCharacterLocations([mockLocation]);
        });

        const { characterLocations } = useTimelineStore.getState();
        expect(characterLocations).toHaveLength(1);
        expect(characterLocations[0].character_name).toBe('John');
      });
    });

    describe('addCharacterLocation', () => {
      it('should add location to list', () => {
        act(() => {
          useTimelineStore.getState().addCharacterLocation(mockLocation);
        });

        const { characterLocations } = useTimelineStore.getState();
        expect(characterLocations).toHaveLength(1);
      });
    });
  });

  describe('UI Actions', () => {
    describe('setSelectedEvent', () => {
      it('should set selected event id', () => {
        act(() => {
          useTimelineStore.getState().setSelectedEvent('event-1');
        });

        const { selectedEventId } = useTimelineStore.getState();
        expect(selectedEventId).toBe('event-1');
      });
    });

    describe('setTimelineOpen', () => {
      it('should open timeline', () => {
        act(() => {
          useTimelineStore.getState().setTimelineOpen(true);
        });

        const { isTimelineOpen } = useTimelineStore.getState();
        expect(isTimelineOpen).toBe(true);
      });
    });

    describe('setActiveTab', () => {
      it('should set active tab', () => {
        act(() => {
          useTimelineStore.getState().setActiveTab('events');
        });

        const { activeTab } = useTimelineStore.getState();
        expect(activeTab).toBe('events');
      });

      it('should accept all valid tab values', () => {
        const validTabs = ['visual', 'gantt', 'events', 'inconsistencies', 'orchestrator', 'locations', 'conflicts', 'graph', 'heatmap', 'network', 'emotion', 'foreshadow'] as const;

        validTabs.forEach((tab) => {
          act(() => {
            useTimelineStore.getState().setActiveTab(tab);
          });

          expect(useTimelineStore.getState().activeTab).toBe(tab);
        });
      });
    });

    describe('setStats', () => {
      it('should set timeline stats', () => {
        const stats: TimelineStats = {
          total_events: 50,
          events_by_type: { PLOT: 20, CHARACTER: 15, SETTING: 15 },
          events_by_chapter: { 'ch-1': 10, 'ch-2': 20, 'ch-3': 20 },
          date_range: {
            earliest: '1200-01-01T00:00:00Z',
            latest: '1200-12-31T00:00:00Z',
          },
        };

        act(() => {
          useTimelineStore.getState().setStats(stats);
        });

        const stored = useTimelineStore.getState().stats;
        expect(stored?.total_events).toBe(50);
      });
    });
  });

  describe('Error Handling Actions', () => {
    describe('setLoadingError', () => {
      it('should set error message', () => {
        act(() => {
          useTimelineStore.getState().setLoadingError('Network error');
        });

        const { loadingError } = useTimelineStore.getState();
        expect(loadingError).toBe('Network error');
      });
    });

    describe('setIsLoading', () => {
      it('should set loading state', () => {
        act(() => {
          useTimelineStore.getState().setIsLoading(true);
        });

        const { isLoading } = useTimelineStore.getState();
        expect(isLoading).toBe(true);
      });
    });

    describe('clearError', () => {
      it('should clear error and reset retry count', () => {
        act(() => {
          useTimelineStore.setState({ loadingError: 'Error', retryCount: 2 });
          useTimelineStore.getState().clearError();
        });

        const state = useTimelineStore.getState();
        expect(state.loadingError).toBeNull();
        expect(state.retryCount).toBe(0);
      });
    });
  });

  describe('Timeline Orchestrator Actions', () => {
    describe('toggleTeachingMoments', () => {
      it('should toggle teaching moments state', () => {
        const initial = useTimelineStore.getState().showTeachingMoments;

        act(() => {
          useTimelineStore.getState().toggleTeachingMoments();
        });

        expect(useTimelineStore.getState().showTeachingMoments).toBe(!initial);
      });
    });

    describe('setFilterByResolved', () => {
      it('should set filter', () => {
        act(() => {
          useTimelineStore.getState().setFilterByResolved('resolved');
        });

        const { filterByResolved } = useTimelineStore.getState();
        expect(filterByResolved).toBe('resolved');
      });

      it('should accept all valid filter values', () => {
        const validFilters = ['all', 'pending', 'resolved'] as const;

        validFilters.forEach((filter) => {
          act(() => {
            useTimelineStore.getState().setFilterByResolved(filter);
          });

          expect(useTimelineStore.getState().filterByResolved).toBe(filter);
        });
      });
    });

    describe('resolveInconsistency', () => {
      it('should resolve inconsistency via API', async () => {
        const mockInconsistency: TimelineInconsistency = {
          id: 'inc-1',
          manuscript_id: 'ms-1',
          inconsistency_type: 'TEMPORAL',
          severity: 'high',
          description: 'Conflict',
          event_ids: [],
          detected_at: '2024-01-01T00:00:00Z',
          is_resolved: false,
        };

        act(() => {
          useTimelineStore.getState().setInconsistencies([mockInconsistency]);
        });

        mockFetch.mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

        await act(async () => {
          await useTimelineStore.getState().resolveInconsistency('inc-1', 'Fixed it');
        });

        const { inconsistencies } = useTimelineStore.getState();
        expect(inconsistencies[0].is_resolved).toBe(true);
        expect(inconsistencies[0].resolution_notes).toBe('Fixed it');
      });

      it('should throw on API error', async () => {
        mockFetch.mockResolvedValue({
          ok: false,
          status: 500,
          text: () => Promise.resolve('Server error'),
        });

        await expect(
          useTimelineStore.getState().resolveInconsistency('inc-1', 'notes')
        ).rejects.toThrow();
      });
    });
  });

  describe('Computed Getters', () => {
    const mockEvents: TimelineEvent[] = [
      {
        id: 'event-1',
        manuscript_id: 'ms-1',
        description: 'Plot event',
        event_type: 'PLOT',
        datetime_str: '1200 AD',
        parsed_datetime: '1200-01-01T00:00:00Z',
        characters: [],
        narrative_importance: 8,
        chapter_id: 'ch-1',
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'event-2',
        manuscript_id: 'ms-1',
        description: 'Character event',
        event_type: 'CHARACTER',
        datetime_str: '1200 AD',
        parsed_datetime: '1200-02-01T00:00:00Z',
        characters: ['John'],
        narrative_importance: 5,
        chapter_id: 'ch-2',
        created_at: '2024-01-01T00:00:00Z',
      },
    ];

    describe('getEventById', () => {
      it('should return event by id', () => {
        act(() => {
          useTimelineStore.getState().setEvents(mockEvents);
        });

        const event = useTimelineStore.getState().getEventById('event-1');
        expect(event?.description).toBe('Plot event');
      });

      it('should return undefined for non-existent event', () => {
        const event = useTimelineStore.getState().getEventById('non-existent');
        expect(event).toBeUndefined();
      });
    });

    describe('getEventsByType', () => {
      it('should filter events by type', () => {
        act(() => {
          useTimelineStore.getState().setEvents(mockEvents);
        });

        const plotEvents = useTimelineStore.getState().getEventsByType('PLOT');
        expect(plotEvents).toHaveLength(1);
        expect(plotEvents[0].description).toBe('Plot event');
      });
    });

    describe('getInconsistenciesBySeverity', () => {
      it('should filter inconsistencies by severity', () => {
        const inconsistencies: TimelineInconsistency[] = [
          {
            id: 'inc-1',
            manuscript_id: 'ms-1',
            inconsistency_type: 'TEMPORAL',
            severity: 'high',
            description: 'High severity',
            event_ids: [],
            detected_at: '2024-01-01T00:00:00Z',
            is_resolved: false,
          },
          {
            id: 'inc-2',
            manuscript_id: 'ms-1',
            inconsistency_type: 'LOCATION',
            severity: 'low',
            description: 'Low severity',
            event_ids: [],
            detected_at: '2024-01-01T00:00:00Z',
            is_resolved: false,
          },
        ];

        act(() => {
          useTimelineStore.getState().setInconsistencies(inconsistencies);
        });

        const highSeverity = useTimelineStore.getState().getInconsistenciesBySeverity('high');
        expect(highSeverity).toHaveLength(1);
        expect(highSeverity[0].description).toBe('High severity');
      });
    });

    describe('getFilteredInconsistencies', () => {
      const inconsistencies: TimelineInconsistency[] = [
        {
          id: 'inc-1',
          manuscript_id: 'ms-1',
          inconsistency_type: 'TEMPORAL',
          severity: 'high',
          description: 'Pending issue',
          event_ids: [],
          detected_at: '2024-01-01T00:00:00Z',
          is_resolved: false,
        },
        {
          id: 'inc-2',
          manuscript_id: 'ms-1',
          inconsistency_type: 'LOCATION',
          severity: 'medium',
          description: 'Resolved issue',
          event_ids: [],
          detected_at: '2024-01-01T00:00:00Z',
          is_resolved: true,
        },
      ];

      it('should filter pending inconsistencies', () => {
        act(() => {
          useTimelineStore.getState().setInconsistencies(inconsistencies);
          useTimelineStore.getState().setFilterByResolved('pending');
        });

        const filtered = useTimelineStore.getState().getFilteredInconsistencies();
        expect(filtered).toHaveLength(1);
        expect(filtered[0].description).toBe('Pending issue');
      });

      it('should filter resolved inconsistencies', () => {
        act(() => {
          useTimelineStore.getState().setInconsistencies(inconsistencies);
          useTimelineStore.getState().setFilterByResolved('resolved');
        });

        const filtered = useTimelineStore.getState().getFilteredInconsistencies();
        expect(filtered).toHaveLength(1);
        expect(filtered[0].description).toBe('Resolved issue');
      });

      it('should return all inconsistencies', () => {
        act(() => {
          useTimelineStore.getState().setInconsistencies(inconsistencies);
          useTimelineStore.getState().setFilterByResolved('all');
        });

        const filtered = useTimelineStore.getState().getFilteredInconsistencies();
        expect(filtered).toHaveLength(2);
      });
    });
  });

  describe('Gantt Timeline Actions', () => {
    describe('computeGanttData', () => {
      it('should return null when no plot beats', () => {
        act(() => {
          useTimelineStore.getState().computeGanttData();
        });

        const { ganttViewData } = useTimelineStore.getState();
        expect(ganttViewData).toBeNull();
      });

      it('should compute gantt data from plot beats', () => {
        const plotBeats = [
          {
            id: 'beat-1',
            beat_name: 'Opening',
            beat_label: 'Opening',
            target_word_count: 5000,
            actual_word_count: 4500,
            is_completed: true,
            target_position_percent: 0,
          },
          {
            id: 'beat-2',
            beat_name: 'Climax',
            beat_label: 'Climax',
            target_word_count: 5000,
            actual_word_count: 0,
            is_completed: false,
            target_position_percent: 50,
          },
        ];

        act(() => {
          useTimelineStore.setState({ plotBeats: plotBeats as any });
          useTimelineStore.getState().computeGanttData();
        });

        const { ganttViewData } = useTimelineStore.getState();
        expect(ganttViewData).toHaveLength(2);
        expect(ganttViewData![0].beat_name).toBe('Opening');
        expect(ganttViewData![0].widthPercent).toBe(50); // 5000/10000 * 100
      });
    });
  });
});
