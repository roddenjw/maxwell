# Maxwell/Codex IDE: Developer Quick-Start Guide

**Last Updated**: 2025-12-15
**Estimated Setup Time**: 30-60 minutes

---

## Overview

This guide will get you from zero to running Maxwell locally in under an hour. You'll have:
- ✅ Frontend running (React + Vite)
- ✅ Backend API running (Python + FastAPI)
- ✅ Database initialized (SQLite)
- ✅ Editor working with auto-save
- ✅ Ready to start developing new features

---

## Prerequisites

Before you begin, ensure you have:

| Tool | Version | Installation |
|------|---------|--------------|
| **Node.js** | 18.x or 20.x | [nodejs.org](https://nodejs.org) |
| **Python** | 3.11+ | [python.org](https://python.org) |
| **Git** | Latest | [git-scm.com](https://git-scm.com) |
| **Code Editor** | Any | VS Code recommended |

### Verify Installation

```bash
node --version  # Should show v18.x or v20.x
python3 --version  # Should show 3.11 or higher
git --version
```

---

## Quick Start (5 Minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/maxwell.git
cd maxwell
```

### 2. Install Dependencies

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd ../backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Development Servers

**Terminal 1 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 4. Open the App

Navigate to: **http://localhost:5173**

You should see the Maxwell welcome screen!

---

## Detailed Setup

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18
- Vite (build tool)
- Lexical (rich text editor)
- TanStack Query (server state)
- Zustand (client state)
- Tailwind CSS (styling)
- TypeScript

#### 2. Configure Environment

Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

#### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at: **http://localhost:5173**

#### 4. Available Scripts

```bash
npm run dev          # Start dev server (hot reload)
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler
npm run test         # Run Vitest tests
```

---

### Backend Setup

#### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- Alembic (migrations)
- spaCy (NLP - optional for Phase 2)
- Pydantic (validation)

#### 3. Download spaCy Model (Optional - Phase 2+)

```bash
python -m spacy download en_core_web_lg
```

#### 4. Configure Environment

Create `.env`:
```env
# Database
DATABASE_URL=sqlite:///./maxwell.db

# API Keys (Phase 3+)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Environment
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### 5. Initialize Database

```bash
# Create initial database
alembic upgrade head
```

#### 6. Start Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**

API docs: **http://localhost:8000/docs** (Swagger UI)

#### 7. Available Commands

```bash
# Start server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head
alembic downgrade -1

# Create migration
alembic revision --autogenerate -m "description"

# Run tests
pytest
pytest --cov=app tests/

# Format code
black app/
isort app/

# Lint code
ruff check app/
mypy app/
```

---

## Project Structure

```
maxwell/
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Editor/       # Lexical editor components
│   │   │   ├── Timeline/     # Timeline Orchestrator (Phase 2A)
│   │   │   ├── Codex/        # Knowledge graph (Phase 2)
│   │   │   └── ...
│   │   ├── stores/           # Zustand state stores
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utilities
│   │   ├── types/            # TypeScript types
│   │   └── App.tsx           # Root component
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                   # Python backend
│   ├── app/
│   │   ├── api/              # API routes
│   │   │   ├── manuscripts.py
│   │   │   ├── timeline.py   # Timeline Orchestrator routes
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── manuscript_service.py
│   │   │   ├── timeline_orchestrator_service.py
│   │   │   └── ...
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Pytest tests
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── pyproject.toml
│
├── files/                     # Documentation
│   ├── CoreFeatures/
│   │   ├── ARCHITECTURE.md
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   ├── API_DOCUMENTATION.md
│   │   ├── DATABASE_MIGRATION_PLAN.md
│   │   └── ...
│   └── fileTimelineOrchestrator/
│       └── ...
│
└── data/                      # Local data storage
    ├── manuscripts/
    ├── chroma/               # Vector database
    └── graph/                # Knowledge graph
```

---

## Development Workflow

### 1. Pick a Task

Check the implementation plan:
```bash
cat files/CoreFeatures/IMPLEMENTATION_PLAN.md
```

Or review the progress tracker:
```bash
cat files/CoreFeatures/PROGRESS.md
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/timeline-event-form
```

### 3. Develop the Feature

**Frontend Example** (React component):
```typescript
// frontend/src/components/Timeline/TimelineEventCard.tsx

import React from 'react';

interface TimelineEventCardProps {
  event: {
    id: string;
    name: string;
    storyDate: string;
    characterIds: string[];
  };
}

export function TimelineEventCard({ event }: TimelineEventCardProps) {
  return (
    <div className="bg-vellum border-l-4 border-bronze p-4 rounded">
      <h3 className="font-garamond text-lg text-midnight">{event.name}</h3>
      <p className="text-sm text-faded-ink">
        {new Date(event.storyDate).toLocaleDateString()}
      </p>
    </div>
  );
}
```

**Backend Example** (API route):
```python
# backend/app/api/timeline.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/timeline", tags=["Timeline"])

class TimelineEventCreate(BaseModel):
    name: str
    story_date: str
    character_ids: list[str]

@router.post("/events")
async def create_event(event: TimelineEventCreate):
    # TODO: Save to database
    return {
        "success": True,
        "data": {
            "id": "evt-uuid-1234",
            "name": event.name,
            "storyDate": event.story_date,
            "characterIds": event.character_ids
        }
    }
```

### 4. Test Your Changes

**Frontend:**
```bash
npm run test
npm run type-check
npm run lint
```

**Backend:**
```bash
pytest tests/
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat(timeline): add TimelineEventCard component"
```

Commit message format:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Build/config changes

### 6. Create Pull Request

```bash
git push origin feature/timeline-event-form
```

Then create a PR on GitHub.

---

## Common Tasks

### Add a New API Endpoint

1. **Define Pydantic model:**
   ```python
   # backend/app/models/timeline.py
   from pydantic import BaseModel

   class TimelineEvent(BaseModel):
       name: str
       story_date: str
   ```

2. **Create route:**
   ```python
   # backend/app/api/timeline.py
   @router.post("/events")
   async def create_event(event: TimelineEvent):
       return {"success": True, "data": event}
   ```

3. **Register router:**
   ```python
   # backend/app/main.py
   from app.api import timeline

   app.include_router(timeline.router, prefix="/api")
   ```

4. **Test endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/timeline/events \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Event", "story_date": "2024-01-01"}'
   ```

### Add a New React Component

1. **Create component:**
   ```typescript
   // frontend/src/components/Timeline/TimelineControls.tsx
   export function TimelineControls() {
     return <div>Controls</div>;
   }
   ```

2. **Export from index:**
   ```typescript
   // frontend/src/components/Timeline/index.ts
   export { TimelineControls } from './TimelineControls';
   ```

3. **Use in parent:**
   ```typescript
   import { TimelineControls } from './components/Timeline';

   export function App() {
     return <TimelineControls />;
   }
   ```

### Run Database Migration

1. **Create migration:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "add timeline tables"
   ```

2. **Review generated migration:**
   ```bash
   cat alembic/versions/XXXXXX_add_timeline_tables.py
   ```

3. **Run migration:**
   ```bash
   alembic upgrade head
   ```

4. **Verify:**
   ```bash
   sqlite3 maxwell.db
   > .tables
   > .schema timeline_events
   ```

### Add State Management (Zustand)

1. **Create store:**
   ```typescript
   // frontend/src/stores/timelineStore.ts
   import { create } from 'zustand';

   interface TimelineStore {
     events: TimelineEvent[];
     addEvent: (event: TimelineEvent) => void;
   }

   export const useTimelineStore = create<TimelineStore>((set) => ({
     events: [],
     addEvent: (event) => set((state) => ({
       events: [...state.events, event]
     }))
   }));
   ```

2. **Use in component:**
   ```typescript
   import { useTimelineStore } from '@/stores/timelineStore';

   export function Timeline() {
     const { events, addEvent } = useTimelineStore();

     return <div>{events.length} events</div>;
   }
   ```

---

## Troubleshooting

### Frontend Won't Start

**Error**: `Cannot find module '@lexical/react'`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

### Database Errors

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by '...'`

**Solution**:
```bash
# Reset database
rm maxwell.db
alembic upgrade head
```

---

### CORS Errors in Browser

**Error**: `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**Solution**:
Check `backend/.env`:
```env
CORS_ORIGINS=http://localhost:5173
```

And verify in `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## IDE Setup

### VS Code (Recommended)

**Install Extensions:**
```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma"
  ]
}
```

**Settings (`.vscode/settings.json`):**
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true
}
```

**Tasks (`.vscode/tasks.json`):**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Frontend",
      "type": "shell",
      "command": "cd frontend && npm run dev",
      "isBackground": true
    },
    {
      "label": "Start Backend",
      "type": "shell",
      "command": "cd backend && source venv/bin/activate && uvicorn app.main:app --reload",
      "isBackground": true
    }
  ]
}
```

---

## Testing

### Frontend Tests (Vitest)

```bash
cd frontend
npm run test
```

**Example test:**
```typescript
// frontend/src/components/Timeline/__tests__/TimelineEventCard.test.tsx
import { render, screen } from '@testing-library/react';
import { TimelineEventCard } from '../TimelineEventCard';

test('renders event name', () => {
  const event = {
    id: 'evt-1',
    name: 'Test Event',
    storyDate: '2024-01-01',
    characterIds: []
  };

  render(<TimelineEventCard event={event} />);
  expect(screen.getByText('Test Event')).toBeInTheDocument();
});
```

### Backend Tests (Pytest)

```bash
cd backend
pytest tests/
```

**Example test:**
```python
# backend/tests/api/test_timeline.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_event():
    response = client.post("/api/timeline/events", json={
        "name": "Test Event",
        "story_date": "2024-01-01",
        "character_ids": []
    })

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["name"] == "Test Event"
```

---

## Performance Tips

### Frontend

1. **Enable React DevTools**
   ```bash
   # Install React DevTools browser extension
   ```

2. **Use React.memo for expensive components**
   ```typescript
   export const TimelineEventCard = React.memo(({ event }) => {
     // Component logic
   });
   ```

3. **Lazy load routes**
   ```typescript
   const Timeline = lazy(() => import('./components/Timeline'));
   ```

### Backend

1. **Use async/await for I/O**
   ```python
   @router.get("/events")
   async def get_events():
       events = await db.query(TimelineEvent).all()
       return events
   ```

2. **Add database indexes**
   ```sql
   CREATE INDEX idx_timeline_events_project
   ON timeline_events(project_id);
   ```

3. **Use connection pooling (production)**
   ```python
   engine = create_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

---

## Next Steps

Now that you're set up, you can:

1. **Complete Phase 1** (Weeks 2-3)
   - Implement versioning backend
   - Build Time Machine UI

2. **Start Phase 2** (Weeks 4-6)
   - Set up spaCy for NLP
   - Build Codex UI

3. **Start Phase 2A** (Weeks 7-8) ⭐
   - Implement Timeline Orchestrator
   - Build timeline validation service

---

## Resources

- **Documentation**: `/files/CoreFeatures/`
- **API Docs**: http://localhost:8000/docs
- **React Docs**: https://react.dev
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Lexical Docs**: https://lexical.dev
- **Tailwind Docs**: https://tailwindcss.com

---

## Getting Help

1. **Check documentation** in `/files/CoreFeatures/`
2. **Search existing issues** on GitHub
3. **Join Discord** (if available)
4. **Ask in team chat**

---

**Happy coding! 🚀**

---

**Last Updated**: 2025-12-15
**Maintained By**: Development Team
