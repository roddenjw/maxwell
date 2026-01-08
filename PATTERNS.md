# Maxwell Code Patterns & Examples

**Last Updated:** 2026-01-08
**Related Docs:** [CLAUDE.md](CLAUDE.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [WORKFLOW.md](WORKFLOW.md)

---

## File Naming Conventions

### Backend Python
- **Models:** `{domain}.py` → `manuscript.py`, `entity.py`, `timeline.py`
- **Services:** `{domain}_service.py` → `codex_service.py`, `timeline_service.py`
- **Routes:** `{domain}.py` → `chapters.py`, `outlines.py`, `timeline.py`
- **Tests:** `{file}.test.py` (colocated)
- **Migrations:** `{hash}_{description}.py`

### Frontend TypeScript
- **Components:** `PascalCase.tsx` → `EntityCard.tsx`, `TimelineSidebar.tsx`
- **Stores:** `{domain}Store.ts` → `codexStore.ts`, `timelineStore.ts`
- **Types:** `{domain}.ts` → `timeline.ts`, `outline.ts`
- **Utilities:** `camelCase.ts` → `extractText.ts`, `formatDate.ts`
- **Hooks:** `use{Name}.ts` → `useKeyboardShortcuts.ts`
- **Tests:** `{file}.test.tsx` (colocated)

---

## Import Order Standards

### Python (PEP 8 compliant)
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
```

### TypeScript (ESLint-compatible)
```typescript
// 1. React and external libraries
import React, { useState, useEffect } from 'react';
import { create } from 'zustand';

// 2. Type imports
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

---

## Backend Patterns

### Creating a New API Route

**File:** `backend/app/api/routes/example.py`

```python
"""Example API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.manuscript import Manuscript

router = APIRouter(prefix="/api/example", tags=["example"])


# === Request/Response Models ===

class ExampleCreate(BaseModel):
    """Request to create a new example"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    manuscript_id: str

class ExampleResponse(BaseModel):
    """Example entity response"""
    id: str
    name: str
    description: str
    manuscript_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Endpoints ===

@router.post("", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    db: Session = Depends(get_db)
):
    """Create a new example entity"""
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

        # Create entity
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
```

**Register in `app/main.py`:**
```python
from app.api.routes import chapters, codex, timeline, example

app.include_router(example.router)  # ← Add new router
```

### Database Model Pattern

**File:** `backend/app/models/example.py`

```python
"""Example domain models"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Example(Base):
    """Example entity with relationships"""
    __tablename__ = "examples"

    # Primary key (UUID string)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Attributes
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    type = Column(String, nullable=True)

    # Flexible JSON storage
    metadata = Column(JSON, default=dict)

    # Timestamps (auto-managed)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="examples")

    def __repr__(self):
        return f"<Example(id={self.id}, name='{self.name}')>"

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

### Service Pattern

**File:** `backend/app/services/example_service.py`

```python
"""Example service - Business logic layer"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.example import Example
from app.models.manuscript import Manuscript


class ExampleService:
    """Service for example-related business logic"""

    def create_example(
        self,
        db: Session,
        manuscript_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Example:
        """Create a new example with validation"""
        # Business logic here
        example = Example(
            manuscript_id=manuscript_id,
            name=name,
            description=description or "",
            created_at=datetime.utcnow()
        )
        db.add(example)
        db.commit()
        db.refresh(example)
        return example

    def validate_example(self, db: Session, example_id: str) -> bool:
        """Validate example meets business rules"""
        example = db.query(Example).filter(Example.id == example_id).first()
        if not example:
            return False
        # Validation logic
        return True


# Singleton instance
example_service = ExampleService()
```

---

## Frontend Patterns

### Component Pattern

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
 * Displays a single example entity with click-to-select and optional delete.
 */
export function ExampleCard({ example, onSelect, onDelete }: ExampleCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();

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
            className="ml-2 text-red-600 hover:text-red-800"
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

### Zustand Store Pattern

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
        error: error instanceof Error ? error.message : 'Failed to fetch',
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
        error: error instanceof Error ? error.message : 'Failed to create',
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

### API Client Pattern

**File:** `frontend/src/lib/api.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Type-safe API fetch wrapper
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
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Example API module
export const exampleApi = {
  async list(manuscriptId: string): Promise<Example[]> {
    return apiFetch<Example[]>(`/api/example/${manuscriptId}`);
  },

  async get(id: string): Promise<Example> {
    return apiFetch<Example>(`/api/example/single/${id}`);
  },

  async create(data: CreateExampleRequest): Promise<Example> {
    return apiFetch<Example>('/api/example', {
      method: 'POST',
      body: data,
    });
  },

  async update(id: string, data: UpdateExampleRequest): Promise<Example> {
    return apiFetch<Example>(`/api/example/${id}`, {
      method: 'PUT',
      body: data,
    });
  },

  async delete(id: string): Promise<void> {
    await apiFetch<{ success: boolean }>(`/api/example/${id}`, {
      method: 'DELETE',
    });
  },
};
```

---

## Feature-Based Organization

**Pattern:** Colocate related components in feature directories with barrel exports.

**Example: Codex Feature**
```
components/Codex/
├── CodexSidebar.tsx         # Main container
├── EntityList.tsx           # Entity browsing
├── EntityCard.tsx           # Single entity display
├── EntityDetail.tsx         # Entity editing modal
├── SuggestionQueue.tsx      # NLP-generated suggestions
├── RelationshipGraph.tsx    # Force-directed graph
├── MergeEntitiesModal.tsx   # Entity merging UI
└── index.ts                 # Barrel export

// index.ts
export { default as CodexSidebar } from './CodexSidebar';
export { default as EntityList } from './EntityList';
export { default as EntityCard } from './EntityCard';
// ... etc
```

**Usage:**
```typescript
import { EntityList, EntityCard, CodexSidebar } from '@/components/Codex';
```

---

## Naming Standards

### Components
- PascalCase: `EntityCard`, `TimelineSidebar`
- Filename matches component name
- Props interface: `{ComponentName}Props`

### Functions
- camelCase: `createEntity()`, `fetchTimeline()`, `extractText()`
- Verb-first naming
- Boolean prefixes: `isValid()`, `hasPermission()`, `canEdit()`
- Event handlers: `handleClick()`, `handleSubmit()`

### Constants
- SCREAMING_SNAKE_CASE for true constants:
  ```typescript
  const API_BASE_URL = 'http://localhost:8000';
  const MAX_SUGGESTIONS = 10;
  ```
- camelCase for configuration objects:
  ```typescript
  const editorConfig = {
    theme: 'maxwell',
    autosave: true,
  };
  ```

### Types/Interfaces
- PascalCase: `Entity`, `TimelineEvent`, `ApiResponse<T>`
- Suffix with purpose:
  - Request types: `CreateEntityRequest`
  - Response types: `ChapterResponse`
  - Props: `EntityCardProps`
  - Store interfaces: `CodexStore`
