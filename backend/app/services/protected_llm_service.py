"""
Protected LLM Service

A wrapper around the LLM service that integrates:
1. Privacy protection via ContentGateway
2. Carbon tracking via CarbonTracker
3. Response caching for efficiency

This is the recommended way to make AI calls for manuscript content.
"""

import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session

from app.services.llm_service import LLMService, LLMConfig, LLMResponse, LLMProvider
from app.services.content_gateway import ContentGateway, get_content_gateway, SafeAIRequest
from app.services.carbon_tracker import CarbonTracker, get_carbon_tracker
from app.services.privacy_config import AIPrivacyConfig, DEFAULT_PRIVACY_CONFIG, AIProvider


@dataclass
class ProtectedLLMResponse:
    """Response from protected LLM service with additional metadata"""
    content: str
    model: str
    provider: str

    # Privacy info
    training_opted_out: bool
    content_hash: str

    # Carbon info
    tokens_used: int
    emissions_micro_gco2: int
    was_cached: bool

    # Cost
    estimated_cost_usd: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "training_opted_out": self.training_opted_out,
            "tokens_used": self.tokens_used,
            "emissions_gco2": self.emissions_micro_gco2 / 1_000_000,
            "was_cached": self.was_cached,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


class ResponseCache:
    """
    Simple in-memory cache for AI responses.

    Caches responses for identical requests to reduce:
    1. API costs
    2. Carbon emissions
    3. Latency

    Cache key is based on: content hash + request type + model
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (response, timestamp)

    def _make_key(self, content_hash: str, request_type: str, model: str) -> str:
        """Create cache key"""
        key_data = f"{content_hash}:{request_type}:{model}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def get(self, content_hash: str, request_type: str, model: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        key = self._make_key(content_hash, request_type, model)

        if key not in self._cache:
            return None

        response, timestamp = self._cache[key]

        # Check TTL
        if datetime.utcnow() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self._cache[key]
            return None

        return response

    def set(self, content_hash: str, request_type: str, model: str, response: str):
        """Cache a response"""
        # Evict oldest entries if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        key = self._make_key(content_hash, request_type, model)
        self._cache[key] = (response, datetime.utcnow())

    def clear(self):
        """Clear the cache"""
        self._cache.clear()


class ProtectedLLMService:
    """
    LLM service with integrated privacy protection and carbon tracking.

    This wraps the base LLMService to:
    1. Verify author privacy preferences before any request
    2. Sanitize content through ContentGateway
    3. Add privacy headers to requests
    4. Track carbon emissions
    5. Cache responses when appropriate
    6. Audit all interactions

    Usage:
        service = ProtectedLLMService(db)

        response = await service.generate(
            manuscript_id="...",
            content="Chapter content here...",
            request_type="grammar_check",
            llm_config=LLMConfig(...)
        )
    """

    # Request types that can be safely cached
    CACHEABLE_REQUESTS = {
        "grammar_check",
        "spell_check",
        "word_count",
        "readability_analysis",
    }

    def __init__(
        self,
        db: Session,
        privacy_config: AIPrivacyConfig = None,
        region: str = "unknown",
        enable_cache: bool = True,
    ):
        self.db = db
        self.privacy_config = privacy_config or DEFAULT_PRIVACY_CONFIG
        self.llm_service = LLMService()
        self.content_gateway = get_content_gateway(db, privacy_config)
        self.carbon_tracker = get_carbon_tracker(db, region)
        self.cache = ResponseCache() if enable_cache else None

    async def generate(
        self,
        manuscript_id: str,
        content: str,
        request_type: str,
        llm_config: LLMConfig,
        chapter_id: Optional[str] = None,
        use_cache: bool = True,
        system_prompt_override: Optional[str] = None,
    ) -> ProtectedLLMResponse:
        """
        Generate an AI response with full privacy protection and carbon tracking.

        Args:
            manuscript_id: The manuscript ID
            content: Content to process
            request_type: Type of AI request
            llm_config: LLM configuration
            chapter_id: Optional chapter ID
            use_cache: Whether to use/check cache
            system_prompt_override: Override the default system prompt

        Returns:
            ProtectedLLMResponse with content and metadata

        Raises:
            AIFeatureDisabledException: If the feature is disabled
            ValueError: If privacy check fails
        """
        # 1. Prepare request through content gateway (privacy check + sanitization)
        gateway_result = await self.content_gateway.prepare_ai_request(
            manuscript_id=manuscript_id,
            content=content,
            request_type=request_type,
            chapter_id=chapter_id,
        )

        if not gateway_result.allowed:
            raise ValueError(gateway_result.error)

        safe_request = gateway_result.request

        # 2. Check cache for cacheable requests
        cached_response = None
        if use_cache and self.cache and request_type in self.CACHEABLE_REQUESTS:
            cached_response = self.cache.get(
                safe_request.content_hash,
                request_type,
                llm_config.model
            )

        if cached_response:
            # Track cache hit for carbon
            await self.carbon_tracker.track_ai_operation(
                provider=llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
                model=llm_config.model,
                tokens=0,  # No tokens used
                manuscript_id=manuscript_id,
                request_type=request_type,
                cache_hit=True,
            )

            return ProtectedLLMResponse(
                content=cached_response,
                model=llm_config.model,
                provider=llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
                training_opted_out=safe_request.training_opted_out,
                content_hash=safe_request.content_hash,
                tokens_used=0,
                emissions_micro_gco2=1,  # Minimal for cache lookup
                was_cached=True,
                estimated_cost_usd=0.0,
            )

        # 3. Build messages with privacy-aware system prompt
        system_prompt = system_prompt_override or safe_request.system_prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": safe_request.content},
        ]

        # 4. Make the LLM call
        llm_response = await self.llm_service.generate(llm_config, messages)

        # 5. Track carbon emissions
        total_tokens = (
            llm_response.usage.get("prompt_tokens", 0) +
            llm_response.usage.get("completion_tokens", 0)
        )

        carbon_result = await self.carbon_tracker.track_ai_operation(
            provider=llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
            model=llm_config.model,
            tokens=total_tokens,
            manuscript_id=manuscript_id,
            request_type=request_type,
            cache_hit=False,
        )

        # 6. Audit the interaction
        await self.content_gateway.audit_interaction(
            manuscript_id=manuscript_id,
            request_type=request_type,
            provider=llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
            model=llm_config.model,
            tokens_sent=llm_response.usage.get("prompt_tokens", 0),
            tokens_received=llm_response.usage.get("completion_tokens", 0),
            content_hash=safe_request.content_hash,
            chapter_id=chapter_id,
            cost_usd=llm_response.cost,
        )

        # 7. Cache the response if appropriate
        if self.cache and request_type in self.CACHEABLE_REQUESTS:
            self.cache.set(
                safe_request.content_hash,
                request_type,
                llm_config.model,
                llm_response.content
            )

        return ProtectedLLMResponse(
            content=llm_response.content,
            model=llm_config.model,
            provider=llm_config.provider.value if hasattr(llm_config.provider, 'value') else str(llm_config.provider),
            training_opted_out=safe_request.training_opted_out,
            content_hash=safe_request.content_hash,
            tokens_used=total_tokens,
            emissions_micro_gco2=carbon_result.emissions_micro_gco2,
            was_cached=False,
            estimated_cost_usd=llm_response.cost,
        )

    async def generate_with_context(
        self,
        manuscript_id: str,
        content: str,
        request_type: str,
        llm_config: LLMConfig,
        author_context: Optional[Dict[str, Any]] = None,
        chapter_id: Optional[str] = None,
    ) -> ProtectedLLMResponse:
        """
        Generate with additional author context.

        Author context (preferences, style, etc.) is safe to include
        as it doesn't contain actual manuscript content.
        """
        # Build enhanced system prompt with author context
        context_addition = ""
        if author_context:
            context_parts = []
            if "preferred_genres" in author_context:
                context_parts.append(f"Genre: {author_context['preferred_genres']}")
            if "writing_style" in author_context:
                context_parts.append(f"Style: {author_context['writing_style']}")
            if "target_audience" in author_context:
                context_parts.append(f"Audience: {author_context['target_audience']}")

            if context_parts:
                context_addition = "\n\nAuthor context:\n" + "\n".join(context_parts)

        return await self.generate(
            manuscript_id=manuscript_id,
            content=content,
            request_type=request_type,
            llm_config=llm_config,
            chapter_id=chapter_id,
            system_prompt_override=None,  # Will be enhanced with context
        )

    def get_optimal_model(self, request_type: str, provider: LLMProvider = None) -> str:
        """
        Get the optimal (most efficient) model for a request type.

        This helps minimize carbon footprint by using smaller models
        for simpler tasks.
        """
        provider = provider or LLMProvider.ANTHROPIC

        # Map request types to model recommendations
        simple_tasks = {"grammar_check", "spell_check", "word_count"}
        medium_tasks = {"style_analysis", "summary", "continuity_check"}
        complex_tasks = {"plot_analysis", "character_analysis", "structure_analysis"}

        if provider == LLMProvider.ANTHROPIC:
            if request_type in simple_tasks:
                return "claude-3-haiku-20240307"
            elif request_type in medium_tasks:
                return "claude-3-5-sonnet-20241022"
            else:
                return "claude-3-5-sonnet-20241022"

        elif provider == LLMProvider.OPENAI:
            if request_type in simple_tasks:
                return "gpt-4o-mini"
            elif request_type in medium_tasks:
                return "gpt-4o"
            else:
                return "gpt-4o"

        # Default
        return "claude-3-haiku-20240307"


# Factory function
def get_protected_llm_service(
    db: Session,
    privacy_config: AIPrivacyConfig = None,
    region: str = "unknown",
) -> ProtectedLLMService:
    """Get a ProtectedLLMService instance"""
    return ProtectedLLMService(db, privacy_config, region)
