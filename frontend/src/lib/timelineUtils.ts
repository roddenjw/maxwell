/**
 * Timeline utility functions for adaptive scaling
 */

export type ManuscriptScale = 'short' | 'medium' | 'long';

export interface LayoutConfig {
  nodeSpacing: number;
  eventSpacing: number;  // For timeline graph horizontal/vertical spacing
  fontSize: number;
  showAllLabels: boolean;
  graphHeight: number;
  heatmapCells: 'all' | 'sample' | 'aggregated';
  nodeRadius: number;
  edgeThickness: number;
}

/**
 * Determine manuscript scale based on number of timeline events
 */
export function getManuscriptScale(eventCount: number): ManuscriptScale {
  if (eventCount < 20) return 'short';      // Short story
  if (eventCount < 100) return 'medium';    // Novella
  return 'long';                             // Novel
}

/**
 * Get layout configuration for a given scale
 */
export function getLayoutConfig(scale: ManuscriptScale): LayoutConfig {
  const LAYOUT_CONFIGS: Record<ManuscriptScale, LayoutConfig> = {
    short: {
      nodeSpacing: 150,      // More space between events
      eventSpacing: 150,     // More space in timeline view
      fontSize: 14,          // Larger text
      showAllLabels: true,   // Show all event labels
      graphHeight: 400,
      heatmapCells: 'all',   // Show all emotion cards
      nodeRadius: 20,        // Larger nodes
      edgeThickness: 1.5     // Thicker edges
    },
    medium: {
      nodeSpacing: 100,
      eventSpacing: 100,
      fontSize: 12,
      showAllLabels: false,  // Show only important labels
      graphHeight: 500,
      heatmapCells: 'sample', // Show representative sample
      nodeRadius: 15,
      edgeThickness: 1.2
    },
    long: {
      nodeSpacing: 60,       // Condensed view
      eventSpacing: 60,
      fontSize: 10,
      showAllLabels: false,  // Minimal labels
      graphHeight: 600,
      heatmapCells: 'aggregated', // Show aggregated patterns
      nodeRadius: 12,        // Smaller nodes
      edgeThickness: 1.0     // Thinner edges
    }
  };

  return LAYOUT_CONFIGS[scale];
}

/**
 * Get scale display information
 */
export function getScaleInfo(scale: ManuscriptScale): { icon: string; label: string; description: string } {
  const SCALE_INFO: Record<ManuscriptScale, { icon: string; label: string; description: string }> = {
    short: {
      icon: '📖',
      label: 'Short Story',
      description: 'Showing all events in detail'
    },
    medium: {
      icon: '📚',
      label: 'Novella',
      description: 'Showing important events'
    },
    long: {
      icon: '📕',
      label: 'Novel',
      description: 'Condensed view for readability'
    }
  };

  return SCALE_INFO[scale];
}
