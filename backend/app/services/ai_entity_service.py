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


# Character archetype roles for AI context
ARCHETYPE_ROLES = {
    'PROTAGONIST': {'label': 'Protagonist', 'description': 'The main character whose journey drives the story'},
    'ANTAGONIST': {'label': 'Antagonist', 'description': 'The primary opposition to the protagonist'},
    'DEUTERAGONIST': {'label': 'Deuteragonist', 'description': 'The secondary main character, often the protagonist\'s closest ally'},
    'MENTOR': {'label': 'Mentor', 'description': 'A wise guide who helps the protagonist learn and grow'},
    'LOVE_INTEREST': {'label': 'Love Interest', 'description': 'A character who serves as the romantic focus'},
    'SIDEKICK': {'label': 'Sidekick', 'description': 'A loyal companion who supports the protagonist'},
    'FOIL': {'label': 'Foil', 'description': 'A character who contrasts with the protagonist'},
    'CATALYST': {'label': 'Catalyst', 'description': 'A character whose actions set the plot in motion'},
    'TRICKSTER': {'label': 'Trickster', 'description': 'A clever, mischievous character who uses wit and deception'},
    'HERALD': {'label': 'Herald', 'description': 'A character who announces change or calls to adventure'},
    'GUARDIAN': {'label': 'Guardian/Threshold', 'description': 'A character who tests the protagonist before allowing progress'},
    'SHAPESHIFTER': {'label': 'Shapeshifter', 'description': 'A character whose loyalty or nature is uncertain'},
}

# Character tropes for AI context
ARCHETYPE_TROPES = {
    'CHOSEN_ONE': {'label': 'The Chosen One', 'description': 'Destined by prophecy or fate to fulfill a special role'},
    'RELUCTANT_HERO': {'label': 'Reluctant Hero', 'description': 'Initially refuses the call to adventure but eventually accepts'},
    'ANTI_HERO': {'label': 'Anti-Hero', 'description': 'Lacks conventional heroic qualities like morality or idealism'},
    'TRAGIC_HERO': {'label': 'Tragic Hero', 'description': 'A noble character whose fatal flaw leads to their downfall'},
    'BYRONIC_HERO': {'label': 'Byronic Hero', 'description': 'Charismatic but flawed - brooding, cynical, with a dark past'},
    'EVERYMAN': {'label': 'Everyman', 'description': 'An ordinary person thrust into extraordinary circumstances'},
    'DARK_LORD': {'label': 'Dark Lord', 'description': 'A powerful evil entity seeking domination or destruction'},
    'WISE_OLD_WIZARD': {'label': 'Wise Old Wizard', 'description': 'An elderly magic user providing guidance and knowledge'},
    'FALLEN_NOBLE': {'label': 'Fallen Noble', 'description': 'Of high birth but has lost status and must rebuild'},
    'ENEMIES_TO_LOVERS': {'label': 'Enemies to Lovers', 'description': 'Characters who start as adversaries but develop romance'},
    'FRIENDS_TO_LOVERS': {'label': 'Friends to Lovers', 'description': 'Long-time friends who realize they have deeper feelings'},
    'GRUMPY_SUNSHINE': {'label': 'Grumpy/Sunshine', 'description': 'A pessimistic character paired with an optimistic one'},
    'FORBIDDEN_LOVE': {'label': 'Forbidden Love', 'description': 'Romance facing external opposition'},
    'HARDBOILED_DETECTIVE': {'label': 'Hardboiled Detective', 'description': 'A cynical, tough investigator in morally gray territory'},
    'FEMME_FATALE': {'label': 'Femme Fatale', 'description': 'A seductive, dangerous woman who uses allure to manipulate'},
    'GENTLEMAN_THIEF': {'label': 'Gentleman Thief', 'description': 'A charming criminal who steals with style and honor'},
    'FINAL_GIRL': {'label': 'Final Girl', 'description': 'The last survivor who confronts and defeats the antagonist'},
    'MAD_SCIENTIST': {'label': 'Mad Scientist', 'description': 'A brilliant but unethical researcher causing problems'},
    'SPACE_COWBOY': {'label': 'Space Cowboy', 'description': 'A roguish spacefarer on the fringes of society'},
    'HAUNTED_PAST': {'label': 'Haunted by the Past', 'description': 'Burdened by traumatic events affecting present behavior'},
    'HIDDEN_DEPTHS': {'label': 'Hidden Depths', 'description': 'Appears simple but reveals unexpected complexity'},
    'MAGNIFICENT_BASTARD': {'label': 'Magnificent Bastard', 'description': 'A villain so clever and charismatic audiences admire them'},
    'HEART_OF_GOLD': {'label': 'Heart of Gold', 'description': 'Rough exterior but kind and caring underneath'},
}


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

    # Character development fields (Brandon Sanderson methodology)
    "want": "what this character consciously desires - their surface-level goal that drives their immediate actions (e.g., revenge, wealth, love, power, recognition)",
    "need": "what this character truly needs for growth, often in conflict with their want - the deeper truth they must learn (e.g., forgiveness, self-acceptance, humility)",
    "flaw": "a significant character flaw that creates internal conflict and obstacles - this should be meaningful and affect their journey (e.g., pride, fear of commitment, distrust)",
    "strength": "their core strength or positive trait that will help them overcome challenges - what makes them capable of being the protagonist (e.g., determination, compassion, cleverness)",
    "arc": "a brief description of their character arc - how they will change from beginning to end, what they'll learn, and how their flaw relates to their need",

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

    # Culture fields
    "origin": "where and how this culture originated",
    "values.core_beliefs": "fundamental beliefs and worldview that guide behavior",
    "values.taboos": "strictly forbidden actions or topics",
    "values.ideals": "aspirational virtues and goals",
    "society.structure": "social organization (hierarchical, egalitarian, clan-based, etc.)",
    "society.roles": "how roles and responsibilities are assigned (by gender, birth, achievement, etc.)",
    "society.family_structure": "typical family units and kinship patterns",
    "traditions.rituals": "important ceremonies and practices",
    "traditions.celebrations": "holidays, festivals, and communal events",
    "traditions.rites_of_passage": "ceremonies marking life transitions",
    "arts.music": "musical traditions, instruments, and styles",
    "arts.visual_arts": "painting, sculpture, architecture, crafts",
    "arts.storytelling": "oral traditions, literature, mythology",
    "language": "language(s) spoken, dialects, writing systems",
    "religion": "spiritual beliefs, deities, religious practices",
    "conflicts": "internal tensions or conflicts with other cultures",
    "notable_figures": "famous individuals from this culture",

    # Race/Species fields
    "origin.homeworld": "where this race originated or evolved",
    "origin.creation_myth": "how this race believes they came to be",
    "origin.evolution": "how they developed their current form",
    "physical.appearance": "typical physical characteristics",
    "physical.lifespan": "how long they typically live",
    "physical.size_range": "typical height and build ranges",
    "physical.distinguishing_features": "features that set them apart from other races",
    "abilities.innate_powers": "natural abilities or magic",
    "abilities.weaknesses": "vulnerabilities or limitations",
    "abilities.special_senses": "enhanced or unique senses",
    "society.typical_culture": "common cultural traits across the race",
    "society.government": "how they typically organize politically",
    "society.relations_with_others": "how they interact with other races",
    "reproduction": "how they reproduce and raise young",
    "notable_individuals": "famous members of this race",
    "stereotypes": "common misconceptions or generalizations about them",
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

            # Handle character archetype information specially
            character_role = existing_data.get('character_role')
            character_tropes = existing_data.get('character_tropes', [])

            if character_role or character_tropes:
                archetype_context = []
                if character_role:
                    role_info = ARCHETYPE_ROLES.get(character_role)
                    if role_info:
                        archetype_context.append(f"Story Role: {role_info['label']} - {role_info['description']}")
                if character_tropes:
                    trope_descriptions = []
                    for trope_id in character_tropes:
                        trope_info = ARCHETYPE_TROPES.get(trope_id)
                        if trope_info:
                            trope_descriptions.append(f"- {trope_info['label']}: {trope_info['description']}")
                    if trope_descriptions:
                        archetype_context.append("Character Tropes:\n" + "\n".join(trope_descriptions))
                if archetype_context:
                    context_parts.append("Character Archetype:\n" + "\n".join(archetype_context))

            for key, value in self._flatten_dict(existing_data):
                # Skip archetype fields (already handled above) and empty values
                if value and key not in ('name', 'aliases', 'character_role', 'character_tropes'):
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

    async def extract_entity_from_selection(
        self,
        api_key: str,
        selected_text: str,
        surrounding_context: str,
        manuscript_genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze selected text and surrounding context to extract entity information

        Args:
            api_key: OpenRouter API key
            selected_text: The text the user selected (typically an entity name)
            surrounding_context: Text around the selection (before and after)
            manuscript_genre: Optional genre for better context

        Returns:
            Dict with extracted entity info: type, name, description, attributes
        """
        logger.info(f"Extracting entity info from selection: '{selected_text}'")

        system_prompt = """You are an expert at analyzing fiction text to identify and describe story entities.

Given a selected text (typically an entity name) and its surrounding context, extract information about this entity.

Respond with a JSON object containing:
{
  "type": "CHARACTER" | "LOCATION" | "ITEM" | "LORE",
  "name": "the entity's proper name",
  "description": "a brief description based on context clues",
  "suggested_aliases": ["any alternative names or titles mentioned"],
  "attributes": {
    "role": "their role if a character (protagonist, antagonist, supporting, etc.)",
    "appearance": "any physical description mentioned",
    "personality": "any personality traits evident",
    "notable_details": "other relevant details from context"
  },
  "confidence": "high" | "medium" | "low"
}

If information is not available from the context, use null for that field.
Only include attributes that can be reasonably inferred from the text."""

        user_prompt = f"""Analyze this entity from a story:

Selected text: "{selected_text}"

Surrounding context:
{surrounding_context}

{f"Genre: {manuscript_genre}" if manuscript_genre else ""}

Extract all available information about this entity from the context."""

        # Call OpenRouter
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="entity_extraction",
            max_tokens=800,
            temperature=0.3  # Lower temperature for more consistent extraction
        )

        if not result.get("success"):
            logger.error(f"Entity extraction failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", "AI extraction failed")
            }

        # Parse the JSON response
        suggestion = result.get("suggestion", "").strip()
        usage = result.get("usage", {})

        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', suggestion)
            if json_match:
                entity_data = json.loads(json_match.group())
            else:
                entity_data = json.loads(suggestion)

            return {
                "success": True,
                "entity_data": entity_data,
                "usage": usage,
                "cost": OpenRouterService.calculate_cost(usage)
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity JSON: {e}")
            # Return basic info derived from selection
            return {
                "success": True,
                "entity_data": {
                    "type": "CHARACTER",  # Default to character
                    "name": selected_text,
                    "description": None,
                    "suggested_aliases": [],
                    "attributes": {},
                    "confidence": "low"
                },
                "usage": usage,
                "cost": OpenRouterService.calculate_cost(usage),
                "parse_warning": "AI response was not valid JSON, using defaults"
            }


    async def generate_comprehensive_entity_fill(
        self,
        api_key: str,
        entity_name: str,
        entity_type: str,
        appearance_contexts: list,
        existing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive entity content from all appearance contexts

        Args:
            api_key: OpenRouter API key
            entity_name: Name of the entity
            entity_type: Type (CHARACTER, LOCATION, ITEM, LORE, CULTURE, CREATURE, RACE)
            appearance_contexts: List of {chapter_title, summary, context_text}
            existing_data: Dict with "attributes" and "template_data" keys

        Returns:
            Dict with generated description and attributes
        """
        logger.info(f"Generating comprehensive fill for {entity_name} from {len(appearance_contexts)} appearances")

        # Build context from all appearances
        appearances_text = "\n\n".join([
            f"Chapter: {ctx.get('chapter_title', 'Unknown')}\n"
            f"Summary: {ctx.get('summary', '')}\n"
            f"Context: {ctx.get('context_text', '') or 'N/A'}"
            for ctx in appearance_contexts[:20]  # Limit to 20 to avoid token limits
        ])

        # Extract attributes and template_data from existing_data
        attributes = existing_data.get("attributes", {}) if isinstance(existing_data, dict) else existing_data
        template_data = existing_data.get("template_data", {}) if isinstance(existing_data, dict) else {}

        # Build template context for AI if template_data exists
        template_context = ""
        if template_data:
            template_parts = []
            for key, value in self._flatten_dict(template_data):
                if value and key not in ('name',):
                    if isinstance(value, list):
                        template_parts.append(f"- {key}: {', '.join(str(v) for v in value)}")
                    else:
                        template_parts.append(f"- {key}: {value}")
            if template_parts:
                template_context = "\n\nESTABLISHED TEMPLATE DATA:\n" + "\n".join(template_parts)

        system_prompt = f"""You are an expert at analyzing fiction text to extract and synthesize information about story entities.

Given all the appearances of a {entity_type.lower()} named "{entity_name}" throughout a story, generate comprehensive details about them.

{"Consider the established template data when generating the description - incorporate relevant details like physical characteristics, abilities, culture, and origin into the description." if template_data else ""}

Respond with a JSON object containing:
{{
  "description": "A comprehensive description synthesized from all appearances (2-3 paragraphs). Include relevant details from template data if available.",
  "attributes": {{
    "appearance": "Physical description details found in the text",
    "personality": "Personality traits and behaviors observed",
    "background": "Background information and history mentioned",
    "role": "Their role in the story",
    "relationships": "Key relationships with other characters/entities mentioned",
    "notable_actions": "Important actions or events they're involved in"
  }},
  "suggested_aliases": ["any alternative names or titles used"]
}}

Only include attributes where you found evidence in the text. Use null for fields with no information."""

        user_prompt = f"""Analyze all appearances of "{entity_name}" and generate comprehensive details:

APPEARANCES:
{appearances_text}

{f"EXISTING ATTRIBUTES: {json.dumps(attributes)}" if attributes else ""}{template_context}

Generate comprehensive details based on these appearances{" and incorporate the established template data" if template_data else ""}."""

        # Call OpenRouter
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="entity_fill",
            max_tokens=1500,
            temperature=0.3
        )

        if not result.get("success"):
            logger.error(f"Entity fill failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", "AI generation failed")
            }

        # Parse the JSON response
        suggestion = result.get("suggestion", "").strip()
        usage = result.get("usage", {})

        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', suggestion)
            if json_match:
                entity_data = json.loads(json_match.group())
            else:
                entity_data = json.loads(suggestion)

            return {
                "success": True,
                "entity_data": entity_data,
                "usage": usage,
                "cost": OpenRouterService.calculate_cost(usage)
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity fill JSON: {e}")
            return {
                "success": True,
                "entity_data": {
                    "description": suggestion,
                    "attributes": {},
                    "suggested_aliases": []
                },
                "usage": usage,
                "cost": OpenRouterService.calculate_cost(usage),
                "parse_warning": "AI response was not valid JSON, using raw text as description"
            }


# Singleton instance
ai_entity_service = AIEntityService()
