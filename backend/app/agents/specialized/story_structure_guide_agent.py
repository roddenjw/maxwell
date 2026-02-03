"""
Story Structure Guide Agent

Specialized agent for guiding writers through story structure and outlining.
Unlike StructureAgent (which analyzes prose), this agent helps BUILD outlines.

This agent:
- Helps fill in beats with story-specific content
- Maps scenes between major plot points
- Provides structure feedback on chapters against their beats
- Suggests outline ideas based on manuscript context
- Guides writers through systematic outline completion

Context Weights:
- Author: 0.4 (some - understand author's voice/preferences)
- World: 0.6 (medium - story needs world context)
- Series: 0.8 (high - series arc matters for structure)
- Manuscript: 1.0 (highest - current outline is primary)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.tools import BaseTool

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import AgentType, AgentConfig
from app.agents.tools.outline_tools import query_outline, query_plot_beats
from app.agents.tools.outline_guide_tools import (
    analyze_outline_completeness,
    get_beat_guidance,
    suggest_scenes_between_beats,
    analyze_chapter_beat_alignment,
    get_next_outline_step,
)
from app.agents.tools.manuscript_tools import query_chapters, query_chapter_content
from app.agents.tools.codex_tools import query_entities


@dataclass
class OutlineGuideMode:
    """Different modes for outline guidance"""
    ANALYZE = "analyze"           # Analyze outline completeness
    SUGGEST_BEAT = "suggest_beat"  # Get content suggestions for a beat
    SUGGEST_SCENES = "suggest_scenes"  # Get scene ideas between beats
    CHAPTER_FEEDBACK = "chapter_feedback"  # Analyze chapter-beat alignment
    NEXT_STEP = "next_step"        # Get recommendation for what to work on next


class StoryStructureGuideAgent(BaseMaxwellAgent):
    """
    Agent for guiding writers through story structure and outlining.

    Unlike StructureAgent (which analyzes written prose against structure),
    this agent helps writers BUILD their outline from scratch by:

    1. Explaining what each beat needs (teaching-first approach)
    2. Suggesting story-specific content for empty beats
    3. Generating bridge scene ideas between major plot points
    4. Analyzing how chapters fulfill their linked beats
    5. Recommending what to work on next

    Teaching focus: Making story structure accessible and actionable.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.STORY_STRUCTURE_GUIDE

    @property
    def system_prompt(self) -> str:
        return """You are Maxwell's Story Structure Guide - a warm, knowledgeable writing mentor who helps authors build compelling story outlines.

## Your Core Role
You help writers develop their outlines by:
1. **Teaching** - Explain WHY each beat matters and what it needs
2. **Guiding** - Suggest story-specific content based on their manuscript
3. **Connecting** - Help map scenes and chapters to structural beats
4. **Coaching** - Recommend what to work on next

## Your Expertise

### Story Structure Frameworks
You're deeply familiar with:
- **Three-Act Structure**: Setup, Confrontation, Resolution
- **Save the Cat (Blake Snyder)**: 15-beat structure for popular fiction
- **Hero's Journey (Campbell/Vogler)**: 12-stage mythic structure
- **Seven-Point Story Structure**: Hook, Plot Turn 1, Pinch 1, Midpoint, Pinch 2, Plot Turn 2, Resolution

### Beat-by-Beat Knowledge
For every major beat, you know:
- Its purpose in the story
- What elements it must contain
- Common mistakes to avoid
- How it connects to surrounding beats

## How You Help

### When Asked About a Beat
1. Explain the beat's purpose in plain language
2. List 2-4 specific things the beat needs
3. Give an example relevant to their genre/story
4. Suggest concrete content based on their characters/world
5. Note common pitfalls to avoid

### When Suggesting Scenes
1. Analyze the emotional journey between beats
2. Consider what story elements need development
3. Propose 2-4 scene ideas with clear purposes
4. Connect scenes to existing characters/conflicts
5. Explain how each scene moves the story forward

### When Analyzing Chapter-Beat Alignment
1. Review what the beat requires
2. Check if the chapter delivers those elements
3. Highlight what's working well
4. Identify what might be missing
5. Suggest specific improvements

### When Recommending Next Steps
1. Consider structural dependencies (some beats inform others)
2. Prioritize foundation beats (opening, inciting incident)
3. Look for gaps that might cause problems later
4. Match recommendations to writer's current progress

## Teaching Philosophy

Every response should educate. When you suggest "add a mentor figure," explain WHY:
- "The mentor provides tools the hero lacks"
- "This creates a relationship the hero can lose later"
- "The mentor embodies the theme the hero must learn"

## Tone and Style

- **Warm and encouraging**: Writers are sharing their creative work
- **Specific and actionable**: Vague advice is unhelpful
- **Teaching-first**: Explain principles, not just instructions
- **Collaborative**: You're a guide, not a dictator
- **Celebratory**: Acknowledge what's working

## Response Format

When suggesting content or scenes, use this structure:

**[Beat Name]: What Your Story Needs**

[Brief explanation of the beat's purpose - 1-2 sentences]

**For your story specifically:**
- [Story-specific suggestion 1]
- [Story-specific suggestion 2]
- [Story-specific suggestion 3]

**Why this matters:**
[Brief explanation of how this serves the reader's experience]

**Watch out for:**
[One common mistake to avoid]

## Important Guidelines

1. **Use character/location names** from the manuscript when available
2. **Be genre-aware** - thriller beats differ from romance beats
3. **Respect writer autonomy** - offer options, not mandates
4. **Consider series context** - if part of a series, account for larger arcs
5. **Keep suggestions achievable** - don't overwhelm with too many ideas

## What You DON'T Do

- Write the actual prose (you guide the outline, not the manuscript)
- Judge the writer's choices (you help execute their vision)
- Insist on rigid adherence to structure (rules can be bent intentionally)
- Provide generic advice disconnected from their story"""

    def _get_tools(self) -> List[BaseTool]:
        """Return tools for outline guidance"""
        return [
            # Outline querying
            query_outline,
            query_plot_beats,
            # Outline guidance
            analyze_outline_completeness,
            get_beat_guidance,
            suggest_scenes_between_beats,
            analyze_chapter_beat_alignment,
            get_next_outline_step,
            # Context tools
            query_chapters,
            query_chapter_content,
            query_entities,
        ]

    async def guide_outline(
        self,
        mode: str,
        user_id: str,
        manuscript_id: str,
        query: Optional[str] = None,
        beat_id: Optional[str] = None,
        beat_label: Optional[str] = None,
        chapter_id: Optional[str] = None,
        from_beat: Optional[str] = None,
        to_beat: Optional[str] = None,
        detail_level: str = "standard"
    ) -> AgentResult:
        """
        Get outline guidance in a specific mode.

        Args:
            mode: One of "analyze", "suggest_beat", "suggest_scenes",
                  "chapter_feedback", "next_step"
            user_id: User ID for context
            manuscript_id: Manuscript ID
            query: Optional free-form query
            beat_id: Beat ID for beat-specific operations
            beat_label: Beat label for beat-specific operations
            chapter_id: Chapter ID for chapter-beat alignment
            from_beat: Starting beat for scene suggestions
            to_beat: Ending beat for scene suggestions
            detail_level: "quick" for brief, "standard" for normal, "detailed" for comprehensive

        Returns:
            AgentResult with guidance
        """
        # Build the analysis query based on mode
        if mode == "analyze":
            analysis_query = f"""Analyze the outline completeness for this manuscript.
            Use the analyze_outline_completeness tool, then provide:
            1. A summary of current progress
            2. Key gaps that need attention
            3. Recommended priority for next steps

            Detail level: {detail_level}"""

        elif mode == "suggest_beat":
            beat_ref = beat_label or beat_id or "the specified beat"
            analysis_query = f"""Help the writer develop the {beat_ref} beat.

            First, use get_beat_guidance to understand what this beat needs.
            Then, use query_outline and query_entities to understand the story context.

            Provide:
            1. Explanation of what this beat needs to accomplish
            2. 3-4 story-specific suggestions based on their characters and world
            3. One or two examples of how this could play out
            4. Common mistakes to avoid

            User query: {query or "What should happen at this beat?"}
            Detail level: {detail_level}"""

        elif mode == "suggest_scenes":
            analysis_query = f"""Suggest scenes to bridge from "{from_beat}" to "{to_beat}".

            First, use suggest_scenes_between_beats to analyze the gap.
            Then, use query_entities to understand available characters.

            Provide:
            1. The emotional/narrative journey needed between these beats
            2. 2-4 scene suggestions with:
               - Scene title
               - Brief description (2-3 sentences)
               - Purpose in the story
               - Which characters should be involved
            3. How these scenes connect the beats

            User query: {query or "What scenes should connect these beats?"}
            Detail level: {detail_level}"""

        elif mode == "chapter_feedback":
            analysis_query = f"""Analyze how well the chapter fulfills its linked beat.

            Use analyze_chapter_beat_alignment to check alignment.

            Provide:
            1. What the beat requires
            2. How the chapter delivers (or doesn't) these requirements
            3. Specific strengths
            4. Specific gaps or areas to strengthen
            5. Actionable suggestions for revision

            Chapter ID: {chapter_id}
            Beat ID/Label: {beat_id or beat_label or "linked beat"}
            User query: {query or "How well does this chapter work for its beat?"}
            Detail level: {detail_level}"""

        elif mode == "next_step":
            analysis_query = f"""Recommend what the writer should work on next.

            Use get_next_outline_step to analyze progress.
            Use analyze_outline_completeness for full context.

            Provide:
            1. Clear recommendation for next focus area
            2. Why this is the priority (structural reasoning)
            3. Brief guidance on how to approach it
            4. What to tackle after this

            User query: {query or "What should I work on next?"}
            Detail level: {detail_level}"""

        else:
            # Freeform query mode
            analysis_query = f"""Help the writer with their outline question.

            Use appropriate tools to gather context, then respond to:
            {query or "How can I improve my outline?"}

            Detail level: {detail_level}"""

        # Run the analysis
        return await self.analyze(
            text=analysis_query,
            user_id=user_id,
            manuscript_id=manuscript_id,
            additional_context=f"Mode: {mode}"
        )


def create_story_structure_guide_agent(
    api_key: str,
    config: Optional[AgentConfig] = None
) -> StoryStructureGuideAgent:
    """
    Create a configured StoryStructureGuideAgent

    Args:
        api_key: API key for the LLM provider
        config: Optional custom configuration

    Returns:
        Configured StoryStructureGuideAgent
    """
    if config is None:
        config = AgentConfig.for_agent_type(AgentType.STORY_STRUCTURE_GUIDE)

    return StoryStructureGuideAgent(config=config, api_key=api_key)
