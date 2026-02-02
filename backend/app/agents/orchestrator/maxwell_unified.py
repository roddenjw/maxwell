"""
Maxwell Unified Agent - Single Entry Point for All Interactions

This is the primary interface to Maxwell's intelligence. It unifies:
- The Supervisor (routing)
- Specialized Agents (analysis)
- The Synthesizer (unified voice)
- The Smart Coach (conversation)

Users interact with ONE entity - Maxwell - who internally delegates to
specialists but always responds in a cohesive, personalized voice.

Usage:
    maxwell = MaxwellUnified(api_key="sk-...", user_id="user123")

    # Natural conversation (auto-routes to agents as needed)
    response = await maxwell.chat(
        message="Is this dialogue working?",
        manuscript_id="ms456",
        context={"selected_text": "..."}
    )

    # Full analysis (runs all relevant agents)
    analysis = await maxwell.analyze(
        text="...",
        manuscript_id="ms456"
    )

    # Quick check (single focus area)
    quick = await maxwell.quick_check(
        text="...",
        focus="dialogue",
        manuscript_id="ms456"
    )
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import asyncio

from app.agents.base.agent_config import AgentConfig, AgentType, ModelConfig, ModelProvider
from app.agents.base.agent_base import AgentResult
from app.agents.base.context_loader import ContextLoader

from app.agents.orchestrator.supervisor_agent import (
    SupervisorAgent, RouteDecision, QueryClassifier, QueryIntent
)
from app.agents.orchestrator.maxwell_synthesizer import (
    MaxwellSynthesizer, SynthesizedFeedback, SynthesisTone
)
from app.agents.orchestrator.writing_assistant import (
    WritingAssistantOrchestrator, OrchestratorResult
)

from app.agents.specialized.style_agent import create_style_agent
from app.agents.specialized.continuity_agent import create_continuity_agent
from app.agents.specialized.structure_agent import create_structure_agent
from app.agents.specialized.voice_agent import create_voice_agent

from app.services.author_learning_service import author_learning_service
from app.services.llm_service import llm_service, LLMConfig, LLMProvider


@dataclass
class MaxwellResponse:
    """Unified response from Maxwell"""
    # The main response content
    content: str

    # Type of response
    response_type: str  # "conversation", "analysis", "quick_check"

    # Structured feedback (if analysis)
    feedback: Optional[SynthesizedFeedback] = None

    # Routing info (for transparency)
    agents_consulted: List[str] = field(default_factory=list)
    routing_reasoning: str = ""

    # Metrics
    cost: float = 0.0
    tokens: int = 0
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "response_type": self.response_type,
            "feedback": self.feedback.to_dict() if self.feedback else None,
            "agents_consulted": self.agents_consulted,
            "routing_reasoning": self.routing_reasoning,
            "cost": self.cost,
            "tokens": self.tokens,
            "execution_time_ms": self.execution_time_ms
        }


MAXWELL_PERSONA_PROMPT = """You are Maxwell, a warm and knowledgeable writing coach embedded in a fiction writing IDE.

## Your Core Identity
- You're a single, cohesive entity (not a collection of tools)
- Warm, encouraging, and genuinely interested in each writer's work
- Teaching-focused: you explain the "why" behind craft principles
- Direct but tactful when pointing out issues
- You remember context from the conversation

## Your Expertise Areas
You have deep knowledge in:
- **Style & Prose**: Pacing, show vs tell, word choice, sentence variety
- **Story Structure**: Beats, arcs, scene goals, narrative momentum
- **Character Consistency**: Traits, facts, timeline accuracy
- **Voice & Dialogue**: Authenticity, distinctiveness, flow

## How You Help
- Answer questions about the writer's manuscript
- Analyze specific passages when asked
- Provide actionable, craft-based feedback
- Brainstorm ideas and solutions
- Educate about writing principles

## Your Voice
- Conversational and approachable
- Uses the author's character/location names
- Celebrates what's working, not just problems
- Provides specific examples and suggestions
- Never condescending or pedantic

{context}"""


class MaxwellUnified:
    """
    The unified Maxwell agent - single entry point for all interactions.

    Internally coordinates:
    - SupervisorAgent for intelligent routing
    - WritingAssistantOrchestrator for parallel analysis
    - MaxwellSynthesizer for unified voice
    - Direct LLM calls for conversation
    """

    def __init__(
        self,
        api_key: str,
        user_id: str,
        model_config: Optional[ModelConfig] = None
    ):
        """
        Initialize Maxwell.

        Args:
            api_key: API key for LLM provider
            user_id: User ID for personalization and context
            model_config: Optional model configuration
        """
        self.api_key = api_key
        self.user_id = user_id
        self.model_config = model_config or ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=2048
        )

        # Internal components
        self._supervisor = SupervisorAgent(api_key, model_config)
        self._synthesizer = MaxwellSynthesizer(api_key, model_config)
        self._context_loader = ContextLoader()

        # Conversation history (for session continuity)
        self._conversation_history: List[Dict[str, str]] = []

        # Metrics
        self._total_cost = 0.0
        self._total_tokens = 0

    async def chat(
        self,
        message: str,
        manuscript_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        auto_analyze: bool = True
    ) -> MaxwellResponse:
        """
        Have a conversation with Maxwell.

        Maxwell automatically determines whether to:
        - Respond conversationally
        - Invoke specialized agents for analysis
        - Combine both

        Args:
            message: User's message
            manuscript_id: Optional manuscript for context
            context: Optional additional context (selected_text, chapter_id, etc.)
            auto_analyze: Whether to auto-invoke agents when analysis seems needed

        Returns:
            MaxwellResponse with conversational reply and optional analysis
        """
        start_time = datetime.utcnow()

        # Determine if this needs agent analysis
        needs_analysis = auto_analyze and QueryClassifier.should_invoke_agents(message)
        selected_text = context.get("selected_text") if context else None

        if needs_analysis and selected_text:
            # Route and analyze, then synthesize
            return await self._chat_with_analysis(
                message=message,
                text=selected_text,
                manuscript_id=manuscript_id,
                context=context,
                start_time=start_time
            )
        else:
            # Pure conversation
            return await self._chat_conversation(
                message=message,
                manuscript_id=manuscript_id,
                context=context,
                start_time=start_time
            )

    async def _chat_with_analysis(
        self,
        message: str,
        text: str,
        manuscript_id: Optional[str],
        context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> MaxwellResponse:
        """Handle chat that requires analysis."""
        # Route the query
        route = await self._supervisor.route_query(message, text[:500])

        # Run targeted analysis
        orchestrator = WritingAssistantOrchestrator(
            api_key=self.api_key,
            model_config=self.model_config,
            enabled_agents=route.agents
        )

        result = await orchestrator.analyze(
            text=text,
            user_id=self.user_id,
            manuscript_id=manuscript_id or "",
            include_author_insights=True
        )

        # Determine synthesis tone from intent
        tone = self._intent_to_tone(route.intent)

        # Synthesize into Maxwell's voice
        feedback = await self._synthesizer.synthesize(
            result.to_dict(),
            tone=tone,
            author_context=result.author_insights
        )

        # Update conversation history
        self._conversation_history.append({"role": "user", "content": message})
        self._conversation_history.append({"role": "assistant", "content": feedback.narrative})

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MaxwellResponse(
            content=feedback.narrative,
            response_type="analysis",
            feedback=feedback,
            agents_consulted=[a.value for a in route.agents],
            routing_reasoning=route.reasoning,
            cost=feedback.cost,
            tokens=feedback.tokens,
            execution_time_ms=execution_time
        )

    async def _chat_conversation(
        self,
        message: str,
        manuscript_id: Optional[str],
        context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> MaxwellResponse:
        """Handle pure conversational chat."""
        # Build context
        context_parts = []

        if manuscript_id:
            try:
                agent_context = self._context_loader.load_full_context(
                    user_id=self.user_id,
                    manuscript_id=manuscript_id,
                    author_weight=0.5,
                    world_weight=0.3,
                    series_weight=0.2,
                    manuscript_weight=0.8
                )
                context_parts.append(agent_context.to_prompt_context(max_tokens=2000))
            except Exception:
                pass

        if context:
            if context.get("selected_text"):
                context_parts.append(f"Currently selected text:\n---\n{context['selected_text']}\n---")
            if context.get("chapter_title"):
                context_parts.append(f"Current chapter: {context['chapter_title']}")

        context_str = "\n\n".join(context_parts) if context_parts else ""
        system_prompt = MAXWELL_PERSONA_PROMPT.format(context=context_str)

        # Build messages with history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self._conversation_history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": message})

        # Generate response
        llm_config = LLMConfig(
            provider=LLMProvider(self.model_config.provider.value),
            model=self.model_config.model_name,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            api_key=self.api_key
        )

        response = await llm_service.generate(llm_config, messages)

        # Update history
        self._conversation_history.append({"role": "user", "content": message})
        self._conversation_history.append({"role": "assistant", "content": response.content})

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MaxwellResponse(
            content=response.content,
            response_type="conversation",
            agents_consulted=[],
            routing_reasoning="Conversational response (no analysis needed)",
            cost=response.cost,
            tokens=response.usage.get("total_tokens", 0),
            execution_time_ms=execution_time
        )

    async def analyze(
        self,
        text: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None,
        tone: SynthesisTone = SynthesisTone.ENCOURAGING
    ) -> MaxwellResponse:
        """
        Run full analysis with all agents.

        Args:
            text: Text to analyze
            manuscript_id: Manuscript ID for context
            chapter_id: Optional current chapter
            tone: Desired feedback tone

        Returns:
            MaxwellResponse with synthesized analysis
        """
        start_time = datetime.utcnow()

        # Run all agents via orchestrator
        orchestrator = WritingAssistantOrchestrator(
            api_key=self.api_key,
            model_config=self.model_config
        )

        result = await orchestrator.analyze(
            text=text,
            user_id=self.user_id,
            manuscript_id=manuscript_id,
            current_chapter_id=chapter_id,
            include_author_insights=True
        )

        # Synthesize
        feedback = await self._synthesizer.synthesize(
            result.to_dict(),
            tone=tone,
            author_context=result.author_insights
        )

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MaxwellResponse(
            content=feedback.narrative,
            response_type="analysis",
            feedback=feedback,
            agents_consulted=["style", "continuity", "structure", "voice"],
            routing_reasoning="Full analysis requested",
            cost=feedback.cost,
            tokens=feedback.tokens,
            execution_time_ms=execution_time
        )

    async def quick_check(
        self,
        text: str,
        focus: str,
        manuscript_id: Optional[str] = None
    ) -> MaxwellResponse:
        """
        Quick focused check using a single agent.

        Args:
            text: Text to check
            focus: Focus area ("style", "continuity", "structure", "voice", "dialogue", "pacing")
            manuscript_id: Optional manuscript for context

        Returns:
            MaxwellResponse with quick feedback
        """
        start_time = datetime.utcnow()

        # Map focus to agent type
        focus_map = {
            "style": AgentType.STYLE,
            "prose": AgentType.STYLE,
            "pacing": AgentType.STYLE,
            "continuity": AgentType.CONTINUITY,
            "consistency": AgentType.CONTINUITY,
            "structure": AgentType.STRUCTURE,
            "plot": AgentType.STRUCTURE,
            "voice": AgentType.VOICE,
            "dialogue": AgentType.VOICE,
        }

        agent_type = focus_map.get(focus.lower(), AgentType.STYLE)

        # Run single agent
        orchestrator = WritingAssistantOrchestrator(
            api_key=self.api_key,
            model_config=self.model_config,
            enabled_agents=[agent_type]
        )

        result = await orchestrator.analyze(
            text=text,
            user_id=self.user_id,
            manuscript_id=manuscript_id or "",
            include_author_insights=False
        )

        # Quick synthesis
        quick_narrative = await self._synthesizer.quick_synthesis(
            result.recommendations + result.issues,
            tone=SynthesisTone.DIRECT
        )

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MaxwellResponse(
            content=quick_narrative,
            response_type="quick_check",
            agents_consulted=[agent_type.value],
            routing_reasoning=f"Quick check focused on {focus}",
            cost=result.total_cost,
            tokens=result.total_tokens,
            execution_time_ms=execution_time
        )

    async def explain(
        self,
        topic: str,
        context: Optional[str] = None
    ) -> MaxwellResponse:
        """
        Get Maxwell's explanation of a writing topic.

        Args:
            topic: Writing topic to explain (e.g., "show vs tell", "pacing")
            context: Optional context from the manuscript

        Returns:
            MaxwellResponse with educational explanation
        """
        start_time = datetime.utcnow()

        prompt = f"""Explain the writing concept of "{topic}" in a warm, educational way.
        Include:
        - What it means
        - Why it matters for the reader experience
        - 1-2 concrete examples
        - Common pitfalls to avoid

        Keep it concise but thorough (2-3 paragraphs)."""

        if context:
            prompt += f"\n\nThe writer is working on text that includes:\n{context[:500]}"

        system_prompt = MAXWELL_PERSONA_PROMPT.format(context="")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        llm_config = LLMConfig(
            provider=LLMProvider(self.model_config.provider.value),
            model=self.model_config.model_name,
            temperature=0.7,
            max_tokens=1024,
            api_key=self.api_key
        )

        response = await llm_service.generate(llm_config, messages)

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MaxwellResponse(
            content=response.content,
            response_type="explanation",
            agents_consulted=[],
            routing_reasoning=f"Educational explanation of {topic}",
            cost=response.cost,
            tokens=response.usage.get("total_tokens", 0),
            execution_time_ms=execution_time
        )

    def _intent_to_tone(self, intent: QueryIntent) -> SynthesisTone:
        """Map query intent to synthesis tone."""
        tone_map = {
            QueryIntent.ANALYSIS: SynthesisTone.ENCOURAGING,
            QueryIntent.CONSISTENCY: SynthesisTone.DIRECT,
            QueryIntent.QUALITY: SynthesisTone.ENCOURAGING,
            QueryIntent.SPECIFIC: SynthesisTone.DIRECT,
            QueryIntent.BRAINSTORM: SynthesisTone.ENCOURAGING,
            QueryIntent.EXPLANATION: SynthesisTone.TEACHING
        }
        return tone_map.get(intent, SynthesisTone.ENCOURAGING)

    def clear_history(self):
        """Clear conversation history."""
        self._conversation_history = []

    def get_metrics(self) -> Dict[str, Any]:
        """Get accumulated metrics."""
        return {
            "total_cost": self._total_cost,
            "total_tokens": self._total_tokens,
            "conversation_length": len(self._conversation_history)
        }


def create_maxwell(
    api_key: str,
    user_id: str,
    model_config: Optional[ModelConfig] = None
) -> MaxwellUnified:
    """Factory function to create Maxwell."""
    return MaxwellUnified(api_key=api_key, user_id=user_id, model_config=model_config)
