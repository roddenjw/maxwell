"""
Tests for Base Agent Class
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import (
    AgentConfig, AgentType, ModelConfig, ModelProvider
)
from app.services.llm_service import LLMResponse, LLMProvider


class TestAgentResult:
    """Tests for AgentResult dataclass"""

    def test_agent_result_creation(self):
        """Test basic AgentResult creation"""
        result = AgentResult(
            agent_type=AgentType.STYLE,
            success=True,
            recommendations=[{"type": "style", "text": "test"}],
            issues=[],
            teaching_points=["Learn about pacing"],
            raw_response="test response"
        )

        assert result.agent_type == AgentType.STYLE
        assert result.success is True
        assert len(result.recommendations) == 1
        assert len(result.issues) == 0
        assert len(result.teaching_points) == 1

    def test_agent_result_defaults(self):
        """Test AgentResult default values"""
        result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=False
        )

        assert result.recommendations == []
        assert result.issues == []
        assert result.teaching_points == []
        assert result.raw_response is None
        assert result.usage == {}
        assert result.cost == 0.0
        assert result.execution_time_ms == 0

    def test_agent_result_to_dict(self):
        """Test AgentResult serialization"""
        result = AgentResult(
            agent_type=AgentType.VOICE,
            success=True,
            recommendations=[{"type": "dialogue", "severity": "medium", "text": "Vary sentence length"}],
            issues=[{"type": "voice", "severity": "high", "description": "Inconsistent tone"}],
            teaching_points=["Character voice should be distinct"],
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost=0.001,
            execution_time_ms=1500
        )

        data = result.to_dict()

        assert data["agent_type"] == "voice"
        assert data["success"] is True
        assert len(data["recommendations"]) == 1
        assert len(data["issues"]) == 1
        assert data["usage"]["total_tokens"] == 150
        assert data["cost"] == 0.001
        assert data["execution_time_ms"] == 1500


class ConcreteTestAgent(BaseMaxwellAgent):
    """Concrete implementation for testing the abstract base class"""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.STYLE

    @property
    def system_prompt(self) -> str:
        return "You are a style analysis expert."

    def _get_tools(self):
        return []  # No tools for basic test


class TestBaseMaxwellAgent:
    """Tests for BaseMaxwellAgent"""

    @pytest.fixture
    def test_config(self):
        """Create a test agent configuration"""
        model_config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            max_tokens=4096,
            temperature=0.7
        )
        return AgentConfig(
            agent_type=AgentType.STYLE,
            model_config=model_config,
            include_teaching=True,
            response_format="json"
        )

    @pytest.fixture
    def test_agent(self, test_config):
        """Create a test agent instance"""
        return ConcreteTestAgent(
            config=test_config,
            api_key="test-api-key"
        )

    def test_agent_initialization(self, test_agent, test_config):
        """Test agent initializes correctly"""
        assert test_agent.config == test_config
        assert test_agent.api_key == "test-api-key"
        assert test_agent._total_cost == 0.0
        assert test_agent._total_tokens == 0

    def test_agent_type_property(self, test_agent):
        """Test agent type is correctly returned"""
        assert test_agent.agent_type == AgentType.STYLE

    def test_system_prompt_property(self, test_agent):
        """Test system prompt is correctly returned"""
        assert "style analysis expert" in test_agent.system_prompt.lower()

    def test_get_tools_empty(self, test_agent):
        """Test get_tools returns empty list for basic agent"""
        assert test_agent.get_tools() == []

    def test_get_tools_with_override(self, test_config):
        """Test tools can be overridden in constructor"""
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        agent = ConcreteTestAgent(
            config=test_config,
            api_key="test-key",
            tools=[mock_tool]
        )

        assert agent.get_tools() == [mock_tool]

    def test_format_system_prompt_basic(self, test_agent):
        """Test basic system prompt formatting"""
        prompt = test_agent._format_system_prompt()

        assert "style analysis expert" in prompt.lower()
        assert "Teaching Philosophy" in prompt
        assert "Response Format" in prompt

    def test_format_system_prompt_without_teaching(self, test_config):
        """Test system prompt without teaching mode"""
        test_config.include_teaching = False
        agent = ConcreteTestAgent(config=test_config, api_key="test-key")

        prompt = agent._format_system_prompt()

        assert "Teaching Philosophy" not in prompt

    def test_format_system_prompt_with_custom_prompt(self, test_config):
        """Test system prompt with custom addition"""
        test_config.custom_system_prompt = "Focus on dialogue quality."
        agent = ConcreteTestAgent(config=test_config, api_key="test-key")

        prompt = agent._format_system_prompt()

        assert "Focus on dialogue quality." in prompt

    def test_format_system_prompt_text_format(self, test_config):
        """Test system prompt without JSON format instruction"""
        test_config.response_format = "text"
        agent = ConcreteTestAgent(config=test_config, api_key="test-key")

        prompt = agent._format_system_prompt()

        assert "Respond with valid JSON" not in prompt

    def test_parse_response_json_success(self, test_agent):
        """Test parsing valid JSON response"""
        json_content = json.dumps({
            "recommendations": [
                {"type": "style", "severity": "medium", "text": "Vary sentence length", "teaching_point": "Rhythm matters"}
            ],
            "issues": [
                {"type": "consistency", "severity": "high", "description": "Timeline conflict"}
            ],
            "praise": [
                {"aspect": "dialogue", "text": "Great voice"}
            ],
            "overall_assessment": "Good work overall"
        })

        result = test_agent._parse_response(
            content=json_content,
            usage={"total_tokens": 150},
            cost=0.001,
            execution_time_ms=1000
        )

        assert result.success is True
        assert len(result.recommendations) == 2  # Including praise
        assert len(result.issues) == 1
        assert "Rhythm matters" in result.teaching_points
        assert result.cost == 0.001

    def test_parse_response_json_failure(self, test_agent):
        """Test parsing invalid JSON falls back to text"""
        invalid_content = "This is not JSON but is useful feedback."

        result = test_agent._parse_response(
            content=invalid_content,
            usage={"total_tokens": 50},
            cost=0.0005,
            execution_time_ms=500
        )

        assert result.success is True
        assert len(result.recommendations) == 1
        assert result.recommendations[0]["text"] == invalid_content
        assert result.recommendations[0]["type"] == "general"

    def test_parse_response_text_format(self, test_config):
        """Test parsing text format response"""
        test_config.response_format = "text"
        agent = ConcreteTestAgent(config=test_config, api_key="test-key")

        result = agent._parse_response(
            content="Your writing shows great potential.",
            usage={"total_tokens": 100},
            cost=0.0003,
            execution_time_ms=800
        )

        assert result.success is True
        assert result.recommendations[0]["text"] == "Your writing shows great potential."

    @pytest.mark.asyncio
    async def test_analyze_success(self, test_agent, mock_llm_response):
        """Test successful analysis"""
        with patch.object(test_agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            # Setup mocks
            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)

            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await test_agent.analyze(
                text="Test text for analysis",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is True
            assert result.agent_type == AgentType.STYLE

    @pytest.mark.asyncio
    async def test_analyze_error_handling(self, test_agent):
        """Test analysis handles errors gracefully"""
        with patch.object(test_agent, '_context_loader') as mock_loader:
            mock_loader.load_full_context.side_effect = Exception("Database error")

            result = await test_agent.analyze(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is False
            assert len(result.issues) == 1
            assert "Database error" in result.issues[0]["description"]

    @pytest.mark.asyncio
    async def test_chat_basic(self, test_agent, mock_llm_response_text):
        """Test basic chat interaction"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_service.generate = AsyncMock(return_value=mock_llm_response_text)

            response = await test_agent.chat(
                message="How can I improve my dialogue?",
                history=[]
            )

            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_history(self, test_agent, mock_llm_response_text):
        """Test chat with conversation history"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_service.generate = AsyncMock(return_value=mock_llm_response_text)

            history = [
                {"role": "user", "content": "What is show don't tell?"},
                {"role": "assistant", "content": "It means demonstrating through action..."}
            ]

            response = await test_agent.chat(
                message="Can you give an example?",
                history=history
            )

            # Verify history was passed
            call_args = mock_service.generate.call_args
            messages = call_args[0][1]  # Second positional arg
            assert len(messages) == 4  # system + 2 history + current

    def test_cost_tracking(self, test_agent):
        """Test cost and token tracking"""
        assert test_agent.get_total_cost() == 0.0
        assert test_agent.get_total_tokens() == 0

        # Simulate tracking
        test_agent._total_cost = 0.005
        test_agent._total_tokens = 1500

        assert test_agent.get_total_cost() == 0.005
        assert test_agent.get_total_tokens() == 1500

    def test_reset_tracking(self, test_agent):
        """Test resetting cost tracking"""
        test_agent._total_cost = 0.01
        test_agent._total_tokens = 3000

        test_agent.reset_tracking()

        assert test_agent.get_total_cost() == 0.0
        assert test_agent.get_total_tokens() == 0

    @pytest.mark.asyncio
    async def test_run_direct(self, test_agent, mock_llm_response):
        """Test direct LLM call"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            messages = [
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "Hello"}
            ]

            result = await test_agent._run_direct(messages)

            assert result == mock_llm_response
            mock_service.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_tools_real_invocation(self, test_agent, mock_llm_response):
        """Test _run_with_tools executes tool calls from the LLM"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            # Create a mock model that returns tool_calls on first invoke, then final on second
            mock_model = AsyncMock()
            mock_model_with_tools = AsyncMock()

            # First call: LLM asks to use a tool
            first_response = MagicMock()
            first_response.tool_calls = [
                {"name": "query_entities", "args": {"manuscript_id": "ms1"}, "id": "call_1"}
            ]
            first_response.content = ""
            first_response.response_metadata = {"usage": {"prompt_tokens": 100, "completion_tokens": 20}}

            # Second call: LLM returns final answer
            second_response = MagicMock()
            second_response.tool_calls = []
            second_response.content = "Based on the entities, here is my analysis."
            second_response.response_metadata = {"usage": {"prompt_tokens": 200, "completion_tokens": 50}}

            mock_model_with_tools.ainvoke = AsyncMock(
                side_effect=[first_response, second_response]
            )

            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)
            mock_service.get_langchain_model = MagicMock(return_value=mock_model)
            mock_service.convert_messages = MagicMock(return_value=[])

            # Create mock tool
            mock_tool = MagicMock()
            mock_tool.name = "query_entities"
            mock_tool.invoke = MagicMock(return_value="Found 3 entities: Alice, Bob, Carol")

            messages = [
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "Who are the characters?"}
            ]

            result = await test_agent._run_with_tools(messages, [mock_tool])

            # Tool was actually invoked
            mock_tool.invoke.assert_called_once_with({"manuscript_id": "ms1"})

            # Final response content
            assert result.content == "Based on the entities, here is my analysis."
            assert result.usage["total_tokens"] == 370

    @pytest.mark.asyncio
    async def test_run_with_tools_no_tool_calls(self, test_agent):
        """Test _run_with_tools when LLM returns no tool calls"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_model = AsyncMock()
            mock_model_with_tools = AsyncMock()

            response = MagicMock()
            response.tool_calls = []
            response.content = "Here is my direct answer."
            response.response_metadata = {"usage": {"prompt_tokens": 50, "completion_tokens": 30}}

            mock_model_with_tools.ainvoke = AsyncMock(return_value=response)
            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)
            mock_service.get_langchain_model = MagicMock(return_value=mock_model)
            mock_service.convert_messages = MagicMock(return_value=[])

            messages = [
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "What is show don't tell?"}
            ]

            result = await test_agent._run_with_tools(messages, [])

            assert result.content == "Here is my direct answer."

    @pytest.mark.asyncio
    async def test_run_with_tools_max_iterations(self, test_agent):
        """Test _run_with_tools respects max_tool_iterations"""
        test_agent.config.max_tool_iterations = 1

        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_model = AsyncMock()
            mock_model_with_tools = AsyncMock()

            # LLM keeps requesting tools on every call
            tool_response = MagicMock()
            tool_response.tool_calls = [
                {"name": "query_entities", "args": {"manuscript_id": "ms1"}, "id": "call_1"}
            ]
            tool_response.content = "I need more data..."
            tool_response.response_metadata = {"usage": {"prompt_tokens": 50, "completion_tokens": 20}}

            mock_model_with_tools.ainvoke = AsyncMock(return_value=tool_response)
            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)
            mock_service.get_langchain_model = MagicMock(return_value=mock_model)
            mock_service.convert_messages = MagicMock(return_value=[])

            mock_tool = MagicMock()
            mock_tool.name = "query_entities"
            mock_tool.invoke = MagicMock(return_value="entities data")

            messages = [
                {"role": "system", "content": "Test"},
                {"role": "user", "content": "Test"}
            ]

            result = await test_agent._run_with_tools(messages, [mock_tool])

            # Should have called ainvoke exactly 2 times (1 + max_iterations)
            assert mock_model_with_tools.ainvoke.call_count == 2
            # Tool executed once before hitting max
            assert mock_tool.invoke.call_count == 1

    @pytest.mark.asyncio
    async def test_run_with_tools_tool_error(self, test_agent):
        """Test _run_with_tools handles tool execution errors"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_model = AsyncMock()
            mock_model_with_tools = AsyncMock()

            # First call: tool request
            first_response = MagicMock()
            first_response.tool_calls = [
                {"name": "query_entities", "args": {"manuscript_id": "bad"}, "id": "call_1"}
            ]
            first_response.content = ""
            first_response.response_metadata = {"usage": {"prompt_tokens": 50, "completion_tokens": 20}}

            # Second call: final response
            second_response = MagicMock()
            second_response.tool_calls = []
            second_response.content = "Sorry, I couldn't retrieve the data."
            second_response.response_metadata = {"usage": {"prompt_tokens": 100, "completion_tokens": 30}}

            mock_model_with_tools.ainvoke = AsyncMock(
                side_effect=[first_response, second_response]
            )
            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)
            mock_service.get_langchain_model = MagicMock(return_value=mock_model)
            mock_service.convert_messages = MagicMock(return_value=[])

            # Tool that raises
            mock_tool = MagicMock()
            mock_tool.name = "query_entities"
            mock_tool.invoke = MagicMock(side_effect=Exception("DB connection failed"))

            messages = [
                {"role": "system", "content": "Test"},
                {"role": "user", "content": "Test"}
            ]

            result = await test_agent._run_with_tools(messages, [mock_tool])

            # Should still get a response even though tool errored
            assert result.content == "Sorry, I couldn't retrieve the data."

    @pytest.mark.asyncio
    async def test_run_with_tools_fallback(self, test_agent, mock_llm_response):
        """Test fallback when bind_tools() fails"""
        with patch('app.agents.base.agent_base.llm_service') as mock_service:
            mock_model = MagicMock()
            mock_model.bind_tools = MagicMock(side_effect=NotImplementedError("No tool support"))
            mock_service.get_langchain_model = MagicMock(return_value=mock_model)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            mock_tool = MagicMock()
            mock_tool.name = "query_entities"
            mock_tool.description = "Query codex entities"

            messages = [
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "Hello"}
            ]

            result = await test_agent._run_with_tools(messages, [mock_tool])

            # Falls back to direct call with tool descriptions in prompt
            assert result == mock_llm_response
            mock_service.generate.assert_called_once()
