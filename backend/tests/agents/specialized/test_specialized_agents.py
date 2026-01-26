"""
Tests for Specialized Agents

Tests for: StyleAgent, ContinuityAgent, StructureAgent, VoiceAgent
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base.agent_config import AgentType, AgentConfig, ModelConfig, ModelProvider
from app.agents.specialized.style_agent import StyleAgent, create_style_agent
from app.agents.specialized.continuity_agent import ContinuityAgent, create_continuity_agent
from app.agents.specialized.structure_agent import StructureAgent, create_structure_agent
from app.agents.specialized.voice_agent import VoiceAgent, create_voice_agent
from app.services.llm_service import LLMResponse, LLMProvider


@pytest.fixture
def default_config():
    """Create a default agent configuration"""
    model_config = ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0.7
    )
    return model_config


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response"""
    return LLMResponse(
        content=json.dumps({
            "recommendations": [
                {"type": "style", "severity": "medium", "text": "Consider varying sentence length."}
            ],
            "issues": [],
            "praise": [{"aspect": "dialogue", "text": "Strong character voices."}],
            "overall_assessment": "Good work."
        }),
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={"prompt_tokens": 300, "completion_tokens": 100, "total_tokens": 400},
        cost=0.0005
    )


class TestStyleAgent:
    """Tests for StyleAgent"""

    def test_style_agent_type(self):
        """Test StyleAgent returns correct agent type"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)
        agent = StyleAgent(config=config, api_key="test-key")

        assert agent.agent_type == AgentType.STYLE

    def test_style_agent_system_prompt(self):
        """Test StyleAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)
        agent = StyleAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "style" in prompt
        assert "prose" in prompt or "writing" in prompt
        assert "show" in prompt or "tell" in prompt

    def test_style_agent_tools(self):
        """Test StyleAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)
        agent = StyleAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_author_profile" in tool_names
        assert "query_feedback_history" in tool_names

    def test_create_style_agent_factory(self):
        """Test create_style_agent factory function"""
        agent = create_style_agent(api_key="test-key")

        assert isinstance(agent, StyleAgent)
        assert agent.agent_type == AgentType.STYLE

    def test_create_style_agent_with_custom_config(self):
        """Test create_style_agent with custom configuration"""
        custom_config = AgentConfig.for_agent_type(
            AgentType.STYLE,
            include_teaching=False,
            max_context_tokens=4000
        )

        agent = create_style_agent(api_key="test-key", config=custom_config)

        assert agent.config.include_teaching is False
        assert agent.config.max_context_tokens == 4000

    @pytest.mark.asyncio
    async def test_style_agent_analyze(self, mock_llm_response):
        """Test StyleAgent analyze method"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)
        agent = StyleAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.analyze(
                text="She walked very slowly into the room.",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is True
            assert result.agent_type == AgentType.STYLE


class TestContinuityAgent:
    """Tests for ContinuityAgent"""

    def test_continuity_agent_type(self):
        """Test ContinuityAgent returns correct agent type"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ContinuityAgent(config=config, api_key="test-key")

        assert agent.agent_type == AgentType.CONTINUITY

    def test_continuity_agent_system_prompt(self):
        """Test ContinuityAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ContinuityAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "continuity" in prompt
        assert "consistency" in prompt or "inconsisten" in prompt
        assert "character" in prompt

    def test_continuity_agent_tools(self):
        """Test ContinuityAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ContinuityAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_entities" in tool_names
        assert "query_timeline" in tool_names
        assert "query_relationships" in tool_names

    def test_create_continuity_agent_factory(self):
        """Test create_continuity_agent factory function"""
        agent = create_continuity_agent(api_key="test-key")

        assert isinstance(agent, ContinuityAgent)
        assert agent.agent_type == AgentType.CONTINUITY

    def test_continuity_agent_context_weights(self):
        """Test ContinuityAgent has appropriate context weights"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)

        # Continuity should weight world and series highly
        assert config.world_context_weight == 1.0
        assert config.series_context_weight == 1.0
        assert config.author_context_weight < 0.5

    @pytest.mark.asyncio
    async def test_continuity_agent_analyze(self, mock_llm_response):
        """Test ContinuityAgent analyze method"""
        mock_llm_response.content = json.dumps({
            "recommendations": [],
            "issues": [
                {"type": "continuity", "severity": "high", "description": "Eye color changed."}
            ],
            "praise": [],
            "overall_assessment": "Check character descriptions."
        })

        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ContinuityAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.analyze(
                text="John's green eyes sparkled.",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is True
            assert len(result.issues) > 0


class TestStructureAgent:
    """Tests for StructureAgent"""

    def test_structure_agent_type(self):
        """Test StructureAgent returns correct agent type"""
        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)
        agent = StructureAgent(config=config, api_key="test-key")

        assert agent.agent_type == AgentType.STRUCTURE

    def test_structure_agent_system_prompt(self):
        """Test StructureAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)
        agent = StructureAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "structure" in prompt
        assert "beat" in prompt or "pacing" in prompt
        assert "three-act" in prompt or "three act" in prompt

    def test_structure_agent_tools(self):
        """Test StructureAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)
        agent = StructureAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_outline" in tool_names
        assert "query_plot_beats" in tool_names
        assert "query_chapters" in tool_names

    def test_create_structure_agent_factory(self):
        """Test create_structure_agent factory function"""
        agent = create_structure_agent(api_key="test-key")

        assert isinstance(agent, StructureAgent)
        assert agent.agent_type == AgentType.STRUCTURE

    def test_structure_agent_context_weights(self):
        """Test StructureAgent has appropriate context weights"""
        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)

        # Structure should weight manuscript highly
        assert config.manuscript_context_weight == 1.0
        assert config.series_context_weight == 0.8

    @pytest.mark.asyncio
    async def test_structure_agent_analyze(self, mock_llm_response):
        """Test StructureAgent analyze method"""
        mock_llm_response.content = json.dumps({
            "recommendations": [
                {"type": "structure", "severity": "medium", "text": "Scene lacks clear goal."}
            ],
            "issues": [],
            "praise": [{"aspect": "pacing", "text": "Good tension build."}],
            "overall_assessment": "Consider adding stakes."
        })

        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)
        agent = StructureAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.analyze(
                text="The hero wandered through the forest thinking about nothing in particular.",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is True
            assert result.agent_type == AgentType.STRUCTURE


class TestVoiceAgent:
    """Tests for VoiceAgent"""

    def test_voice_agent_type(self):
        """Test VoiceAgent returns correct agent type"""
        config = AgentConfig.for_agent_type(AgentType.VOICE)
        agent = VoiceAgent(config=config, api_key="test-key")

        assert agent.agent_type == AgentType.VOICE

    def test_voice_agent_system_prompt(self):
        """Test VoiceAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.VOICE)
        agent = VoiceAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "voice" in prompt or "dialogue" in prompt
        assert "character" in prompt
        assert "authentic" in prompt or "distinct" in prompt

    def test_voice_agent_tools(self):
        """Test VoiceAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.VOICE)
        agent = VoiceAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_entities" in tool_names
        assert "query_character_profile" in tool_names
        assert "query_author_profile" in tool_names

    def test_create_voice_agent_factory(self):
        """Test create_voice_agent factory function"""
        agent = create_voice_agent(api_key="test-key")

        assert isinstance(agent, VoiceAgent)
        assert agent.agent_type == AgentType.VOICE

    def test_voice_agent_context_weights(self):
        """Test VoiceAgent has appropriate context weights"""
        config = AgentConfig.for_agent_type(AgentType.VOICE)

        # Voice should weight author style
        assert config.author_context_weight == 0.7
        assert config.world_context_weight == 0.5

    @pytest.mark.asyncio
    async def test_voice_agent_analyze(self, mock_llm_response):
        """Test VoiceAgent analyze method"""
        mock_llm_response.content = json.dumps({
            "recommendations": [
                {"type": "voice", "severity": "medium", "text": "Characters have similar speech patterns."}
            ],
            "issues": [],
            "praise": [{"aspect": "subtext", "text": "Good use of subtext."}],
            "overall_assessment": "Vary speech patterns more."
        })

        config = AgentConfig.for_agent_type(AgentType.VOICE)
        agent = VoiceAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.analyze(
                text='"I think we should go," said Alice.\n"I think you might be right," said Bob.',
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is True
            assert result.agent_type == AgentType.VOICE


class TestAgentCostTracking:
    """Tests for cost tracking across all agent types"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_class,agent_type", [
        (StyleAgent, AgentType.STYLE),
        (ContinuityAgent, AgentType.CONTINUITY),
        (StructureAgent, AgentType.STRUCTURE),
        (VoiceAgent, AgentType.VOICE),
    ])
    async def test_agent_tracks_costs(self, agent_class, agent_type, mock_llm_response):
        """Test all agents track costs correctly"""
        config = AgentConfig.for_agent_type(agent_type)
        agent = agent_class(config=config, api_key="test-key")

        # Initial state
        assert agent.get_total_cost() == 0.0
        assert agent.get_total_tokens() == 0

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            await agent.analyze(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            # Should have tracked costs
            assert agent.get_total_cost() > 0
            assert agent.get_total_tokens() > 0


class TestAgentErrorHandling:
    """Tests for error handling across all agent types"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_class,agent_type", [
        (StyleAgent, AgentType.STYLE),
        (ContinuityAgent, AgentType.CONTINUITY),
        (StructureAgent, AgentType.STRUCTURE),
        (VoiceAgent, AgentType.VOICE),
    ])
    async def test_agent_handles_llm_error(self, agent_class, agent_type):
        """Test all agents handle LLM errors gracefully"""
        config = AgentConfig.for_agent_type(agent_type)
        agent = agent_class(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(side_effect=Exception("API Error"))

            result = await agent.analyze(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is False
            assert len(result.issues) > 0
            assert "API Error" in result.issues[0]["description"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_class,agent_type", [
        (StyleAgent, AgentType.STYLE),
        (ContinuityAgent, AgentType.CONTINUITY),
        (StructureAgent, AgentType.STRUCTURE),
        (VoiceAgent, AgentType.VOICE),
    ])
    async def test_agent_handles_context_error(self, agent_class, agent_type):
        """Test all agents handle context loading errors gracefully"""
        config = AgentConfig.for_agent_type(agent_type)
        agent = agent_class(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader:
            mock_loader.load_full_context.side_effect = Exception("Database Error")

            result = await agent.analyze(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is False
            assert "Database Error" in result.issues[0]["description"]
