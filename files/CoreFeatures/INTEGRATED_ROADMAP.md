# Maxwell/Codex IDE: Integrated Feature Roadmap

**Last Updated**: 2025-12-15
**Project Status**: Phase 1 Complete, Phase 2+ In Planning
**Total Timeline**: 16 weeks (4 months) for MVP

---

## Overview

This roadmap shows how all features integrate together to create a comprehensive writing IDE that helps authors with:
- **Creative Writing** (Living Manuscript)
- **Story Consistency** (The Codex + Timeline Orchestrator)
- **AI Assistance** (The Muse + The Coach)
- **Structural Analysis** (Pacing, Consistency, Timeline Validation)

---

## Feature Integration Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAXWELL WRITING IDE                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │  MANUSCRIPT  │ │   CODEX   │ │  TIMELINE   │
        │   (Editor)   │ │ (Knowledge)│ │(Validation) │
        └──────┬───────┘ └─────┬─────┘ └──────┬──────┘
               │               │               │
               └───────┬───────┴───────┬───────┘
                       │               │
                ┌──────▼──────┐ ┌─────▼─────┐
                │   THE MUSE  │ │ THE COACH │
                │ (Generation)│ │ (Learning)│
                └─────────────┘ └───────────┘
```

### Integration Details

**1. Manuscript → Codex**
- Auto-detects entity mentions in text
- Suggests new characters/locations to add to Codex
- Links entity mentions to Codex entries (clickable)

**2. Manuscript → Timeline**
- Events can reference manuscript scenes
- Timeline validates story dates against manuscript content
- Detects inconsistencies between timeline and prose

**3. Codex → Timeline**
- Characters shared between Codex and Timeline
- Locations shared between both systems
- Timeline uses Codex data for validation

**4. Timeline → Coach**
- Coach learns from timeline patterns
- Coach references timeline issues in feedback
- Cross-validates timeline logic with prose consistency

**5. Codex → Muse**
- GraphRAG uses Codex for context retrieval
- AI generation maintains consistency with Codex facts
- Entity relationships inform story suggestions

**6. Timeline → Structural Analysis**
- Timeline gaps inform pacing analysis
- Character presence tracking complements arc analysis
- Causality validation enhances plot hole detection

---

## 16-Week Development Timeline

### Phase 1: Core Experience (Weeks 1-3) ✅ COMPLETE
**Goal**: Distraction-free editor that never loses work

- ✅ **Week 1**: Project setup + Lexical editor
  - Monorepo structure
  - React + Vite + TypeScript
  - Python + FastAPI
  - Rich text editor with custom nodes
  - Maxwell Design System

- ⏳ **Week 2**: Auto-save + versioning backend
  - SQLite database setup
  - Git-based versioning (pygit2)
  - Version service implementation
  - Auto-save with 5s debounce

- ⏳ **Week 3**: Time Machine UI + variant system
  - History slider visualization
  - Snapshot management
  - Diff viewer
  - Scene variants (multiverse)

**Deliverable**: Working editor with version control

---

### Phase 2: Knowledge Layer (Weeks 4-6)
**Goal**: Build the "story bible" that knows everything

- ⏳ **Week 4**: spaCy NLP + entity extraction
  - Install and configure spaCy
  - Entity extraction pipeline
  - Pronoun resolution
  - Background entity detection

- ⏳ **Week 5**: Codex UI + suggestion queue
  - Entity card components
  - Create/edit entity forms
  - Suggestion approval workflow
  - Entity search and filtering

- ⏳ **Week 6**: Relationship graph + visualizer
  - Relationship detection logic
  - Force-directed graph visualization
  - Interactive graph exploration
  - Relationship strength tracking

**Deliverable**: Codex system that tracks characters, locations, items, lore

**Integration**: Codex provides knowledge base for Timeline and Muse

---

### Phase 2A: Timeline Orchestrator ⭐ NEW (Weeks 7-8)
**Goal**: Timeline validation + teaching for multi-POV stories

- ⏳ **Week 7**: Database + Service
  - Database schema (6 new models)
    - TimelineEvent
    - Location (shared with Codex)
    - TravelLeg
    - TimelineIssue
    - TravelSpeedProfile
    - LocationDistance
  - TimelineOrchestratorService
    - 5 validators (impossible travel, dependencies, presence, gaps, paradoxes)
    - Teaching points for each issue type
  - Unit tests for all validators

- ⏳ **Week 8**: API + Frontend
  - 9 REST API endpoints
    - Event CRUD
    - Location CRUD
    - Travel leg tracking
    - Validation endpoint
    - Speed profile configuration
    - Comprehensive data retrieval
  - Frontend components
    - TimelineOrchestrator (main container)
    - TimelineVisualization (vertical timeline)
    - TimelineEventCard (event display)
    - TimelineIssuesPanel (issues sidebar)
    - TimelineTeachingPanel (learning moments)
    - TimelineControls (filters & actions)
  - Forms for event/location/travel management
  - Maxwell Design System integration

**Deliverable**: Timeline validation system with teaching capabilities

**Integration**:
- Uses Codex characters and locations
- Feeds issues to Coach for personalized feedback
- Complements structural analysis

**Key Features**:
1. **Impossible Travel Detection** - "Character can't travel 900km in 5 days at horse speed"
2. **Dependency Validation** - "Prerequisite event must happen before dependent event"
3. **Character Presence** - "Character appears only once - underdeveloped?"
4. **Timing Gaps** - "30+ day gap between events - intentional?"
5. **Paradox Detection** - "Circular dependency: A→B→C→A is impossible"

---

### Phase 3: Generative Layer (Weeks 9-14)
**Goal**: AI-powered writing assistance with LangChain agents

- ⏳ **Week 9**: LangChain setup
  - LLM factory (Claude, GPT, local models)
  - Smart routing (cloud vs local)
  - Streaming responses
  - Codex tools for LangChain agents

- ⏳ **Week 10**: GraphRAG implementation
  - Entity context retrieval
  - Vector-based similarity search
  - RAG prompt engineering
  - Embedding service

- ⏳ **Week 11**: Beat expansion + style matching
  - Beat-to-prose UI (split pane)
  - Style matching analysis
  - Sensory "paint" tools
  - Streaming generation UI

- ⏳ **Week 12-13**: The Coach (Learning Agent)
  - Database schema (coaching_history, writing_profile)
  - WritingCoach agent implementation
  - Tool integration (Codex, pacing, consistency, **timeline**)
  - Feedback UI components
  - Learning loop (tracks reactions)

- ⏳ **Week 14**: Timeline-Coach integration
  - Coach references timeline issues
  - Timeline patterns in writer profile
  - Cross-validation (timeline + prose)
  - Teaching content library

**Deliverable**: AI assistant that learns your style and provides personalized feedback

**Integration**:
- Coach uses Timeline Orchestrator data for validation
- Coach uses Codex for fact-checking
- Coach learns from timeline patterns
- Muse uses Codex for consistent generation

---

### Phase 4: Polish & Distribution (Weeks 15-16)
**Goal**: Production-ready application

- ⏳ **Week 15**: Pacing + consistency + testing
  - Pacing graph (Vonnegut)
  - Consistency linter
  - Unit tests (>60% coverage)
  - Integration tests
  - E2E tests (Playwright)

- ⏳ **Week 16**: Electron packaging + deployment
  - Electron app packaging
  - Build pipeline (GitHub Actions)
  - Windows/Mac/Linux installers
  - Auto-update mechanism
  - Documentation

**Deliverable**: Shipped desktop application

---

## Feature Dependency Graph

```
Project Setup (Week 1)
    ↓
Lexical Editor (Week 1)
    ↓
Version Control Backend (Week 2)
    ↓
Time Machine UI (Week 3)
    ↓
┌───────────────┴───────────────┐
│                               │
Codex (Weeks 4-6)        Timeline Orchestrator (Weeks 7-8)
│                               │
└───────────────┬───────────────┘
                ↓
    ┌───────────┴───────────┐
    │                       │
LangChain Setup      Structural Analysis
(Week 9)              (Week 15)
    ↓                       ↓
GraphRAG                 Pacing Graph
(Week 10)                   │
    ↓                       │
Beat Expansion              │
(Week 11)                   │
    ↓                       │
The Coach ←─────────────────┘
(Weeks 12-14)
    ↓
Deployment
(Week 16)
```

---

## Epic Summary

| Epic | Weeks | Effort | Priority | Key Features | Dependencies |
|------|-------|--------|----------|--------------|--------------|
| **1. Living Manuscript** | 1-3 | 9 days | Critical | Editor, Versioning, Variants | None |
| **2. The Codex** | 4-6 | 10 days | High | Entity extraction, Relationships | Epic 1 |
| **3. Timeline Orchestrator** ⭐ | 7-8 | 9 days | High | Timeline validation, Teaching | Epic 1, 2 |
| **4. The Muse** | 9-14 | 17 days | High | AI generation, GraphRAG, Coach | Epic 2, 3 |
| **5. Structural Analysis** | 15 | 6 days | Medium | Pacing, Consistency | Epic 1, 2, 3 |
| **6. Deployment** | 16 | 3 days | High | Packaging, Distribution | All |
| **Total** | **16 weeks** | **54 days** | | | |

---

## Integration Scenarios

### Scenario 1: Writing a Fantasy Battle Scene

```
1. WRITER types in Editor:
   "Arya arrived at King's Landing on the 15th..."

2. CODEX detects:
   - Entity: "Arya" (character)
   - Entity: "King's Landing" (location)
   - Suggests adding to Codex if not present

3. TIMELINE checks:
   - Was Arya somewhere else recently?
   - How far away was previous location?
   - Is this physically possible?
   - → Detects impossible travel if too fast

4. COACH analyzes:
   - Checks prose consistency
   - References timeline issue if found
   - Provides personalized feedback:
     "I noticed Arya travels 900km in 5 days. Timeline Orchestrator
     flagged this as impossible at horse speed. Consider: 1) Extend
     timeline, 2) Explain magic travel, 3) Remove one appearance."

5. MUSE assists:
   - Uses Codex context (Arya's traits, King's Landing description)
   - Uses Timeline context (previous events)
   - Generates consistent prose if requested
```

### Scenario 2: Planning a Multi-POV Story

```
1. WRITER creates Timeline:
   - Event: "Jon takes the black" (Day 1, The Wall)
   - Event: "Daenerys marries Drogo" (Day 1, Essos)
   - Event: "Jon meets wildlings" (Day 60, Beyond the Wall)
   - Event: "Daenerys hatches dragons" (Day 100, Dothraki Sea)

2. TIMELINE ORCHESTRATOR validates:
   - Character presence: ✓ Both have 2+ events
   - Travel time: ✓ Jon travels 50km (possible)
   - Dependencies: ✓ No circular references
   - Gaps: ⚠️ 40 days between Jon events
   - → Suggests: "Consider what Jon does between Day 60-100"

3. CODEX tracks:
   - Jon: Location history (The Wall → Beyond Wall)
   - Daenerys: Location history (Essos → Dothraki Sea)
   - Relationships: Jon-Wildlings, Daenerys-Drogo

4. COACH learns:
   - Writer prefers 60-100 day gaps between POV switches
   - Writer tends to underdevelop travel scenes
   - Adjusts future feedback accordingly

5. STRUCTURAL ANALYSIS shows:
   - Pacing graph: Both arcs have good tension rise
   - Timeline consistency: ✓ All events logically ordered
```

---

## Teaching-First Philosophy

Every feature includes **teaching moments**:

1. **Timeline Orchestrator**: Explains WHY timing matters to readers
   - "Fantasy readers subconsciously track distance..."
   - Examples from Game of Thrones, Lord of the Rings

2. **Coach**: Learns writer's patterns and explains craft principles
   - "I notice you tend to rush dialogue scenes..."
   - References writing craft books

3. **Codex**: Helps writers understand consistency
   - "This contradicts earlier description of character's eyes..."
   - Teaches importance of story bibles

4. **Structural Analysis**: Explains pacing and structure
   - "Tension drops here - intentional or missed opportunity?"
   - References Save the Cat, 3-act structure

---

## Technical Architecture Integration

### Database Layer
```
SQLite (Primary)
├── manuscripts
├── scenes
├── entities (Codex)
├── relationships (Codex)
├── timeline_events ⭐ NEW
├── locations ⭐ NEW (shared with Codex)
├── travel_legs ⭐ NEW
├── timeline_issues ⭐ NEW
├── travel_speed_profiles ⭐ NEW
├── location_distances ⭐ NEW
├── snapshots (versioning)
├── coaching_history (Coach)
└── writing_profile (Coach)

ChromaDB (Vectors)
├── scene_embeddings (RAG)
├── entity_embeddings (RAG)
└── coach_memory (per user)

Git (.codex/)
└── Version history (immutable)
```

### API Routes Integration
```
/api/manuscripts/*        (Epic 1)
/api/versioning/*         (Epic 1)
/api/codex/*              (Epic 2)
/api/timeline/* ⭐ NEW    (Epic 3 - Timeline Orchestrator)
/api/generate/*           (Epic 4 - Muse)
/api/coach/* ⭐ NEW       (Epic 4 - Coach)
/api/analyze/*            (Epic 5 - Structural)
```

### Frontend Routes
```
/                         → Manuscript Library
/editor/:id               → Lexical Editor
/codex                    → Entity Management
/timeline ⭐ NEW          → Timeline Orchestrator
/history                  → Time Machine
/coach ⭐ NEW             → Writing Coach
/analysis                 → Pacing + Consistency
```

---

## Risk Mitigation with Timeline Orchestrator

| Original Risk | Timeline Orchestrator Solution |
|--------------|-------------------------------|
| Writers lose track of multi-POV timelines | Timeline Orchestrator visualizes all events chronologically |
| Plot holes from impossible travel | Impossible travel validator with distance/speed calculations |
| Broken causality (A before B before A) | Paradox detector using graph algorithms |
| Underdeveloped characters | Character presence validator flags 0 or 1 event characters |
| Pacing issues from large gaps | Timing gap detector flags >30 day gaps between events |

---

## Success Metrics

### User Experience
- Writers can manage 50+ timeline events without confusion
- Timeline validation catches 95%+ of logic errors
- Teaching points rated "helpful" by 70%+ of users
- Writers improve timeline understanding after 3+ uses

### Technical Performance
- Timeline validation: <500ms for 1000+ events ✓ (target)
- Editor latency: <50ms keystroke rendering ✓ (target)
- Database queries: <100ms for graph lookups ✓ (target)
- AI generation: <2s to first token ✓ (target)

### Integration Health
- Codex-Timeline data sharing: 100% consistent
- Coach-Timeline cross-validation: Working in Phase 3
- Muse-Codex context retrieval: Working in Phase 3
- No data loss across integrated systems

---

## Development Priorities

### Must Have (MVP)
1. ✅ Lexical Editor
2. ✅ Manuscript Management
3. ⏳ Version Control (Week 2-3)
4. ⏳ Codex (Week 4-6)
5. ⏳ Timeline Orchestrator (Week 7-8) ⭐ NEW
6. ⏳ Basic AI Generation (Week 9-11)
7. ⏳ The Coach (Week 12-14)

### Should Have (Post-MVP)
8. ⏳ Advanced Visualization (timeline heat maps)
9. ⏳ Collaboration Features
10. ⏳ Cloud Sync
11. ⏳ Mobile Companion App

### Nice to Have (Future)
12. Custom AI Model Fine-tuning
13. Export to EPUB/PDF
14. Plugin System
15. Multi-language Support

---

## Next Actions

### Immediate (Week 2-3)
1. Complete versioning backend (Git + pygit2)
2. Implement Time Machine UI
3. Test version control end-to-end

### Short-term (Week 4-8)
1. Implement Codex (spaCy + entity extraction)
2. Build relationship graph visualizer
3. **Implement Timeline Orchestrator database schema** ⭐
4. **Build TimelineOrchestratorService with 5 validators** ⭐
5. **Create Timeline visualization components** ⭐

### Medium-term (Week 9-14)
1. Set up LangChain with Claude/GPT/Local models
2. Implement GraphRAG with Codex integration
3. Build The Coach agent with learning loop
4. **Integrate Timeline Orchestrator with Coach** ⭐

### Long-term (Week 15-16)
1. Complete structural analysis tools
2. Package Electron application
3. Set up deployment pipeline
4. Conduct user testing

---

## Documentation Status

### Core Documentation ✅
- [x] SPECIFICATION.md (Master spec)
- [x] ARCHITECTURE.md (System design)
- [x] IMPLEMENTATION_PLAN.md (Task breakdown)
- [x] DEVELOPMENT_PHASES.md (14-week → 16-week roadmap)
- [x] PROGRESS.md (Task tracking)
- [x] INTEGRATED_ROADMAP.md (This document) ⭐ NEW

### Timeline Orchestrator Documentation ✅ NEW
- [x] TIMELINE-ORCHESTRATOR-SPEC.md (809 lines)
- [x] 01-DATABASE-SCHEMA.md (405 lines)
- [x] 02-BACKEND-SERVICE.md (744 lines)
- [x] 03-API-ROUTES.md
- [x] QUICK-REFERENCE.md (493 lines)
- [x] TEACHING_FEATURES.md
- [x] ORCHESTRATOR_README.md (479 lines)

### To Be Created
- [ ] API_DOCUMENTATION.md (OpenAPI spec)
- [ ] TESTING_STRATEGY.md (Detailed test plans)
- [ ] DEPLOYMENT_GUIDE.md (Production setup)
- [ ] USER_GUIDE.md (End-user documentation)

---

## Conclusion

The **Timeline Orchestrator** (Phase 2A, Weeks 7-8) is now fully integrated into the Maxwell/Codex IDE roadmap. It adds:

✅ **9 days of development effort**
✅ **6 new database models**
✅ **5 intelligent validators**
✅ **9 RESTful API endpoints**
✅ **10+ frontend components**
✅ **Teaching-first design philosophy**

This feature targets fantasy/sci-fi writers with complex multi-POV narratives and teaches them about:
- Travel logistics and reader expectations
- Causality and story logic
- Character development and presence
- Pacing through time gaps
- Avoiding temporal paradoxes

The Timeline Orchestrator integrates seamlessly with:
- **The Codex** (shared characters/locations)
- **The Coach** (cross-validated feedback)
- **Structural Analysis** (pacing validation)

**Total Updated Timeline**: 16 weeks (4 months) for MVP with Timeline Orchestrator

---

**Status**: Ready for implementation
**Next Phase**: Week 2 (Versioning Backend)
**Next New Feature**: Week 7 (Timeline Orchestrator Database)

**Updated**: 2025-12-15
**Maintained By**: Development Team
