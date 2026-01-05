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
            num_ideas=num_ideas
        )

        # Call OpenRouter
        openrouter = OpenRouterService(api_key)
        result = await openrouter.get_writing_suggestion(
            text=user_prompt,
            context=system_prompt,
            suggestion_type="character",
            max_tokens=2000  # Allow for detailed character responses
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
        num_ideas: int
    ) -> tuple[str, str]:
        """Build character brainstorming prompt using Brandon Sanderson's methodology"""

        system_prompt = f"""You are an expert fiction writing coach specializing in character development.

Your approach follows Brandon Sanderson's character creation methodology:
- WANT: What does the character want on the surface?
- NEED: What do they actually need (often unknown to them)?
- FLAW: What personal weakness holds them back?
- STRENGTH: What unique ability or trait defines them?
- ARC: How will they change from beginning to end?

Genre context: {genre}

Focus on creating characters that:
1. Have clear, compelling motivations
2. Possess both strengths and meaningful flaws
3. Generate natural conflict and story potential
4. Feel authentic and three-dimensional
5. Complement but don't duplicate existing characters

Provide {num_ideas} distinct character concepts in JSON format."""

        existing_context = ""
        if existing_characters:
            existing_context = f"\n\nExisting Characters: {', '.join(existing_characters)}"

        user_prompt = f"""Story Premise: {story_premise}{existing_context}

Please create {num_ideas} unique character concepts. For each character, provide a JSON object with these exact fields:

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

Return a JSON array of {num_ideas} character objects. Use this exact format:
[
  {{ character object 1 }},
  {{ character object 2 }},
  ...
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        return system_prompt, user_prompt

    def _parse_character_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response into character data"""
        try:
            # Try direct JSON parse
            characters = json.loads(ai_response)
            if isinstance(characters, list):
                return characters
            elif isinstance(characters, dict):
                return [characters]
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        if "```json" in ai_response:
            try:
                json_str = ai_response.split("```json")[1].split("```")[0].strip()
                characters = json.loads(json_str)
                if isinstance(characters, list):
                    return characters
                elif isinstance(characters, dict):
                    return [characters]
            except (IndexError, json.JSONDecodeError):
                pass

        # Try to extract JSON array using regex as last resort
        import re
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(json_pattern, ai_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error(f"Could not parse character response: {ai_response[:200]}")
        raise ValueError("Could not parse AI response as JSON")

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
