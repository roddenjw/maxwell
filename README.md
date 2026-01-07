# Maxwell

> **A fiction writing IDE that thinks like a novelist**

Maxwell is a local-first writing environment designed specifically for fiction authors. It combines the focused writing experience of Scrivener with intelligent tools for story structure, character development, timeline management, and AI-powered assistance.

**Status:** Beta Development (65% complete) | **License:** Proprietary

---

## What is Maxwell?

Maxwell helps fiction writers:
- **Write** with a distraction-free editor (Lexical-based, Garamond typography)
- **Structure** their story with proven templates (Hero's Journey, Save the Cat, 3-Act, etc.)
- **Track** characters, locations, and relationships in a living Codex
- **Validate** timelines for chronological consistency and impossible events
- **Brainstorm** with AI-powered idea generation (characters, plots, conflicts)
- **Version** their work with Git-backed snapshots and time-travel diffs
- **Analyze** their writing with Fast Coach AI feedback

**Key Principle:** Teaching-first design. Maxwell doesn't just detect errors—it explains *why* they matter and *how* to fix them.

---

## Features

### ✅ Completed (Phases 1-3)

- **Rich Text Editor** - Lexical-based editor with Garamond font, auto-save, formatting
- **Hierarchical Chapters** - Scrivener-like folder/document structure
- **Version Control** - Git-backed snapshots with visual diff viewer ("Time Machine")
- **Entity Extraction** - Automatic NLP-powered detection of characters, locations, items
- **Relationship Graph** - Force-directed visualization of character connections
- **Timeline Management** - Chronological event tracking with emotional arcs
- **Story Structure Templates** - 9 built-in structures (Hero's Journey, Save the Cat, etc.)
- **AI Integration** - BYOK (Bring Your Own Key) with OpenRouter (20+ models)
- **Fast Coach** - Real-time AI writing feedback and style analysis
- **Export** - DOCX format with formatting preservation

### 🔄 In Progress (Phases 4-6)

- **Timeline Orchestrator** (85%) - Advanced validation, impossible travel detection, teaching moments
- **Outline Engine** (70%) - Plot beat tracking, progress visualization, checkpoint system
- **Brainstorming Tools** (40%) - AI character generation, idea management

### ⏳ Planned (Phases 7-8)

- **PLG Features** - Viral recap cards, real-time entity extraction, guided onboarding
- **Collaboration** - Multi-user comments, beta reader workflows, sharing
- **Mobile App** - iOS/Android React Native app
- **Advanced AI** - Plot arc analysis, foreshadowing tracker, theme analyzer

---

## Quick Start

### Prerequisites

- **Backend:** Python 3.13+, pip
- **Frontend:** Node.js 18+, npm
- **Database:** SQLite (included)
- **Git:** For version control features

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/maxwell.git
cd maxwell

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000

# In new terminal: Frontend setup
cd frontend
npm install
npm run dev

# Open browser to http://localhost:5173
```

### First Manuscript

1. Click "New Manuscript" on welcome screen
2. Choose a story structure (Hero's Journey recommended)
3. Start writing in the editor
4. Entities will be auto-detected as you write
5. Check the Timeline sidebar to track chronology
6. View the Codex to see your story world

---

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- SQLite (database)
- spaCy (NLP for entity extraction)
- OpenRouter (AI model aggregation)

**Frontend:**
- React 18 + TypeScript
- Lexical (rich text editor)
- Zustand (state management)
- Tailwind CSS (styling)
- Vite (build tool)

**Database:**
- 15 tables (manuscripts, chapters, entities, timeline, outlines, etc.)
- 8 Alembic migrations
- Local SQLite file storage

---

## Project Structure

```
maxwell/
├── backend/                # Python FastAPI backend
│   ├── app/
│   │   ├── api/routes/    # REST API endpoints (104 endpoints)
│   │   ├── models/        # SQLAlchemy ORM models (15 tables)
│   │   ├── services/      # Business logic layer
│   │   └── main.py        # FastAPI app initialization
│   ├── migrations/        # Alembic database migrations
│   ├── data/              # Local data storage
│   │   ├── codex.db       # SQLite database
│   │   └── manuscripts/   # Git repositories
│   └── requirements.txt   # Python dependencies
│
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components (50+ components)
│   │   ├── stores/        # Zustand state management
│   │   ├── types/         # TypeScript type definitions
│   │   ├── lib/           # API client and utilities
│   │   └── App.tsx        # Root component
│   └── package.json       # Node dependencies
│
├── docs/                  # Documentation
│   └── ARCHITECTURE_DECISIONS.md  # ADRs
│
├── CLAUDE.md              # Development guide (architecture, standards, workflow)
├── PROGRESS.md            # Project progress tracker
├── IMPLEMENTATION_PLAN_v2.md  # Implementation roadmap
├── FEATURES.md            # Feature documentation
└── README.md              # This file
```

---

## Documentation

### For Developers

Start here in order:

1. **[README.md](./README.md)** *(you are here)* - Project overview and quick start
2. **[CLAUDE.md](./CLAUDE.md)** - Architecture, coding standards, development workflow
3. **[PROGRESS.md](./PROGRESS.md)** - Current status, active work, milestones

### For Planning

- **[IMPLEMENTATION_PLAN_v2.md](./IMPLEMENTATION_PLAN_v2.md)** - Detailed roadmap for all phases
- **[PLG_STRATEGY.md](./PLG_STRATEGY.md)** - Product-led growth strategy

### For Features

- **[FEATURES.md](./FEATURES.md)** - User guides for major features
- **[docs/ARCHITECTURE_DECISIONS.md](./docs/ARCHITECTURE_DECISIONS.md)** - ADRs for key decisions

---

## Development

### Running Tests

**Backend:**
```bash
cd backend
source venv/bin/activate
pytest                      # All tests
pytest --cov                # With coverage
```

**Frontend:**
```bash
cd frontend
npm test                    # All tests
npm run coverage            # Coverage report
```

### Database Migrations

```bash
cd backend
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check current migration
alembic current
```

### Code Style

- **Backend:** PEP 8 (use `black` for formatting)
- **Frontend:** ESLint + Prettier
- **Commits:** Conventional Commits format (`feat:`, `fix:`, etc.)

See [CLAUDE.md](./CLAUDE.md) for detailed coding standards.

---

## Contributing

Maxwell is currently in private beta. Contributing guidelines will be published when we open source.

**For now:**
1. Read [CLAUDE.md](./CLAUDE.md) for architecture and standards
2. Follow the test colocation pattern (tests next to source files)
3. Update [PROGRESS.md](./PROGRESS.md) when completing features
4. Use conventional commit messages

---

## Roadmap

| Quarter | Focus | Key Deliverables |
|---------|-------|------------------|
| **Q1 2026** | Phases 4-6 completion | Beta launch, 100 users |
| **Q2 2026** | PLG features, Collaboration | 1,000 users, first revenue |
| **Q3 2026** | Mobile app, Advanced AI | Public v1.0, 10k users |
| **Q4 2026** | Enterprise, Marketplace | $10k MRR, teams feature |

See [PROGRESS.md](./PROGRESS.md) for detailed milestones and [IMPLEMENTATION_PLAN_v2.md](./IMPLEMENTATION_PLAN_v2.md) for full roadmap.

---

## License

Copyright © 2026 Maxwell. All rights reserved.

This is proprietary software. Unauthorized copying, modification, or distribution is prohibited.

---

## Contact

- **Issues:** Report bugs via GitHub Issues (when public)
- **Email:** support@maxwell.app (not yet active)
- **Website:** maxwell.app (coming soon)

---

## Acknowledgments

**Built with:**
- [Lexical](https://lexical.dev/) - Meta's extensible text editor framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [spaCy](https://spacy.io/) - Industrial-strength NLP
- [OpenRouter](https://openrouter.ai/) - Unified AI API
- [Zustand](https://github.com/pmndrs/zustand) - Minimalist state management

**Inspired by:**
- Scrivener's hierarchical document structure
- Notion's database and relationship system
- Brandon Sanderson's teaching on story structure
- K.M. Weiland's character arc methodology

---

**Maxwell** - Write smarter, not harder.
