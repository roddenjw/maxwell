"""
Supervisor Agent - Intelligent Query Routing

The Supervisor understands user intent and routes to the appropriate
specialized agents. It's the "front door" to Maxwell's expertise.

Instead of users manually choosing "run style analysis" or "check continuity",
they can ask natural questions and the Supervisor determines which experts to consult.

Routing Examples:
- "Is this scene working?" → Style + Structure + Voice
- "Does Marcus feel consistent?" → Continuity + Voice
- "Is this dialogue authentic?" → Voice
- "Does this fit my world rules?" → Continuity
- "How's the pacing?" → Style + Structure

Usage:
    supervisor = SupervisorAgent(api_key="sk-...")
    routing = await supervisor.route_query("Is this character believable?")
    # Returns: RouteDecision(agents=[CONTINUITY, VOICE], reasoning="...")
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from app.agents.base.agent_config import AgentType, ModelConfig, ModelProvider
from app.services.llm_service import llm_service, LLMConfig, LLMProvider


class QueryIntent(Enum):
    """High-level categories of user intent"""
    ANALYSIS = "analysis"           # "How is my writing?"
    CONSISTENCY = "consistency"     # "Is this consistent?"
    QUALITY = "quality"             # "Is this good?"
    SPECIFIC = "specific"           # "Check the dialogue"
    BRAINSTORM = "brainstorm"       # "Help me with ideas"
    EXPLANATION = "explanation"     # "Why doesn't this work?"


@dataclass
class RouteDecision:
    """Result of supervisor routing"""
    agents: List[AgentType]
    intent: QueryIntent
    reasoning: str
    confidence: float = 1.0
    suggested_focus: Optional[str] = None  # Specific area to examine

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agents": [a.value for a in self.agents],
            "intent": self.intent.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "suggested_focus": self.suggested_focus
        }


# Fast routing rules for common patterns (no LLM needed)
FAST_ROUTING_RULES: Dict[str, List[AgentType]] = {
    # Style-focused keywords
    "pacing": [AgentType.STYLE, AgentType.STRUCTURE],
    "slow": [AgentType.STYLE, AgentType.STRUCTURE],
    "boring": [AgentType.STYLE, AgentType.STRUCTURE],
    "show don't tell": [AgentType.STYLE],
    "prose": [AgentType.STYLE],
    "overwritten": [AgentType.STYLE],
    "purple prose": [AgentType.STYLE],

    # Voice-focused keywords
    "dialogue": [AgentType.VOICE],
    "conversation": [AgentType.VOICE],
    "voice": [AgentType.VOICE],
    "authentic": [AgentType.VOICE, AgentType.CONTINUITY],
    "sounds like": [AgentType.VOICE],

    # Continuity-focused keywords
    "consistent": [AgentType.CONTINUITY],
    "contradiction": [AgentType.CONTINUITY],
    "plot hole": [AgentType.CONTINUITY, AgentType.STRUCTURE],
    "timeline": [AgentType.CONTINUITY],
    "continuity": [AgentType.CONTINUITY],
    "eye color": [AgentType.CONTINUITY],
    "character trait": [AgentType.CONTINUITY, AgentType.VOICE],

    # Structure-focused keywords (prose analysis)
    "structure": [AgentType.STRUCTURE],
    "arc": [AgentType.STRUCTURE],
    "scene goal": [AgentType.STRUCTURE],
    "turning point": [AgentType.STRUCTURE],
    "climax": [AgentType.STRUCTURE],

    # Outline guidance keywords (building/developing outline)
    "outline": [AgentType.STORY_STRUCTURE_GUIDE],
    "beat": [AgentType.STORY_STRUCTURE_GUIDE],
    "fill in": [AgentType.STORY_STRUCTURE_GUIDE],
    "what happens next": [AgentType.STORY_STRUCTURE_GUIDE],
    "what should happen": [AgentType.STORY_STRUCTURE_GUIDE],
    "scene between": [AgentType.STORY_STRUCTURE_GUIDE],
    "scenes between": [AgentType.STORY_STRUCTURE_GUIDE],
    "bridge scene": [AgentType.STORY_STRUCTURE_GUIDE],
    "develop my outline": [AgentType.STORY_STRUCTURE_GUIDE],
    "structure my": [AgentType.STORY_STRUCTURE_GUIDE],
    "how should i outline": [AgentType.STORY_STRUCTURE_GUIDE],
    "inciting incident": [AgentType.STORY_STRUCTURE_GUIDE],
    "midpoint": [AgentType.STORY_STRUCTURE_GUIDE],
    "plot point": [AgentType.STORY_STRUCTURE_GUIDE],
    "work on next": [AgentType.STORY_STRUCTURE_GUIDE],

    # Combined queries
    "working": [AgentType.STYLE, AgentType.STRUCTURE, AgentType.VOICE],
    "scene": [AgentType.STYLE, AgentType.STRUCTURE, AgentType.VOICE],
    "chapter": [AgentType.STYLE, AgentType.STRUCTURE, AgentType.CONTINUITY],
    "character": [AgentType.CONTINUITY, AgentType.VOICE],
    "believable": [AgentType.CONTINUITY, AgentType.VOICE],
}


ROUTING_SYSTEM_PROMPT = """You are Maxwell's query router. Your job is to understand what the writer is asking and determine which of Maxwell's specialized analysis capabilities to use.

## Available Specialists

1. **STYLE** - Prose quality, pacing, show vs tell, sentence variety, word choice, readability
2. **CONTINUITY** - Character consistency, timeline accuracy, world rule adherence, fact checking
3. **STRUCTURE** - Story beats, scene goals, arc progression, narrative structure, plot alignment
4. **VOICE** - Dialogue authenticity, character voice distinctiveness, conversational flow
5. **STORY_STRUCTURE_GUIDE** - Outline development, beat guidance, scene mapping between beats, filling in outline gaps

## Routing Principles

- Most questions need 2-3 specialists, not all
- "Is this working?" type questions → Style + Structure + Voice
- "Is this consistent?" → Continuity (+ Voice if about character)
- Dialogue questions → Voice (+ Continuity if about character consistency)
- Pacing questions → Style + Structure
- Outline/beat development questions → Story_Structure_Guide
- "What should happen at this beat?" → Story_Structure_Guide
- "What scenes between..." → Story_Structure_Guide
- "Help me fill in my outline" → Story_Structure_Guide
- When uncertain, include more rather than fewer

## Response Format
Return JSON:
{
  "agents": ["style", "continuity", "structure", "voice", "story_structure_guide"],  // Only include needed ones
  "intent": "analysis|consistency|quality|specific|brainstorm|explanation",
  "reasoning": "Brief explanation of routing decision",
  "confidence": 0.0-1.0,
  "suggested_focus": "Optional specific area to examine"
}"""


class SupervisorAgent:
    """
    Routes user queries to appropriate specialized agents.

    Uses fast keyword matching for common patterns and falls back
    to LLM for complex or ambiguous queries.
    """

    def __init__(
        self,
        api_key: str,
        model_config: Optional[ModelConfig] = None,
        use_fast_routing: bool = True
    ):
        """
        Initialize the Supervisor.

        Args:
            api_key: API key for LLM provider
            model_config: Optional model config (defaults to fast model)
            use_fast_routing: Whether to use keyword-based fast routing
        """
        self.api_key = api_key
        self.model_config = model_config or ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            temperature=0.3,  # Low temperature for consistent routing
            max_tokens=512
        )
        self.use_fast_routing = use_fast_routing

    async def route_query(
        self,
        query: str,
        context: Optional[str] = None
    ) -> RouteDecision:
        """
        Determine which agents should handle a query.

        Args:
            query: The user's question or request
            context: Optional additional context (selected text, chapter info, etc.)

        Returns:
            RouteDecision with agents to invoke
        """
        query_lower = query.lower()

        # Try fast routing first
        if self.use_fast_routing:
            fast_result = self._fast_route(query_lower)
            if fast_result:
                return fast_result

        # Fall back to LLM routing
        return await self._llm_route(query, context)

    def _fast_route(self, query_lower: str) -> Optional[RouteDecision]:
        """
        Attempt fast keyword-based routing.

        Returns None if no confident match found.
        """
        matched_agents: Set[AgentType] = set()
        matched_keywords: List[str] = []

        for keyword, agents in FAST_ROUTING_RULES.items():
            if keyword in query_lower:
                matched_agents.update(agents)
                matched_keywords.append(keyword)

        if matched_agents:
            # Determine intent from keywords
            if any(k in matched_keywords for k in ["consistent", "contradiction", "continuity", "plot hole"]):
                intent = QueryIntent.CONSISTENCY
            elif any(k in matched_keywords for k in ["working", "scene", "chapter"]):
                intent = QueryIntent.ANALYSIS
            else:
                intent = QueryIntent.SPECIFIC

            return RouteDecision(
                agents=list(matched_agents),
                intent=intent,
                reasoning=f"Fast routing matched keywords: {', '.join(matched_keywords)}",
                confidence=0.85
            )

        return None

    async def _llm_route(
        self,
        query: str,
        context: Optional[str] = None
    ) -> RouteDecision:
        """
        Use LLM for complex routing decisions.
        """
        user_message = f"User query: {query}"
        if context:
            user_message += f"\n\nAdditional context: {context}"

        llm_config = LLMConfig(
            provider=LLMProvider(self.model_config.provider.value),
            model=self.model_config.model_name,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            response_format="json",
            api_key=self.api_key
        )

        messages = [
            {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        response = await llm_service.generate(llm_config, messages)

        return self._parse_routing_response(response.content)

    def _parse_routing_response(self, content: str) -> RouteDecision:
        """Parse LLM routing response."""
        try:
            data = json.loads(content)

            # Map agent strings to enum
            agent_map = {
                "style": AgentType.STYLE,
                "continuity": AgentType.CONTINUITY,
                "structure": AgentType.STRUCTURE,
                "voice": AgentType.VOICE,
                "consistency": AgentType.CONSISTENCY,
                "research": AgentType.RESEARCH,
                "story_structure_guide": AgentType.STORY_STRUCTURE_GUIDE,
            }

            agents = [
                agent_map[a.lower()]
                for a in data.get("agents", ["style"])
                if a.lower() in agent_map
            ]

            # Default to all main agents if none parsed
            if not agents:
                agents = [AgentType.STYLE, AgentType.STRUCTURE, AgentType.CONTINUITY, AgentType.VOICE]

            # Parse intent
            intent_map = {
                "analysis": QueryIntent.ANALYSIS,
                "consistency": QueryIntent.CONSISTENCY,
                "quality": QueryIntent.QUALITY,
                "specific": QueryIntent.SPECIFIC,
                "brainstorm": QueryIntent.BRAINSTORM,
                "explanation": QueryIntent.EXPLANATION
            }
            intent = intent_map.get(data.get("intent", "analysis"), QueryIntent.ANALYSIS)

            return RouteDecision(
                agents=agents,
                intent=intent,
                reasoning=data.get("reasoning", "LLM routing"),
                confidence=data.get("confidence", 0.8),
                suggested_focus=data.get("suggested_focus")
            )

        except (json.JSONDecodeError, KeyError):
            # Default routing on parse failure
            return RouteDecision(
                agents=[AgentType.STYLE, AgentType.STRUCTURE, AgentType.CONTINUITY, AgentType.VOICE],
                intent=QueryIntent.ANALYSIS,
                reasoning="Default routing (parse error)",
                confidence=0.5
            )

    def get_all_agents(self) -> List[AgentType]:
        """Get list of all available agent types for full analysis."""
        return [
            AgentType.STYLE,
            AgentType.STRUCTURE,
            AgentType.CONTINUITY,
            AgentType.VOICE
        ]


class QueryClassifier:
    """
    Lightweight classifier for common query patterns.

    Used by SmartCoach to decide whether to invoke specialized agents
    or handle conversationally.
    """

    # Patterns that should trigger agent analysis
    ANALYSIS_TRIGGERS = [
        "analyze", "check", "review", "look at", "is this", "does this",
        "how is", "how's", "working", "consistent", "makes sense",
        "feel right", "sounds right", "believable", "authentic"
    ]

    # Patterns for conversational handling (no agents needed)
    CONVERSATION_PATTERNS = [
        "tell me about", "what is", "explain", "help me understand",
        "how do i", "what should", "brainstorm", "ideas for", "suggest"
    ]

    @classmethod
    def should_invoke_agents(cls, message: str) -> bool:
        """Determine if a message should trigger agent analysis."""
        message_lower = message.lower()

        # Check for analysis triggers
        for trigger in cls.ANALYSIS_TRIGGERS:
            if trigger in message_lower:
                return True

        return False

    @classmethod
    def is_brainstorm_request(cls, message: str) -> bool:
        """Check if user wants brainstorming/ideation."""
        message_lower = message.lower()
        brainstorm_words = ["brainstorm", "ideas", "suggest", "help me come up with", "what if"]
        return any(word in message_lower for word in brainstorm_words)

    @classmethod
    def extract_focus_area(cls, message: str) -> Optional[str]:
        """Extract what the user wants to focus on."""
        message_lower = message.lower()

        if "dialogue" in message_lower:
            return "dialogue"
        if "pacing" in message_lower:
            return "pacing"
        if "character" in message_lower:
            return "character"
        if "scene" in message_lower:
            return "scene"
        if "chapter" in message_lower:
            return "chapter"

        return None


def create_supervisor_agent(
    api_key: str,
    model_config: Optional[ModelConfig] = None
) -> SupervisorAgent:
    """Factory function to create a Supervisor Agent."""
    return SupervisorAgent(api_key=api_key, model_config=model_config)
