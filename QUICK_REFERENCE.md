# Maxwell Quick Reference

**Last Updated:** 2026-01-08
**Related Docs:** [CLAUDE.md](CLAUDE.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [PATTERNS.md](PATTERNS.md) | [WORKFLOW.md](WORKFLOW.md)

---

## Common Commands

### Backend

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

### Frontend

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

---

## Directory Structure

### Backend
```
backend/
├── app/
│   ├── api/routes/          # API endpoint handlers
│   │   ├── chapters.py
│   │   ├── codex.py
│   │   ├── timeline.py
│   │   ├── outlines.py
│   │   └── brainstorming.py
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── manuscript.py
│   │   ├── entity.py
│   │   ├── timeline.py
│   │   ├── outline.py
│   │   └── brainstorm.py
│   ├── services/            # Business logic layer
│   │   ├── codex_service.py
│   │   ├── nlp_service.py
│   │   ├── timeline_service.py
│   │   └── story_structures.py
│   ├── database.py          # SQLAlchemy setup
│   ├── main.py              # FastAPI app
│   └── __init__.py
├── migrations/              # Alembic migrations
├── tests/                   # Integration tests
├── data/                    # Local storage
│   ├── codex.db            # SQLite database
│   └── manuscripts/        # Git repositories
└── requirements.txt
```

### Frontend
```
frontend/
└── src/
    ├── components/          # React components (feature-based)
    │   ├── Codex/          # Entity management (8 components)
    │   ├── Timeline/       # Timeline tools (9 components)
    │   ├── Outline/        # Story structure (5 components)
    │   ├── Brainstorming/  # Ideation (5 components)
    │   ├── Editor/         # Writing interface
    │   └── common/         # Shared components
    ├── stores/             # Zustand state management
    │   ├── manuscriptStore.ts
    │   ├── codexStore.ts
    │   ├── timelineStore.ts
    │   ├── outlineStore.ts
    │   └── brainstormStore.ts
    ├── types/              # TypeScript types
    ├── lib/                # Utilities
    │   ├── api.ts          # API client
    │   └── extractText.ts
    ├── hooks/              # Custom React hooks
    ├── App.tsx
    └── main.tsx
```

---

## Key File Locations

### Backend
- **Main app:** `backend/app/main.py`
- **Database config:** `backend/app/database.py`
- **API routes:** `backend/app/api/routes/`
- **Services:** `backend/app/services/`
- **Models:** `backend/app/models/`
- **Migrations:** `backend/migrations/versions/`

### Frontend
- **Root component:** `frontend/src/App.tsx`
- **API client:** `frontend/src/lib/api.ts`
- **Components:** `frontend/src/components/`
- **Stores:** `frontend/src/stores/`
- **Types:** `frontend/src/types/`

### Documentation
- **Quick start:** `CLAUDE.md`
- **Architecture:** `ARCHITECTURE.md`
- **Code patterns:** `PATTERNS.md`
- **Workflow:** `WORKFLOW.md`
- **Progress tracking:** `PROGRESS.md`
- **Roadmap:** `IMPLEMENTATION_PLAN_v2.md`
- **Features:** `FEATURES.md`

---

## File Templates

### New API Route
- **Template:** `backend/app/api/routes/chapters.py`
- **Register in:** `backend/app/main.py`
- **Test file:** Colocated `{route_name}.test.py`

### New Component
- **Template:** `frontend/src/components/Codex/EntityCard.tsx`
- **Export from:** `frontend/src/components/{Feature}/index.ts`
- **Test file:** Colocated `{ComponentName}.test.tsx`

### New Store
- **Template:** `frontend/src/stores/timelineStore.ts`
- **Import in:** Components as needed

### New Model
- **Template:** `backend/app/models/entity.py`
- **Import in:** `backend/app/models/__init__.py`
- **Migration:** `alembic revision --autogenerate`

---

## API Endpoints

### Manuscripts & Chapters
```
GET    /api/manuscripts
POST   /api/manuscripts
GET    /api/manuscripts/{id}
PUT    /api/manuscripts/{id}
DELETE /api/manuscripts/{id}

GET    /api/chapters/manuscript/{manuscript_id}
POST   /api/chapters
GET    /api/chapters/{id}
PUT    /api/chapters/{id}
DELETE /api/chapters/{id}
```

### Codex (Entities)
```
GET    /api/codex/entities/{manuscript_id}
POST   /api/codex/entities
PUT    /api/codex/entities/{id}
DELETE /api/codex/entities/{id}

GET    /api/codex/relationships/{manuscript_id}
POST   /api/codex/relationships
DELETE /api/codex/relationships/{id}

GET    /api/codex/suggestions/{manuscript_id}
POST   /api/codex/suggestions/accept/{id}
DELETE /api/codex/suggestions/{id}
```

### Timeline
```
GET    /api/timeline/events/{manuscript_id}
POST   /api/timeline/events
PUT    /api/timeline/events/{id}
DELETE /api/timeline/events/{id}

POST   /api/timeline/validate/{manuscript_id}
GET    /api/timeline/inconsistencies/{manuscript_id}
POST   /api/timeline/calculate-travel
GET    /api/timeline/stats/{manuscript_id}
```

### Outlines
```
GET    /api/outlines/manuscript/{manuscript_id}
POST   /api/outlines
GET    /api/outlines/{id}
PUT    /api/outlines/{id}
DELETE /api/outlines/{id}

POST   /api/outlines/generate
GET    /api/outlines/templates
```

---

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=sqlite:///./data/codex.db

# API Keys (user-provided)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# NLP
SPACY_MODEL=en_core_web_sm

# Git
GIT_USER_NAME=Maxwell
GIT_USER_EMAIL=noreply@maxwell.local
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## Design System

### Colors (Tailwind)
- `vellum-*` - Warm cream background (50-900)
- `bronze-*` - Copper accents (300, 500, 700)
- `midnight-*` - Deep text color (600, 700, 900)

### Typography
- `font-garamond` - Headings and display text
- `font-sans` - Body text and UI elements

### Common Patterns
```css
/* Cards */
bg-vellum-100 border border-bronze-300 rounded-lg

/* Hover states */
hover:border-bronze-500 hover:shadow-md

/* Buttons */
bg-bronze-500 text-white px-4 py-2 rounded

/* Transitions */
transition-all duration-200
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.13+

# Reinstall dependencies
pip install -r requirements.txt

# Check database
alembic current
alembic upgrade head

# Test imports
python -c "from app.main import app; print('✅ OK')"
```

### Frontend won't build
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check TypeScript
npx tsc --noEmit

# Check for port conflicts
lsof -i :5173
```

### Database issues
```bash
# Reset database (⚠️ destroys data)
rm data/codex.db
alembic upgrade head

# Check schema
sqlite3 data/codex.db ".schema"

# Query database
sqlite3 data/codex.db "SELECT * FROM manuscripts;"
```

---

## Useful Snippets

### Create a test database
```python
# In tests/conftest.py
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Mock API calls in tests
```typescript
// In component tests
import { vi } from 'vitest';

vi.mock('@/lib/api', () => ({
  exampleApi: {
    list: vi.fn().mockResolvedValue([mockExample]),
    create: vi.fn().mockResolvedValue(mockExample),
  },
}));
```

### Background task pattern
```python
from fastapi import BackgroundTasks

@router.post("/analyze")
async def analyze(manuscript_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(nlp_service.analyze, manuscript_id)
    return {"success": True, "message": "Analysis started"}
```

---

## Git Workflow

### Feature branch
```bash
git checkout -b feature/ai-outline-suggestions
# ... make changes
git add .
git commit -m "feat: Add AI outline suggestions panel"
git push origin feature/ai-outline-suggestions
```

### Commit types
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code restructuring
- `docs:` - Documentation
- `test:` - Tests
- `chore:` - Build/config

### View changes
```bash
git status
git diff
git log --oneline -10
```
