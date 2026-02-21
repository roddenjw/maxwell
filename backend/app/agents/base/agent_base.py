"""
Base Agent Class for Maxwell's LangChain Framework

All specialized agents inherit from BaseMaxwellAgent which provides:
- Hierarchical context loading
- LLM abstraction
- Tool management
- Cost tracking
- Teaching-first responses
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json

import logging

from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from app.agents.base.agent_config import AgentConfig, AgentType, ModelProvider
from app.agents.base.context_loader import ContextLoader, AgentContext
from app.services.llm_service import llm_service, LLMConfig, LLMResponse, LLMProvider, calculate_cost
from app.services.privacy_middleware import PrivacyMiddleware, PrivacyBlockedException, check_ai_allowed
from app.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an agent analysis"""
    agent_type: AgentType
    success: bool
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    teaching_points: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_type": self.agent_type.value,
            "success": self.success,
            "recommendations": self.recommendations,
            "issues": self.issues,
            "teaching_points": self.teaching_points,
            "usage": self.usage,
            "cost": self.cost,
            "execution_time_ms": self.execution_time_ms
        }


class BaseMaxwellAgent(ABC):
    """
    Base class for all Maxwell agents

    Provides:
    - Hierarchical context loading
    - LLM abstraction (multiple providers)
    - Tool management
    - Cost tracking
    - Teaching-first response formatting

    Usage:
        class StyleAgent(BaseMaxwellAgent):
            @property
            def agent_type(self) -> AgentType:
                return AgentType.STYLE

            @property
            def system_prompt(self) -> str:
                return "You are a writing style expert..."

            def _get_tools(self) -> List[BaseTool]:
                return [query_manuscript_stats, query_author_profile]

        agent = StyleAgent(config, api_key="sk-...")
        result = await agent.analyze(text, manuscript_id="...")
    """

    def __init__(
        self,
        config: AgentConfig,
        api_key: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """
        Initialize the agent

        Args:
            config: Agent configuration
            api_key: API key for the LLM provider
            tools: Optional list of LangChain tools (overrides config)
        """
        self.config = config
        self.api_key = api_key
        self._tools = tools
        self._context_loader = ContextLoader()
        self._total_cost = 0.0
        self._total_tokens = 0

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def _get_tools(self) -> List[BaseTool]:
        """Return the list of tools available to this agent"""
        pass

    def get_tools(self) -> List[BaseTool]:
        """Get tools, with override support"""
        if self._tools is not None:
            return self._tools
        return self._get_tools()

    def _build_llm_config(self) -> LLMConfig:
        """Build LLM configuration from agent config"""
        model_config = self.config.model_config
        return LLMConfig(
            provider=LLMProvider(model_config.provider.value),
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            response_format=self.config.response_format,
            api_key=self.api_key,
            model_path=model_config.model_path,
            n_ctx=model_config.n_ctx,
            n_gpu_layers=model_config.n_gpu_layers,
        )

    async def load_context(
        self,
        user_id: str,
        manuscript_id: str,
        current_chapter_id: Optional[str] = None
    ) -> AgentContext:
        """Load hierarchical context based on agent config weights"""
        return self._context_loader.load_full_context(
            user_id=user_id,
            manuscript_id=manuscript_id,
            current_chapter_id=current_chapter_id,
            author_weight=self.config.author_context_weight,
            world_weight=self.config.world_context_weight,
            series_weight=self.config.series_context_weight,
            manuscript_weight=self.config.manuscript_context_weight
        )

    def _format_system_prompt(self, context: Optional[AgentContext] = None) -> str:
        """Format the full system prompt with context"""
        parts = [self.system_prompt]

        # Add custom prompt if configured
        if self.config.custom_system_prompt:
            parts.append(f"\n\n{self.config.custom_system_prompt}")

        # Add teaching instruction if enabled
        if self.config.include_teaching:
            parts.append("""

## Teaching Philosophy
You are a writing mentor, not just an analyzer. For each issue or suggestion:
1. Explain WHY it matters for the reader experience
2. Provide 2-3 concrete alternatives (not prescriptive commands)
3. Reference established writing craft principles when relevant
4. Be encouraging - highlight what works well too""")

        # Add context if provided
        if context:
            context_text = context.to_prompt_context(self.config.max_context_tokens)
            parts.append(f"\n\n{context_text}")

        # Add response format instruction
        if self.config.response_format == "json":
            parts.append("""

## Response Format
Respond with valid JSON matching this schema:
{
  "recommendations": [
    {
      "type": "string",
      "severity": "high|medium|low",
      "text": "string",
      "suggestion": "string",
      "teaching_point": "string"
    }
  ],
  "issues": [
    {
      "type": "string",
      "severity": "high|medium|low",
      "description": "string",
      "location": "string (optional)",
      "suggestion": "string"
    }
  ],
  "praise": [
    {
      "aspect": "string",
      "text": "string"
    }
  ],
  "overall_assessment": "string"
}""")

        return "\n".join(parts)

    async def analyze(
        self,
        text: str,
        user_id: str,
        manuscript_id: str,
        current_chapter_id: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> AgentResult:
        """
        Analyze text and return recommendations

        Args:
            text: The text to analyze
            user_id: User ID for author context
            manuscript_id: Manuscript ID for context
            current_chapter_id: Optional current chapter
            additional_context: Optional additional context to include

        Returns:
            AgentResult with recommendations, issues, and teaching points
        """
        start_time = datetime.utcnow()

        try:
            # Check if AI assistance is enabled for this manuscript
            # (Training is always blocked by default - this just checks if AI can help at all)
            db = next(get_db())
            try:
                privacy_result = await check_ai_allowed(db, manuscript_id)

                if not privacy_result.allowed:
                    execution_time = int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    )
                    return AgentResult(
                        agent_type=self.agent_type,
                        success=False,
                        issues=[{
                            "type": "ai_disabled",
                            "severity": "info",
                            "description": privacy_result.reason or "AI assistance is disabled for this manuscript"
                        }],
                        execution_time_ms=execution_time
                    )
            finally:
                db.close()

            # Load context
            context = await self.load_context(
                user_id=user_id,
                manuscript_id=manuscript_id,
                current_chapter_id=current_chapter_id
            )

            # Build prompt
            system_prompt = self._format_system_prompt(context)

            # Build user message
            user_content = f"Please analyze the following text:\n\n---\n{text}\n---"
            if additional_context:
                user_content += f"\n\nAdditional context:\n{additional_context}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # Check if we have tools to use
            tools = self.get_tools()

            if tools:
                # Use agent executor with tools
                result = await self._run_with_tools(messages, tools)
            else:
                # Direct LLM call
                result = await self._run_direct(messages)

            # Calculate execution time
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            # Update totals
            self._total_cost += result.cost
            self._total_tokens += result.usage.get("total_tokens", 0)

            # Parse response
            return self._parse_response(
                result.content,
                result.usage,
                result.cost,
                execution_time
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                issues=[{
                    "type": "error",
                    "severity": "high",
                    "description": str(e)
                }],
                execution_time_ms=execution_time
            )

    async def _run_direct(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Run direct LLM call without tools"""
        config = self._build_llm_config()
        return await llm_service.generate(config, messages)

    async def _run_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[BaseTool]
    ) -> LLMResponse:
        """
        Run agent with real LangChain tool calling.

        Uses model.bind_tools() + iterative tool-call loop:
        1. Send messages to LLM with tools bound
        2. If LLM returns tool_calls, execute each tool and append ToolMessage
        3. Re-invoke until no more tool calls or max_tool_iterations reached
        4. Falls back to text-in-prompt approach if bind_tools() isn't supported
        """
        config = self._build_llm_config()
        max_iterations = self.config.max_tool_iterations

        try:
            model = llm_service.get_langchain_model(config)
            model_with_tools = model.bind_tools(tools)
        except Exception as e:
            logger.warning(
                "bind_tools() failed (%s), falling back to text-in-prompt approach", e
            )
            return await self._run_with_tools_fallback(messages, tools)

        # Convert dict messages to LangChain message objects
        lc_messages = llm_service.convert_messages(messages)

        total_prompt_tokens = 0
        total_completion_tokens = 0

        for iteration in range(max_iterations + 1):
            response = await model_with_tools.ainvoke(lc_messages)

            # Accumulate usage from response metadata
            if hasattr(response, "response_metadata"):
                meta = response.response_metadata
                usage = meta.get("usage") or meta.get("token_usage") or {}
                total_prompt_tokens += usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)

            # If no tool calls, we're done
            if not hasattr(response, "tool_calls") or not response.tool_calls:
                break

            # Don't execute tools on the last allowed iteration
            if iteration >= max_iterations:
                logger.info("Max tool iterations (%d) reached, returning last response", max_iterations)
                break

            # Execute each tool call
            lc_messages.append(response)  # Append the AIMessage with tool_calls

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call.get("id", tool_name)

                logger.info("Executing tool: %s with args: %s", tool_name, tool_args)

                # Find the matching tool
                matching_tool = next(
                    (t for t in tools if t.name == tool_name), None
                )

                if matching_tool:
                    try:
                        tool_result = matching_tool.invoke(tool_args)
                        # Convert non-string results to string
                        if not isinstance(tool_result, str):
                            tool_result = json.dumps(tool_result, default=str)
                    except Exception as tool_err:
                        logger.warning("Tool %s raised error: %s", tool_name, tool_err)
                        tool_result = f"Error executing {tool_name}: {str(tool_err)}"
                else:
                    tool_result = f"Tool '{tool_name}' not found"

                lc_messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_id)
                )

        # Build final LLMResponse
        content = response.content if hasattr(response, "content") else str(response)
        total_tokens = total_prompt_tokens + total_completion_tokens
        cost = calculate_cost(
            config.model, total_prompt_tokens, total_completion_tokens
        )

        return LLMResponse(
            content=content,
            model=config.model,
            provider=LLMProvider(config.provider.value),
            usage={
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
            },
            cost=cost,
            raw_response=response,
        )

    async def _run_with_tools_fallback(
        self,
        messages: List[Dict[str, str]],
        tools: List[BaseTool]
    ) -> LLMResponse:
        """
        Fallback: append tool descriptions as text in system prompt.
        Used when the model doesn't support bind_tools().
        """
        tool_context = []
        for tool in tools[:5]:
            tool_context.append(f"- **{tool.name}**: {tool.description}")

        if tool_context:
            tool_info = "\n\n## Available Tools\n" + "\n".join(tool_context)
            messages[0]["content"] += tool_info

        return await self._run_direct(messages)

    def _parse_response(
        self,
        content: str,
        usage: Dict[str, int],
        cost: float,
        execution_time_ms: int
    ) -> AgentResult:
        """Parse LLM response into AgentResult"""
        recommendations = []
        issues = []
        teaching_points = []

        if self.config.response_format == "json":
            try:
                # Parse JSON response
                data = json.loads(content)
                recommendations = data.get("recommendations", [])
                issues = data.get("issues", [])

                # Extract teaching points
                for rec in recommendations:
                    if rec.get("teaching_point"):
                        teaching_points.append(rec["teaching_point"])

                # Add praise as positive recommendations
                for praise in data.get("praise", []):
                    recommendations.append({
                        "type": "praise",
                        "severity": "positive",
                        "text": praise.get("text", ""),
                        "aspect": praise.get("aspect", "")
                    })

            except json.JSONDecodeError:
                # Fallback: treat as plain text
                recommendations.append({
                    "type": "general",
                    "severity": "medium",
                    "text": content
                })
        else:
            # Plain text response
            recommendations.append({
                "type": "general",
                "severity": "medium",
                "text": content
            })

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            recommendations=recommendations,
            issues=issues,
            teaching_points=teaching_points,
            raw_response=content,
            usage=usage,
            cost=cost,
            execution_time_ms=execution_time_ms
        )

    async def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[AgentContext] = None
    ) -> str:
        """
        Have a conversation with the agent

        Args:
            message: User message
            history: Optional conversation history
            context: Optional pre-loaded context

        Returns:
            Agent response text
        """
        # Build messages
        system_prompt = self._format_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]

        # Add history
        if history:
            messages.extend(history)

        # Add current message
        messages.append({"role": "user", "content": message})

        # Get response
        config = self._build_llm_config()
        config.response_format = None  # Text response for chat
        response = await llm_service.generate(config, messages)

        # Track costs
        self._total_cost += response.cost
        self._total_tokens += response.usage.get("total_tokens", 0)

        return response.content

    def get_total_cost(self) -> float:
        """Get total cost for all calls made by this agent"""
        return self._total_cost

    def get_total_tokens(self) -> int:
        """Get total tokens used by this agent"""
        return self._total_tokens

    def reset_tracking(self):
        """Reset cost and token tracking"""
        self._total_cost = 0.0
        self._total_tokens = 0
