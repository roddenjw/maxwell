# Codex IDE: Development Phases

## Table of Contents
1. [Phase Overview](#phase-overview)
2. [Phase 1: The Core Experience](#phase-1-the-core-experience)
3. [Phase 2: The Knowledge Layer](#phase-2-the-knowledge-layer)
4. [Phase 3: The Generative Layer](#phase-3-the-generative-layer)
5. [Phase 4: The Polish & Teacher](#phase-4-the-polish--teacher)
6. [Phase 5: Deployment & Launch](#phase-5-deployment--launch)
7. [Quality Gates](#quality-gates)
8. [User Feedback Integration](#user-feedback-integration)

---

## Phase Overview

Each phase follows the principle of **"Invisible Engineering"** - building complex backend systems while maintaining a simple, metaphorical frontend experience.

### Development Principles
- **Ship incrementally**: Each phase delivers user-facing value
- **Test continuously**: Unit, integration, E2E tests at every step
- **Document as you go**: Update docs with architectural decisions
- **User-centric**: Validate assumptions with user testing

### Timeline Summary

| Phase | Duration | Key Deliverable | User Value |
|-------|----------|-----------------|------------|
| Phase 1 | 3 weeks | Working editor with versioning | "Never lose work" |
| Phase 2 | 3 weeks | Codex with entity extraction | "Tool knows the characters" |
| Phase 3 | 4 weeks | AI-powered writing assistance | "Helps write when stuck" |
| Phase 4 | 2 weeks | Analysis & polish tools | "Teaches structure and editing" |
| Phase 5 | 2 weeks | Production-ready desktop app | "Installable software" |
| **Total** | **14 weeks** | **Full MVP** | **Complete writing IDE** |

---

## Phase 1: The Core Experience

**Goal**: A distraction-free editor that "never loses work"

**Duration**: 3 weeks (15 working days)

### Week 1: Foundation & Editor

#### Day 1-2: Project Setup
**Tasks**:
- [ ] Initialize monorepo structure
- [ ] Set up frontend (React + Vite + TypeScript)
- [ ] Set up backend (Python + FastAPI)
- [ ] Configure development environment
- [ ] Initialize Git repository with proper `.gitignore`

**Deliverables**:
- `npm run dev` starts frontend
- `uvicorn app.main:app --reload` starts backend
- Both communicate via API

**Validation**:
```bash
# Frontend health check
curl http://localhost:5173

# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

---

#### Day 3-5: Lexical Editor Implementation
**Tasks**:
- [ ] Create `ManuscriptEditor.tsx` component
- [ ] Implement basic toolbar (bold, italic, headings)
- [ ] Add keyboard shortcuts (Ctrl+B, Ctrl+I)
- [ ] Implement Markdown support
- [ ] Add word count display

**Code Checkpoint**:
```typescript
// Verify editor works
const editorState = editor.getEditorState();
const json = editorState.toJSON();
console.log(json); // Should show Lexical AST
```

**Validation**:
- Can type text and see it rendered
- Formatting buttons work
- Keyboard shortcuts work
- Word count updates in real-time

---

### Week 2: Database & Versioning Backend

#### Day 6-7: Database Setup
**Tasks**:
- [ ] Configure SQLAlchemy with SQLite
- [ ] Create initial schema (manuscripts, scenes, snapshots)
- [ ] Set up Alembic migrations
- [ ] Create database initialization script
- [ ] Implement `ManuscriptRepository` class

**Validation**:
```python
# Test database operations
manuscript = ManuscriptRepository.create(title="Test Novel")
assert manuscript.id is not None

retrieved = ManuscriptRepository.get(manuscript.id)
assert retrieved.title == "Test Novel"
```

---

#### Day 8-10: Git-Based Versioning
**Tasks**:
- [ ] Install and configure `pygit2`
- [ ] Create `.codex/` repository structure
- [ ] Implement `VersionService` class
  - `create_snapshot()`
  - `get_history()`
  - `restore_snapshot()`
- [ ] Create API endpoints for versioning
- [ ] Write unit tests for Git operations

**Code Checkpoint**:
```python
# Test snapshot creation
version_service.create_snapshot(
    manuscript_id="ms-001",
    label="Chapter 1 complete",
    trigger_type="MANUAL"
)

history = version_service.get_history("ms-001")
assert len(history) > 0
```

**Validation**:
- Can create Git commits programmatically
- Can retrieve commit history
- Can checkout previous commits without data loss

---

### Week 3: Auto-Save & Time Machine UI

#### Day 11-12: Auto-Save Implementation
**Tasks**:
- [ ] Create `AutoSavePlugin.tsx` with 5-second debounce
- [ ] Implement save status indicator
- [ ] Add save endpoint (`PUT /api/manuscripts/{id}`)
- [ ] Implement optimistic updates with TanStack Query
- [ ] Add error handling for failed saves

**Code Checkpoint**:
```typescript
// Test auto-save
const { mutate } = useMutation({
  mutationFn: saveManuscript,
  onSuccess: () => console.log('Saved!')
});

// Triggers after 5 seconds of inactivity
```

**Validation**:
- Content saves 5 seconds after typing stops
- Save indicator shows "Saving..." then "Saved"
- Can refresh page without data loss

---

#### Day 13-15: Time Machine UI
**Tasks**:
- [ ] Create `HistorySlider.tsx` component
- [ ] Design timeline visualization with date markers
- [ ] Create `SnapshotCard.tsx` with icons for trigger types
- [ ] Implement `DiffViewer.tsx` (green for added, red for removed)
- [ ] Add "Restore this Version" functionality
- [ ] Add confirmation dialog before restore

**Code Checkpoint**:
```typescript
// Test diff calculation
const changes = diffWords(oldText, newText);
console.log(changes);
// Should show added/removed/unchanged parts
```

**Validation**:
- Timeline displays all snapshots chronologically
- Clicking snapshot shows preview
- Diff view highlights changes correctly
- Restore creates safety snapshot before overwriting

---

### Phase 1 Milestone: Demo & User Testing

**What to Demo**:
1. Write a paragraph in the editor
2. Show auto-save indicator
3. Close and reopen app (data persists)
4. Open Time Machine
5. Show snapshot history
6. Restore previous version
7. Verify content restored

**Success Criteria**:
- [ ] Editor feels responsive (<50ms input latency)
- [ ] Auto-save works reliably
- [ ] No data loss scenarios
- [ ] Time Machine metaphor is intuitive
- [ ] Users can understand versioning without Git knowledge

**User Feedback Questions**:
1. Did you understand how versioning works?
2. Did you trust that your work was being saved?
3. Was the Time Machine UI intuitive?
4. What would make you feel safer about your data?

---

## Phase 2: The Knowledge Layer

**Goal**: The tool "knows" who the characters are

**Duration**: 3 weeks (15 working days)

### Week 4: NLP Pipeline & Codex Schema

#### Day 16-17: spaCy Setup
**Tasks**:
- [ ] Install spaCy and download `en_core_web_lg`
- [ ] Install neuralcoref for pronoun resolution
- [ ] Create `NLPService` class
- [ ] Implement `extract_entities(text)` function
- [ ] Implement `extract_proper_nouns(text)` function
- [ ] Write unit tests for entity extraction

**Code Checkpoint**:
```python
# Test entity extraction
text = "Elara walked through the Crystal Cavern with her companion, Thorne."
entities = nlp_service.extract_entities(text)

assert ("Elara", "PERSON") in entities
assert ("Thorne", "PERSON") in entities
assert ("Crystal Cavern", "LOC") in entities
```

**Validation**:
- spaCy pipeline loads in <5 seconds
- Entity extraction accuracy >80% on test corpus
- Pronoun resolution works for simple cases

---

#### Day 18-19: Codex Schema & Database
**Tasks**:
- [ ] Create `Entity` Pydantic model
- [ ] Create `Character`, `Location`, `Item`, `Lore` subclasses
- [ ] Create `entities` table in SQLite
- [ ] Create `relationships` table
- [ ] Create TypeScript types matching Python models
- [ ] Implement `CodexRepository` class

**Code Checkpoint**:
```python
# Test entity creation
character = Character(
    id=str(uuid.uuid4()),
    name="Elara Vance",
    aliases=["El", "The Wanderer"],
    attributes={
        "age": 24,
        "appearance": "Scar on left cheek",
        "voice": "Sarcastic, short sentences"
    }
)

CodexRepository.create(character)
retrieved = CodexRepository.get(character.id)
assert retrieved.name == "Elara Vance"
```

**Validation**:
- All entity types can be created and retrieved
- JSON serialization works frontend ↔ backend
- Database constraints prevent invalid data

---

#### Day 20: ChromaDB & KuzuDB Setup
**Tasks**:
- [ ] Install ChromaDB and create collections
- [ ] Install KuzuDB and define graph schema
- [ ] Create embedding service for entity descriptions
- [ ] Implement `VectorRepository` for similarity search
- [ ] Implement `GraphRepository` for relationship queries

**Code Checkpoint**:
```python
# Test vector storage
embedding_service.add_entity_embedding(
    entity_id="uuid-1234",
    entity_type="CHARACTER",
    description="Elara Vance, brave warrior with cybernetic eye"
)

similar = embedding_service.find_similar_entities("warrior woman", top_k=3)
assert "Elara Vance" in [e.name for e in similar]
```

**Validation**:
- ChromaDB can store and retrieve embeddings
- Similarity search returns relevant results
- Graph queries execute in <100ms

---

### Week 5: Entity Extraction & Suggestion Queue

#### Day 21-23: Asynchronous Entity Detection
**Tasks**:
- [ ] Create background task system with FastAPI
- [ ] Create `entity_suggestions` table
- [ ] Implement `analyze_manuscript_async()` function
- [ ] Create suggestion comparison logic (check existing Codex)
- [ ] Add WebSocket endpoint for real-time updates
- [ ] Create API endpoints:
  - `POST /api/analyze/extract-entities`
  - `GET /api/codex/suggestions`
  - `POST /api/codex/suggestions/{id}/approve`

**Code Checkpoint**:
```python
# Test async analysis
background_tasks.add_task(
    process_text_for_entities,
    manuscript_id="ms-001",
    text="John entered the haunted castle."
)

# Wait for processing
await asyncio.sleep(2)

suggestions = get_suggestions("ms-001")
assert any(s.name == "John" for s in suggestions)
```

**Validation**:
- Analysis completes within 10 seconds for 5,000 words
- Suggestions don't include existing entities
- WebSocket pushes updates to frontend

---

#### Day 24-25: Suggestion Queue UI
**Tasks**:
- [ ] Create `SuggestionQueue.tsx` component
- [ ] Create `SuggestionCard.tsx` with approve/reject buttons
- [ ] Add notification badge to Codex sidebar
- [ ] Implement WebSocket listener in frontend
- [ ] Add toast notifications for new suggestions
- [ ] Implement approval flow (creates entity in Codex)

**Code Checkpoint**:
```typescript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/analysis');
ws.onmessage = (event) => {
  const suggestion = JSON.parse(event.data);
  toast(`New character detected: ${suggestion.name}`);
};
```

**Validation**:
- Suggestions appear in sidebar within 5 seconds
- Approve button creates entity correctly
- Reject button removes from queue
- Badge count accurate

---

### Week 6: Codex UI & Relationship Graph

#### Day 26-27: Codex Sidebar
**Tasks**:
- [ ] Create `CodexSidebar.tsx` component
- [ ] Create `EntityCard.tsx` for display
- [ ] Create `EntityForm.tsx` for create/edit
- [ ] Implement entity type filter (Characters, Locations, etc.)
- [ ] Add search functionality
- [ ] Create contextual panel (shows entities mentioned in current scene)

**Code Checkpoint**:
```typescript
// Test contextual filtering
const sceneText = "Elara entered the Crystal Cavern.";
const relevantEntities = extractEntityMentions(sceneText);

console.log(relevantEntities);
// Expected: ["Elara", "Crystal Cavern"]
```

**Validation**:
- Sidebar displays all entities
- Clicking entity shows details
- Edit form works and syncs to backend
- Contextual panel updates as cursor moves

---

#### Day 28-30: Relationship Detection & Graph
**Tasks**:
- [ ] Implement `extract_relationships()` in NLP service
- [ ] Create relationship detection rules (verbs like "kissed", "fought")
- [ ] Create `create_or_update_relationship()` function
- [ ] Create `RelationshipGraph.tsx` using `react-force-graph`
- [ ] Add interactive features (click node, hover link)
- [ ] Implement graph filtering by entity type

**Code Checkpoint**:
```python
# Test relationship detection
text = "Elara fought alongside Thorne against the dragon."
relationships = extract_relationships(text, ["Elara", "Thorne"])

assert ("Elara", "Thorne", "ALLIANCE") in relationships
```

**Validation**:
- Relationships detected with >70% accuracy
- Graph renders all entities and connections
- Line thickness represents interaction count
- Clicking node opens entity details

---

### Phase 2 Milestone: Demo & User Testing

**What to Demo**:
1. Write: "Sarah met John at the old lighthouse."
2. Show suggestion queue detecting Sarah, John, lighthouse
3. Approve all suggestions
4. Show Codex sidebar with three entities
5. Edit Sarah's attributes (add age, appearance)
6. Show contextual panel highlighting relevant entities
7. Open relationship graph
8. Show connection between Sarah and John

**Success Criteria**:
- [ ] Entity detection works automatically
- [ ] Approval process is quick and intuitive
- [ ] Codex feels like a "living encyclopedia"
- [ ] Relationship graph provides insights
- [ ] No Git/database concepts visible to user

**User Feedback Questions**:
1. Did the entity suggestions feel accurate?
2. Was it clear when to approve vs. reject?
3. Did the Codex help you keep track of your story?
4. Was the relationship graph useful?

---

## Phase 3: The Generative Layer

**Goal**: The tool helps write the story when stuck

**Duration**: 4 weeks (20 working days)

### Week 7: LLM Router & Local Models

#### Day 31-33: Local LLM Setup
**Tasks**:
- [ ] Install `llama-cpp-python` with GPU support
- [ ] Download Llama 3 8B GGUF model (quantized)
- [ ] Create `BaseLLM` abstract class
- [ ] Create `LocalLLM` implementation
- [ ] Test generation speed (should be >10 tokens/sec)
- [ ] Implement streaming response

**Code Checkpoint**:
```python
# Test local generation
llm = LocalLLM("models/llama-3-8b-q4.gguf")
response = await llm.generate(
    prompt="Write a sentence about a brave knight.",
    max_tokens=50
)

print(response)
# Expected: "Sir Galahad raised his sword against the dragon..."
```

**Validation**:
- Model loads in <30 seconds
- Generation speed >10 tokens/second (on GPU)
- Text quality is coherent
- Streaming works without buffering

---

#### Day 34-35: Cloud LLM Integration
**Tasks**:
- [ ] Install `anthropic` SDK
- [ ] Install `openai` SDK
- [ ] Create `ClaudeLLM` implementation
- [ ] Create `OpenAILLM` implementation
- [ ] Implement API key management (secure storage)
- [ ] Add error handling for rate limits

**Code Checkpoint**:
```python
# Test Claude API
claude = ClaudeLLM(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await claude.generate(
    prompt="Write a dramatic scene opening.",
    system_prompt="You are a fiction writing assistant."
)

print(response)
```

**Validation**:
- API calls succeed
- Streaming works
- Error messages are user-friendly
- API keys never logged

---

#### Day 36-37: LLM Router Implementation
**Tasks**:
- [ ] Create `LLMRouter` class
- [ ] Implement task complexity detection
- [ ] Add user preference handling (local-only, cloud-only, auto)
- [ ] Create `POST /api/generate` endpoint with streaming
- [ ] Add rate limiting middleware
- [ ] Implement fallback logic (cloud → local if API fails)

**Code Checkpoint**:
```python
# Test router selection
router = LLMRouter()

# Simple task → local model
llm = router.select_model(TaskComplexity.SIMPLE)
assert isinstance(llm, LocalLLM)

# Complex task → cloud model (if available)
llm = router.select_model(TaskComplexity.COMPLEX)
assert isinstance(llm, ClaudeLLM) or isinstance(llm, LocalLLM)
```

**Validation**:
- Router selects correct model based on complexity
- Fallback works when cloud unavailable
- User preferences respected

---

### Week 8: GraphRAG & Context Retrieval

#### Day 38-40: Entity Context Retrieval
**Tasks**:
- [ ] Create `RAGService` class
- [ ] Implement `get_entity_context(entity_names, manuscript_id)`
- [ ] Implement `get_scene_context(location_name, manuscript_id)`
- [ ] Create prompt templates for context injection
- [ ] Test context formatting for LLMs

**Code Checkpoint**:
```python
# Test context retrieval
context = rag_service.get_entity_context(
    entity_names=["Elara", "Crystal Cavern"],
    manuscript_id="ms-001"
)

print(context)
# Expected:
# Elara (CHARACTER):
# - age: 24
# - appearance: Scar on left cheek
#
# Crystal Cavern (LOCATION):
# - description: A glittering underground cave
```

**Validation**:
- Context includes all relevant attributes
- Formatting is LLM-friendly
- Performance <100ms for 5 entities

---

#### Day 41-42: Vector-Based Similarity Search
**Tasks**:
- [ ] Install `sentence-transformers`
- [ ] Create `EmbeddingService` class
- [ ] Implement `embed_text(text)` function
- [ ] Implement `find_similar_scenes(query, manuscript_id, top_k)`
- [ ] Create background job to embed all scenes
- [ ] Add embedding cache

**Code Checkpoint**:
```python
# Test similarity search
similar = embedding_service.find_similar_scenes(
    query="A fight scene in a dark forest",
    manuscript_id="ms-001",
    top_k=3
)

print([s.content[:100] for s in similar])
# Should return scenes with combat in forest settings
```

**Validation**:
- Embeddings generated in <1 second per scene
- Similarity search returns relevant scenes
- Results improve with more data

---

#### Day 43: RAG Prompt Engineering
**Tasks**:
- [ ] Create `build_rag_prompt()` function
- [ ] Design system prompt template
- [ ] Design user prompt template
- [ ] Test prompt effectiveness with sample requests
- [ ] A/B test different prompt formats

**Code Checkpoint**:
```python
# Test RAG prompt construction
system_prompt, user_prompt = build_rag_prompt(
    user_request="Write a scene where Elara enters the Crystal Cavern",
    manuscript_id="ms-001",
    entity_names=["Elara", "Crystal Cavern"]
)

print(system_prompt)
# Should include entity traits and location details
```

**Validation**:
- Generated text includes entity details
- Style matches existing manuscript
- Contradictions <5% in testing

---

### Week 9: Beat Expansion & Style Matching

#### Day 44-46: Beat Expansion UI
**Tasks**:
- [ ] Create `BeatExpander.tsx` split-pane component
- [ ] Implement beat list (editable bullet points)
- [ ] Add "Expand" button for each beat
- [ ] Implement streaming response display
- [ ] Add "Insert to Manuscript" button
- [ ] Create keyboard shortcuts (Ctrl+E to expand)

**Code Checkpoint**:
```typescript
// Test beat expansion
const beat = "Hero discovers a secret door in the library";
const prose = await expandBeat(beat);

console.log(prose);
// Expected: ~300 words of prose based on the beat
```

**Validation**:
- Beat expansion generates 200-400 words
- Prose matches manuscript style
- Streaming shows progressive typing effect
- Insert button adds to editor correctly

---

#### Day 47-48: Style Matching Implementation
**Tasks**:
- [ ] Install `textstat` for readability analysis
- [ ] Create `StyleAnalyzer` class
- [ ] Implement `analyze_writing_style(text)` function
  - Calculate avg sentence length
  - Calculate burstiness (sentence length variance)
  - Calculate Flesch reading score
  - Calculate lexical diversity
- [ ] Create `build_style_matching_prompt(previous_text)` function
- [ ] Integrate style matching into beat expansion

**Code Checkpoint**:
```python
# Test style analysis
text = "Short sentence. This one is longer and more complex. Brief again."
style = analyze_writing_style(text)

print(style)
# Expected:
# {
#   "avg_sentence_length": 4.5,
#   "burstiness": 2.3,
#   "flesch_score": 75,
#   "lexical_diversity": 0.85
# }
```

**Validation**:
- Style analysis produces consistent metrics
- Generated prose matches source burstiness ±20%
- Reading level matches ±10 Flesch points

---

#### Day 49-50: AI Toolbar Integration
**Tasks**:
- [ ] Create `AIAssistToolbar.tsx` in editor
- [ ] Add buttons: "Continue", "Rewrite", "Expand Beat"
- [ ] Implement "Continue from cursor" feature
- [ ] Add loading states and error handling
- [ ] Create undo/redo for AI insertions

**Validation**:
- Toolbar appears when focused in editor
- "Continue" generates coherent next sentences
- "Rewrite" maintains meaning while changing style
- All features work with keyboard shortcuts

---

### Week 10: Sensory Paint Tools

#### Day 51-53: Floating Toolbar
**Tasks**:
- [ ] Create `FloatingToolbar.tsx` component
- [ ] Implement text selection detection
- [ ] Position toolbar above selection
- [ ] Add sensory buttons (Sight, Smell, Sound)
- [ ] Add transformation buttons (Intensify, Show Don't Tell)
- [ ] Implement replace selection functionality

**Code Checkpoint**:
```typescript
// Test sensory enhancement
const original = "He entered the room.";
const enhanced = await applySensoryPaint(original, 'sight');

console.log(enhanced);
// Expected: "He stepped into the dimly lit room, where shadows
// danced along the cracked plaster walls."
```

**Validation**:
- Toolbar appears on text selection
- Each transformation button works
- Original text replaced smoothly
- Undo restores original text

---

#### Day 54-55: Prompt Engineering for Transformations
**Tasks**:
- [ ] Create prompt templates for each tool:
  - Sight: "Add vivid visual descriptions"
  - Smell: "Add olfactory details"
  - Sound: "Add auditory elements"
  - Intensify: "Make more dramatic and intense"
  - Show Don't Tell: "Convert telling to showing"
- [ ] Test each prompt with 10+ examples
- [ ] Refine prompts based on output quality
- [ ] Add context awareness (genre, tone)

**Validation**:
- Each tool produces distinct output
- Transformations feel natural, not forced
- User testing shows >80% satisfaction

---

### Phase 3 Milestone: Demo & User Testing

**What to Demo**:
1. Open beat expander with outline: "• Hero finds ancient map • Map leads to treasure • Villain appears"
2. Expand first beat → show streaming prose generation
3. Insert prose into manuscript
4. Select a paragraph in editor
5. Show floating toolbar
6. Click "Sight" → show enhanced description
7. Use "Continue" button to extend scene
8. Show consistency with Codex entities

**Success Criteria**:
- [ ] AI generation feels instantaneous (<2s to first token)
- [ ] Generated prose is coherent and on-topic
- [ ] Style matching produces similar writing
- [ ] Tools are discoverable and intuitive
- [ ] No "AI slop" (generic, overly flowery text)

**User Feedback Questions**:
1. Did AI help you overcome writer's block?
2. Was generated text useful or did you delete it?
3. Which tool did you use most?
4. Did the style matching work well?

---

## Phase 4: The Polish & Teacher

**Goal**: Teach structure and editing

**Duration**: 2 weeks (10 working days)

### Week 11: Pacing Graph & Consistency Linter

#### Day 56-58: Pacing Analysis
**Tasks**:
- [ ] Install `textblob` for sentiment analysis
- [ ] Create `PacingAnalyzer` class
- [ ] Implement `analyze_pacing(text, chunk_size=500)`
  - Calculate sentiment per chunk
  - Calculate tension (active verb density)
  - Calculate sentence length
- [ ] Create API endpoint `GET /api/analyze/pacing/{manuscript_id}`
- [ ] Create `PacingGraph.tsx` using Chart.js/Recharts
- [ ] Add insights (detect flat sections)

**Code Checkpoint**:
```python
# Test pacing analysis
text = "He walked slowly. Then he ran fast! The explosion rocked the building."
pacing_data = analyze_pacing(text)

print(pacing_data)
# Expected array with sentiment and tension scores
```

**Validation**:
- Pacing data calculated in <5 seconds for 50,000 words
- Graph renders smoothly
- Flat sections correctly identified
- Insights are actionable

---

#### Day 59-60: Consistency Linter
**Tasks**:
- [ ] Create `ConsistencyChecker` class
- [ ] Implement `check_consistency(text, manuscript_id)`
- [ ] Create attribute extraction from text
- [ ] Compare text attributes with Codex
- [ ] Create `ConsistencyLinterPlugin.tsx`
- [ ] Add purple wavy underline for errors
- [ ] Create tooltip showing contradiction details

**Code Checkpoint**:
```python
# Test consistency checking
# Codex says: John has blue eyes
text = "John's brown eyes gleamed in the light."

errors = check_consistency(text, "ms-001")
assert len(errors) == 1
assert errors[0].attribute == "eyes"
assert errors[0].codex_value == "blue"
assert errors[0].text_value == "brown"
```

**Validation**:
- Consistency errors detected accurately
- False positive rate <10%
- Underlines appear in editor
- Clicking opens Codex to fix

---

### Week 12: Testing & Bug Fixes

#### Day 61-63: Comprehensive Testing
**Tasks**:
- [ ] Write unit tests for all services (target: 60% coverage)
- [ ] Write integration tests for all API endpoints
- [ ] Write E2E tests for critical user flows:
  - Create manuscript → write → save → restore
  - Entity detection → approval → codex display
  - Beat expansion → insert to manuscript
  - Consistency error detection → fix
- [ ] Run performance profiling
- [ ] Fix any bugs found during testing

**Validation**:
- All tests pass
- Code coverage >60%
- No critical bugs
- Performance meets targets

---

#### Day 64-65: Polish & UX Refinement
**Tasks**:
- [ ] Add keyboard shortcut guide (Ctrl+?)
- [ ] Add tooltips to all buttons
- [ ] Implement dark mode
- [ ] Add user preferences panel
- [ ] Improve loading states across app
- [ ] Add empty states (e.g., "No entities yet")
- [ ] Final accessibility audit (WCAG 2.1 AA)

**Validation**:
- All features have keyboard shortcuts
- UI feels polished and professional
- Dark mode works everywhere
- Accessibility score >90

---

### Phase 4 Milestone: Beta Testing

**Beta Test Plan**:
1. Recruit 10-15 fiction writers
2. Give 1-week trial period
3. Collect feedback via:
   - In-app surveys
   - User interviews
   - Analytics (with permission)
4. Prioritize top 5 pain points
5. Fix critical issues before launch

**Success Criteria**:
- [ ] No data loss incidents
- [ ] All core features work reliably
- [ ] User satisfaction score >4/5
- [ ] Would recommend to other writers: >70%

---

## Phase 5: Deployment & Launch

**Goal**: Production-ready installable software

**Duration**: 2 weeks (10 working days)

### Week 13: Electron Packaging

#### Day 66-68: Electron Setup
**Tasks**:
- [ ] Create `electron/` directory
- [ ] Create `main.js` for Electron main process
- [ ] Create `preload.js` for security
- [ ] Bundle Python backend with PyInstaller
- [ ] Configure auto-start of backend server
- [ ] Test IPC communication
- [ ] Add window state persistence

**Code Checkpoint**:
```javascript
// Test backend auto-start
function startBackend() {
  const pythonPath = path.join(__dirname, 'python', 'codex-backend');
  backendProcess = spawn(pythonPath);

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
}

app.whenReady().then(startBackend);
```

**Validation**:
- Backend starts automatically on app launch
- Frontend can communicate with backend
- App window opens reliably
- Closing app stops backend gracefully

---

#### Day 69-70: Platform-Specific Builds
**Tasks**:
- [ ] Configure `electron-builder`
- [ ] Create Windows installer (NSIS)
- [ ] Create macOS DMG
- [ ] Create Linux AppImage
- [ ] Add app icons for each platform
- [ ] Configure code signing (macOS)
- [ ] Test installers on clean VMs

**Validation**:
- Installers build successfully
- Apps install without errors
- Uninstallers work correctly
- File associations work (.codex files)

---

### Week 14: CI/CD & Documentation

#### Day 71-72: Build Pipeline
**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Configure matrix builds (Windows, macOS, Linux)
- [ ] Add automated testing in CI
- [ ] Configure release automation
- [ ] Set up artifact storage
- [ ] Create auto-updater configuration

**Code Checkpoint**:
```yaml
# Test CI pipeline
name: Build & Release
on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    # ... build steps
```

**Validation**:
- CI builds pass on all platforms
- Artifacts generated correctly
- Auto-updater can fetch new versions

---

#### Day 73-74: Documentation
**Tasks**:
- [ ] Write user manual (Getting Started, Features, FAQ)
- [ ] Create video tutorials:
  - Getting started (5 min)
  - Using the Codex (3 min)
  - AI writing assistance (4 min)
  - Time Machine versioning (2 min)
- [ ] Write API documentation (for future plugins)
- [ ] Create troubleshooting guide
- [ ] Write privacy policy
- [ ] Create LICENSE file (recommend: GPL-3.0 or MIT)

**Deliverables**:
- `docs/user-guide.md`
- `docs/video-tutorials/` (hosted on YouTube/Vimeo)
- `docs/api/` (for developers)
- `PRIVACY.md`
- `LICENSE`

---

#### Day 75: Launch Preparation
**Tasks**:
- [ ] Create landing page (codex-ide.com)
- [ ] Set up download hosting (GitHub Releases)
- [ ] Prepare launch announcement (blog post)
- [ ] Create social media posts
- [ ] Set up support email (support@codex-ide.com)
- [ ] Create Discord/Forum community
- [ ] Final security audit
- [ ] Create press kit

**Validation**:
- Website loads correctly
- Download links work
- Support channels monitored
- Community guidelines published

---

### Phase 5 Milestone: Public Launch

**Launch Checklist**:
- [ ] All platforms build successfully
- [ ] Documentation complete
- [ ] No critical bugs
- [ ] Auto-updater tested
- [ ] Analytics/crash reporting configured (opt-in)
- [ ] Support system ready
- [ ] Marketing materials prepared
- [ ] Press outreach completed

**Success Metrics (First Month)**:
- Downloads: >500
- Active users: >200
- Crash rate: <1%
- Support ticket resolution: <24 hours
- App store rating: >4.0/5

---

## Quality Gates

Each phase must pass these gates before proceeding:

### Technical Quality Gates
- [ ] All tests pass (unit, integration, E2E)
- [ ] Code coverage >60%
- [ ] No critical security vulnerabilities
- [ ] Performance targets met (see ARCHITECTURE.md)
- [ ] No known data loss bugs
- [ ] Documentation updated

### User Experience Gates
- [ ] Feature demo completed successfully
- [ ] User testing feedback collected
- [ ] UX issues addressed or documented
- [ ] Accessibility requirements met
- [ ] Error messages are user-friendly

### Process Gates
- [ ] Code reviewed by at least one other developer
- [ ] Architecture decisions documented (TDRs)
- [ ] Git history is clean and descriptive
- [ ] No hardcoded secrets in codebase

---

## User Feedback Integration

### Feedback Collection Methods

1. **In-App Surveys**
   - After completing first manuscript
   - After using AI features 10 times
   - After 1 week of use

2. **User Interviews**
   - 30-min video calls with 3-5 users per phase
   - Focus on pain points and delighters

3. **Analytics** (with explicit user consent)
   - Feature usage (which tools used most)
   - Performance metrics (load times, crash rates)
   - NO manuscript content collected

4. **Community Channels**
   - Discord server for discussions
   - GitHub Issues for bug reports
   - Feature request board (e.g., Canny)

### Feedback Prioritization

Use the **RICE framework**:
- **Reach**: How many users affected?
- **Impact**: How much does it improve experience?
- **Confidence**: How sure are we this is right?
- **Effort**: How long will it take?

Score = (Reach × Impact × Confidence) / Effort

### Iteration Cycles

After each phase:
1. Collect feedback (1-2 days)
2. Analyze and prioritize (1 day)
3. Address critical issues (2-3 days)
4. Document learnings (0.5 days)
5. Update roadmap for next phase

---

## Risk Management

### High-Impact Risks

| Risk | Mitigation | Contingency |
|------|------------|-------------|
| **spaCy accuracy too low** | Use larger model (en_core_web_trf), fine-tune on fiction corpus | Add manual entity creation flow, reduce auto-suggestions |
| **Local LLM too slow** | Use smaller quantized model (4-bit), optimize with GPU | Default to cloud models, show "processing" indicator |
| **Electron bundle too large** | Use Tauri instead, optimize assets | Accept larger size, use delta updates |
| **User data loss** | Extensive testing, automatic backups | Implement data recovery tool, export to JSON |
| **API costs too high** | Prefer local models, cache responses | Add usage limits, require user API keys |

### Weekly Risk Review

Every Friday:
1. Review risks from past week
2. Identify new risks
3. Update mitigation strategies
4. Adjust timeline if needed

---

## Post-Launch Roadmap

### Version 1.1 (Month 2-3)
- [ ] Export to EPUB, PDF, manuscript format
- [ ] Advanced plotting tools (Save the Cat wizard)
- [ ] Custom themes and fonts
- [ ] Dictation mode (speech-to-text)

### Version 1.2 (Month 4-6)
- [ ] Plugin system for custom AI models
- [ ] Collaboration features (read-only sharing)
- [ ] Mobile companion app (iOS/Android)
- [ ] Cloud sync (optional, encrypted)

### Version 2.0 (Month 7-12)
- [ ] Real-time co-editing
- [ ] Project templates (genres: fantasy, sci-fi, romance)
- [ ] Advanced analytics (character arc visualizer)
- [ ] Integration with publishing platforms

---

## Developer Handoff Checklist

When transferring this project to developers:

### Prerequisites
- [ ] Development machines meet requirements (16GB RAM, GPU recommended)
- [ ] Developers have access to:
  - GitHub repository
  - API keys (Anthropic, OpenAI)
  - Design files (Figma/Sketch)

### Onboarding Tasks (First Week)
- [ ] Clone repository
- [ ] Set up development environment
- [ ] Run all tests successfully
- [ ] Read ARCHITECTURE.md and SPECIFICATION.md
- [ ] Complete "hello world" task (e.g., add a button)

### Team Roles
- **Frontend Developer**: React, Lexical, UI components
- **Backend Developer**: Python, FastAPI, NLP pipeline
- **DevOps Engineer**: CI/CD, deployment, monitoring
- **QA Engineer**: Testing, bug tracking, user acceptance

### Communication
- **Daily Standups**: 15 min sync (async for remote teams)
- **Weekly Demos**: Show progress to stakeholders
- **Sprint Planning**: 2-week sprints, align with phases
- **Retrospectives**: After each phase, document learnings

---

## Conclusion

This 14-week development plan transforms the Codex IDE specification into a production-ready application. Each phase delivers tangible user value while maintaining technical excellence.

**Key Success Factors**:
1. **User-centric design**: Test early and often
2. **Incremental delivery**: Ship value every week
3. **Technical rigor**: Maintain code quality throughout
4. **Invisible engineering**: Hide complexity behind metaphors
5. **Community building**: Engage users from day one

**Next Steps**:
1. Review this plan with team and stakeholders
2. Adjust timeline based on available resources
3. Set up project management tools (Jira, Linear, etc.)
4. Begin Phase 1: The Core Experience

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Maintained By**: Project Lead

**Questions or Concerns?** Contact: project-lead@codex-ide.com
