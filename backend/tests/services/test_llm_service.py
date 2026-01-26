"""
Tests for LLM Service
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_service import (
    LLMService,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    calculate_cost,
    PRICING
)


class TestLLMProvider:
    """Tests for LLMProvider enum"""

    def test_all_providers_exist(self):
        """Test all expected providers are defined"""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENROUTER.value == "openrouter"
        assert LLMProvider.LOCAL.value == "local"


class TestLLMConfig:
    """Tests for LLMConfig dataclass"""

    def test_llm_config_creation(self):
        """Test basic LLMConfig creation"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307"
        )

        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-haiku-20240307"
        assert config.temperature == 0.7  # Default
        assert config.max_tokens == 4096  # Default

    def test_llm_config_with_api_key(self):
        """Test LLMConfig with API key"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="sk-test-key",
            temperature=0.5,
            max_tokens=8192
        )

        assert config.api_key == "sk-test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192

    def test_llm_config_openrouter(self):
        """Test LLMConfig for OpenRouter"""
        config = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="anthropic/claude-3-opus",
            api_key="or-test-key",
            base_url="https://openrouter.ai/api/v1"
        )

        assert config.provider == LLMProvider.OPENROUTER
        assert config.base_url == "https://openrouter.ai/api/v1"

    def test_llm_config_local(self):
        """Test LLMConfig for local model"""
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="llama-3-8b",
            model_path="/path/to/model.gguf",
            n_ctx=8192,
            n_gpu_layers=35
        )

        assert config.provider == LLMProvider.LOCAL
        assert config.model_path == "/path/to/model.gguf"
        assert config.n_ctx == 8192
        assert config.n_gpu_layers == 35


class TestLLMResponse:
    """Tests for LLMResponse dataclass"""

    def test_llm_response_creation(self):
        """Test basic LLMResponse creation"""
        response = LLMResponse(
            content="Hello, world!",
            model="claude-3-haiku-20240307",
            provider=LLMProvider.ANTHROPIC,
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            cost=0.001
        )

        assert response.content == "Hello, world!"
        assert response.model == "claude-3-haiku-20240307"
        assert response.provider == LLMProvider.ANTHROPIC
        assert response.usage["total_tokens"] == 150
        assert response.cost == 0.001

    def test_llm_response_to_dict(self):
        """Test LLMResponse serialization"""
        response = LLMResponse(
            content="Test response",
            model="gpt-4o",
            provider=LLMProvider.OPENAI,
            usage={"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
            cost=0.005
        )

        data = response.to_dict()

        assert data["content"] == "Test response"
        assert data["model"] == "gpt-4o"
        assert data["provider"] == "openai"
        assert data["usage"]["total_tokens"] == 300
        assert data["cost"] == 0.005


class TestCalculateCost:
    """Tests for calculate_cost function"""

    def test_calculate_cost_anthropic_haiku(self):
        """Test cost calculation for Claude Haiku"""
        cost = calculate_cost(
            model="claude-3-haiku-20240307",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Haiku: $0.25/1M input, $1.25/1M output
        expected = (1000 * 0.25 + 500 * 1.25) / 1_000_000
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_anthropic_sonnet(self):
        """Test cost calculation for Claude Sonnet"""
        cost = calculate_cost(
            model="claude-3-5-sonnet-20241022",
            prompt_tokens=2000,
            completion_tokens=1000
        )

        # Sonnet: $3/1M input, $15/1M output
        expected = (2000 * 3.0 + 1000 * 15.0) / 1_000_000
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_openai_gpt4o(self):
        """Test cost calculation for GPT-4o"""
        cost = calculate_cost(
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # GPT-4o: $5/1M input, $15/1M output
        expected = (1000 * 5.0 + 500 * 15.0) / 1_000_000
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_openai_gpt4o_mini(self):
        """Test cost calculation for GPT-4o-mini"""
        cost = calculate_cost(
            model="gpt-4o-mini",
            prompt_tokens=5000,
            completion_tokens=2000
        )

        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        expected = (5000 * 0.15 + 2000 * 0.60) / 1_000_000
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model uses fallback"""
        cost = calculate_cost(
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Fallback: $1/1M input, $3/1M output
        expected = (1000 * 1.0 + 500 * 3.0) / 1_000_000
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        cost = calculate_cost(
            model="claude-3-haiku-20240307",
            prompt_tokens=0,
            completion_tokens=0
        )

        assert cost == 0.0


class TestPricing:
    """Tests for PRICING dictionary"""

    def test_pricing_contains_openai_models(self):
        """Test pricing includes OpenAI models"""
        assert "gpt-4o" in PRICING
        assert "gpt-4o-mini" in PRICING
        assert "gpt-3.5-turbo" in PRICING

    def test_pricing_contains_anthropic_models(self):
        """Test pricing includes Anthropic models"""
        assert "claude-3-haiku-20240307" in PRICING
        assert "claude-3-sonnet-20240229" in PRICING
        assert "claude-3-opus-20240229" in PRICING

    def test_pricing_format(self):
        """Test pricing entries have correct format"""
        for model, pricing in PRICING.items():
            assert len(pricing) == 2, f"Model {model} should have (input, output) pricing"
            assert pricing[0] >= 0, f"Input price for {model} should be >= 0"
            assert pricing[1] >= 0, f"Output price for {model} should be >= 0"


class TestLLMService:
    """Tests for LLMService class"""

    @pytest.fixture
    def service(self):
        """Create LLM service instance"""
        return LLMService()

    def test_service_instantiation(self, service):
        """Test LLMService can be instantiated"""
        assert service is not None
        assert service._local_model is None

    def test_convert_messages_system(self, service):
        """Test message conversion for system message"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

        converted = service._convert_messages(messages)

        assert len(converted) == 1
        assert converted[0].content == "You are a helpful assistant."

    def test_convert_messages_user(self, service):
        """Test message conversion for user message"""
        messages = [
            {"role": "user", "content": "Hello!"}
        ]

        converted = service._convert_messages(messages)

        assert len(converted) == 1
        assert converted[0].content == "Hello!"

    def test_convert_messages_assistant(self, service):
        """Test message conversion for assistant message"""
        messages = [
            {"role": "assistant", "content": "Hi there!"}
        ]

        converted = service._convert_messages(messages)

        assert len(converted) == 1
        assert converted[0].content == "Hi there!"

    def test_convert_messages_full_conversation(self, service):
        """Test converting a full conversation"""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"}
        ]

        converted = service._convert_messages(messages)

        assert len(converted) == 4

    def test_get_test_model_openai(self, service):
        """Test getting test model for OpenAI"""
        model = service._get_test_model(LLMProvider.OPENAI)
        assert model == "gpt-3.5-turbo"

    def test_get_test_model_anthropic(self, service):
        """Test getting test model for Anthropic"""
        model = service._get_test_model(LLMProvider.ANTHROPIC)
        assert model == "claude-3-haiku-20240307"

    def test_get_test_model_openrouter(self, service):
        """Test getting test model for OpenRouter"""
        model = service._get_test_model(LLMProvider.OPENROUTER)
        assert model == "anthropic/claude-3-haiku"

    def test_get_test_model_local(self, service):
        """Test getting test model for local"""
        model = service._get_test_model(LLMProvider.LOCAL)
        assert model == "local"

    @pytest.mark.asyncio
    async def test_generate_success(self, service):
        """Test successful generation"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key="test-key"
        )

        messages = [
            {"role": "user", "content": "Hello"}
        ]

        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help?"
        mock_response.response_metadata = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        with patch.object(service, '_get_langchain_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model

            response = await service.generate(config, messages)

        assert response.content == "Hello! How can I help?"
        assert response.model == "claude-3-haiku-20240307"
        assert response.provider == LLMProvider.ANTHROPIC

    @pytest.mark.asyncio
    async def test_generate_json_success(self, service):
        """Test successful JSON generation"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key="test-key"
        )

        messages = [
            {"role": "user", "content": "Return JSON with a greeting"}
        ]

        mock_response = MagicMock()
        mock_response.content = '{"greeting": "Hello!"}'
        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
        }

        with patch.object(service, '_get_langchain_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model

            result = await service.generate_json(config, messages.copy())

        assert result == {"greeting": "Hello!"}

    @pytest.mark.asyncio
    async def test_generate_json_with_code_block(self, service):
        """Test JSON generation extracts from code blocks"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key="test-key"
        )

        messages = [{"role": "user", "content": "Test"}]

        mock_response = MagicMock()
        mock_response.content = '```json\n{"data": "test"}\n```'
        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        }

        with patch.object(service, '_get_langchain_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_model.return_value = mock_model

            result = await service.generate_json(config, messages.copy())

        assert result == {"data": "test"}

    def test_get_langchain_model_openai(self, service):
        """Test getting OpenAI model"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key"
        )

        with patch('app.services.llm_service.ChatOpenAI') as MockOpenAI:
            model = service._get_langchain_model(config)
            MockOpenAI.assert_called_once()

    def test_get_langchain_model_anthropic(self, service):
        """Test getting Anthropic model"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key="test-key"
        )

        with patch('app.services.llm_service.ChatAnthropic') as MockAnthropic:
            model = service._get_langchain_model(config)
            MockAnthropic.assert_called_once()

    def test_get_langchain_model_unsupported(self, service):
        """Test getting unsupported provider raises error"""
        config = LLMConfig(
            provider="invalid",  # Invalid provider
            model="test"
        )

        with pytest.raises(ValueError, match="Unsupported provider"):
            service._get_langchain_model(config)


class TestLLMServiceGlobalInstance:
    """Tests for global llm_service instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        from app.services.llm_service import llm_service

        assert llm_service is not None
        assert isinstance(llm_service, LLMService)
