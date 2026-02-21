"""
Refinement Service for Maxwell

Generic AI refinement loop for any suggestion type.
Supports iterative "suggest -> select -> refine -> save" pattern
across multiple domains: beat suggestions, beat descriptions,
beat mappings, brainstorm ideas, entity suggestions, wiki entries,
plot hole fixes, writing feedback.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from app.services.llm_service import LLMService, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)

# Domain-specific system prompts
DOMAIN_PROMPTS = {
    "beat_suggestion": (
        "You are refining a scene/beat idea for a fiction outline. "
        "The user has an AI-generated beat suggestion and wants to improve it. "
        "Maintain the same JSON structure as the original suggestion. "
        "Apply the user's feedback to produce a better version."
    ),
    "beat_description": (
        "You are refining a plot beat description for a fiction outline. "
        "The user has an AI-generated description for a specific story beat "
        "and wants to adjust it. Return the refined description as a JSON object "
        "with a 'description' field."
    ),
    "beat_mapping": (
        "You are helping map manuscript chapters to outline beats. "
        "The user is reviewing an AI-suggested mapping between a beat and "
        "chapter(s) and wants to adjust it. Provide gap analysis feedback "
        "on whether the suggested chapter(s) fulfill the beat's narrative purpose. "
        "Return the refined mapping as a JSON object."
    ),
    "brainstorm_idea": (
        "You are refining a brainstorming idea for a fiction project. "
        "The user has an AI-generated idea and wants to improve or redirect it. "
        "Maintain the same JSON structure as the original."
    ),
    "entity_suggestion": (
        "You are refining a character, location, or item description "
        "for a fiction project's codex. Apply the user's feedback to produce "
        "a more accurate or detailed version. Maintain the same JSON structure."
    ),
    "wiki_entry": (
        "You are refining a wiki entry for a fiction world. "
        "The user wants to adjust the content, accuracy, or scope of the entry. "
        "Maintain the same JSON structure as the original."
    ),
    "plot_hole_fix": (
        "You are refining a suggested fix for a plot hole in a fiction manuscript. "
        "The user has reviewed the fix and wants adjustments. "
        "Maintain the same JSON structure as the original."
    ),
    "writing_feedback": (
        "You are refining writing feedback for a fiction manuscript. "
        "The user wants to adjust the tone, focus, or specificity of the feedback. "
        "Maintain the same JSON structure as the original."
    ),
}


class RefinementService:
    """Generic AI refinement loop for any suggestion type."""

    def __init__(self):
        self.llm_service = LLMService()

    async def refine(
        self,
        api_key: str,
        domain: str,
        original: Dict[str, Any],
        feedback: str,
        context: Dict[str, str],
        history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Refine an AI suggestion based on user feedback.

        Args:
            api_key: OpenRouter API key
            domain: Key into DOMAIN_PROMPTS (e.g. "beat_suggestion")
            original: The original suggestion object
            feedback: User's refinement feedback
            context: Domain-specific context (e.g. beat name, outline info)
            history: Previous refinement turns [{role, content}]

        Returns:
            Refined suggestion in same schema as original
        """
        domain_prompt = DOMAIN_PROMPTS.get(domain)
        if not domain_prompt:
            raise ValueError(f"Unknown refinement domain: {domain}. "
                           f"Valid domains: {list(DOMAIN_PROMPTS.keys())}")

        # Build context string
        context_str = "\n".join(
            f"- {k}: {v}" for k, v in context.items()
        ) if context else "No additional context provided."

        system_prompt = (
            f"{domain_prompt}\n\n"
            f"Context:\n{context_str}\n\n"
            f"Original suggestion:\n{json.dumps(original, indent=2)}\n\n"
            f"IMPORTANT: Return ONLY valid JSON in the exact same structure as the original suggestion. "
            f"Do not include any text outside the JSON object."
        )

        # Build messages with history
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history
        for turn in history:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", "")
            })

        # Add current feedback
        messages.append({
            "role": "user",
            "content": f"Please refine this suggestion based on my feedback: {feedback}"
        })

        config = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="anthropic/claude-sonnet-4",
            temperature=0.7,
            max_tokens=2048,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        try:
            response = await self.llm_service.generate(config, messages)

            # Parse JSON from response
            content = response.content.strip()

            # Handle markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first and last lines (```json and ```)
                content = "\n".join(lines[1:-1]).strip()

            refined = json.loads(content)

            return {
                "refined": refined,
                "usage": response.usage,
                "cost": {
                    "total_usd": response.cost,
                    "formatted": f"${response.cost:.4f}"
                }
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse refinement response as JSON: {e}")
            # Return original with error note
            return {
                "refined": original,
                "error": "AI response was not valid JSON. Please try again.",
                "usage": {},
                "cost": {"total_usd": 0, "formatted": "$0.00"}
            }
        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            raise


# Singleton
refinement_service = RefinementService()
