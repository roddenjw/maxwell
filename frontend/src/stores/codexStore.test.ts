/**
 * Tests for Codex Store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useCodexStore } from './codexStore';
import type { Entity, Relationship, EntitySuggestion } from '@/types/codex';

describe('CodexStore', () => {
  // Reset store before each test
  beforeEach(() => {
    useCodexStore.setState({
      entities: [],
      relationships: [],
      suggestions: [],
      selectedEntityId: null,
      activeTab: 'entities',
      isSidebarOpen: false,
      isAnalyzing: false,
    });
  });

  describe('Initial State', () => {
    it('should have empty entities array', () => {
      const { entities } = useCodexStore.getState();
      expect(entities).toEqual([]);
    });

    it('should have empty relationships array', () => {
      const { relationships } = useCodexStore.getState();
      expect(relationships).toEqual([]);
    });

    it('should have empty suggestions array', () => {
      const { suggestions } = useCodexStore.getState();
      expect(suggestions).toEqual([]);
    });

    it('should have null selectedEntityId', () => {
      const { selectedEntityId } = useCodexStore.getState();
      expect(selectedEntityId).toBeNull();
    });

    it('should have entities as activeTab', () => {
      const { activeTab } = useCodexStore.getState();
      expect(activeTab).toBe('entities');
    });

    it('should have sidebar closed', () => {
      const { isSidebarOpen } = useCodexStore.getState();
      expect(isSidebarOpen).toBe(false);
    });

    it('should not be analyzing', () => {
      const { isAnalyzing } = useCodexStore.getState();
      expect(isAnalyzing).toBe(false);
    });
  });

  describe('Entity Actions', () => {
    const mockEntity: Entity = {
      id: 'entity-1',
      manuscript_id: 'ms-1',
      type: 'CHARACTER',
      name: 'John Doe',
      description: 'Main character',
      aliases: ['Johnny'],
      attributes: { age: 30 },
      first_appearance_chapter: 1,
      is_auto_detected: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    describe('setEntities', () => {
      it('should set entities array', () => {
        act(() => {
          useCodexStore.getState().setEntities([mockEntity]);
        });

        const { entities } = useCodexStore.getState();
        expect(entities).toHaveLength(1);
        expect(entities[0]).toEqual(mockEntity);
      });

      it('should replace existing entities', () => {
        act(() => {
          useCodexStore.getState().setEntities([mockEntity]);
          useCodexStore.getState().setEntities([]);
        });

        const { entities } = useCodexStore.getState();
        expect(entities).toHaveLength(0);
      });
    });

    describe('addEntity', () => {
      it('should add entity to list', () => {
        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
        });

        const { entities } = useCodexStore.getState();
        expect(entities).toHaveLength(1);
        expect(entities[0].name).toBe('John Doe');
      });

      it('should append to existing entities', () => {
        const secondEntity: Entity = {
          ...mockEntity,
          id: 'entity-2',
          name: 'Jane Doe',
        };

        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().addEntity(secondEntity);
        });

        const { entities } = useCodexStore.getState();
        expect(entities).toHaveLength(2);
      });
    });

    describe('updateEntity', () => {
      it('should update entity fields', () => {
        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().updateEntity('entity-1', {
            name: 'John Smith',
            description: 'Updated description',
          });
        });

        const { entities } = useCodexStore.getState();
        expect(entities[0].name).toBe('John Smith');
        expect(entities[0].description).toBe('Updated description');
      });

      it('should not affect other entities', () => {
        const secondEntity: Entity = {
          ...mockEntity,
          id: 'entity-2',
          name: 'Jane Doe',
        };

        act(() => {
          useCodexStore.getState().setEntities([mockEntity, secondEntity]);
          useCodexStore.getState().updateEntity('entity-1', { name: 'Updated' });
        });

        const { entities } = useCodexStore.getState();
        expect(entities[0].name).toBe('Updated');
        expect(entities[1].name).toBe('Jane Doe');
      });
    });

    describe('removeEntity', () => {
      it('should remove entity from list', () => {
        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().removeEntity('entity-1');
        });

        const { entities } = useCodexStore.getState();
        expect(entities).toHaveLength(0);
      });

      it('should clear selectedEntityId if removed entity was selected', () => {
        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().setSelectedEntity('entity-1');
          useCodexStore.getState().removeEntity('entity-1');
        });

        const { selectedEntityId } = useCodexStore.getState();
        expect(selectedEntityId).toBeNull();
      });

      it('should remove relationships involving the entity', () => {
        const relationship: Relationship = {
          id: 'rel-1',
          manuscript_id: 'ms-1',
          source_entity_id: 'entity-1',
          target_entity_id: 'entity-2',
          relationship_type: 'friend',
          description: 'Friends',
          strength: 0.8,
          is_auto_detected: false,
          created_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().addRelationship(relationship);
          useCodexStore.getState().removeEntity('entity-1');
        });

        const { relationships } = useCodexStore.getState();
        expect(relationships).toHaveLength(0);
      });
    });
  });

  describe('Relationship Actions', () => {
    const mockRelationship: Relationship = {
      id: 'rel-1',
      manuscript_id: 'ms-1',
      source_entity_id: 'entity-1',
      target_entity_id: 'entity-2',
      relationship_type: 'friend',
      description: 'Best friends',
      strength: 0.9,
      is_auto_detected: false,
      created_at: '2024-01-01T00:00:00Z',
    };

    describe('setRelationships', () => {
      it('should set relationships array', () => {
        act(() => {
          useCodexStore.getState().setRelationships([mockRelationship]);
        });

        const { relationships } = useCodexStore.getState();
        expect(relationships).toHaveLength(1);
      });
    });

    describe('addRelationship', () => {
      it('should add relationship to list', () => {
        act(() => {
          useCodexStore.getState().addRelationship(mockRelationship);
        });

        const { relationships } = useCodexStore.getState();
        expect(relationships).toHaveLength(1);
        expect(relationships[0].relationship_type).toBe('friend');
      });
    });

    describe('removeRelationship', () => {
      it('should remove relationship from list', () => {
        act(() => {
          useCodexStore.getState().addRelationship(mockRelationship);
          useCodexStore.getState().removeRelationship('rel-1');
        });

        const { relationships } = useCodexStore.getState();
        expect(relationships).toHaveLength(0);
      });
    });
  });

  describe('Suggestion Actions', () => {
    const mockSuggestion: EntitySuggestion = {
      id: 'sug-1',
      manuscript_id: 'ms-1',
      entity_type: 'CHARACTER',
      name: 'New Character',
      description: 'A new character found in text',
      confidence: 0.85,
      source_text: 'She met Sarah at the cafe.',
      chapter_id: 'ch-1',
      status: 'PENDING',
      created_at: '2024-01-01T00:00:00Z',
    };

    describe('setSuggestions', () => {
      it('should set suggestions array', () => {
        act(() => {
          useCodexStore.getState().setSuggestions([mockSuggestion]);
        });

        const { suggestions } = useCodexStore.getState();
        expect(suggestions).toHaveLength(1);
      });
    });

    describe('addSuggestion', () => {
      it('should add suggestion to list', () => {
        act(() => {
          useCodexStore.getState().addSuggestion(mockSuggestion);
        });

        const { suggestions } = useCodexStore.getState();
        expect(suggestions).toHaveLength(1);
        expect(suggestions[0].name).toBe('New Character');
      });
    });

    describe('removeSuggestion', () => {
      it('should remove suggestion from list', () => {
        act(() => {
          useCodexStore.getState().addSuggestion(mockSuggestion);
          useCodexStore.getState().removeSuggestion('sug-1');
        });

        const { suggestions } = useCodexStore.getState();
        expect(suggestions).toHaveLength(0);
      });
    });
  });

  describe('UI Actions', () => {
    describe('setSelectedEntity', () => {
      it('should set selected entity id', () => {
        act(() => {
          useCodexStore.getState().setSelectedEntity('entity-1');
        });

        const { selectedEntityId } = useCodexStore.getState();
        expect(selectedEntityId).toBe('entity-1');
      });

      it('should allow setting to null', () => {
        act(() => {
          useCodexStore.getState().setSelectedEntity('entity-1');
          useCodexStore.getState().setSelectedEntity(null);
        });

        const { selectedEntityId } = useCodexStore.getState();
        expect(selectedEntityId).toBeNull();
      });
    });

    describe('setActiveTab', () => {
      it('should set active tab', () => {
        act(() => {
          useCodexStore.getState().setActiveTab('relationships');
        });

        const { activeTab } = useCodexStore.getState();
        expect(activeTab).toBe('relationships');
      });
    });

    describe('setSidebarOpen', () => {
      it('should open sidebar', () => {
        act(() => {
          useCodexStore.getState().setSidebarOpen(true);
        });

        const { isSidebarOpen } = useCodexStore.getState();
        expect(isSidebarOpen).toBe(true);
      });

      it('should close sidebar', () => {
        act(() => {
          useCodexStore.getState().setSidebarOpen(true);
          useCodexStore.getState().setSidebarOpen(false);
        });

        const { isSidebarOpen } = useCodexStore.getState();
        expect(isSidebarOpen).toBe(false);
      });
    });

    describe('toggleSidebar', () => {
      it('should toggle sidebar state', () => {
        const initialState = useCodexStore.getState().isSidebarOpen;

        act(() => {
          useCodexStore.getState().toggleSidebar();
        });

        expect(useCodexStore.getState().isSidebarOpen).toBe(!initialState);

        act(() => {
          useCodexStore.getState().toggleSidebar();
        });

        expect(useCodexStore.getState().isSidebarOpen).toBe(initialState);
      });
    });

    describe('setAnalyzing', () => {
      it('should set analyzing state', () => {
        act(() => {
          useCodexStore.getState().setAnalyzing(true);
        });

        const { isAnalyzing } = useCodexStore.getState();
        expect(isAnalyzing).toBe(true);
      });
    });
  });

  describe('Utility Actions', () => {
    describe('clearAll', () => {
      it('should reset all state', () => {
        const mockEntity: Entity = {
          id: 'entity-1',
          manuscript_id: 'ms-1',
          type: 'CHARACTER',
          name: 'Test',
          description: '',
          aliases: [],
          attributes: {},
          first_appearance_chapter: 1,
          is_auto_detected: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        act(() => {
          useCodexStore.getState().addEntity(mockEntity);
          useCodexStore.getState().setSelectedEntity('entity-1');
          useCodexStore.getState().setActiveTab('relationships');
          useCodexStore.getState().setAnalyzing(true);
          useCodexStore.getState().clearAll();
        });

        const state = useCodexStore.getState();
        expect(state.entities).toHaveLength(0);
        expect(state.relationships).toHaveLength(0);
        expect(state.suggestions).toHaveLength(0);
        expect(state.selectedEntityId).toBeNull();
        expect(state.activeTab).toBe('entities');
        expect(state.isAnalyzing).toBe(false);
      });
    });

    describe('getPendingSuggestionsCount', () => {
      it('should return count of pending suggestions', () => {
        const pendingSuggestion: EntitySuggestion = {
          id: 'sug-1',
          manuscript_id: 'ms-1',
          entity_type: 'CHARACTER',
          name: 'Pending',
          description: '',
          confidence: 0.8,
          source_text: '',
          chapter_id: 'ch-1',
          status: 'PENDING',
          created_at: '2024-01-01T00:00:00Z',
        };

        const approvedSuggestion: EntitySuggestion = {
          ...pendingSuggestion,
          id: 'sug-2',
          status: 'APPROVED',
        };

        act(() => {
          useCodexStore.getState().setSuggestions([pendingSuggestion, approvedSuggestion]);
        });

        const count = useCodexStore.getState().getPendingSuggestionsCount();
        expect(count).toBe(1);
      });

      it('should return 0 when no pending suggestions', () => {
        const count = useCodexStore.getState().getPendingSuggestionsCount();
        expect(count).toBe(0);
      });
    });

    describe('getEntitiesByType', () => {
      it('should filter entities by type', () => {
        const character: Entity = {
          id: 'entity-1',
          manuscript_id: 'ms-1',
          type: 'CHARACTER',
          name: 'John',
          description: '',
          aliases: [],
          attributes: {},
          first_appearance_chapter: 1,
          is_auto_detected: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };

        const location: Entity = {
          ...character,
          id: 'entity-2',
          type: 'LOCATION',
          name: 'Castle',
        };

        act(() => {
          useCodexStore.getState().setEntities([character, location]);
        });

        const characters = useCodexStore.getState().getEntitiesByType('CHARACTER');
        expect(characters).toHaveLength(1);
        expect(characters[0].name).toBe('John');

        const locations = useCodexStore.getState().getEntitiesByType('LOCATION');
        expect(locations).toHaveLength(1);
        expect(locations[0].name).toBe('Castle');
      });
    });

    describe('getEntityRelationships', () => {
      it('should return relationships involving entity', () => {
        const rel1: Relationship = {
          id: 'rel-1',
          manuscript_id: 'ms-1',
          source_entity_id: 'entity-1',
          target_entity_id: 'entity-2',
          relationship_type: 'friend',
          description: '',
          strength: 0.8,
          is_auto_detected: false,
          created_at: '2024-01-01T00:00:00Z',
        };

        const rel2: Relationship = {
          ...rel1,
          id: 'rel-2',
          source_entity_id: 'entity-3',
          target_entity_id: 'entity-1',
        };

        const rel3: Relationship = {
          ...rel1,
          id: 'rel-3',
          source_entity_id: 'entity-2',
          target_entity_id: 'entity-3',
        };

        act(() => {
          useCodexStore.getState().setRelationships([rel1, rel2, rel3]);
        });

        const entityRels = useCodexStore.getState().getEntityRelationships('entity-1');
        expect(entityRels).toHaveLength(2);
        expect(entityRels.map((r) => r.id)).toContain('rel-1');
        expect(entityRels.map((r) => r.id)).toContain('rel-2');
      });
    });
  });
});
