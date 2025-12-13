# Codex IDE: System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Architectural Principles](#architectural-principles)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Component Architecture](#component-architecture)
6. [Data Architecture](#data-architecture)
7. [API Design](#api-design)
8. [Scalability & Performance](#scalability--performance)
9. [Security Architecture](#security-architecture)
10. [Testing Strategy](#testing-strategy)

---

## System Overview

Codex IDE is a desktop-first, locally-running IDE for fiction authors that combines:
- **Rich text editing** with semantic understanding
- **Version control** (Git-based, abstracted from users)
- **Knowledge graph** for story consistency
- **AI-powered writing assistance** with hybrid local/cloud LLM routing

### Core Design Philosophy: "Invisible Engineering"
- **Complex Backend**: Git versioning, GraphRAG, NLP pipelines
- **Simple Frontend**: Metaphorical UIs ("Time Machine," "Story Bible," "Magic Assist")
- **Never expose**: commit hashes, graph nodes, raw JSON to end users

---

## Architectural Principles

### 1. Separation of Concerns
- **Presentation Layer** (React): UI components, user interactions
- **Business Logic Layer** (Python FastAPI): NLP, AI routing, graph operations
- **Data Layer**: SQLite (structured data), ChromaDB (vectors), KuzuDB (graphs)

### 2. Offline-First Architecture
- All core features work without internet
- Cloud LLMs optional for advanced features
- Local data storage with optional sync capabilities

### 3. Event-Driven Design
- Asynchronous NLP processing triggered by user actions
- Debounced auto-save (5 seconds after typing stops)
- Streaming responses for AI generation

### 4. Progressive Enhancement
- Core editor works immediately
- Advanced features (AI, graph) load progressively
- Graceful degradation when services unavailable

### 5. Data Consistency
- Single source of truth: SQLite for application state
- Derived data: ChromaDB vectors, KuzuDB relationships
- Git as immutable history layer

---

## Technology Stack

### Frontend Stack
| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **React** | 18.x | UI Framework | Component reusability, mature ecosystem |
| **TypeScript** | 5.x | Type Safety | Catch errors at compile-time, better DX |
| **Vite** | 5.x | Build Tool | Fast HMR, optimized production builds |
| **Tailwind CSS** | 3.x | Styling | Utility-first, consistent design system |
| **Shadcn/UI** | Latest | Component Library | Accessible, customizable, headless |
| **Lexical** | Latest | Rich Text Editor | Headless, extensible, structured nodes |
| **TanStack Query** | 5.x | Server State | Caching, synchronization, optimistic updates |
| **Zustand** | 4.x | Client State | Lightweight, simple API, TypeScript support |
| **react-force-graph** | Latest | Graph Visualization | Interactive 3D/2D force-directed graphs |

### Backend Stack
| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Python** | 3.11+ | Runtime | Required for NLP libraries |
| **FastAPI** | 0.104+ | API Framework | Async support, auto-docs, type validation |
| **spaCy** | 3.7+ | NLP Pipeline | NER, POS tagging, dependency parsing |
| **neuralcoref** | 4.0+ | Coreference Resolution | Pronoun resolution for entity tracking |
| **Pydantic** | 2.x | Data Validation | Runtime type checking, JSON schema |
| **SQLAlchemy** | 2.x | ORM | Database abstraction, migrations |

### Data Stack
| Technology | Purpose | Justification |
|------------|---------|---------------|
| **SQLite** | Primary Database | Zero-config, file-based, ACID compliant |
| **ChromaDB** | Vector Store | Embedding storage for RAG, lightweight |
| **KuzuDB/NetworkX** | Knowledge Graph | Relationship tracking, graph queries |
| **Git (libgit2)** | Version Control | Industry-standard versioning |

### AI/LLM Stack
| Technology | Purpose | Use Case |
|------------|---------|----------|
| **Llama 3 (8B)** | Local LLM | Simple tasks (paraphrasing, grammar) |
| **Mistral 7B** | Local LLM | Alternative local model |
| **Claude 3.5 Sonnet** | Cloud LLM | Complex prose generation, plotting |
| **GPT-4o** | Cloud LLM | Alternative cloud option |
| **OpenRouter** | API Gateway | Access to uncensored models if needed |

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Electron/Tauri)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Lexical    │  │  React UI    │  │  Zustand     │     │
│  │   Editor     │  │  Components  │  │  State       │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                           │                                │
│                    TanStack Query                          │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────┼────────────────────────────────┐
│                    BACKEND (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   API        │  │   NLP        │  │   AI         │     │
│  │   Routes     │  │   Pipeline   │  │   Router     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                           │                                │
│                    Service Layer                           │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────┐
│                    DATA LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   SQLite     │  │   ChromaDB   │  │   KuzuDB     │     │
│  │  (App Data)  │  │  (Vectors)   │  │  (Graph)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Git Repository (.codex/)                │ │
│  │                 (Version History)                    │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Patterns

#### 1. Hexagonal Architecture (Ports & Adapters)
- **Core Domain**: Manuscript, Entity, Codex models
- **Ports**: Interfaces for storage, NLP, AI
- **Adapters**: SQLite adapter, spaCy adapter, OpenAI adapter
- **Benefits**: Testability, flexibility, independence

#### 2. CQRS-Lite Pattern
- **Commands**: Write operations (save manuscript, create entity)
- **Queries**: Read operations (fetch history, search codex)
- **Benefits**: Optimized reads, clear intent, audit trail

#### 3. Repository Pattern
- Abstraction over data access
- `ManuscriptRepository`, `CodexRepository`, `VersionRepository`
- Benefits: Swappable storage, testable business logic

#### 4. Strategy Pattern (AI Router)
- Different LLM selection strategies based on:
  - Task complexity
  - Privacy requirements
  - Cost constraints
  - Network availability

---

## Component Architecture

### Frontend Components

#### 1. Editor Module
```typescript
components/
├── Editor/
│   ├── ManuscriptEditor.tsx        // Main editor component
│   ├── plugins/
│   │   ├── AutoSavePlugin.tsx      // Debounced auto-save
│   │   ├── EntityMentionPlugin.tsx // Clickable entity references
│   │   ├── SceneBreakPlugin.tsx    // Custom scene separators
│   │   └── FocusModePlugin.tsx     // Distraction-free mode
│   ├── nodes/
│   │   ├── EntityMentionNode.tsx   // Custom Lexical node
│   │   ├── SceneBreakNode.tsx      // Scene separator node
│   │   └── DialogueNode.tsx        // Dialogue-specific styling
│   └── toolbar/
│       ├── FloatingToolbar.tsx     // Context menu for selection
│       └── AIAssistToolbar.tsx     // AI action buttons
```

#### 2. Versioning Module
```typescript
components/
├── TimeMachine/
│   ├── HistorySlider.tsx          // Visual timeline
│   ├── SnapshotCard.tsx           // Individual snapshot UI
│   ├── DiffViewer.tsx             // Side-by-side comparison
│   └── MultiverseTab.tsx          // Branch/variant switcher
```

#### 3. Codex Module
```typescript
components/
├── Codex/
│   ├── CodexSidebar.tsx           // Main sidebar container
│   ├── EntityCard.tsx             // Character/location display
│   ├── EntityForm.tsx             // Create/edit entities
│   ├── RelationshipGraph.tsx      // Force-directed graph
│   ├── SuggestionQueue.tsx        // Pending entity approvals
│   └── ContextualPanel.tsx        // Shows relevant entities
```

#### 4. AI Module
```typescript
components/
├── Muse/
│   ├── BeatExpander.tsx           // Beat-to-prose conversion
│   ├── RewritePanel.tsx           // Style transformation
│   ├── SensoryPaint.tsx           // Sensory description tools
│   ├── StreamingResponse.tsx      // Typing effect UI
│   └── ModelSelector.tsx          // LLM choice (if exposed)
```

#### 5. Analysis Module
```typescript
components/
├── Coach/
│   ├── PacingGraph.tsx            // Sentiment/tension visualization
│   ├── ConsistencyLinter.tsx      // Inline contradiction warnings
│   └── StructureWizard.tsx        // Save the Cat templates
```

### Backend Services

#### 1. API Layer (`/app/api/`)
```python
api/
├── routes/
│   ├── manuscript.py      // CRUD for manuscript content
│   ├── versioning.py      // History, snapshots, branches
│   ├── codex.py           // Entity management, search
│   ├── generation.py      // AI text generation
│   └── analysis.py        // NLP analysis, linting
├── dependencies.py        // Shared dependencies (DB sessions)
└── middleware.py          // CORS, error handling, logging
```

#### 2. Service Layer (`/app/services/`)
```python
services/
├── manuscript_service.py  // Business logic for manuscripts
├── version_service.py     // Git operations wrapper
├── nlp_service.py         // spaCy pipeline, NER
├── codex_service.py       // Graph operations, entity extraction
├── embedding_service.py   // Vector generation for RAG
├── llm_service.py         // LLM routing, prompt engineering
└── consistency_service.py // Fact-checking against codex
```

#### 3. Domain Models (`/app/models/`)
```python
models/
├── manuscript.py          // Manuscript, Scene, Chapter
├── entity.py              // Character, Location, Item, Lore
├── relationship.py        // Entity relationships
├── version.py             // Snapshot metadata
└── user_preferences.py    // Settings, model choices
```

#### 4. Repositories (`/app/repositories/`)
```python
repositories/
├── base.py                // Generic repository interface
├── manuscript_repo.py     // SQLite operations for manuscripts
├── codex_repo.py          // SQLite operations for entities
├── vector_repo.py         // ChromaDB operations
└── graph_repo.py          // KuzuDB operations
```

---

## Data Architecture

### Database Schema (SQLite)

#### Manuscripts Table
```sql
CREATE TABLE manuscripts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count INTEGER DEFAULT 0,
    active_variant_id TEXT,
    lexical_state TEXT -- Serialized Lexical editor state
);
```

#### Scenes Table
```sql
CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    manuscript_id TEXT REFERENCES manuscripts(id),
    position INTEGER NOT NULL,
    pov_character_id TEXT REFERENCES entities(id),
    setting_id TEXT REFERENCES entities(id),
    time_of_day TEXT,
    beat_type TEXT,
    word_count INTEGER,
    completion_status TEXT,
    content TEXT, -- Lexical serialized state
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Entities Table
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL, -- CHARACTER, LOCATION, ITEM, LORE
    name TEXT NOT NULL,
    aliases TEXT, -- JSON array
    attributes TEXT, -- JSON object
    appearance_history TEXT, -- JSON array of {scene_id, description}
    image_seed INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Relationships Table
```sql
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT REFERENCES entities(id),
    target_entity_id TEXT REFERENCES entities(id),
    relationship_type TEXT,
    strength INTEGER DEFAULT 1, -- Interaction count
    context TEXT, -- JSON array of scenes where they interact
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Snapshots Table (Version Metadata)
```sql
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    manuscript_id TEXT REFERENCES manuscripts(id),
    git_commit_hash TEXT NOT NULL,
    label TEXT, -- User-friendly description
    trigger_type TEXT, -- AUTO_SAVE, MANUAL, PRE_GENERATION
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Variants Table (Multiverse)
```sql
CREATE TABLE variants (
    id TEXT PRIMARY KEY,
    scene_id TEXT REFERENCES scenes(id),
    label TEXT NOT NULL,
    content TEXT,
    is_main BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Store (ChromaDB)

#### Collections
```python
# Scene embeddings for semantic search
scenes_collection = {
    "name": "scene_embeddings",
    "metadata": {
        "scene_id": "sc-001",
        "manuscript_id": "ms-001",
        "chapter": 3
    },
    "embedding": [0.123, 0.456, ...],  # 1536-dim for OpenAI, 768 for local
    "document": "The scene text content..."
}

# Entity embeddings for context retrieval
entities_collection = {
    "name": "entity_embeddings",
    "metadata": {
        "entity_id": "uuid-1234",
        "entity_type": "CHARACTER",
        "name": "Elara Vance"
    },
    "embedding": [...],
    "document": "Comprehensive entity description with attributes..."
}
```

### Knowledge Graph (KuzuDB)

#### Node Types
```cypher
// Character nodes
CREATE NODE TABLE Character(
    id STRING,
    name STRING,
    attributes STRING,
    PRIMARY KEY(id)
);

// Location nodes
CREATE NODE TABLE Location(
    id STRING,
    name STRING,
    attributes STRING,
    PRIMARY KEY(id)
);

// Relationship edges
CREATE REL TABLE KNOWS(
    FROM Character TO Character,
    context STRING,
    strength INT
);

CREATE REL TABLE LOCATED_IN(
    FROM Character TO Location,
    scene_id STRING
);
```

### Git Repository Structure

```
.codex/
├── manuscripts/
│   └── main-manuscript.json      // Current state
├── entities/
│   └── characters/
│       └── elara-vance.json
├── .git/                         // Hidden Git internals
└── snapshots.db                  // SQLite metadata
```

---

## API Design

### RESTful Endpoints

#### Manuscript Operations
```
GET    /api/manuscripts                    // List all manuscripts
POST   /api/manuscripts                    // Create new manuscript
GET    /api/manuscripts/{id}               // Get manuscript details
PUT    /api/manuscripts/{id}               // Update manuscript
DELETE /api/manuscripts/{id}               // Delete manuscript
GET    /api/manuscripts/{id}/scenes        // Get all scenes
POST   /api/manuscripts/{id}/scenes        // Create scene
```

#### Versioning Operations
```
GET    /api/manuscripts/{id}/history       // Get snapshot timeline
POST   /api/manuscripts/{id}/snapshots     // Create snapshot
GET    /api/snapshots/{id}                 // Get snapshot details
POST   /api/snapshots/{id}/restore         // Restore to snapshot
GET    /api/scenes/{id}/variants           // Get scene variants
POST   /api/scenes/{id}/variants           // Create variant
PUT    /api/variants/{id}/merge            // Merge variant to main
```

#### Codex Operations
```
GET    /api/codex/entities                 // List all entities
POST   /api/codex/entities                 // Create entity
GET    /api/codex/entities/{id}            // Get entity
PUT    /api/codex/entities/{id}            // Update entity
DELETE /api/codex/entities/{id}            // Delete entity
GET    /api/codex/entities/{id}/relationships  // Get relationships
GET    /api/codex/graph                    // Get full graph data
GET    /api/codex/suggestions              // Get pending suggestions
POST   /api/codex/suggestions/{id}/approve // Approve suggestion
```

#### AI Generation
```
POST   /api/generate/beat-expansion        // Expand outline to prose
POST   /api/generate/rewrite               // Rewrite with style
POST   /api/generate/sensory               // Add sensory details
POST   /api/generate/continue              // Continue from cursor
```

#### Analysis
```
POST   /api/analyze/extract-entities       // Run NLP extraction
GET    /api/analyze/pacing/{manuscript_id} // Get pacing data
GET    /api/analyze/consistency            // Run consistency check
```

### WebSocket Endpoints

```
WS     /ws/generate                        // Streaming AI generation
WS     /ws/analysis                        // Real-time NLP updates
```

### API Response Standards

#### Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
  "meta": {
    "timestamp": "2025-11-23T10:30:00Z",
    "version": "1.0.0"
  }
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Character with ID uuid-1234 not found",
    "details": {}
  },
  "meta": {
    "timestamp": "2025-11-23T10:30:00Z"
  }
}
```

---

## Scalability & Performance

### Performance Targets
| Metric | Target | Measurement |
|--------|--------|-------------|
| Editor Input Latency | <50ms | Time to render keystroke |
| Auto-Save Trigger | 5s debounce | After typing stops |
| NLP Processing | <10s | For 5,000-word chapter |
| AI Generation Start | <2s | Time to first token |
| Graph Query | <100ms | Relationship lookup |
| Snapshot Creation | <1s | For 100,000-word manuscript |

### Optimization Strategies

#### 1. Frontend Optimizations
- **Code Splitting**: Lazy load AI, Codex, Analysis modules
- **Virtual Scrolling**: For long manuscripts (react-window)
- **Memoization**: React.memo for entity cards, graph nodes
- **Web Workers**: Offload diff calculations, syntax highlighting
- **IndexedDB Cache**: Store recent snapshots locally

#### 2. Backend Optimizations
- **Async Processing**: FastAPI async routes for I/O operations
- **Background Tasks**: Celery for long-running NLP jobs
- **Connection Pooling**: SQLite WAL mode for concurrent reads
- **Vector Index**: HNSW index in ChromaDB for fast similarity search
- **LRU Cache**: In-memory cache for frequent entity lookups

#### 3. Database Optimizations
```sql
-- Indexes for common queries
CREATE INDEX idx_scenes_manuscript ON scenes(manuscript_id);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_snapshots_manuscript ON snapshots(manuscript_id, created_at DESC);
```

#### 4. AI Optimization
- **Prompt Caching**: Cache system prompts for consistent contexts
- **Streaming**: Server-Sent Events (SSE) for progressive rendering
- **Local Model Quantization**: 4-bit quantized Llama for lower memory
- **Request Batching**: Combine multiple small requests when possible

### Scalability Considerations

#### Vertical Scaling (Single User, Large Projects)
- **Large Manuscripts**: Pagination at scene level, not full load
- **Graph Size**: Use graph sampling for visualization (top N relationships)
- **Vector Store**: Partition by manuscript for faster queries
- **Git Repository**: Git LFS for binary assets (character portraits)

#### Horizontal Scaling (Future: Multi-User)
- **Database**: Migrate to PostgreSQL with read replicas
- **File Storage**: S3-compatible object storage for manuscripts
- **AI Layer**: Load balancer for multiple LLM inference servers
- **Session Management**: Redis for distributed sessions

---

## Security Architecture

### Threat Model

#### Assets to Protect
1. **User Manuscripts**: Intellectual property, unpublished work
2. **API Keys**: OpenAI, Anthropic credentials
3. **Personal Data**: User preferences, writing patterns

#### Threats
1. **Data Loss**: Accidental deletion, corruption
2. **Unauthorized Access**: Malware reading manuscripts
3. **API Key Exposure**: Hardcoded credentials
4. **Prompt Injection**: Malicious input to LLMs

### Security Measures

#### 1. Data Protection
```python
# Encryption at rest (SQLite)
from sqlcipher3 import dbapi2 as sqlite

conn = sqlite.connect('codex.db')
conn.execute("PRAGMA key = 'user_password'")
```

#### 2. API Key Management
```python
# Environment variables only, never hardcode
import os
from cryptography.fernet import Fernet

# Encrypt stored API keys
def encrypt_api_key(key: str) -> str:
    cipher = Fernet(os.getenv("MASTER_KEY"))
    return cipher.encrypt(key.encode()).decode()
```

#### 3. Input Sanitization
```python
# Prevent prompt injection
def sanitize_user_input(text: str) -> str:
    # Remove system prompt markers
    text = text.replace("</s>", "").replace("<|im_end|>", "")
    # Limit length to prevent DoS
    return text[:10000]
```

#### 4. Secure File Permissions
```python
# Restrict database file access (Unix)
import os
os.chmod('codex.db', 0o600)  # Owner read/write only
```

#### 5. No Telemetry by Default
- All usage data stays local
- Optional anonymous crash reports (user opt-in)
- No manuscript content ever sent without explicit AI action

### Compliance Considerations
- **GDPR**: User data stays on device, right to deletion
- **COPPA**: No user accounts needed, no data collection
- **Accessibility**: WCAG 2.1 AA compliance for UI

---

## Testing Strategy

### Test Pyramid

```
       /\
      /  \      E2E Tests (10%)
     /    \     - Full user workflows
    /──────\    - Critical paths only
   /        \
  /  Inte-  \  Integration Tests (30%)
 /   gration \  - API endpoints
/─────────────\ - Service layer
\             / - Database operations
 \   Unit    /  Unit Tests (60%)
  \  Tests  /   - Pure functions
   \       /    - Component logic
    \     /     - Domain models
     \   /
      \ /
```

### Testing Layers

#### 1. Unit Tests (60% Coverage Target)
```python
# Backend: pytest
def test_entity_extraction():
    text = "John walked into the castle."
    entities = extract_entities(text)
    assert "John" in [e.name for e in entities]
    assert entities[0].type == EntityType.CHARACTER

# Frontend: Vitest + Testing Library
test('EntityCard displays character name', () => {
  render(<EntityCard entity={mockCharacter} />);
  expect(screen.getByText('Elara Vance')).toBeInTheDocument();
});
```

#### 2. Integration Tests (30% Coverage Target)
```python
# API integration tests
@pytest.mark.asyncio
async def test_create_and_retrieve_manuscript(client):
    response = await client.post("/api/manuscripts", json={
        "title": "Test Novel"
    })
    assert response.status_code == 201
    manuscript_id = response.json()["data"]["id"]

    response = await client.get(f"/api/manuscripts/{manuscript_id}")
    assert response.json()["data"]["title"] == "Test Novel"
```

#### 3. E2E Tests (10% Coverage Target)
```typescript
// Playwright
test('user can write and version manuscript', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="new-manuscript"]');
  await page.fill('[data-testid="manuscript-title"]', 'My Novel');

  const editor = page.locator('[data-lexical-editor]');
  await editor.type('Once upon a time...');

  await page.click('[data-testid="create-snapshot"]');
  await expect(page.locator('[data-testid="snapshot-list"]')).toContainText('Once upon a time');
});
```

### Continuous Integration

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=app tests/

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v4
      - run: npm install
      - run: npm run test:unit
      - run: npm run test:e2e
```

### Performance Testing
```python
# Load testing with locust
from locust import HttpUser, task

class CodexUser(HttpUser):
    @task
    def analyze_manuscript(self):
        self.client.post("/api/analyze/extract-entities", json={
            "text": "A 5000-word chapter..."
        })
```

---

## Development Workflow

### Project Structure
```
codex-ide/
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── stores/           # Zustand stores
│   │   ├── lib/              # Utilities
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/                   # Python FastAPI
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── docs/                      # Documentation
├── scripts/                   # Build, deployment scripts
└── docker-compose.yml         # Local development environment
```

### Environment Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Frontend
cd frontend
npm install

# Run development servers
# Terminal 1: Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
npm run dev
```

### Code Quality Tools
- **Python**: Black (formatting), Ruff (linting), mypy (type checking)
- **TypeScript**: Prettier, ESLint, tsc --noEmit
- **Git Hooks**: Pre-commit hooks for formatting, linting

---

## Deployment Architecture

### Desktop Application Packaging

#### Option 1: Electron (Recommended for MVP)
```
electron-app/
├── main.js              // Electron main process
├── preload.js           // Context bridge
├── backend-server.py    // Bundled Python server
└── frontend/            // Built React app
```

**Benefits**: Cross-platform, mature ecosystem, auto-updates
**Tradeoffs**: Larger bundle size (~200MB)

#### Option 2: Tauri (Future Consideration)
```
tauri-app/
├── src-tauri/           // Rust backend
├── frontend/            // React app
└── python-service/      // Sidecar Python process
```

**Benefits**: Smaller bundle (~40MB), better performance
**Tradeoffs**: Less mature, harder to debug

### Distribution
- **Windows**: NSIS installer (.exe)
- **macOS**: DMG with code signing
- **Linux**: AppImage + .deb package

### Update Mechanism
- Electron auto-updater with GitHub releases
- Semantic versioning (1.0.0 → 1.1.0)
- Delta updates to minimize download size

---

## Monitoring & Observability

### Logging Strategy
```python
import structlog

logger = structlog.get_logger()

# Structured logging
logger.info("entity_extracted",
    entity_id="uuid-1234",
    entity_type="CHARACTER",
    manuscript_id="ms-001",
    confidence=0.92
)
```

### Error Tracking (Optional)
- Sentry integration (opt-in)
- Local error logs at `~/.codex/logs/`
- Crash reports: minidumps for debugging

### Analytics (Local Only)
- Usage metrics stored in SQLite
- No external transmission
- User dashboard: "You've written 50,000 words this month!"

---

## Future Architecture Considerations

### Potential Enhancements
1. **Cloud Sync**: Optional Dropbox/Google Drive backup
2. **Collaboration**: Real-time co-editing with CRDTs
3. **Mobile Companion**: Read-only iOS/Android app
4. **Plugin System**: Custom AI models, exporters, themes
5. **Multi-language Support**: i18n with react-i18next

### Migration Paths
- **Database**: SQLite → PostgreSQL for multi-user
- **Graph**: KuzuDB → Neo4j for advanced queries
- **Vector Store**: ChromaDB → Pinecone for cloud features
- **AI**: Self-hosted LLMs → Kubernetes cluster

---

## Appendix

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Desktop-first vs Web | Offline-first, data privacy, better editor performance |
| Python backend | Required for spaCy/NLP, fast prototyping |
| Lexical over ProseMirror | More modern, better React integration |
| Git for versioning | Industry-standard, mature, efficient |
| Local LLM support | Privacy, cost control, offline capability |

### Reference Architecture Patterns
- **Clean Architecture** (Robert C. Martin)
- **Domain-Driven Design** (Eric Evans)
- **Event Sourcing** for version history
- **CQRS** for read/write separation

### Technology Decision Records (TDRs)
Future decisions should be documented in `/docs/decisions/` following the ADR format.

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-23 | Initial architecture document | System |

---

**Document Status**: Living Document
**Review Cycle**: Quarterly or on major architectural changes
**Owner**: Technical Lead
