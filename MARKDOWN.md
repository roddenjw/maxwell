# MAXWELL DESIGN SYSTEM

**Version:** 1.0
**Brand Archetype:** The Ruthless Editor / The Literary Architect
**Vibe:** Professional, Classic, Distraction-Free, Authoritative, Warm.

---

## 1. COLOR PALETTE (The "Study" Theme)

_Use these exact hex codes to maintain the "Classic Literary" aesthetic._

### Primary Backgrounds (The Page)

- **Aged Vellum (Main Canvas):** `#F9F7F1`
  - _Usage:_ The main writing area. Not stark white, but a soft, paper-like cream that reduces eye strain.
- **Clean Slate (Secondary/Sidebar):** `#E2E8F0`
  - _Usage:_ Sidebars, settings menus, and neutral areas.
- **Pure White (Input Backgrounds):** `#FFFFFF`
  - _Usage:_ Only for active input fields or "cards" that need to pop off the Vellum background

### Text & Accents (The Ink)

- **Midnight Ink (Primary Text):** `#1E293B` (Dark Slate Blue/Black)
  - _Usage:_ All body text, primary headers. Avoid pure black (#000000).
- **Faded Ink (Secondary Text):** `#64748B`
  - _Usage:_ UI labels, timestamps, placeholders.

### Brand Accents (The Finish)

- **Bronze Accent (Primary Action):** `#B48E55` (Muted Gold/Bronze)
  - _Usage:_ Primary buttons, active states, links, highlighting the "current chapter."
- **Leatherbound (Dark Accent):** `#451a03` (Deep Brown)
  - _Usage:_ Hover states for buttons, footer backgrounds.
- **Redline (Error/Editing):** `#9F1239` (Deep Rose)
  - _Usage:_ Critical errors or "suggested deletion" highlights.

---

## 2. TYPOGRAPHY

_We mix a classic serif for authority with a clean sans-serif for UI utility._

### Primary Serif (Headlines & Long-form Writing)

- **Family:** "EB Garamond", "Garamond", "Georgia", serif.
- **Usage:**
  - The Logo ("MAXWELL")
  - All H1, H2, H3 headers.
  - The user's actual writing content (the book).
- **Weight:** Bold (700) for Headers, Regular (400) for body text.

### Secondary Sans-Serif (UI & Navigation)

- **Family:** "Inter", "Helvetica Neue", "Arial", sans-serif.
- **Usage:**
  - Sidebar menus ("Chapter 1", "Settings").
  - Button text.
  - Tooltips and popups.
- **Weight:** Medium (500) for better readability on small UI text.

---

## 3. UI COMPONENT SPECS

### Buttons

- **Primary Button ("The Bronze Stamp"):**
  - Background: Bronze Accent (`#B48E55`)
  - Text: White (`#FFFFFF`)
  - Font: Sans-Serif, Uppercase, Tracking (Letter-spacing) `0.05em`.
  - Border-Radius: `2px` (Sharp, not rounded. Feels like a book spine).
- **Secondary Button ("The Ghost"):**
  - Background: Transparent.
  - Border: 1px Solid Midnight Ink (`#1E293B`).
  - Text: Midnight Ink.

### The "Editor" (Text Input Area)

- **Shadow:** None (Flat design).
- **Padding:** Large margins (mimic a physical book page). `padding: 4rem`.
- **Line-Height:** Relaxed. `1.8` (Standard is 1.5, we want 1.8 for readability).
- **Cursor:** Bronze (`#B48E55`).

### Layout Structure

- **The Sidebar (Left):** Fixed width (`280px`). Background: Clean Slate. Border-Right: 1px solid `#CBD5E1`.
- **The Desk (Center):** Fluid width. Background: Aged Vellum.
- **The Inspector (Right - Collapsible):** For "Maxwell's Advice". Background: White. Border-Left: 1px solid `#CBD5E1`.

---

## 4. TAILWIND CONFIG EXTENSION

_If using Tailwind CSS, add this to `tailwind.config.js`_

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        vellum: "#F9F7F1",
        midnight: "#1E293B",
        bronze: "#B48E55",
        "bronze-dark": "#8D6E42",
        "slate-ui": "#E2E8F0",
      },
      fontFamily: {
        serif: ['"EB Garamond"', "Georgia", "serif"],
        sans: ["Inter", '"Helvetica Neue"', "sans-serif"],
      },
      boxShadow: {
        book: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
      },
    },
  },
};
```
