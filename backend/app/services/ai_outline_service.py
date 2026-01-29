"""
AI Outline Service - AI-powered outline analysis and suggestions
Uses OpenRouter API with Claude 3.5 Sonnet for intelligent story structure insights
"""

import httpx
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.outline import Outline, PlotBeat
from app.models.manuscript import Manuscript, Chapter
from app.services.openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)


def _get_manuscript_context(db: Session, outline: Outline) -> str:
    """
    Extract manuscript chapter content for AI context

    Strategy:
    1. Include FULL TEXT of chapters linked to plot beats (most relevant)
    2. Include first 5,000 chars of other chapters for context
    3. Limit to ~10 total chapters (prevents massive prompts)

    Cost: ~30,000 tokens = $0.09 per analysis (reasonable for quality results)

    Args:
        db: Database session
        outline: Outline object

    Returns:
        String with chapter content for AI analysis
    """
    logger.info(f"Getting manuscript context for outline {outline.id}, manuscript {outline.manuscript_id}")

    # Get chapters linked to this outline's plot beats
    linked_chapter_ids = [
        beat.chapter_id
        for beat in outline.plot_beats
        if beat.chapter_id
    ]

    logger.info(f"Found {len(linked_chapter_ids)} linked chapters")

    linked_chapters = []
    if linked_chapter_ids:
        linked_chapters = db.query(Chapter).filter(
            Chapter.id.in_(linked_chapter_ids),
            Chapter.is_folder == 0
        ).order_by(Chapter.order_index).all()

    # Get other chapters (early in manuscript) for general context
    other_chapters_query = db.query(Chapter).filter(
        Chapter.manuscript_id == outline.manuscript_id,
        Chapter.is_folder == 0
    )

    if linked_chapter_ids:
        other_chapters_query = other_chapters_query.filter(
            ~Chapter.id.in_(linked_chapter_ids)
        )

    other_chapters = other_chapters_query.order_by(Chapter.order_index).limit(10).all()

    logger.info(f"Found {len(other_chapters)} other chapters")

    if not linked_chapters and not other_chapters:
        logger.warning("No chapters found for context")
        return "No chapters written yet."

    # Build chapter excerpts
    chapter_excerpts = []

    # 1. Add linked chapters with FULL TEXT (highest priority)
    for ch in linked_chapters:
        content = ch.content if ch.content else "[Empty chapter]"
        chapter_excerpts.append(f"## {ch.title} [LINKED TO BEAT]\n{content}")
        logger.info(f"Added linked chapter: {ch.title}, content length: {len(content)}")

    # 2. Add other chapters with excerpts (5,000 chars = ~1,000 words)
    remaining_slots = max(0, 10 - len(linked_chapters))
    for ch in other_chapters[:remaining_slots]:
        if ch.content:
            excerpt = ch.content[:5000]
            suffix = "..." if len(ch.content) > 5000 else ""
            chapter_excerpts.append(f"## {ch.title}\n{excerpt}{suffix}")
            logger.info(f"Added chapter excerpt: {ch.title}, excerpt length: {len(excerpt)}")
        else:
            chapter_excerpts.append(f"## {ch.title}\n[Empty chapter]")
            logger.info(f"Added empty chapter: {ch.title}")

    result = "\n\n".join(chapter_excerpts)
    logger.info(f"Total manuscript context length: {len(result)} characters")
    return result


class AIOutlineService:
    """Service for AI-powered outline analysis"""

    def __init__(self, api_key: str):
        """
        Initialize with user's OpenRouter API key (BYOK pattern)

        Args:
            api_key: User's OpenRouter API key
        """
        self.openrouter = OpenRouterService(api_key)
        self.api_key = api_key

    async def generate_beat_descriptions(
        self,
        outline: Outline,
        beats: List[PlotBeat],
        db: Session,
        feedback: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered descriptions for plot beats with manuscript context

        Args:
            outline: Outline object with premise and structure info
            beats: List of PlotBeat objects
            db: Database session
            feedback: Optional user feedback on previous suggestions
                     Format: {beatName: {liked: [], disliked: [], notes: ""}}

        Returns:
            Dict with beat descriptions and usage info
        """
        try:
            # Get manuscript context from chapters
            logger.info(f"🎬 Generating beat descriptions for outline {outline.id}")
            manuscript_context = _get_manuscript_context(db, outline)
            logger.info(f"📝 Manuscript context retrieved: {len(manuscript_context)} characters")

            # Build prompt with outline context
            system_prompt = """You are a professional story editor analyzing a SPECIFIC manuscript.
Your task is to describe what ACTUALLY HAPPENS in this author's story, not what SHOULD happen in a generic story.

CRITICAL: You MUST reference specific characters, events, and plot points from the manuscript chapters provided.
DO NOT write generic beat descriptions like "Introduce the protagonist" or "Present the conflict."
INSTEAD write story-specific descriptions like "Jarn offers the protagonist a choice between returning to life or accepting death."

If a beat hasn't been written yet, analyze the chapters provided and suggest what could happen next based on the existing story."""

            # Prepare beat info for analysis
            beat_info = []
            for beat in beats:
                beat_info.append({
                    "beat_name": beat.beat_name,
                    "beat_label": beat.beat_label,
                    "position": f"{int(beat.target_position_percent * 100)}%",
                    "order": beat.order_index
                })

            # Build feedback context if provided
            feedback_context = ""
            if feedback:
                feedback_sections = []
                for beat_name, fb in feedback.items():
                    if fb.get("liked") or fb.get("disliked") or fb.get("notes"):
                        fb_text = f"\n**Feedback for {beat_name}:**"
                        if fb.get("liked"):
                            fb_text += f"\n  - LIKED suggestions about: {', '.join(fb['liked'])}"
                        if fb.get("disliked"):
                            fb_text += f"\n  - DISLIKED suggestions about: {', '.join(fb['disliked'])}"
                        if fb.get("notes"):
                            fb_text += f"\n  - Additional notes: {fb['notes']}"
                        feedback_sections.append(fb_text)
                if feedback_sections:
                    feedback_context = "\n\n**USER FEEDBACK ON PREVIOUS SUGGESTIONS:**" + "".join(feedback_sections) + "\n\nIMPORTANT: Use this feedback to refine your suggestions. Generate NEW suggestions that align with what the user liked and avoid what they disliked.\n"

            user_prompt = f"""You are analyzing an ACTUAL MANUSCRIPT (see chapters below), not creating a template.

**Manuscript Chapters:**
{manuscript_context}

**Plot Beats to Describe:**
{json.dumps(beat_info, indent=2)}

**Story Context:**
- Premise: {outline.premise or "Infer from the chapters above"}
- Genre: {outline.genre or "General fiction"}
- Target Length: {outline.target_word_count:,} words
{feedback_context}
INSTRUCTIONS:
1. Read the manuscript chapters carefully
2. For each beat, describe what ACTUALLY happens in THIS STORY (not generic advice)
3. MUST mention specific character names, locations, or events from the chapters
4. If a beat hasn't been written, suggest what could happen next based on existing chapters

EXAMPLE OF GOOD RESPONSE:
"The protagonist awakens in a twilight realm and meets Jarn, a peculiar man with a crooked nose who sits before an empty throne. Jarn speaks in riddles about relativity and choices, setting up the central mystery of where the protagonist is and why."

EXAMPLE OF BAD RESPONSE (DO NOT DO THIS):
"Introduce your protagonist in their ordinary world. Show who they are and what they want."

Respond in JSON format:
{{
  "beat_descriptions": {{
    "beat_name": "2-3 sentence description mentioning SPECIFIC story elements",
    ...
  }}
}}"""

            # Make API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter.BASE_URL}/chat/completions",
                    headers=self.openrouter.headers,
                    json={
                        "model": self.openrouter.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 3000,  # Increased for detailed story-specific responses
                        "temperature": 0.6,  # Slightly lower for more focused responses
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code}")

                    # Handle specific error codes with user-friendly messages
                    if response.status_code == 402:
                        return {
                            "success": False,
                            "error": "insufficient_credits",
                            "message": "Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits to continue using AI features."
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Your OpenRouter API key is invalid. Please check your API key in Settings."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"api_error_{response.status_code}",
                            "message": f"OpenRouter API error: {response.status_code}"
                        }

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Log the raw AI response for debugging
                logger.info("="*80)
                logger.info("AI RESPONSE FOR BEAT DESCRIPTIONS:")
                logger.info(f"Response length: {len(content)} characters")
                logger.info(f"First 500 chars: {content[:500]}")
                logger.info("="*80)

                parsed = json.loads(content)

                return {
                    "success": True,
                    "beat_descriptions": parsed.get("beat_descriptions", {}),
                    "usage": data.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Beat description generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_beat_content_suggestions(
        self,
        beat: PlotBeat,
        outline: Outline,
        previous_beats: List[PlotBeat],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate specific scene ideas and content suggestions for a single beat
        with full manuscript context and Codex entities.

        Args:
            beat: PlotBeat to generate suggestions for
            outline: Parent outline with premise
            previous_beats: List of beats that come before this one
            db: Database session for fetching manuscript context and entities

        Returns:
            Dict with content suggestions and usage info
        """
        try:
            # Build manuscript context if database session available
            manuscript_context = ""
            entity_context = ""

            if db and outline.manuscript_id:
                # Get manuscript content for context
                manuscript_context = _get_manuscript_context(db, outline)
                if manuscript_context == "No chapters written yet.":
                    manuscript_context = ""

                # Get Codex entities for the manuscript
                from app.models.entity import Entity
                entities = db.query(Entity).filter(
                    Entity.manuscript_id == outline.manuscript_id
                ).all()

                if entities:
                    entity_summaries = []
                    for entity in entities[:20]:  # Limit to 20 entities to control prompt size
                        summary = f"- **{entity.name}** ({entity.type})"
                        if entity.attributes:
                            # Add key attributes
                            attrs = entity.attributes
                            if attrs.get('description'):
                                summary += f": {attrs['description'][:150]}"
                            elif attrs.get('role'):
                                summary += f": {attrs['role']}"
                        entity_summaries.append(summary)

                    entity_context = "\n**Characters & Entities from Codex:**\n" + "\n".join(entity_summaries)

            system_prompt = """You are a creative writing consultant helping authors brainstorm scenes for THEIR SPECIFIC STORY.

CRITICAL RULES:
1. You MUST reference the actual characters, locations, and events from the manuscript and Codex
2. DO NOT invent new characters - use the ones the author has already created
3. If the manuscript has existing content, your suggestions must logically follow from what's written
4. Be specific - mention character names, established relationships, and existing plot elements

Provide 3-5 specific, concrete scene ideas or character moments for the given plot beat."""

            # Build context from previous beats
            previous_context = ""
            if previous_beats:
                prev_summaries = []
                for prev in previous_beats[-3:]:  # Last 3 beats for context
                    if prev.user_notes:
                        prev_summaries.append(f"- {prev.beat_label}: {prev.user_notes[:200]}")
                    elif prev.beat_description:
                        prev_summaries.append(f"- {prev.beat_label}: {prev.beat_description[:150]}")
                if prev_summaries:
                    previous_context = "\n**Previous beats in outline:**\n" + "\n".join(prev_summaries)

            # Build manuscript excerpt (limited for token efficiency)
            manuscript_excerpt = ""
            if manuscript_context:
                # Truncate to ~3000 chars for beat suggestions (keep it focused)
                manuscript_excerpt = f"\n**Manuscript Excerpt (for context):**\n{manuscript_context[:3000]}"
                if len(manuscript_context) > 3000:
                    manuscript_excerpt += "...\n[truncated for brevity]"

            user_prompt = f"""Suggest 3-5 specific scenes, conflicts, or character moments for this plot beat.

**Story Context:**
- Premise: {outline.premise or "Infer from manuscript below"}
- Genre: {outline.genre or "General fiction"}
- Target Length: {outline.target_word_count:,} words
{entity_context}
{manuscript_excerpt}

**Current Beat:** {beat.beat_label} ({beat.beat_name})
**Position:** {int(beat.target_position_percent * 100)}% through story
**Beat Description:** {beat.beat_description or "Not provided"}
**Target Word Count:** {beat.target_word_count:,} words
{previous_context}

IMPORTANT: Your suggestions MUST use the actual characters and settings from the manuscript/Codex above.
DO NOT suggest generic placeholders like "the protagonist" - use their actual names.

Provide concrete, specific suggestions that:
- Use actual character names from the Codex
- Reference established locations and relationships
- Build on existing story events
- Fit this beat's narrative purpose

Format as a JSON array of suggestion objects:
{{
  "suggestions": [
    {{
      "type": "scene|character|dialogue|subplot",
      "title": "Brief title (use character names)",
      "description": "2-3 sentence detailed suggestion using specific story elements"
    }},
    ...
  ]
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter.BASE_URL}/chat/completions",
                    headers=self.openrouter.headers,
                    json={
                        "model": self.openrouter.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.8,  # Higher for creativity
                        "response_format": {"type": "json_object"}
                    },
                    timeout=45.0
                )

                if response.status_code != 200:
                    # Handle specific error codes with user-friendly messages
                    if response.status_code == 402:
                        return {
                            "success": False,
                            "error": "insufficient_credits",
                            "message": "Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits to continue using AI features."
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Your OpenRouter API key is invalid. Please check your API key in Settings."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"api_error_{response.status_code}",
                            "message": f"OpenRouter API error: {response.status_code}"
                        }

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                return {
                    "success": True,
                    "suggestions": parsed.get("suggestions", []),
                    "usage": data.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Content suggestion generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def detect_plot_holes(
        self,
        outline: Outline,
        beats: List[PlotBeat],
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze outline for plot holes with manuscript context and validation

        Args:
            outline: Outline object
            beats: List of all plot beats with notes
            db: Database session

        Returns:
            Dict with detected plot holes and usage info
        """
        try:
            # Get manuscript context
            manuscript_context = _get_manuscript_context(db, outline)

            # Check if we have enough data to analyze
            beats_with_content = [
                b for b in beats
                if b.user_notes or b.content_summary or b.chapter_id
            ]

            if not beats_with_content and manuscript_context == "No chapters written yet.":
                return {
                    "success": True,
                    "plot_holes": [],
                    "overall_assessment": "Not enough content to analyze yet. Write some chapters or add notes to plot beats, then try again."
                }

            system_prompt = """You are a plot consistency analyst reading a SPECIFIC manuscript.
Your task is to identify plot holes and inconsistencies in the ACTUAL STORY, not provide generic writing advice.

CRITICAL: You must reference specific story elements (character names, events, locations) when identifying problems.
DO NOT give generic feedback like "The protagonist needs stronger motivation."
INSTEAD give story-specific feedback like "Why does Jarn offer the protagonist this choice? His motivation is unclear."

If you find no significant plot holes, explain why the story is coherent so far."""

            # Build outline summary with beat notes and chapter content
            beat_summaries = []
            for beat in sorted(beats, key=lambda b: b.order_index):
                summary = f"{beat.beat_label} ({int(beat.target_position_percent * 100)}%)"
                if beat.beat_description:
                    summary += f": {beat.beat_description}"
                if beat.user_notes:
                    summary += f"\n  Notes: {beat.user_notes}"
                if beat.content_summary:
                    summary += f"\n  Written: {beat.content_summary}"
                beat_summaries.append(summary)

            user_prompt = f"""Analyze THIS SPECIFIC MANUSCRIPT for plot holes and inconsistencies.

**Manuscript Chapters (Read Carefully):**
{manuscript_context}

**Plot Structure ({outline.structure_type}):**
{chr(10).join(beat_summaries)}

INSTRUCTIONS:
1. Read the manuscript chapters carefully
2. Look for actual plot holes in THIS story (not generic issues)
3. Reference specific characters, events, and story elements
4. If no major issues, explain why the story is coherent

Look for:
- Character inconsistencies or unclear motivations (mention character names)
- Timeline problems (reference specific events)
- Unresolved setups (cite what was set up)
- Logic errors (explain the contradiction)
- Missing explanations (specify what's unclear)

EXAMPLE OF GOOD FEEDBACK:
"The protagonist awakens in a mysterious realm but we don't know how they died or why they're in this specific place. Jarn's purpose is unclear - is he judging the protagonist?"

EXAMPLE OF BAD FEEDBACK (DO NOT DO THIS):
"The story needs stronger world-building and clearer stakes."

Respond in JSON format:
{{
  "plot_holes": [
    {{
      "severity": "high|medium|low",
      "location": "Which chapter or beat",
      "issue": "Specific plot hole with story details",
      "suggestion": "How to fix it in this story"
    }}
  ],
  "overall_assessment": "1-2 sentence assessment of THIS STORY's coherence"
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter.BASE_URL}/chat/completions",
                    headers=self.openrouter.headers,
                    json={
                        "model": self.openrouter.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.5,  # Lower for analytical work
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    # Handle specific error codes with user-friendly messages
                    if response.status_code == 402:
                        return {
                            "success": False,
                            "error": "insufficient_credits",
                            "message": "Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits to continue using AI features."
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Your OpenRouter API key is invalid. Please check your API key in Settings."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"api_error_{response.status_code}",
                            "message": f"OpenRouter API error: {response.status_code}"
                        }

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                return {
                    "success": True,
                    "plot_holes": parsed.get("plot_holes", []),
                    "overall_assessment": parsed.get("overall_assessment", ""),
                    "usage": data.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Plot hole detection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_pacing(
        self,
        outline: Outline,
        beats: List[PlotBeat]
    ) -> Dict[str, Any]:
        """
        Analyze story pacing and structure balance

        Args:
            outline: Outline object
            beats: List of all plot beats

        Returns:
            Dict with pacing analysis and usage info
        """
        try:
            system_prompt = """You are a story pacing expert analyzing narrative structure.
Evaluate:
- Act distribution and balance (should follow structure conventions)
- Beat spacing and rhythm
- Climax positioning and buildup
- Resolution length and satisfying conclusion
- Overall story flow and momentum

Provide a score (0-10) and specific, actionable recommendations."""

            # Calculate act distribution
            act_distribution = {"act1": 0, "act2": 0, "act3": 0}
            beat_positions = []

            for beat in sorted(beats, key=lambda b: b.order_index):
                pos = beat.target_position_percent
                if pos <= 0.25:
                    act_distribution["act1"] += 1
                elif pos <= 0.75:
                    act_distribution["act2"] += 1
                else:
                    act_distribution["act3"] += 1

                beat_positions.append({
                    "name": beat.beat_label,
                    "position": f"{int(pos * 100)}%",
                    "target_words": beat.target_word_count,
                    "actual_words": beat.actual_word_count
                })

            user_prompt = f"""Analyze the pacing and structure balance of this outline:

**Structure Type:** {outline.structure_type}

**Target Length:** {outline.target_word_count:,} words

**Act Distribution:**
- Act 1: {act_distribution['act1']} beats
- Act 2: {act_distribution['act2']} beats
- Act 3: {act_distribution['act3']} beats

**Beat Positions and Word Counts:**
{json.dumps(beat_positions, indent=2)}

Evaluate:
1. Is the act distribution appropriate for {outline.structure_type}?
2. Are beats well-spaced throughout the story?
3. Is the climax positioned correctly?
4. Is there enough resolution?
5. Are word counts balanced appropriately?

Respond in JSON format:
{{
  "overall_score": 7.5,
  "act_balance": {{
    "act1_percent": 0.25,
    "act2_percent": 0.50,
    "act3_percent": 0.25
  }},
  "issues": [
    "List of specific pacing problems"
  ],
  "recommendations": [
    "Specific, actionable recommendations to improve pacing"
  ],
  "strengths": [
    "What's working well in the current structure"
  ]
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter.BASE_URL}/chat/completions",
                    headers=self.openrouter.headers,
                    json={
                        "model": self.openrouter.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.5,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    # Handle specific error codes with user-friendly messages
                    if response.status_code == 402:
                        return {
                            "success": False,
                            "error": "insufficient_credits",
                            "message": "Your OpenRouter API key has insufficient credits. Please add credits at https://openrouter.ai/credits to continue using AI features."
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Your OpenRouter API key is invalid. Please check your API key in Settings."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"api_error_{response.status_code}",
                            "message": f"OpenRouter API error: {response.status_code}"
                        }

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                return {
                    "success": True,
                    "pacing_analysis": parsed,
                    "usage": data.get("usage", {})
                }

        except Exception as e:
            logger.error(f"Pacing analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_full_analysis(
        self,
        outline_id: str,
        db: Session,
        analysis_types: Optional[List[str]] = None,
        feedback: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run complete AI analysis on outline (all or selected types)

        Args:
            outline_id: ID of outline to analyze
            db: Database session
            analysis_types: List of analysis types to run (default: all)
                          Options: ["beat_descriptions", "content_suggestions", "plot_holes", "pacing"]
            feedback: Optional user feedback on previous suggestions for refinement
                     Format: {beatName: {liked: [], disliked: [], notes: ""}}

        Returns:
            Dict with all analysis results and total usage/cost
        """
        if analysis_types is None:
            analysis_types = ["beat_descriptions", "plot_holes", "pacing"]

        try:
            # Fetch outline and beats
            outline = db.query(Outline).filter(Outline.id == outline_id).first()
            if not outline:
                return {
                    "success": False,
                    "error": "Outline not found"
                }

            beats = sorted(outline.plot_beats, key=lambda b: b.order_index)

            results = {
                "success": True,
                "data": {}
            }
            total_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            # Run selected analyses
            if "beat_descriptions" in analysis_types:
                desc_result = await self.generate_beat_descriptions(outline, beats, db, feedback)
                if desc_result["success"]:
                    results["data"]["beat_descriptions"] = desc_result["beat_descriptions"]
                    usage = desc_result.get("usage", {})
                    total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                    total_usage["total_tokens"] += usage.get("total_tokens", 0)

            if "plot_holes" in analysis_types:
                holes_result = await self.detect_plot_holes(outline, beats, db)
                if holes_result["success"]:
                    results["data"]["plot_holes"] = holes_result["plot_holes"]
                    results["data"]["overall_assessment"] = holes_result.get("overall_assessment", "")
                    usage = holes_result.get("usage", {})
                    total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                    total_usage["total_tokens"] += usage.get("total_tokens", 0)

            if "pacing" in analysis_types:
                pacing_result = await self.analyze_pacing(outline, beats)
                if pacing_result["success"]:
                    results["data"]["pacing_analysis"] = pacing_result["pacing_analysis"]
                    usage = pacing_result.get("usage", {})
                    total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                    total_usage["total_tokens"] += usage.get("total_tokens", 0)

            # Calculate cost
            cost = OpenRouterService.calculate_cost(total_usage)

            results["usage"] = total_usage
            results["cost"] = {
                "total_usd": round(cost, 4),
                "formatted": f"${cost:.4f}"
            }

            return results

        except Exception as e:
            logger.error(f"Full analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_bridge_scenes(
        self,
        from_beat: PlotBeat,
        to_beat: PlotBeat,
        outline: Outline,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate scene suggestions to bridge the gap between two beats.

        This AI-powered feature helps writers create scenes that naturally
        connect major story beats, ensuring smooth narrative flow.

        Args:
            from_beat: The beat to start from
            to_beat: The beat to arrive at
            outline: The outline containing these beats
            db: Database session

        Returns:
            Dict with scene suggestions and usage info
        """
        try:
            # Get manuscript context for more relevant suggestions
            manuscript_context = _get_manuscript_context(db, outline)

            system_prompt = """You are a master storyteller helping bridge two story beats with compelling scenes.
Your suggestions should:
- Create natural narrative flow between the beats
- Maintain consistent tone and pacing
- Develop characters and relationships
- Build tension or provide necessary relief
- Set up future events organically"""

            user_prompt = f"""A writer needs help bridging the gap between two story beats.

**Story Context:**
- Genre: {outline.genre or "Not specified"}
- Structure: {outline.structure_type}
- Premise: {outline.premise or "Not specified"}
- Target Length: {outline.target_word_count:,} words

**FROM BEAT ({int(from_beat.target_position_percent * 100)}% through story):**
Title: {from_beat.beat_label}
Description: {from_beat.beat_description or "No description"}
Writer's Notes: {from_beat.user_notes or "No notes"}

**TO BEAT ({int(to_beat.target_position_percent * 100)}% through story):**
Title: {to_beat.beat_label}
Description: {to_beat.beat_description or "No description"}
Writer's Notes: {to_beat.user_notes or "No notes"}

**Manuscript Excerpts:**
{manuscript_context[:5000]}

Generate 2-3 scene suggestions that would naturally bridge these beats.

For each scene provide:
1. A compelling title
2. A detailed description (2-3 sentences) of what happens
3. The emotional purpose (what the reader should feel)
4. Suggested word count (typically 500-1500 words for bridge scenes)

Respond in JSON format:
{{
  "scenes": [
    {{
      "title": "Scene title",
      "description": "What happens in the scene...",
      "emotional_purpose": "How this advances the emotional journey",
      "suggested_word_count": 1000
    }}
  ],
  "bridging_analysis": "Brief explanation of the narrative gap and how these scenes fill it"
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter.BASE_URL}/chat/completions",
                    headers=self.openrouter.headers,
                    json={
                        "model": self.openrouter.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,  # Balanced creativity
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    if response.status_code == 402:
                        return {
                            "success": False,
                            "error": "insufficient_credits",
                            "message": "Your OpenRouter API key has insufficient credits."
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Your OpenRouter API key is invalid."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"api_error_{response.status_code}",
                            "message": f"OpenRouter API error: {response.status_code}"
                        }

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                # Calculate cost
                usage = data.get("usage", {})
                cost = OpenRouterService.calculate_cost(usage)

                return {
                    "success": True,
                    "scenes": parsed.get("scenes", []),
                    "bridging_analysis": parsed.get("bridging_analysis", ""),
                    "from_beat_id": from_beat.id,
                    "to_beat_id": to_beat.id,
                    "usage": usage,
                    "cost": {
                        "total_usd": round(cost, 4),
                        "formatted": f"${cost:.4f}"
                    }
                }

        except Exception as e:
            logger.error(f"Bridge scene generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
