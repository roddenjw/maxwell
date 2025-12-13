# LangChain Architecture Upgrade - Summary

**Date**: 2025-12-12
**Status**: Implementation plan updated ✅

---

## What Changed

The original implementation plan used a simple LLM router that selected between local and cloud models. This has been **completely redesigned** to use LangChain with stateful agents that learn and remember.

### Before (Simple Router)
```
User writes text → Send to LLM → Get response → Done
```
- No memory between sessions
- No learning from feedback
- Generic suggestions for everyone
- Manual context gathering

### After (LangChain Agent)
```
User writes text → Agent analyzes with tools → Provides personalized feedback → Learns from reaction → Updates profile
```
- Persistent memory across sessions
- Learns your writing patterns over time
- Personalized to YOUR strengths/weaknesses
- Autonomous tool use (queries Codex, checks consistency, analyzes pacing)

---

## New Epic 3.4: "The Coach"

A **stateful LangChain agent** that becomes your personal writing coach:

### What It Does

1. **Learns Your Patterns**
   - Tracks your sentence length preferences
   - Identifies overused words
   - Recognizes your strengths (e.g., "vivid descriptions")
   - Spots your weaknesses (e.g., "tends to info-dump")

2. **Provides Personalized Feedback**
   - "I notice you tend to rush dialogue scenes - this one feels rushed too"
   - "Great use of sensory details here! That's your strength"
   - "You've used 'just' 15 times in this chapter - more than usual"

3. **Uses Tools Autonomously**
   - **GetEntityInfo**: Checks character details from Codex
   - **GetRecentScenes**: Maintains narrative continuity
   - **SearchSimilarScenes**: Finds style references from your past writing
   - **AnalyzePacing**: Checks tension and pacing automatically
   - **CheckConsistency**: Finds plot holes

4. **Improves Over Time**
   - You rate feedback as "helpful" or "not helpful"
   - Agent learns which advice you accept vs reject
   - Future suggestions adapt to your preferences

### Database Schema

**coaching_history**
```sql
id, user_id, manuscript_id, scene_text, agent_feedback, user_reaction, created_at
```
Stores every coaching interaction for learning.

**writing_profile**
```json
{
  "style_metrics": {
    "avg_sentence_length": 15.2,
    "lexical_diversity": 0.68
  },
  "strengths": ["vivid_descriptions", "natural_dialogue"],
  "weaknesses": ["info_dumping", "passive_voice"],
  "overused_words": {"just": 142, "really": 89},
  "preferences": {"pov": "third_person", "tense": "past"}
}
```
Your learned writing profile that grows over time.

**ChromaDB collection per user**
- Stores semantic memory of past feedback
- Enables "SearchPastFeedback" tool
- Agent can recall similar situations

---

## Architecture Changes

### Epic 3.1: LangChain Foundation (4 days)
**New Tasks:**
- Install LangChain + dependencies
- Create LLM factory (Claude, GPT-4, local Llama)
- Build LangChain tools for Codex access
- Implement streaming handlers

**Code Example:**
```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_openai_tools_agent
from langchain.tools import Tool

# Create LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

# Create tools
tools = [
    Tool(
        name="GetEntityInfo",
        func=get_entity_from_codex,
        description="Look up character/location details"
    ),
    Tool(
        name="AnalyzePacing",
        func=analyze_pacing,
        description="Check scene pacing and tension"
    )
]

# Create agent
agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=system_prompt)
```

### Epic 3.4: The Coach (5 days)
**New Epic - Personalized Learning Agent:**
- Day 1: Database schema for learning & memory
- Days 2-3: WritingCoach class implementation
- Days 4-5: Feedback UI + learning loop

**User Experience:**
1. User selects text in editor
2. Clicks "Get Feedback" in Coach panel
3. Agent analyzes with full context:
   - Checks Codex for consistency
   - Compares pacing to recent scenes
   - References user's writing profile
   - Searches past feedback for similar situations
4. Provides specific, personalized feedback
5. User rates it helpful/not helpful
6. Profile updates for next time

---

## Updated Timeline

**Old Plan**: 12 weeks
**New Plan**: 13 weeks (+ 1 week for learning coach)

### Weeks 7-11: Generative Layer (was Weeks 7-10)
- **Week 7**: LangChain setup + LLM wrappers + Codex tools
- **Week 8**: GraphRAG implementation + embedding system
- **Week 9**: Beat expansion + style matching
- **Week 10**: The Coach - Database + agent implementation ⭐ NEW
- **Week 11**: The Coach UI + feedback learning loop ⭐ NEW

### Phase 4: Weeks 12-13 (was Weeks 11-12)
- Week 12: Pacing graph + consistency linter + testing
- Week 13: Electron packaging + deployment

---

## Dependencies Added

```bash
# requirements.txt additions
langchain==0.1.0
langchain-anthropic==0.1.0
langchain-community==0.0.13
langchain-openai==0.0.5
llama-cpp-python==0.2.0
```

---

## Why This Matters

### The Problem with Simple LLMs
Generic AI writing tools give the same advice to everyone:
- "Show, don't tell"
- "Use active voice"
- "Vary sentence length"

This is like having a textbook as your coach.

### The Power of Stateful Agents
A LangChain agent that learns YOU:
- Knows you already vary sentence length well
- Knows you struggle with info-dumping specifically
- Remembers you rejected advice about dialogue tags (you prefer minimal)
- Catches when you use "just" too much (it knows your pattern)

**This is like having a coach who's worked with you for months.**

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agent reliability (tool failures) | Error handling, fallback to simple prompts, verbose logging |
| Token costs (Claude API) | Smart routing to local models, query caching, spending limits |
| Memory degradation over time | Periodic validation, manual profile correction |
| Privacy (sending text to cloud) | Local-only mode option, transparent opt-in |

---

## Next Steps

1. ✅ **Updated IMPLEMENTATION_PLAN.md** (complete)
2. Continue with Phase 1: Backend infrastructure
3. Weeks 2-6: Build foundation (versioning, Codex, database)
4. Week 7: Begin LangChain integration
5. Week 10: Build The Coach

---

## Key Differences Summary

| Feature | Old Plan | New Plan (LangChain) |
|---------|----------|---------------------|
| Memory | None | Persistent across sessions |
| Personalization | Generic | Learns YOUR patterns |
| Tool Use | Manual context | Agent uses tools autonomously |
| Feedback Quality | Static | Improves over time |
| Complexity | Simple | Stateful agent with memory |
| Timeline | 12 weeks | 13 weeks |
| Effort | 48.5 days | 53.5 days |

---

**The Bottom Line**: For 1 extra week of development, you get an AI coach that actually knows you and gets better over time, instead of a generic suggestion engine.
