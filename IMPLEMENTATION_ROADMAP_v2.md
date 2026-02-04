# Maxwell Implementation Roadmap v2.0

**Date:** February 4, 2026
**Vision:** Unified Narrative Intelligence System
**Core Principle:** Everything connects through the World Wiki

---

## Executive Summary

This roadmap transforms Maxwell from a **collection of features** into an **integrated narrative intelligence system** where:

1. The **World Wiki** is the single source of truth
2. All analyzers **reference the Wiki** for consistency checking
3. **Character arcs** integrate with outlines
4. **AI auto-populates** with author approval
5. Every feature **works together seamlessly**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            WORLD WIKI                                    │
│                    (Single Source of Truth)                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Characters    Locations    World Rules    Factions    Artifacts  │   │
│  │  + Voice       + History    + Magic        + Relations  + History │   │
│  │  + Arcs        + Culture    + Physics      + Goals      + Powers  │   │
│  │  + Relations   + Secrets    + Social       + Members    + Limits  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│              ┌───────────────┼───────────────┐                          │
│              ▼               ▼               ▼                          │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│     │   CODEX     │  │  OUTLINE    │  │  TIMELINE   │                  │
│     │ (Manuscript │  │ (Structure  │  │  (Events    │                  │
│     │   View)     │  │  + Arcs)    │  │  + Travel)  │                  │
│     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│            │                │                │                          │
└────────────┼────────────────┼────────────────┼──────────────────────────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  CONSISTENCY      │
                    │     ENGINE        │
                    │  ┌─────────────┐  │
                    │  │ Voice       │  │
                    │  │ POV         │  │
                    │  │ Timeline    │  │
                    │  │ World Rules │  │
                    │  │ Arcs        │  │
                    │  │ Foreshadow  │  │
                    │  └─────────────┘  │
                    └─────────▲─────────┘
                              │
                    ┌─────────┴─────────┐
                    │   MAXWELL AGENTS  │
                    │  (Query Wiki for  │
                    │   all decisions)  │
                    └───────────────────┘
```

---

## Phase 7: World Wiki Foundation (Weeks 1-3)

### Goal: Create the interconnected backbone

### 7.1 Wiki Core Infrastructure
**Week 1**

| Task | Description | Effort |
|------|-------------|--------|
| WikiEntry model | Core wiki entry with structured_data + content | M |
| WikiChange model | Approval queue for AI suggestions | S |
| WikiCrossReference model | Links between entries | S |
| WorldRule model | Custom validation rules | M |
| CharacterArc model | Arc tracking with templates | M |
| Database migration | Create all tables | S |
| WikiService | CRUD operations | M |

**Deliverables:**
- `backend/app/models/wiki.py`
- `backend/app/models/character_arc.py`
- `backend/app/models/world_rule.py`
- `backend/app/services/wiki_service.py`
- Database migration

### 7.2 Wiki ↔ Codex Integration
**Week 2**

| Task | Description | Effort |
|------|-------------|--------|
| WikiCodexBridge service | Sync between Codex entities and Wiki entries | M |
| Auto-create wiki entries | Existing entities → Wiki entries | M |
| World-level Codex view | See all entities in Library at World level | M |
| Entity → Wiki link UI | Show wiki connection in entity details | S |
| Wiki → Entity sync | Changes propagate both directions | M |

**Deliverables:**
- `backend/app/services/wiki_codex_bridge.py`
- Updated `backend/app/api/routes/codex.py`
- Updated `frontend/src/components/Codex/EntityDetail.tsx`
- New world-level entity browser in Library

### 7.3 Wiki Browser UI
**Week 3**

| Task | Description | Effort |
|------|-------------|--------|
| WorldWikiBrowser component | Main wiki interface in Library | L |
| WikiEntryEditor component | Rich editor for entries | L |
| WikiEntryCard component | Card display for entries | M |
| WikiSearch component | Search across all entries | M |
| Entry type icons/styling | Visual differentiation | S |
| Cross-reference display | Show linked entries | M |

**Deliverables:**
- `frontend/src/components/Wiki/WorldWikiBrowser.tsx`
- `frontend/src/components/Wiki/WikiEntryEditor.tsx`
- `frontend/src/components/Wiki/WikiEntryCard.tsx`
- `frontend/src/components/Wiki/WikiSearch.tsx`
- Integration with Library view

---

## Phase 8: Character Arc System (Weeks 4-5)

### Goal: Character arcs integrated with outline

### 8.1 Arc Templates & Designer
**Week 4**

| Task | Description | Effort |
|------|-------------|--------|
| Arc template database | 6+ templates (redemption, fall, coming of age, etc.) | M |
| CharacterArcService | Arc CRUD + template application | M |
| ArcTemplateSelector component | Choose template with preview | M |
| CharacterArcDesigner component | Visual arc planning | L |
| Planned arc editor | Author defines intended arc | M |

**Arc Templates:**
1. **Redemption Arc** - Flawed → Transformed → Redeemed
2. **Tragic Fall** - Noble → Corrupted → Destroyed
3. **Coming of Age** - Innocent → Challenged → Mature
4. **Positive Change** - Lie believed → Truth embraced
5. **Flat Arc (Testing)** - Truth known → World changed
6. **Negative Change** - Truth rejected → Lie embraced

**Deliverables:**
- `backend/app/services/character_arc_service.py`
- Arc templates data
- `frontend/src/components/CharacterArc/ArcTemplateSelector.tsx`
- `frontend/src/components/CharacterArc/CharacterArcDesigner.tsx`

### 8.2 Outline Integration
**Week 5**

| Task | Description | Effort |
|------|-------------|--------|
| Arc → Beat mapping | Link arc stages to outline beats | M |
| OutlineCharacterView | Character-centric outline view | L |
| Arc stage annotations | Show arc stage on beat cards | M |
| Arc detection service | Detect actual arc from manuscript | L |
| Planned vs Detected view | Compare intended vs actual | M |
| Arc deviation warnings | Alert when arc goes off-track | M |

**Deliverables:**
- `frontend/src/components/Outline/OutlineCharacterView.tsx`
- Updated `PlotBeatCard.tsx` with arc annotations
- `backend/app/services/arc_detection_service.py`
- `frontend/src/components/CharacterArc/ArcComparisonView.tsx`

---

## Phase 9: World Rules Engine (Weeks 6-7)

### Goal: Custom rule validation for fantasy/sci-fi

### 9.1 Rule Definition System
**Week 6**

| Task | Description | Effort |
|------|-------------|--------|
| WorldRule service | Rule CRUD + validation | M |
| Rule editor UI | Define rules with patterns | L |
| Rule categories | Magic, physics, social, temporal | S |
| Pattern matching engine | Regex + keyword validation | M |
| Exception handling | Define when rules don't apply | M |

**Example Rules:**
- "Magic requires verbal incantation" (flag silent magic)
- "Vampires cannot enter without invitation" (check entry scenes)
- "Faster-than-light travel impossible" (flag FTL mentions)
- "Nobility always uses formal address" (check dialogue formality)

**Deliverables:**
- `backend/app/services/world_rule_service.py`
- `frontend/src/components/Wiki/WorldRuleEditor.tsx`
- Pattern matching engine

### 9.2 Rule Validation Integration
**Week 7**

| Task | Description | Effort |
|------|-------------|--------|
| WikiConsistencyEngine | Central API for all consistency checks | L |
| Timeline → Rules integration | Travel validator uses world rules | M |
| Editor → Rules integration | Real-time rule checking while writing | M |
| Rule violation panel | Show violations with context | M |
| Violation resolution workflow | Mark as fixed/exception | S |

**Deliverables:**
- `backend/app/services/wiki_consistency_engine.py`
- Updated `timeline_service.py` to use wiki rules
- `frontend/src/components/Editor/RuleViolationPanel.tsx`
- Integration with Fast Coach

---

## Phase 10: AI Auto-Population (Weeks 8-9)

### Goal: Wiki that builds itself with author approval

### 10.1 Auto-Population Pipeline
**Week 8**

| Task | Description | Effort |
|------|-------------|--------|
| WikiAutoPopulator service | Analyze manuscripts for wiki content | L |
| Entity extraction → Wiki | Enhanced NLP extraction | M |
| Relationship extraction | Detect relationship changes | M |
| World rule extraction | Find rules in exposition/dialogue | L |
| Location detail extraction | Culture, history, atmosphere | M |

**Extraction Patterns:**
- "In [world], [rule]" → World Rule
- "[Character] is [description]" → Character wiki entry
- "[Location] was known for [history]" → Location history
- "The law states that [rule]" → Social rule

**Deliverables:**
- `backend/app/services/wiki_auto_populator.py`
- Enhanced extraction patterns
- Integration with chapter save

### 10.2 Approval Queue
**Week 9**

| Task | Description | Effort |
|------|-------------|--------|
| WikiChangeQueue UI | Review pending AI changes | L |
| Change diff display | Show old vs new | M |
| AI reasoning display | Why AI suggests this change | M |
| Bulk approve/reject | Handle multiple changes | M |
| Incremental updates | Update wiki on chapter save | M |
| Confidence thresholds | Auto-approve high confidence | S |

**Deliverables:**
- `frontend/src/components/Wiki/WikiChangeQueue.tsx`
- `backend/app/api/routes/wiki_changes.py`
- Notification system for pending changes

---

## Phase 11: Deep Analysis Features (Weeks 10-12)

### Goal: Advanced features powered by Wiki

### 11.1 POV Consistency Checker
**Week 10**

| Task | Description | Effort |
|------|-------------|--------|
| POV detection service | Identify POV per scene | M |
| Head-hopping detection | Multiple POVs in scene | M |
| POV-inappropriate knowledge | Character knows too much | L |
| POV consistency panel | Show issues with fixes | M |
| Wiki POV expectations | Store expected POV per character | S |

**Deliverables:**
- `backend/app/services/pov_consistency_service.py`
- `frontend/src/components/Analysis/POVConsistencyPanel.tsx`
- Integration with Fast Coach

### 11.2 Scene Purpose Analyzer
**Week 11**

| Task | Description | Effort |
|------|-------------|--------|
| Scene purpose classifier | Categorize scene purposes | L |
| Purpose detection patterns | NLP patterns for purposes | M |
| Purposeless scene detection | Flag scenes without clear goal | M |
| Missing purpose types | Genre needs X scene types | M |
| Scene purpose panel | Visualization + suggestions | M |

**Scene Purposes:**
- Character introduction
- Relationship development
- Plot advancement
- World exposition
- Tension building
- Conflict resolution
- Revelation/twist
- Emotional beat

**Deliverables:**
- `backend/app/services/scene_purpose_service.py`
- `frontend/src/components/Analysis/ScenePurposePanel.tsx`

### 11.3 Relationship Evolution Tracker
**Week 12**

| Task | Description | Effort |
|------|-------------|--------|
| Relationship state model | Track relationship changes | M |
| Evolution detection | Detect state changes | L |
| Relationship timeline | Visual evolution | M |
| Unearned changes detection | Flag sudden shifts | M |
| Wiki relationship integration | Store in wiki, validate against | M |

**Deliverables:**
- `backend/app/services/relationship_evolution_service.py`
- `frontend/src/components/Wiki/RelationshipTimeline.tsx`

---

## Phase 12: Pacing & Subplot Features (Weeks 13-14)

### Goal: Complete narrative tracking toolkit

### 12.1 Emotional Beat Mapping
**Week 13**

| Task | Description | Effort |
|------|-------------|--------|
| Emotional beat detection | Classify emotional beats per scene | M |
| Emotional rhythm analysis | Detect patterns and monotony | M |
| Genre emotional templates | Expected beats for genre | M |
| EmotionalBeatMap component | Visual emotional journey | L |
| Emotional gap detection | Missing emotional beats | M |
| Wiki emotional expectations | Store character emotional norms | S |

**Emotional Beat Types:**
- Joy/Triumph
- Fear/Tension
- Sadness/Loss
- Anger/Conflict
- Love/Connection
- Surprise/Revelation
- Hope/Anticipation
- Despair/Defeat

**Extends TensionHeatmap with:**
- Reader emotional experience (not just tension)
- Per-character emotional arcs
- Genre-appropriate emotional rhythm

**Deliverables:**
- `backend/app/services/emotional_beat_service.py`
- `frontend/src/components/Timeline/EmotionalBeatMap.tsx`
- Integration with character arcs

### 12.2 Subplot Tracker
**Week 13-14**

| Task | Description | Effort |
|------|-------------|--------|
| Subplot model | Track subplot threads | M |
| Subplot detection | Identify subplot beginnings | L |
| Subplot presence tracking | Which chapters have which subplots | M |
| Abandoned subplot detection | Flag subplots that disappear | M |
| Unresolved subplot warnings | Alert at story end | M |
| SubplotTracker component | Visual subplot management | L |
| Wiki subplot storage | Store subplots in wiki | S |

**Subplot Tracking:**
- Main plot vs subplots
- Character-specific subplots (romance, rivalry, growth)
- Theme-related subplots
- Mystery/revelation subplots

**Builds on Foreshadowing:**
- Foreshadowing = single setup/payoff
- Subplot = sustained narrative thread

**Deliverables:**
- `backend/app/services/subplot_tracker_service.py`
- `backend/app/models/subplot.py`
- `frontend/src/components/Timeline/SubplotTracker.tsx`

### 12.3 Pacing Optimizer
**Week 14**

| Task | Description | Effort |
|------|-------------|--------|
| Pacing analysis service | Analyze story pacing | M |
| Slow section detection | Heavy description, low dialogue | M |
| Pacing suggestions | Active fix recommendations | L |
| Genre pacing norms | Expected pacing per genre | M |
| Scene merge suggestions | Combine slow scenes | M |
| Tension valley detection | Too long without tension | M |
| PacingOptimizer component | Suggestions with actions | L |

**Pacing Metrics:**
- Scene length variation
- Dialogue-to-description ratio
- Action density
- Tension level changes
- Chapter length consistency

**Active Suggestions:**
- "Consider cutting this scene - unclear purpose"
- "Merge these scenes - both accomplish same goal"
- "Add tension beat here - 3 chapters since last conflict"
- "This section is 80% description - add dialogue"

**Deliverables:**
- `backend/app/services/pacing_optimizer_service.py`
- `frontend/src/components/Analysis/PacingOptimizer.tsx`
- Integration with Scene Purpose Analyzer

---

## Phase 13: Agent Wiki Integration (Weeks 15-16)

### Goal: All agents powered by Wiki

### 13.1 Wiki Agent Tools
**Week 15**

| Task | Description | Effort |
|------|-------------|--------|
| WikiAgentTools | LangChain tools for wiki queries | M |
| Update all agents | Query wiki before responding | L |
| Agent → Wiki suggestions | Agents suggest wiki updates | M |
| Cross-agent wiki sharing | Agents share wiki context | M |

**Wiki Tools:**
- `query_wiki` - Search wiki entries
- `get_character_facts` - All known character info
- `get_world_rules` - Rules for validation
- `check_rule_violation` - Validate text against rules
- `suggest_wiki_update` - Queue update for approval

**Deliverables:**
- `backend/app/agents/tools/wiki_tools.py`
- Updated all agent files to use wiki
- Agent suggestion → approval queue

### 13.2 Unified Analysis Dashboard
**Week 16**

| Task | Description | Effort |
|------|-------------|--------|
| AnalysisDashboard component | Single view of all analyses | L |
| Issue aggregation | Combine all analyzer outputs | M |
| Priority sorting | Most important issues first | M |
| Fix workflow | Resolve issues with wiki updates | M |
| Progress tracking | Issues fixed over time | M |

**Deliverables:**
- `frontend/src/components/Analysis/AnalysisDashboard.tsx`
- Unified issue model
- Integration with all analyzers

---

## Feature Interconnection Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              WORLD WIKI                                  │
│                                  │                                       │
│    ┌────────────────────────────┼─────────────────────────────────┐     │
│    │                            │                                 │     │
│    ▼                            ▼                                 ▼     │
│ ┌──────────┐              ┌──────────┐                     ┌──────────┐│
│ │Characters│◄────────────►│ Outline  │◄───────────────────►│ Timeline ││
│ │+ Voice   │   arc        │+ Beats   │    event            │+ Events  ││
│ │+ Arcs    │   mapping    │+ Scenes  │    linking          │+ Travel  ││
│ └────┬─────┘              └────┬─────┘                     └────┬─────┘│
│      │                         │                                │      │
│      │    ┌────────────────────┼────────────────────────────────┘      │
│      │    │                    │                                       │
│      ▼    ▼                    ▼                                       │
│ ┌─────────────────────────────────────────────────────────────────┐   │
│ │                    CONSISTENCY ENGINE                            │   │
│ │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │   │
│ │  │   Voice    │ │    POV     │ │   Rules    │ │   Arcs     │   │   │
│ │  │ Consistency│ │ Consistency│ │ Validation │ │ Tracking   │   │   │
│ │  └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘   │   │
│ │         │              │              │              │          │   │
│ │         └──────────────┴──────────────┴──────────────┘          │   │
│ │                                 │                                │   │
│ └─────────────────────────────────┼────────────────────────────────┘   │
│                                   │                                     │
│                                   ▼                                     │
│                    ┌──────────────────────────┐                        │
│                    │    MAXWELL AGENTS        │                        │
│                    │  (All query Wiki first)  │                        │
│                    └──────────────────────────┘                        │
│                                   │                                     │
│                                   ▼                                     │
│                    ┌──────────────────────────┐                        │
│                    │  UNIFIED FEEDBACK        │                        │
│                    │  (One coherent voice)    │                        │
│                    └──────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Summary

| Phase | Weeks | Focus | Key Deliverable |
|-------|-------|-------|-----------------|
| 7 | 1-3 | Wiki Foundation | World Wiki + Codex integration |
| 8 | 4-5 | Character Arcs | Arc designer + Outline integration |
| 9 | 6-7 | World Rules | Custom validation rules |
| 10 | 8-9 | Auto-Population | AI suggestions + Approval queue |
| 11 | 10-12 | Deep Analysis | POV + Scene purpose + Relationships |
| 12 | 13-14 | Pacing & Subplots | Emotional beats + Subplot tracker + Pacing optimizer |
| 13 | 15-16 | Agent Integration | Wiki-powered agents + Unified dashboard |

**Total Timeline:** 16 weeks

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Wiki entries per world | 50+ |
| Auto-population accuracy | 70%+ approved |
| Arc completion tracking | 90% accurate |
| Rule violation detection | 85% accurate |
| All analyzers use wiki | 100% |
| User wiki engagement | 5+ edits/session |
| Cross-feature navigation | <2 clicks |

---

## Unique Competitive Advantage

After full implementation, Maxwell will be the **only** writing tool with:

1. **Living World Wiki** - Auto-populating, author-approved knowledge base
2. **Character Arc Tracking** - Planned vs detected with outline integration
3. **Custom World Rules** - Author-defined validation for any genre
4. **Unified Consistency** - All analyzers share one source of truth
5. **Interconnected Analysis** - Voice, POV, arcs, rules work together
6. **AI with Author Control** - Suggestions, not automation

No competitor has attempted this level of integration. Novelcrafter has static Codex. Scrivener has organization. ProWritingAid has analysis. **Only Maxwell connects everything.**

---

## Next Steps

1. **Review and approve plan**
2. **Begin Phase 7.1** - Wiki database models
3. **Parallel:** Update PROGRESS.md with Phase 7-12 roadmap
