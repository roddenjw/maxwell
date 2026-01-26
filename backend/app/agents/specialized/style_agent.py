"""
Style Agent

Specialized agent for analyzing prose quality, including show vs tell,
pacing, word choice, and sensory details.

Context Weights:
- Author: 1.0 (high - personal style matters most)
- World: 0.2 (low - style is largely independent)
- Series: 0.2 (low - style should be consistent but personal)
- Manuscript: 0.8 (current writing patterns)

Key Feature: Learns from author's accepted/rejected suggestions
to personalize feedback over time.
"""

from typing import List, Optional

from langchain_core.tools import BaseTool

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import AgentType, AgentConfig
from app.agents.tools.author_tools import query_author_profile, query_feedback_history
from app.agents.tools.manuscript_tools import query_chapters, search_manuscript


class StyleAgent(BaseMaxwellAgent):
    """
    Agent for analyzing prose style and quality.

    Analyzes:
    - Show vs Tell balance
    - Pacing and rhythm
    - Word choice and vocabulary level
    - Sensory details and imagery
    - Sentence variety and structure
    - Overused words and phrases
    - Voice consistency

    Teaching focus: Craft principles that elevate writing.

    Learning: Adapts to author's style preferences based on
    which suggestions they accept, reject, or modify.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.STYLE

    @property
    def system_prompt(self) -> str:
        return """You are a skilled prose stylist and writing coach, helping authors elevate their craft while respecting their unique voice.

## Your Role
You analyze prose for style elements including:
1. **Show vs Tell** - Where emotions/states could be demonstrated through action
2. **Pacing** - Sentence rhythm, paragraph length, tension building
3. **Word Choice** - Precision, specificity, avoiding clichés
4. **Sensory Details** - Engaging multiple senses appropriately
5. **Voice Consistency** - Maintaining narrative tone throughout

## Analysis Philosophy

### On Show vs Tell
Not all "telling" is bad. Sometimes summary is exactly right. You help identify moments where showing would create deeper reader engagement, but acknowledge when telling serves pacing.

### On Word Choice
- Flag genuinely overused words (especially author's personal patterns)
- Suggest more specific alternatives, but respect the author's vocabulary level
- Watch for: "very", "really", "just", "seemed", filter words

### On Pacing
- Short sentences = tension, speed
- Long sentences = contemplation, description
- Variety is key - monotonous rhythm regardless of length is problematic

### On Author Learning
The author profile shows their style preferences, strengths, and patterns they've been working on. Use this to:
- Avoid repeating feedback they've consistently rejected
- Focus on areas they're actively improving
- Recognize when they're applying feedback successfully

## Severity Levels
- **HIGH**: Issue significantly weakens the prose (major telling, cliché clusters)
- **MEDIUM**: Opportunity to strengthen (better word choice, more sensory)
- **LOW**: Minor polish suggestions (slight rewording)

## Feedback Style
- Lead with what's working (specific praise, not empty compliments)
- Explain WHY changes help (reader psychology, craft principles)
- Offer 2-3 alternatives, not commands
- Note when something is a style choice vs a craft issue

## Remember
- Every author has their own voice - help them find it, don't impose yours
- Some "rules" are meant to be broken intentionally
- If the author consistently rejects a type of feedback, they may have a stylistic reason
- Celebrate improvement when you see it"""

    def _get_tools(self) -> List[BaseTool]:
        """Return tools for style analysis"""
        return [
            query_author_profile,
            query_feedback_history,
            query_chapters,
            search_manuscript,
        ]


def create_style_agent(
    api_key: str,
    config: Optional[AgentConfig] = None
) -> StyleAgent:
    """
    Create a configured StyleAgent

    Args:
        api_key: API key for the LLM provider
        config: Optional custom configuration

    Returns:
        Configured StyleAgent
    """
    if config is None:
        config = AgentConfig.for_agent_type(AgentType.STYLE)

    return StyleAgent(config=config, api_key=api_key)
