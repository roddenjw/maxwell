"""
Specialized Agents for Maxwell

Each agent focuses on a specific aspect of writing analysis:
- ContinuityAgent: Character facts, timeline consistency
- StyleAgent: Prose quality, show vs tell, pacing
- StructureAgent: Beat alignment, story progression
- VoiceAgent: Dialogue authenticity, character voice
- ConsistencyAgent: Dedicated consistency checking (real-time and full scan)
- ResearchAgent: Worldbuilding and research generation
- StoryStructureGuideAgent: Outline guidance and beat mapping
"""

from app.agents.specialized.continuity_agent import ContinuityAgent, create_continuity_agent
from app.agents.specialized.style_agent import StyleAgent, create_style_agent
from app.agents.specialized.structure_agent import StructureAgent, create_structure_agent
from app.agents.specialized.voice_agent import VoiceAgent, create_voice_agent
from app.agents.specialized.consistency_agent import (
    ConsistencyAgent,
    create_consistency_agent,
    ConsistencyFocus,
    ConsistencyResult,
    ConsistencyIssue,
)
from app.agents.specialized.research_agent import (
    ResearchAgent,
    create_research_agent,
    WorldbuildingCategory,
    ResearchResult,
    WorldbuildingElement,
)
from app.agents.specialized.story_structure_guide_agent import (
    StoryStructureGuideAgent,
    create_story_structure_guide_agent,
    OutlineGuideMode,
)

__all__ = [
    # Original agents
    "ContinuityAgent",
    "create_continuity_agent",
    "StyleAgent",
    "create_style_agent",
    "StructureAgent",
    "create_structure_agent",
    "VoiceAgent",
    "create_voice_agent",
    # Consistency agent
    "ConsistencyAgent",
    "create_consistency_agent",
    "ConsistencyFocus",
    "ConsistencyResult",
    "ConsistencyIssue",
    # Research agent
    "ResearchAgent",
    "create_research_agent",
    "WorldbuildingCategory",
    "ResearchResult",
    "WorldbuildingElement",
    # Story Structure Guide agent
    "StoryStructureGuideAgent",
    "create_story_structure_guide_agent",
    "OutlineGuideMode",
]
