# Maxwell Development Workflow

**Last Updated:** 2026-01-08
**Related Docs:** [CLAUDE.md](CLAUDE.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [PATTERNS.md](PATTERNS.md)

---

## Testing Standards

### Philosophy
Colocate tests next to source files for discoverability and maintenance.

### Structure

**Backend:**
```
backend/app/api/routes/
├── chapters.py
└── chapters.test.py         # ← Colocated unit test

backend/app/services/
├── timeline_service.py
└── timeline_service.test.py # ← Colocated unit test
```

**Frontend:**
```
frontend/src/components/Codex/
├── EntityCard.tsx
├── EntityCard.test.tsx      # ← Colocated unit test
└── EntityCard.stories.tsx   # ← Storybook story (future)
```

Integration tests stay in `/backend/tests/` directory.

### When to Write Tests

**Required:**
1. **Critical business logic** - Services, validators, algorithms
2. **Data transformation** - JSON parsing, text extraction, serialization
3. **Complex algorithms** - Graph traversal, conflict detection, NLP
4. **Bug fixes** - Regression test for each bug fixed
5. **Public APIs** - All REST endpoint edge cases

**Optional:**
1. Simple CRUD routes (get by ID, delete by ID)
2. UI components without complex logic (mostly presentational)
3. Type definitions and interfaces
4. Configuration files

### Coverage Expectations
- **Services:** 70%+ coverage (critical business logic)
- **Routes:** 50%+ coverage (API contracts)
- **Utilities:** 80%+ coverage (shared functions)
- **Overall project:** 80%+ target

### Running Tests

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

---

## Database Migrations

### Creating Migrations

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

### Migration Naming

Use descriptive names:
- ✅ `add_timeline_orchestrator_models`
- ✅ `add_outline_and_plot_beats_tables`
- ✅ `genericize_story_structure_names`
- ❌ `update_db` (too vague)
- ❌ `schema_changes` (not descriptive)

### Migration Best Practices

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

---

## Git Commit Standards

### Commit Message Format (Conventional Commits)

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

### Commit Best Practices

1. **One logical change per commit**
   - Don't mix feature + bug fix in same commit
   - Don't bundle unrelated refactoring

2. **Subject line: 50 chars max, imperative mood**
   - ✅ "Add Timeline Orchestrator" (imperative)
   - ❌ "Added Timeline Orchestrator" (past tense)

3. **Body: Wrap at 72 chars, explain why not what**
   - Code shows what changed
   - Commit message explains why

4. **Reference issues**
   - `Closes #42` (automatically closes issue)
   - `Fixes #38` (automatically closes issue)
   - `Refs #56` (references but doesn't close)

---

## Feature Development Process

### Step-by-Step Workflow

**1. Planning**
- Review IMPLEMENTATION_PLAN_v2.md for feature specifications
- Create implementation task list
- Identify dependencies (database changes, new models, services)

**2. Backend First (if full-stack feature)**

a. **Create models** (`backend/app/models/`)
   ```python
   class PlotBeat(Base):
       __tablename__ = "plot_beats"
       id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
   ```

b. **Generate migration**
   ```bash
   alembic revision --autogenerate -m "Add outline and plot beats tables"
   alembic upgrade head
   ```

c. **Create service** (`backend/app/services/`)
   ```python
   class OutlineService:
       def create_outline(self, manuscript_id, structure_type):
           # Business logic
   ```

d. **Create routes** (`backend/app/api/routes/`)
   ```python
   @router.post("/outlines")
   async def create_outline(data: CreateOutlineRequest):
       # Call service
   ```

e. **Write tests** (colocated `.test.py` files)

f. **Update API types** (for frontend TypeScript)

**3. Frontend**

a. **Define TypeScript types** (`frontend/src/types/`)
   ```typescript
   export interface PlotBeat {
       id: string;
       name: string;
   }
   ```

b. **Create Zustand store** (`frontend/src/stores/`)
   ```typescript
   export const useOutlineStore = create<OutlineStore>((set) => ({
       outlines: [],
       fetchOutlines: async (manuscriptId) => { /* ... */ },
   }));
   ```

c. **Update API client** (`frontend/src/lib/api.ts`)
   ```typescript
   export const outlineApi = {
       create: (data) => apiFetch('/api/outlines', { method: 'POST', body: data }),
   };
   ```

d. **Build components** (`frontend/src/components/[Feature]/`)

e. **Integrate with App.tsx** (add to sidebar, routes, etc.)

**4. Testing**
- Unit tests for services (backend)
- Integration tests for routes (backend)
- Component tests for UI (frontend)
- Manual end-to-end testing

**5. Documentation**
- Update PROGRESS.md with feature status
- Add code comments/docstrings
- Update ARCHITECTURE.md if architectural patterns changed
- Update FEATURES.md if user-facing feature

---

## Documentation Standards

### Code Comments

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
        >>> issues = validate_timeline_orchestrator("ms-123")
        >>> print(f"Found {len(issues)} timeline issues")
    """
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

### When to Update Documentation

**ARCHITECTURE.md:**
- After making architectural decisions (new patterns, tech choices)
- When adding new code conventions or standards
- Quarterly accuracy review

**WORKFLOW.md:**
- When changing development processes
- Adding new tools or commands
- Updating testing standards

**PATTERNS.md:**
- When establishing new code patterns
- Adding reusable examples
- Documenting common solutions

**PROGRESS.md:**
- Daily during active development (update progress %)
- After completing features/tasks
- Weekly summary of completions
- After each sprint/milestone

**IMPLEMENTATION_PLAN_v2.md:**
- When adding new phases to roadmap
- When adjusting timeline estimates
- After major scope changes
- Monthly roadmap review

**FEATURES.md:**
- After shipping new user-facing features
- When UX/UI changes significantly
- After adding screenshots/examples
- Based on user feedback
