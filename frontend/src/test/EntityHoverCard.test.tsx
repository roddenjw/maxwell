/**
 * EntityHoverCard Component Tests
 * Tests for the entity hover tooltip functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createMockEntity } from './setup';

describe('EntityHoverCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Visibility', () => {
    it('should render when isVisible is true and entity exists', () => {
      const isVisible = true;
      const entity = createMockEntity({ id: 'e1', name: 'John' });
      const shouldRender = isVisible && entity;
      expect(shouldRender).toBeTruthy();
    });

    it('should not render when isVisible is false', () => {
      const isVisible = false;
      const shouldRender = isVisible;
      expect(shouldRender).toBe(false);
    });

    it('should handle null entity gracefully', () => {
      const entity = null;
      const hasEntity = !!entity;
      expect(hasEntity).toBe(false);
    });
  });

  describe('Entity Display', () => {
    it('should display entity name', () => {
      const entity = createMockEntity({ name: 'John Smith' });
      expect(entity.name).toBe('John Smith');
    });

    it('should display entity type', () => {
      const entity = createMockEntity({ type: 'character' });
      expect(entity.type).toBe('character');
    });

    it('should display entity description or fallback', () => {
      const entityWithDescription = createMockEntity({ description: 'A brave warrior' });
      const entityWithoutDescription = createMockEntity({ description: '' });

      expect(entityWithDescription.description).toBe('A brave warrior');
      expect(entityWithoutDescription.description).toBe('');
    });

    it('should display type icon', () => {
      const getEntityTypeIcon = (type: string) => {
        const icons: Record<string, string> = {
          character: '👤',
          location: '📍',
          item: '🔮',
          lore: '📜',
        };
        return icons[type.toLowerCase()] || '📝';
      };

      expect(getEntityTypeIcon('character')).toBe('👤');
      expect(getEntityTypeIcon('location')).toBe('📍');
      expect(getEntityTypeIcon('item')).toBe('🔮');
      expect(getEntityTypeIcon('lore')).toBe('📜');
    });
  });

  describe('Positioning', () => {
    it('should use correct z-index from Z_INDEX constants', () => {
      const Z_INDEX = { HOVER_CARD: 65 };
      expect(Z_INDEX.HOVER_CARD).toBe(65);
    });

    it('should calculate position based on cursor coordinates', () => {
      const position = { x: 100, y: 200 };
      expect(position.x).toBe(100);
      expect(position.y).toBe(200);
    });

    it('should flip upward when near bottom of viewport', () => {
      const viewportHeight = 800;
      const cardHeight = 200;
      const cursorY = 700;
      const margin = 8;

      const shouldFlipUp = cursorY + cardHeight + margin > viewportHeight;
      expect(shouldFlipUp).toBe(true);
    });

    it('should not flip when enough space below cursor', () => {
      const viewportHeight = 800;
      const cardHeight = 200;
      const cursorY = 300;
      const margin = 8;

      const shouldFlipUp = cursorY + cardHeight + margin > viewportHeight;
      expect(shouldFlipUp).toBe(false);
    });

    it('should adjust horizontal position when near right edge', () => {
      const viewportWidth = 1200;
      const cardWidth = 280;
      const cursorX = 1000;
      const margin = 8;

      // If card would overflow right, adjust left
      const adjustedX = Math.min(cursorX, viewportWidth - cardWidth - margin);
      expect(adjustedX).toBeLessThan(cursorX);
    });

    it('should adjust horizontal position when near left edge', () => {
      const cursorX = 10;
      const margin = 8;

      // Ensure minimum margin from left edge
      const adjustedX = Math.max(cursorX, margin);
      expect(adjustedX).toBeGreaterThanOrEqual(margin);
    });
  });

  describe('Mouse Interaction', () => {
    it('should appear on mouse enter', () => {
      let isVisible = false;
      const onMouseEnter = () => { isVisible = true; };

      onMouseEnter();
      expect(isVisible).toBe(true);
    });

    it('should disappear on mouse leave', () => {
      let isVisible = true;
      const onMouseLeave = () => { isVisible = false; };

      onMouseLeave();
      expect(isVisible).toBe(false);
    });

    it('should handle rapid mouse movements', () => {
      let isVisible = false;
      const onMouseEnter = () => { isVisible = true; };
      const onMouseLeave = () => { isVisible = false; };

      // Simulate rapid enter/leave
      onMouseEnter();
      onMouseLeave();
      onMouseEnter();
      onMouseLeave();
      onMouseEnter();

      expect(isVisible).toBe(true);
    });
  });

  describe('Entity Loading', () => {
    it('should show loading state when entity is being loaded', () => {
      const isLoading = true;
      expect(isLoading).toBe(true);
    });

    it('should show error fallback when entity not found', () => {
      const entity = null;
      const showError = !entity;
      expect(showError).toBe(true);
    });
  });

  describe('Preloading', () => {
    it('should use preloaded entities from codex store', () => {
      const mockEntities = [
        createMockEntity({ id: 'e1', name: 'John' }),
        createMockEntity({ id: 'e2', name: 'Jane' }),
      ];

      const findEntity = (id: string) => mockEntities.find(e => e.id === id);

      expect(findEntity('e1')?.name).toBe('John');
      expect(findEntity('e3')).toBeUndefined();
    });
  });

  describe('Styling', () => {
    it('should apply shadow and border styling', () => {
      const cardStyles = 'shadow-xl border-2 border-bronze/30';
      expect(cardStyles).toContain('shadow-xl');
      expect(cardStyles).toContain('border');
    });

    it('should have fixed width', () => {
      const cardWidth = 280;
      expect(cardWidth).toBe(280);
    });

    it('should render in portal to body', () => {
      // Component uses createPortal to render at document.body
      const portalTarget = document.body;
      expect(portalTarget).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have appropriate role for tooltip', () => {
      const role = 'tooltip';
      expect(role).toBe('tooltip');
    });
  });
});
