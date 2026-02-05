# Maxwell Unified World Wiki - Implementation Plan

**Date:** February 4, 2026
**Version:** 1.0
**Status:** Architecture & Implementation Plan

---

## 1. Vision: The Interconnected Narrative Backbone

### Current Problem
Maxwell's features are **disparate and scattered**:
- Codex entities live at manuscript level
- Voice analysis is standalone
- Foreshadowing tracking is separate
- Timeline validation doesn't know about world rules
- No unified place for "how this world works"

### Solution: World Wiki
A **living, interconnected knowledge base** that:
1. Lives at **World/Series level** (shared across manuscripts)
2. **Auto-populates** from manuscript analysis
3. **Manually editable** by authors
4. **AI-updated** with approval queue
5. **Referenced by ALL agents** for consistency checking
6. **Visualizes character arcs** integrated with outline

```
┌─────────────────────────────────────────────────────────────────┐
│                         WORLD WIKI                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Characters │  │  Locations  │  │ World Rules │              │
│  │  + Arcs     │  │  + History  │  │ + Magic     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                    ┌─────▼─────┐                                 │
│                    │ CONSISTENCY│                                │
│                    │   ENGINE   │                                │
│                    └─────┬─────┘                                 │
│                          │                                       │
│    ┌─────────────────────┼─────────────────────┐                │
│    ▼                     ▼                     ▼                │
│ ┌──────────┐      ┌──────────┐          ┌──────────┐           │
│ │  Voice   │      │ Timeline │          │Foreshadow│           │
│ │ Analyzer │      │Validator │          │ Tracker  │           │
│ └──────────┘      └──────────┘          └──────────┘           │
│                                                                  │
│                    ┌─────────────┐                              │
│                    │   AGENTS    │◄── All agents query Wiki     │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. World Wiki Architecture

### 2.1 Wiki Entry Types

```python
class WikiEntryType(Enum):
    # Characters
    CHARACTER = "character"
    CHARACTER_ARC = "character_arc"
    CHARACTER_RELATIONSHIP = "character_relationship"

    # Locations
    LOCATION = "location"
    LOCATION_HISTORY = "location_history"

    # World Rules
    MAGIC_SYSTEM = "magic_system"
    WORLD_RULE = "world_rule"
    TECHNOLOGY = "technology"
    CULTURE = "culture"
    RELIGION = "religion"

    # Narrative Elements
    FACTION = "faction"
    ARTIFACT = "artifact"
    CREATURE = "creature"
    EVENT = "event"  # Historical events

    # Meta
    TIMELINE_FACT = "timeline_fact"
    THEME = "theme"
```

### 2.2 Database Schema

```python
class WikiEntry(Base):
    """Core wiki entry - the building block of the World Wiki"""
    __tablename__ = "wiki_entries"

    id = Column(String, primary_key=True)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    # Entry metadata
    entry_type = Column(String, nullable=False)  # WikiEntryType
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False)  # URL-friendly: "john-smith"

    # Content (structured JSON for type-specific fields + free-form)
    structured_data = Column(JSON, default=dict)  # Type-specific fields
    content = Column(Text)  # Free-form markdown content
    summary = Column(Text)  # AI-generated summary

    # Linking
    parent_id = Column(String, ForeignKey("wiki_entries.id"))  # Hierarchical
    linked_entity_id = Column(String, ForeignKey("entities.id"))  # Codex link

    # Source tracking
    source_manuscripts = Column(JSON, default=list)  # Which manuscripts reference this
    source_chapters = Column(JSON, default=list)  # Specific chapters

    # Status
    status = Column(String, default="draft")  # draft, published, archived
    confidence_score = Column(Float, default=1.0)  # How confident is the data
    last_verified_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(String)  # "ai" or "author"


class WikiChange(Base):
    """Pending changes from AI that need author approval"""
    __tablename__ = "wiki_changes"

    id = Column(String, primary_key=True)
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)

    # Change details
    change_type = Column(String)  # "create", "update", "merge", "delete"
    field_changed = Column(String)  # Which field, or "full" for new entry
    old_value = Column(JSON)
    new_value = Column(JSON)

    # AI reasoning
    reason = Column(Text)  # Why AI suggests this change
    source_text = Column(Text)  # The manuscript text that triggered this
    source_chapter_id = Column(String)
    confidence = Column(Float)

    # Status
    status = Column(String, default="pending")  # pending, approved, rejected
    reviewed_at = Column(DateTime)
    reviewer_note = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class CharacterArc(Base):
    """Character arc tracking - links to wiki and outline"""
    __tablename__ = "character_arcs"

    id = Column(String, primary_key=True)
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Arc template
    arc_template = Column(String)  # "redemption", "fall", "coming_of_age", etc.

    # Planned arc (author's intention)
    planned_arc = Column(JSON, default=dict)
    # {
    #   "starting_state": "Selfish loner",
    #   "catalyst": "Meets orphan who needs help",
    #   "midpoint_shift": "Begins caring about others",
    #   "dark_moment": "Betrays new friends for old habits",
    #   "resolution": "Sacrifices self for community",
    #   "ending_state": "Selfless hero"
    # }

    # Detected arc (from manuscript analysis)
    detected_arc = Column(JSON, default=dict)
    # Same structure, but populated by AI analysis

    # Arc beats linked to outline
    arc_beats = Column(JSON, default=list)
    # [
    #   {"beat_id": "...", "arc_stage": "catalyst", "chapter_id": "..."},
    #   ...
    # ]

    # Tracking
    arc_completion = Column(Float, default=0.0)  # 0-1 based on beats hit
    arc_deviation_notes = Column(Text)  # Where actual differs from planned

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class WorldRule(Base):
    """Specific rules the world must follow - for validation"""
    __tablename__ = "world_rules"

    id = Column(String, primary_key=True)
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    # Rule definition
    rule_type = Column(String)  # "magic", "physics", "social", "temporal"
    rule_name = Column(String, nullable=False)
    rule_description = Column(Text)

    # For validation
    validation_pattern = Column(Text)  # Regex or keyword pattern
    validation_keywords = Column(JSON, default=list)  # Words that trigger check
    exception_keywords = Column(JSON, default=list)  # Words that exempt

    # Examples
    valid_examples = Column(JSON, default=list)
    violation_examples = Column(JSON, default=list)

    # Status
    is_active = Column(Integer, default=1)
    severity = Column(String, default="warning")  # "error", "warning", "info"

    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.3 Wiki Cross-References

```python
class WikiCrossReference(Base):
    """Links between wiki entries"""
    __tablename__ = "wiki_cross_references"

    id = Column(String, primary_key=True)
    source_entry_id = Column(String, ForeignKey("wiki_entries.id"))
    target_entry_id = Column(String, ForeignKey("wiki_entries.id"))

    reference_type = Column(String)
    # "mentions", "related_to", "part_of", "conflicts_with",
    # "depends_on", "child_of", "ally_of", "enemy_of"

    context = Column(Text)  # Where/why this reference exists
    bidirectional = Column(Integer, default=1)  # Show on both entries?

    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 3. Integration Points

### 3.1 Wiki ↔ Codex Integration

The Codex becomes a **manuscript-level view** into the World Wiki:

```python
class WikiCodexBridge:
    """
    Bridges manuscript Codex entities to World Wiki entries.

    - When entity created in Codex → Creates/links to Wiki entry
    - When Wiki entry updated → Updates linked Codex entities
    - Entities can override Wiki data for manuscript-specific needs
    """

    def sync_entity_to_wiki(self, entity: Entity) -> WikiEntry:
        """Create or update wiki entry from Codex entity"""

    def sync_wiki_to_entity(self, wiki_entry: WikiEntry, manuscript_id: str) -> Entity:
        """Create or update Codex entity from Wiki entry"""

    def get_manuscript_overrides(self, wiki_entry_id: str, manuscript_id: str) -> dict:
        """Get manuscript-specific overrides for a wiki entry"""
```

### 3.2 Wiki ↔ Outline Integration (Character Arcs)

```python
class CharacterArcService:
    """
    Integrates character arcs with outline plot beats.

    - Character arc templates map to story structure
    - Each character can have their own arc view of the outline
    - Tracks planned vs actual arc progression
    """

    # Arc Templates
    ARC_TEMPLATES = {
        "redemption": {
            "name": "Redemption Arc",
            "stages": ["flawed_state", "catalyst", "struggle", "dark_moment", "transformation", "redeemed_state"],
            "description": "Character moves from moral failing to redemption",
            "beat_mapping": {
                "three_act": {"flawed_state": "act_1", "catalyst": "inciting_incident", ...},
                "heros_journey": {"flawed_state": "ordinary_world", "catalyst": "call_to_adventure", ...}
            }
        },
        "fall": {
            "name": "Tragic Fall",
            "stages": ["noble_state", "temptation", "compromise", "corruption", "downfall"],
            ...
        },
        "coming_of_age": {
            "name": "Coming of Age",
            "stages": ["innocence", "challenge", "mentor", "trial", "growth", "maturity"],
            ...
        },
        "positive_change": {
            "name": "Positive Change Arc",
            "stages": ["lie_believed", "desire", "conflict", "truth_glimpsed", "truth_embraced"],
            ...
        },
        "flat_arc": {
            "name": "Flat Arc (Testing)",
            "stages": ["truth_known", "world_challenges", "truth_tested", "world_changed"],
            ...
        },
        "negative_change": {
            "name": "Negative Change Arc",
            "stages": ["truth_known", "temptation", "compromise", "lie_embraced", "destruction"],
            ...
        }
    }

    def create_character_arc(self, wiki_entry_id: str, manuscript_id: str, template: str) -> CharacterArc:
        """Create a character arc from template"""

    def map_arc_to_outline(self, arc_id: str, outline_id: str) -> List[dict]:
        """Map arc stages to outline beats"""

    def detect_arc_from_manuscript(self, wiki_entry_id: str, manuscript_id: str) -> dict:
        """Analyze manuscript to detect actual character arc"""

    def compare_arcs(self, arc_id: str) -> dict:
        """Compare planned arc to detected arc, return deviations"""
```

### 3.3 Wiki ↔ All Analyzers

```python
class WikiConsistencyEngine:
    """
    Central consistency engine that all analyzers use.

    Provides:
    - Character facts for voice analysis
    - World rules for timeline validation
    - Relationship status for continuity
    - Magic rules for world consistency
    """

    def get_character_facts(self, character_name: str, world_id: str) -> dict:
        """Get all known facts about a character"""
        # Used by: VoiceAnalyzer, ContinuityAgent, ConsistencyChecker

    def get_world_rules(self, world_id: str, rule_type: str = None) -> List[WorldRule]:
        """Get world rules for validation"""
        # Used by: TimelineValidator, WorldConsistencyChecker

    def get_relationship_state(self, char_a: str, char_b: str, at_chapter: str = None) -> dict:
        """Get relationship state, optionally at a specific point in story"""
        # Used by: ContinuityAgent, RelationshipTracker

    def get_location_facts(self, location_name: str, world_id: str) -> dict:
        """Get location details for consistency checking"""
        # Used by: TimelineValidator, TravelValidator

    def validate_against_rules(self, text: str, world_id: str) -> List[dict]:
        """Check text against all world rules"""
        # Used by: All analyzers
```

### 3.4 Wiki ↔ Agents

```python
class WikiAgentTools:
    """
    LangChain tools for agents to query the Wiki.
    """

    @tool
    def query_wiki(query: str, world_id: str, entry_type: str = None) -> str:
        """Search the World Wiki for information"""

    @tool
    def get_character_arc(character_name: str, manuscript_id: str) -> str:
        """Get a character's planned and detected arc"""

    @tool
    def check_world_rule(rule_name: str, text: str) -> str:
        """Check if text violates a world rule"""

    @tool
    def get_relationship_history(char_a: str, char_b: str) -> str:
        """Get the history of a relationship"""

    @tool
    def suggest_wiki_update(entry_id: str, field: str, new_value: str, reason: str) -> str:
        """Suggest an update to a wiki entry (goes to approval queue)"""
```

---

## 4. User Interface Components

### 4.1 World Wiki Browser

```typescript
// WorldWikiBrowser.tsx
// Lives in Library view at World level

interface WorldWikiBrowserProps {
  worldId: string;
}

// Features:
// - Sidebar with entry type categories
// - Search across all entries
// - Create new entries manually
// - View approval queue (pending AI changes)
// - Cross-reference graph visualization
// - Quick filters (characters, locations, rules, etc.)
```

### 4.2 Wiki Entry Editor

```typescript
// WikiEntryEditor.tsx
// Rich editor for wiki entries

interface WikiEntryEditorProps {
  entryId: string;
  mode: "view" | "edit";
}

// Features:
// - Structured fields based on entry type
// - Free-form content area (markdown)
// - Cross-reference linking (@ mentions)
// - Source tracking (which manuscripts reference this)
// - Version history
// - AI suggestion panel
```

### 4.3 Character Arc Designer

```typescript
// CharacterArcDesigner.tsx
// Visual arc planning and tracking

interface CharacterArcDesignerProps {
  characterWikiId: string;
  manuscriptId: string;
}

// Features:
// - Template selection with previews
// - Visual arc timeline
// - Drag beats to arc stages
// - Planned vs Detected comparison
// - Outline integration (shows which beats = which arc stages)
// - Deviation warnings
```

### 4.4 Change Approval Queue

```typescript
// WikiChangeQueue.tsx
// Review and approve AI suggestions

interface WikiChangeQueueProps {
  worldId: string;
}

// Features:
// - List of pending changes
// - Grouped by entry
// - Show diff (old vs new)
// - Show AI reasoning
// - Show source text that triggered change
// - Approve/Reject/Edit buttons
// - Bulk actions
```

### 4.5 Integrated Outline Character View

```typescript
// OutlineCharacterView.tsx
// Character-centric view of the outline

interface OutlineCharacterViewProps {
  outlineId: string;
  characterWikiId: string;
}

// Features:
// - Shows outline beats where character appears
// - Arc stage annotations on beats
// - Visual arc progression
// - Missing arc beats highlighted
// - Suggested scenes for arc completion
```

---

## 5. Auto-Population Pipeline

### 5.1 Manuscript Analysis → Wiki Updates

```python
class WikiAutoPopulator:
    """
    Analyzes manuscripts and suggests Wiki updates.
    All changes go to approval queue.
    """

    async def analyze_manuscript(self, manuscript_id: str) -> List[WikiChange]:
        """Full manuscript analysis for wiki updates"""

        # 1. Extract entities (existing NLP)
        entities = await self.extract_entities(manuscript_id)

        # 2. Extract relationships
        relationships = await self.extract_relationships(manuscript_id)

        # 3. Extract world rules (from exposition)
        rules = await self.extract_world_rules(manuscript_id)

        # 4. Detect character arcs
        arcs = await self.detect_character_arcs(manuscript_id)

        # 5. Extract location details
        locations = await self.extract_location_details(manuscript_id)

        # 6. Compare to existing Wiki entries
        # 7. Generate changes for new or updated info
        # 8. Add to approval queue

        return changes

    async def extract_world_rules(self, manuscript_id: str) -> List[dict]:
        """Extract world rules from exposition and dialogue"""
        # Look for patterns like:
        # "In this world, [rule]"
        # "The laws of [X] state that..."
        # "Magic requires..."
        # "No one can [X] without [Y]"
        # "[X] is impossible because..."
```

### 5.2 Incremental Updates

```python
class WikiIncrementalUpdater:
    """
    Updates wiki as author writes (real-time).
    """

    async def on_chapter_save(self, chapter_id: str):
        """Analyze chapter for wiki updates"""
        # Lightweight analysis
        # Queue significant changes for approval

    async def on_entity_created(self, entity: Entity):
        """Link new entity to wiki or create entry"""

    async def on_entity_updated(self, entity: Entity):
        """Propagate entity changes to wiki"""
```

---

## 6. Implementation Phases

### Phase 1: Wiki Foundation (Week 1-2)
**Goal:** Core wiki infrastructure

- [ ] Database models (WikiEntry, WikiChange, WorldRule, CharacterArc)
- [ ] Migration scripts
- [ ] WikiService CRUD operations
- [ ] WikiConsistencyEngine base
- [ ] API endpoints for wiki CRUD
- [ ] Basic WikiBrowser UI

### Phase 2: Codex Integration (Week 2-3)
**Goal:** Bridge existing Codex to Wiki

- [ ] WikiCodexBridge service
- [ ] Auto-create wiki entries from existing entities
- [ ] Sync mechanism (Codex ↔ Wiki)
- [ ] World-level entity view in Library
- [ ] Update Codex UI to show wiki link

### Phase 3: Character Arcs (Week 3-4)
**Goal:** Character arc system

- [ ] CharacterArc model and service
- [ ] Arc templates database (6+ templates)
- [ ] CharacterArcDesigner UI
- [ ] Outline integration (character view)
- [ ] Arc detection from manuscript (basic)
- [ ] Planned vs Detected comparison

### Phase 4: World Rules Engine (Week 4-5)
**Goal:** Custom rule validation

- [ ] WorldRule model and service
- [ ] Rule editor UI
- [ ] Pattern matching validation
- [ ] Integration with TimelineValidator
- [ ] Integration with ConsistencyChecker
- [ ] Violation reporting

### Phase 5: Auto-Population (Week 5-6)
**Goal:** AI-powered wiki updates

- [ ] WikiAutoPopulator service
- [ ] World rule extraction
- [ ] Relationship detection improvements
- [ ] Change approval queue
- [ ] WikiChangeQueue UI
- [ ] Incremental updates on save

### Phase 6: Agent Integration (Week 6-7)
**Goal:** All agents use Wiki

- [ ] WikiAgentTools (LangChain tools)
- [ ] Update all agents to query wiki
- [ ] Agent suggestions → approval queue
- [ ] Cross-referencing in agent responses

### Phase 7: Visualization & Polish (Week 7-8)
**Goal:** Visual tools and refinement

- [ ] Wiki graph visualization (entry relationships)
- [ ] Character arc timeline visualization
- [ ] Cross-reference network view
- [ ] Search improvements
- [ ] Bulk operations
- [ ] Export wiki to document

---

## 7. Integration with Existing Features

### Voice Consistency → Wiki
```python
# VoiceAnalysisService now queries Wiki for character voice expectations
character_wiki = wiki_service.get_character_facts(character_name, world_id)
expected_voice = character_wiki.get("voice_patterns", {})
# Compare detected voice to wiki-documented voice
```

### Foreshadowing → Wiki
```python
# Detected foreshadowing can be promoted to Wiki entries
wiki_service.create_entry(
    entry_type="timeline_fact",
    title="The prophecy of the three crowns",
    structured_data={"setup_chapter": "...", "payoff_chapter": "..."}
)
```

### Timeline → Wiki
```python
# Timeline validator checks against world rules
rules = wiki_service.get_world_rules(world_id, rule_type="travel")
# e.g., "Teleportation requires a trained mage"
# Validates travel events against these rules
```

### Outline → Wiki
```python
# Outline beats can be linked to character arc stages
arc = wiki_service.get_character_arc(character_id, manuscript_id)
beat_stage_mapping = arc.arc_beats
# Shows which beats fulfill which arc stages
```

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Wiki entries created | 50+ per world | Database count |
| Auto-populated entries | 70% of entries | Source tracking |
| Change approval rate | 80%+ approved | Approval queue stats |
| Arc completion tracking | 90% accuracy | Manual verification |
| Rule violation detection | 85% accuracy | Test suite |
| Agent wiki usage | 100% of queries | Agent logs |
| User engagement | 3+ wiki edits/session | Analytics |

---

## 9. File Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── wiki.py                 # WikiEntry, WikiChange, WikiCrossReference
│   │   ├── character_arc.py        # CharacterArc model
│   │   └── world_rule.py           # WorldRule model
│   ├── services/
│   │   ├── wiki_service.py         # Core wiki CRUD
│   │   ├── wiki_codex_bridge.py    # Codex ↔ Wiki sync
│   │   ├── wiki_consistency_engine.py  # Central consistency API
│   │   ├── wiki_auto_populator.py  # AI analysis → wiki
│   │   └── character_arc_service.py    # Arc management
│   ├── agents/
│   │   └── tools/
│   │       └── wiki_tools.py       # LangChain wiki tools
│   └── api/routes/
│       ├── wiki.py                 # Wiki CRUD endpoints
│       ├── wiki_changes.py         # Approval queue endpoints
│       └── character_arcs.py       # Arc endpoints

frontend/
└── src/
    └── components/
        ├── Wiki/
        │   ├── WorldWikiBrowser.tsx
        │   ├── WikiEntryEditor.tsx
        │   ├── WikiEntryCard.tsx
        │   ├── WikiSearch.tsx
        │   ├── WikiChangeQueue.tsx
        │   ├── WikiGraphView.tsx
        │   └── index.ts
        ├── CharacterArc/
        │   ├── CharacterArcDesigner.tsx
        │   ├── ArcTemplateSelector.tsx
        │   ├── ArcTimelineView.tsx
        │   ├── ArcComparisonView.tsx
        │   └── index.ts
        └── Outline/
            └── OutlineCharacterView.tsx  # New view
```

---

## 10. Summary

The World Wiki becomes the **unified backbone** that connects all Maxwell features:

1. **Single Source of Truth** - All character, location, and rule data lives here
2. **Auto-Populating** - AI extracts from manuscripts, author approves
3. **Manually Editable** - Authors can add/edit/organize
4. **World/Series Level** - Shared across manuscripts
5. **Powers All Analysis** - Every validator, analyzer, and agent queries it
6. **Character Arcs** - Integrated with outline, planned vs detected
7. **World Rules** - Custom validation rules for fantasy/sci-fi

This transforms Maxwell from a collection of features into an **integrated narrative intelligence system**.
