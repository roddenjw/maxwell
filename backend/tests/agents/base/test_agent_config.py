"""
Tests for Agent Configuration
"""
import pytest

from app.agents.base.agent_config import (
    AgentConfig,
    AgentType,
    ModelConfig,
    ModelProvider,
    ModelCapability,
    DEFAULT_MODELS
)


class TestModelConfig:
    """Tests for ModelConfig dataclass"""

    def test_model_config_creation(self):
        """Test basic ModelConfig creation"""
        config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            max_tokens=4096,
            temperature=0.7
        )

        assert config.provider == ModelProvider.ANTHROPIC
        assert config.model_name == "claude-3-haiku-20240307"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.capability == ModelCapability.STANDARD

    def test_model_config_defaults(self):
        """Test ModelConfig default values"""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o-mini"
        )

        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.capability == ModelCapability.STANDARD
        assert config.model_path is None
        assert config.n_ctx == 4096
        assert config.n_gpu_layers == -1

    def test_model_config_local_settings(self):
        """Test ModelConfig with local model settings"""
        config = ModelConfig(
            provider=ModelProvider.LOCAL,
            model_name="llama-3-8b",
            model_path="/path/to/model.gguf",
            n_ctx=8192,
            n_gpu_layers=35
        )

        assert config.provider == ModelProvider.LOCAL
        assert config.model_path == "/path/to/model.gguf"
        assert config.n_ctx == 8192
        assert config.n_gpu_layers == 35

    def test_model_config_to_dict(self):
        """Test ModelConfig serialization"""
        config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            max_tokens=8192,
            temperature=0.5,
            capability=ModelCapability.ADVANCED
        )

        result = config.to_dict()

        assert result["provider"] == "anthropic"
        assert result["model_name"] == "claude-3-sonnet-20240229"
        assert result["max_tokens"] == 8192
        assert result["temperature"] == 0.5
        assert result["capability"] == "advanced"


class TestAgentType:
    """Tests for AgentType enum"""

    def test_all_agent_types_exist(self):
        """Test all expected agent types are defined"""
        expected_types = ["continuity", "style", "structure", "voice", "consistency", "research", "coach"]
        for t in expected_types:
            assert AgentType(t) is not None

    def test_agent_type_values(self):
        """Test agent type string values"""
        assert AgentType.CONTINUITY.value == "continuity"
        assert AgentType.STYLE.value == "style"
        assert AgentType.STRUCTURE.value == "structure"
        assert AgentType.VOICE.value == "voice"
        assert AgentType.COACH.value == "coach"


class TestModelProvider:
    """Tests for ModelProvider enum"""

    def test_all_providers_exist(self):
        """Test all expected providers are defined"""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.OPENROUTER.value == "openrouter"
        assert ModelProvider.LOCAL.value == "local"


class TestDefaultModels:
    """Tests for DEFAULT_MODELS configuration"""

    def test_default_models_exist(self):
        """Test default models are defined for main providers"""
        assert ModelProvider.OPENAI in DEFAULT_MODELS
        assert ModelProvider.ANTHROPIC in DEFAULT_MODELS
        assert ModelProvider.OPENROUTER in DEFAULT_MODELS

    def test_default_models_are_valid(self):
        """Test default model configs are properly configured"""
        for provider, config in DEFAULT_MODELS.items():
            assert config.provider == provider
            assert config.model_name is not None
            assert config.max_tokens > 0
            assert 0 <= config.temperature <= 2


class TestAgentConfig:
    """Tests for AgentConfig dataclass"""

    def test_agent_config_creation(self):
        """Test basic AgentConfig creation"""
        model_config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307"
        )

        config = AgentConfig(
            agent_type=AgentType.STYLE,
            model_config=model_config
        )

        assert config.agent_type == AgentType.STYLE
        assert config.model_config.provider == ModelProvider.ANTHROPIC
        assert config.include_teaching is True
        assert config.response_format == "json"

    def test_agent_config_defaults(self):
        """Test AgentConfig default values"""
        model_config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307"
        )

        config = AgentConfig(
            agent_type=AgentType.CONTINUITY,
            model_config=model_config
        )

        assert config.author_context_weight == 0.5
        assert config.world_context_weight == 0.5
        assert config.series_context_weight == 0.5
        assert config.manuscript_context_weight == 1.0
        assert config.max_context_tokens == 8000
        assert config.track_costs is True
        assert config.custom_system_prompt is None
        assert config.enabled_tools == []

    def test_agent_config_for_style_agent(self):
        """Test AgentConfig.for_agent_type with STYLE agent"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)

        assert config.agent_type == AgentType.STYLE
        assert config.author_context_weight == 1.0
        assert config.world_context_weight == 0.2
        assert "query_author_profile" in config.enabled_tools

    def test_agent_config_for_continuity_agent(self):
        """Test AgentConfig.for_agent_type with CONTINUITY agent"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)

        assert config.agent_type == AgentType.CONTINUITY
        assert config.world_context_weight == 1.0
        assert config.series_context_weight == 1.0
        assert "query_entities" in config.enabled_tools
        assert "query_timeline" in config.enabled_tools

    def test_agent_config_for_voice_agent(self):
        """Test AgentConfig.for_agent_type with VOICE agent"""
        config = AgentConfig.for_agent_type(AgentType.VOICE)

        assert config.agent_type == AgentType.VOICE
        assert config.author_context_weight == 0.7
        assert "query_character_profile" in config.enabled_tools

    def test_agent_config_for_structure_agent(self):
        """Test AgentConfig.for_agent_type with STRUCTURE agent"""
        config = AgentConfig.for_agent_type(AgentType.STRUCTURE)

        assert config.agent_type == AgentType.STRUCTURE
        assert config.manuscript_context_weight == 1.0
        assert config.series_context_weight == 0.8
        assert "query_outline" in config.enabled_tools

    def test_agent_config_for_coach_agent(self):
        """Test AgentConfig.for_agent_type with COACH agent"""
        config = AgentConfig.for_agent_type(AgentType.COACH)

        assert config.agent_type == AgentType.COACH
        assert config.response_format == "text"  # Coach uses text, not JSON
        assert config.author_context_weight == 0.8
        assert "query_entities" in config.enabled_tools

    def test_agent_config_for_consistency_agent(self):
        """Test AgentConfig.for_agent_type with CONSISTENCY agent"""
        config = AgentConfig.for_agent_type(AgentType.CONSISTENCY)

        assert config.agent_type == AgentType.CONSISTENCY
        assert config.world_context_weight == 1.0
        assert config.manuscript_context_weight == 1.0
        assert "query_relationships" in config.enabled_tools

    def test_agent_config_for_research_agent(self):
        """Test AgentConfig.for_agent_type with RESEARCH agent"""
        config = AgentConfig.for_agent_type(AgentType.RESEARCH)

        assert config.agent_type == AgentType.RESEARCH
        assert config.world_context_weight == 1.0
        assert "query_entities" in config.enabled_tools

    def test_agent_config_custom_model(self):
        """Test AgentConfig.for_agent_type with custom model"""
        custom_model = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            max_tokens=8192,
            temperature=0.3,
            capability=ModelCapability.ADVANCED
        )

        config = AgentConfig.for_agent_type(
            AgentType.STYLE,
            model_config=custom_model
        )

        assert config.model_config.provider == ModelProvider.OPENAI
        assert config.model_config.model_name == "gpt-4o"
        assert config.model_config.max_tokens == 8192

    def test_agent_config_with_kwargs(self):
        """Test AgentConfig.for_agent_type with additional kwargs"""
        config = AgentConfig.for_agent_type(
            AgentType.STYLE,
            include_teaching=False,
            max_context_tokens=4000,
            custom_system_prompt="Be extra concise."
        )

        assert config.include_teaching is False
        assert config.max_context_tokens == 4000
        assert config.custom_system_prompt == "Be extra concise."

    def test_agent_config_to_dict(self):
        """Test AgentConfig serialization"""
        config = AgentConfig.for_agent_type(AgentType.STYLE)
        result = config.to_dict()

        assert result["agent_type"] == "style"
        assert "model_config" in result
        assert result["model_config"]["provider"] == "anthropic"
        assert result["author_context_weight"] == 1.0
        assert result["include_teaching"] is True
        assert result["response_format"] == "json"
        assert "enabled_tools" in result
