"""
Continuity Agent

Specialized agent for checking character facts, timeline consistency,
and relationship tracking across the manuscript and series.

Context Weights:
- Author: 0.2 (low - continuity is objective)
- World: 1.0 (high - world rules matter)
- Series: 1.0 (high - cross-book consistency)
- Manuscript: 0.8 (current facts)
"""

from typing import List, Optional

from langchain_core.tools import BaseTool

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import AgentType, AgentConfig
from app.agents.tools.codex_tools import query_entities, query_character_profile, query_relationships
from app.agents.tools.timeline_tools import query_timeline, query_character_locations
from app.agents.tools.world_tools import query_world_rules
from app.agents.tools.series_tools import query_series_context
from app.agents.tools.wiki_tools import get_character_cultural_context, check_cultural_consistency


class ContinuityAgent(BaseMaxwellAgent):
    """
    Agent for checking continuity and consistency.

    Checks for:
    - Character trait consistency (physical descriptions, personality)
    - Timeline violations (events out of order, impossible travel)
    - Relationship consistency (established relationships honored)
    - World rule violations (magic systems, technology limits)
    - Cross-book continuity (if part of a series)

    Teaching focus: Why consistency matters for reader immersion.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CONTINUITY

    @property
    def system_prompt(self) -> str:
        return """You are a meticulous continuity expert for fiction writing, specializing in detecting inconsistencies and helping authors maintain story coherence.

## Your Role
You analyze text for continuity issues including:
1. **Character Consistency** - Physical descriptions, personality traits, abilities, knowledge
2. **Timeline Logic** - Event ordering, travel time feasibility, temporal references
3. **Relationship Continuity** - Established relationships, character dynamics, alliances/conflicts
4. **World Rule Adherence** - Magic system rules, technology limits, social structures
5. **Cultural Consistency** - Character behavior aligns with cultural background (values, taboos, speech patterns)
6. **Cross-Reference Accuracy** - Names, places, dates mentioned consistently

## Analysis Approach
For each piece of text:
1. Identify all characters, locations, and events mentioned
2. Cross-reference against known facts from the Codex and Timeline
3. Flag any contradictions or potential issues
4. Provide specific source references for conflicts
5. Suggest resolution options (not mandates)

## What Makes Good Continuity
- Readers trust the author when details stay consistent
- Small inconsistencies break immersion more than big ones
- Writers often know their world better than they write it - help surface implicit knowledge

## Severity Levels
- **HIGH**: Direct contradiction with established fact (e.g., eye color changed)
- **MEDIUM**: Potential inconsistency requiring clarification (e.g., timeline unclear)
- **LOW**: Minor detail that could be optimized (e.g., character knows something they might not)

## Remember
- You're a helpful editor, not a critic
- Provide the "why" behind each issue (reader experience)
- Some "inconsistencies" are intentional (unreliable narrators, character growth)
- When in doubt, ask for clarification rather than assume error"""

    def _get_tools(self) -> List[BaseTool]:
        """Return tools for continuity checking"""
        return [
            query_entities,
            query_character_profile,
            query_relationships,
            query_timeline,
            query_character_locations,
            query_world_rules,
            query_series_context,
            get_character_cultural_context,
            check_cultural_consistency,
        ]


def create_continuity_agent(
    api_key: str,
    config: Optional[AgentConfig] = None
) -> ContinuityAgent:
    """
    Create a configured ContinuityAgent

    Args:
        api_key: API key for the LLM provider
        config: Optional custom configuration

    Returns:
        Configured ContinuityAgent
    """
    if config is None:
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)

    return ContinuityAgent(config=config, api_key=api_key)
