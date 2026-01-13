# Maxwell Development Guide

> **Quick Start:** This is the entry point for Maxwell development. Choose the guide you need below.

**Last Updated:** 2026-01-08
**Version:** 2.0

---

## 📚 Documentation Index

### For New Developers
1. **Start here:** [ARCHITECTURE.md](ARCHITECTURE.md) - System design, tech stack, and key decisions
2. **Then read:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands and file locations
3. **When coding:** [PATTERNS.md](PATTERNS.md) - Code examples and conventions
4. **Before committing:** [WORKFLOW.md](WORKFLOW.md) - Testing, migrations, and git standards

### Quick Links
- **Architecture & Design:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Code Patterns:** [PATTERNS.md](PATTERNS.md)
- **Development Workflow:** [WORKFLOW.md](WORKFLOW.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Progress Tracking:** [PROGRESS.md](PROGRESS.md)
- **Implementation Roadmap:** [IMPLEMENTATION_PLAN_v2.md](IMPLEMENTATION_PLAN_v2.md)
- **User Features Guide:** [FEATURES.md](FEATURES.md)

---

## 🚀 Getting Started (5 Minutes)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repo-url>
cd Maxwell

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend setup (in new terminal)
cd frontend
npm install
```

### 2. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Open:** http://localhost:5173

### 3. Verify Setup

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend should show welcome screen
# Backend should log incoming requests
```

---

## 📖 What to Read When

### "I need to understand the system architecture"
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)
- System design philosophy
- Tech stack overview
- Architecture layers (backend 3-tier, frontend component-store-API)
- Database schema
- Key architectural decisions (ADRs)

### "I'm adding a new feature"
→ Read [WORKFLOW.md](WORKFLOW.md) Section 3.5: Feature Development Process
- Step-by-step workflow (backend → frontend → testing → docs)
- When to create models, services, routes
- How to integrate with existing code

### "I need a code example"
→ Read [PATTERNS.md](PATTERNS.md)
- API route patterns
- Database model patterns
- Component patterns
- Store patterns
- Naming conventions

### "What's the command for X?"
→ Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Common commands (backend, frontend, testing)
- Directory structure
- API endpoints
- Environment variables
- Troubleshooting

### "How do I run tests / create migrations / commit code?"
→ Read [WORKFLOW.md](WORKFLOW.md)
- Testing standards and commands
- Database migration workflow
- Git commit standards (Conventional Commits)
- Documentation standards

### "What's been completed and what's next?"
→ Read [PROGRESS.md](PROGRESS.md) and [IMPLEMENTATION_PLAN_v2.md](IMPLEMENTATION_PLAN_v2.md)
- Current progress percentages
- Completed features
- Upcoming work
- 14-week roadmap

---

## 🎯 Core Concepts (Read This First!)

### Vision
Maxwell is a **local-first fiction writing IDE** with invisible engineering:
- Writers get powerful tools without complexity
- All core features work offline (SQLite, local Git)
- AI features require user-provided API keys (BYOK)
- Teaching-first design (tools educate writers about craft)

### Tech Stack
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, SQLite, spaCy
- **Frontend:** React 18, TypeScript, Vite, Lexical editor, Zustand
- **Storage:** SQLite database + Git repositories per manuscript

### Architecture Pattern
```
Frontend Components → Zustand Stores → API Client → Backend Routes → Services → Models → Database
```

### Design System
- **Vellum:** Warm cream background (feels like parchment)
- **Bronze:** Copper accents (vintage, literary)
- **Midnight:** Deep text color (readable, elegant)
- **Font:** Garamond for headings, sans-serif for UI

---

## 🛠 Common Tasks

### Add a new API endpoint
1. Create model in `backend/app/models/` (if needed)
2. Run `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Create service in `backend/app/services/` (if complex logic)
5. Create route in `backend/app/api/routes/`
6. Register router in `backend/app/main.py`
7. Add API types to `frontend/src/lib/api.ts`

**Example:** See [PATTERNS.md](PATTERNS.md#backend-patterns) for full code examples

### Add a new React component
1. Create types in `frontend/src/types/` (if needed)
2. Create component in `frontend/src/components/{Feature}/`
3. Export from `frontend/src/components/{Feature}/index.ts`
4. Update store in `frontend/src/stores/` (if stateful)
5. Integrate in parent component or `App.tsx`

**Example:** See [PATTERNS.md](PATTERNS.md#frontend-patterns) for full code examples

### Run tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### Create a database migration
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

### Make a commit
```bash
git add .
git commit -m "feat: Add new feature"  # Use conventional commit format
git push
```

See [WORKFLOW.md](WORKFLOW.md#git-commit-standards) for commit message standards

---

## 📂 Project Structure

```
Maxwell/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── database.py      # SQLAlchemy config
│   │   └── main.py          # FastAPI app
│   ├── migrations/          # Alembic migrations
│   ├── tests/               # Integration tests
│   └── data/                # SQLite DB + Git repos
├── frontend/
│   └── src/
│       ├── components/      # React components (feature-based)
│       ├── stores/          # Zustand state management
│       ├── types/           # TypeScript types
│       ├── lib/             # API client, utilities
│       └── App.tsx          # Root component
├── CLAUDE.md                # This file (quick start)
├── ARCHITECTURE.md          # System design & ADRs
├── PATTERNS.md              # Code examples & conventions
├── WORKFLOW.md              # Testing, migrations, git
├── QUICK_REFERENCE.md       # Commands & locations
├── PROGRESS.md              # Current progress
└── IMPLEMENTATION_PLAN_v2.md  # Roadmap
```

---

## 🔍 Finding Things

### "Where is the X model defined?"
- **Backend models:** `backend/app/models/`
- Look for: `manuscript.py`, `entity.py`, `timeline.py`, `outline.py`

### "Where is the X API endpoint?"
- **Backend routes:** `backend/app/api/routes/`
- Look for: `chapters.py`, `codex.py`, `timeline.py`, `outlines.py`

### "Where is the X component?"
- **Frontend components:** `frontend/src/components/{Feature}/`
- Features: `Codex/`, `Timeline/`, `Outline/`, `Editor/`

### "Where is the X store?"
- **Zustand stores:** `frontend/src/stores/`
- Look for: `codexStore.ts`, `timelineStore.ts`, `outlineStore.ts`

### "How do I call the X API?"
- **API client:** `frontend/src/lib/api.ts`
- Exports: `manuscriptApi`, `codexApi`, `timelineApi`, `outlineApi`

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for full directory structure

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version (needs 3.13+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Check database schema
alembic current
alembic upgrade head
```

### Frontend won't build
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npx tsc --noEmit
```

### Tests failing
```bash
# Backend: Check database schema
alembic upgrade head

# Frontend: Clear test cache
npm test -- --clearCache
```

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#troubleshooting) for more solutions

---

## 📝 Contributing

### Before you code
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Check [PROGRESS.md](PROGRESS.md) to see what's already done
3. Review [PATTERNS.md](PATTERNS.md) for code conventions

### While you code
1. Follow naming conventions in [PATTERNS.md](PATTERNS.md#naming-standards)
2. Write tests (see [WORKFLOW.md](WORKFLOW.md#testing-standards))
3. Add docstrings for public functions

### Before you commit
1. Run tests: `pytest` (backend) and `npm test` (frontend)
2. Check types: `npx tsc --noEmit` (frontend)
3. Use conventional commits: `feat:`, `fix:`, `refactor:`, etc.
4. **ALWAYS update PROGRESS.md when you complete a feature or fix a bug**
   - Add entry to "Recent Completions" with date and details
   - Update phase completion percentages
   - Mark completed items in "Active Work" sections
   - Remove fixed bugs from "Technical Debt & Known Issues"
   - Update component/feature counts if applicable

See [WORKFLOW.md](WORKFLOW.md) for full development workflow

---

## 🎓 Learning Resources

### Understanding the codebase
- **Backend architecture:** [ARCHITECTURE.md](ARCHITECTURE.md#backend-three-tier-pattern)
- **Frontend architecture:** [ARCHITECTURE.md](ARCHITECTURE.md#frontend-component-store-api-pattern)
- **Database schema:** [ARCHITECTURE.md](ARCHITECTURE.md#database-schema-overview)

### Code examples
- **API routes:** [PATTERNS.md](PATTERNS.md#creating-a-new-api-route)
- **Components:** [PATTERNS.md](PATTERNS.md#component-pattern)
- **Stores:** [PATTERNS.md](PATTERNS.md#zustand-store-pattern)
- **Models:** [PATTERNS.md](PATTERNS.md#database-model-pattern)

### Best practices
- **Testing:** [WORKFLOW.md](WORKFLOW.md#testing-standards)
- **Migrations:** [WORKFLOW.md](WORKFLOW.md#database-migrations)
- **Git commits:** [WORKFLOW.md](WORKFLOW.md#git-commit-standards)
- **Documentation:** [WORKFLOW.md](WORKFLOW.md#documentation-standards)

---

## 💬 Getting Help

### Documentation issues
- Found an error? Update the relevant .md file
- Something unclear? Ask the team or open an issue

### Feature questions
- Check [IMPLEMENTATION_PLAN_v2.md](IMPLEMENTATION_PLAN_v2.md) for planned features
- Check [PROGRESS.md](PROGRESS.md) for current status
- Check [FEATURES.md](FEATURES.md) for user-facing documentation

### Code questions
- Search for similar code in the codebase
- Check [PATTERNS.md](PATTERNS.md) for examples
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions

---

**Next Steps:**
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
3. Start coding! Refer to [PATTERNS.md](PATTERNS.md) for examples

**Happy coding! 🎉**
