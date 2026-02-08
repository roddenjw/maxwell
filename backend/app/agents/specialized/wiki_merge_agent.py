"""
Wiki Merge Agent

Specialized agent for intelligently merging Codex entity data into
existing Wiki entries. When codex data arrives, this agent:
- Compares incoming data against existing wiki entry
- Produces a single cohesive merged entry (not duplicate/append)
- Preserves existing information from other manuscripts
- Incorporates new details naturally

Returns a merge result with confidence score.
"""

import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.services.llm_service import llm_service, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)

MERGE_SYSTEM_PROMPT = """You are a wiki editor for a fictional world encyclopedia. Your job is to merge new information about a character, location, or item into an existing wiki entry.

Rules:
1. Preserve ALL existing information unless the new data directly contradicts it.
2. When there's a contradiction, prefer the newer data but note what changed.
3. Produce a single cohesive entry — never duplicate or append blindly.
4. Write in an encyclopedic tone appropriate for a fictional world wiki.
5. If the new data adds details that complement existing info, weave them in naturally.
6. Keep structured_data fields as a flat JSON object with descriptive keys.
7. For the content field, use Markdown with ## headings for sections.

You MUST respond with valid JSON matching this exact schema:
{
  "merged_content": "string (markdown content for the wiki entry)",
  "merged_structured_data": { "key": "value" },
  "merged_summary": "string (1-2 sentence summary)",
  "merged_aliases": ["list", "of", "aliases"],
  "confidence": 0.95,
  "needs_review": false,
  "reason": "string explaining merge decisions"
}

confidence should be:
- 0.9-1.0: Simple additive merge, no conflicts
- 0.7-0.89: Minor ambiguities but reasonable merge
- Below 0.7: Significant conflicts or unclear how to merge
"""


@dataclass
class MergeResult:
    """Result from a wiki merge operation"""
    merged_content: str
    merged_structured_data: Dict[str, Any]
    merged_summary: str
    merged_aliases: list
    confidence: float
    needs_review: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merged_content": self.merged_content,
            "merged_structured_data": self.merged_structured_data,
            "merged_summary": self.merged_summary,
            "merged_aliases": self.merged_aliases,
            "confidence": self.confidence,
            "needs_review": self.needs_review,
            "reason": self.reason,
        }


async def merge_entity_into_wiki(
    api_key: str,
    existing_wiki: Dict[str, Any],
    incoming_entity: Dict[str, Any],
    entry_type: str,
) -> MergeResult:
    """
    Use LLM to intelligently merge an incoming codex entity into an existing wiki entry.

    Args:
        api_key: LLM API key (OpenRouter)
        existing_wiki: Dict with keys: title, content, structured_data, summary, aliases
        incoming_entity: Dict with keys: name, attributes, aliases, type
        entry_type: Wiki entry type (character, location, artifact, etc.)

    Returns:
        MergeResult with merged data and confidence score
    """
    config = LLMConfig(
        provider=LLMProvider.OPENROUTER,
        model="anthropic/claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=4096,
        response_format="json",
        api_key=api_key,
    )

    user_prompt = f"""Merge the following incoming entity data into the existing wiki entry.

## Existing Wiki Entry
**Title:** {existing_wiki.get('title', 'Unknown')}
**Type:** {entry_type}
**Content:**
{existing_wiki.get('content', '(empty)')}

**Structured Data:**
{json.dumps(existing_wiki.get('structured_data', {}), indent=2)}

**Summary:** {existing_wiki.get('summary', '(none)')}
**Aliases:** {json.dumps(existing_wiki.get('aliases', []))}

## Incoming Entity Data (from manuscript codex)
**Name:** {incoming_entity.get('name', 'Unknown')}
**Type:** {incoming_entity.get('type', 'Unknown')}
**Attributes:**
{json.dumps(incoming_entity.get('attributes', {}), indent=2)}

**Aliases:** {json.dumps(incoming_entity.get('aliases', []))}

Please merge these into a single cohesive wiki entry."""

    messages = [
        {"role": "system", "content": MERGE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        result = await llm_service.generate_json(config, messages)

        return MergeResult(
            merged_content=result.get("merged_content", existing_wiki.get("content", "")),
            merged_structured_data=result.get("merged_structured_data", existing_wiki.get("structured_data", {})),
            merged_summary=result.get("merged_summary", existing_wiki.get("summary", "")),
            merged_aliases=result.get("merged_aliases", existing_wiki.get("aliases", [])),
            confidence=float(result.get("confidence", 0.5)),
            needs_review=result.get("needs_review", True),
            reason=result.get("reason", "AI merge completed"),
        )
    except Exception as e:
        logger.error(f"Wiki merge agent failed: {e}")
        # Return a low-confidence result that queues for review
        return MergeResult(
            merged_content=existing_wiki.get("content", ""),
            merged_structured_data=existing_wiki.get("structured_data", {}),
            merged_summary=existing_wiki.get("summary", ""),
            merged_aliases=list(set(
                (existing_wiki.get("aliases") or []) +
                (incoming_entity.get("aliases") or [])
            )),
            confidence=0.0,
            needs_review=True,
            reason=f"Merge agent error: {str(e)}. Queued for manual review.",
        )
