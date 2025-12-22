# Maxwell/Codex IDE: Architectural Decision Records (ADRs)

**Purpose**: Document significant architectural and design decisions made during the development of Maxwell.

**Format**: Each decision includes context, decision, rationale, consequences, and alternatives considered.

---

## Table of Contents

1. [ADR-001: Desktop-First Architecture](#adr-001-desktop-first-architecture)
2. [ADR-002: Lexical for Rich Text Editing](#adr-002-lexical-for-rich-text-editing)
3. [ADR-003: Git for Version Control](#adr-003-git-for-version-control)
4. [ADR-004: Python Backend with FastAPI](#adr-004-python-backend-with-fastapi)
5. [ADR-005: SQLite for Development Database](#adr-005-sqlite-for-development-database)
6. [ADR-006: Timeline Orchestrator as Separate Phase](#adr-006-timeline-orchestrator-as-separate-phase)
7. [ADR-007: Teaching-First Design Philosophy](#adr-007-teaching-first-design-philosophy)
8. [ADR-008: Hybrid Local/Cloud LLM Strategy](#adr-008-hybrid-localcloud-llm-strategy)
9. [ADR-009: Maxwell Design System](#adr-009-maxwell-design-system)
10. [ADR-010: JSON for Entity Attributes](#adr-010-json-for-entity-attributes)

---

## ADR-001: Desktop-First Architecture

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Architecture Team

### Context

We need to decide whether to build Maxwell as:
1. Web application (browser-based)
2. Desktop application (Electron/Tauri)
3. Hybrid (web + desktop apps)

**Key Requirements**:
- Writers need offline access (writing anywhere)
- Privacy is critical (manuscripts are intellectual property)
- Performance matters (rich text editor latency <50ms)
- Data ownership (writers control their files)

### Decision

**Build a desktop-first application using Electron (MVP) with Tauri as future option.**

### Rationale

**Offline-First**:
- Writers need to work without internet (planes, cafes, remote locations)
- Desktop apps naturally support offline-first architecture
- Web apps require complex offline strategies (Service Workers, IndexedDB)

**Data Privacy**:
- All data stays on user's machine
- No cloud storage required (optional sync later)
- Writers control their manuscripts completely
- Meets GDPR requirements by default

**Performance**:
- Native OS integration for better editor performance
- Direct file system access (faster than browser APIs)
- No network latency for core features
- Can use full system resources

**User Experience**:
- Feels like a "real" application (like Scrivener, Word)
- Can integrate with OS (menubar, file associations)
- Better for long writing sessions
- No browser chrome/distractions

### Consequences

**Positive**:
- ✅ Better offline support
- ✅ Superior performance
- ✅ Native OS integration
- ✅ Data privacy by design
- ✅ No server infrastructure costs (initially)

**Negative**:
- ❌ Need separate builds for Windows/Mac/Linux
- ❌ Larger download size (~200MB vs <5MB for web)
- ❌ Update distribution more complex
- ❌ Cannot access from phone/tablet easily
- ❌ Requires desktop installation

**Migration Path**:
- If we need web access later: Build read-only web viewer
- If we need collaboration: Add optional cloud sync
- If we need mobile: Build companion mobile app

### Alternatives Considered

**1. Web Application**
- **Pros**: Cross-platform, easy deployment, no installation
- **Cons**: Offline support hard, privacy concerns, performance limitations
- **Why rejected**: Doesn't meet offline and privacy requirements

**2. Progressive Web App (PWA)**
- **Pros**: Installable, some offline support, web-based
- **Cons**: Limited OS integration, browser-dependent features, storage limits
- **Why rejected**: Not "native" enough for serious writing tool

**3. Tauri (instead of Electron)**
- **Pros**: Smaller bundle (~40MB), better performance, Rust-based
- **Cons**: Less mature ecosystem, harder debugging, fewer examples
- **Why deferred**: Will consider for v2.0 after MVP validation

---

## ADR-002: Lexical for Rich Text Editing

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Frontend Team

### Context

We need a rich text editor that supports:
- Custom nodes (scene breaks, entity mentions)
- Structured content (not just HTML)
- Real-time collaboration (future)
- Excellent performance
- Extensibility

**Options**:
1. Lexical (Meta/Facebook)
2. ProseMirror
3. Slate
4. Draft.js
5. Build custom editor

### Decision

**Use Lexical as the rich text editing framework.**

### Rationale

**Structured Content Model**:
- Lexical uses nodes (like AST), not HTML
- Each node is a typed object (SceneBreakNode, EntityMentionNode)
- Easy to serialize/deserialize
- Perfect for our needs (scene structure, entity tracking)

**Performance**:
- Built for speed (used in Facebook)
- Optimized React integration
- No contentEditable surprises
- <50ms keystroke latency

**Extensibility**:
- Plugin architecture
- Custom nodes straightforward
- Custom commands easy
- Headless core (we control UI)

**Modern & Maintained**:
- Actively developed by Meta
- Growing ecosystem
- Good TypeScript support
- React-first design

**Future-Proof**:
- Built for collaboration (CRDTs planned)
- Supports undo/redo natively
- Handles complex editing scenarios

### Consequences

**Positive**:
- ✅ Structured content (not messy HTML)
- ✅ Custom nodes for story elements
- ✅ Great performance
- ✅ Future collaboration support
- ✅ Active development

**Negative**:
- ❌ Newer library (less mature than ProseMirror)
- ❌ Smaller ecosystem (fewer plugins)
- ❌ Learning curve for custom nodes
- ❌ API still evolving

### Alternatives Considered

**1. ProseMirror**
- **Pros**: Mature, battle-tested, great docs
- **Cons**: Steep learning curve, complex API, not React-native
- **Why rejected**: Too complex for our needs

**2. Slate**
- **Pros**: React-first, simple API, good docs
- **Cons**: Performance issues at scale, API instability, less maintained
- **Why rejected**: Performance and stability concerns

**3. Draft.js**
- **Pros**: Made by Facebook, React integration
- **Cons**: No longer actively maintained, deprecated, performance issues
- **Why rejected**: Abandoned by Facebook in favor of Lexical

**4. Custom Editor**
- **Pros**: Total control, optimized for our use case
- **Cons**: Months of development, browser inconsistencies, accessibility hard
- **Why rejected**: Too much engineering effort

---

## ADR-003: Git for Version Control

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Architecture Team

### Context

Writers need version control ("Time Machine") to:
- Save snapshots of their work
- Compare versions
- Restore previous versions
- Experiment with alternate versions (multiverse)

**Options**:
1. Git (industry standard)
2. Custom versioning system
3. Delta storage (only store changes)
4. Full copy snapshots

### Decision

**Use Git as the underlying version control system, abstracted from users.**

### Rationale

**Proven & Mature**:
- Git is battle-tested (billions of repos)
- Handles large files efficiently
- Solves hard problems (merging, branching, history)
- Industry standard (writers may already know Git)

**Efficient Storage**:
- Only stores diffs between versions
- Compresses content automatically
- Handles binary files (for future: images, audio)
- Scales to gigabytes of content

**Powerful Features**:
- Branches = "multiverse" (alternate versions)
- Tags = snapshots with labels
- Diffs = visual comparison
- Revert = restore previous version

**Tooling Ecosystem**:
- Existing Git tools work (if user wants CLI access)
- Can sync to GitHub/GitLab (future feature)
- Merge tools available
- GUIs available (Gitk, SourceTree)

**Hidden Complexity**:
- Users never see commit hashes
- UI uses metaphors: "snapshots" not "commits"
- "Time Machine" not "Git log"
- No merge conflicts for single-user initially

### Consequences

**Positive**:
- ✅ Robust version control
- ✅ Efficient storage
- ✅ Proven at scale
- ✅ Future collaboration support
- ✅ Existing tools compatible

**Negative**:
- ❌ Adds dependency (pygit2 or libgit2)
- ❌ Git repository overhead (~200KB for .git/)
- ❌ Need to abstract Git concepts for writers
- ❌ Merge conflicts if multi-user later

### Alternatives Considered

**1. Custom Versioning System**
- **Pros**: Full control, optimized for manuscripts
- **Cons**: Reinventing the wheel, months of work, bugs
- **Why rejected**: Git already solves this perfectly

**2. Delta Storage (Custom)**
- **Pros**: Simple implementation, small storage
- **Cons**: Slow for large histories, no branching, complex merges
- **Why rejected**: Less efficient than Git

**3. Full Copy Snapshots**
- **Pros**: Very simple, instant restore
- **Cons**: Storage grows linearly, wasteful for large manuscripts
- **Why rejected**: Doesn't scale

---

## ADR-004: Python Backend with FastAPI

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Backend Team

### Context

We need a backend for:
- NLP (entity extraction, analysis)
- AI integration (LLM calls)
- Database operations
- API endpoints for frontend

**Language Options**:
1. Python (with FastAPI)
2. Node.js (with Express/Nest)
3. Rust (with Actix)
4. Go (with Gin/Fiber)

### Decision

**Use Python 3.11+ with FastAPI framework.**

### Rationale

**NLP Ecosystem**:
- spaCy (NLP) is Python-first
- Best NER (named entity recognition) libraries in Python
- HuggingFace transformers (Python)
- Coreference resolution libraries (Python)
- **This is the deciding factor**: NLP requires Python

**AI/LLM Integration**:
- LangChain (Python)
- OpenAI SDK (Python-first)
- Anthropic SDK (Python)
- Local LLMs (llama.cpp Python bindings)

**FastAPI Benefits**:
- Async/await support (fast I/O)
- Auto-generated OpenAPI docs
- Pydantic validation (type safety)
- WebSocket support
- Modern, actively developed

**Developer Experience**:
- Type hints (Python 3.11+)
- Great IDE support (VS Code, PyCharm)
- Easy to read and maintain
- Large talent pool

### Consequences

**Positive**:
- ✅ Best NLP libraries available
- ✅ Excellent AI/LLM ecosystem
- ✅ Fast development (FastAPI)
- ✅ Auto-generated API docs
- ✅ Strong typing (Pydantic)

**Negative**:
- ❌ Python slower than compiled languages
- ❌ GIL limitations (can work around with async)
- ❌ Larger deployment size
- ❌ Dependency management (pip/poetry)

### Alternatives Considered

**1. Node.js**
- **Pros**: JavaScript everywhere, fast I/O, npm ecosystem
- **Cons**: Poor NLP libraries, weak typing (even with TypeScript for runtime)
- **Why rejected**: NLP libraries in JS are inferior

**2. Rust**
- **Pros**: Blazing fast, memory safe, great for performance
- **Cons**: No NLP libraries, steep learning curve, slower development
- **Why rejected**: NLP doesn't exist in Rust

**3. Go**
- **Pros**: Fast, simple concurrency, good for APIs
- **Cons**: Weak NLP ecosystem, no ML libraries
- **Why rejected**: NLP requirements

---

## ADR-005: SQLite for Development Database

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Backend Team

### Context

We need a database for:
- Manuscripts and scenes
- Entities and relationships
- Timeline events
- Version metadata
- User preferences

**Development vs Production needs differ**.

### Decision

**Use SQLite for development and MVP. Migrate to PostgreSQL for multi-user production.**

### Rationale

**SQLite for MVP**:

**Zero Configuration**:
- No server to install
- Single file database
- Bundled with Python
- Perfect for desktop app

**Performance**:
- Fast for single-user access
- Good for <100GB of data
- Efficient for read-heavy workloads
- WAL mode for concurrency

**Portability**:
- Database is a single file
- Easy to backup (copy file)
- Can sync via Dropbox/iCloud (future)
- Cross-platform

**Development Speed**:
- No setup required
- Easy to delete and recreate
- Great for testing
- Simple migrations

**Perfect for Desktop App**:
- Users don't need to run database server
- App is self-contained
- Works offline automatically
- No configuration needed

### Consequences

**Positive**:
- ✅ Zero-config setup
- ✅ Perfect for desktop/single-user
- ✅ Fast development
- ✅ Easy backup/restore
- ✅ Portable

**Negative**:
- ❌ Limited concurrency (not an issue for single-user)
- ❌ Weaker for multi-user (planned migration)
- ❌ Smaller ecosystem than PostgreSQL
- ❌ Some SQL feature limitations

**Migration Path**:
- MVP: SQLite
- Multi-user cloud: PostgreSQL
- Mobile read-only: SQLite sync

### Alternatives Considered

**1. PostgreSQL**
- **Pros**: Full-featured, great for multi-user, robust
- **Cons**: Requires server, complex setup, overkill for desktop
- **Why deferred**: Use later for cloud version

**2. MongoDB**
- **Pros**: Flexible schema, good for JSON
- **Cons**: Requires server, inconsistent for relationships
- **Why rejected**: Our data is relational

**3. IndexedDB (browser)**
- **Pros**: Built into browsers, no backend needed
- **Cons**: Not for desktop apps, query limitations
- **Why rejected**: We're building desktop-first

---

## ADR-006: Timeline Orchestrator as Separate Phase

**Status**: Accepted
**Date**: 2025-12-15
**Deciders**: Product Team

### Context

The Timeline Orchestrator feature is substantial:
- 6 new database tables
- 5 complex validators
- 9 API endpoints
- 10+ frontend components

**Should it be**:
1. Integrated into Phase 2 (Codex)
2. Part of Phase 3 (AI features)
3. Separate phase (Phase 2A)

### Decision

**Create Phase 2A (Weeks 7-8) specifically for Timeline Orchestrator.**

### Rationale

**Scope**:
- Too large to add to Phase 2 (would extend from 3 weeks to 5 weeks)
- Not related to AI (doesn't fit Phase 3)
- Deserves focused development time

**Dependencies**:
- Requires Codex (characters, locations) - so must be after Phase 2
- Can be built independently of AI features
- Coach integration can happen later (Phase 3)

**Risk Management**:
- Separating reduces complexity
- Easier to test in isolation
- Can ship MVP without Timeline if needed
- Allows early user feedback

**Clear Deliverable**:
- Phase 2A has single focus: timeline validation
- Easier to track progress
- Clear success metrics

### Consequences

**Positive**:
- ✅ Focused development (2 weeks)
- ✅ Clear milestones
- ✅ Can be optional feature
- ✅ Easier to test
- ✅ Lower risk

**Negative**:
- ❌ Extends total timeline by 2 weeks (13→16 weeks)
- ❌ Another phase to manage
- ❌ Delayed integration with Coach

### Alternatives Considered

**1. Add to Phase 2 (Codex)**
- **Why rejected**: Too much scope, would delay core Codex features

**2. Add to Phase 3 (AI)**
- **Why rejected**: Not related to AI generation, wrong grouping

**3. Post-MVP Feature**
- **Why rejected**: Too valuable for fantasy/sci-fi writers, competitive differentiator

---

## ADR-007: Teaching-First Design Philosophy

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: Product Team, UX Team

### Context

How should we approach feedback and validation?

**Options**:
1. **Prescriptive**: "Your pacing is wrong. Fix it."
2. **Descriptive**: "Scene is 200 words. Average is 400."
3. **Teaching**: "Here's why pacing matters to readers..."

### Decision

**Adopt a teaching-first philosophy across all features.**

Every issue detected includes:
- **Description**: What's wrong
- **Suggestion**: Multiple options to fix (not one "right" answer)
- **Teaching Point**: Why it matters + examples from published works

### Rationale

**Empowerment vs Prescription**:
- Writers want to learn, not just fix issues
- Teaching builds skills, not dependency
- Respects writer's creative choices
- Explains the "why" not just the "what"

**Long-term Value**:
- Writers improve over time
- Understand craft principles
- Make informed decisions
- Less hand-holding needed later

**Differentiation**:
- Most tools just flag issues ("passive voice detected")
- We explain WHY it matters
- Cite examples (Game of Thrones, Lord of the Rings)
- Reference craft books (Save the Cat, Story Grid)

**Trust Building**:
- Shows we respect writer's intelligence
- Not a "know-it-all" tool
- Acknowledges multiple valid approaches
- Builds confidence

### Examples

**Bad (Prescriptive)**:
```
❌ "Arya travels too fast. Change the timeline."
```

**Good (Teaching-First)**:
```
✅ Description: "Arya appears 900km away 5 days later at horse speed (80km/day, needs 11 days)"

Suggestion: "Options:
1. Extend timeline by 6 days
2. Use faster travel method (explain magic/flying)
3. Add a travel scene showing the journey
4. Remove one appearance if not critical"

Teaching Point: "Fantasy readers subconsciously track travel time and distance.
Game of Thrones shows this well: characters take weeks to travel between cities,
which makes the world feel real. If you introduce magic travel, readers will wonder
why characters don't use it to solve other problems. Either make travel methods
consistent or establish clear rules for when magic can/can't be used."
```

### Consequences

**Positive**:
- ✅ Writers learn craft principles
- ✅ Builds long-term skills
- ✅ Differentiates from competitors
- ✅ Respectful tone
- ✅ Multiple solutions offered

**Negative**:
- ❌ More content to write (teaching points)
- ❌ Longer feedback messages
- ❌ Need to research examples from published works
- ❌ Requires craft knowledge to write teaching content

---

## ADR-008: Hybrid Local/Cloud LLM Strategy

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: AI Team

### Context

AI features need LLMs (Large Language Models). Options:
1. Cloud only (OpenAI, Anthropic)
2. Local only (Llama, Mistral)
3. Hybrid (both, with smart routing)

### Decision

**Implement hybrid LLM strategy with smart routing based on task complexity, privacy, and cost.**

### Routing Logic

| Task | Model | Rationale |
|------|-------|-----------|
| Grammar check | Local (Llama 8B) | Fast, simple, private |
| Paraphrasing | Local (Llama 8B) | Fast, simple, private |
| Simple rewrite | Local (Mistral 7B) | Medium complexity, private |
| Beat expansion | Cloud (Claude 3.5 Sonnet) | Complex, quality critical |
| Plotting help | Cloud (GPT-4o) | Complex reasoning needed |
| Style matching | Cloud (Claude) | Needs deep understanding |

### Rationale

**Privacy**:
- Sensitive content stays local (grammar, simple edits)
- Cloud only for non-sensitive or user-approved content
- User controls routing ("never send to cloud")

**Cost**:
- Local is free (after GPU investment)
- Cloud is $0.015/1K tokens (Claude 3.5 Sonnet)
- Smart routing saves money

**Quality**:
- Local models good for simple tasks
- Cloud models better for complex tasks
- Use best tool for each job

**Performance**:
- Local: <1s latency (if GPU)
- Cloud: 2-3s latency
- Route accordingly

**Offline**:
- Core features work offline (local models)
- Advanced features require internet (cloud models)
- Graceful degradation

### Consequences

**Positive**:
- ✅ Privacy for sensitive tasks
- ✅ Cost optimization
- ✅ Quality for complex tasks
- ✅ Offline support for basics
- ✅ Flexibility

**Negative**:
- ❌ Complex routing logic
- ❌ Need to ship local models (~4GB download)
- ❌ GPU recommended for local models
- ❌ More code paths to maintain

### Alternatives Considered

**1. Cloud Only**
- **Pros**: Simple, best quality
- **Cons**: Privacy concerns, cost, no offline
- **Why rejected**: Privacy and offline requirements

**2. Local Only**
- **Pros**: Private, free, offline
- **Cons**: Quality limitations, GPU needed, slow on CPU
- **Why rejected**: Can't match cloud quality

---

## ADR-009: Maxwell Design System

**Status**: Accepted
**Date**: 2025-11-23
**Deciders**: UX Team, Frontend Team

### Context

Visual design for a writing IDE targeting authors who love classic literature.

**Brand Options**:
1. Modern/Minimalist (Notion-style)
2. Writer's Classic (Scrivener-style)
3. Code Editor (VS Code-style)
4. Literary Classic (Book-inspired)

### Decision

**Create "Maxwell Design System" inspired by classic literary aesthetics.**

### Design Tokens

```typescript
const maxwellTheme = {
  colors: {
    vellum: '#F9F7F1',      // Warm paper background
    midnight: '#1E293B',     // Primary text (deep blue-black)
    bronze: '#B48E55',       // Accents, CTAs (warm metallic)
    fadedInk: '#64748B',     // Secondary text
    slateUI: '#E2E8F0',      // Borders, UI elements
    redline: '#9F1239'       // Errors, delete actions
  },
  typography: {
    serif: 'EB Garamond',    // Body text, manuscript
    sans: 'Inter'            // UI, controls
  }
};
```

### Rationale

**Target Audience**:
- Writers love books
- Appreciate craftsmanship
- Value aesthetics
- Spend hours in the app

**Emotional Connection**:
- Evokes classic books and manuscripts
- Feels like a "writing tool" not "software"
- Warm, inviting, not cold/technical
- Respects the craft of writing

**Differentiation**:
- Most writing tools use modern/minimal or cluttered
- We use literary classic
- Stands out visually
- Memorable brand

**Usability**:
- High contrast (vellum + midnight)
- Bronze accents guide attention
- Serif for reading, sans for UI
- Accessibility compliant (WCAG AA)

### Consequences

**Positive**:
- ✅ Unique brand identity
- ✅ Emotionally resonant for writers
- ✅ Differentiated from competitors
- ✅ Beautiful, craft-focused
- ✅ Accessible

**Negative**:
- ❌ May not appeal to technical writers
- ❌ Serif fonts can be polarizing
- ❌ More design work upfront
- ❌ Custom theme (not using defaults)

---

## ADR-010: JSON for Entity Attributes

**Status**: Accepted
**Date**: 2025-12-15
**Deciders**: Backend Team

### Context

Entity attributes (character traits, location details) need flexible storage.

**Options**:
1. Fixed schema (columns for each attribute)
2. EAV (Entity-Attribute-Value) table
3. JSON column
4. Separate attributes table with FK

### Decision

**Store entity attributes as JSON in a single column.**

### Rationale

**Flexibility**:
- Different entity types have different attributes
- Character: age, height, house, skills
- Location: climate, population, government
- JSON allows any structure

**Simplicity**:
- Single column, easy to query
- No JOIN complexity
- Easy to add new attributes

**Performance**:
- SQLite supports JSON functions
- Can index JSON paths if needed
- Good for 1000s of entities

**Evolution**:
- Easy to change attribute structure
- No migrations for new attributes
- Writers can add custom fields

### Example

```sql
-- Characters
{
  "age": 11,
  "house": "Stark",
  "skills": ["swordfighting", "stealth"],
  "physicalDescription": "Small for her age, brown hair, grey eyes"
}

-- Locations
{
  "climate": "temperate",
  "population": 500000,
  "government": "monarchy",
  "defenses": ["walls", "guards", "castle"]
}
```

### Consequences

**Positive**:
- ✅ Flexible schema
- ✅ Easy to evolve
- ✅ Simple queries
- ✅ Writer-friendly (can add fields)

**Negative**:
- ❌ Harder to query specific attributes
- ❌ No type validation at DB level
- ❌ Can become inconsistent
- ❌ Larger storage than normalized

**Migration Path**:
- If we hit query performance issues: Extract common attributes to columns
- If we need strict typing: Add Pydantic validation layer

### Alternatives Considered

**1. Fixed Schema**
- **Why rejected**: Too rigid, different entity types have different attributes

**2. EAV Table**
- **Why rejected**: Complex queries (lots of JOINs), poor performance

**3. Separate Attributes Table**
- **Why rejected**: Overkill for MVP, complex schema

---

## Summary of Decisions

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| 001 | Desktop-First | Accepted | High - Defines entire architecture |
| 002 | Lexical Editor | Accepted | High - Core user experience |
| 003 | Git for Versioning | Accepted | Medium - Internal implementation |
| 004 | Python + FastAPI | Accepted | High - Enables NLP capabilities |
| 005 | SQLite for MVP | Accepted | Medium - Can migrate later |
| 006 | Timeline as Phase 2A | Accepted | Medium - Extends timeline by 2 weeks |
| 007 | Teaching-First | Accepted | High - Defines product philosophy |
| 008 | Hybrid LLM | Accepted | High - Enables privacy + quality |
| 009 | Maxwell Design | Accepted | Medium - Brand differentiation |
| 010 | JSON Attributes | Accepted | Low - Implementation detail |

---

## Decision Process

When making architectural decisions:

1. **Identify the decision** to be made
2. **Gather context** (requirements, constraints, options)
3. **List alternatives** (at least 3)
4. **Evaluate trade-offs** for each alternative
5. **Document rationale** (why chosen, why others rejected)
6. **Consider consequences** (positive and negative)
7. **Define migration path** (if applicable)
8. **Get stakeholder buy-in**
9. **Document as ADR**

---

**Maintained By**: Architecture Team
**Last Review**: 2025-12-15
**Next Review**: 2026-01-15 (or after major decisions)
