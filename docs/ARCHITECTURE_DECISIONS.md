# Architecture Decision Records (ADRs)

This document contains Architecture Decision Records for Maxwell, documenting significant architectural and design decisions made throughout the project.

**Format:** Each ADR follows the structure: Context → Decision → Consequences

**Last Updated:** 2026-01-07

---

## Table of Contents

1. [ADR-001: Git-Based Version Control](#adr-001-git-based-version-control)
2. [ADR-002: Two-Tier Coaching System](#adr-002-two-tier-coaching-system)
3. [ADR-003: Lexical JSON Storage](#adr-003-lexical-json-storage)
4. [ADR-004: Service Layer Pattern](#adr-004-service-layer-pattern)
5. [ADR-005: Background Task Processing](#adr-005-background-task-processing)
6. [ADR-006: JSON Columns for Flexibility](#adr-006-json-columns-for-flexibility)
7. [ADR-007: ApiResponse<T> Pattern](#adr-007-apiresponset-pattern)

---

## ADR-001: Git-Based Version Control

**Date:** 2025-12-13
**Status:** ✅ Implemented
**Deciders:** Tech Lead, Product Lead

### Context

Writers need reliable version history without complex UX. The system must:
- Work offline without external dependencies
- Handle large text files efficiently (novels can be 100k+ words)
- Support features like diff viewing, restoration, and branching
- Provide instant snapshot creation
- Enable visual timeline navigation

**Alternatives Considered:**
1. **Custom diff algorithm** - Build our own versioning from scratch
   - Pros: Full control, optimized for our use case
   - Cons: Reinventing the wheel, hard to get right, maintenance burden

2. **SQLite blob storage** - Store each version as complete copy in database
   - Pros: Simple, fast queries
   - Cons: Massive storage waste, no diff capabilities, slow for large files

3. **Git integration** - Use Git under the hood with custom interface
   - Pros: 30+ years of battle-testing, excellent diff/merge, small storage footprint
   - Cons: Need to learn Git internals, 20MB+ repos for long novels

### Decision

Use Git (via pygit2) with one repository per manuscript. Each snapshot maps to a Git commit, diffs use `git diff`, and restoration uses `git checkout`.

**Repository Structure:**
```
data/manuscripts/{manuscript_id}/.git/
```

**Hybrid Approach:**
- **Git:** Stores actual file history (immutable, full fidelity)
- **SQLite:** Stores snapshot metadata for fast queries

**Implementation:**
- Service: `backend/app/services/version_service.py`
- Model: `backend/app/models/versioning.py` (Snapshot)
- Routes: `backend/app/api/routes/versioning.py`
- Frontend: `frontend/src/components/TimeMachine/`

### Consequences

**Positive:**
- ✅ Proven reliability (Git has 30+ years of production use)
- ✅ Powerful diff/merge capabilities built-in
- ✅ Works completely offline
- ✅ Small storage footprint (Git compression)
- ✅ Familiar to developer users
- ✅ Enables advanced features (branching, merging)
- ✅ Fast snapshot creation (<100ms)

**Negative:**
- ⚠️ Requires learning Git internals for maintenance
- ⚠️ Repository size grows over time (20MB+ for long novels with many snapshots)
- ⚠️ Limited to text files (not binary assets like images)
- ⚠️ Git complexity hidden but still present under the hood

**Mitigations:**
- Document Git integration thoroughly in CLAUDE.md
- Provide garbage collection/cleanup tools for old repositories
- Plan for future binary asset support (Git LFS or separate storage)

### Related Decisions

- [ADR-003: Lexical JSON Storage](#adr-003-lexical-json-storage) - Format stored in Git

---

## ADR-002: Two-Tier Coaching System

**Date:** 2025-12-13
**Status:** ✅ Implemented
**Deciders:** Tech Lead, Product Lead, UX Designer

### Context

Writers need real-time writing feedback, but AI analysis is too slow and expensive to run on every keystroke. Need to balance:
- **Speed:** Instant feedback while typing (< 100ms)
- **Cost:** Free for basic features, pay-per-use for advanced
- **Quality:** Simple rule-based + deep AI insights
- **UX:** Non-intrusive, passive assistance

**Existing Approaches:**
- **Grammarly:** Real-time but limited to grammar/spelling
- **ProWritingAid:** Batch analysis, slow, expensive subscription
- **Claude/GPT:** Deep insights but too slow for real-time, costly

### Decision

Implement a **two-tier coaching system**:

**1. Fast Coach (Python - Real-time)**
- Rule-based + statistical analysis
- Runs locally, no API calls
- Always-on, passive assistance
- Analysis < 100ms
- Free for all users

**2. Smart Coach (AI - On-demand)**
- AI-powered via OpenRouter
- Deep narrative-level feedback
- Requires explicit user action
- Pay-per-use (BYOK model)
- 3-10 seconds per analysis

**Fast Coach Services:**
- `style_analyzer.py` - Sentence variance, passive voice, adverbs, paragraphs
- `word_analyzer.py` - Weak words, telling verbs, repetition, clichés
- `consistency_checker.py` - Character attributes, entity mentions (via Codex)

**Smart Coach (future):**
- LangChain-based learning system
- Learns user's style over time
- Provides plot/character arc feedback

### Consequences

**Positive:**
- ✅ Instant feedback without lag or cost
- ✅ Always-on assistance improves writing in real-time
- ✅ AI available for deeper analysis when needed
- ✅ Users control AI costs (BYOK)
- ✅ No subscription required
- ✅ Privacy: AI is optional, local analysis is default

**Negative:**
- ⚠️ Fast Coach limited to rule-based patterns
- ⚠️ AI suggestions require API key setup
- ⚠️ Two-tier UX could be confusing
- ⚠️ Maintenance burden for two separate systems

**Mitigations:**
- Clear UI distinction between Fast Coach (instant) and AI (on-demand)
- Comprehensive testing for Fast Coach rules
- Future: Combine both tiers into unified interface

### Related Decisions

- [ADR-005: Background Task Processing](#adr-005-background-task-processing) - Used for AI analysis
- [ADR-003: Lexical JSON Storage](#adr-003-lexical-json-storage) - Text extraction for analysis

---

## ADR-003: Lexical JSON Storage

**Date:** 2025-12-12
**Status:** ✅ Implemented
**Deciders:** Tech Lead

### Context

Need rich text formatting (bold, italics, lists) without losing data when switching editors. Must support:
- Format preservation across sessions
- Plain text extraction for NLP/search
- Future editor flexibility
- Reasonable storage size
- Fast serialization/deserialization

**Alternatives Considered:**
1. **HTML storage** - Store as HTML strings
   - Pros: Universal format, browser-native
   - Cons: Hard to parse, XSS risks, bloated markup, no schema

2. **Markdown storage** - Store as Markdown
   - Pros: Human-readable, simple
   - Cons: Limited formatting, conversion loss, no rich structure

3. **ProseMirror JSON** - ProseMirror's native format
   - Pros: Well-documented, stable
   - Cons: Locked into ProseMirror ecosystem

4. **Lexical JSON** - Lexical's native format
   - Pros: Meta-backed, extensible, structured tree, TypeScript-first
   - Cons: Relatively new framework

### Decision

Store Lexical editor state as JSON string in `lexical_state` column. Extract plain text on save for search/NLP and store in `content` column.

**Dual Storage:**
- `Chapter.lexical_state` - Full Lexical JSON (format-preserving)
- `Chapter.content` - Plain text extraction (search/analysis)

**Extraction Function:**
```python
def extract_text_from_lexical(lexical_state_str: str) -> str:
    """Recursively walk Lexical node tree and extract text"""
    # Implementation in backend/app/api/routes/chapters.py:21-68
```

**Implementation:**
- Models: `backend/app/models/manuscript.py` (Chapter, Manuscript)
- Routes: `backend/app/api/routes/chapters.py`
- Frontend: Lexical editor in `frontend/src/components/Editor/`

### Consequences

**Positive:**
- ✅ Format-preserving (bold, italics, lists, etc.)
- ✅ Editor-agnostic JSON format
- ✅ Plain text available for NLP/search
- ✅ Structured tree for advanced features
- ✅ TypeScript-first (good for our stack)
- ✅ Extensible for custom nodes (e.g., scene breaks)

**Negative:**
- ⚠️ Large JSON payloads for long chapters (10-50KB per chapter)
- ⚠️ Custom extraction logic required
- ⚠️ Lexical is relatively new (launched 2021)
- ⚠️ Migration complexity if we switch editors

**Mitigations:**
- Compress Lexical JSON in database (future optimization)
- Version extraction logic with tests
- Document Lexical JSON schema for future migrations

### Related Decisions

- [ADR-001: Git-Based Version Control](#adr-001-git-based-version-control) - Lexical JSON stored in Git
- [ADR-002: Two-Tier Coaching System](#adr-002-two-tier-coaching-system) - Needs plain text extraction

---

## ADR-004: Service Layer Pattern

**Date:** 2025-12-10
**Status:** ✅ Implemented
**Deciders:** Tech Lead

### Context

Backend needs clear separation of concerns. Routes should handle HTTP, business logic should be reusable, and database access should be isolated.

**Goals:**
- Testable business logic
- Reusable across multiple routes
- Clear responsibility boundaries
- Easy to understand for new developers

**Anti-pattern observed in early code:**
Routes directly querying database with complex joins and business logic mixed into HTTP handlers.

### Decision

Adopt **three-tier architecture** with service layer:

```
Routes (API Layer)          →  backend/app/api/routes/*.py
  ↓ Call
Services (Business Logic)   →  backend/app/services/*.py
  ↓ Query/Persist
Models (Data Layer)         →  backend/app/models/*.py
```

**Service Responsibilities:**
- Business logic and validation
- Complex queries and data aggregation
- Cross-entity operations
- Algorithm implementation

**Route Responsibilities:**
- HTTP request/response handling
- Request validation (Pydantic)
- Authentication/authorization (future)
- Call appropriate services

**Example:**
```python
# Route (app/api/routes/timeline.py)
@router.post("/validate/{manuscript_id}")
async def validate_timeline(manuscript_id: str, db: Session = Depends(get_db)):
    issues = timeline_service.validate_timeline_orchestrator(manuscript_id)
    return {"success": True, "data": issues}

# Service (app/services/timeline_service.py)
class TimelineService:
    def validate_timeline_orchestrator(self, manuscript_id: str) -> List[TimelineInconsistency]:
        # Complex validation logic here
        # Runs 5 validators, creates inconsistency records
        return issues
```

**Service Singletons:**
All services instantiated once and exported:
```python
# app/services/__init__.py
from app.services.timeline_service import TimelineService
timeline_service = TimelineService()  # Singleton
```

### Consequences

**Positive:**
- ✅ Clear separation of concerns
- ✅ Business logic is testable without HTTP
- ✅ Services reusable across multiple routes
- ✅ Easier to understand for new developers
- ✅ Database session management isolated to routes

**Negative:**
- ⚠️ Extra layer of indirection
- ⚠️ Not all routes need services (simple CRUD can stay in routes)
- ⚠️ Service singletons share database sessions (potential issue)

**Guidelines:**
- Use services for complex business logic (3+ operations)
- Simple CRUD can stay in routes (e.g., get by ID, delete)
- Services manage their own database sessions: `db = SessionLocal()`
- Services are stateless (no instance variables for request state)

### Related Decisions

- [ADR-007: ApiResponse<T> Pattern](#adr-007-apiresponset-pattern) - Response format from routes

---

## ADR-005: Background Task Processing

**Date:** 2025-12-12
**Status:** ✅ Implemented
**Deciders:** Tech Lead, UX Designer

### Context

NLP analysis and AI generation can take seconds. Cannot block the editor or API responses, as this creates poor UX.

**Requirements:**
- Editor must remain responsive during analysis
- API should return immediately
- Long-running tasks processed asynchronously
- Users notified when tasks complete

**Use Cases:**
- NLP entity extraction (1-5 seconds)
- AI writing suggestions (3-10 seconds)
- Timeline validation (2-10 seconds for large manuscripts)
- Chapter recap generation (10-20 seconds)

**Alternatives Considered:**
1. **Synchronous blocking** - Wait for operation to complete
   - Pros: Simple
   - Cons: Editor freezes, timeout issues, poor UX

2. **WebSocket with workers** - Celery/RQ worker queue
   - Pros: Robust, scalable
   - Cons: Complex setup, Redis dependency, overkill for local-first app

3. **FastAPI BackgroundTasks** - Built-in async task runner
   - Pros: Simple, no extra dependencies, good for local-first
   - Cons: No persistence, tasks lost if server restarts

### Decision

Use FastAPI `BackgroundTasks` for async processing. Future: Add WebSocket for real-time updates.

**Implementation Pattern:**
```python
from fastapi import BackgroundTasks

@router.post("/analyze")
async def analyze_text(
    manuscript_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Start background processing
    background_tasks.add_task(
        nlp_service.analyze_manuscript,
        manuscript_id
    )

    return {
        "success": True,
        "message": "Analysis started in background"
    }
```

**Current Implementation:**
- NLP entity extraction
- AI writing suggestions
- Timeline validation (for very large manuscripts)

**Future (WebSocket):**
```python
# Planned for real-time updates
websocket_manager.broadcast({
    "type": "analysis_complete",
    "manuscript_id": manuscript_id,
    "entities": extracted_entities
})
```

### Consequences

**Positive:**
- ✅ Non-blocking API responses
- ✅ Editor remains responsive
- ✅ Simple implementation (no external dependencies)
- ✅ Good enough for local-first use case

**Negative:**
- ⚠️ No task status tracking (user doesn't know when complete)
- ⚠️ Tasks lost if server restarts
- ⚠️ No retry mechanism
- ⚠️ Limited to single-server deployment

**Mitigations:**
- Add WebSocket for real-time progress updates (Phase 7)
- Document that tasks may be lost on server restart
- For critical operations (snapshots), use synchronous calls

### Related Decisions

- [ADR-002: Two-Tier Coaching System](#adr-002-two-tier-coaching-system) - AI analysis runs in background

---

## ADR-006: JSON Columns for Flexibility

**Date:** 2025-12-10
**Status:** ✅ Implemented
**Deciders:** Tech Lead

### Context

Features need flexible attributes without schema changes. Different entity types have different fields:
- Characters: age, eye_color, hair_color, personality traits
- Locations: coordinates, size, population
- Items: magical properties, value, owner

Adding columns for each attribute creates:
- Sparse tables (most columns NULL)
- Frequent schema migrations
- Hard to extend for new attributes

### Decision

Use JSON columns for flexible storage: `settings`, `attributes`, `metadata`.

**Examples:**
```python
# Manuscript.settings (JSON)
{
  "editor_theme": "dark",
  "autosave_interval": 5000,
  "word_count_target": 80000
}

# Entity.attributes (JSON)
{
  "age": 50,
  "eye_color": "grey",
  "hair_color": "grey",
  "personality": ["wise", "brooding"],
  "backstory": "Lost family in war..."
}

# TimelineEvent.event_metadata (JSON)
{
  "word_count": 1523,
  "dialogue_count": 15,
  "scene_type": "action"
}

# Relationship.relationship_metadata (JSON)
{
  "duration_years": 10,
  "strength": 8,
  "conflict_level": 3,
  "notes": "Childhood friends"
}
```

**Database Schema:**
```python
class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    type = Column(String)  # CHARACTER, LOCATION, ITEM, LORE
    name = Column(String)

    # Flexible JSON storage
    attributes = Column(JSON, default=dict)
```

**Implementation:**
- All major models have JSON columns
- SQLite/PostgreSQL/MySQL all support JSON columns
- Frontend TypeScript types allow `[key: string]: any` for flexibility

### Consequences

**Positive:**
- ✅ Rapid feature iteration without migrations
- ✅ No sparse tables (NULL columns)
- ✅ Per-entity customization
- ✅ Easy to extend (just add new keys to JSON)
- ✅ Works across database backends (SQLite, PostgreSQL, MySQL)

**Negative:**
- ⚠️ Harder to query/filter (can't index JSON keys easily)
- ⚠️ No database-level validation (structure enforced in code)
- ⚠️ Potential for schema drift (different entities have different keys)
- ⚠️ Can't do efficient joins on JSON fields

**Guidelines:**
- Use JSON columns for optional, variable attributes
- Use regular columns for required, queryable fields (name, type, created_at)
- Document expected JSON structure in model docstrings
- Add application-level validation for JSON structure

**Migration Path:**
If a JSON field becomes frequently queried, extract to regular column:
```python
# Before
entity.attributes = {"age": 50, ...}

# After (migration)
entity.age = 50  # New column
entity.attributes = {other attributes...}
```

### Related Decisions

- [ADR-004: Service Layer Pattern](#adr-004-service-layer-pattern) - Services validate JSON structure

---

## ADR-007: ApiResponse<T> Pattern

**Date:** 2025-12-10
**Status:** ✅ Implemented
**Deciders:** Tech Lead, Frontend Lead

### Context

Need consistent API response format for:
- Error handling
- Loading states
- TypeScript type safety
- Debugging (error codes, details)

**Early code had inconsistent responses:**
```python
# Inconsistent
return {"entity": entity}  # Success
return {"error": "Not found"}  # Error
return entity  # Direct return
```

Frontend couldn't reliably detect success/failure or parse errors.

### Decision

All API endpoints return standardized `ApiResponse<T>` structure.

**TypeScript Interface:**
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp: string;
    version: string;
  };
}
```

**Python Response Patterns:**
```python
# Success
return {
    "success": True,
    "data": entity
}

# Error
return {
    "success": False,
    "error": {
        "code": "NOT_FOUND",
        "message": "Entity not found",
        "details": {"entity_id": entity_id}
    }
}

# With metadata
return {
    "success": True,
    "data": entities,
    "meta": {
        "total": len(entities),
        "timestamp": datetime.utcnow().isoformat()
    }
}
```

**Error Codes:**
- `NOT_FOUND` - Resource doesn't exist
- `VALIDATION_ERROR` - Invalid input
- `UNAUTHORIZED` - Auth required (future)
- `INTERNAL_ERROR` - Server error

**Frontend Usage:**
```typescript
const response = await apiFetch<Entity>('/api/entities/123');

if (response.success) {
  console.log(response.data);  // Type: Entity
} else {
  console.error(response.error.message);
  alert(`Error ${response.error.code}: ${response.error.message}`);
}
```

### Consequences

**Positive:**
- ✅ Consistent error handling across all endpoints
- ✅ TypeScript type safety (discriminated union on `success`)
- ✅ Clear success/failure detection
- ✅ Structured error codes for client-side logic
- ✅ Optional metadata for pagination, timestamps
- ✅ Easy to debug (error details included)

**Negative:**
- ⚠️ Extra nesting (`response.data` instead of `response`)
- ⚠️ Slightly more verbose
- ⚠️ Need to maintain error code constants

**Guidelines:**
- Always use this pattern (no exceptions)
- Error codes should be SCREAMING_SNAKE_CASE constants
- Include details object for debugging (don't expose sensitive data)
- Meta is optional, use for pagination/stats

**Example Error Codes:**
```python
# Common error codes
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_FORBIDDEN = "FORBIDDEN"
ERROR_INTERNAL = "INTERNAL_ERROR"
ERROR_CONFLICT = "CONFLICT"
```

### Related Decisions

- [ADR-004: Service Layer Pattern](#adr-004-service-layer-pattern) - Services return data, routes wrap in ApiResponse

---

## Future ADRs

As the project evolves, document new architectural decisions here:

**Planned:**
- ADR-008: WebSocket Architecture for Real-Time Updates
- ADR-009: Offline-First Data Sync Strategy
- ADR-010: Multi-User Collaboration Model
- ADR-011: Mobile App Architecture (React Native vs. Native)
- ADR-012: Search & Indexing Strategy (Full-text search)

**Template for New ADRs:**
```markdown
## ADR-XXX: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Deciders:** [List of people involved]

### Context
[Problem statement, requirements, constraints]

### Decision
[What we decided to do and why]

### Consequences
**Positive:**
- ✅ [Benefit 1]
- ✅ [Benefit 2]

**Negative:**
- ⚠️ [Trade-off 1]
- ⚠️ [Trade-off 2]

**Mitigations:**
- [How we address trade-offs]

### Related Decisions
- [Links to related ADRs]
```

---

## Revisiting Decisions

ADRs are living documents. As the project evolves, decisions may need to be:

**Deprecated:**
- Mark as "Deprecated" if superseded by new decision
- Link to new ADR
- Document migration path

**Updated:**
- Add "Updated" section with date
- Explain why decision changed
- Document impact on codebase

**Superseded:**
- Mark as "Superseded by ADR-XXX"
- Explain why original decision no longer applies

---

**Last Updated:** 2026-01-07
**Maintainer:** Maxwell Development Team
**Review Frequency:** Quarterly (next review: 2026-04-01)
