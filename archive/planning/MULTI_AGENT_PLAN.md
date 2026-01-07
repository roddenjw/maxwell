# Writing Helper Platform - LangChain Agent Architecture

**Created**: December 13, 2025  
**Status**: Reference Document for Implementation  
**Related**: Epic 4 (Agentic AI Integration), Novel Skeleton Generator

---

## Overview

This document outlines the agent-based architecture for the Writing Helper Platform using LangChain. Rather than a single monolithic AI agent, we use a team of specialized agents, each focused on a specific aspect of narrative analysis and feedback.

### Architecture Philosophy

**Single Agent Approach:**
- ❌ Lacks deep expertise in any single domain
- ❌ Inefficient token usage (sees entire manuscript for every query)
- ❌ Surface-level feedback across all areas
- ❌ Poor user experience (generic responses)

**Multi-Agent Approach (Recommended):**
- ✅ Deep, specialized expertise in each domain
- ✅ Efficient token usage (each agent sees only relevant context)
- ✅ Higher quality feedback
- ✅ Better user experience (targeted, actionable advice)
- ✅ Scalable (easy to add new agents)
- ✅ Matches how professional editors actually work

---

## Agent Architecture

### High-Level Structure

```
User Input
    ↓
┌─────────────────────────┐
│ Supervisor Agent        │ (Understands user intent, routes queries)
└────────┬────────────────┘
         ↓
    ┌────┴────┬────────┬───────────┐
    ↓         ↓        ↓           ↓
┌─────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│ Character│ │ Plot │ │ Craft  │ │  World  │
│ Agent    │ │ Agent│ │ Agent  │ │ Agent   │
└────┬────┘ └──┬───┘ └───┬────┘ └────┬────┘
     │         │         │           │
     └─────────┴─────────┴───────────┘
             ↓
    ┌──────────────────────┐
    │ Synthesized Feedback │
    │ (Prioritized, Acted) │
    └──────────────────────┘
```

---

## The Five Agents

### 1. Character Development Agent ⭐ (Priority: Highest)

**Purpose**: Ensure character consistency, believability, and arc progression.

**Responsibilities:**
- Analyze character behavior against personality profiles (OCEAN model)
- Check dialogue consistency with established voice
- Track character arc progression
- Validate character motivations across scenes
- Monitor relationship evolution

**Tools Available:**
- `checkDialogueConsistency()` - Compare dialogue to voice profile
- `analyzeCharacterBehavior()` - Check actions against personality
- `validateArcProgression()` - Ensure arc milestones are hit
- `analyzRelationshipEvolution()` - Track relationship changes
- `extractCharacterMotivations()` - Identify and validate motivations

**Example Query:**
```
Character: Sophia (high agreeableness: 0.8, low neuroticism: 0.2)
Scene: Chapter 12 - Sophia violently attacks a guard
Question: Is this consistent?

Agent Response:
"INCONSISTENCY DETECTED:
- High agreeableness + low neuroticism suggests Sophia avoids conflict
- Violent attack contradicts established personality
- UNLESS there's a breaking point moment preceding this

RECOMMENDED ACTIONS:
1. Add catalyst scene showing Sophia's limits
2. Reframe attack as defensive (not aggressive)
3. Adjust personality profile to include situational aggression
"
```

**System Prompt Template:**
```
You are a character psychologist and analyst. Your expertise is in:
- The OCEAN personality model (Big Five traits)
- Character motivation hierarchies (Maslow's needs)
- Dialogue authenticity and voice consistency
- Character arc progression (positive/negative/flat arcs)
- Relationship dynamics and evolution

When analyzing a character:
1. Reference their established personality profile
2. Check if actions align with their motivations
3. Verify dialogue matches their voice
4. Ensure arc follows their established trajectory
5. Flag inconsistencies with specific examples

Always explain your reasoning and provide specific textual evidence.
```

---

### 2. Plot Integrity Agent ⭐ (Priority: High)

**Purpose**: Detect plot holes, logical inconsistencies, and causality gaps.

**Responsibilities:**
- Identify plot holes and logical contradictions
- Check causality (do events have clear causes?)
- Verify timeline consistency
- Track unresolved plot threads
- Validate cause-and-effect chains

**Tools Available:**
- `detectPlotHoles()` - Find contradictions and gaps
- `checkCausality()` - Verify cause-and-effect relationships
- `verifyTimeline()` - Check for temporal inconsistencies
- `extractEvents()` - Build event chain from manuscript
- `findUnresolvedThreads()` - Identify plot threads not resolved

**Example Query:**
```
Chapter 3: Locked door has no key
Chapter 8: Character opens door with found key
Chapter 15: Character mentions "that locked door we couldn't open"

Agent Response:
"UNRESOLVED THREAD DETECTED:
- Chapter 15 reference contradicts Chapter 8 resolution
- Reader will be confused about door's status
- Either: (a) Remove Chapter 15 reference, or
         (b) Lock a DIFFERENT door in Chapter 15"
```

**System Prompt Template:**
```
You are a plot architect and story engineer. Your expertise is in:
- Three-act structure and plot point placement
- Cause-and-effect relationships (causality)
- Timeline consistency and temporal logic
- Subplot tracking and resolution
- Narrative payoff and callback fulfillment

When analyzing a plot:
1. Map out all major events and their causes
2. Check for causality gaps (effects without causes)
3. Verify timeline doesn't contradict itself
4. Track introduced plot threads to their resolution
5. Check that character goals have clear obstacles

Flag any inconsistencies with scene references and specific line numbers.
```

---

### 3. Craft & Style Agent ⭐ (Priority: Medium-High)

**Purpose**: Improve how the story is told (pacing, prose, themes, dialogue quality).

**Responsibilities:**
- Analyze story pacing (tension curves, breathing room)
- Track thematic elements and consistency
- Evaluate dialogue quality and distinctiveness
- Assess prose style (show vs. tell, active voice, etc.)
- Recommend craft improvements

**Tools Available:**
- `analyzePacing()` - Check scene length and intensity curves
- `trackThemes()` - Monitor thematic presence and development
- `evaluateDialogueNaturalness()` - Rate dialogue quality
- `analyzeProseStyle()` - Check for writing craft issues
- `compareTones()` - Check consistency of narrative voice

**Example Query:**
```
Chapters 8-10: 45 pages without major plot development
User: "These chapters feel slow. Are they necessary?"

Agent Response:
"PACING CONCERN DETECTED:
- 45-page stretch with low tension (intensity score: 2.3/10)
- Follows climax (intensity 9.0), so breathing room is good
- BUT: Only 15% of content advances plot
- 30% is character introspection, 35% is description

RECOMMENDATIONS:
- Keep introspection (character development)
- Trim descriptions by 20-30%
- Add subplot tension (raise stakes on secondary plot)
- Target: 25-30 pages (still breathing room, better paced)
"
```

**System Prompt Template:**
```
You are a writing coach and craft specialist. Your expertise is in:
- Pacing and narrative rhythm (tension curves)
- Thematic development and consistency
- Dialogue authenticity and distinctiveness
- Prose quality (show vs. tell, active voice, sensory details)
- Narrative voice consistency

When analyzing craft:
1. Evaluate pacing against genre expectations
2. Track thematic elements and their development
3. Check dialogue sounds natural and character-distinct
4. Identify show-vs-tell opportunities
5. Note prose strengths and weaknesses

Always provide specific improvements with examples. Focus on HOW the
story is told, not WHAT happens (plot agent handles that).
```

---

### 4. World Building Agent (Priority: Medium)

**Purpose**: Ensure world consistency, magic system logic, and lore integrity.

**Responsibilities:**
- Validate magic/technology system consistency
- Check world lore for contradictions
- Verify geography and travel logic
- Monitor cultural rules and consistency
- Track established world facts

**Tools Available:**
- `validateLore()` - Check world facts for contradictions
- `checkMagicSystemConsistency()` - Verify magic rules
- `verifyGeography()` - Check travel times and distances
- `validateCulturalRules()` - Ensure cultural consistency
- `extractWorldFacts()` - Build world knowledge base

**Example Query:**
```
Established Rule: Magic requires 3-hour meditation to recharge
Scene 1: Wizard meditates 3 hours
Scene 2: Wizard casts spell, meditates 30 minutes, casts again

Agent Response:
"MAGIC SYSTEM INCONSISTENCY:
- Scene 2 violates established 3-hour recharge rule
- Reader will feel cheated by rule-breaking

OPTIONS:
1. Extend meditation in Scene 2 to 3 hours
2. Establish that desperate situations allow shorter recharge (costs health?)
3. Introduce second magic source (different rules)
"
```

**System Prompt Template:**
```
You are a world-building architect. Your expertise is in:
- Magic/technology system design and consistency
- World lore and historical facts
- Geography, travel, and logistics
- Cultural rules and social systems
- World fact tracking and contradiction detection

When analyzing world-building:
1. Track all established world facts
2. Check new scenes against these facts
3. Verify magic/technology rules are consistent
4. Check geography for logical travel times
5. Monitor cultural consistency

Flag any contradictions or rule-breaks with specific evidence.
```

---

### 5. Supervisor Agent (Priority: Core Infrastructure)

**Purpose**: Understand user intent, route to appropriate specialists, synthesize feedback.

**Responsibilities:**
- Interpret user questions and concerns
- Route to appropriate specialist agents
- Decide if multiple agents are needed
- Synthesize feedback from multiple agents
- Prioritize issues by severity
- Explain reasoning to user

**Tools Available:**
- `callCharacterAgent()` - Route character concerns
- `callPlotAgent()` - Route plot concerns
- `callCraftAgent()` - Route craft concerns
- `callWorldAgent()` - Route world concerns
- `synthesizeFeedback()` - Combine multiple agent outputs

**Example Flow:**
```
User: "My character does something that doesn't fit her personality 
       but it's important for the plot. How do I fix this?"

Supervisor Analysis:
"This question requires TWO agents:
1. Character Agent - check personality consistency
2. Plot Agent - verify plot requirement
Then synthesize a solution that satisfies both."

Character Agent Output:
"Inconsistency: Action contradicts agreeableness profile"

Plot Agent Output:
"Plot requirement: Action is necessary for climax setup"

Supervisor Synthesis:
"SOLUTION: Add a breaking point scene that explains why she breaks
her normal pattern. This satisfies BOTH concerns:
- Character: Shows her limits, makes arc more complex
- Plot: Gives her motivation for the required action"
```

**System Prompt Template:**
```
You are the head writing coach. Your job is to understand the writer's
question and route them to the right specialist(s).

Your process:
1. Understand what they're asking about
2. Identify which agent(s) have expertise
3. If one agent, route directly
4. If multiple agents, call them in parallel
5. Synthesize their feedback into one cohesive response

ROUTING GUIDE:
- "Does this make sense?" → Plot Agent
- "Is this character action consistent?" → Character Agent
- "Does this feel paced right?" → Craft Agent
- "Does this break my world rules?" → World Agent
- Questions spanning multiple areas → Call appropriate agents + synthesize

Always explain your reasoning to the writer. Show them which agents
you consulted and why. Prioritize by story impact (plot > character > craft).
```

---

## Implementation Patterns

### Pattern 1: Supervisor-Routed Query (User-Facing)

```typescript
class WritingCoachSupervisor {
  async handleUserQuestion(manuscriptId: string, userQuestion: string) {
    // Step 1: Supervisor interprets query
    const interpretation = await this.supervisorAgent.invoke({
      message: userQuestion,
      context: "User asking for feedback"
    });
    
    // Step 2: Route to appropriate agents
    const agentsToCall = interpretation.recommendedAgents;
    // Could be: ["characterAgent"], or ["plotAgent", "characterAgent"]
    
    // Step 3: Call specialists in parallel
    const results = await Promise.all(
      agentsToCall.map(agentName => {
        const agent = this.agents[agentName];
        const relevantContext = this.extractContextForAgent(
          manuscriptId, 
          agentName
        );
        return agent.invoke(relevantContext);
      })
    );
    
    // Step 4: Synthesize feedback
    const finalResponse = await this.supervisorAgent.invoke({
      userQuestion,
      specialistFeedback: results,
      task: "synthesize into actionable advice"
    });
    
    return {
      answer: finalResponse.answer,
      agentsConsulted: agentsToCall,
      reasoning: finalResponse.reasoning
    };
  }
}
```

### Pattern 2: Direct Agent Call (Automated Analysis)

```typescript
class ManuscriptAnalyzer {
  async runFullAnalysis(manuscriptId: string) {
    const manuscript = await fetchManuscript(manuscriptId);
    
    // No supervisor overhead - we know exactly what we need
    const [characterIssues, plotIssues, craftIssues, worldIssues] = 
      await Promise.all([
        this.characterAgent.detectIssues(manuscript),
        this.plotAgent.detectIssues(manuscript),
        this.craftAgent.detectIssues(manuscript),
        this.worldAgent.detectIssues(manuscript)
      ]);
    
    // Combine and prioritize
    const allIssues = [
      ...characterIssues,
      ...plotIssues,
      ...craftIssues,
      ...worldIssues
    ];
    
    const prioritized = this.prioritizeByServerity(allIssues);
    
    return prioritized;
  }
}
```

### Pattern 3: Context Extraction (Token Efficiency)

```typescript
class ContextExtractor {
  // Don't send entire 80,000 word manuscript to every agent
  
  extractContextForCharacterAgent(
    manuscript: string, 
    characterName: string
  ) {
    // Find all scenes with this character
    // Include: character introduction, dialogue samples, relationship scenes
    // Exclude: scenes without this character
    // Result: ~3,000-5,000 tokens instead of 20,000+
    return relevantScenes;
  }
  
  extractContextForPlotAgent(manuscript: string) {
    // Extract: chapter summaries, major events, turning points
    // Exclude: detailed prose, internal monologue
    // Result: ~5,000-8,000 tokens (structured data is efficient)
    return eventChain;
  }
  
  extractContextForCraftAgent(manuscript: string, sceneIndex: number) {
    // For pacing: full scene + surrounding scenes for context
    // For prose style: scene samples from different chapters
    // Result: ~4,000-6,000 tokens per analysis
    return relevantScenes;
  }
}
```

---

## When to Use Each Agent

### Supervisor Agent (Route User Questions)
```typescript
✅ DO: User types "Does my character feel real?"
✅ DO: User asks "Is this plot twist earned?"
✅ DO: User says "These middle chapters feel slow"

❌ DON'T: Call during automated background analysis
❌ DON'T: Use when you already know the analysis type
❌ DON'T: Use for every single query (slow, uses tokens)
```

### Direct Agent Calls (Automated Analysis)
```typescript
✅ DO: On manuscript save, auto-run all agents
✅ DO: User clicks "Analyze entire manuscript"
✅ DO: Batch processing at night

PATTERN:
await characterAgent.analyze(manuscript);
await plotAgent.analyze(manuscript);
// No supervisor - we know exactly what we need
```

### Hybrid Approach (Recommended)
```typescript
User Types Message
    ↓
[Is it short?] → Call Supervisor (routes to right agents)
[Is it long/complex?] → Run all agents in background

This balances:
- User experience (supervisor for interactive queries)
- Efficiency (direct calls for batch analysis)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create CharacterAgent (highest value)
- [ ] Create PlotAgent (foundational)
- [ ] Implement basic Supervisor
- [ ] Build context extraction utilities

**Deliverable**: User can ask "Is character X consistent?" and get quality feedback

### Phase 2: Expansion (Week 3-4)
- [ ] Create CraftAgent (differentiation)
- [ ] Improve Supervisor routing logic
- [ ] Add background analysis on save
- [ ] Build issue UI to display agent feedback

**Deliverable**: Full feedback suite from 3 agents on user demand or auto-analysis

### Phase 3: Depth (Week 5-6)
- [ ] Create WorldAgent (for fantasy/sci-fi focus)
- [ ] Add specialized prompts for user's specific genre
- [ ] Build agent caching for repeated analyses
- [ ] Implement cost tracking per agent

**Deliverable**: Enterprise-grade specialized analysis

### Phase 4: Polish (Week 7-8)
- [ ] Optimize token usage and context extraction
- [ ] Add user-facing explanations of agent reasoning
- [ ] Implement batch analysis scheduling
- [ ] Build analytics on which agents are most valuable

**Deliverable**: Production-ready agent system

---

## Technology Stack

### LangChain Components
```typescript
import { ChatOpenAI } from "@langchain/openai";
import { AgentExecutor, createOpenAIToolsAgent } from "langchain/agents";
import { Tool } from "@langchain/core/tools";
import { DynamicStructuredTool } from "@langchain/core/tools";
```

### Agent Structure
```typescript
interface SpecialistAgent {
  name: string;
  systemPrompt: string;
  tools: Tool[];
  invoke(context: AgentContext): Promise<AgentOutput>;
}

interface AgentOutput {
  issues: Issue[];
  suggestions: Suggestion[];
  reasoning: string;
  confidence: number;
}
```

### Tools Pattern
```typescript
const characterConsistencyTool = new DynamicStructuredTool({
  name: "check_character_consistency",
  description: "Check if a character's action is consistent with their personality",
  schema: z.object({
    characterName: z.string(),
    action: z.string(),
    personalityProfile: z.object({
      openness: z.number(),
      conscientiousness: z.number(),
      extraversion: z.number(),
      agreeableness: z.number(),
      neuroticism: z.number()
    })
  }),
  func: async (input) => {
    // Your existing CharacterConsistencyService logic here
    return await characterConsistencyService.check(input);
  }
});
```

---

## Token Usage Optimization

### Current Approach (Inefficient)
```
Single agent analyzes entire 80,000 word manuscript
= ~20,000 tokens per analysis
x 5 agents = 100,000 tokens
x users = $$ spent

Cost: ~$3 per full analysis (expensive)
```

### Multi-Agent Approach (Efficient)
```
Character Agent: Analyzes only character scenes (~3,000 tokens)
Plot Agent: Analyzes event chain (~5,000 tokens)
Craft Agent: Analyzes scene samples (~4,000 tokens)
World Agent: Analyzes lore references (~2,000 tokens)

Total: ~14,000 tokens per full analysis
Cost: ~$0.40 per full analysis (10x cheaper!)

Plus: Context extraction means better focused analysis
```

### Caching Strategy
```typescript
// Store agent outputs for 1 hour
const cache = new Map<string, CachedAnalysis>();

const cacheKey = `${manuscriptId}:${agentName}:${wordCount}`;

if (cache.has(cacheKey)) {
  return cache.get(cacheKey); // Free! (no tokens)
}

// Run analysis
const result = await agent.invoke(context);

// Store for later
cache.set(cacheKey, result);
```

---

## Integration with Existing Services

### Connection to PlotAnalysisService
```typescript
// Your existing service
const plotAnalysisService = new PlotAnalysisService();

// LangChain agent uses it as a tool
const detectPlotHolesTool = new DynamicStructuredTool({
  name: "detect_plot_holes",
  func: async (input) => {
    return await plotAnalysisService.detectPlotHoles(input.manuscriptId);
  }
});
```

### Connection to CharacterConsistencyService
```typescript
// Your existing service
const characterService = new CharacterConsistencyService();

// LangChain agent uses it
const checkCharacterConsistency = new DynamicStructuredTool({
  name: "check_character_consistency",
  func: async (input) => {
    return await characterService.checkCharacterConsistency(input.manuscriptId);
  }
});
```

### Connection to Novel Skeleton Generator
```typescript
// Supervisor agent can call skeleton generator for structure advice
const generateStructureTool = new DynamicStructuredTool({
  name: "suggest_structure",
  func: async (input) => {
    const generator = new NovelSkeletonGenerator();
    return await generator.suggestStructureImprovement(
      input.manuscriptId,
      input.userInput
    );
  }
});
```

---

## User-Facing Features

### 1. Interactive Feedback Chat
```
User: "Is Chapter 12 paced correctly?"
System: "Routing to Craft Agent..."
Agent: "Chapter 12 analysis: [detailed feedback]"
Display: Highlighted pacing issues with suggestions
```

### 2. Auto-Analysis on Save
```
User: [Saves manuscript]
System: Runs all agents in background
Toast: "Analyzed! Found 3 plot issues, 1 character issue"
Display: Issues panel updates with new findings
```

### 3. Agent Specialization Display
```
FEEDBACK FOR YOUR STORY:

PLOT INTEGRITY (via Plot Agent):
  ⚠️ Plot hole in Chapter 8...
  ⚠️ Unresolved thread from Chapter 3...

CHARACTER DEVELOPMENT (via Character Agent):
  ✓ Character arcs are progressing well
  ⚠️ Dialogue inconsistency for Sarah...

PACING & CRAFT (via Craft Agent):
  ⚠️ Chapter 6 is paced very slowly...
  ⚠️ Theme of "redemption" not developed enough...

WORLD BUILDING (via World Agent):
  ✓ Magic system is consistent
  ✓ Geography checks out
```

---

## Success Metrics

### Quality Metrics
- [ ] Agent feedback matches professional editor feedback (>80% alignment)
- [ ] Users can't tell if feedback is from agent or human
- [ ] Writers implement >60% of agent suggestions

### Efficiency Metrics
- [ ] Average tokens per analysis < 15,000
- [ ] Cost per analysis < $0.50
- [ ] Analysis completes in < 30 seconds

### Engagement Metrics
- [ ] Users run agent feedback >5x per manuscript
- [ ] Character and Plot agents used equally (balanced value)
- [ ] Craft agent used >50% of the time (craft matters!)

---

## Gotchas & Considerations

### ⚠️ Hallucination Risk
- Agents might make up "facts" about the manuscript
- **Mitigation**: Always pass actual manuscript text, use structured outputs

### ⚠️ Contradictory Feedback
- Character agent might flag something plot agent says is necessary
- **Mitigation**: Supervisor synthesizes and resolves conflicts

### ⚠️ Genre-Specific Rules
- Magic system rules vary by genre
- Literary fiction paces differently than thriller
- **Mitigation**: Pass genre context to agents, customize prompts

### ⚠️ Token Cost Creep
- Adding more agents = more tokens
- Long manuscripts = exponential token growth
- **Mitigation**: Aggressive context extraction, caching, batch analysis at night

---

## Related Documentation

- **Novel Skeleton Generator**: `/mnt/project/Writing_Helper_Platform_-_Complete_Technical_Implementation_Guide.md`
- **Defect Detection**: PlotAnalysisService, CharacterConsistencyService
- **User Stories**: Epic 4 (Agentic AI Integration)
- **Database Schema**: Project, Character, PlotPoint, Issue models

---

## Questions for Joe

1. Should Supervisor also suggest when agents disagree? (e.g., character vs. plot conflict) Yes.
2. For CraftAgent, should it have sub-tools for pacing, prose, dialogue separately? Yes it should
3. Should agents store their analysis in the database for historical tracking? Yes
4. What happens if an agent can't find issues? (Empty feedback, "All good!", specific message?) Provide some confirmation
5. Should users be able to disable certain agents? (e.g., "I don't care about pacing") Not to begin with. 

---

**Last Updated**: December 13, 2025  
**Status**: Ready for Implementation  
**Next Step**: Build CharacterAgent (Phase 1)