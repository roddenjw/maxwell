"""
Unified LLM Service for Maxwell

Provides a single interface to multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- OpenRouter (Multiple models)
- Local (llama-cpp-python)

Follows BYOK pattern - API keys passed per request, never stored.

PRIVACY NOTE:
All supported providers do NOT train on API data by default:
- Anthropic: Does not use API data for training (https://privacy.claude.com)
- OpenAI: Does not use API data for training since March 2023
- OpenRouter: Routing service only, doesn't train. Underlying providers apply.
- Local: Data never leaves your machine

For additional privacy protection, use the ProtectedLLMService which adds
explicit opt-out headers, content sanitization, and audit logging.
"""

import json
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import AsyncCallbackHandler


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    cost: float  # Estimated cost in USD
    raw_response: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider.value,
            "usage": self.usage,
            "cost": self.cost
        }


@dataclass
class LLMConfig:
    """Configuration for LLM calls"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    response_format: Optional[str] = None  # "json" for JSON mode
    api_key: Optional[str] = None  # Required for cloud providers
    base_url: Optional[str] = None  # For OpenRouter or custom endpoints

    # Local model specific
    model_path: Optional[str] = None
    n_ctx: int = 4096
    n_gpu_layers: int = -1


# Pricing per 1M tokens (input, output)
PRICING = {
    # OpenAI
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),

    # Anthropic
    "claude-3-opus-20240229": (15.00, 75.00),
    "claude-3-sonnet-20240229": (3.00, 15.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),

    # OpenRouter uses similar pricing, varies by model
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost for API call"""
    # Normalize model name
    model_key = model.lower()

    # First try exact match
    if model_key in PRICING:
        input_price, output_price = PRICING[model_key]
        cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
        return round(cost, 6)

    # Then try substring match, preferring longer matches
    matching_keys = [(key, len(key)) for key in PRICING if key in model_key]
    if matching_keys:
        # Use the longest matching key (more specific match)
        best_key = max(matching_keys, key=lambda x: x[1])[0]
        input_price, output_price = PRICING[best_key]
        cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
        return round(cost, 6)

    # Default fallback pricing (conservative estimate)
    return round((prompt_tokens * 1.0 + completion_tokens * 3.0) / 1_000_000, 6)


class LLMService:
    """
    Unified interface for LLM providers

    Usage:
        service = LLMService()

        response = await service.generate(
            config=LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-haiku-20240307",
                api_key="sk-...",
            ),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
    """

    def __init__(self):
        self._local_model = None
        self._local_model_path = None

    def _get_langchain_model(self, config: LLMConfig) -> BaseChatModel:
        """Get appropriate LangChain model based on config"""
        if config.provider == LLMProvider.OPENAI:
            kwargs = {
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "api_key": config.api_key,
                # Note: OpenAI does NOT train on API data since March 2023
                # See: https://help.openai.com/en/articles/5722486
            }
            if config.response_format == "json":
                kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            return ChatOpenAI(**kwargs)

        elif config.provider == LLMProvider.ANTHROPIC:
            # Note: Anthropic does NOT train on API data
            # See: https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training
            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
            )

        elif config.provider == LLMProvider.OPENROUTER:
            kwargs = {
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "api_key": config.api_key,
                "base_url": config.base_url or "https://openrouter.ai/api/v1",
                # OpenRouter-specific headers for identification and privacy
                "default_headers": {
                    "HTTP-Referer": "https://maxwell.writing",  # Identifies app to OpenRouter
                    "X-Title": "Maxwell Writing IDE",  # App name shown in OpenRouter dashboard
                    # Note: OpenRouter routes to underlying providers (Anthropic, OpenAI, etc.)
                    # Those providers don't train on API data by default
                },
            }
            if config.response_format == "json":
                kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            return ChatOpenAI(**kwargs)

        elif config.provider == LLMProvider.LOCAL:
            return self._get_local_model(config)

        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    def get_langchain_model(self, config: LLMConfig) -> BaseChatModel:
        """Public wrapper for _get_langchain_model - used by agents for tool calling"""
        return self._get_langchain_model(config)

    def convert_messages(self, messages: List[Dict[str, str]]):
        """Public wrapper for _convert_messages - used by agents for tool calling"""
        return self._convert_messages(messages)

    def _get_local_model(self, config: LLMConfig):
        """Get or initialize local llama-cpp model"""
        from app.services.local_llm_service import LocalLLMService
        local_service = LocalLLMService()
        return local_service.get_langchain_model(config)

    def _convert_messages(self, messages: List[Dict[str, str]]):
        """Convert dict messages to LangChain message objects"""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))

        return converted

    async def generate(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> LLMResponse:
        """
        Generate a response from the configured LLM

        Args:
            config: LLM configuration with provider, model, and API key
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response (not yet implemented)

        Returns:
            LLMResponse with content, usage, and cost information
        """
        model = self._get_langchain_model(config)
        langchain_messages = self._convert_messages(messages)

        # Invoke the model
        response = await model.ainvoke(langchain_messages)

        # Extract usage info
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        # Try to get usage from response metadata
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if "usage" in metadata:
                usage = metadata["usage"]
            elif "token_usage" in metadata:
                usage = metadata["token_usage"]

        # Calculate cost
        cost = calculate_cost(
            config.model,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0)
        )

        return LLMResponse(
            content=response.content,
            model=config.model,
            provider=config.provider,
            usage=usage,
            cost=cost,
            raw_response=response
        )

    async def generate_json(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM

        Args:
            config: LLM configuration (response_format will be set to json)
            messages: List of message dicts
            schema: Optional JSON schema for validation (appended to system prompt)

        Returns:
            Parsed JSON response as dictionary
        """
        # Update config to request JSON
        json_config = LLMConfig(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            response_format="json",
            api_key=config.api_key,
            base_url=config.base_url,
            model_path=config.model_path,
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
        )

        # Add schema to system message if provided
        if schema:
            schema_instruction = f"\n\nRespond with valid JSON matching this schema:\n```json\n{json.dumps(schema, indent=2)}\n```"
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += schema_instruction
            else:
                messages.insert(0, {"role": "system", "content": schema_instruction})

        response = await self.generate(json_config, messages)

        # Parse JSON from response
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

    def validate_api_key(self, provider: LLMProvider, api_key: str) -> bool:
        """
        Validate that an API key works for the given provider

        Args:
            provider: The LLM provider
            api_key: The API key to validate

        Returns:
            True if the key is valid
        """
        try:
            config = LLMConfig(
                provider=provider,
                model=self._get_test_model(provider),
                api_key=api_key,
                max_tokens=10
            )
            model = self._get_langchain_model(config)

            # Quick test invocation
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                model.ainvoke([HumanMessage(content="test")])
            )
            return True
        except Exception:
            return False

    def _get_test_model(self, provider: LLMProvider) -> str:
        """Get a cheap model for testing API keys"""
        if provider == LLMProvider.OPENAI:
            return "gpt-3.5-turbo"
        elif provider == LLMProvider.ANTHROPIC:
            return "claude-3-haiku-20240307"
        elif provider == LLMProvider.OPENROUTER:
            return "anthropic/claude-3-haiku"
        else:
            return "local"


# Global instance
llm_service = LLMService()
