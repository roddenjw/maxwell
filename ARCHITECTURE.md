# Maxwell Architecture

**Last Updated:** 2026-01-08
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
