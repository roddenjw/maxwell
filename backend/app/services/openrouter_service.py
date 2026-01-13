"""
OpenRouter Service - AI-powered writing suggestions using OpenRouter API
Implements BYOK (Bring Your Own Key) pattern for user control
"""

import httpx
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service for interacting with OpenRouter API"""

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"  # Fast, high-quality model

    def __init__(self, api_key: str):
        """
        Initialize OpenRouter service with user's API key

        Args:
            api_key: User's OpenRouter API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://maxwell-writer.com",  # Optional: for rankings
            "X-Title": "Maxwell Writing Assistant",
        }

    async def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate the API key with OpenRouter

        Returns:
            Dict with validation status and credit info
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/auth/key",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "valid": True,
                        "limit": data.get("data", {}).get("limit"),
                        "usage": data.get("data", {}).get("usage"),
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }

    async def get_writing_suggestion(
        self,
        text: str,
        context: str = "",
        suggestion_type: str = "general",
        max_tokens: int = 500,
        temperature: float = 0.7,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered writing suggestion

        Args:
            text: The text to analyze
            context: Additional context about the manuscript
            suggestion_type: Type of suggestion (general, dialogue, pacing, etc.)
            max_tokens: Maximum tokens in response
            temperature: Temperature for response randomness (0.0-1.0). Lower values (0.5-0.6)
                        are better for structured output like JSON. Default 0.7.
            response_format: Optional response format constraint. Use {"type": "json_object"}
                           to enforce JSON output at the API level.

        Returns:
            Dict with suggestion and usage info
        """
        try:
            # Use custom prompts if provided (for brainstorming, etc.)
            # Otherwise build generic writing feedback prompts
            if context:
                # Custom prompts: context = system prompt, text = user prompt
                system_prompt = context
                user_prompt = text
            else:
                # Generic writing feedback: build prompts from text
                system_prompt = self._build_system_prompt(suggestion_type)
                user_prompt = self._build_user_prompt(text, context, suggestion_type)

            async with httpx.AsyncClient() as client:
                # Build API payload
                payload = {
                    "model": self.DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

                # Add response_format if specified
                if response_format:
                    payload["response_format"] = response_format
                    logger.info(f"Using response_format: {response_format}")

                logger.info(f"Sending OpenRouter request with temperature={temperature}, max_tokens={max_tokens}")

                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                logger.info(f"OpenRouter response status: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }

                data = response.json()

                # Extract suggestion and usage
                suggestion = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                # Debug: Log first 200 chars of response
                logger.info(f"AI response preview (first 200 chars): {suggestion[:200] if suggestion else 'EMPTY'}")

                return {
                    "success": True,
                    "suggestion": suggestion,
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    "model": data.get("model", self.DEFAULT_MODEL)
                }

        except httpx.TimeoutException:
            logger.error("OpenRouter request timed out")
            return {
                "success": False,
                "error": "Request timed out. Please try again."
            }
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_batch_suggestions(
        self,
        analyses: List[Dict[str, Any]],
        manuscript_context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get AI suggestions for multiple analysis results

        Args:
            analyses: List of rule-based analysis results
            manuscript_context: Context about the manuscript

        Returns:
            List of enhanced suggestions with AI insights
        """
        suggestions = []

        for analysis in analyses:
            suggestion_type = analysis.get("type", "general")
            text = analysis.get("text", "")
            issue = analysis.get("issue", "")

            # Build context for AI
            context = f"{manuscript_context}\n\nIssue detected: {issue}"

            result = await self.get_writing_suggestion(
                text=text,
                context=context,
                suggestion_type=suggestion_type,
                max_tokens=300
            )

            if result["success"]:
                suggestions.append({
                    "original_analysis": analysis,
                    "ai_suggestion": result["suggestion"],
                    "usage": result["usage"]
                })

        return suggestions

    def _build_system_prompt(self, suggestion_type: str) -> str:
        """Build system prompt based on suggestion type"""

        base_prompt = """You are an expert writing coach helping authors improve their fiction manuscripts.
Provide specific, actionable suggestions that are encouraging and constructive."""

        type_specific = {
            "general": "Focus on overall writing quality, clarity, and engagement.",
            "dialogue": "Focus on dialogue tags, character voice, and conversation flow.",
            "pacing": "Focus on scene pacing, tension, and narrative momentum.",
            "description": "Focus on sensory details, show-don't-tell, and vivid imagery.",
            "character": "Focus on character consistency, motivation, and development.",
            "style": "Focus on prose style, word choice, and sentence variety.",
            "consistency": "Focus on plot consistency, continuity, and logical coherence.",
        }

        specific = type_specific.get(suggestion_type, type_specific["general"])

        return f"{base_prompt}\n\n{specific}"

    def _build_user_prompt(
        self,
        text: str,
        context: str,
        suggestion_type: str
    ) -> str:
        """Build user prompt with text and context"""

        prompt = f"""Please analyze this excerpt and provide 1-2 specific, actionable suggestions for improvement.

Context: {context if context else "Fiction manuscript excerpt"}

Excerpt:
{text[:1000]}  # Limit text length

Provide your suggestions in a friendly, encouraging tone. Be specific about what to improve and why."""

        return prompt

    @staticmethod
    def calculate_cost(usage: Dict[str, int], model: str = DEFAULT_MODEL) -> float:
        """
        Calculate approximate cost for API usage

        Args:
            usage: Dict with prompt_tokens, completion_tokens
            model: Model name used

        Returns:
            Estimated cost in USD
        """
        # Approximate costs per 1M tokens (as of Jan 2026)
        # These are estimates - actual costs vary by model
        pricing = {
            "anthropic/claude-3.5-sonnet": {
                "input": 3.00,   # $3 per 1M input tokens
                "output": 15.00  # $15 per 1M output tokens
            },
            "openai/gpt-4-turbo": {
                "input": 10.00,
                "output": 30.00
            },
            "openai/gpt-3.5-turbo": {
                "input": 0.50,
                "output": 1.50
            }
        }

        # Default to Claude pricing
        model_pricing = pricing.get(model, pricing["anthropic/claude-3.5-sonnet"])

        prompt_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * model_pricing["input"]
        completion_cost = (usage.get("completion_tokens", 0) / 1_000_000) * model_pricing["output"]

        return prompt_cost + completion_cost


async def test_openrouter_connection(api_key: str) -> Dict[str, Any]:
    """
    Test OpenRouter connection with user's API key

    Args:
        api_key: User's OpenRouter API key

    Returns:
        Dict with test results
    """
    service = OpenRouterService(api_key)
    return await service.validate_api_key()
