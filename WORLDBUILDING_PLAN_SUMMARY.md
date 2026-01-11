# Cross-Manuscript Worldbuilding System - Executive Summary

**Date:** 2026-01-10
**Status:** Plan Complete - Awaiting Approval
**Implementation Time:** 8-9 weeks

---

## 🎯 What This Enables

**Series authors can:**
- Create a "World" (e.g., "The Stormlight Archive", "Middle Earth")
- Share characters, locations, magic systems, and lore across multiple manuscripts
- Track character evolution over time automatically
- Ensure consistency across books with AI-powered validation

**The Magic:** Temporal state tracking means characters evolve naturally. Import "Gandalf" at Year 1500 → get Gandalf the Grey. Import at Year 3500 → get Gandalf the White. The system knows *when* in the timeline and gives you the right version.

---

## 📊 FEEDBACK.md Analysis

I've categorized all feedback items from FEEDBACK.md:

### 🐛 Bugs (5 items - Fix in Phase 7)
1. Outline summary text truncation
2. Outline Timeline tab not functioning
3. Outline Analytics tab not functioning
4. Outline beat navigation broken
5. Timeline event hover tooltip truncation

### ⚡ Enhancements (10 items - Phase 7 & 9)
1. Add scenes between outline beats
2. Fix Timeline Swimlanes character linking
3. Auto-generated commit messages in Time Machine
4. Editor toolbar cleanup (Scrivener-style)
5. More font options
6. Card view for chapters with summaries
7. Binder folder structure with doc types
8. Standardized brainstorm output
9. **Hover over entities to see state at that time** ⭐ (enabled by this plan)
10. Hover to create entities from text

### 🚀 New Features (4 items - Phase 8 & 9)
1. AI beat transition helper
2. Character sheets as standalone Library docs ✅ (THIS PLAN)
3. **Library with World/Series hierarchy** ✅ (THIS PLAN - CORE FEATURE)
4. Guided worldbuilding brainstorming (locations, creatures, magic, etc.)

**Key Finding:** Your FEEDBACK.md item "Brainstorm #2" is EXACTLY what this cross-manuscript worldbuilding system delivers!

---

## 🏗️ Core Design

### 1. Named Worlds
Create worlds like "The Stormlight Archive" or "Middle Earth" that contain:
- Characters (with temporal evolution)
- Locations
- Magic/Technology systems
- Lore and history
- Creatures

### 2. Temporal State Tracking (The Innovation)

Instead of version numbers, entities evolve through *time*:

```
Gandalf (World Entity)
├─ State 1 (Year 0 - 3000): Gandalf the Grey
│  └─ Power: 7, Abilities: [staff-combat, fire-magic]
└─ State 2 (Year 3000+): Gandalf the White
   └─ Power: 9, Abilities: [staff-combat, fire-magic, light-magic, banishment]
   └─ Change: "Reborn after defeating Balrog"
```

**Your manuscripts know "when" they occur:**
- Book 1 (Years 1000-1500): Gets Grey Gandalf
- Book 2 (Years 3500-4000): Gets White Gandalf
- **Automatic** - no manual version selection needed

### 3. Dedicated Magic/Tech Systems

Structured systems with:
- **Rules:** How magic works (hard/soft magic, tech specs)
- **Limitations:** What it can't do
- **Costs:** Resource consumption (mana, stamina, fuel)
- **Abilities:** Individual powers/techniques
- **Timeline Tracking:** When abilities were discovered/learned

**Consistency Validation:** Timeline Orchestrator checks:
- ❌ Character using ability before learning it
- ❌ Violating magic system rules (e.g., resurrection if forbidden)
- ❌ Using more mana than available

### 4. Auto-Documentation

As you write, Maxwell detects changes:
```
You write: "Gandalf defeats Balrog and transforms..."
↓
Maxwell: "Gandalf appears to have changed. Create state snapshot?"
↓
You: "Yes - he became Gandalf the White, power increased"
↓
All future books importing Gandalf after this point get the White version
```

---

## 🗄️ Database Schema (9 New Tables)

### Core Tables
1. **worlds** - World containers (name, description, timeline settings)
2. **world_manuscripts** - Links manuscripts to worlds with timeline positions
3. **world_entities** - Shared characters, locations, creatures, lore
4. **world_entity_states** ⭐ - Temporal snapshots of entity evolution
5. **manuscript_entity_links** - Tracks which manuscript entities link to world

### Magic System Tables
6. **magic_systems** - Magic/tech system definitions
7. **magic_abilities** - Individual abilities within systems
8. **character_abilities** - Which characters have which abilities (with timeline tracking)
9. **world_timeline_events** - Major cross-manuscript events

All backward compatible - existing manuscripts work unchanged.

---

## 🛣️ Implementation Plan (6 Phases)

### Phase 1: Core Infrastructure (2 weeks)
- Database schema + migration
- World CRUD (create, read, update, delete)
- Link manuscripts to worlds
- Basic World Dashboard UI

**Deliverable:** Authors can create worlds and link manuscripts

### Phase 2: Temporal State System (2 weeks)
- State resolution algorithm: `get_entity_at_time()`
- State merge logic
- Entity evolution API
- Visual timeline UI

**Deliverable:** "Give me Gandalf at Year 1500" works correctly

### Phase 3: Entity Import/Sync (1 week)
- Import entities from world into manuscripts
- Time-aware entity browser
- Sync modes (read-only, bidirectional, write-back)

**Deliverable:** Authors can import characters with correct temporal state

### Phase 4: Magic Systems (2 weeks)
- Magic system builder
- Abilities and character assignment
- Temporal ability tracking
- Template library

**Deliverable:** Define magic systems with rules, grant abilities to characters

### Phase 5: Timeline Integration (1-2 weeks)
- Validator 6: World consistency checks
- Validator 7: Magic system rule validation
- Auto-detect state changes
- Teaching moments

**Deliverable:** Timeline catches inconsistencies across manuscripts

### Phase 6: Polish & Templates (1 week)
- Magic system templates (hard magic, soft magic, tech)
- World timeline visualization
- Performance optimization
- Documentation

**Deliverable:** Production-ready with smooth UX

---

## 📁 Critical Files

### Backend (New)
- `/backend/app/models/world.py`
- `/backend/app/models/magic_system.py`
- `/backend/app/services/world_service.py` (core logic)
- `/backend/app/services/magic_service.py`
- `/backend/app/api/routes/worlds.py`
- `/backend/app/api/routes/magic_systems.py`
- Migration: `/backend/migrations/versions/xxx_add_world_tables.py`

### Backend (Modified)
- `/backend/app/services/timeline_service.py` (add validators)

### Frontend (New)
- `/frontend/src/components/Worlds/WorldDashboard.tsx`
- `/frontend/src/components/Worlds/WorldEntityBrowser.tsx`
- `/frontend/src/components/Worlds/EntityStateTimeline.tsx`
- `/frontend/src/components/MagicSystem/SystemBuilder.tsx`
- `/frontend/src/stores/worldStore.ts`
- `/frontend/src/stores/magicStore.ts`

### Frontend (Modified)
- `/frontend/src/components/Codex/EntityList.tsx` (add import button)
- `/frontend/src/components/Timeline/TimelineView.tsx` (show world conflicts)

---

## 🗺️ Roadmap Integration

**Current Status:**
- Phase 1-3: ✅ Complete (MVP, Codex, AI)
- Phase 4: 🔄 70% (Story Structure)
- Phase 5: 🔄 40% (Brainstorming)
- Phase 6: ✅ Complete (Timeline Orchestrator)

**Proposed:**

### Phase 7: Bug Fixes & Polish (1 week) - Feb 2026
Fix all FEEDBACK.md bugs before adding features

### Phase 8: Cross-Manuscript Worldbuilding (8-9 weeks) - Mar-Apr 2026
**THIS PLAN** - Named Worlds, Temporal States, Magic Systems

### Phase 9: Enhanced Brainstorming & Binder (2-3 weeks) - May 2026
- AI beat transition helper
- Scenes between beats
- Card view, folder structure
- Guided worldbuilding brainstorming

### Phase 10: PLG Features
(Original Phase 7 - timeline maintained)

---

## ✅ Success Metrics

**Phase 8 will succeed when:**

1. ✅ Author creates world and links 3 manuscripts at different timeline positions
2. ✅ Character imported into Book 2 shows evolved state from Book 1
3. ✅ Magic system with 5+ abilities validates correctly
4. ✅ Entity browser resolves 100 entities at specific time in <1 second
5. ✅ Temporal state changes auto-detected with 80%+ accuracy
6. ✅ 90% complete "Create World → Import Entity → Grant Ability" without help

**Target User Testimonial:**
> "I'm writing a 5-book series and Maxwell tracks my characters' evolution across all books. When I import Kelsier into Book 2, Maxwell knows he has Steel Pushing because he learned it in Book 1. The magic system validation caught me using Allomancy inconsistently - saved me from a major plot hole!"

---

## 🎨 Key User Flows

### Creating a World
```
Dashboard → Worlds → Create World
├─ Name: "The Stormlight Archive"
├─ Timeline: Years (0 = Ancient times)
└─ Create

World Dashboard
├─ Entities tab (characters, locations, creatures)
├─ Magic Systems tab
├─ Timeline tab (world events)
└─ Manuscripts tab (linked books)
```

### Importing a Character
```
Writing Book 2 (Year 3500-4000)
├─ Codex → Import from World
├─ Browse: Filter by CHARACTER, search "Kaladin"
├─ Time slider: Set to Year 3500
├─ Preview: Shows evolved Kaladin (now has Full Lashing ability)
├─ Import → Sync mode: Read-only
└─ Result: Kaladin appears in Codex with world link indicator
```

### Auto-Documentation Flow
```
Writing: "After the battle, Kaladin mastered Full Lashing"
↓
Timeline Orchestrator detects change
↓
Prompt: "Kaladin gained new ability. Create state snapshot?"
├─ Ability: Full Lashing (from Stormlight magic system)
├─ Gained at: Year 3542 (current event time)
├─ Mastery: Level 8
└─ Save

Future manuscripts after Year 3542 automatically see Kaladin with this ability
```

---

## 🔄 Integration with Existing Systems

### Timeline Orchestrator
**New Validators:**
- **Validator 6:** World Consistency (entity lifecycle, ability timing)
- **Validator 7:** Magic Rules (costs, limitations, resurrections)

**Extended Metadata:**
```json
{
  "abilities_used": ["steel-push", "soothing"],
  "magic_cost_consumed": {"stamina": 50, "mana": 30},
  "entity_state_changes": [{"entity": "frodo", "change": "gained_ring"}]
}
```

### Codex
- Add "Import from World" button
- World-linked entities show special indicator
- Entity details show timeline evolution graph
- Quick reference hover shows state at current time

### Brainstorming
- Generate entities directly into worlds
- Magic system templates for ideation
- Character brainstorming creates world entities

---

## 🤔 What This DOESN'T Include

These are separate phases (from FEEDBACK.md):

**Phase 7 (Bug Fixes):**
- Outline tab fixes
- Timeline tooltip fixes
- UI truncation issues

**Phase 9 (Binder Enhancements):**
- Card view for chapters
- Folder structure with doc types
- AI beat transitions
- Scenes between beats

**Future:**
- Export/import worlds between users
- Collaborative worldbuilding
- World version control
- Mobile app

---

## 💬 Questions or Concerns?

**Common Questions:**

**Q: Is this too complex for new users?**
A: Opt-in design. Worlds are hidden until you create one. Single-manuscript authors never see it.

**Q: Performance with large worlds?**
A: Caching, indexes, lazy loading. Target: 100 entities resolved in <1 second.

**Q: What if I change something in Book 1 after publishing Book 2?**
A: State versioning supports retroactive changes. System can show warnings about downstream effects.

**Q: Can I have alternate timelines (what-ifs)?**
A: Yes! `is_canonical` flag supports alternate timelines and non-canon stories.

---

## 📝 Next Steps

1. ✅ Review this summary
2. ⏳ Confirm you want to proceed with this design
3. ⏳ Start Phase 1 implementation (World Infrastructure)

**Full detailed plan:** `/Users/josephrodden/.claude/plans/zippy-puzzling-valley.md`

---

**Ready to build?** Just confirm and we'll start with Phase 1! 🚀
