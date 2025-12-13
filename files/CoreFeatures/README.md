# Codex IDE

An AI-powered IDE for fiction authors that unifies the flexibility of a word processor, the rigor of a knowledge graph, and the creativity of generative AI.

## 🎯 Project Status

**Version**: 0.1.0-alpha
**Phase**: Phase 1 - Core Experience
**Status**: 🟡 In Development

## 📚 Documentation

- [SPECIFICATION.md](./SPECIFICATION.md) - Product requirements and design philosophy
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and technical design
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Detailed task breakdown
- [DEVELOPMENT_PHASES.md](./DEVELOPMENT_PHASES.md) - 14-week development roadmap
- [PROGRESS.md](./PROGRESS.md) - Current development progress

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **Git** (for version control)
- **16GB RAM** recommended
- **GPU** optional (for local LLM inference)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Maxwell
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_lg
   ```

### Development

Run both frontend and backend simultaneously:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit http://localhost:5173 to see the application.

## 🏗️ Project Structure

```
Maxwell/
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── stores/       # Zustand state management
│   │   ├── types/        # TypeScript type definitions
│   │   └── styles/       # CSS and Tailwind
│   └── package.json
│
├── backend/              # Python + FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── models/      # Data models
│   │   └── repositories/# Data access layer
│   ├── tests/           # Backend tests
│   └── requirements.txt
│
├── data/                # Local data storage
│   ├── manuscripts/     # Git repositories for manuscripts
│   ├── chroma/         # ChromaDB vector store
│   └── graph/          # KuzuDB graph database
│
├── docs/               # Additional documentation
└── scripts/            # Build and deployment scripts
```

## 🎨 Features

### Phase 1: Living Manuscript (Current)
- ✅ Rich text editor with Lexical
- 🟡 Git-based versioning ("Time Machine")
- ⏳ Auto-save with 5-second debounce
- ⏳ Variant/branch system ("Multiverse")

### Phase 2: The Codex (Upcoming)
- ⏳ Automatic entity extraction (characters, locations)
- ⏳ Knowledge graph visualization
- ⏳ Relationship tracking

### Phase 3: The Muse (Planned)
- ⏳ Hybrid local/cloud LLM routing
- ⏳ GraphRAG for context-aware generation
- ⏳ Beat expansion engine
- ⏳ Sensory paint tools

### Phase 4: The Coach (Planned)
- ⏳ Pacing analysis (Vonnegut curve)
- ⏳ Consistency linter
- ⏳ Structural analysis

## 🧪 Testing

**Frontend:**
```bash
cd frontend
npm run test:unit      # Unit tests with Vitest
npm run test:e2e       # E2E tests with Playwright
```

**Backend:**
```bash
cd backend
pytest                 # Run all tests
pytest --cov=app      # With coverage
```

## 🛠️ Development Tools

**Code Quality:**
```bash
# Frontend
npm run lint          # ESLint
npm run format        # Prettier

# Backend
black app/            # Code formatting
ruff app/             # Linting
mypy app/             # Type checking
```

## 📦 Building for Production

```bash
# Frontend build
cd frontend
npm run build

# Backend build (PyInstaller)
cd backend
pyinstaller --onefile app/main.py -n codex-backend
```

## 🤝 Contributing

This is currently an internal development project. See [DEVELOPMENT_PHASES.md](./DEVELOPMENT_PHASES.md) for the roadmap.

## 📝 License

TBD - To be determined

## 🔗 Useful Links

- [Lexical Documentation](https://lexical.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [spaCy Documentation](https://spacy.io/)

## 💡 Design Philosophy

**"Invisible Engineering"**

Complex Backend → Git versioning, GraphRAG, NLP pipelines
Simple Frontend → "Time Machine", "Story Bible", "Magic Assist"

The user should never see a commit hash, a node edge, or a JSON object.

## 📊 Current Sprint

See [PROGRESS.md](./PROGRESS.md) for detailed task tracking.

**Week 1 Goals:**
- ✅ Project setup and structure
- 🟡 Basic editor implementation
- ⏳ Database configuration
- ⏳ Version control integration

---

**Last Updated**: 2025-11-23
**Status**: Active Development
