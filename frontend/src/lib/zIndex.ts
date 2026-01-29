/**
 * Centralized Z-Index Hierarchy
 *
 * This module provides a consistent z-index system across the application
 * to prevent overlapping UI issues and ensure proper layering.
 *
 * Layer order (lowest to highest):
 * 1. BASE - Default content layer
 * 2. EDITOR_CONTENT - Editor elements
 * 3. SIDEBAR - Side navigation panels
 * 4. COMPANION_PANEL - Pop-out companion panels (Codex mini, Coach mini)
 * 5. SLIDE_PANEL - Slide-in panels (AI Suggestions)
 * 6. MODAL_BACKDROP - Modal overlay background
 * 7. MODAL - Modal dialogs
 * 8. DROPDOWN - Dropdown menus and popovers
 * 9. TOOLTIP - Tooltips
 * 10. HOVER_CARD - Entity hover cards
 * 11. TOAST - Toast notifications (always on top)
 */

export const Z_INDEX = {
  /** Default content layer */
  BASE: 0,

  /** Editor elements (toolbar, content blocks) */
  EDITOR_CONTENT: 10,

  /** Side navigation panels */
  SIDEBAR: 20,

  /** Pop-out companion panels (Codex mini, Coach mini, etc.) */
  COMPANION_PANEL: 25,

  /** Slide-in panels (AI Suggestions panel) */
  SLIDE_PANEL: 30,

  /** Modal overlay background */
  MODAL_BACKDROP: 40,

  /** Modal dialogs */
  MODAL: 45,

  /** Dropdown menus and popovers */
  DROPDOWN: 55,

  /** Tooltips */
  TOOLTIP: 60,

  /** Entity hover cards */
  HOVER_CARD: 65,

  /** Toast notifications (always visible) */
  TOAST: 70,
} as const;

export type ZIndexKey = keyof typeof Z_INDEX;
export type ZIndexValue = (typeof Z_INDEX)[ZIndexKey];
