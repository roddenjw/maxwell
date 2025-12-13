# Integrated Agent Architecture for Maxwell IDE

**Last Updated**: 2025-12-13
**Status**: Consolidated Multi-Agent + Fast Coach Design

---

## Overview

Maxwell IDE uses a **three-tier intelligence system**:

1. **Fast Coach** (Python - Real-time) - Instant feedback as you type
2. **Specialist Agents** (LangChain - On-demand) - Deep domain expertise
3. **Supervisor Agent** (LangChain - Coordinator) - Routes and synthesizes

This combines the best of:
- **MULTI_AGENT_PLAN.md** → 5 specialized LangChain agents
- **COACH_ARCHITECTURE.md** → Python real-time analysis
- **LANGCHAIN_UPGRADE.md** → Stateful learning system

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              USER TYPES TEXT IN EDITOR                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
┌───▼────────────┐   ┌─────────▼──────────┐
│  TIER 1:       │   │   TIER 2 & 3:      │
│  FAST COACH    │   │   USER ASKS        │
│  (Automatic)   │   │   QUESTION         │
└───┬────────────┘   └─────────┬──────────┘
    │                          │
    │ Python (< 100ms)         │ LangChain (5-10s)
    │ - Style                  │
    │ - Words                  │  ┌────────────────────┐
    │ - Consistency            │  │ SUPERVISOR AGENT   │
    │ - Pacing                 │  │ (Routes queries)   │
    │                          │  └────────┬───────────┘
┌───▼────────────┐             │           │
│ Inline         │             │  ┌────────┴────────┬────────┬────────┐
│ Highlights     │             │  │                 │        │        │
│ (underlines)   │             │  ▼                 ▼        ▼        ▼
└────────────────┘             │ ┌──────────┐ ┌────────┐ ┌──────┐ ┌───────┐
                               │ │Character │ │  Plot  │ │Craft │ │ World │
                               │ │  Agent   │ │ Agent  │ │Agent │ │ Agent │
                               │ └────┬─────┘ └───┬────┘ └──┬───┘ └───┬───┘
                               │      │           │         │         │
                               │      └───────────┴─────────┴─────────┘
                               │                  │
                               │      ┌───────────▼───────────┐
                               │      │  Synthesized Feedback │
                               └─────→│  (Side Panel)         │
                                      └───────────────────────┘
```

---

## Tier 1: Fast Coach (Python - Real-time)

**When**: Always active, 500ms after typing stops
**How**: Python rule-based + statistical analysis
**Where**: Inline highlights in editor

### Services (from COACH_ARCHITECTURE.md)

1. **Style Analyzer** - Sentence variance, readability, passive voice
2. **Word Analyzer** - Weak words, repetition, clichés
3. **Consistency Checker** - Character attributes vs Codex
4. **Pacing Analyzer** - Tension metrics, dialogue ratio

**Output**: Yellow/orange/purple underlines with hover tooltips

**Example**:
```
"She felt really sad"
 ^^^^ ^^^^^^
 │    └─ WEAK_WORD (orange)
 └─ SHOW_NOT_TELL (purple)
```

---

## Tier 2: Specialist Agents (LangChain - On-demand)

**When**: User clicks "Get Feedback" or asks a question
**How**: LangChain agents with tools and expertise
**Where**: Side panel with detailed analysis

### The Five Specialists (from MULTI_AGENT_PLAN.md)

#### 1. Character Development Agent ⭐
**Expertise**: OCEAN personality model, dialogue, arcs, motivations

**Tools**:
- `checkDialogueConsistency()` - Voice matching
- `analyzeCharacterBehavior()` - Actions vs personality
- `validateArcProgression()` - Arc milestones
- `analyzeRelationshipEvolution()` - Relationship tracking

**Example**:
```
User: "Does Sophia's attack in Chapter 12 make sense?"

Character Agent:
"INCONSISTENCY: Sophia has high agreeableness (0.8) and low
neuroticism (0.2). Violent attack contradicts this UNLESS:
1. Add breaking point scene showing her limits
2. Reframe as defensive (not aggressive)
3. Update personality profile to include situational aggression"
```

---

#### 2. Plot Integrity Agent ⭐
**Expertise**: Plot holes, causality, timeline, unresolved threads

**Tools**:
- `detectPlotHoles()` - Contradictions
- `checkCausality()` - Cause-and-effect
- `verifyTimeline()` - Temporal consistency
- `findUnresolvedThreads()` - Dropped plot threads

**Example**:
```
User: "Does my locked door subplot work?"

Plot Agent:
"UNRESOLVED THREAD:
- Chapter 3: Door locked, no key
- Chapter 8: Character opens door with found key
- Chapter 15: 'That locked door we couldn't open'

ISSUE: Chapter 15 contradicts Chapter 8 resolution.
FIX: Either (a) remove Ch.15 reference, or (b) lock different door"
```

---

#### 3. Craft & Style Agent ⭐
**Expertise**: Pacing, themes, dialogue quality, prose style

**Tools**:
- `analyzePacing()` - Tension curves
- `trackThemes()` - Thematic consistency
- `evaluateDialogueNaturalness()` - Dialogue quality
- `analyzeProseStyle()` - Show vs tell, active voice

**Example**:
```
User: "Chapters 8-10 feel slow. Are they necessary?"

Craft Agent:
"PACING CONCERN:
- 45 pages, low tension (2.3/10)
- Follows climax (9.0/10) → breathing room is good
- BUT: Only 15% advances plot

RECOMMENDATION:
- Keep introspection (character development)
- Trim descriptions 20-30%
- Add subplot tension
- Target: 25-30 pages (still breathing room, better paced)"
```

---

#### 4. World Building Agent
**Expertise**: Magic systems, lore, geography, cultural rules

**Tools**:
- `validateLore()` - World facts
- `checkMagicSystemConsistency()` - Rule consistency
- `verifyGeography()` - Travel logic
- `validateCulturalRules()` - Cultural consistency

**Example**:
```
User: "Did I break my magic system?"

World Agent:
"MAGIC INCONSISTENCY:
- Established: 3-hour meditation to recharge
- Scene 2: Wizard meditates 30 min, casts again

OPTIONS:
1. Extend meditation to 3 hours
2. Establish desperate situations = shorter recharge (health cost?)
3. Introduce second magic source (different rules)"
```

---

## Tier 3: Supervisor Agent (Coordinator)

**Role**: Understand user intent, route to specialists, synthesize feedback

**Process**:
```
1. Interpret user question
2. Identify which specialist(s) needed
3. Call specialists in parallel
4. Synthesize into cohesive response
5. Prioritize by story impact
```

**Example**:
```
User: "My character does something that doesn't fit her personality
       but it's important for the plot. How do I fix this?"

Supervisor:
"This requires TWO agents:
1. Character Agent - check personality fit
2. Plot Agent - verify plot necessity
Then synthesize solution"

Character Agent: "Inconsistency with agreeableness"
Plot Agent: "Action necessary for climax setup"

Supervisor Synthesis:
"SOLUTION: Add breaking point scene that:
- Shows character's limits (satisfies Character Agent)
- Motivates the required action (satisfies Plot Agent)
- Makes arc more complex (bonus!)"
```

---

## Integration: How They Work Together

### Scenario 1: User is Writing (Automatic)

```
USER TYPES
    ↓
Fast Coach (500ms)
    ├─→ Style issues → Inline yellow underlines
    ├─→ Weak words → Inline orange highlights
    ├─→ Consistency errors → Inline purple wavy
    └─→ Pacing metrics → Stored for specialists
```

**No interruption, no API calls, instant feedback**

---

### Scenario 2: User Asks Question (Interactive)

```
USER: "Does Chapter 12 work?"
    ↓
Supervisor Agent
    ├─→ Interprets: "work" = pacing + plot + character
    ├─→ Routes to: Craft Agent, Plot Agent, Character Agent
    └─→ Calls specialists in parallel
         │
         ├─→ Craft Agent: "Pacing is good, tension builds well"
         ├─→ Plot Agent: "Climax is earned, causality checks out"
         └─→ Character Agent: "Protagonist arc milestone hit"
              │
              ↓
    Supervisor Synthesis:
    "Chapter 12 is strong:
    ✓ Pacing builds tension (Craft)
    ✓ Plot climax is earned (Plot)
    ✓ Character arc advances (Character)

    One minor note: Dialogue for Sarah feels slightly
    off-voice in the confrontation scene (line 234)"
```

---

### Scenario 3: Auto-Analysis (Background)

```
USER SAVES MANUSCRIPT
    ↓
Background Analysis (no supervisor overhead)
    ├─→ Character Agent → detectIssues()
    ├─→ Plot Agent → detectIssues()
    ├─→ Craft Agent → detectIssues()
    └─→ World Agent → detectIssues()
         │
         ↓
    Prioritize by severity
         ↓
    Update Issues Panel:
    "⚠️ 3 plot issues, 1 character issue, 2 craft suggestions"
```

---

## Data Flow & Storage

### Fast Coach Reactions
```sql
CREATE TABLE fast_coach_reactions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    suggestion_type TEXT,  -- STYLE, WORD_CHOICE, CONSISTENCY, PACING
    reaction TEXT,          -- ACCEPTED, IGNORED, DISMISSED
    created_at DATETIME
);
```

### Agent Analysis Storage
```sql
CREATE TABLE agent_analysis (
    id TEXT PRIMARY KEY,
    manuscript_id TEXT,
    agent_type TEXT,  -- CHARACTER, PLOT, CRAFT, WORLD
    analysis_data JSON,
    issues_found INTEGER,
    created_at DATETIME
);
```

### Learning Profile (Shared by All)
```sql
CREATE TABLE writing_profile (
    user_id TEXT PRIMARY KEY,
    profile_data JSON,
    -- Includes Fast Coach patterns AND specialist agent learnings
    updated_at DATETIME
);
```

**Profile Structure**:
```json
{
  "fast_coach_patterns": {
    "weak_words_accept_rate": 0.85,
    "passive_voice_ignore_rate": 0.90,
    "top_accepted_type": "WORD_CHOICE"
  },
  "character_agent_patterns": {
    "prefers_deep_character_analysis": true,
    "arc_style": "negative_arc"
  },
  "plot_agent_patterns": {
    "accepts_plot_hole_warnings": 0.95,
    "prefers_tight_causality": true
  },
  "craft_agent_patterns": {
    "target_pacing": "fast_paced_thriller",
    "ignores_theme_suggestions": true
  },
  "style_metrics": {
    "avg_sentence_length": 15.2,
    "lexical_diversity": 0.68
  }
}
```

---

## Token Optimization (from MULTI_AGENT_PLAN.md)

### Context Extraction

**Don't send entire 80K word manuscript to every agent!**

```typescript
class ContextExtractor {
  extractForCharacterAgent(manuscript, characterName) {
    // Only scenes with this character
    // Result: ~3,000 tokens vs 20,000
  }

  extractForPlotAgent(manuscript) {
    // Chapter summaries + major events
    // Result: ~5,000 tokens
  }

  extractForCraftAgent(manuscript, sceneIndex) {
    // Target scene + surrounding context
    // Result: ~4,000 tokens
  }

  extractForWorldAgent(manuscript) {
    // Lore references only
    // Result: ~2,000 tokens
  }
}
```

**Savings**:
- Single agent: ~20,000 tokens per analysis
- 5 specialized agents with context extraction: ~14,000 tokens total
- **Reduction: 30% fewer tokens, 10x cheaper per analysis**

---

## Implementation Roadmap (Integrated)

### Week 7-8: LangChain Foundation
- ✅ LangChain dependencies (already added)
- **Day 1-2**: Supervisor Agent infrastructure
- **Day 3**: Context extraction utilities
- **Day 4-5**: Character Agent (highest priority)

### Week 8-9: Fast Coach + Plot Agent
- **Week 8**: Fast Coach Python services (real-time)
  - Style, Word, Consistency, Pacing analyzers
  - Editor integration
- **Week 9**: Plot Agent (second priority)
  - Plot hole detection
  - Timeline verification
  - Causality checking

### Week 10: Craft Agent + Integration
- **Day 1-3**: Craft Agent
  - Pacing analysis
  - Theme tracking
  - Dialogue quality
- **Day 4-5**: Integration layer
  - Fast Coach feeds data to specialists
  - Specialists learn from Fast Coach patterns

### Week 11: World Agent + Polish
- **Day 1-2**: World Agent (for fantasy/sci-fi)
- **Day 3-5**: UI components
  - Supervisor chat interface
  - Agent feedback panels
  - Issue visualization

---

## Technology Stack

### Frontend
```typescript
// React components
- FastCoachPlugin.tsx (Tier 1 - inline)
- AgentChat.tsx (Tier 2/3 - side panel)
- IssuesPanel.tsx (background analysis)
- AgentFeedbackCard.tsx (shows which agent)
```

### Backend Services

**Fast Coach (Python)**:
```python
app/services/fast_coach/
├── style_analyzer.py
├── word_analyzer.py
├── consistency_checker.py
└── pacing_analyzer.py
```

**Specialist Agents (LangChain)**:
```python
app/services/agents/
├── supervisor_agent.py
├── character_agent.py
├── plot_agent.py
├── craft_agent.py
├── world_agent.py
├── context_extractor.py
└── agent_cache.py
```

### API Routes
```python
app/api/routes/
├── fast_coach.py         # POST /api/fast-coach/analyze
├── agents.py             # POST /api/agents/query (supervisor)
└── analysis.py           # POST /api/analysis/run (background)
```

---

## User Experience Flow

### Writing Flow
```
1. User types: "She felt really sad"
   → Fast Coach (100ms): Underlines "felt" and "really"
   → User hovers: Sees suggestions
   → User continues writing (not interrupted)

2. User finishes scene
   → Clicks "Get Feedback"
   → Modal: "Analyzing scene..." (5-10s)
   → Results stream in:
     "✓ Character voice is consistent (Character Agent)
      ✓ Pacing is good for this chapter (Craft Agent)
      ⚠️ Dialogue tag variety could improve (Craft Agent)"

3. User saves manuscript
   → Background: All agents analyze
   → Toast: "Analysis complete! Found 2 issues"
   → Issues panel updates
```

---

## Cost Analysis

### Fast Coach: $0 (Python, runs locally)

### Specialist Agents (per full manuscript analysis):
- Character Agent: ~3,000 tokens × $0.03/1K = $0.09
- Plot Agent: ~5,000 tokens × $0.03/1K = $0.15
- Craft Agent: ~4,000 tokens × $0.03/1K = $0.12
- World Agent: ~2,000 tokens × $0.03/1K = $0.06
- Supervisor: ~1,000 tokens × $0.03/1K = $0.03

**Total per analysis: ~$0.45**

With caching (1 hour) and smart routing:
- **Average cost per user session: $0.10-0.20**

---

## Success Metrics

### Quality
- [ ] Agent feedback matches professional editor (>80%)
- [ ] Users implement >60% of agent suggestions
- [ ] Character + Plot agents used equally (balanced value)

### Efficiency
- [ ] Fast Coach < 100ms per analysis
- [ ] Specialist agents < 30 seconds
- [ ] Token usage < 15,000 per full analysis
- [ ] Cost per analysis < $0.50

### Engagement
- [ ] Users check Fast Coach feedback >20x per session
- [ ] Users request specialist analysis >5x per manuscript
- [ ] Issue acceptance rate >70%

---

## Summary

**Three-Tier Intelligence**:
1. **Fast Coach** (Python) → Instant, always-on, free
2. **Specialist Agents** (LangChain) → Deep, on-demand, smart
3. **Supervisor** (Coordinator) → Routes and synthesizes

**Integration Points**:
- Fast Coach patterns inform specialist prompts
- Specialists use Fast Coach metrics as context
- All learnings feed into shared WritingProfile
- User reactions teach all systems

**Result**: Best of all worlds
- Instant feedback (Fast Coach)
- Deep expertise (Specialists)
- Continuous learning (Shared profile)
- Cost-effective (Context extraction + caching)

---

**Status**: Architecture consolidated and ready for implementation
**Next Step**: Begin Week 7 - Build Supervisor Agent foundation
