"""
Research & Worldbuilding Agent for Maxwell

An agent for generating interconnected worldbuilding elements:
- Cultures and societies
- Magic/technology systems
- Geography and locations
- History and lore
- Politics and factions

Features:
- Generates content that fits existing world context
- Creates draft Codex entities from research
- Optional web search for real-world research (DuckDuckGo)
- Cross-references with existing entities

Usage:
    agent = create_research_agent(api_key="sk-...")

    # Generate worldbuilding
    result = await agent.generate_worldbuilding(
        topic="magic system",
        manuscript_id="ms123",
        constraints=["low magic", "elemental based"]
    )

    # Research real-world topic
    result = await agent.research_topic(
        topic="medieval castle defenses",
        use_web_search=True
    )
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import AgentConfig, AgentType, ModelConfig
from app.agents.tools import (
    query_entities,
    query_world_settings,
    query_world_rules,
    search_entities,
)
from langchain_core.tools import BaseTool


class WorldbuildingCategory(str, Enum):
    """Categories of worldbuilding content"""
    CULTURE = "culture"
    MAGIC_SYSTEM = "magic_system"
    TECHNOLOGY = "technology"
    GEOGRAPHY = "geography"
    HISTORY = "history"
    POLITICS = "politics"
    RELIGION = "religion"
    ECONOMY = "economy"
    CREATURE = "creature"
    LANGUAGE = "language"


@dataclass
class WorldbuildingElement:
    """A generated worldbuilding element"""
    category: str
    name: str
    description: str
    details: Dict[str, Any]
    connections: List[str]  # Names of related elements
    draft_entity: Optional[Dict[str, Any]] = None  # Ready for Codex import

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "details": self.details,
            "connections": self.connections,
            "draft_entity": self.draft_entity,
        }


@dataclass
class ResearchResult:
    """Result from research or worldbuilding generation"""
    success: bool
    topic: str
    elements: List[WorldbuildingElement] = field(default_factory=list)
    summary: str = ""
    sources: List[str] = field(default_factory=list)  # For web research
    suggestions: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "topic": self.topic,
            "elements": [e.to_dict() for e in self.elements],
            "summary": self.summary,
            "sources": self.sources,
            "suggestions": self.suggestions,
            "execution_time_ms": self.execution_time_ms,
            "cost": self.cost,
            "element_count": len(self.elements),
        }


RESEARCH_SYSTEM_PROMPT = """You are a creative worldbuilding assistant for fiction writers. Your expertise includes:

## Worldbuilding Domains
1. **Cultures & Societies**: Social structures, customs, traditions, values, conflicts
2. **Magic/Technology Systems**: Rules, limitations, costs, applications, rare abilities
3. **Geography**: Climates, terrain, natural resources, strategic locations
4. **History**: Wars, migrations, discoveries, rise and fall of civilizations
5. **Politics**: Power structures, factions, alliances, conflicts, leadership
6. **Religion**: Beliefs, practices, organizations, conflicts, supernatural elements
7. **Economy**: Trade, currency, resources, class systems, industry
8. **Creatures**: Flora, fauna, monsters, their roles in the ecosystem
9. **Languages**: Naming conventions, common phrases, linguistic families

## Generation Principles
1. **Internal Consistency**: Everything must fit together logically
2. **Interconnection**: Elements should reference and affect each other
3. **Conflict Potential**: Include sources of tension and drama
4. **Sensory Details**: Provide concrete, evocative descriptions
5. **Author's World First**: Always respect and build upon existing world context

## Response Format
Respond with valid JSON:
{
  "elements": [
    {
      "category": "culture|magic_system|geography|history|politics|religion|economy|creature|language",
      "name": "Element Name",
      "description": "2-3 sentence overview",
      "details": {
        "key_aspects": ["aspect1", "aspect2"],
        "notable_features": ["feature1", "feature2"],
        "potential_conflicts": ["conflict1"],
        "story_hooks": ["hook1", "hook2"]
      },
      "connections": ["Related Element 1", "Related Element 2"],
      "draft_entity": {
        "name": "Element Name",
        "type": "LORE|LOCATION|FACTION|ITEM|CONCEPT",
        "description": "For Codex import",
        "attributes": {}
      }
    }
  ],
  "summary": "Brief overview of how these elements fit together",
  "suggestions": ["Ideas for further development"]
}"""


WORLDBUILDING_PROMPT_TEMPLATE = """Generate worldbuilding content for: {topic}

## Existing World Context
{world_context}

## Existing Relevant Entities
{entity_context}

## Author's Constraints
{constraints}

## Genre/Tone
{genre}

Generate {count} interconnected elements that:
1. Fit naturally with the existing world
2. Connect to existing entities where possible
3. Provide story hooks and conflict potential
4. Include sensory and cultural details

Make each element ready for Codex import with a draft_entity structure."""


RESEARCH_PROMPT_TEMPLATE = """Research the following topic for fiction writing: {topic}

## Purpose
{purpose}

## World Context (if applicable)
{world_context}

## Specific Questions
{questions}

Provide:
1. Key facts relevant to fiction writing
2. Interesting details that could inspire story elements
3. Common misconceptions to avoid
4. Story-worthy aspects (conflicts, drama potential)
5. Suggestions for how to adapt this for the author's world

Focus on practical information for storytelling, not academic completeness."""


class ResearchAgent(BaseMaxwellAgent):
    """
    Agent specialized in worldbuilding and research.

    Generates interconnected world elements and researches topics
    to support fiction writing.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CONTINUITY  # Reusing continuity type for now

    @property
    def system_prompt(self) -> str:
        return RESEARCH_SYSTEM_PROMPT

    def _get_tools(self) -> List[BaseTool]:
        return [
            query_entities,
            query_world_settings,
            query_world_rules,
            search_entities,
        ]

    async def generate_worldbuilding(
        self,
        topic: str,
        user_id: str,
        manuscript_id: str,
        category: Optional[WorldbuildingCategory] = None,
        constraints: Optional[List[str]] = None,
        count: int = 3,
        genre: str = "fantasy"
    ) -> ResearchResult:
        """
        Generate interconnected worldbuilding elements.

        Args:
            topic: What to generate (e.g., "merchant guilds", "desert civilization")
            user_id: User ID for context
            manuscript_id: Manuscript ID for world context
            category: Specific category to focus on
            constraints: Author-specified constraints
            count: Number of elements to generate
            genre: Genre for tone matching

        Returns:
            ResearchResult with generated elements
        """
        start_time = datetime.utcnow()

        try:
            # Load world context
            world_context = await self._load_world_context(manuscript_id)
            entity_context = await self._load_relevant_entities(manuscript_id, topic)

            # Build prompt
            constraint_text = "\n".join(f"- {c}" for c in (constraints or []))
            if not constraint_text:
                constraint_text = "No specific constraints"

            prompt = WORLDBUILDING_PROMPT_TEMPLATE.format(
                topic=topic,
                world_context=world_context,
                entity_context=entity_context,
                constraints=constraint_text,
                genre=genre,
                count=count
            )

            # Run generation
            result = await self.analyze(
                text=prompt,
                user_id=user_id,
                manuscript_id=manuscript_id
            )

            # Parse elements
            elements = self._parse_elements(result)

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ResearchResult(
                success=result.success,
                topic=topic,
                elements=elements,
                summary=self._extract_summary(result),
                suggestions=self._extract_suggestions(result),
                execution_time_ms=execution_time,
                cost=result.cost
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            return ResearchResult(
                success=False,
                topic=topic,
                summary=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )

    async def research_topic(
        self,
        topic: str,
        user_id: str,
        manuscript_id: Optional[str] = None,
        purpose: str = "worldbuilding inspiration",
        questions: Optional[List[str]] = None,
        use_web_search: bool = False
    ) -> ResearchResult:
        """
        Research a topic for fiction writing.

        Args:
            topic: What to research (e.g., "medieval castle defenses")
            user_id: User ID
            manuscript_id: Optional manuscript for world context
            purpose: What the research is for
            questions: Specific questions to answer
            use_web_search: Whether to use DuckDuckGo (not implemented yet)

        Returns:
            ResearchResult with findings
        """
        start_time = datetime.utcnow()

        try:
            # Load world context if manuscript provided
            world_context = ""
            if manuscript_id:
                world_context = await self._load_world_context(manuscript_id)

            # Build questions text
            questions_text = "\n".join(f"- {q}" for q in (questions or []))
            if not questions_text:
                questions_text = "General overview for fiction writing"

            prompt = RESEARCH_PROMPT_TEMPLATE.format(
                topic=topic,
                purpose=purpose,
                world_context=world_context or "No specific world context",
                questions=questions_text
            )

            # Run research
            result = await self.analyze(
                text=prompt,
                user_id=user_id,
                manuscript_id=manuscript_id or ""
            )

            # Parse results
            elements = self._parse_elements(result)

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ResearchResult(
                success=result.success,
                topic=topic,
                elements=elements,
                summary=self._extract_summary(result),
                suggestions=self._extract_suggestions(result),
                sources=["AI-generated based on training data"],
                execution_time_ms=execution_time,
                cost=result.cost
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            return ResearchResult(
                success=False,
                topic=topic,
                summary=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )

    def _parse_elements(self, result: AgentResult) -> List[WorldbuildingElement]:
        """Parse AgentResult into WorldbuildingElement objects"""
        elements = []

        # Try to extract from recommendations
        for rec in result.recommendations:
            if rec.get("type") == "worldbuilding" or "element" in rec.get("type", "").lower():
                elements.append(WorldbuildingElement(
                    category=rec.get("category", "general"),
                    name=rec.get("name", rec.get("text", "")[:50]),
                    description=rec.get("text", ""),
                    details=rec.get("details", {}),
                    connections=rec.get("connections", []),
                    draft_entity=rec.get("draft_entity"),
                ))

        # If no structured elements, create one from raw response
        if not elements and result.raw_response:
            elements.append(WorldbuildingElement(
                category="general",
                name="Research Results",
                description=result.raw_response[:500],
                details={},
                connections=[],
            ))

        return elements

    def _extract_summary(self, result: AgentResult) -> str:
        """Extract summary from result"""
        if result.raw_response:
            # Try to find summary in JSON response
            import json
            try:
                data = json.loads(result.raw_response)
                return data.get("summary", "")
            except (json.JSONDecodeError, TypeError):
                pass
        return ""

    def _extract_suggestions(self, result: AgentResult) -> List[str]:
        """Extract suggestions from result"""
        if result.raw_response:
            import json
            try:
                data = json.loads(result.raw_response)
                return data.get("suggestions", [])
            except (json.JSONDecodeError, TypeError):
                pass
        return result.teaching_points

    async def _load_world_context(self, manuscript_id: str) -> str:
        """Load world context for the manuscript"""
        return f"[World context for manuscript {manuscript_id}]"

    async def _load_relevant_entities(self, manuscript_id: str, topic: str) -> str:
        """Load entities relevant to the topic"""
        return f"[Entities related to '{topic}' in manuscript {manuscript_id}]"


def create_research_agent(
    api_key: str,
    config: Optional[AgentConfig] = None
) -> ResearchAgent:
    """Factory function to create a Research Agent"""
    if config is None:
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        config.response_format = "json"

    return ResearchAgent(config=config, api_key=api_key)
