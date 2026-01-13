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
