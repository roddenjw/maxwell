# Maxwell Implementation Plan v2.0
## Integrated Roadmap: MVP → PLG Growth Engine

**Last Updated:** January 25, 2026
**Vision:** The world's most intuitive fiction writing IDE with invisible engineering and viral growth mechanics

---

## Executive Summary

This plan integrates the full development roadmap from MVP launch to PLG growth engine:
- **Phases 1-3:** MVP, Codex, and AI Integration (COMPLETE)
- **Phases 4-6:** Story Structure, Brainstorming, Timeline Orchestrator (COMPLETE)
- **Phase 7:** PLG Features and Viral Mechanics (PLANNED)
- **Phase 8:** Library & World Management (COMPLETE)

**Key Principle:** Each phase must ship a feature that drives the next phase's growth.

**Current Status:** See [PROGRESS.md](./PROGRESS.md) for detailed progress tracking, metrics, and active work.

---

## Phase 1: The MVP — "The Binder"
**Timeline:** Months 1-3 (January - March 2026)
**Status:** ✅ Complete
**Goal:** Launch a fully functional Scrivener alternative with local-first storage

### Core Features
- Rich text editor with Lexical framework
- Hierarchical chapter/folder structure (Scrivener-like binder)
- Drag-and-drop chapter reordering
- Local-first SQLite storage
- Export to DOCX/PDF formats
- Git-based version control (snapshots)
- Auto-save functionality

### Success Criteria
- ✅ Writers can create multi-chapter manuscripts
- ✅ Writers can organize chapters into folders
- ✅ Writers can export completed manuscripts
- ✅ All data stored locally (no cloud dependency)
- ✅ Version history with snapshot restoration

### Target Audience
Indie authors, r/writing community, writing Twitter, Scrivener users seeking alternatives

### Pricing Model
Beta Lifetime Deal ($49)

---

## Phase 2: The Logic Layer — "The Codex"
**Timeline:** Months 4-6 (Q1-Q2 2026)
**Status:** ✅ Complete
**Goal:** Automatic worldbuilding and consistency tracking

### Core Features
- **Entity Extraction:** NLP-powered detection of characters, locations, items
- **Codex Database:** Centralized registry of all story elements
- **Relationship Graph:** Visual connections between characters
- **Consistency Checking:** Track character appearances, location usage
- **Entity Suggestions:** One-click approval of detected entities
- **Merge/Split:** Resolve duplicate entities

### Technical Approach
- spaCy for named entity recognition (NER)
- SQLAlchemy models for entity storage
- Force-directed graph visualization
- Real-time extraction with background processing

### Success Criteria
- ✅ Entity extraction accuracy >85%
- ✅ Auto-detection of characters/locations as writer types
- ✅ Writers can track 50+ entities without manual entry
- ✅ Relationship graph shows character connections

### Revenue Target
$50,000 ARR from early adopters

---

## Phase 3: The AI Integration — "Zero Mark-up AI"
**Timeline:** Months 7-9 (July - September 2026)
**Status:** ✅ Complete
**Goal:** Guided BYOK (Bring Your Own Key) with OpenRouter integration

### Core Features
- **OpenRouter Integration:** Access to 100+ AI models with single API
- **BYOK Model:** User provides API key, pays OpenRouter directly (zero markup)
- **Fast Coach:** Real-time writing feedback (Python-based, instant)
- **Smart Coach:** AI-powered deep analysis (Claude/GPT, on-demand)
- **Recap Engine:** AI-generated chapter summaries
- **Usage Tracking:** Token usage and cost transparency

### Technical Approach
- FastAPI backend for AI orchestration
- OpenRouter API for model aggregation
- Two-tier coaching system (see ARCHITECTURE_DECISIONS.md ADR-002)
- Lexical JSON parsing for content extraction

### Success Criteria
- ✅ Users can enable AI with one click
- ✅ Real-time feedback appears within 2 seconds
- ✅ Chapter recaps generated in <10 seconds
- ✅ Zero markup on AI costs (transparent pricing)

### Pricing Model
Keep at $99 base price + user pays OpenRouter directly

### Target Audience
Sudowrite refugees, cost-conscious authors, AI-curious writers

---

## Phase 4: Story Structure & Outline Engine
**Timeline:** Months 10-13 (Q3 2026)
**Status:** ✅ 100% Complete (Jan 12, 2026)
**Goal:** Proven story structure templates with plot beat tracking

### Core Features

#### 4.1 Story Structure Templates
- **9 Built-in Structures:**
  - Hero's Journey (17 beats)
  - Save the Cat (15 beats)
  - Three-Act Structure (8 beats)
  - Five-Act Structure (10 beats)
  - Seven-Point Story Structure (7 beats)
  - Freytag's Pyramid (5 beats)
  - Dan Harmon's Story Circle (8 beats)
  - Fichtean Curve (variable beats)
  - Kishōtenketsu (4 beats)
- **Genre-Specific Defaults:** Fantasy, Thriller, Romance, Sci-Fi, Mystery
- **Custom Templates:** Users can create their own structures

#### 4.2 Manuscript Creation Wizard
- Choose story structure at manuscript creation
- Genre selection with tailored templates
- Pre-populated plot beat checkpoints
- Optional vs. mandatory outline paths (pantser-friendly)

#### 4.3 Plot Beat Tracking
- Progress visualization (donut charts, percentage complete)
- Checkpoint system tied to chapter completion
- Beat-to-chapter mapping
- Narrative arc visualization (emotional beats over time)

#### 4.4 Outline Editor
- Drag-and-drop beat reordering
- Beat descriptions with AI-powered suggestions
- Plot beat cards with narrative importance
- Switch structure mid-project (preserve custom beats)

#### 4.5 Integration with Editor
- Scene-level guidance tied to current plot beat
- "You are here" marker in outline sidebar
- Auto-update beat completion based on chapter progress
- Gantt-style timeline with beat markers

### Technical Approach
- **Backend:** SQLAlchemy models for StoryStructure, PlotBeat, Checkpoint
- **Frontend:** Zustand store for outline state, custom plot beat components
- **AI Integration:** Claude API for beat suggestions and scene guidance
- **Visualization:** Recharts for progress charts, D3.js for timeline views

### Success Criteria
- Writers can choose from 9 proven story structures
- Plot beat completion tracked automatically
- Progress visualization shows manuscript status at a glance
- Writers can switch structures without losing custom work
- AI suggests plot beats based on genre and structure

### Deliverables
- ✅ Backend story structure API (14 endpoints)
- ✅ Plot beat database models and migrations
- ✅ Outline sidebar component
- ✅ Create outline modal with genre selection
- ✅ Switch structure modal
- ✅ Plot beat completion tracking UI
- ✅ Progress visualization (dual-metric progress bar)
- ✅ Gantt-style timeline with beat markers (GanttTimelineView)
- ✅ Scene-level guidance integration (SceneDetectionPlugin, BeatContextPanel)
- ✅ AI-powered beat analysis with suggestions
- ✅ Beat Context Panel for writing integration
- ✅ Outline Reference Sidebar

---

## Phase 5: Brainstorming & Ideation Tools
**Timeline:** Months 14-17 (Q4 2026)
**Status:** ✅ 100% Complete (Jan 21, 2026)
**Goal:** AI-powered creative ideation for characters, plots, and settings

### Core Features

#### 5.1 Character Brainstorming
- **AI-Powered Generation:** Generate character ideas based on:
  - Genre (Fantasy, Thriller, Romance, etc.)
  - Role (Protagonist, Antagonist, Mentor, etc.)
  - Archetype preferences
- **Character Attributes:** Name, age, backstory, motivations, flaws, strengths
- **Brandon Sanderson Method:** Character triangle (Desire, Fear, Flaw)
- **Integration with Codex:** Save generated characters directly to entity database

#### 5.2 Plot Ideation
- **Conflict Generation:** Central conflicts based on genre and story structure
- **Plot Twist Suggestions:** Unexpected turns based on current plot
- **Scene Ideas:** "What happens next?" based on current chapter context
- **Subplot Weaving:** Secondary plot threads that complement main story

#### 5.3 Location/Setting Brainstorming
- **Setting Generation:** Detailed location descriptions with atmosphere
- **Worldbuilding Elements:** Culture, history, geography, magic systems
- **Location Relationships:** How settings connect to plot and characters

#### 5.4 Idea Management
- **Brainstorm Sessions:** Save and organize ideation sessions
- **Idea Cards:** Visual representation of generated ideas
- **Refinement Loop:** Iteratively improve ideas with AI
- **Idea Integration:** One-click add to Codex, outline, or timeline

#### 5.5 Mind Mapping (Future)
- Visual connection of ideas
- Branching exploration of concepts
- Export as image or structured data

### Technical Approach
- **Backend:** Brainstorm session models, idea generation API using Claude
- **Frontend:** Brainstorming modal, idea cards, integration panels
- **AI Prompts:** Structured prompts for different idea types
- **Session Management:** Save/load brainstorm sessions

### Success Criteria
- Writers can generate 5+ character ideas in <60 seconds
- Plot twist suggestions feel relevant to current story
- Generated ideas integrate seamlessly with Codex
- Session history allows revisiting previous ideation
- 80% of generated ideas rated "useful" by writers

### Deliverables
- ✅ Backend character generation API
- ✅ Brainstorm session database models
- ✅ Brainstorming modal (main container)
- ✅ Character generation form and results
- ✅ Idea card display components
- ✅ Idea integration with Codex
- ✅ Multi-type brainstorming (plot, location, conflict, scene)
- ✅ Plot generation API with twists and subplots
- ✅ Location generation API with worldbuilding
- ✅ Conflict generation API (internal, interpersonal, external, societal)
- ✅ Scene generation API with beat context
- ✅ Mind mapping tool (MindMapCanvas)
- ✅ Character development worksheets (full/quick/interview)
- ✅ AI entity expansion (deepen, expand, connect)
- ✅ Session history management
- ✅ Idea refinement loop
- ✅ Manuscript context auto-loading

---

## Phase 6: Timeline Orchestrator (Advanced)
**Timeline:** Months 18-20 (Q1 2027)
**Status:** ✅ 100% Complete (Jan 21, 2026)
**Goal:** Chronological consistency validation with teaching moments

### Core Features

#### 6.1 Timeline Event Tracking
- **Event Database:** All story events with timestamps
- **Character Location Tracking:** Where each character is at each event
- **Dependency Management:** Events that must occur before others
- **Narrative Importance Scoring:** Weight events by story significance

#### 6.2 Validation System (5 Validators)
- **Impossible Travel Detector:** Flag when characters can't physically travel between locations in time
- **Dependency Violation Checker:** Ensure prerequisite events occur first
- **Character Presence Validator:** Detect when character is in two places at once
- **Timing Gap Analyzer:** Identify suspicious time gaps in character journeys
- **Temporal Paradox Detector:** Catch logical contradictions in timeline

#### 6.3 Travel Speed Profiles
- Customizable movement speeds (walking, horse, carriage, ship, teleportation)
- Location distance management (city-to-city travel times)
- Genre-specific defaults (fantasy vs. sci-fi vs. contemporary)

#### 6.4 Teaching Moments
- **Educational Explanations:** Why timeline issues matter for reader immersion
- **Fix Suggestions:** How to resolve detected issues (add travel time, adjust dates)
- **Examples:** Real-world author mistakes and solutions
- **Progressive Disclosure:** Start simple, reveal complexity as needed

#### 6.5 Visualization
- Timeline view with event cards
- Character journey maps
- Gantt chart with plot beat markers
- Issues panel with severity filtering (Critical, Warning, Info)

### Technical Approach
- **Backend:** Timeline event models, validation service, travel speed profiles
- **Frontend:** Timeline components, event forms, teaching panel, visualization
- **Validation Engine:** Five separate validators with customizable thresholds
- **Teaching System:** Context-aware explanations tied to specific issues

### Success Criteria
- Detect 95% of impossible travel scenarios
- Zero false positives for valid timelines
- Teaching moments rated "helpful" by 80% of users
- Writers can validate 200+ event timelines in <3 seconds
- Integration with plot beats shows story structure on timeline

### Deliverables
- ✅ Backend timeline orchestrator API
- ✅ 5 core validators (travel, dependency, presence, gap, paradox)
- ✅ Travel speed profiles and location distances
- ✅ Timeline visualization components
- ✅ Event cards and event forms
- ✅ Issues panel with severity filtering
- ✅ Teaching moments panel
- ✅ Performance optimization (query optimization, virtualization)
- ✅ Gantt chart view with plot beat integration (GanttTimelineView)
- ✅ Character journey visualizations (CharacterJourneySwimlane)
- ✅ Foreshadowing Tracker (5 types, Chekhov warnings)
- ✅ Character location tracking with journey statistics

---

## Phase 8: Library & World Management
**Timeline:** Added during Phase 5-6 development
**Status:** ✅ 100% Complete (Jan 18, 2026)
**Goal:** Hierarchical organization for multi-book authors and worldbuilders

### Core Features

#### 8.1 World/Series Hierarchy
- **World Model:** Top-level container for a fictional universe
- **Series Model:** Collection of related manuscripts within a world
- **Manuscript Assignment:** Assign manuscripts to series for organization
- **Auto-migration:** Preserves existing data in default "My Library" world

#### 8.2 Entity Scoping
- **Three Scope Levels:** MANUSCRIPT, SERIES, WORLD
- **Scope Inheritance:** World entities visible across all manuscripts
- **Copy to Manuscript:** Clone world entity for local customization
- **Shared Codex:** Characters and locations usable across books

#### 8.3 Library Navigation
- **WorldLibrary Component:** Browse worlds, series, and manuscripts
- **Breadcrumb Navigation:** Library → World → Series → Manuscript
- **Toggle Views:** Switch between Manuscript Library and World Library
- **World Settings:** Genre, themes, and metadata per world

### Technical Approach
- **Backend:** World and Series SQLAlchemy models, entity scope fields
- **Frontend:** WorldLibrary, SeriesExplorer, SharedEntityLibrary components
- **API:** 18 new endpoints for worlds, series, entity scoping
- **Migration:** Auto-creates default world/series for existing users

### Deliverables
- ✅ World and Series database models
- ✅ Entity scope field (MANUSCRIPT/SERIES/WORLD)
- ✅ World CRUD API (4 endpoints)
- ✅ Series CRUD API (6 endpoints)
- ✅ Manuscript assignment to series (3 endpoints)
- ✅ World entity management (5 endpoints)
- ✅ WorldLibrary component (350+ lines)
- ✅ CreateWorldModal component
- ✅ SeriesExplorer component
- ✅ SharedEntityLibrary component
- ✅ Zustand worldStore (350+ lines)
- ✅ Auto-migration for existing data

---

## Phase 7: PLG Features, UX Polish & Viral Mechanics
**Timeline:** Q1-Q2 2027
**Status:** ⏳ Planned
**Goal:** Product-led growth features, Scrivener-like UX, and user-requested enhancements

### Core Features

#### 7.0 Scrivener-like UX Improvements (User Feedback Priority)
Based on user feedback in FEEDBACK.md, these UX improvements are prioritized:

**Text Editor Polish:**
- **Cleaner Toolbar:** Group formatting options into dropdown menus, reduce visual clutter
- **Font Options:** Add 10+ writing-friendly fonts (Georgia, Palatino, Baskerville, Merriweather, Lora)
- **Focus Mode:** Option to hide toolbar entirely during drafting

**Corkboard/Card View:**
- **Card-based Chapter View:** Visual grid of chapter cards (like Scrivener corkboard)
- **Chapter Summaries:** AI-generated or user-entered summaries on cards
- **Drag-and-Drop:** Reorder chapters by dragging cards (already implemented in tree)

**Inline Entity Features:**
- **Entity Hover Descriptions:** Detect entity names in text, show tooltip with Codex info
- **Create Entity from Selection:** Right-click highlighted text to create new entity

**Time Machine Enhancements:**
- **Auto-Generated Commit Messages:** Diff chapters between versions, AI summarizes changes
- **Visual Diff Viewer:** Side-by-side comparison of version changes

#### 7.1 Aesthetic Recap Engine (Viral Sharing)
- **Beautiful Recap Cards:** AI-generated chapter summaries as shareable images
- **Social Media Ready:** Instagram/Twitter-optimized dimensions
- **Customizable Themes:** Fonts, colors, backgrounds
- **Branding:** Subtle "Created with Maxwell" watermark
- **Share Functionality:** One-click share to social platforms

#### 7.2 Narrative Archivist (Real-Time NLP)
- **Background Extraction:** Entity extraction happens automatically as you type
- **Zero Interruption:** No manual "Analyze" button needed
- **Debounced Processing:** Extract entities after 3 seconds of inactivity
- **Notification System:** Subtle toast when new entities detected
- **Confidence Scoring:** Only suggest high-confidence entities (>80%)

#### 7.3 AI Concierge (Guided BYOK Onboarding)
- **Interactive Tutorial:** "Let's enable AI features in 60 seconds"
- **Cost Transparency:** "Chapter recaps cost ~$0.02 each"
- **Model Recommendations:** "For drafting, try Claude Haiku (fastest, cheapest)"
- **First-Time Free:** $1 credit for new users to try AI features
- **Balance Widget:** Always-visible AI balance in header

#### 7.4 Guided Onboarding Flow
- **Welcome Screen:** "What are you writing?" (Genre, length, experience level)
- **Sample Manuscript:** Pre-populated example to explore features
- **Interactive Tooltips:** Progressive feature discovery
- **Achievement System:** Celebrate first chapter, first export, first AI use
- **Tutorial Videos:** Embedded Loom videos for complex features

#### 7.5 Collaboration Features (Beta Reader Workflows)
- **Share Manuscript:** Generate read-only link for beta readers
- **Inline Comments:** Beta readers can leave feedback on specific paragraphs
- **Feedback Dashboard:** Aggregate all comments in one view
- **Revision Tracking:** See which feedback has been addressed
- **Permissions:** Granular control (view, comment, suggest edits)

### Technical Approach
- **Viral Cards:** HTML Canvas API for image generation, meta tags for social sharing
- **Real-Time NLP:** WebSocket connection for live entity extraction, debounced triggers
- **Onboarding:** Interactive tutorial using react-joyride or similar
- **Collaboration:** WebSocket-based real-time comments, permission system

### Success Criteria
- 20% of users share recap cards on social media
- Real-time entity extraction perceived as "magic" by users
- BYOK onboarding completion rate >90%
- 50% of new users complete guided onboarding
- Beta reader workflow used by 30% of active users

### Viral Metrics
- **K-Factor:** 0.3 (each user refers 0.3 new users)
- **Social Shares:** 500+ recap cards shared per month
- **Organic Growth:** 40% of signups from word-of-mouth
- **NPS Score:** 70+ (strong likelihood to recommend)

---

## PLG Features Integration Timeline

### Q1 2026 (Months 1-3): MVP Foundation
- ✅ Launch core writing features
- ✅ Establish local-first architecture
- ✅ Beta Lifetime Deal ($49)

### Q2 2026 (Months 4-6): Codex & AI
- ✅ Entity extraction and Codex
- ✅ BYOK AI integration
- ✅ Fast Coach and Recap Engine

### Q3 2026 (Months 7-9): Story Structure (COMPLETE)
- ✅ Outline engine with plot beats
- ✅ Manuscript creation wizard
- ✅ Progress tracking and visualization
- ✅ Scene-level guidance integration
- ✅ Gantt timeline view

### Q4 2026 (Months 10-12): Brainstorming & Timeline (COMPLETE)
- ✅ Character/plot/location/conflict/scene ideation tools
- ✅ Timeline orchestrator with validation
- ✅ Teaching moments system
- ✅ Mind mapping tool
- ✅ Foreshadowing tracker

### Q1 2026 (Bonus): Library & World Management (COMPLETE)
- ✅ World/Series hierarchy
- ✅ Entity scoping across manuscripts
- ✅ Shared Codex for series

### Q1 2027 (Months 13-15): PLG Mechanics & UX Polish
- ⏳ Aesthetic Recap Engine (viral sharing)
- ⏳ Real-time entity extraction
- ⏳ Guided onboarding flow
- ⏳ Scrivener-like UX improvements (toolbar, fonts, corkboard)
- ⏳ Entity hover descriptions in editor

### Q2 2027 (Months 16-18): Collaboration & Advanced Features
- ⏳ Beta reader workflows
- ⏳ Inline comments and feedback
- ⏳ Multi-user manuscript sharing
- ⏳ Plot hole interaction system
- ⏳ Character consistency checker

---

## Phase 9: LangChain Agent Framework
**Timeline:** January 2026
**Status:** ✅ Complete
**Goal:** Multi-agent AI writing assistant with teaching-first feedback

### Architecture
- **Hierarchical Context System:** 4-level context (Author → World → Series → Manuscript)
- **Agent Base Framework:** `BaseMaxwellAgent` class with tool management and cost tracking
- **LLM Service Abstraction:** Unified interface for OpenAI, Anthropic, OpenRouter, and Local LLM
- **Author Learning System:** Tracks suggestion acceptance/rejection to personalize feedback

### Specialized Agents (6 total)
1. **ContinuityAgent:** Character facts, timeline consistency, world rules
2. **StyleAgent:** Prose quality, show vs tell, pacing, word choice
3. **StructureAgent:** Beat alignment, story progression, scene goals
4. **VoiceAgent:** Dialogue authenticity, character voice consistency
5. **ConsistencyAgent:** Dedicated consistency checking (real-time + full scan modes)
6. **ResearchAgent:** Worldbuilding generation and topic research

### Smart Coach
- **SmartCoachAgent:** Conversational writing coach with session-based memory
- **Tool-Augmented Responses:** Queries Codex, Timeline, Outline, Manuscript
- **Cost Tracking:** Per-session and per-message cost display
- **Frontend Panel:** SmartCoachPanel component with chat UI

### Agent Tools (17 tools)
- Codex tools: query_entities, query_character_profile, query_relationships, search_entities
- Timeline tools: query_timeline, query_character_locations
- Outline tools: query_outline, query_plot_beats
- Manuscript tools: query_chapters, query_chapter_content, search_manuscript
- World tools: query_world_settings, query_world_rules
- Series tools: query_series_context, query_cross_book_entities
- Author tools: query_author_profile, query_feedback_history

### API Endpoints (15 endpoints)
- Writing Assistant: `/analyze`, `/quick-check`, `/feedback`, `/insights`, `/history`, `/analysis`, `/types`
- Smart Coach: `/coach/session`, `/coach/chat`, `/coach/sessions`, `/coach/session/{id}`, `/coach/archive`, `/coach/title`
- Consistency: `/consistency/check`, `/consistency/full-scan`
- Research: `/research/worldbuilding`, `/research/topic`, `/research/categories`

### Database Models
- `AgentAnalysis` - Stores agent results
- `CoachSession` / `CoachMessage` - Conversational coaching
- `AuthorLearning` - Author preference tracking
- `SuggestionFeedback` - Learning from user responses

### Files Created
- `backend/app/agents/` - 20+ new files
- `backend/app/services/llm_service.py`, `local_llm_service.py`, `author_learning_service.py`
- `frontend/src/stores/agentStore.ts`
- `frontend/src/components/Coach/SmartCoachPanel.tsx`
- `frontend/src/lib/api.ts` - agentApi additions

---

## Phase 9.5: Maxwell Unified Architecture
**Timeline:** February 2026
**Status:** ✅ Core Complete | ⏳ Polish Remaining
**Goal:** Maxwell presents as ONE cohesive entity, not a collection of disconnected tools

### Completed ✅

#### Maxwell Unified Entry Point
- `MaxwellUnified` class as primary interface for all AI interactions
- Single `chat()` method that auto-routes to specialists when needed
- `analyze()` for full multi-agent analysis with synthesis
- `quick_check()` for focused single-agent checks
- `explain()` for writing concept explanations

#### Supervisor Agent (Intelligent Routing)
- `SupervisorAgent` determines which specialists to invoke
- Fast keyword-based routing for common patterns (no LLM needed)
- LLM fallback for complex/ambiguous queries
- `RouteDecision` with agents, intent, reasoning, confidence

#### Maxwell Synthesizer (Unified Voice)
- `MaxwellSynthesizer` transforms multi-agent output into Maxwell's voice
- "I noticed..." not "The Style Agent found..."
- Prioritizes by impact (plot > continuity > style)
- Celebrates strengths before critiquing
- Tone options: encouraging, direct, teaching, celebratory

#### Smart Coach Integration
- `SmartCoachAgent` now routes to specialized agents automatically
- When user asks "Is this working?" with selected text → agents consulted
- Session-based memory preserved while adding agent analysis
- Responses synthesized into natural Maxwell voice

#### API Endpoints (4 new)
- `POST /api/agents/maxwell/chat` - Primary chat interface (auto-routes)
- `POST /api/agents/maxwell/analyze` - Full synthesized analysis
- `POST /api/agents/maxwell/quick-check` - Single-agent focused check
- `POST /api/agents/maxwell/explain` - Writing concept explanations

#### Frontend Updates
- Maxwell types in `api.ts` (MaxwellResponse, SynthesizedFeedback)
- Agent store with Maxwell state management
- API methods for all Maxwell endpoints

#### Phase A: UI Integration ✅
- `MaxwellPanel.tsx` - Unified panel with Chat and Feedback tabs
- `useMaxwell` hook - Easy integration for any component
- App.tsx integration with overlay panel
- EditorToolbar "✨ Maxwell" button
- Keyboard shortcut (Cmd/Ctrl+M) to toggle panel
- Selected text detection for context-aware analysis
- Quick action buttons: Full Analysis, Style, Dialogue, Continuity
- FeedbackView displays priorities, highlights, teaching moments

### Remaining Work ⏳

#### Phase B: Conversation Memory (Priority: Medium)
- [ ] Persistent Maxwell conversation history (separate from Coach sessions)
- [ ] Context awareness across sessions (remembers previous feedback)
- [ ] "You mentioned before..." references to prior conversations

#### Phase C: Cross-Agent Reasoning (Priority: Medium)
- [ ] When agents disagree, Maxwell mediates
- [ ] "This action feels out of character, but serves your plot. Here's how to bridge..."
- [ ] Unified "story health" assessment combining all agent perspectives

#### Phase D: Proactive Suggestions (Priority: Low)
- [ ] Background analysis while writing (opt-in)
- [ ] Gentle nudges: "I noticed 3 potential issues in Chapter 5..."
- [ ] Weekly writing insights email

#### Phase E: Voice Customization (Priority: Low)
- [ ] User preference for Maxwell's tone (formal/casual/encouraging/direct)
- [ ] Adjust feedback depth (brief/standard/comprehensive)
- [ ] "Teaching mode" toggle for educational explanations

---

## Success Metrics by Phase

| Phase | Users | Revenue | Retention (6mo) | NPS | Key Metric | Status |
|-------|-------|---------|----------------|-----|------------|--------|
| **Phase 1** | 100 | $4,900 | 60% | 50 | Manuscripts created | ✅ Complete |
| **Phase 2** | 500 | $25,000 | 70% | 60 | Entities extracted | ✅ Complete |
| **Phase 3** | 2,000 | $99,000 | 75% | 65 | AI usage rate | ✅ Complete |
| **Phase 4-6** | 5,000 | $250,000 | 80% | 70 | Completion rate | ✅ Complete |
| **Phase 8** | - | - | - | - | World/Series usage | ✅ Complete |
| **Phase 9** | - | - | - | - | Agent framework | ✅ Complete |
| **Phase 7** | 15,000 | $750,000 | 85% | 75 | Viral coefficient | ⏳ Planned |

**Target by End of 2027:**
- 15,000+ active users
- $750k ARR
- 85% retention after 6 months
- NPS score 75+
- Viral K-factor 0.3+

---

## Critical Path Dependencies

### Phase 4 depends on:
- ✅ Chapter database schema (Phase 1)
- ✅ AI integration for beat suggestions (Phase 3)
- ✅ Lexical editor integration (Phase 1)

### Phase 5 depends on:
- ✅ Entity extraction system (Phase 2)
- ✅ AI integration for idea generation (Phase 3)
- ✅ Story structure templates (Phase 4)

### Phase 6 depends on:
- ✅ Entity tracking (Phase 2)
- ✅ Chapter structure (Phase 1)
- ✅ Plot beats for timeline markers (Phase 4)

### Phase 8 depends on:
- ✅ Entity system (Phase 2)
- ✅ Manuscript management (Phase 1)

### Phase 7 depends on:
- ✅ AI integration infrastructure (Phase 3)
- ✅ Entity extraction (Phase 2)
- ✅ All core features stable and polished (Phases 1-6, 8)

**Key Insight:** Phases 1-3 are foundational; Phases 4-8 build on top. Phase 7 is PLG layer.

---

## Risk Mitigation

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Timeline validation performance slow | Medium | High | Optimize validation algorithms, cache results, background processing |
| AI costs too high for users | Low | High | BYOK model eliminates markup, user controls costs |
| Real-time NLP interrupts writing | Medium | Medium | Debounced extraction, confidence thresholds, user can disable |
| Database size grows too large | Low | Medium | SQLite handles 100GB+, periodic cleanup, export/archive old projects |

### Product Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Feature complexity overwhelms users | High | High | Progressive disclosure, guided onboarding, tooltips |
| Users don't understand BYOK | Medium | Medium | AI Concierge tutorial, pre-funded $1 credit |
| Story structures feel restrictive | Medium | Medium | Offer freeform mode, custom templates, easy switching |
| Timeline validation false positives | Medium | High | Tunable thresholds, manual override, teaching moments explain why |

### Market Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Scrivener releases major update | Low | Medium | Focus on AI features Scrivener can't match |
| Sudowrite lowers prices | Medium | Medium | BYOK model is always cheaper (zero markup) |
| Saturation of AI writing tools | High | Low | Maxwell is IDE-first, not AI-first; unique Codex/Timeline |

---

## Success Criteria: The Full Creation Engine

**When Maxwell becomes indispensable:**
1. ✅ Writers can brainstorm ideas → AI helps generate options
2. ✅ Writers can outline → AI suggests plot beats based on proven structures
3. ✅ Writers can draft → Real-time structure guidance shows current beat
4. ✅ Writers can revise → Consistency checking across entire manuscript (Codex + Timeline)
5. ✅ Writers can finish → Export to DOCX/PDF, share with beta readers, publish

**Competitive Moat:**
- **Scrivener** lacks AI and Codex intelligence
- **Sudowrite** lacks structure and organization features
- **Plottr** lacks full writing environment and AI
- **Maxwell** combines all three: IDE + Intelligence + Structure

**Vision Metrics:**
- Time from idea → first draft: **30% faster** than industry average
- Manuscript completion rate: **3x industry average** (~30% vs. 10%)
- User retention: **80%+ after 6 months**
- NPS Score: **70+** (strong likelihood to recommend)
- Viral K-Factor: **0.3+** (sustainable organic growth)

---

## Research Resources

### Story Structure
- KM Weiland: "Structuring Your Novel"
- Blake Snyder: "Save the Cat"
- Christopher Vogler: "The Writer's Journey"
- Shawn Coyne: "The Story Grid"

### Brainstorming & Craft
- Brandon Sanderson: BYU Creative Writing Lectures (YouTube)
- Brandon Sanderson: "Sanderson's Laws of Magic"
- James Scott Bell: "Plot & Structure"
- Donald Maass: "The Emotional Craft of Fiction"

### Worldbuilding
- Brandon Sanderson: Worldbuilding Lectures
- Timothy Hickson: "On Writing and Worldbuilding"
- r/worldbuilding community resources

### Competitor Analysis
- **Sudowrite:** AI creative assistant patterns, pricing model
- **NovelAI:** AI storytelling UX, subscription structure
- **Plottr:** Outline/timeline visualization, board views
- **Campfire:** World-building tools, relationship graphs
- **Scrivener:** Binder/corkboard UX, organizational paradigms

---

**Last Updated:** January 25, 2026
**Next Review:** End of Phase 7 (Q2 2027)
**Document Owner:** Implementation Team

**Related Documentation:**
- Current progress and metrics: [PROGRESS.md](./PROGRESS.md)
- Architecture and development standards: [CLAUDE.md](./CLAUDE.md)
- Feature documentation: [FEATURES.md](./FEATURES.md)
- Future enhancements: [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md)
- User feedback tracking: [FEEDBACK.md](./FEEDBACK.md)
- Growth strategy: [PLG_STRATEGY.md](./PLG_STRATEGY.md)
- Architectural decisions: [docs/ARCHITECTURE_DECISIONS.md](./docs/ARCHITECTURE_DECISIONS.md)
