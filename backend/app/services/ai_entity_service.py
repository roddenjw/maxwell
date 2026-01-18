"""
AI Entity Service - AI-powered entity field generation
Helps populate entity template fields with contextual suggestions
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)


# Template field prompts - guide the AI on what to generate
FIELD_PROMPTS = {
    # Character fields
    "physical.age": "a realistic age or age description",
    "physical.appearance": "a vivid physical description including height, build, hair color, eye color, and overall presence",
    "physical.distinguishing_features": "unique physical characteristics that make this character memorable (scars, tattoos, unusual features, distinctive mannerisms)",
    "personality.traits": "3-5 core personality traits that define their behavior",
    "personality.strengths": "what this character excels at, their best qualities",
    "personality.flaws": "meaningful character flaws that create internal conflict and room for growth",
    "backstory.origin": "where they come from, their childhood, and formative environment",
    "backstory.key_events": "pivotal life events that shaped who they are today",
    "backstory.secrets": "hidden aspects of their past they don't want others to know",
    "motivation.want": "their conscious surface-level goal or desire",
    "motivation.need": "what they actually need (often in conflict with their want)",

    # Location fields
    "geography.terrain": "the physical landscape and terrain features",
    "geography.climate": "weather patterns, seasons, and environmental conditions",
    "geography.size": "the scale and scope of this location",
    "atmosphere.mood": "the emotional feeling and ambiance of this place",
    "atmosphere.sounds": "the characteristic sounds one would hear",
    "atmosphere.smells": "the distinctive scents and aromas",
    "history.founded": "when and how this place came to be",
    "history.key_events": "important historical events that happened here",
    "history.current_state": "the present condition and situation",
    "notable_features": "distinctive landmarks or notable aspects",
    "inhabitants": "who lives or works here",
    "secrets": "hidden aspects or mysteries about this place",

    # Item fields
    "origin.creator": "who made this item and their story",
    "origin.creation_date": "when it was created",
    "origin.creation_story": "the circumstances and purpose of its creation",
    "properties.physical_description": "detailed visual description of the item",
    "properties.powers": "special abilities or magical properties",
    "properties.limitations": "restrictions, costs, or weaknesses",
    "history.previous_owners": "notable people who possessed it",
    "history.notable_events": "significant moments in its history",
    "current_owner": "who has it now",
    "significance": "why this item matters to the story",

    # Magic System fields
    "source": "where the magic comes from",
    "rules.how_it_works": "the fundamental mechanics and principles",
    "rules.limitations": "what magic cannot do",
    "rules.costs": "the price or toll of using magic",
    "users.who_can_use": "who has access to this magic and why",
    "users.how_learned": "how practitioners gain and develop abilities",
    "users.organizations": "groups or institutions that practice this magic",
    "effects": "the types of effects this magic can produce",
    "weaknesses": "how magic can be countered or nullified",
    "cultural_impact": "how magic affects society and culture",

    # Creature fields
    "species": "classification and species name",
    "habitat": "where these creatures live",
    "physical.appearance": "what they look like",
    "physical.size": "typical size range",
    "physical.distinguishing_features": "unique physical characteristics",
    "behavior.temperament": "typical behavior and demeanor",
    "behavior.diet": "what they eat",
    "behavior.social_structure": "how they organize socially",
    "abilities": "special abilities or powers",
    "weaknesses": "vulnerabilities and weaknesses",
    "cultural_significance": "how they're viewed by people in the world",

    # Organization fields
    "purpose": "the organization's goals and mission",
    "structure.leadership": "who leads and how leadership is determined",
    "structure.hierarchy": "ranks, roles, and structure",
    "structure.membership_requirements": "how one joins",
    "history.founding": "when and why it was founded",
    "history.key_events": "important moments in its history",
    "history.current_status": "its present state and influence",
    "resources": "money, assets, and capabilities",
    "allies": "allied groups or individuals",
    "enemies": "opposing forces",
    "secrets": "hidden agendas or activities",
}


class AIEntityService:
    """Service for AI-powered entity field generation"""

    async def generate_field_suggestion(
        self,
        api_key: str,
        entity_name: str,
        entity_type: str,
        template_type: str,
        field_path: str,
        existing_data: Dict[str, Any],
        manuscript_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a suggestion for a specific entity field

        Args:
            api_key: OpenRouter API key
            entity_name: Name of the entity
            entity_type: Type (CHARACTER, LOCATION, ITEM, LORE)
            template_type: Template type (CHARACTER, LOCATION, ITEM, MAGIC_SYSTEM, etc.)
            field_path: Which field to generate (e.g., "physical.appearance")
            existing_data: Already filled template fields for context
            manuscript_context: Optional story context from manuscript

        Returns:
            Dict with success, suggestion, and usage info
        """
        logger.info(f"Generating suggestion for {entity_name}.{field_path}")

        # Build the prompt
        field_hint = FIELD_PROMPTS.get(field_path, f"appropriate content for the {field_path.replace('.', ' ')} field")

        system_prompt = f"""You are a creative writing assistant helping an author develop a {template_type.lower()} for their story.

Your task is to generate {field_hint} for a {template_type.lower()} named "{entity_name}".

Guidelines:
- Be specific and evocative, avoiding generic descriptions
- Match the tone and style implied by the entity name and existing details
- Create content that could inspire interesting story developments
- Keep your response focused and appropriately sized for the field
- Write in a way that's easy for the author to edit and build upon

Respond with ONLY the content for this field - no explanations, no field labels, no formatting."""

        # Build context from existing data
        context_parts = []

        if existing_data:
            filled_fields = []
            for key, value in self._flatten_dict(existing_data):
                if value and key != 'name' and key != 'aliases':
                    if isinstance(value, list):
                        filled_fields.append(f"- {key}: {', '.join(str(v) for v in value)}")
                    else:
                        filled_fields.append(f"- {key}: {value}")

            if filled_fields:
                context_parts.append("Already established details:\n" + "\n".join(filled_fields))

        if manuscript_context:
            context_parts.append(f"Story context:\n{manuscript_context[:2000]}")

        user_prompt = f"Generate {field_hint} for {entity_name}."

        if context_parts:
            user_prompt = "\n\n".join(context_parts) + "\n\n" + user_prompt

        # Call OpenRouter
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="entity_field",
            max_tokens=500,
            temperature=0.7
        )

        if not result.get("success"):
            logger.error(f"Field generation failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", "AI generation failed")
            }

        suggestion = result.get("suggestion", "").strip()
        usage = result.get("usage", {})

        # For tags/list fields, try to parse into a list
        if field_path.endswith(('.traits', '.effects', '.abilities', '.notable_features')):
            # Try to split on newlines or commas
            if '\n' in suggestion:
                suggestion = [s.strip().lstrip('- •') for s in suggestion.split('\n') if s.strip()]
            elif ',' in suggestion:
                suggestion = [s.strip() for s in suggestion.split(',') if s.strip()]

        return {
            "success": True,
            "suggestion": suggestion,
            "usage": usage,
            "cost": OpenRouterService.calculate_cost(usage)
        }

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> list:
        """Flatten nested dict to list of (key, value) tuples"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key))
            else:
                items.append((new_key, v))
        return items


# Singleton instance
ai_entity_service = AIEntityService()
