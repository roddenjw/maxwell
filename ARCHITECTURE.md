# Maxwell Architecture

**Last Updated:** 2026-02-08
**Related Docs:** [CLAUDE.md](CLAUDE.md) | [PATTERNS.md](PATTERNS.md) | [WORKFLOW.md](WORKFLOW.md)

---

## System Design Philosophy

**Vision:** Invisible engineering for fiction writers

Maxwell is a **local-first fiction writing IDE** with powerful features and zero complexity. Key principles:

- **Local-first:** SQLite database, no cloud dependency for core features
- **Async background processing:** NLP and AI analysis never blocks the editor
- **Git-backed version control:** Reliable snapshots without Git UX complexity
- **BYOK (Bring Your Own Key):** Users provide their own AI API keys, we charge zero markup
- **Maxwell Design System:** Vellum (warm cream), Bronze (copper accents), Midnight (deep text)
- **Teaching-first:** Tools educate writers about craft (e.g., Timeline Orchestrator teaches consistency)

---

## Tech Stack

### Backend (Python 3.13)
- **FastAPI 0.104+** - Async web framework
- **SQLAlchemy 2.0+** - ORM with declarative models
- **SQLite** - File-based database (PostgreSQL/MySQL ready)
- **Alembic** - Database migrations
- **pygit2** - Git integration for versioning
- **spaCy 3.8.11** - NLP for entity extraction
- **ChromaDB** - Vector embeddings (optional, Python 3.13 compatible version pending)

### Frontend (React 18 + TypeScript 5.2)
- **Vite 5.0** - Build tool and dev server
- **Lexical 0.12.5** - Rich text editor framework
- **Zustand 4.4.7** - Lightweight state management
- **TanStack Query 5.0** - Server state/caching (planned)
- **Tailwind CSS 3.4.0** - Utility-first styling
- **react-force-graph-2d** - Relationship graph visualization
- **Vis.js** - Timeline visualization

---

## Architecture Layers

### Backend: Three-Tier Pattern

```
Routes (API Layer)          →  backend/app/api/routes/*.py
  ↓ Call
Services (Business Logic)   →  backend/app/services/*.py
  ↓ Query/Persist
Models (Data Layer)         →  backend/app/models/*.py
  ↓ Store
Database (SQLite)           →  data/codex.db
```

**Simple Request Flow:**
```
POST /api/chapters
  → chapters.py route handler
    → Chapter model (manuscript.py)
      → SQLite via SQLAlchemy ORM
```

**Complex Feature Flow:**
```
POST /api/timeline/validate/{manuscript_id}
  → timeline.py route handler
    → timeline_service.validate_timeline_orchestrator()
      → Queries TimelineEvent, CharacterLocation, TravelLeg models
      → Runs 5 validators
      → Creates TimelineInconsistency records
        → Returns validation results to route
```

### Frontend: Component-Store-API Pattern

```
Components (UI)             →  frontend/src/components/[Feature]/
  ↓ Uses
Stores (State)              →  frontend/src/stores/*Store.ts
  ↓ Calls
API Client                  →  frontend/src/lib/api.ts
  ↓ HTTP
Backend Routes              →  backend/app/api/routes/
```

**Data Flow Example:**
```
EntityCard component
  → Uses codexStore.entities (Zustand)
    → codexStore.fetchEntities() calls codexApi.list()
      → HTTP GET /api/codex/entities/{manuscript_id}
        → Backend returns Entity[] JSON
          → codexStore.setEntities() updates state
            → EntityCard re-renders with new data
```

---

## Key Architectural Decisions

### ADR-001: Git-Based Version Control

**Context:** Writers need reliable version history without complex UX. System must work offline and handle large text files efficiently.

**Decision:** Use Git (via pygit2) with one repository per manuscript. Snapshots map to Git commits, diffs use `git diff`.

**Consequences:**
- ✅ Proven reliability (30+ years of Git)
- ✅ Powerful diff/merge capabilities
- ✅ Works offline, no external dependencies
- ✅ Familiar to developer users
- ⚠️ Requires learning Git internals for maintenance
- ⚠️ 20MB+ repos for long novels
- ⚠️ Limited to text (not binary assets)

**Implementation:**
- Service: `backend/app/services/version_service.py`
- Storage: `data/manuscripts/{manuscript_id}/.git`
- API: `/api/versioning/snapshots`

### ADR-002: Lexical JSON Storage

**Context:** Need rich text formatting without losing data when switching editors. Must support NLP analysis on plain text.

**Decision:** Store Lexical editor state as JSON string in `lexical_state` column. Extract plain text on save for search/NLP.

**Consequences:**
- ✅ Format-preserving (bold, italics, lists, etc.)
- ✅ Editor-agnostic JSON format
- ✅ Plain text extraction for NLP/search
- ⚠️ Large JSON payloads for long chapters
- ⚠️ Custom extraction logic required

**Implementation:**
- Models: `Chapter.lexical_state` (JSON string), `Chapter.content` (plain text)
- Extraction: `extract_text_from_lexical()` in chapters.py
- API: `/api/chapters` routes handle both formats

### ADR-003: ApiResponse<T> Pattern

**Context:** Need consistent API response format for error handling, loading states, and TypeScript type safety.

**Decision:** All API endpoints return standardized `ApiResponse<T>` structure.

**Format:**
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: any };
  meta?: { timestamp: string; version: string };
}
```

**Examples:**
```python
# Success
return {"success": True, "data": entity}

# Error
return {
    "success": False,
    "error": {
        "code": "NOT_FOUND",
        "message": "Entity not found",
        "details": {"entity_id": entity_id}
    }
}
```

### ADR-004: Background Task Processing

**Context:** NLP analysis and AI generation can take seconds. Cannot block the editor or API responses.

**Decision:** Use FastAPI `BackgroundTasks` for async processing. WebSocket for real-time updates (planned).

**Implementation:**
```python
@router.post("/analyze")
async def analyze_text(
    data: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        nlp_service.analyze_manuscript,
        data.manuscript_id
    )
    return {"success": True, "message": "Analysis started"}
```

### ADR-005: JSON Columns for Flexibility

**Context:** Features need flexible attributes without schema changes. Entity types have different fields (characters vs locations).

**Decision:** Use JSON columns for flexible storage: `settings`, `attributes`, `metadata`.

**Examples:**
- `Manuscript.settings` - Editor preferences, theme, auto-save interval
- `Entity.attributes` - Character age, appearance, location coordinates
- `TimelineEvent.event_metadata` - Word count, dialogue count, scene type
- `Relationship.relationship_metadata` - Duration, strength, conflict level

**Consequences:**
- ✅ Rapid feature iteration
- ✅ No migrations for new attributes
- ✅ Per-entity customization
- ⚠️ Harder to query/index
- ⚠️ No database-level validation

---

## Database Schema Overview

**Core Tables (15 total):**

```
manuscripts
├── chapters (hierarchical, Scrivener-like)
├── scenes
├── entities (characters, locations, items, lore)
│   ├── relationships (between entities)
│   └── entity_suggestions (NLP auto-detected)
├── timeline_events
│   ├── character_locations
│   ├── timeline_inconsistencies
│   ├── travel_legs (Timeline Orchestrator)
│   ├── location_distances
│   └── travel_speed_profiles
├── outlines (story structures)
│   └── plot_beats
├── brainstorm_sessions
│   └── brainstorm_ideas
└── snapshots (version control)
```

**Relationship Pattern:**
```
Manuscript (1)
  ├── Chapter (many) → parent_id self-reference for hierarchy
  ├── Entity (many)
  ├── TimelineEvent (many)
  ├── Outline (many) → PlotBeat (many)
  ├── BrainstormSession (many) → BrainstormIdea (many)
  └── Snapshot (many)
```

**Key Fields:**
- All IDs: UUID strings (e.g., `"c4ca4238-a0b9-3382-8dcc-509a6f75849b"`)
- Timestamps: `created_at`, `updated_at` (UTC datetime)
- JSON columns: `settings`, `attributes`, `metadata` (flexible storage)
- Cascades: `cascade="all, delete-orphan"` for related records

---

## LangChain Agent Framework

### Agent Architecture Overview

Maxwell uses a LangChain-based agent system for advanced writing assistance. The framework provides:

1. **Multi-Agent Writing Assistant** - Four specialized agents analyzing text in parallel
2. **Smart Coach** - Conversational coaching with memory and tool access
3. **Author Learning System** - Tracks preferences and improves over time

### Agent Hierarchy

```
backend/app/agents/
├── base/
│   ├── agent_base.py           # BaseMaxwellAgent class
│   ├── agent_config.py         # Configuration management
│   └── context_loader.py       # Hierarchical context loading
├── tools/                       # LangChain Tools (17 total)
│   ├── codex_tools.py          # Entity queries
│   ├── timeline_tools.py       # Timeline queries
│   ├── outline_tools.py        # Beat/structure queries
│   ├── manuscript_tools.py     # Chapter content queries
│   ├── world_tools.py          # World settings, rules
│   ├── series_tools.py         # Cross-book context
│   └── author_tools.py         # Author profile, learning
├── specialized/                 # Specialized Agents
│   ├── continuity_agent.py     # Character facts, timeline
│   ├── style_agent.py          # Prose quality
│   ├── structure_agent.py      # Story beats
│   ├── voice_agent.py          # Dialogue consistency
│   ├── consistency_agent.py    # Full consistency checking
│   └── research_agent.py       # Worldbuilding research
├── orchestrator/
│   ├── maxwell_unified.py      # PRIMARY ENTRY POINT - unified Maxwell persona
│   ├── supervisor_agent.py     # Intelligent query routing
│   ├── maxwell_synthesizer.py  # Unified voice synthesis
│   └── writing_assistant.py    # Multi-agent parallel execution
└── coach/
    └── smart_coach_agent.py    # Conversational coach (integrated with agents)
```

### Maxwell Unified Architecture

Maxwell presents as a **single cohesive entity** while internally delegating to specialized agents:

```
User Question: "Is this dialogue working?"
         │
         ▼
┌──────────────────────────────────────────────────────┐
│              MaxwellUnified                          │
│  (Single entry point for all interactions)          │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│              SupervisorAgent                         │
│  - Analyzes user intent                              │
│  - Routes to appropriate specialists                 │
│  - Fast routing for common patterns                  │
│  Returns: [VOICE, STYLE, CONTINUITY]                │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│          WritingAssistantOrchestrator               │
│  - Runs selected agents in parallel                  │
│  - Deduplicates findings                            │
│  - Aggregates costs                                  │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│             MaxwellSynthesizer                       │
│  - Transforms raw agent output into Maxwell's voice  │
│  - "I noticed..." not "The Style Agent found..."    │
│  - Prioritizes by impact, celebrates strengths      │
│  - Teaching-focused explanations                    │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│                 User Response                        │
│  "Your dialogue here is sharp - the rhythm feels    │
│  natural. I noticed one continuity issue though:    │
│  Sarah mentioned her blue eyes in Chapter 2, but..."│
└──────────────────────────────────────────────────────┘
```

**Key Principle**: Users interact with ONE entity (Maxwell) who speaks with a unified voice, while specialized expertise is applied behind the scenes.

### Context Hierarchy

Agents operate with a four-level context hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTHOR CONTEXT (Persistent across all work)                    │
│  - Writing style preferences, strengths, weaknesses             │
│  - Overused words/patterns, favorite techniques                 │
│  - Learning history (coaching patterns that worked)             │
├─────────────────────────────────────────────────────────────────┤
│  WORLD CONTEXT (Shared across universe)                         │
│  - World settings (genre, magic system, tech level)             │
│  - World-scoped entities, established rules                     │
├─────────────────────────────────────────────────────────────────┤
│  SERIES CONTEXT (Shared within series)                          │
│  - Plot threads and arcs across books                           │
│  - Character development, series timeline                       │
├─────────────────────────────────────────────────────────────────┤
│  MANUSCRIPT CONTEXT (Current work)                              │
│  - Chapters, scenes, current position                           │
│  - Manuscript-scoped entities, outline, local timeline          │
└─────────────────────────────────────────────────────────────────┘
```

### LLM Service Abstraction

```python
# Unified interface for multiple providers
llm_service.generate(
    config=LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-haiku-20240307",
        api_key=user_api_key,  # BYOK pattern
    ),
    messages=[...],
)
```

Supported providers:
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Anthropic**: Claude 3 Opus/Sonnet/Haiku
- **OpenRouter**: Access to 100+ models
- **Local**: llama-cpp-python for offline use

### Author Learning Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent generates │───►│ User responds   │───►│ System learns   │
│ suggestion      │    │ Accept/Reject/  │    │ Updates profile │
│                 │    │ Modify          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
                              ┌─────────────────────────────────┐
                              │ Future suggestions personalized │
                              │ - Style preferences applied     │
                              │ - Rejected patterns avoided     │
                              │ - Improvement tracking shown    │
                              └─────────────────────────────────┘
```

### Agent Database Models

```
agent_analyses         # Analysis results with recommendations
coach_sessions         # Coaching conversation sessions
coach_messages         # Individual messages in sessions
author_learning        # Learned preferences and patterns
suggestion_feedback    # User response to suggestions
```

---

## World Wiki: The Narrative Backbone

### Philosophy: Single Source of Truth

The **World Wiki** is the architectural foundation that unifies all Maxwell features. Rather than having disconnected analysis tools, the wiki serves as a **central knowledge graph** that:

1. **Stores all narrative facts** - Characters, locations, items, world rules, relationships
2. **Provides context to all agents** - Every AI query draws from wiki knowledge
3. **Enables consistency checking** - All validators reference the same truth source
4. **Supports auto-population** - AI extracts facts from writing and suggests wiki updates
5. **Lives at the World level** - Shared across manuscripts in a series/universe

### Why Wiki-Centric Architecture?

**Problem:** In competitive tools (Sudowrite, Novelcrafter), features feel "disparate and scattered." Character tracking, timeline validation, world rules, and AI assistance operate independently, leading to inconsistent suggestions and duplicated information.

**Solution:** The World Wiki acts as the **narrative backbone**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        WORLD WIKI                                │
│  (Single Source of Truth for all narrative elements)            │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  Characters  │ │  Locations   │ │    Items     │            │
│  │  - Facts     │ │  - Geography │ │  - Properties│            │
│  │  - Arcs      │ │  - Culture   │ │  - Lore      │            │
│  │  - Relations │ │  - History   │ │  - Rules     │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ World Rules  │ │ Relationships│ │   Factions   │            │
│  │  - Magic     │ │  - States    │ │  - Politics  │            │
│  │  - Physics   │ │  - Evolution │ │  - Alliances │            │
│  │  - Social    │ │  - Conflicts │ │  - Culture   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   AI Agents     │  │   Validators    │  │   Analyzers     │
│  - Continuity   │  │  - POV          │  │  - Pacing       │
│  - Style        │  │  - Timeline     │  │  - Subplots     │
│  - Voice        │  │  - Rules        │  │  - Beats        │
│  Query wiki for │  │  Check against  │  │  Reference wiki │
│  character facts│  │  wiki rules     │  │  for context    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Wiki Data Model

```
worlds
├── wiki_entries (characters, locations, items, factions, concepts, events)
│   ├── structured_data (JSON - type-specific fields)
│   ├── aliases (alternative names)
│   ├── tags (categorization)
│   └── confidence_score (AI vs human certainty)
├── world_rules (magic_system, physical_law, social_rule, cultural, temporal)
│   ├── validation_keywords (trigger detection)
│   ├── severity (error, warning, info)
│   └── examples (usage patterns)
├── character_arcs (per manuscript)
│   ├── arc_template (hero's journey, redemption, etc.)
│   ├── planned_arc vs detected_arc
│   └── arc_beats (mapped to chapters)
├── relationship_entries
│   ├── relationship_type (family, romantic, rival, etc.)
│   ├── state_history (evolution over time)
│   └── wiki_consistency_link
└── wiki_changes (approval queue)
    ├── change_type (create, update, delete)
    ├── confidence (AI certainty)
    ├── source_text (where extracted from)
    └── status (pending, approved, rejected)
```

### Culture System

Cultures are wiki entries of type `CULTURE` that anchor characters, factions, and locations to shared traditions, values, and norms. The culture system enables agents to understand **why** characters behave the way they do.

**Culture-Entity Relationships** (10 WikiReferenceType enums):
- `BORN_IN`, `ADOPTED_INTO`, `MEMBER_OF`, `LEADER_OF`, `WORSHIPS`
- `EXILED_FROM`, `RESENTS`, `ALLIED_WITH`, `TRADES_WITH`, `INFLUENCED_BY`

**CultureService** (`backend/app/services/culture_service.py`):
- `link_entity_to_culture()` / `unlink_entity_from_culture()` — manage relationships
- `get_character_cultural_context()` — full cultural context for a character
- `format_character_culture_summary()` — compact string for agent prompts (values, taboos, norms, speech patterns, tensions)
- `get_cultural_rules()` — world rules of type CULTURAL

**Agent Integration:** All agents (continuity, consistency, voice) query culture context via `WorldContext.culture_context` to understand character behavior, speech patterns, and cultural tensions.

### Codex-Wiki Bridge & AI Context

The Codex (entity management) and Wiki (world knowledge) sync bidirectionally:

**Codex → Wiki Sync:** When entities are created/updated in the Codex, `_trigger_wiki_sync()` fires a background task that merges entity data into the wiki via the **Wiki Merge Agent** (`wiki_merge_agent.py`). High-confidence merges (>= 0.85) auto-apply; lower-confidence changes queue for review.

**Wiki → Codex:** When manuscripts are assigned to a series, `assign_manuscript_to_series()` auto-populates the Codex from the world wiki.

**Context-Aware Entity AI Generation:** When generating AI suggestions for Codex entities, `_gather_entity_world_context()` assembles rich context from 7 sources:
1. World metadata (name, description) via entity → manuscript → series → world chain
2. Manuscript genre and premise
3. Linked wiki entry (structured data, summary, content)
4. Wiki search by entity name (fallback)
5. Active world rules (especially CULTURAL rules)
6. Culture context via `CultureService.format_character_culture_summary()`
7. Chapter text mentions and related entities

This context is injected into LLM prompts with world-grounding instructions ("ONLY use races/species that exist in the established world") and time-aware description guidance ("Note physical changes over time with chapter context").

### Manuscript Movement Between Worlds

Manuscripts can be moved between worlds/series via `move_manuscript_to_world()`:
- **Same-world moves:** Reassign series, no wiki changes needed
- **Cross-world moves:** Copy WikiEntry rows to target world, map old→new IDs for character arcs and cross-references, update entity world_id fields
- **Auto-world creation:** `ensure_manuscript_has_world()` creates a world + "Standalone" series for manuscripts without one

### Agent Wiki Integration

All agents access the wiki through a standardized tool set:

```python
# Wiki Query Tools (read-only)
query_wiki(world_id, query, entry_types, limit)
get_character_facts(character_name, world_id)
get_location_facts(location_name, world_id)
get_world_rules(world_id, rule_type)
get_relationship_state(char_a, char_b, world_id)

# Culture Tools
get_culture_context(character_name, world_id)
get_cultural_rules(world_id)

# Consistency Check Tools
check_rule_violations(text, world_id, rule_types)
check_character_consistency(character_name, text, world_id)

# Wiki Update Tools (suggestions only)
suggest_wiki_update(world_id, change_type, entry_type, title, ...)
suggest_character_update(world_id, character_name, field, value, ...)
```

**Key Principle:** Agents **never modify the wiki directly**. All changes go through the approval queue for author review.

### Auto-Population Pipeline

The wiki grows automatically as writers work:

```
Writer saves chapter
        │
        ▼
┌─────────────────────────────────────┐
│     WikiAutoPopulator.on_chapter_save│
│  1. Extract entities (NER)          │
│  2. Extract world rules (patterns)  │
│  3. Detect relationships            │
│  4. Track location details          │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│     WikiChange Queue (Pending)      │
│  - Each extraction = change request │
│  - Includes source text, confidence │
│  - Deduplicates against existing    │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│     Author Review Dashboard         │
│  - Approve individual changes       │
│  - Bulk approve high-confidence     │
│  - Edit before accepting            │
│  - Reject with reason               │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│     Wiki Updated                    │
│  - New entries created              │
│  - Existing entries enriched        │
│  - Agents now have richer context   │
└─────────────────────────────────────┘
```

### Consistency Engine

The wiki powers a comprehensive consistency system:

| Analyzer | Wiki Data Used | What It Checks |
|----------|----------------|----------------|
| POV Consistency | Character knowledge scope | Head-hopping, inappropriate knowledge |
| Scene Purpose | Story structure, arcs | Every scene advances plot/character |
| Relationship Evolution | Relationship states | Natural progression, no sudden jumps |
| World Rules | Magic/physics/social rules | Text doesn't violate established rules |
| Character Consistency | Physical traits, personality | Contradictions in descriptions |
| Timeline Validation | Events, locations, travel | Temporal impossibilities |

### Updated Context Hierarchy

With the wiki, agents now operate with a **five-level** context hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTHOR CONTEXT (Persistent across all work)                    │
│  - Writing style preferences, strengths, weaknesses             │
│  - Overused words/patterns, favorite techniques                 │
├─────────────────────────────────────────────────────────────────┤
│  WORLD WIKI (Shared across universe) ◄── NEW: Central backbone  │
│  - All characters, locations, items, factions                   │
│  - World rules (magic, physics, social, cultural)               │
│  - Relationships and their evolution                            │
│  - Character arcs and progression                               │
├─────────────────────────────────────────────────────────────────┤
│  SERIES CONTEXT (Shared within series)                          │
│  - Plot threads and arcs across books                           │
│  - Character development, series timeline                       │
├─────────────────────────────────────────────────────────────────┤
│  MANUSCRIPT CONTEXT (Current work)                              │
│  - Chapters, scenes, current position                           │
│  - Manuscript-specific timeline, outline                        │
├─────────────────────────────────────────────────────────────────┤
│  CHAPTER/SCENE CONTEXT (Immediate focus)                        │
│  - Current text being analyzed                                  │
│  - Local POV character, active scene purpose                    │
└─────────────────────────────────────────────────────────────────┘
```

### ADR-006: World Wiki as Central Context Backbone

**Context:** Maxwell's features (AI agents, validators, analyzers) were operating independently, each maintaining their own understanding of the story world. This led to inconsistent suggestions and duplicated effort.

**Decision:** Implement the World Wiki as the **single source of truth** for all narrative elements. All AI features query the wiki for context rather than inferring from raw text alone.

**Consequences:**
- ✅ Unified context across all features
- ✅ Agents give consistent, wiki-aware suggestions
- ✅ Authors maintain control via approval queue
- ✅ Knowledge persists across manuscripts in a world
- ✅ Deep analysis (POV, pacing, subplots) references established facts
- ⚠️ Requires wiki population before full effectiveness
- ⚠️ Auto-population needs careful confidence thresholds
- ⚠️ Author approval queue adds friction (by design)

**Implementation:**
- Models: `backend/app/models/wiki.py`, `character_arc.py`, `world_rule.py`
- Services: `wiki_service.py`, `wiki_auto_populator.py`, `culture_service.py`, `pov_consistency_service.py`, etc.
- Bridge: `wiki_codex_bridge.py` (codex↔wiki sync), `wiki_merge_agent.py` (AI-powered merge)
- Agent Tools: `backend/app/agents/tools/wiki_tools.py`
- Context Helper: `_gather_entity_world_context()` in `codex.py` routes (7-source context assembly for AI generation)
- API: `/api/wiki/*`, `/api/wiki/cultures/*`, `/api/analysis/*`

---

## Design System

**Colors (Tailwind):**
- `vellum-*` - Warm cream background (50-900)
- `bronze-*` - Copper accents (300, 500, 700)
- `midnight-*` - Deep text color (600, 700, 900)

**Typography:**
- `font-garamond` - Headings and display text
- `font-sans` - Body text and UI elements

**Common Patterns:**
- Cards: `bg-vellum-100 border border-bronze-300 rounded-lg`
- Hover: `hover:border-bronze-500 hover:shadow-md`
- Buttons: `bg-bronze-500 text-white px-4 py-2 rounded`
