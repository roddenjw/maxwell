# CLAUDE.md - Maxwell Development Guide

> **Purpose:** This is the primary development guide for Maxwell. Read this first when working on the project. It contains architecture, standards, workflows, and implementation patterns.

**Last Updated:** 2026-01-07
**Version:** 1.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Code Organization Standards](#2-code-organization-standards)
3. [Development Workflow](#3-development-workflow)
4. [Implementation Patterns & Examples](#4-implementation-patterns--examples)
5. [Quick Reference](#5-quick-reference)

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 System Design Philosophy

**Vision:** Invisible engineering for fiction writers

Maxwell is designed to be a **local-first fiction writing IDE** that provides powerful features without complexity. Key principles:

- **Local-first:** SQLite database, no cloud dependency for core features
- **Async background processing:** NLP and AI analysis never blocks the editor
- **Git-backed version control:** Reliable snapshots without Git UX complexity
- **BYOK (Bring Your Own Key):** Users provide their own AI API keys, we charge zero markup
- **Maxwell Design System:** Vellum (warm cream), Bronze (copper accents), Midnight (deep text)
- **Teaching-first:** Tools educate writers about craft (e.g., Timeline Orchestrator teaches consistency)

### 1.2 Tech Stack

**Backend (Python 3.13)**
- **FastAPI 0.104+** - Async web framework
- **SQLAlchemy 2.0+** - ORM with declarative models
- **SQLite** - File-based database (PostgreSQL/MySQL ready)
- **Alembic** - Database migrations
- **pygit2** - Git integration for versioning
- **spaCy 3.8.11** - NLP for entity extraction
- **ChromaDB** - Vector embeddings (optional, Python 3.13 compatible version pending)

**Frontend (React 18 + TypeScript 5.2)**
- **Vite 5.0** - Build tool and dev server
- **Lexical 0.12.5** - Rich text editor framework
- **Zustand 4.4.7** - Lightweight state management
- **TanStack Query 5.0** - Server state/caching (planned)
- **Tailwind CSS 3.4.0** - Utility-first styling
- **react-force-graph-2d** - Relationship graph visualization
- **Vis.js** - Timeline visualization

### 1.3 Architecture Layers

#### Backend: Three-Tier Pattern

```
Routes (API Layer)          →  backend/app/api/routes/*.py
  ↓ Call
Services (Business Logic)   →  backend/app/services/*.py
  ↓ Query/Persist
Models (Data Layer)         →  backend/app/models/*.py
  ↓ Store
Database (SQLite)           →  data/codex.db
```

**Request Flow Example:**
```
POST /api/chapters
  → chapters.py route handler
    → (no dedicated service - direct DB access for simple CRUD)
      → Chapter model (manuscript.py)
        → SQLite via SQLAlchemy ORM
```

**Complex Feature Flow:**
```
POST /api/timeline/validate/{manuscript_id}
  → timeline.py route handler
    → timeline_service.validate_timeline_orchestrator()
      → Queries TimelineEvent, CharacterLocation, TravelLeg models
      → Runs 5 validators (travel, dependencies, presence, timing, paradoxes)
      → Creates TimelineInconsistency records
        → Returns validation results to route
          → API response to frontend
```

#### Frontend: Component-Store-API Pattern

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

### 1.4 Key Architectural Decisions

#### ADR-001: Git-Based Version Control

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

#### ADR-002: Lexical JSON Storage

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

#### ADR-003: ApiResponse<T> Pattern

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

#### ADR-004: Background Task Processing

**Context:** NLP analysis and AI generation can take seconds. Cannot block the editor or API responses.

**Decision:** Use FastAPI `BackgroundTasks` for async processing. WebSocket for real-time updates (planned).

**Implementation:**
```python
@router.post("/analyze")
async def analyze_text(
    data: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    # Start async processing
    background_tasks.add_task(
        nlp_service.analyze_manuscript,
        data.manuscript_id
    )
    return {"success": True, "message": "Analysis started"}
```

#### ADR-005: JSON Columns for Flexibility

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

### 1.5 Database Schema Overview

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

## 2. CODE ORGANIZATION STANDARDS

### 2.1 File Naming Conventions

**Backend Python:**
- **Models:** `{domain}.py` → `manuscript.py`, `entity.py`, `timeline.py`
- **Services:** `{domain}_service.py` → `codex_service.py`, `timeline_service.py`
- **Routes:** `{domain}.py` → `chapters.py`, `outlines.py`, `timeline.py`
- **Tests:** `{file}.test.py` → `chapters.test.py`, `timeline_service.test.py` (colocated)
- **Migrations:** `{hash}_{description}.py` → `b8b0d4d0f396_initial_schema_manuscripts_entities_.py`

**Frontend TypeScript:**
- **Components:** `PascalCase.tsx` → `EntityCard.tsx`, `TimelineSidebar.tsx`
- **Stores:** `{domain}Store.ts` → `codexStore.ts`, `timelineStore.ts`, `manuscriptStore.ts`
- **Types:** `{domain}.ts` → `timeline.ts`, `outline.ts`, `codex.ts`
- **Utilities:** `camelCase.ts` → `extractText.ts`, `formatDate.ts`
- **Hooks:** `use{Name}.ts` → `useKeyboardShortcuts.ts`, `useRealtimeNLP.ts`
- **Tests:** `{file}.test.tsx` → `EntityCard.test.tsx` (colocated)

### 2.2 Directory Structure

**Backend:**
```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint handlers
│   │       ├── chapters.py  # Chapter CRUD (create, read, update, delete)
│   │       ├── codex.py     # Entity/relationship management
│   │       ├── timeline.py  # Timeline orchestrator (18 endpoints)
│   │       ├── outlines.py  # Story structure (14 endpoints)
│   │       └── brainstorming.py  # AI ideation tools
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── manuscript.py    # Manuscript, Chapter, Scene
│   │   ├── entity.py        # Entity, Relationship, EntitySuggestion
│   │   ├── timeline.py      # TimelineEvent, CharacterLocation, etc.
│   │   ├── outline.py       # Outline, PlotBeat
│   │   └── brainstorm.py    # BrainstormSession, BrainstormIdea
│   ├── services/            # Business logic layer
│   │   ├── codex_service.py      # Entity extraction, merging
│   │   ├── nlp_service.py        # spaCy NLP analysis
│   │   ├── timeline_service.py   # Timeline validation (800+ lines)
│   │   ├── story_structures.py   # Plot beat templates
│   │   └── brainstorming_service.py  # AI idea generation
│   ├── database.py          # SQLAlchemy setup, session management
│   ├── main.py              # FastAPI app initialization
│   └── __init__.py
├── migrations/              # Alembic database migrations
│   ├── env.py
│   └── versions/            # Migration files (8 total)
├── tests/                   # Integration tests (colocated unit tests)
│   ├── conftest.py          # Pytest fixtures (test_db, client)
│   └── test_*.py
├── data/                    # Local data storage
│   ├── codex.db             # SQLite database
│   └── manuscripts/         # Git repositories (one per manuscript)
│       └── {manuscript_id}/
│           └── .git/
├── requirements.txt         # Python dependencies
└── alembic.ini             # Alembic configuration
```

**Frontend:**
```
frontend/
└── src/
    ├── components/          # React components (feature-based)
    │   ├── [Feature]/       # Feature directory (e.g., Codex, Timeline)
    │   │   ├── FeatureName.tsx
    │   │   ├── FeatureName.test.tsx  # Colocated test
    │   │   └── index.ts     # Barrel export
    │   ├── Codex/           # Entity management (8 components)
    │   │   ├── CodexSidebar.tsx
    │   │   ├── EntityList.tsx
    │   │   ├── EntityCard.tsx
    │   │   ├── EntityDetail.tsx
    │   │   ├── SuggestionQueue.tsx
    │   │   ├── RelationshipGraph.tsx
    │   │   ├── MergeEntitiesModal.tsx
    │   │   └── index.ts
    │   ├── Timeline/        # Timeline tools (9 components)
    │   ├── Outline/         # Story structure (5 components)
    │   ├── Brainstorming/   # Ideation (5 components)
    │   ├── Editor/          # Writing interface
    │   │   ├── ManuscriptEditor.tsx
    │   │   ├── EditorToolbar.tsx
    │   │   └── plugins/     # Lexical editor plugins
    │   │       ├── AutoSavePlugin.tsx
    │   │       └── RichTextPlugin.tsx
    │   └── common/          # Shared components
    ├── stores/              # Zustand state management
    │   ├── manuscriptStore.ts
    │   ├── codexStore.ts
    │   ├── timelineStore.ts
    │   ├── outlineStore.ts
    │   └── brainstormStore.ts
    ├── types/               # TypeScript type definitions
    │   ├── codex.ts
    │   ├── timeline.ts
    │   ├── outline.ts
    │   └── brainstorm.ts
    ├── lib/                 # Utility libraries
    │   ├── api.ts           # API client (type-safe fetch wrappers)
    │   └── extractText.ts   # Lexical text extraction
    ├── hooks/               # Custom React hooks
    │   ├── useKeyboardShortcuts.ts
    │   └── useRealtimeNLP.ts
    ├── App.tsx              # Root component
    ├── main.tsx             # React app entry point
    └── index.css            # Tailwind CSS imports
```

### 2.3 Import Order Standards

**Python (PEP 8 compliant):**
```python
# 1. Standard library imports
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import json

# 2. Third-party library imports
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# 3. Local application imports
from app.database import get_db
from app.models.manuscript import Chapter, Manuscript
from app.services.timeline_service import timeline_service
from app.services.nlp_service import nlp_service
```

**TypeScript (ESLint-compatible):**
```typescript
// 1. React and external libraries
import React, { useState, useEffect } from 'react';
import { create } from 'zustand';
import { useQuery } from '@tanstack/react-query';

// 2. Type imports (aliased imports)
import type { Entity, Relationship } from '@/types/codex';
import type { TimelineEvent } from '@/types/timeline';

// 3. Components (internal)
import { EntityCard } from '@/components/Codex';
import { TimelineVisualization } from '@/components/Timeline';

// 4. Utilities and API clients
import { codexApi } from '@/lib/api';
import { extractTextFromLexical } from '@/lib/extractText';

// 5. Styles (if separate CSS modules)
import styles from './EntityList.module.css';
```

### 2.4 Feature-Based Component Organization

**Pattern:** Colocate related components in feature directories with barrel exports.

**Example: Codex Feature**
```
components/Codex/
├── CodexSidebar.tsx         # Main container component
├── EntityList.tsx           # Entity browsing (search, filter)
├── EntityCard.tsx           # Single entity display
├── EntityDetail.tsx         # Entity editing modal
├── SuggestionQueue.tsx      # NLP-generated suggestions
├── SuggestionCard.tsx       # Single suggestion display
├── RelationshipGraph.tsx    # Force-directed graph visualization
├── MergeEntitiesModal.tsx   # Entity merging UI
└── index.ts                 # Barrel export (re-export all)

// index.ts
export { default as CodexSidebar } from './CodexSidebar';
export { default as EntityList } from './EntityList';
export { default as EntityCard } from './EntityCard';
export { default as EntityDetail } from './EntityDetail';
export { default as SuggestionQueue } from './SuggestionQueue';
export { default as RelationshipGraph } from './RelationshipGraph';
export { default as MergeEntitiesModal } from './MergeEntitiesModal';
```

**Usage:**
```typescript
// Import multiple components from feature
import { EntityList, EntityCard, CodexSidebar } from '@/components/Codex';
```

### 2.5 Naming Standards

**Components:**
- PascalCase for component names
- Filename matches component: `EntityCard.tsx` exports `EntityCard`
- Props interface: `{ComponentName}Props`
  ```typescript
  interface EntityCardProps {
    entity: Entity;
    onSelect: (id: string) => void;
    onDelete?: (id: string) => void;
  }

  export function EntityCard({ entity, onSelect, onDelete }: EntityCardProps) {
    // ...
  }
  ```

**Functions:**
- camelCase for functions and methods
- Verb-first naming: `createEntity()`, `fetchTimeline()`, `extractText()`
- Boolean prefixes: `isValid()`, `hasPermission()`, `canEdit()`, `shouldUpdate()`
- Event handlers: `handleClick()`, `handleSubmit()`, `handleDelete()`

**Constants:**
- SCREAMING_SNAKE_CASE for true constants
  ```typescript
  const API_BASE_URL = 'http://localhost:8000';
  const MAX_SUGGESTIONS = 10;
  const DEFAULT_AUTOSAVE_INTERVAL = 5000; // ms
  ```
- camelCase for configuration objects
  ```typescript
  const editorConfig = {
    theme: 'maxwell',
    autosave: true,
    autosaveInterval: 5000,
  };
  ```

**Types/Interfaces:**
- PascalCase: `Entity`, `TimelineEvent`, `ApiResponse<T>`
- Suffix with purpose:
  - Request types: `CreateEntityRequest`, `UpdateChapterRequest`
  - Response types: `ChapterResponse`, `TimelineStatsResponse`
  - Props: `EntityCardProps`, `TimelineSidebarProps`
  - Store interfaces: `CodexStore`, `TimelineStore`

---

## 3. DEVELOPMENT WORKFLOW

### 3.1 Testing Standards

**Philosophy:** Colocate tests next to source files for discoverability and maintenance.

#### Backend Testing

**Structure:**
```
backend/app/api/routes/
├── chapters.py
└── chapters.test.py         # ← Colocated unit test

backend/app/services/
├── timeline_service.py
└── timeline_service.test.py # ← Colocated unit test
```

**Integration tests** stay in `/backend/tests/` directory.

#### Frontend Testing

**Structure:**
```
frontend/src/components/Codex/
├── EntityCard.tsx
├── EntityCard.test.tsx      # ← Colocated unit test
└── EntityCard.stories.tsx   # ← Storybook story (future)
```

#### When to Write Tests

**Required:**
1. **Critical business logic** - Services, validators, algorithms
   - Example: `timeline_service.validate_timeline_orchestrator()`
2. **Data transformation** - JSON parsing, text extraction, serialization
   - Example: `extract_text_from_lexical()`, `serialize_chapter()`
3. **Complex algorithms** - Graph traversal, conflict detection, NLP
   - Example: Relationship graph generation
4. **Bug fixes** - Regression test for each bug fixed
   - Example: Chapter serialization bug → `test_chapter_serialization.py`
5. **Public APIs** - All REST endpoint edge cases
   - Example: Timeline validation endpoint

**Optional:**
1. Simple CRUD routes (get by ID, delete by ID)
2. UI components without complex logic (mostly presentational)
3. Type definitions and interfaces
4. Configuration files

#### Coverage Expectations

- **Services:** 70%+ coverage (critical business logic)
- **Routes:** 50%+ coverage (API contracts)
- **Utilities:** 80%+ coverage (shared functions)
- **Overall project:** 60%+ target

#### Test Structure

**Pytest (Backend):**
```python
def test_validate_timeline_detects_impossible_travel(test_db):
    """
    Timeline Orchestrator should detect when character travels
    impossible distance in available time
    """
    # Arrange
    manuscript_id = "test-ms-123"
    char_id = create_test_character(test_db, manuscript_id)
    loc_a, loc_b = create_test_locations(test_db, manuscript_id, distance=100)  # 100km apart

    event1 = create_timeline_event(test_db, manuscript_id, {
        "order_index": 0,
        "location_id": loc_a,
        "character_ids": [char_id]
    })
    event2 = create_timeline_event(test_db, manuscript_id, {
        "order_index": 1,  # 1 day later
        "location_id": loc_b,
        "character_ids": [char_id]
    })

    # Act
    issues = timeline_service.validate_timeline_orchestrator(manuscript_id)

    # Assert
    assert len(issues) > 0
    assert any(i.inconsistency_type == "IMPOSSIBLE_TRAVEL" for i in issues)
    travel_issue = next(i for i in issues if i.inconsistency_type == "IMPOSSIBLE_TRAVEL")
    assert char_id in travel_issue.description
```

**Vitest (Frontend):**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EntityCard } from './EntityCard';
import type { Entity } from '@/types/codex';

describe('EntityCard', () => {
  const mockEntity: Entity = {
    id: '123',
    name: 'Frodo Baggins',
    type: 'CHARACTER',
    description: 'Hobbit from the Shire',
    attributes: { age: 50 },
    manuscript_id: 'ms-456',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  it('displays entity name and type', () => {
    // Arrange
    const onSelect = vi.fn();

    // Act
    render(<EntityCard entity={mockEntity} onSelect={onSelect} />);

    // Assert
    expect(screen.getByText('Frodo Baggins')).toBeInTheDocument();
    expect(screen.getByText('CHARACTER')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    // Arrange
    const onSelect = vi.fn();
    render(<EntityCard entity={mockEntity} onSelect={onSelect} />);

    // Act
    fireEvent.click(screen.getByText('Frodo Baggins'));

    // Assert
    expect(onSelect).toHaveBeenCalledWith('123');
  });
});
```

#### Running Tests

**Backend:**
```bash
cd backend
source venv/bin/activate

# All tests
pytest

# Specific file
pytest app/api/routes/chapters.test.py

# Verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend

# All tests
npm test

# Specific test
npm test EntityCard

# Coverage report
npm run coverage
```

#### Test Configuration

**pytest.ini** (Backend):
```ini
[pytest]
testpaths = app tests
python_files = test_*.py *_test.py *.test.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
```

**vite.config.ts** (Frontend):
```typescript
export default defineConfig({
  // ... other config
  test: {
    include: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}'],
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
  },
});
```

### 3.2 Database Migrations

#### Creating Migrations

```bash
cd backend
source venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add timeline orchestrator models"

# Review generated migration
cat migrations/versions/{hash}_add_timeline_orchestrator_models.py

# Apply migration
alembic upgrade head

# Check current migration
alembic current
```

#### Migration Naming

Use descriptive names:
- ✅ `add_timeline_orchestrator_models`
- ✅ `add_outline_and_plot_beats_tables`
- ✅ `genericize_story_structure_names`
- ❌ `update_db` (too vague)
- ❌ `schema_changes` (not descriptive)

#### Migration Best Practices

1. **Review auto-generated SQL** before applying
   - Alembic sometimes generates incorrect constraints
   - Check for missing foreign keys or indexes

2. **Test on fresh database**
   ```bash
   rm data/codex.db
   alembic upgrade head
   python -c "from app.database import engine; from app.models import *; print('✅ Schema valid')"
   ```

3. **Include data migrations if needed**
   - Not just schema changes
   - Example: Populate default plot beat templates

4. **Never edit applied migrations**
   - Create new migration to fix issues
   - Editing breaks migration history

#### Migration Example

```python
"""add_timeline_orchestrator_models

Revision ID: b0adcf561edc
Revises: 927396b0fa40
Create Date: 2026-01-05 14:29:11.507167
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = 'b0adcf561edc'
down_revision: Union[str, Sequence[str], None] = '927396b0fa40'

def upgrade() -> None:
    """Upgrade schema."""
    # Create travel_legs table
    op.create_table(
        'travel_legs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('character_id', sa.String(), nullable=False),
        # ... more columns
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_travel_legs_manuscript_id', 'travel_legs', ['manuscript_id'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_travel_legs_manuscript_id', table_name='travel_legs')
    op.drop_table('travel_legs')
```

### 3.3 Documentation Standards

#### Code Comments

Use docstrings for all public functions/classes. Explain "why" not "what" in inline comments.

**Python Docstrings (Google Style):**
```python
def validate_timeline_orchestrator(manuscript_id: str, check_travel: bool = True) -> List[TimelineInconsistency]:
    """
    Validate timeline for chronological inconsistencies and impossible events

    Runs 5 core validators:
    1. Impossible travel (character teleportation)
    2. Dependency violations (events out of order)
    3. Character presence (character in two places)
    4. Timing gaps (suspicious time jumps)
    5. Temporal paradoxes (circular dependencies)

    Args:
        manuscript_id: UUID of manuscript to validate
        check_travel: Whether to validate character travel times (default: True)

    Returns:
        List of TimelineInconsistency objects (empty if valid)

    Raises:
        ValueError: If manuscript not found

    Example:
        >>> issues = validate_timeline_orchestrator("ms-123", check_travel=False)
        >>> print(f"Found {len(issues)} timeline issues")
    """
    # Implementation...
```

**TypeScript JSDoc:**
```typescript
/**
 * Extract plain text from Lexical editor JSON state
 *
 * Recursively walks Lexical node tree and concatenates text content.
 * Paragraph nodes are separated by newlines.
 *
 * @param lexicalState - Lexical editor state as JSON string
 * @returns Plain text with paragraphs separated by newlines
 *
 * @example
 * const text = extractTextFromLexical('{"root": {...}}');
 * console.log(text); // "Chapter 1\n\nIt was a dark night."
 */
export function extractTextFromLexical(lexicalState: string): string {
  // Implementation...
}
```

#### When to Update Documentation

**CLAUDE.md** (this file):
- After making architectural decisions (new patterns, tech choices)
- When adding new code conventions or standards
- Quarterly accuracy review
- Owner: Tech lead

**PROGRESS.md:**
- Daily during active development (update progress %)
- After completing features/tasks
- Weekly summary of completions
- After each sprint/milestone
- Owner: Project manager / Tech lead

**IMPLEMENTATION_PLAN_v2.md:**
- When adding new phases to roadmap
- When adjusting timeline estimates
- After major scope changes
- Monthly roadmap review
- Owner: Product owner

**FEATURES.md:**
- After shipping new user-facing features
- When UX/UI changes significantly
- After adding screenshots/examples
- Based on user feedback
- Owner: Product manager

### 3.4 Git Commit Standards

#### Commit Message Format (Conventional Commits)

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat:` - New feature for users
- `fix:` - Bug fix
- `refactor:` - Code restructuring (no behavior change)
- `docs:` - Documentation only changes
- `test:` - Adding or updating tests
- `chore:` - Build/config changes, dependencies
- `perf:` - Performance improvements
- `style:` - Code style/formatting (no logic change)

**Examples:**

```
feat: Add Timeline Orchestrator travel validation

- Implement character location tracking across events
- Add travel speed profiles (walking, horse, teleport)
- Calculate realistic travel times between locations
- Detect impossible journeys and generate teaching moments
- Create 3 new database tables (travel_legs, location_distances, travel_speed_profiles)

Closes #42
```

```
fix: Chapter serialization includes SQLAlchemy metadata

Previously chapter endpoints returned SQLAlchemy internal metadata
(_sa_instance_state) which caused frontend errors. Now using explicit
serialize_chapter() function to map only expected fields.

Fixes #38
```

```
refactor: Extract Lexical text parsing to utility module

Moved extract_text_from_lexical() from chapters.py to lib/extractText.ts
for reusability across codex and timeline services.

No behavior change.
```

```
docs: Update PROGRESS.md with Phase 4 completion

Phase 4 (Story Structure & Outline Engine) now 100% complete.
Updated metrics, added completion date, moved to completed phases.
```

**Commit Best Practices:**

1. **One logical change per commit**
   - Don't mix feature + bug fix in same commit
   - Don't bundle unrelated refactoring

2. **Subject line: 50 chars max, imperative mood**
   - ✅ "Add Timeline Orchestrator" (imperative)
   - ❌ "Added Timeline Orchestrator" (past tense)
   - ✅ "Fix chapter serialization bug"
   - ❌ "Fixes for chapters" (vague)

3. **Body: Wrap at 72 chars, explain why not what**
   - Code shows what changed
   - Commit message explains why

4. **Reference issues**
   - `Closes #42` (automatically closes issue)
   - `Fixes #38` (automatically closes issue)
   - `Refs #56` (references but doesn't close)

5. **Use conventional commits for automated changelog**
   - Tools can generate CHANGELOG.md from commit history
   - Semantic versioning can be automated

### 3.5 Feature Development Process

#### Step-by-Step Workflow

**1. Planning**
- Review IMPLEMENTATION_PLAN_v2.md for feature specifications
- Create implementation task list (TodoWrite tool for Claude)
- Identify dependencies (database changes, new models, services)

**2. Backend First (if full-stack feature)**

a. **Create models** (`backend/app/models/`)
   ```python
   # app/models/outline.py
   class PlotBeat(Base):
       __tablename__ = "plot_beats"
       id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
       # ... fields
   ```

b. **Generate migration**
   ```bash
   alembic revision --autogenerate -m "Add outline and plot beats tables"
   alembic upgrade head
   ```

c. **Create service** (`backend/app/services/`)
   ```python
   # app/services/outline_service.py
   class OutlineService:
       def create_outline(self, manuscript_id, structure_type):
           # Business logic
   ```

d. **Create routes** (`backend/app/api/routes/`)
   ```python
   # app/api/routes/outlines.py
   @router.post("/outlines")
   async def create_outline(data: CreateOutlineRequest):
       # Call service
   ```

e. **Write tests** (colocated `.test.py` files)

f. **Update API types** (for frontend TypeScript)

**3. Frontend**

a. **Define TypeScript types** (`frontend/src/types/`)
   ```typescript
   // src/types/outline.ts
   export interface PlotBeat {
       id: string;
       name: string;
       // ... fields
   }
   ```

b. **Create Zustand store** (`frontend/src/stores/`)
   ```typescript
   // src/stores/outlineStore.ts
   export const useOutlineStore = create<OutlineStore>((set) => ({
       outlines: [],
       fetchOutlines: async (manuscriptId) => { /* ... */ },
   }));
   ```

c. **Update API client** (`frontend/src/lib/api.ts`)
   ```typescript
   export const outlineApi = {
       create: (data: CreateOutlineRequest) =>
           apiFetch<Outline>('/api/outlines', { method: 'POST', body: data }),
   };
   ```

d. **Build components** (`frontend/src/components/[Feature]/`)
   ```
   components/Outline/
   ├── OutlineSidebar.tsx
   ├── PlotBeatCard.tsx
   ├── CreateOutlineModal.tsx
   └── index.ts
   ```

e. **Integrate with App.tsx** (add to sidebar, routes, etc.)

**4. Testing**
- Unit tests for services (backend)
- Integration tests for routes (backend)
- Component tests for UI (frontend)
- Manual end-to-end testing

**5. Documentation**
- Update PROGRESS.md with feature status
- Add code comments/docstrings
- Update CLAUDE.md if architectural patterns changed
- Update FEATURES.md if user-facing feature

---

## 4. IMPLEMENTATION PATTERNS & EXAMPLES

### 4.1 Backend: Creating a New API Route

**File:** `backend/app/api/routes/example.py`

```python
"""
Example API Routes
Demonstrates standard patterns for Maxwell API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.manuscript import Manuscript
from app.services.example_service import example_service

router = APIRouter(prefix="/api/example", tags=["example"])


# === Request/Response Models ===

class ExampleCreate(BaseModel):
    """Request to create a new example"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    manuscript_id: str

class ExampleUpdate(BaseModel):
    """Request to update an example"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None

class ExampleResponse(BaseModel):
    """Example entity response"""
    id: str
    name: str
    description: str
    manuscript_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models


# === Endpoints ===

@router.post("", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new example entity

    Args:
        data: Example creation request
        db: Database session (injected)

    Returns:
        Created example entity

    Raises:
        HTTPException 404: Manuscript not found
        HTTPException 500: Database error
    """
    try:
        # Validate manuscript exists
        manuscript = db.query(Manuscript).filter(
            Manuscript.id == data.manuscript_id
        ).first()

        if not manuscript:
            raise HTTPException(
                status_code=404,
                detail=f"Manuscript not found: {data.manuscript_id}"
            )

        # Create entity (call service or direct DB)
        example = Example(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description or "",
            manuscript_id=data.manuscript_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(example)
        db.commit()
        db.refresh(example)

        return example

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{manuscript_id}", response_model=List[ExampleResponse])
async def list_examples(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get all examples for a manuscript"""
    examples = db.query(Example).filter(
        Example.manuscript_id == manuscript_id
    ).order_by(Example.created_at.desc()).all()

    return examples


@router.get("/single/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: str,
    db: Session = Depends(get_db)
):
    """Get single example by ID"""
    example = db.query(Example).filter(Example.id == example_id).first()

    if not example:
        raise HTTPException(status_code=404, detail="Example not found")

    return example


@router.put("/{example_id}", response_model=ExampleResponse)
async def update_example(
    example_id: str,
    data: ExampleUpdate,
    db: Session = Depends(get_db)
):
    """Update an example"""
    example = db.query(Example).filter(Example.id == example_id).first()

    if not example:
        raise HTTPException(status_code=404, detail="Example not found")

    # Update fields
    if data.name is not None:
        example.name = data.name
    if data.description is not None:
        example.description = data.description

    example.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(example)

    return example


@router.delete("/{example_id}")
async def delete_example(
    example_id: str,
    db: Session = Depends(get_db)
):
    """Delete an example"""
    example = db.query(Example).filter(Example.id == example_id).first()

    if not example:
        raise HTTPException(status_code=404, detail="Example not found")

    db.delete(example)
    db.commit()

    return {"success": True, "message": "Example deleted"}


@router.post("/analyze")
async def analyze_examples(
    manuscript_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Async analysis using background tasks

    Starts analysis in background, returns immediately.
    Client should poll for results or use WebSocket.
    """
    # Start background processing
    background_tasks.add_task(
        example_service.analyze_manuscript,
        manuscript_id
    )

    return {
        "success": True,
        "message": "Analysis started in background"
    }
```

**Register in `app/main.py`:**
```python
from app.api.routes import chapters, codex, timeline, outlines, example

app.include_router(chapters.router)
app.include_router(codex.router)
app.include_router(timeline.router)
app.include_router(outlines.router)
app.include_router(example.router)  # ← Add new router
```

### 4.2 Frontend: Creating a Feature Component

**File:** `frontend/src/components/Example/ExampleCard.tsx`

```typescript
import React, { useState } from 'react';
import type { Example } from '@/types/example';

interface ExampleCardProps {
  example: Example;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
}

/**
 * ExampleCard component
 *
 * Displays a single example entity with click-to-select and optional delete.
 */
export function ExampleCard({ example, onSelect, onDelete }: ExampleCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click event

    if (!confirm(`Delete "${example.name}"?`)) {
      return;
    }

    setIsDeleting(true);

    try {
      await onDelete?.(example.id);
    } catch (error) {
      console.error('Failed to delete example:', error);
      alert('Failed to delete example. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      onClick={() => onSelect(example.id)}
      className="p-4 bg-vellum-100 border border-bronze-300 rounded-lg
                 hover:border-bronze-500 hover:shadow-md cursor-pointer
                 transition-all duration-200"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(example.id);
        }
      }}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-garamond text-lg text-midnight-900 font-semibold">
            {example.name}
          </h3>
          {example.description && (
            <p className="text-sm text-midnight-700 mt-1 line-clamp-2">
              {example.description}
            </p>
          )}
        </div>

        {onDelete && (
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="ml-2 text-red-600 hover:text-red-800 disabled:opacity-50
                       disabled:cursor-not-allowed"
            aria-label={`Delete ${example.name}`}
          >
            {isDeleting ? '...' : '×'}
          </button>
        )}
      </div>

      <div className="mt-2 text-xs text-midnight-600">
        Created {new Date(example.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
```

**Test:** `frontend/src/components/Example/ExampleCard.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExampleCard } from './ExampleCard';
import type { Example } from '@/types/example';

describe('ExampleCard', () => {
  const mockExample: Example = {
    id: 'ex-123',
    name: 'Test Example',
    description: 'This is a test example',
    manuscript_id: 'ms-456',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  it('renders example name and description', () => {
    const onSelect = vi.fn();

    render(<ExampleCard example={mockExample} onSelect={onSelect} />);

    expect(screen.getByText('Test Example')).toBeInTheDocument();
    expect(screen.getByText('This is a test example')).toBeInTheDocument();
  });

  it('calls onSelect when card is clicked', () => {
    const onSelect = vi.fn();

    render(<ExampleCard example={mockExample} onSelect={onSelect} />);

    fireEvent.click(screen.getByText('Test Example'));

    expect(onSelect).toHaveBeenCalledWith('ex-123');
  });

  it('shows delete button when onDelete provided', () => {
    const onSelect = vi.fn();
    const onDelete = vi.fn();

    render(<ExampleCard example={mockExample} onSelect={onSelect} onDelete={onDelete} />);

    expect(screen.getByLabelText('Delete Test Example')).toBeInTheDocument();
  });

  it('calls onDelete with confirmation when delete button clicked', async () => {
    const onSelect = vi.fn();
    const onDelete = vi.fn().mockResolvedValue(undefined);

    // Mock window.confirm
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<ExampleCard example={mockExample} onSelect={onSelect} onDelete={onDelete} />);

    fireEvent.click(screen.getByLabelText('Delete Test Example'));

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith('ex-123');
    });
  });
});
```

### 4.3 State Management with Zustand

**File:** `frontend/src/stores/exampleStore.ts`

```typescript
import { create } from 'zustand';
import type { Example } from '@/types/example';
import { exampleApi } from '@/lib/api';

interface ExampleStore {
  // State
  examples: Example[];
  selectedExampleId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setExamples: (examples: Example[]) => void;
  addExample: (example: Example) => void;
  updateExample: (id: string, updated: Partial<Example>) => void;
  removeExample: (id: string) => void;
  setSelectedExample: (id: string | null) => void;

  // Async actions
  fetchExamples: (manuscriptId: string) => Promise<void>;
  createExample: (data: CreateExampleRequest) => Promise<Example>;
  deleteExample: (id: string) => Promise<void>;

  // Computed
  selectedExample: () => Example | null;
  getExamplesByType: (type: string) => Example[];
}

export const useExampleStore = create<ExampleStore>((set, get) => ({
  // Initial state
  examples: [],
  selectedExampleId: null,
  isLoading: false,
  error: null,

  // Synchronous actions
  setExamples: (examples) => set({ examples }),

  addExample: (example) => set((state) => ({
    examples: [...state.examples, example],
  })),

  updateExample: (id, updated) => set((state) => ({
    examples: state.examples.map((ex) =>
      ex.id === id ? { ...ex, ...updated } : ex
    ),
  })),

  removeExample: (id) => set((state) => ({
    examples: state.examples.filter((ex) => ex.id !== id),
    selectedExampleId: state.selectedExampleId === id ? null : state.selectedExampleId,
  })),

  setSelectedExample: (id) => set({ selectedExampleId: id }),

  // Async actions
  fetchExamples: async (manuscriptId) => {
    set({ isLoading: true, error: null });

    try {
      const examples = await exampleApi.list(manuscriptId);
      set({ examples, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch examples',
        isLoading: false,
      });
    }
  },

  createExample: async (data) => {
    set({ isLoading: true, error: null });

    try {
      const example = await exampleApi.create(data);
      set((state) => ({
        examples: [...state.examples, example],
        isLoading: false,
      }));
      return example;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create example',
        isLoading: false,
      });
      throw error;
    }
  },

  deleteExample: async (id) => {
    set({ isLoading: true, error: null });

    try {
      await exampleApi.delete(id);
      set((state) => ({
        examples: state.examples.filter((ex) => ex.id !== id),
        selectedExampleId: state.selectedExampleId === id ? null : state.selectedExampleId,
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete example',
        isLoading: false,
      });
      throw error;
    }
  },

  // Computed properties
  selectedExample: () => {
    const { examples, selectedExampleId } = get();
    return examples.find((ex) => ex.id === selectedExampleId) || null;
  },

  getExamplesByType: (type) => {
    const { examples } = get();
    return examples.filter((ex) => ex.type === type);
  },
}));
```

**Usage in components:**
```typescript
import { useExampleStore } from '@/stores/exampleStore';

export function ExampleList() {
  const { examples, fetchExamples, isLoading } = useExampleStore();

  useEffect(() => {
    fetchExamples('ms-123');
  }, []);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {examples.map((ex) => (
        <ExampleCard key={ex.id} example={ex} onSelect={() => {}} />
      ))}
    </div>
  );
}
```

### 4.4 API Client Pattern

**File:** `frontend/src/lib/api.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Type-safe API fetch wrapper
 *
 * Handles JSON serialization, error responses, and type safety.
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// Example API module
export const exampleApi = {
  /**
   * List all examples for a manuscript
   */
  async list(manuscriptId: string): Promise<Example[]> {
    return apiFetch<Example[]>(`/api/example/${manuscriptId}`);
  },

  /**
   * Get single example by ID
   */
  async get(id: string): Promise<Example> {
    return apiFetch<Example>(`/api/example/single/${id}`);
  },

  /**
   * Create a new example
   */
  async create(data: CreateExampleRequest): Promise<Example> {
    return apiFetch<Example>('/api/example', {
      method: 'POST',
      body: data,
    });
  },

  /**
   * Update an example
   */
  async update(id: string, data: UpdateExampleRequest): Promise<Example> {
    return apiFetch<Example>(`/api/example/${id}`, {
      method: 'PUT',
      body: data,
    });
  },

  /**
   * Delete an example
   */
  async delete(id: string): Promise<void> {
    await apiFetch<{ success: boolean }>(`/api/example/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Start async analysis
   */
  async analyze(manuscriptId: string): Promise<void> {
    await apiFetch<{ success: boolean }>('/api/example/analyze', {
      method: 'POST',
      body: { manuscript_id: manuscriptId },
    });
  },
};
```

### 4.5 Database Model Pattern

**File:** `backend/app/models/example.py`

```python
"""
Example domain models
Demonstrates Maxwell database model patterns
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Example(Base):
    """
    Example entity with relationships

    Demonstrates standard model patterns:
    - UUID primary key
    - Foreign key to manuscript
    - Timestamps (created_at, updated_at)
    - JSON column for flexible metadata
    - Relationship to parent manuscript
    """
    __tablename__ = "examples"

    # Primary key (UUID string)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Attributes
    name = Column(String, nullable=False)
    description = Column(Text, default="")

    # Optional type field (e.g., "CHARACTER", "LOCATION")
    type = Column(String, nullable=True)

    # Flexible JSON storage for varying attributes
    metadata = Column(JSON, default=dict)

    # Timestamps (auto-managed)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="examples")

    def __repr__(self):
        return f"<Example(id={self.id}, name='{self.name}', type='{self.type}')>"

    def to_dict(self):
        """Convert to dictionary (for API responses)"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "metadata": self.metadata,
            "manuscript_id": self.manuscript_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

**Register in `backend/app/models/__init__.py`:**
```python
from app.models.manuscript import Manuscript, Chapter, Scene
from app.models.entity import Entity, Relationship
from app.models.timeline import TimelineEvent, CharacterLocation
from app.models.outline import Outline, PlotBeat
from app.models.example import Example  # ← Add new model
```

**Update parent model relationship (`manuscript.py`):**
```python
class Manuscript(Base):
    __tablename__ = "manuscripts"

    # ... existing fields

    # Relationships
    examples = relationship("Example", back_populates="manuscript", cascade="all, delete-orphan")
```

---

## 5. QUICK REFERENCE

### 5.1 Common Commands

**Backend:**
```bash
# Navigate to backend
cd /Users/josephrodden/Maxwell/backend

# Activate virtual environment
source venv/bin/activate

# Start dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest                        # All tests
pytest -v                     # Verbose
pytest --cov                  # With coverage
pytest app/api/routes/chapters.test.py  # Specific file

# Database migrations
alembic upgrade head          # Apply all migrations
alembic current               # Show current migration
alembic revision --autogenerate -m "description"  # Create migration

# Check for errors
python -m app.main            # Import check
```

**Frontend:**
```bash
# Navigate to frontend
cd /Users/josephrodden/Maxwell/frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test                      # All tests
npm test EntityCard           # Specific test
npm run coverage              # Coverage report

# Type checking
npx tsc --noEmit              # Check types without building
```

### 5.2 File Templates

When creating new features, copy these patterns:

**New API Route:**
- Template: `backend/app/api/routes/chapters.py`
- Register in: `backend/app/main.py`
- Test file: `{route_name}.test.py` (colocated)

**New Component:**
- Template: `frontend/src/components/Codex/EntityCard.tsx`
- Export from: `frontend/src/components/{Feature}/index.ts`
- Test file: `{ComponentName}.test.tsx` (colocated)

**New Store:**
- Template: `frontend/src/stores/timelineStore.ts`
- Import in components as needed

**New Model:**
- Template: `backend/app/models/entity.py`
- Import in: `backend/app/models/__init__.py`
- Create migration: `alembic revision --autogenerate`

### 5.3 Key Project Files

**Backend:**
- Main app: `/Users/josephrodden/Maxwell/backend/app/main.py`
- Database config: `/Users/josephrodden/Maxwell/backend/app/database.py`
- API routes: `/Users/josephrodden/Maxwell/backend/app/api/routes/`
- Services: `/Users/josephrodden/Maxwell/backend/app/services/`
- Models: `/Users/josephrodden/Maxwell/backend/app/models/`
- Migrations: `/Users/josephrodden/Maxwell/backend/migrations/versions/`

**Frontend:**
- Root component: `/Users/josephrodden/Maxwell/frontend/src/App.tsx`
- API client: `/Users/josephrodden/Maxwell/frontend/src/lib/api.ts`
- Components: `/Users/josephrodden/Maxwell/frontend/src/components/`
- Stores: `/Users/josephrodden/Maxwell/frontend/src/stores/`
- Types: `/Users/josephrodden/Maxwell/frontend/src/types/`

**Documentation:**
- Architecture (this file): `/Users/josephrodden/Maxwell/CLAUDE.md`
- Progress tracking: `/Users/josephrodden/Maxwell/PROGRESS.md`
- Implementation roadmap: `/Users/josephrodden/Maxwell/IMPLEMENTATION_PLAN_v2.md`
- Features guide: `/Users/josephrodden/Maxwell/FEATURES.md`

### 5.4 Design System

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

---

**Last Updated:** 2026-01-07
**Version:** 1.0
**Next Review:** 2026-02-07 (monthly)

**Feedback:** If you find errors or have suggestions for this guide, update directly or create an issue in the project repository.
