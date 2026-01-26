"""
Tests for Writing Assistant Orchestrator
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.orchestrator.writing_assistant import (
    WritingAssistantOrchestrator,
    OrchestratorResult
)
from app.agents.base.agent_config import AgentType, ModelConfig, ModelProvider
from app.agents.base.agent_base import AgentResult
from app.services.llm_service import LLMResponse, LLMProvider


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


@pytest.fixture
def sample_agent_result():
    """Create a sample agent result"""
    return AgentResult(
        agent_type=AgentType.STYLE,
        success=True,
        recommendations=[
            {"type": "style", "severity": "medium", "text": "Vary sentence length."}
        ],
        issues=[],
        teaching_points=["Sentence variety improves reading rhythm."],
        usage={"prompt_tokens": 300, "completion_tokens": 100, "total_tokens": 400},
        cost=0.0005,
        execution_time_ms=1500
    )


class TestOrchestratorResult:
    """Tests for OrchestratorResult dataclass"""

    def test_orchestrator_result_creation(self):
        """Test basic OrchestratorResult creation"""
        result = OrchestratorResult(
            success=True,
            recommendations=[{"type": "test", "text": "Test rec"}],
            issues=[],
            total_cost=0.01,
            total_tokens=500
        )

        assert result.success is True
        assert len(result.recommendations) == 1
        assert result.total_cost == 0.01
        assert result.total_tokens == 500

    def test_orchestrator_result_defaults(self):
        """Test OrchestratorResult default values"""
        result = OrchestratorResult(success=False)

        assert result.recommendations == []
        assert result.issues == []
        assert result.teaching_points == []
        assert result.praise == []
        assert result.agent_results == {}
        assert result.total_cost == 0.0
        assert result.execution_time_ms == 0

    def test_orchestrator_result_to_dict(self, sample_agent_result):
        """Test OrchestratorResult serialization"""
        result = OrchestratorResult(
            success=True,
            recommendations=[
                {"type": "style", "severity": "medium", "text": "Test", "source_agent": "style"}
            ],
            issues=[
                {"type": "continuity", "severity": "high", "description": "Issue", "source_agent": "continuity"}
            ],
            teaching_points=["Learn about pacing"],
            praise=[{"aspect": "dialogue", "text": "Great voices"}],
            agent_results={"style": sample_agent_result},
            total_cost=0.005,
            total_tokens=1000,
            execution_time_ms=3000,
            author_insights={"strengths": ["dialogue"]}
        )

        data = result.to_dict()

        assert data["success"] is True
        assert len(data["recommendations"]) == 1
        assert len(data["issues"]) == 1
        assert len(data["teaching_points"]) == 1
        assert "style" in data["agent_results"]
        assert data["total_cost"] == 0.005
        assert data["author_insights"] is not None


class TestWritingAssistantOrchestrator:
    """Tests for WritingAssistantOrchestrator"""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        assert orchestrator.api_key == "test-key"
        assert len(orchestrator.enabled_agents) == 4
        assert AgentType.STYLE in orchestrator.enabled_agents
        assert AgentType.CONTINUITY in orchestrator.enabled_agents

    def test_orchestrator_with_custom_model(self):
        """Test orchestrator with custom model config"""
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            temperature=0.5
        )

        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            model_config=model_config
        )

        assert orchestrator.model_config.provider == ModelProvider.OPENAI
        assert orchestrator.model_config.model_name == "gpt-4o"

    def test_orchestrator_with_subset_of_agents(self):
        """Test orchestrator with limited agents"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[AgentType.STYLE, AgentType.VOICE]
        )

        assert len(orchestrator.enabled_agents) == 2
        assert AgentType.STYLE in orchestrator.enabled_agents
        assert AgentType.VOICE in orchestrator.enabled_agents
        assert AgentType.CONTINUITY not in orchestrator.enabled_agents

    def test_create_agents(self):
        """Test _create_agents method"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")
        agents = orchestrator._create_agents()

        assert len(agents) == 4
        assert AgentType.STYLE in agents
        assert AgentType.CONTINUITY in agents
        assert AgentType.STRUCTURE in agents
        assert AgentType.VOICE in agents

    def test_create_agents_subset(self):
        """Test _create_agents with subset"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[AgentType.STYLE]
        )
        agents = orchestrator._create_agents()

        assert len(agents) == 1
        assert AgentType.STYLE in agents

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_llm_response, sample_agent_result):
        """Test successful analysis with all agents"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        with patch.object(orchestrator, '_create_agents') as mock_create:
            # Create mock agents
            mock_agents = {}
            for agent_type in orchestrator.enabled_agents:
                mock_agent = MagicMock()
                result = AgentResult(
                    agent_type=agent_type,
                    success=True,
                    recommendations=[{"type": agent_type.value, "severity": "medium", "text": f"Rec from {agent_type.value}"}],
                    issues=[],
                    teaching_points=[f"Teaching from {agent_type.value}"],
                    usage={"total_tokens": 100},
                    cost=0.001
                )
                mock_agent.analyze = AsyncMock(return_value=result)
                mock_agents[agent_type] = mock_agent

            mock_create.return_value = mock_agents

            with patch('app.agents.orchestrator.writing_assistant.author_learning_service') as mock_learning:
                mock_learning.get_author_insights.return_value = {"strengths": ["dialogue"]}
                mock_learning.should_suppress_suggestion_type.return_value = False

                result = await orchestrator.analyze(
                    text="Test text for analysis",
                    user_id="test-user",
                    manuscript_id="test-ms"
                )

        assert result.success is True
        assert len(result.agent_results) == 4
        assert result.total_cost > 0
        assert result.total_tokens > 0

    @pytest.mark.asyncio
    async def test_analyze_no_agents(self):
        """Test analysis with no agents enabled"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[]
        )

        result = await orchestrator.analyze(
            text="Test",
            user_id="test-user",
            manuscript_id="test-ms"
        )

        assert result.success is False
        assert len(result.issues) == 1
        assert "No agents enabled" in result.issues[0]["description"]

    @pytest.mark.asyncio
    async def test_analyze_handles_agent_failure(self):
        """Test analysis handles individual agent failures"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[AgentType.STYLE, AgentType.VOICE]
        )

        with patch.object(orchestrator, '_create_agents') as mock_create:
            # One agent succeeds, one fails
            mock_style = MagicMock()
            mock_style.analyze = AsyncMock(return_value=AgentResult(
                agent_type=AgentType.STYLE,
                success=True,
                recommendations=[{"type": "style", "text": "Good"}],
                usage={"total_tokens": 100},
                cost=0.001
            ))

            mock_voice = MagicMock()
            mock_voice.analyze = AsyncMock(side_effect=Exception("Voice agent failed"))

            mock_create.return_value = {
                AgentType.STYLE: mock_style,
                AgentType.VOICE: mock_voice
            }

            with patch('app.agents.orchestrator.writing_assistant.author_learning_service') as mock_learning:
                mock_learning.get_author_insights.return_value = None
                mock_learning.should_suppress_suggestion_type.return_value = False

                result = await orchestrator.analyze(
                    text="Test",
                    user_id="test-user",
                    manuscript_id="test-ms"
                )

        assert result.success is True  # Overall still succeeds
        assert "style" in result.agent_results
        assert result.agent_results["voice"].success is False

    def test_deduplicate_recommendations(self):
        """Test recommendation deduplication"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        recommendations = [
            {"type": "style", "text": "Vary sentence length for better rhythm."},
            {"type": "style", "text": "Vary sentence length for better rhythm."},  # Duplicate
            {"type": "voice", "text": "Character voices are distinct."},
        ]

        result = orchestrator._deduplicate_recommendations(recommendations)

        assert len(result) == 2

    def test_deduplicate_issues(self):
        """Test issue deduplication"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        issues = [
            {"type": "continuity", "description": "Eye color changed from blue to green."},
            {"type": "continuity", "description": "Eye color changed from blue to green."},  # Duplicate
            {"type": "timeline", "description": "Event sequence error."},
        ]

        result = orchestrator._deduplicate_issues(issues)

        assert len(result) == 2

    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        assert orchestrator._deduplicate_recommendations([]) == []
        assert orchestrator._deduplicate_issues([]) == []

    def test_filter_suppressed_suggestions(self):
        """Test filtering suppressed suggestion types"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        recommendations = [
            {"type": "style", "severity": "high", "text": "High priority"},
            {"type": "style", "severity": "medium", "text": "Medium priority"},
            {"type": "passive_voice", "severity": "low", "text": "Suppressed type"},
        ]

        with patch('app.agents.orchestrator.writing_assistant.author_learning_service') as mock_learning:
            # Suppress "passive_voice" type
            def should_suppress(user_id, suggestion_type):
                return suggestion_type == "passive_voice"

            mock_learning.should_suppress_suggestion_type.side_effect = should_suppress

            result = orchestrator._filter_suppressed_suggestions(recommendations, "test-user")

        # High severity should not be suppressed even if type is suppressed
        assert len(result) == 2
        assert any(r["text"] == "High priority" for r in result)
        assert any(r["text"] == "Medium priority" for r in result)

    @pytest.mark.asyncio
    async def test_quick_check_success(self):
        """Test quick_check method"""
        orchestrator = WritingAssistantOrchestrator(api_key="test-key")

        with patch.object(orchestrator, '_create_agents') as mock_create:
            mock_style = MagicMock()
            mock_style.analyze = AsyncMock(return_value=AgentResult(
                agent_type=AgentType.STYLE,
                success=True,
                recommendations=[{"type": "style", "text": "Quick check result"}],
                usage={"total_tokens": 50},
                cost=0.0005
            ))

            mock_create.return_value = {AgentType.STYLE: mock_style}

            result = await orchestrator.quick_check(
                text="Quick test",
                user_id="test-user",
                manuscript_id="test-ms",
                focus_area=AgentType.STYLE
            )

        assert result.success is True
        assert result.agent_type == AgentType.STYLE

    @pytest.mark.asyncio
    async def test_quick_check_agent_not_available(self):
        """Test quick_check with unavailable agent"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[AgentType.STYLE]  # Only style enabled
        )

        result = await orchestrator.quick_check(
            text="Test",
            user_id="test-user",
            manuscript_id="test-ms",
            focus_area=AgentType.VOICE  # Not enabled
        )

        assert result.success is False
        assert "not available" in result.issues[0]["description"]


class TestOrchestratorParallelExecution:
    """Tests for parallel agent execution"""

    @pytest.mark.asyncio
    async def test_agents_run_in_parallel(self):
        """Test that agents actually run in parallel"""
        orchestrator = WritingAssistantOrchestrator(
            api_key="test-key",
            enabled_agents=[AgentType.STYLE, AgentType.VOICE]
        )

        execution_order = []

        async def slow_analyze(*args, **kwargs):
            execution_order.append("start")
            await asyncio.sleep(0.1)
            execution_order.append("end")
            return AgentResult(
                agent_type=AgentType.STYLE,
                success=True,
                usage={"total_tokens": 100},
                cost=0.001
            )

        with patch.object(orchestrator, '_create_agents') as mock_create:
            mock_style = MagicMock()
            mock_style.analyze = slow_analyze

            mock_voice = MagicMock()
            mock_voice.analyze = slow_analyze

            mock_create.return_value = {
                AgentType.STYLE: mock_style,
                AgentType.VOICE: mock_voice
            }

            with patch('app.agents.orchestrator.writing_assistant.author_learning_service') as mock_learning:
                mock_learning.get_author_insights.return_value = None
                mock_learning.should_suppress_suggestion_type.return_value = False

                await orchestrator.analyze(
                    text="Test",
                    user_id="test-user",
                    manuscript_id="test-ms"
                )

        # If parallel, we should see: start, start, end, end
        # If sequential, we'd see: start, end, start, end
        assert execution_order[:2] == ["start", "start"]
