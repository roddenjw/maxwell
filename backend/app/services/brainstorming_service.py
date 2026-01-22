"""
Brainstorming Service - AI-powered idea generation for writing
Implements Brandon Sanderson's character methodology and other proven techniques
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.brainstorm import BrainstormSession, BrainstormIdea
from app.models.entity import Entity
from app.models.outline import PlotBeat
from app.services.openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)


class BrainstormingService:
    """Orchestrates AI-powered brainstorming sessions"""

    def __init__(self, db: Session):
        self.db = db

    # ===== Session Management =====

    def create_session(
        self,
        manuscript_id: str,
        session_type: str,
        context_data: Dict[str, Any],
        outline_id: Optional[str] = None
    ) -> BrainstormSession:
        """Create a new brainstorming session"""
        session = BrainstormSession(
            manuscript_id=manuscript_id,
            outline_id=outline_id,
            session_type=session_type,
            context_data=context_data,
            status='IN_PROGRESS'
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created brainstorming session {session.id} of type {session_type}")
        return session

    def get_session(self, session_id: str) -> Optional[BrainstormSession]:
        """Get session with all ideas"""
        return self.db.query(BrainstormSession).filter(
            BrainstormSession.id == session_id
        ).first()

    def get_manuscript_sessions(self, manuscript_id: str) -> List[BrainstormSession]:
        """Get all sessions for a manuscript"""
        return self.db.query(BrainstormSession).filter(
            BrainstormSession.manuscript_id == manuscript_id
        ).order_by(BrainstormSession.created_at.desc()).all()

    def update_session_status(self, session_id: str, status: str) -> BrainstormSession:
        """Update session status"""
        session = self.get_session(session_id)
        if session:
            session.status = status
            self.db.commit()
            self.db.refresh(session)
        return session

    # ===== Character Generation (Brandon Sanderson Methodology) =====

    async def generate_character_ideas(
        self,
        session_id: str,
        api_key: str,
        genre: str,
        existing_characters: List[Entity],
        story_premise: str,
        character_ideas: Optional[str] = None,
        num_ideas: int = 5
    ) -> List[BrainstormIdea]:
        """
        Generate character development ideas using AI

        Uses Brandon Sanderson's methodology:
        - WANT: What does the character want on the surface?
        - NEED: What do they actually need (often unknown to them)?
        - FLAW: What personal weakness holds them back?
        - STRENGTH: What unique ability or trait defines them?
        - ARC: How will they change from beginning to end?
        """
        logger.info(f"Generating {num_ideas} character ideas for session {session_id}")

        # Build prompts
        system_prompt, user_prompt = self._build_character_prompt(
            genre=genre,
            existing_characters=[char.name for char in existing_characters],
            story_premise=story_premise,
            character_ideas=character_ideas,
            num_ideas=num_ideas
        )

        # Call OpenRouter with response_format to enforce JSON
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="character",
            max_tokens=2000,  # Allow for detailed character responses
            temperature=0.6,  # Lower temp for structured output
            response_format={"type": "json_object"}  # Enforce JSON at API level
        )

        if not result.get("success"):
            logger.error(f"Character generation failed: {result.get('error')}")
            raise Exception(f"AI generation failed: {result.get('error')}")

        # Parse AI response
        ai_response = result["suggestion"]
        characters = self._parse_character_response(ai_response)

        # Calculate cost
        usage = result.get("usage", {})
        cost_per_character = OpenRouterService.calculate_cost(usage) / len(characters) if characters else 0

        # Create BrainstormIdea records
        ideas = []
        for char_data in characters:
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='CHARACTER',
                title=char_data.get('name', 'Unnamed Character'),
                description=self._format_character_description(char_data),
                idea_metadata=char_data,  # Store full character data
                ai_cost=cost_per_character,
                ai_tokens=usage.get("total_tokens", 0) // len(characters),
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            ideas.append(idea)

        self.db.commit()

        # Refresh all ideas to get IDs
        for idea in ideas:
            self.db.refresh(idea)

        logger.info(f"Created {len(ideas)} character ideas")
        return ideas

    def _build_character_prompt(
        self,
        genre: str,
        existing_characters: List[str],
        story_premise: str,
        character_ideas: Optional[str],
        num_ideas: int
    ) -> tuple[str, str]:
        """Build character brainstorming prompt using Brandon Sanderson's methodology"""

        system_prompt = f"""You are a JSON-generating character development assistant.

Your ONLY task is to generate valid JSON objects. You MUST NOT include any conversational text, explanations, or commentary.

Character development approach:
- WANT: What does the character want on the surface?
- NEED: What do they actually need (often unknown to them)?
- FLAW: What personal weakness holds them back?
- STRENGTH: What unique ability or trait defines them?
- ARC: How will they change from beginning to end?

Genre context: {genre}

CRITICAL: Your response must be a valid JSON object starting with {{ and ending with }}. The root object must have a "characters" key with an array of character objects. No other text is allowed."""

        existing_context = ""
        if existing_characters:
            existing_context = f"\n\nExisting Characters: {', '.join(existing_characters)}"

        ideas_context = ""
        if character_ideas and character_ideas.strip():
            ideas_context = f"\n\nWriter's Initial Character Ideas: {character_ideas.strip()}\nDevelop these ideas into full characters with wants, needs, flaws, strengths, and arcs."

        user_prompt = f"""Story Premise: {story_premise}{existing_context}{ideas_context}

Create {num_ideas} character concepts. For each character, provide a JSON object with these exact fields:

{{
  "name": "Character name",
  "role": "Their role in the story (protagonist, antagonist, mentor, etc.)",
  "want": "Surface-level goal or desire",
  "need": "Deeper emotional/psychological need",
  "flaw": "Major character flaw or weakness",
  "strength": "Key strength or unique ability",
  "arc": "Anticipated character transformation",
  "hook": "One-sentence compelling hook",
  "relationships": "Potential relationships with existing characters",
  "story_potential": "How they could drive plot and conflict"
}}

Return a valid JSON object with this exact structure:
{{
  "characters": [
    {{ character object 1 }},
    {{ character object 2 }},
    ...
  ]
}}

CRITICAL RULES:
1. Start your response with {{ (opening brace)
2. Root must be an object with "characters" key containing an array
3. End your response with }} (closing brace)
4. NO introductory text like "Here are" or "Thank you"
5. NO explanations or comments
6. NO markdown code blocks or formatting
7. ONLY valid JSON object

Your response must be parseable by JSON.parse(). Anything else will fail."""

        return system_prompt, user_prompt

    def _parse_character_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response into character data

        Expected format with response_format enforcement: {"characters": [...]}
        Legacy support: [...] or single object {...}
        """
        try:
            # Direct parse - response_format ensures valid JSON
            parsed = json.loads(ai_response)

            # Handle object format: {"characters": [...]}
            if isinstance(parsed, dict) and "characters" in parsed:
                return parsed["characters"]
            # Legacy array format support: [...]
            elif isinstance(parsed, list):
                return parsed
            # Single object: {...}
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ValueError(f"Unexpected JSON structure: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response (first 500 chars): {ai_response[:500]}")
            raise ValueError(f"Could not parse AI response as JSON: {e}")

    def _format_character_description(self, char_data: Dict[str, Any]) -> str:
        """Format character data into readable description"""
        description = f"""**{char_data.get('name', 'Unnamed Character')}** - {char_data.get('role', 'Character')}

{char_data.get('hook', '')}

**What They Want**: {char_data.get('want', 'Unknown')}
**What They Need**: {char_data.get('need', 'Unknown')}
**Fatal Flaw**: {char_data.get('flaw', 'Unknown')}
**Key Strength**: {char_data.get('strength', 'Unknown')}
**Character Arc**: {char_data.get('arc', 'Unknown')}

**Relationships**: {char_data.get('relationships', 'To be determined')}

**Story Potential**: {char_data.get('story_potential', 'Unknown')}"""

        return description

    # ===== Plot Generation =====

    async def generate_plot_ideas(
        self,
        session_id: str,
        api_key: str,
        genre: str,
        premise: str,
        existing_beats: List[PlotBeat],
        num_ideas: int = 5
    ) -> List[BrainstormIdea]:
        """
        Generate plot ideas (conflicts, twists, subplots)

        Plot elements include:
        - CENTRAL CONFLICT: The main story tension
        - PLOT TWIST: Unexpected turns that change everything
        - SUBPLOT: Secondary storylines that enrich the narrative
        - COMPLICATION: Obstacles and challenges
        """
        logger.info(f"Generating {num_ideas} plot ideas for session {session_id}")

        # Build prompts
        system_prompt, user_prompt = self._build_plot_prompt(
            genre=genre,
            premise=premise,
            existing_beats=[beat.beat_label for beat in existing_beats],
            num_ideas=num_ideas
        )

        # Call OpenRouter with response_format to enforce JSON
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="plot",
            max_tokens=2500,  # Allow for detailed plot responses
            temperature=0.6,  # Lower temp for structured output
            response_format={"type": "json_object"}  # Enforce JSON at API level
        )

        if not result.get("success"):
            logger.error(f"Plot generation failed: {result.get('error')}")
            raise Exception(f"AI generation failed: {result.get('error')}")

        # Parse AI response
        ai_response = result["suggestion"]
        plots = self._parse_plot_response(ai_response)

        # Calculate cost
        usage = result.get("usage", {})
        cost_per_plot = OpenRouterService.calculate_cost(usage) / len(plots) if plots else 0

        # Create BrainstormIdea records
        ideas = []
        for plot_data in plots:
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='PLOT_BEAT',
                title=plot_data.get('title', 'Untitled Plot Idea'),
                description=self._format_plot_description(plot_data),
                idea_metadata=plot_data,  # Store full plot data
                ai_cost=cost_per_plot,
                ai_tokens=usage.get("total_tokens", 0) // len(plots),
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            ideas.append(idea)

        self.db.commit()

        # Refresh all ideas to get IDs
        for idea in ideas:
            self.db.refresh(idea)

        logger.info(f"Created {len(ideas)} plot ideas")
        return ideas

    def _build_plot_prompt(
        self,
        genre: str,
        premise: str,
        existing_beats: List[str],
        num_ideas: int
    ) -> tuple[str, str]:
        """Build plot brainstorming prompt"""

        system_prompt = f"""You are a JSON-generating plot development assistant.

Your ONLY task is to generate valid JSON objects. You MUST NOT include any conversational text, explanations, or commentary.

Plot development approach:
- CENTRAL CONFLICT: The main tension driving the story
- PLOT TWIST: Unexpected revelations that change everything
- SUBPLOT: Secondary storylines that enrich the main plot
- COMPLICATION: Obstacles and challenges that raise stakes

Genre context: {genre}

CRITICAL: Your response must be a valid JSON object starting with {{ and ending with }}. The root object must have a "plots" key with an array of plot objects. No other text is allowed."""

        existing_context = ""
        if existing_beats:
            existing_context = f"\n\nExisting Plot Beats: {', '.join(existing_beats)}"

        user_prompt = f"""Story Premise: {premise}{existing_context}

Create {num_ideas} unique plot ideas. For each plot element, provide a JSON object with these exact fields:

{{
  "type": "central_conflict" | "plot_twist" | "subplot" | "complication",
  "title": "Compelling one-line hook",
  "description": "Detailed explanation of the plot element",
  "setup": "How to introduce this element",
  "escalation": "How the stakes/tension increase",
  "resolution": "Potential ways this could resolve",
  "stakes": "What's at risk or what characters could gain/lose",
  "connects_to": "How this ties to other story elements",
  "beat_position": "Suggested story position (early/middle/late)"
}}

Return a valid JSON object with this exact structure:
{{
  "plots": [
    {{ plot object 1 }},
    {{ plot object 2 }},
    ...
  ]
}}

CRITICAL RULES:
1. Start your response with {{ (opening brace)
2. Root must be an object with "plots" key containing an array
3. End your response with }} (closing brace)
4. NO introductory text like "Here are" or "Thank you"
5. NO explanations or comments
6. NO markdown code blocks or formatting
7. ONLY valid JSON object

Your response must be parseable by JSON.parse(). Anything else will fail."""

        return system_prompt, user_prompt

    def _parse_plot_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response into plot data

        Expected format with response_format enforcement: {"plots": [...]}
        Legacy support: [...] or single object {...}
        """
        try:
            # Direct parse - response_format ensures valid JSON
            parsed = json.loads(ai_response)

            # Handle object format: {"plots": [...]}
            if isinstance(parsed, dict) and "plots" in parsed:
                return parsed["plots"]
            # Legacy array format support: [...]
            elif isinstance(parsed, list):
                return parsed
            # Single object: {...}
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ValueError(f"Unexpected JSON structure: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response (first 500 chars): {ai_response[:500]}")
            raise ValueError(f"Could not parse AI response as JSON: {e}")

    def _format_plot_description(self, plot_data: Dict[str, Any]) -> str:
        """Format plot data into readable description"""
        plot_type = plot_data.get('type', 'plot element').replace('_', ' ').title()

        description = f"""**{plot_data.get('title', 'Untitled Plot')}** - {plot_type}

{plot_data.get('description', '')}

**Setup**: {plot_data.get('setup', 'To be determined')}

**How It Escalates**: {plot_data.get('escalation', 'To be determined')}

**Potential Resolution**: {plot_data.get('resolution', 'To be determined')}

**Stakes**: {plot_data.get('stakes', 'Unknown')}

**Connections**: {plot_data.get('connects_to', 'Standalone element')}

**Suggested Position**: {plot_data.get('beat_position', 'Flexible')}"""

        return description

    # ===== Location/Setting Generation =====

    async def generate_location_ideas(
        self,
        session_id: str,
        api_key: str,
        genre: str,
        premise: str,
        existing_locations: List[Entity],
        num_ideas: int = 5
    ) -> List[BrainstormIdea]:
        """
        Generate location/setting ideas with worldbuilding details

        Location elements include:
        - ATMOSPHERE: Mood and sensory details
        - CULTURE: Social norms and customs
        - GEOGRAPHY: Physical layout and environment
        - HISTORY: Backstory and significance
        - STORY_ROLE: How this location serves the narrative
        """
        logger.info(f"Generating {num_ideas} location ideas for session {session_id}")

        # Build prompts
        system_prompt, user_prompt = self._build_location_prompt(
            genre=genre,
            premise=premise,
            existing_locations=[loc.name for loc in existing_locations],
            num_ideas=num_ideas
        )

        # Call OpenRouter with response_format to enforce JSON
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="setting",
            max_tokens=2500,  # Allow for detailed worldbuilding responses
            temperature=0.6,  # Lower temp for structured output
            response_format={"type": "json_object"}  # Enforce JSON at API level
        )

        if not result.get("success"):
            logger.error(f"Location generation failed: {result.get('error')}")
            raise Exception(f"AI generation failed: {result.get('error')}")

        # Parse AI response
        ai_response = result["suggestion"]
        locations = self._parse_location_response(ai_response)

        # Calculate cost
        usage = result.get("usage", {})
        cost_per_location = OpenRouterService.calculate_cost(usage) / len(locations) if locations else 0

        # Create BrainstormIdea records
        ideas = []
        for location_data in locations:
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='WORLD',  # Maps to Entity type LOCATION
                title=location_data.get('name', 'Unnamed Location'),
                description=self._format_location_description(location_data),
                idea_metadata=location_data,  # Store full location data
                ai_cost=cost_per_location,
                ai_tokens=usage.get("total_tokens", 0) // len(locations),
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            ideas.append(idea)

        self.db.commit()

        # Refresh all ideas to get IDs
        for idea in ideas:
            self.db.refresh(idea)

        logger.info(f"Created {len(ideas)} location ideas")
        return ideas

    def _build_location_prompt(
        self,
        genre: str,
        premise: str,
        existing_locations: List[str],
        num_ideas: int
    ) -> tuple[str, str]:
        """Build location/setting brainstorming prompt"""

        system_prompt = f"""You are an expert fiction writing coach specializing in worldbuilding and setting creation.

Your approach focuses on creating immersive, multi-dimensional locations:
- ATMOSPHERE: Sensory details, mood, and feeling
- CULTURE: Social norms, customs, and inhabitants
- GEOGRAPHY: Physical layout, environment, and landmarks
- HISTORY: Backstory, significance, and evolution
- STORY_ROLE: How this location serves the narrative

Genre context: {genre}

Focus on creating locations that:
1. Feel vivid and immersive through specific sensory details
2. Have logical internal consistency
3. Serve clear narrative purposes
4. Offer opportunities for conflict and character development
5. Complement but contrast with existing settings

Provide {num_ideas} distinct location concepts in JSON format."""

        existing_context = ""
        if existing_locations:
            existing_context = f"\n\nExisting Locations: {', '.join(existing_locations)}"

        user_prompt = f"""Story Premise: {premise}{existing_context}

Please create {num_ideas} unique location/setting ideas. Each location should be a JSON object with these exact fields:

{{
  "name": "Location name",
  "type": "city" | "building" | "wilderness" | "realm" | "other",
  "atmosphere": "Mood and sensory details (sights, sounds, smells)",
  "culture": "Social norms, customs, inhabitants",
  "geography": "Physical layout, environment, landmarks",
  "history": "Backstory and significance",
  "story_role": "How this location serves the narrative",
  "secrets": "Hidden elements or mysteries",
  "hook": "One-sentence compelling description"
}}

Return a valid JSON object with this exact structure:
{{
  "locations": [
    {{ location object 1 }},
    {{ location object 2 }},
    ...
  ]
}}

CRITICAL RULES:
1. Start your response with {{ (opening brace)
2. Root must be an object with "locations" key containing an array
3. End your response with }} (closing brace)
4. NO introductory text like "Here are" or "Thank you"
5. NO explanations or comments
6. NO markdown code blocks or formatting
7. ONLY valid JSON object

Your response must be parseable by JSON.parse(). Anything else will fail."""

        return system_prompt, user_prompt

    def _parse_location_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response into location data

        Expected format with response_format enforcement: {"locations": [...]}
        Legacy support: [...] or single object {...}
        """
        try:
            # Direct parse - response_format ensures valid JSON
            parsed = json.loads(ai_response)

            # Handle object format: {"locations": [...]}
            if isinstance(parsed, dict) and "locations" in parsed:
                return parsed["locations"]
            # Legacy array format support: [...]
            elif isinstance(parsed, list):
                return parsed
            # Single object: {...}
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ValueError(f"Unexpected JSON structure: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response (first 500 chars): {ai_response[:500]}")
            raise ValueError(f"Could not parse AI response as JSON: {e}")

    def _format_location_description(self, location_data: Dict[str, Any]) -> str:
        """Format location data into readable description"""
        location_type = location_data.get('type', 'location').title()

        description = f"""**{location_data.get('name', 'Unnamed Location')}** - {location_type}

{location_data.get('hook', '')}

**Atmosphere**: {location_data.get('atmosphere', 'Unknown')}

**Culture & Inhabitants**: {location_data.get('culture', 'Unknown')}

**Geography**: {location_data.get('geography', 'Unknown')}

**History**: {location_data.get('history', 'Unknown')}

**Story Role**: {location_data.get('story_role', 'To be determined')}

**Secrets**: {location_data.get('secrets', 'None yet discovered')}"""

        return description

    # ===== Integration Methods =====

    async def integrate_idea_to_codex(
        self,
        idea_id: str,
        entity_type: Optional[str] = None
    ) -> Entity:
        """
        Integrate brainstorm idea into Codex as new entity

        Args:
            idea_id: The brainstorm idea to integrate
            entity_type: Optional entity type override (defaults to idea type)
        """
        idea = self.db.query(BrainstormIdea).filter(BrainstormIdea.id == idea_id).first()
        if not idea:
            raise ValueError(f"Brainstorm idea {idea_id} not found")

        # Get session to find manuscript
        session = self.get_session(idea.session_id)
        if not session:
            raise ValueError(f"Session {idea.session_id} not found")

        # Determine entity type
        if not entity_type:
            entity_type = idea.idea_type  # CHARACTER, LOCATION, etc.

        # Create entity from idea
        entity = Entity(
            manuscript_id=session.manuscript_id,
            type=entity_type,
            name=idea.title,
            attributes=idea.idea_metadata  # Store all character data (want, need, flaw, etc.)
        )

        # Add brainstorm source tracking
        entity.attributes['brainstorm_source_id'] = idea_id
        entity.attributes['description'] = idea.edited_content if idea.edited_content else idea.description

        self.db.add(entity)

        # Update idea integration status
        idea.integrated_to_codex = True
        idea.entity_id = entity.id

        self.db.commit()
        self.db.refresh(entity)

        logger.info(f"Integrated brainstorm idea {idea_id} to codex entity {entity.id}")
        return entity

    # ===== Idea Management =====

    def update_idea(
        self,
        idea_id: str,
        updates: Dict[str, Any]
    ) -> BrainstormIdea:
        """Update idea (selection, notes, edited content)"""
        idea = self.db.query(BrainstormIdea).filter(BrainstormIdea.id == idea_id).first()
        if not idea:
            raise ValueError(f"Idea {idea_id} not found")

        # Update allowed fields
        if 'is_selected' in updates:
            idea.is_selected = updates['is_selected']
        if 'user_notes' in updates:
            idea.user_notes = updates['user_notes']
        if 'edited_content' in updates:
            idea.edited_content = updates['edited_content']

        self.db.commit()
        self.db.refresh(idea)

        return idea

    def delete_idea(self, idea_id: str) -> bool:
        """Delete a brainstorm idea"""
        idea = self.db.query(BrainstormIdea).filter(BrainstormIdea.id == idea_id).first()
        if idea:
            self.db.delete(idea)
            self.db.commit()
            return True
        return False

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        session = self.get_session(session_id)
        if not session:
            return {}

        ideas = session.ideas
        total_cost = sum(idea.ai_cost for idea in ideas)
        total_tokens = sum(idea.ai_tokens for idea in ideas)
        selected_count = sum(1 for idea in ideas if idea.is_selected)
        integrated_count = sum(1 for idea in ideas if idea.integrated_to_codex or idea.integrated_to_outline)

        return {
            'session_id': session_id,
            'session_type': session.session_type,
            'status': session.status,
            'total_ideas': len(ideas),
            'selected_ideas': selected_count,
            'integrated_ideas': integrated_count,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'created_at': session.created_at.isoformat(),
        }

    # ===== Idea Refinement =====

    async def refine_idea(
        self,
        original_idea: BrainstormIdea,
        api_key: str,
        feedback: str,
        direction: str = "refine",
        combine_with: Optional[BrainstormIdea] = None
    ) -> BrainstormIdea:
        """
        Refine an existing idea based on user feedback.

        Directions:
        - refine: Tweak the idea based on specific feedback
        - expand: Add more depth and detail
        - contrast: Create an opposing/contrasting version
        - combine: Merge elements from two ideas
        """
        logger.info(f"Refining idea {original_idea.id} with direction: {direction}")

        # Build refinement prompt based on idea type
        system_prompt, user_prompt = self._build_refinement_prompt(
            original_idea=original_idea,
            feedback=feedback,
            direction=direction,
            combine_with=combine_with
        )

        # Call OpenRouter
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="refinement",
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Refinement failed: {result.get('error')}")

        # Parse response
        ai_response = result["suggestion"]
        refined_data = self._parse_refinement_response(ai_response, original_idea.idea_type)

        # Calculate cost
        usage = result.get("usage", {})
        cost = OpenRouterService.calculate_cost(usage)

        # Create new refined idea
        refined_idea = BrainstormIdea(
            session_id=original_idea.session_id,
            idea_type=original_idea.idea_type,
            title=refined_data.get('name', refined_data.get('title', original_idea.title + ' (Refined)')),
            description=self._format_refined_description(refined_data, original_idea.idea_type),
            idea_metadata={
                **refined_data,
                'refined_from': original_idea.id,
                'refinement_direction': direction,
                'refinement_feedback': feedback
            },
            ai_cost=cost,
            ai_tokens=usage.get("total_tokens", 0),
            ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
        )

        self.db.add(refined_idea)
        self.db.commit()
        self.db.refresh(refined_idea)

        logger.info(f"Created refined idea {refined_idea.id} from {original_idea.id}")
        return refined_idea

    def _build_refinement_prompt(
        self,
        original_idea: BrainstormIdea,
        feedback: str,
        direction: str,
        combine_with: Optional[BrainstormIdea]
    ) -> tuple[str, str]:
        """Build prompt for idea refinement"""

        idea_type = original_idea.idea_type
        original_content = json.dumps(original_idea.idea_metadata, indent=2)

        direction_instructions = {
            "refine": "Refine and improve this idea while maintaining its core essence. Apply the user's specific feedback.",
            "expand": "Expand this idea with much more depth, detail, and nuance. Add layers of complexity.",
            "contrast": "Create a compelling contrasting version - if the original is dark, make it lighter; if serious, make it humorous, etc.",
            "combine": "Merge the best elements of both ideas into a cohesive new concept."
        }

        system_prompt = f"""You are a JSON-generating creative writing assistant specializing in {idea_type.lower()} development.

Your task is to {direction_instructions.get(direction, direction_instructions['refine'])}

Return a single refined {idea_type.lower()} as a valid JSON object.

CRITICAL: Your response must be a valid JSON object starting with {{ and ending with }}. No other text is allowed."""

        combine_context = ""
        if combine_with:
            combine_context = f"\n\nSecond idea to combine with:\n{json.dumps(combine_with.idea_metadata, indent=2)}"

        if idea_type == 'CHARACTER':
            json_structure = """{
  "name": "Character name",
  "role": "Story role",
  "want": "Surface desire",
  "need": "Deeper need",
  "flaw": "Character flaw",
  "strength": "Key strength",
  "arc": "Character arc",
  "hook": "Compelling hook",
  "relationships": "Key relationships",
  "story_potential": "Story potential"
}"""
        elif idea_type == 'PLOT_BEAT':
            json_structure = """{
  "type": "plot element type",
  "title": "Plot title",
  "description": "Description",
  "setup": "How to set it up",
  "escalation": "How it escalates",
  "resolution": "How it resolves",
  "stakes": "What's at stake",
  "connects_to": "Connections",
  "beat_position": "Position in story"
}"""
        else:  # WORLD/LOCATION
            json_structure = """{
  "name": "Location name",
  "type": "Location type",
  "atmosphere": "Mood and sensory details",
  "culture": "Culture and inhabitants",
  "geography": "Physical layout",
  "history": "Backstory",
  "story_role": "Narrative function",
  "secrets": "Hidden elements",
  "hook": "Compelling hook"
}"""

        user_prompt = f"""Original {idea_type}:
{original_content}
{combine_context}

User Feedback: {feedback}

Please create a refined version that incorporates this feedback. Return as JSON:
{json_structure}

ONLY return the JSON object, nothing else."""

        return system_prompt, user_prompt

    def _parse_refinement_response(self, ai_response: str, idea_type: str) -> Dict[str, Any]:
        """Parse refinement AI response"""
        try:
            parsed = json.loads(ai_response)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError(f"Unexpected response format: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Could not parse AI response: {e}")

    def _format_refined_description(self, data: Dict[str, Any], idea_type: str) -> str:
        """Format refined idea into description based on type"""
        if idea_type == 'CHARACTER':
            return self._format_character_description(data)
        elif idea_type == 'PLOT_BEAT':
            return self._format_plot_description(data)
        else:
            return self._format_location_description(data)

    # ===== Conflict Generation =====

    async def generate_conflict_ideas(
        self,
        session_id: str,
        api_key: str,
        genre: str,
        premise: str,
        characters: List[Entity],
        conflict_type: str = "any",
        num_ideas: int = 5
    ) -> List[BrainstormIdea]:
        """
        Generate conflict scenario ideas.

        Conflict types:
        - internal: Inner struggles, moral dilemmas
        - interpersonal: Between characters
        - external: Character vs environment/society
        - societal: Larger systemic conflicts
        - any: Mix of all types
        """
        logger.info(f"Generating {num_ideas} conflict ideas for session {session_id}")

        system_prompt, user_prompt = self._build_conflict_prompt(
            genre=genre,
            premise=premise,
            characters=characters,
            conflict_type=conflict_type,
            num_ideas=num_ideas
        )

        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="conflict",
            max_tokens=2500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Conflict generation failed: {result.get('error')}")

        ai_response = result["suggestion"]
        conflicts = self._parse_conflict_response(ai_response)

        usage = result.get("usage", {})
        cost_per_conflict = OpenRouterService.calculate_cost(usage) / len(conflicts) if conflicts else 0

        ideas = []
        for conflict_data in conflicts:
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='CONFLICT',
                title=conflict_data.get('title', 'Untitled Conflict'),
                description=self._format_conflict_description(conflict_data),
                idea_metadata=conflict_data,
                ai_cost=cost_per_conflict,
                ai_tokens=usage.get("total_tokens", 0) // len(conflicts),
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            ideas.append(idea)

        self.db.commit()
        for idea in ideas:
            self.db.refresh(idea)

        logger.info(f"Created {len(ideas)} conflict ideas")
        return ideas

    def _build_conflict_prompt(
        self,
        genre: str,
        premise: str,
        characters: List[Entity],
        conflict_type: str,
        num_ideas: int
    ) -> tuple[str, str]:
        """Build conflict generation prompt"""

        type_instruction = ""
        if conflict_type != "any":
            type_descriptions = {
                "internal": "internal conflicts (character vs self, moral dilemmas, inner demons)",
                "interpersonal": "interpersonal conflicts (character vs character, relationships, betrayals)",
                "external": "external conflicts (character vs nature, environment, obstacles)",
                "societal": "societal conflicts (character vs system, institutions, cultural norms)"
            }
            type_instruction = f"\n\nFocus specifically on {type_descriptions.get(conflict_type, 'varied conflicts')}."

        system_prompt = f"""You are a JSON-generating conflict development assistant for {genre} fiction.

Your task is to create compelling, layered conflicts that drive narrative tension.{type_instruction}

CRITICAL: Your response must be a valid JSON object with a "conflicts" array. No other text allowed."""

        char_context = ""
        if characters:
            char_list = [f"- {c.name}: {c.attributes.get('role', 'Character')}" for c in characters]
            char_context = f"\n\nAvailable Characters:\n" + "\n".join(char_list)

        user_prompt = f"""Story Premise: {premise}{char_context}

Create {num_ideas} compelling conflict scenarios. Each conflict should be a JSON object:

{{
  "title": "Conflict title (punchy, evocative)",
  "type": "internal" | "interpersonal" | "external" | "societal",
  "participants": ["Character names involved"],
  "core_tension": "The fundamental opposition or struggle",
  "stakes": "What could be gained or lost",
  "trigger": "What initiates this conflict",
  "escalation_points": ["How the conflict intensifies over time"],
  "possible_resolutions": ["Different ways this could resolve"],
  "emotional_core": "The underlying emotional truth",
  "scene_opportunities": ["Specific scenes this conflict enables"],
  "thematic_connection": "How this ties to larger story themes"
}}

Return as:
{{
  "conflicts": [...]
}}"""

        return system_prompt, user_prompt

    def _parse_conflict_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse conflict AI response"""
        try:
            parsed = json.loads(ai_response)
            if isinstance(parsed, dict) and "conflicts" in parsed:
                return parsed["conflicts"]
            elif isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            raise ValueError(f"Unexpected format: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Could not parse AI response: {e}")

    def _format_conflict_description(self, data: Dict[str, Any]) -> str:
        """Format conflict into readable description"""
        conflict_type = data.get('type', 'conflict').replace('_', ' ').title()
        participants = ", ".join(data.get('participants', ['Unknown']))

        description = f"""**{data.get('title', 'Untitled Conflict')}** - {conflict_type}

**Participants**: {participants}

**Core Tension**: {data.get('core_tension', 'Unknown')}

**Stakes**: {data.get('stakes', 'Unknown')}

**Trigger**: {data.get('trigger', 'Unknown')}

**Escalation Points**:
{chr(10).join('• ' + p for p in data.get('escalation_points', ['To be determined']))}

**Possible Resolutions**:
{chr(10).join('• ' + r for r in data.get('possible_resolutions', ['To be determined']))}

**Emotional Core**: {data.get('emotional_core', 'Unknown')}

**Scene Opportunities**:
{chr(10).join('• ' + s for s in data.get('scene_opportunities', ['To be explored']))}

**Thematic Connection**: {data.get('thematic_connection', 'To be determined')}"""

        return description

    # ===== Scene Generation =====

    async def generate_scene_ideas(
        self,
        session_id: str,
        api_key: str,
        genre: str,
        premise: str,
        characters: List[Entity],
        location: Optional[Entity],
        beat: Optional[PlotBeat],
        scene_purpose: str = "any",
        num_ideas: int = 3
    ) -> List[BrainstormIdea]:
        """Generate scene ideas with structure and beats"""
        logger.info(f"Generating {num_ideas} scene ideas for session {session_id}")

        system_prompt, user_prompt = self._build_scene_prompt(
            genre=genre,
            premise=premise,
            characters=characters,
            location=location,
            beat=beat,
            scene_purpose=scene_purpose,
            num_ideas=num_ideas
        )

        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="scene",
            max_tokens=3000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Scene generation failed: {result.get('error')}")

        ai_response = result["suggestion"]
        scenes = self._parse_scene_response(ai_response)

        usage = result.get("usage", {})
        cost_per_scene = OpenRouterService.calculate_cost(usage) / len(scenes) if scenes else 0

        ideas = []
        for scene_data in scenes:
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='SCENE',
                title=scene_data.get('title', 'Untitled Scene'),
                description=self._format_scene_description(scene_data),
                idea_metadata=scene_data,
                ai_cost=cost_per_scene,
                ai_tokens=usage.get("total_tokens", 0) // len(scenes),
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            ideas.append(idea)

        self.db.commit()
        for idea in ideas:
            self.db.refresh(idea)

        logger.info(f"Created {len(ideas)} scene ideas")
        return ideas

    def _build_scene_prompt(
        self,
        genre: str,
        premise: str,
        characters: List[Entity],
        location: Optional[Entity],
        beat: Optional[PlotBeat],
        scene_purpose: str,
        num_ideas: int
    ) -> tuple[str, str]:
        """Build scene generation prompt"""

        purpose_instruction = ""
        if scene_purpose != "any":
            purpose_descriptions = {
                "introduction": "introductory scenes that establish characters, world, or stakes",
                "conflict": "conflict scenes with rising tension and opposition",
                "revelation": "revelation scenes where key information is discovered",
                "climax": "climactic scenes with peak emotional/action intensity",
                "resolution": "resolution scenes that provide closure or transition"
            }
            purpose_instruction = f"\n\nFocus on {purpose_descriptions.get(scene_purpose, 'varied scene types')}."

        system_prompt = f"""You are a JSON-generating scene development assistant for {genre} fiction.

Create vivid, structurally sound scene concepts with clear beats and emotional arcs.{purpose_instruction}

CRITICAL: Your response must be a valid JSON object with a "scenes" array. No other text allowed."""

        context_parts = [f"Story Premise: {premise}"]

        if characters:
            char_list = [f"- {c.name}: {c.attributes.get('hook', c.attributes.get('role', 'Character'))}" for c in characters]
            context_parts.append("Characters:\n" + "\n".join(char_list))

        if location:
            context_parts.append(f"Location: {location.name} - {location.attributes.get('atmosphere', 'Unknown atmosphere')}")

        if beat:
            context_parts.append(f"Plot Beat: {beat.beat_label} - {beat.description or 'No description'}")

        user_prompt = f"""{chr(10).join(context_parts)}

Create {num_ideas} scene ideas. Each scene should be a JSON object:

{{
  "title": "Scene title (evocative, specific)",
  "purpose": "introduction" | "conflict" | "revelation" | "climax" | "resolution",
  "pov_character": "Whose perspective",
  "characters_present": ["All characters in scene"],
  "location": "Where the scene takes place",
  "opening_hook": "First line or image that pulls readers in",
  "scene_goal": "What the POV character wants in this scene",
  "obstacle": "What stands in their way",
  "outcome": "disaster" | "partial_success" | "success" | "twist",
  "emotional_arc": {{
    "start": "Emotional state at beginning",
    "shift": "What causes the emotional change",
    "end": "Emotional state at end"
  }},
  "scene_beats": [
    "Beat 1: Setup/establishing moment",
    "Beat 2: Goal revealed/conflict introduced",
    "Beat 3: Rising tension",
    "Beat 4: Peak moment/turning point",
    "Beat 5: Outcome/transition"
  ],
  "sensory_details": ["Key sensory moments to include"],
  "dialogue_moments": ["Key exchanges or lines"],
  "subtext": "What's happening beneath the surface"
}}

Return as:
{{
  "scenes": [...]
}}"""

        return system_prompt, user_prompt

    def _parse_scene_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse scene AI response"""
        try:
            parsed = json.loads(ai_response)
            if isinstance(parsed, dict) and "scenes" in parsed:
                return parsed["scenes"]
            elif isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            raise ValueError(f"Unexpected format: {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Could not parse AI response: {e}")

    def _format_scene_description(self, data: Dict[str, Any]) -> str:
        """Format scene into readable description"""
        purpose = data.get('purpose', 'scene').title()
        characters = ", ".join(data.get('characters_present', ['Unknown']))

        emotional_arc = data.get('emotional_arc', {})
        beats = data.get('scene_beats', ['To be developed'])

        description = f"""**{data.get('title', 'Untitled Scene')}** - {purpose} Scene

**POV**: {data.get('pov_character', 'Unknown')}
**Characters**: {characters}
**Location**: {data.get('location', 'Unknown')}

**Opening Hook**: {data.get('opening_hook', 'To be written')}

**Scene Goal**: {data.get('scene_goal', 'Unknown')}
**Obstacle**: {data.get('obstacle', 'Unknown')}
**Outcome**: {data.get('outcome', 'Unknown').replace('_', ' ').title()}

**Emotional Arc**:
• Start: {emotional_arc.get('start', 'Unknown')}
• Shift: {emotional_arc.get('shift', 'Unknown')}
• End: {emotional_arc.get('end', 'Unknown')}

**Scene Beats**:
{chr(10).join('• ' + b for b in beats)}

**Sensory Details**:
{chr(10).join('• ' + s for s in data.get('sensory_details', ['To be explored']))}

**Key Dialogue Moments**:
{chr(10).join('• ' + d for d in data.get('dialogue_moments', ['To be written']))}

**Subtext**: {data.get('subtext', 'To be developed')}"""

        return description

    # ===== Character Development Worksheets =====

    async def generate_character_worksheet(
        self,
        session_id: str,
        api_key: str,
        character: Optional[Entity],
        character_name: Optional[str],
        worksheet_type: str,
        other_characters: List[Entity]
    ) -> Dict[str, Any]:
        """Generate a deep character development worksheet"""
        logger.info(f"Generating {worksheet_type} worksheet for session {session_id}")

        name = character.name if character else character_name
        existing_data = character.attributes if character else {}

        system_prompt, user_prompt = self._build_worksheet_prompt(
            name=name,
            existing_data=existing_data,
            worksheet_type=worksheet_type,
            other_characters=other_characters
        )

        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="worksheet",
            max_tokens=3500,
            temperature=0.6,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Worksheet generation failed: {result.get('error')}")

        ai_response = result["suggestion"]
        worksheet = json.loads(ai_response)

        # Add metadata
        usage = result.get("usage", {})
        worksheet['_metadata'] = {
            'character_id': character.id if character else None,
            'character_name': name,
            'worksheet_type': worksheet_type,
            'ai_cost': OpenRouterService.calculate_cost(usage),
            'ai_tokens': usage.get("total_tokens", 0)
        }

        # If character exists, optionally update their attributes
        if character:
            # Store worksheet in idea for reference
            idea = BrainstormIdea(
                session_id=session_id,
                idea_type='CHARACTER_WORKSHEET',
                title=f"{name} - {worksheet_type.title()} Worksheet",
                description=self._format_worksheet_description(worksheet, worksheet_type),
                idea_metadata=worksheet,
                ai_cost=worksheet['_metadata']['ai_cost'],
                ai_tokens=worksheet['_metadata']['ai_tokens'],
                ai_model=result.get("model", "anthropic/claude-3.5-sonnet")
            )
            self.db.add(idea)
            self.db.commit()
            self.db.refresh(idea)
            worksheet['_metadata']['idea_id'] = idea.id

        return worksheet

    def _build_worksheet_prompt(
        self,
        name: str,
        existing_data: Dict[str, Any],
        worksheet_type: str,
        other_characters: List[Entity]
    ) -> tuple[str, str]:
        """Build character worksheet prompt"""

        worksheet_structures = {
            "full": """Create a comprehensive character worksheet covering:
1. Core Identity (name meaning, age, appearance, first impression)
2. Psychology (fears, desires, beliefs, contradictions, coping mechanisms)
3. Backstory (formative events, relationships, wounds, defining moments)
4. Voice (speech patterns, vocabulary, verbal tics, internal monologue style)
5. Relationships (with each other character)
6. Arc Potential (starting point, catalyst, transformation, endpoint)""",

            "backstory": """Create a detailed backstory worksheet covering:
1. Birth & Early Childhood (circumstances, family, formative experiences)
2. Key Relationships (parents, siblings, mentors, first love, enemies)
3. Defining Moments (traumas, triumphs, turning points)
4. Skills & Education (how they learned what they know)
5. Wounds (emotional scars, unresolved issues)
6. Secrets (what they hide, why they hide it)""",

            "psychology": """Create a deep psychological profile covering:
1. Core Beliefs (about self, others, the world)
2. Defense Mechanisms (how they protect themselves emotionally)
3. Attachment Style (how they connect with others)
4. Cognitive Patterns (how they think, biases, blind spots)
5. Emotional Range (what they feel easily, what they suppress)
6. Shadow Self (the parts they deny or reject)
7. Greatest Fear & Deepest Desire (the engine of motivation)""",

            "voice": """Create a voice and dialogue worksheet covering:
1. Speech Patterns (sentence structure, rhythm, formality level)
2. Vocabulary (education level, region, profession, era)
3. Verbal Tics (repeated phrases, filler words, unique expressions)
4. Internal Monologue (how they think vs how they speak)
5. Subtext Tendencies (what they say vs what they mean)
6. Conversation Style (listener vs talker, direct vs indirect)
7. Sample Dialogue (key emotional situations)""",

            "relationships": """Create a relationship dynamics worksheet covering:
For each other character, define:
1. History (how they met, key shared experiences)
2. Current Status (allies, enemies, complicated)
3. Power Dynamic (who has power, how it shifts)
4. Communication Style (how they talk to each other)
5. Conflict Points (sources of tension)
6. Mutual Needs (what they provide each other)
7. Potential Arc (how the relationship could evolve)"""
        }

        system_prompt = f"""You are a JSON-generating character development specialist.

{worksheet_structures.get(worksheet_type, worksheet_structures['full'])}

Create deep, specific, story-useful content. Avoid generic responses.

CRITICAL: Return a valid JSON object. No other text allowed."""

        existing_context = ""
        if existing_data:
            relevant_keys = ['want', 'need', 'flaw', 'strength', 'arc', 'role', 'hook', 'relationships', 'story_potential', 'description']
            existing_info = {k: v for k, v in existing_data.items() if k in relevant_keys and v}
            if existing_info:
                existing_context = f"\n\nExisting Character Data:\n{json.dumps(existing_info, indent=2)}"

        other_char_context = ""
        if other_characters:
            char_list = [f"- {c.name}: {c.attributes.get('role', 'Character')}" for c in other_characters]
            other_char_context = f"\n\nOther Characters in Story:\n" + "\n".join(char_list)

        user_prompt = f"""Character Name: {name}{existing_context}{other_char_context}

Generate a detailed {worksheet_type} worksheet as a JSON object with clearly labeled sections.
Each section should have rich, specific content that could be directly used in writing.

Make it specific to THIS character - avoid generic advice that could apply to anyone."""

        return system_prompt, user_prompt

    def _format_worksheet_description(self, worksheet: Dict[str, Any], worksheet_type: str) -> str:
        """Format worksheet into readable description"""
        sections = []
        for key, value in worksheet.items():
            if key.startswith('_'):
                continue
            section_title = key.replace('_', ' ').title()
            if isinstance(value, dict):
                items = [f"  • {k}: {v}" for k, v in value.items()]
                sections.append(f"**{section_title}**:\n" + "\n".join(items))
            elif isinstance(value, list):
                items = [f"  • {item}" for item in value]
                sections.append(f"**{section_title}**:\n" + "\n".join(items))
            else:
                sections.append(f"**{section_title}**: {value}")

        return "\n\n".join(sections)

    # ===== AI Entity Expansion =====

    async def expand_entity(
        self,
        entity: Entity,
        api_key: str,
        expansion_type: str,
        other_entities: List[Entity]
    ) -> Dict[str, Any]:
        """Expand an existing entity with AI-generated content"""
        logger.info(f"Expanding entity {entity.id} with type: {expansion_type}")

        system_prompt, user_prompt = self._build_expansion_prompt(
            entity=entity,
            expansion_type=expansion_type,
            other_entities=other_entities
        )

        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="expansion",
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Expansion failed: {result.get('error')}")

        ai_response = result["suggestion"]
        expansion = json.loads(ai_response)

        # Merge expansion into entity attributes
        usage = result.get("usage", {})
        expansion['_expansion_metadata'] = {
            'type': expansion_type,
            'ai_cost': OpenRouterService.calculate_cost(usage),
            'ai_tokens': usage.get("total_tokens", 0)
        }

        # Update entity with expanded attributes
        if 'expanded_attributes' in expansion:
            for key, value in expansion['expanded_attributes'].items():
                entity.attributes[key] = value
            self.db.commit()
            self.db.refresh(entity)

        return expansion

    def _build_expansion_prompt(
        self,
        entity: Entity,
        expansion_type: str,
        other_entities: List[Entity]
    ) -> tuple[str, str]:
        """Build entity expansion prompt"""

        expansion_instructions = {
            "deepen": "Add much more depth, nuance, and specific detail to all aspects",
            "relationships": "Develop detailed relationships with other entities",
            "history": "Create rich backstory and history",
            "secrets": "Develop hidden aspects, mysteries, and unrevealed truths",
            "conflicts": "Identify potential conflicts this entity could drive or be involved in"
        }

        entity_type = entity.type.lower()
        system_prompt = f"""You are a JSON-generating {entity_type} development specialist.

Your task: {expansion_instructions.get(expansion_type, 'Expand with more detail')}

Create content that deepens the existing entity without contradicting established facts.

CRITICAL: Return a valid JSON object. No other text allowed."""

        existing_data = json.dumps(entity.attributes, indent=2)

        other_context = ""
        if other_entities and expansion_type in ['relationships', 'conflicts']:
            entity_list = [f"- {e.name} ({e.type}): {e.attributes.get('hook', e.attributes.get('role', 'Unknown'))}" for e in other_entities[:10]]
            other_context = f"\n\nOther Entities:\n" + "\n".join(entity_list)

        user_prompt = f"""Entity: {entity.name} ({entity.type})

Current Data:
{existing_data}
{other_context}

Expand this entity focusing on: {expansion_type}

Return as JSON with:
{{
  "expanded_attributes": {{ ... new/updated attributes ... }},
  "suggestions": [ ... ideas for further development ... ],
  "story_hooks": [ ... specific ways to use this in the narrative ... ]
}}"""

        return system_prompt, user_prompt

    async def generate_related_entities(
        self,
        source_entity: Entity,
        api_key: str,
        relationship_type: str,
        existing_entities: List[Entity]
    ) -> List[Dict[str, Any]]:
        """Generate new entities related to an existing one"""
        logger.info(f"Generating related entities for {source_entity.id}")

        system_prompt, user_prompt = self._build_related_entities_prompt(
            source_entity=source_entity,
            relationship_type=relationship_type,
            existing_entities=existing_entities
        )

        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="related_entities",
            max_tokens=2500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        if not result.get("success"):
            raise Exception(f"Related entity generation failed: {result.get('error')}")

        ai_response = result["suggestion"]
        parsed = json.loads(ai_response)

        usage = result.get("usage", {})
        total_cost = OpenRouterService.calculate_cost(usage)

        related = parsed.get('related_entities', [])
        for entity in related:
            entity['_metadata'] = {
                'source_entity_id': source_entity.id,
                'relationship_type': relationship_type,
                'ai_cost': total_cost / len(related) if related else 0
            }

        return related

    def _build_related_entities_prompt(
        self,
        source_entity: Entity,
        relationship_type: str,
        existing_entities: List[Entity]
    ) -> tuple[str, str]:
        """Build prompt for generating related entities"""

        source_type = source_entity.type
        relationship_instructions = {
            "deepen": "Create entities that add depth to the source (mentors, rivals, loved ones)",
            "relationships": "Create characters with significant relationships to the source",
            "history": "Create entities from the source's past",
            "secrets": "Create entities connected to the source's hidden aspects",
            "conflicts": "Create entities that could drive conflict with the source"
        }

        system_prompt = f"""You are a JSON-generating entity creation assistant.

Your task: {relationship_instructions.get(relationship_type, 'Create related entities')}

Create entities that complement and enrich the source entity.

CRITICAL: Return a valid JSON object with "related_entities" array. No other text allowed."""

        source_data = json.dumps(source_entity.attributes, indent=2)

        existing_names = [e.name for e in existing_entities]
        existing_context = f"\n\nExisting entities (avoid duplicates): {', '.join(existing_names)}" if existing_names else ""

        if source_type == 'CHARACTER':
            entity_template = """{
  "type": "CHARACTER" | "LOCATION",
  "name": "Entity name",
  "role": "Role in story",
  "relationship_to_source": "How they relate to the source character",
  "hook": "Compelling one-liner",
  ... other relevant attributes ...
}"""
        else:
            entity_template = """{
  "type": "CHARACTER" | "LOCATION" | "LORE",
  "name": "Entity name",
  "relationship_to_source": "How they relate to the source",
  "hook": "Compelling one-liner",
  ... other relevant attributes ...
}"""

        user_prompt = f"""Source Entity: {source_entity.name} ({source_type})

Source Data:
{source_data}
{existing_context}

Generate 3-5 related entities. Each should be:
{entity_template}

Return as:
{{
  "related_entities": [...]
}}"""

        return system_prompt, user_prompt
