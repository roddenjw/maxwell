"""
Smart Coach Agent for Maxwell

A conversational writing coach that can:
- Have natural conversations about the author's work
- Query Codex, Timeline, Outline, and Manuscript data
- Remember conversation context within sessions
- Provide personalized coaching based on author profile
- Track cost and token usage

Usage:
    coach = SmartCoachAgent(api_key="sk-...", user_id="user123")

    # Start or continue a session
    session = await coach.start_session(manuscript_id="ms456")

    # Send a message
    response = await coach.chat(
        session_id=session.id,
        message="Who is the main character?",
        context={"chapter_id": "ch789"}
    )
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

from langchain_core.messages import ToolMessage

from app.agents.base.agent_config import ModelConfig, ModelProvider, AgentType
from app.agents.base.context_loader import ContextLoader
from app.agents.tools import ALL_TOOLS
from app.services.llm_service import llm_service, LLMConfig, LLMProvider, calculate_cost
from app.database import SessionLocal
from app.models.agent import CoachSession, CoachMessage

logger = logging.getLogger(__name__)


@dataclass
class CoachResponse:
    """Response from the Smart Coach"""
    content: str
    tools_used: List[str] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    tokens: int = 0
    session_id: str = ""

    # New fields for agent integration
    agents_consulted: List[str] = field(default_factory=list)
    analysis_performed: bool = False
    synthesized_feedback: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "tools_used": self.tools_used,
            "tool_results": self.tool_results,
            "cost": self.cost,
            "tokens": self.tokens,
            "session_id": self.session_id,
            "agents_consulted": self.agents_consulted,
            "analysis_performed": self.analysis_performed,
            "synthesized_feedback": self.synthesized_feedback
        }


COACH_SYSTEM_PROMPT = """You are Maxwell, a friendly and knowledgeable writing coach embedded in a fiction writing IDE. Your role is to help authors with their creative writing by:

## Your Capabilities
1. **Answer questions about the story**: You have access to tools that let you query the Codex (character profiles, locations, items, lore), Timeline (events), Outline (story structure), and Manuscript (chapters, content).

2. **Provide craft guidance**: Offer advice on writing technique, story structure, character development, dialogue, pacing, and style.

3. **Support creative exploration**: Help brainstorm ideas, work through plot problems, develop characters, and explore "what if" scenarios.

4. **Track context**: Remember what we've discussed in this session and use manuscript context to give informed answers.

## Your Personality
- Warm, encouraging, and supportive - writers need motivation
- Curious and engaged with the author's work
- Teaching-focused: explain the "why" behind suggestions
- Direct but tactful when pointing out issues
- Celebrate what's working, not just what needs improvement

## Tool Usage
When the author asks about their story (characters, events, locations, plot), use your tools to look up accurate information rather than guessing. If a tool doesn't return helpful results, be honest and suggest the author may need to add that information to their Codex or Timeline.

## Response Style
- Keep responses conversational and concise
- Use the author's character/location names once you know them
- Offer specific, actionable suggestions when giving feedback
- Ask clarifying questions when needed
- Remember: you're a collaborator, not an authority

{context}"""


class SmartCoachAgent:
    """
    Conversational writing coach with memory and tool access.

    Maintains session-based conversations with persistent history.

    Now integrated with Maxwell's specialized agents - automatically
    routes analysis requests to Style, Continuity, Structure, and
    Voice agents, then synthesizes results into a unified response.
    """

    def __init__(
        self,
        api_key: str,
        user_id: str,
        model_config: Optional[ModelConfig] = None,
        enable_agent_routing: bool = True
    ):
        """
        Initialize the Smart Coach.

        Args:
            api_key: API key for LLM provider
            user_id: User ID for context and tracking
            model_config: Optional model configuration
            enable_agent_routing: Whether to route analysis requests to specialized agents
        """
        self.api_key = api_key
        self.user_id = user_id
        self.model_config = model_config or ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=2048
        )
        self._context_loader = ContextLoader()
        self._tools = ALL_TOOLS
        self._enable_agent_routing = enable_agent_routing

        # Lazy-loaded agent components (avoid circular imports)
        self._supervisor = None
        self._synthesizer = None
        self._orchestrator = None

    def _get_supervisor(self):
        """Lazy load the supervisor agent."""
        if self._supervisor is None:
            from app.agents.orchestrator.supervisor_agent import SupervisorAgent
            self._supervisor = SupervisorAgent(self.api_key, self.model_config)
        return self._supervisor

    def _get_synthesizer(self):
        """Lazy load the synthesizer."""
        if self._synthesizer is None:
            from app.agents.orchestrator.maxwell_synthesizer import MaxwellSynthesizer
            self._synthesizer = MaxwellSynthesizer(self.api_key, self.model_config)
        return self._synthesizer

    def _get_orchestrator(self, enabled_agents: Optional[List[AgentType]] = None):
        """Lazy load the orchestrator."""
        from app.agents.orchestrator.writing_assistant import WritingAssistantOrchestrator
        return WritingAssistantOrchestrator(
            self.api_key,
            self.model_config,
            enabled_agents=enabled_agents
        )

    def _should_invoke_agents(self, message: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if this message should trigger specialized agent analysis.

        Returns True if:
        - There's selected text to analyze, AND
        - The message asks for feedback/analysis
        """
        if not self._enable_agent_routing:
            return False

        # Need selected text to analyze
        if not context or not context.get("selected_text"):
            return False

        message_lower = message.lower()

        # Analysis trigger keywords
        analysis_triggers = [
            "analyze", "check", "review", "look at", "is this",
            "does this", "how is", "how's", "working", "consistent",
            "makes sense", "feel right", "sounds right", "believable",
            "authentic", "feedback", "what do you think", "critique"
        ]

        return any(trigger in message_lower for trigger in analysis_triggers)

    async def start_session(
        self,
        manuscript_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> CoachSession:
        """
        Start a new coaching session.

        Args:
            manuscript_id: Optional manuscript to focus on
            initial_context: Optional initial context (chapter_id, selected_text, etc.)
            title: Optional session title

        Returns:
            CoachSession instance
        """
        db = SessionLocal()
        try:
            session = CoachSession(
                user_id=self.user_id,
                manuscript_id=manuscript_id,
                title=title or "Coaching Session",
                initial_context=initial_context or {},
                status="active"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()

    async def get_session(self, session_id: str) -> Optional[CoachSession]:
        """Get an existing session by ID."""
        db = SessionLocal()
        try:
            return db.query(CoachSession).filter(
                CoachSession.id == session_id
            ).first()
        finally:
            db.close()

    async def list_sessions(
        self,
        manuscript_id: Optional[str] = None,
        limit: int = 20,
        include_archived: bool = False
    ) -> List[CoachSession]:
        """List coaching sessions for this user."""
        db = SessionLocal()
        try:
            query = db.query(CoachSession).filter(
                CoachSession.user_id == self.user_id
            )

            if manuscript_id:
                query = query.filter(CoachSession.manuscript_id == manuscript_id)

            if not include_archived:
                query = query.filter(CoachSession.status == "active")

            return query.order_by(
                CoachSession.updated_at.desc()
            ).limit(limit).all()
        finally:
            db.close()

    async def chat(
        self,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CoachResponse:
        """
        Send a message to the coach and get a response.

        Now with intelligent routing: if the message requests analysis
        of selected text, Maxwell automatically consults specialized
        agents and synthesizes their feedback into a unified response.

        Args:
            session_id: ID of the coaching session
            message: User's message
            context: Optional additional context (chapter_id, selected_text, etc.)

        Returns:
            CoachResponse with the assistant's reply
        """
        db = SessionLocal()
        try:
            # Get session
            session = db.query(CoachSession).filter(
                CoachSession.id == session_id
            ).first()

            if not session:
                return CoachResponse(
                    content="Session not found. Please start a new session.",
                    session_id=""
                )

            # Save user message
            user_message = CoachMessage(
                session_id=session_id,
                role="user",
                content=message
            )
            db.add(user_message)
            db.commit()

            # Check if this should route to specialized agents
            if self._should_invoke_agents(message, context):
                response = await self._chat_with_agent_analysis(
                    db, session, message, context
                )
            else:
                response = await self._chat_conversational(
                    db, session, message, context
                )

            # Update session with response
            response.session_id = session_id
            return response

        finally:
            db.close()

    async def _chat_with_agent_analysis(
        self,
        db,
        session: CoachSession,
        message: str,
        context: Dict[str, Any]
    ) -> CoachResponse:
        """
        Handle chat that requires specialized agent analysis.

        Routes to appropriate agents, runs analysis, synthesizes result.
        """
        selected_text = context.get("selected_text", "")

        # Route the query to determine which agents to use
        supervisor = self._get_supervisor()
        route = await supervisor.route_query(message, selected_text[:500])

        # Run targeted analysis with selected agents
        orchestrator = self._get_orchestrator(enabled_agents=route.agents)
        result = await orchestrator.analyze(
            text=selected_text,
            user_id=self.user_id,
            manuscript_id=session.manuscript_id or "",
            include_author_insights=True
        )

        # Synthesize into Maxwell's unified voice
        synthesizer = self._get_synthesizer()
        from app.agents.orchestrator.maxwell_synthesizer import SynthesisTone
        feedback = await synthesizer.synthesize(
            result.to_dict(),
            tone=SynthesisTone.ENCOURAGING,
            author_context=result.author_insights
        )

        # Save assistant message
        assistant_message = CoachMessage(
            session_id=str(session.id),
            role="assistant",
            content=feedback.narrative,
            tools_used=[a.value for a in route.agents],
            tool_results={"synthesis": feedback.to_dict()},
            cost=feedback.cost,
            tokens=feedback.tokens
        )
        db.add(assistant_message)

        # Update session stats
        session.message_count += 2
        session.total_cost += feedback.cost
        session.total_tokens += feedback.tokens
        session.last_message_at = datetime.utcnow()
        db.commit()

        return CoachResponse(
            content=feedback.narrative,
            tools_used=[a.value for a in route.agents],
            tool_results={},
            cost=feedback.cost,
            tokens=feedback.tokens,
            agents_consulted=[a.value for a in route.agents],
            analysis_performed=True,
            synthesized_feedback=feedback.to_dict()
        )

    async def _chat_conversational(
        self,
        db,
        session: CoachSession,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> CoachResponse:
        """
        Handle conversational chat with real LLM tool calling.

        Uses model.bind_tools() so the LLM can dynamically invoke
        query_entities, query_timeline, etc. based on user questions.
        """
        # Build conversation history
        messages = await self._build_messages(db, session, message, context)

        llm_config = self._build_llm_config()
        max_iterations = 3
        tools_used = []
        tool_results = {}

        try:
            model = llm_service.get_langchain_model(llm_config)
            model_with_tools = model.bind_tools(self._tools)

            # Convert to LangChain messages
            lc_messages = llm_service.convert_messages(messages)

            total_prompt_tokens = 0
            total_completion_tokens = 0

            for iteration in range(max_iterations + 1):
                response = await model_with_tools.ainvoke(lc_messages)

                # Accumulate usage
                if hasattr(response, "response_metadata"):
                    meta = response.response_metadata
                    usage = meta.get("usage") or meta.get("token_usage") or {}
                    total_prompt_tokens += usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
                    total_completion_tokens += usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)

                # If no tool calls, we're done
                if not hasattr(response, "tool_calls") or not response.tool_calls:
                    break

                if iteration >= max_iterations:
                    break

                # Execute tool calls
                lc_messages.append(response)

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call.get("id", tool_name)

                    logger.info("Coach executing tool: %s", tool_name)

                    matching_tool = next(
                        (t for t in self._tools if t.name == tool_name), None
                    )

                    if matching_tool:
                        try:
                            result = matching_tool.invoke(tool_args)
                            if not isinstance(result, str):
                                result = json.dumps(result, default=str)
                            tools_used.append(tool_name)
                            tool_results[tool_name] = result[:500]  # Truncate for storage
                        except Exception as tool_err:
                            logger.warning("Tool %s error: %s", tool_name, tool_err)
                            result = f"Error executing {tool_name}: {str(tool_err)}"
                    else:
                        result = f"Tool '{tool_name}' not found"

                    lc_messages.append(
                        ToolMessage(content=result, tool_call_id=tool_id)
                    )

            response_content = response.content if hasattr(response, "content") else str(response)
            total_tokens = total_prompt_tokens + total_completion_tokens
            cost = calculate_cost(
                llm_config.model, total_prompt_tokens, total_completion_tokens
            )

        except Exception as e:
            # Fallback: direct call without tools
            logger.warning("Tool-calling failed (%s), falling back to direct call", e)
            llm_response = await llm_service.generate(llm_config, messages)
            response_content = llm_response.content
            cost = llm_response.cost
            total_tokens = llm_response.usage.get("total_tokens", 0)

        # Save assistant message
        assistant_message = CoachMessage(
            session_id=str(session.id),
            role="assistant",
            content=response_content,
            tools_used=tools_used,
            tool_results=tool_results,
            cost=cost,
            tokens=total_tokens
        )
        db.add(assistant_message)

        # Update session stats
        session.message_count += 2
        session.total_cost += cost
        session.total_tokens += total_tokens
        session.last_message_at = datetime.utcnow()
        db.commit()

        return CoachResponse(
            content=response_content,
            tools_used=tools_used,
            tool_results=tool_results,
            cost=cost,
            tokens=total_tokens,
            agents_consulted=[],
            analysis_performed=False
        )

    async def _build_messages(
        self,
        db,
        session: CoachSession,
        current_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Build the messages list for the LLM call."""
        messages = []

        # Build context string
        context_parts = []

        # Add manuscript context if available
        if session.manuscript_id:
            try:
                agent_context = self._context_loader.load_full_context(
                    user_id=self.user_id,
                    manuscript_id=session.manuscript_id,
                    author_weight=0.5,
                    world_weight=0.3,
                    series_weight=0.2,
                    manuscript_weight=0.8
                )
                context_parts.append(agent_context.to_prompt_context(max_tokens=2000))
            except Exception:
                pass  # Context loading is optional

        # Add session initial context
        if session.initial_context:
            context_parts.append(f"Session started with context: {json.dumps(session.initial_context)}")

        # Add current turn context
        if context:
            if context.get("selected_text"):
                context_parts.append(f"Currently selected text:\n---\n{context['selected_text']}\n---")
            if context.get("chapter_title"):
                context_parts.append(f"Current chapter: {context['chapter_title']}")

        # Note: tool descriptions are NOT added to prompt when using bind_tools().
        # The LLM receives tool schemas natively via the API.

        # Build system message
        context_str = "\n\n".join(context_parts) if context_parts else ""
        system_prompt = COACH_SYSTEM_PROMPT.format(context=context_str)
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history (last 20 messages)
        history = db.query(CoachMessage).filter(
            CoachMessage.session_id == session.id
        ).order_by(
            CoachMessage.created_at.asc()
        ).limit(20).all()

        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Current message is already in history since we saved it

        return messages

    def _build_llm_config(self) -> LLMConfig:
        """Build LLM configuration."""
        return LLMConfig(
            provider=LLMProvider(self.model_config.provider.value),
            model=self.model_config.model_name,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            api_key=self.api_key
        )

    async def archive_session(self, session_id: str) -> bool:
        """Archive a coaching session."""
        db = SessionLocal()
        try:
            session = db.query(CoachSession).filter(
                CoachSession.id == session_id,
                CoachSession.user_id == self.user_id
            ).first()

            if session:
                session.status = "archived"
                db.commit()
                return True
            return False
        finally:
            db.close()

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages from a session."""
        db = SessionLocal()
        try:
            messages = db.query(CoachMessage).filter(
                CoachMessage.session_id == session_id
            ).order_by(
                CoachMessage.created_at.asc()
            ).limit(limit).all()

            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tools_used": msg.tools_used,
                    "cost": msg.cost,
                    "tokens": msg.tokens,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        finally:
            db.close()


def create_smart_coach(
    api_key: str,
    user_id: str,
    model_config: Optional[ModelConfig] = None
) -> SmartCoachAgent:
    """Factory function to create a Smart Coach agent."""
    return SmartCoachAgent(
        api_key=api_key,
        user_id=user_id,
        model_config=model_config
    )
