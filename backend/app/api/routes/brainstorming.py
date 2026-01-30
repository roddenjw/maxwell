"""
Brainstorming API Routes
Handles AI-powered idea generation for characters, plots, world-building, and conflicts
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db
from app.models.brainstorm import BrainstormSession, BrainstormIdea
from app.models.entity import Entity
from app.models.outline import PlotBeat, Outline
from app.models.manuscript import Manuscript, Chapter
from app.services.brainstorming_service import BrainstormingService

router = APIRouter(prefix="/api/brainstorming", tags=["brainstorming"])


# ===== Request/Response Models =====

class CreateSessionRequest(BaseModel):
    manuscript_id: str
    outline_id: Optional[str] = None
    session_type: str  # CHARACTER, PLOT_BEAT, WORLD, CONFLICT
    context_data: Dict[str, Any]


class SessionResponse(BaseModel):
    id: str
    manuscript_id: str
    outline_id: Optional[str]
    session_type: str
    context_data: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str


class CharacterGenerationRequest(BaseModel):
    api_key: str
    genre: str
    story_premise: str
    character_ideas: Optional[str] = None  # Optional initial character ideas from writer
    num_ideas: int = 5


class PlotGenerationRequest(BaseModel):
    api_key: str
    genre: str
    premise: str
    num_ideas: int = 5


class LocationGenerationRequest(BaseModel):
    api_key: str
    genre: str
    premise: str
    num_ideas: int = 5


class IdeaResponse(BaseModel):
    id: str
    session_id: str
    idea_type: str
    title: str
    description: str
    idea_metadata: Dict[str, Any]
    is_selected: bool
    user_notes: str
    edited_content: Optional[str]
    integrated_to_outline: bool
    integrated_to_codex: bool
    plot_beat_id: Optional[str]
    entity_id: Optional[str]
    ai_cost: float
    ai_tokens: int
    ai_model: str
    created_at: str
    updated_at: str


class UpdateIdeaRequest(BaseModel):
    is_selected: Optional[bool] = None
    user_notes: Optional[str] = None
    edited_content: Optional[str] = None


class IntegrateCodexRequest(BaseModel):
    entity_type: Optional[str] = None


class RefineIdeaRequest(BaseModel):
    api_key: str
    feedback: str  # User feedback like "make darker", "more comedic", "stronger motivation"
    direction: str = "refine"  # "refine", "expand", "contrast", "combine"
    combine_with_idea_id: Optional[str] = None  # For combining two ideas


class ConflictGenerationRequest(BaseModel):
    api_key: str
    genre: str
    premise: str
    character_ids: Optional[List[str]] = None  # Optional characters to involve
    conflict_type: str = "any"  # "internal", "interpersonal", "external", "societal", "any"
    num_ideas: int = 5


class SceneGenerationRequest(BaseModel):
    api_key: str
    genre: str
    premise: str
    beat_id: Optional[str] = None  # Optional outline beat to base scene on
    character_ids: Optional[List[str]] = None  # Characters in the scene
    location_id: Optional[str] = None  # Optional location setting
    scene_purpose: str = "any"  # "introduction", "conflict", "revelation", "climax", "resolution", "any"
    num_ideas: int = 3


class CharacterWorksheetRequest(BaseModel):
    api_key: str
    character_id: Optional[str] = None  # Existing entity to develop
    character_name: Optional[str] = None  # Or just a name for new character
    worksheet_type: str = "full"  # "full", "backstory", "psychology", "voice", "relationships"


class ExpandEntityRequest(BaseModel):
    api_key: str
    expansion_type: str = "deepen"  # "deepen", "relationships", "history", "secrets", "conflicts"


# ===== Session Management Endpoints =====

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new brainstorming session"""
    try:
        service = BrainstormingService(db)
        session = service.create_session(
            manuscript_id=request.manuscript_id,
            outline_id=request.outline_id,
            session_type=request.session_type,
            context_data=request.context_data
        )

        return SessionResponse(
            id=session.id,
            manuscript_id=session.manuscript_id,
            outline_id=session.outline_id,
            session_type=session.session_type,
            context_data=session.context_data,
            status=session.status,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session details"""
    try:
        service = BrainstormingService(db)
        session = service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            id=session.id,
            manuscript_id=session.manuscript_id,
            outline_id=session.outline_id,
            session_type=session.session_type,
            context_data=session.context_data,
            status=session.status,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manuscripts/{manuscript_id}/context")
async def get_brainstorm_context(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get manuscript context for brainstorming (outline + entities + manuscript metadata)"""
    try:
        # Get manuscript for stored premise/genre
        manuscript = db.query(Manuscript).filter(
            Manuscript.id == manuscript_id
        ).first()

        # Get active outline
        outline = db.query(Outline).filter(
            Outline.manuscript_id == manuscript_id,
            Outline.is_active == True
        ).first()

        # Get existing entities grouped by type
        entities = db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id
        ).all()

        characters = [e for e in entities if e.type == 'CHARACTER']
        locations = [e for e in entities if e.type == 'LOCATION']

        # Premise priority: manuscript.premise > outline.premise (if not auto-extracted)
        premise_value = None
        premise_source = None

        # First check manuscript-level premise
        if manuscript and manuscript.premise:
            premise_value = manuscript.premise
            premise_source = manuscript.premise_source or 'user_written'
        # Fall back to outline premise if no manuscript premise
        elif outline and outline.premise:
            # Skip if it's auto-extracted chapter content
            if not outline.premise.startswith("[Auto-extracted from manuscript]"):
                premise_value = outline.premise
                premise_source = 'outline'

        # Genre priority: manuscript.genre > outline.genre
        genre_value = None
        if manuscript and manuscript.genre:
            genre_value = manuscript.genre
        elif outline and outline.genre:
            genre_value = outline.genre

        return {
            "outline": {
                "genre": genre_value,
                "premise": premise_value,
                "premise_source": premise_source,
                "logline": outline.logline if outline else None,
            },
            "manuscript": {
                "premise": manuscript.premise if manuscript else None,
                "premise_source": manuscript.premise_source if manuscript else None,
                "genre": manuscript.genre if manuscript else None,
            },
            "existing_entities": {
                "characters": [{"id": c.id, "name": c.name} for c in characters],
                "locations": [{"id": l.id, "name": l.name} for l in locations],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manuscripts/{manuscript_id}/sessions", response_model=List[SessionResponse])
async def list_manuscript_sessions(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """List all sessions for a manuscript"""
    try:
        service = BrainstormingService(db)
        sessions = service.get_manuscript_sessions(manuscript_id)

        return [
            SessionResponse(
                id=session.id,
                manuscript_id=session.manuscript_id,
                outline_id=session.outline_id,
                session_type=session.session_type,
                context_data=session.context_data,
                status=session.status,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat()
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Update session status"""
    try:
        service = BrainstormingService(db)
        session = service.update_session_status(session_id, status)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "session_id": session_id, "status": session.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Character Generation Endpoint =====

@router.post("/sessions/{session_id}/generate/characters", response_model=List[IdeaResponse])
async def generate_character_ideas(
    session_id: str,
    request: CharacterGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate character ideas using AI"""
    try:
        service = BrainstormingService(db)

        # Get session to retrieve context
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get existing characters for context
        existing_characters = db.query(Entity).filter(
            Entity.manuscript_id == session.manuscript_id,
            Entity.type == 'CHARACTER'
        ).all()

        # Generate ideas
        ideas = await service.generate_character_ideas(
            session_id=session_id,
            api_key=request.api_key,
            genre=request.genre,
            existing_characters=existing_characters,
            story_premise=request.story_premise,
            character_ideas=request.character_ideas,
            num_ideas=request.num_ideas
        )

        # Return ideas
        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Plot Generation Endpoint =====

@router.post("/sessions/{session_id}/generate/plots", response_model=List[IdeaResponse])
async def generate_plot_ideas(
    session_id: str,
    request: PlotGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate plot ideas using AI (conflicts, twists, subplots)"""
    try:
        service = BrainstormingService(db)

        # Get session to retrieve context
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get existing plot beats for context
        existing_beats = []
        if session.outline_id:
            existing_beats = db.query(PlotBeat).filter(
                PlotBeat.outline_id == session.outline_id
            ).all()

        # Generate ideas
        ideas = await service.generate_plot_ideas(
            session_id=session_id,
            api_key=request.api_key,
            genre=request.genre,
            premise=request.premise,
            existing_beats=existing_beats,
            num_ideas=request.num_ideas
        )

        # Return ideas
        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Location Generation Endpoint =====

@router.post("/sessions/{session_id}/generate/locations", response_model=List[IdeaResponse])
async def generate_location_ideas(
    session_id: str,
    request: LocationGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate location/setting ideas using AI"""
    try:
        service = BrainstormingService(db)

        # Get session to retrieve context
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get existing locations for context
        existing_locations = db.query(Entity).filter(
            Entity.manuscript_id == session.manuscript_id,
            Entity.type == 'LOCATION'
        ).all()

        # Generate ideas
        ideas = await service.generate_location_ideas(
            session_id=session_id,
            api_key=request.api_key,
            genre=request.genre,
            premise=request.premise,
            existing_locations=existing_locations,
            num_ideas=request.num_ideas
        )

        # Return ideas
        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Idea Management Endpoints =====

@router.get("/sessions/{session_id}/ideas", response_model=List[IdeaResponse])
async def list_session_ideas(
    session_id: str,
    db: Session = Depends(get_db)
):
    """List all ideas for a session"""
    try:
        ideas = db.query(BrainstormIdea).filter(
            BrainstormIdea.session_id == session_id
        ).all()

        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ideas/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    request: UpdateIdeaRequest,
    db: Session = Depends(get_db)
):
    """Update idea (selection, notes, edited content)"""
    try:
        service = BrainstormingService(db)
        idea = service.update_idea(idea_id, request.dict(exclude_unset=True))

        return IdeaResponse(
            id=idea.id,
            session_id=idea.session_id,
            idea_type=idea.idea_type,
            title=idea.title,
            description=idea.description,
            idea_metadata=idea.idea_metadata,
            is_selected=idea.is_selected,
            user_notes=idea.user_notes,
            edited_content=idea.edited_content,
            integrated_to_outline=idea.integrated_to_outline,
            integrated_to_codex=idea.integrated_to_codex,
            plot_beat_id=idea.plot_beat_id,
            entity_id=idea.entity_id,
            ai_cost=idea.ai_cost,
            ai_tokens=idea.ai_tokens,
            ai_model=idea.ai_model,
            created_at=idea.created_at.isoformat(),
            updated_at=idea.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ideas/{idea_id}")
async def delete_idea(
    idea_id: str,
    db: Session = Depends(get_db)
):
    """Delete a single idea"""
    try:
        service = BrainstormingService(db)
        success = service.delete_idea(idea_id)

        if not success:
            raise HTTPException(status_code=404, detail="Idea not found")

        return {"success": True, "idea_id": idea_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Integration Endpoints =====

@router.post("/ideas/{idea_id}/integrate/codex")
async def integrate_to_codex(
    idea_id: str,
    request: IntegrateCodexRequest,
    db: Session = Depends(get_db)
):
    """Integrate idea into Codex as entity"""
    try:
        service = BrainstormingService(db)
        entity = await service.integrate_idea_to_codex(
            idea_id=idea_id,
            entity_type=request.entity_type
        )

        return {
            "success": True,
            "idea_id": idea_id,
            "entity": {
                "id": entity.id,
                "type": entity.type,
                "name": entity.name,
                "attributes": entity.attributes,
                "created_at": entity.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Analytics Endpoints =====

@router.get("/sessions/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session statistics (ideas, tokens, cost)"""
    try:
        service = BrainstormingService(db)
        stats = service.get_session_stats(session_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "data": stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Idea Refinement Endpoints =====

@router.post("/ideas/{idea_id}/refine", response_model=IdeaResponse)
async def refine_idea(
    idea_id: str,
    request: RefineIdeaRequest,
    db: Session = Depends(get_db)
):
    """
    Refine an existing idea based on user feedback.
    Updates the idea in-place. Refinement history is preserved in idea_metadata.
    """
    try:
        service = BrainstormingService(db)

        # Get the original idea
        original_idea = db.query(BrainstormIdea).filter(BrainstormIdea.id == idea_id).first()
        if not original_idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        # Get combine target if specified
        combine_idea = None
        if request.combine_with_idea_id:
            combine_idea = db.query(BrainstormIdea).filter(
                BrainstormIdea.id == request.combine_with_idea_id
            ).first()

        # Generate refined idea
        refined_idea = await service.refine_idea(
            original_idea=original_idea,
            api_key=request.api_key,
            feedback=request.feedback,
            direction=request.direction,
            combine_with=combine_idea
        )

        return IdeaResponse(
            id=refined_idea.id,
            session_id=refined_idea.session_id,
            idea_type=refined_idea.idea_type,
            title=refined_idea.title,
            description=refined_idea.description,
            idea_metadata=refined_idea.idea_metadata,
            is_selected=refined_idea.is_selected,
            user_notes=refined_idea.user_notes,
            edited_content=refined_idea.edited_content,
            integrated_to_outline=refined_idea.integrated_to_outline,
            integrated_to_codex=refined_idea.integrated_to_codex,
            plot_beat_id=refined_idea.plot_beat_id,
            entity_id=refined_idea.entity_id,
            ai_cost=refined_idea.ai_cost,
            ai_tokens=refined_idea.ai_tokens,
            ai_model=refined_idea.ai_model,
            created_at=refined_idea.created_at.isoformat(),
            updated_at=refined_idea.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Conflict Generation Endpoints =====

@router.post("/sessions/{session_id}/generate/conflicts", response_model=List[IdeaResponse])
async def generate_conflict_ideas(
    session_id: str,
    request: ConflictGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate conflict scenario ideas using AI"""
    try:
        service = BrainstormingService(db)

        # Get session to retrieve context
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get specified characters if any
        characters = []
        if request.character_ids:
            characters = db.query(Entity).filter(
                Entity.id.in_(request.character_ids),
                Entity.type == 'CHARACTER'
            ).all()
        else:
            # Get all characters for context
            characters = db.query(Entity).filter(
                Entity.manuscript_id == session.manuscript_id,
                Entity.type == 'CHARACTER'
            ).all()

        # Generate conflict ideas
        ideas = await service.generate_conflict_ideas(
            session_id=session_id,
            api_key=request.api_key,
            genre=request.genre,
            premise=request.premise,
            characters=characters,
            conflict_type=request.conflict_type,
            num_ideas=request.num_ideas
        )

        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Scene Generation Endpoints =====

@router.post("/sessions/{session_id}/generate/scenes", response_model=List[IdeaResponse])
async def generate_scene_ideas(
    session_id: str,
    request: SceneGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate scene ideas using AI"""
    try:
        service = BrainstormingService(db)

        # Get session to retrieve context
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get optional entities
        characters = []
        if request.character_ids:
            characters = db.query(Entity).filter(
                Entity.id.in_(request.character_ids),
                Entity.type == 'CHARACTER'
            ).all()

        location = None
        if request.location_id:
            location = db.query(Entity).filter(
                Entity.id == request.location_id,
                Entity.type == 'LOCATION'
            ).first()

        beat = None
        if request.beat_id:
            beat = db.query(PlotBeat).filter(PlotBeat.id == request.beat_id).first()

        # Generate scene ideas
        ideas = await service.generate_scene_ideas(
            session_id=session_id,
            api_key=request.api_key,
            genre=request.genre,
            premise=request.premise,
            characters=characters,
            location=location,
            beat=beat,
            scene_purpose=request.scene_purpose,
            num_ideas=request.num_ideas
        )

        return [
            IdeaResponse(
                id=idea.id,
                session_id=idea.session_id,
                idea_type=idea.idea_type,
                title=idea.title,
                description=idea.description,
                idea_metadata=idea.idea_metadata,
                is_selected=idea.is_selected,
                user_notes=idea.user_notes,
                edited_content=idea.edited_content,
                integrated_to_outline=idea.integrated_to_outline,
                integrated_to_codex=idea.integrated_to_codex,
                plot_beat_id=idea.plot_beat_id,
                entity_id=idea.entity_id,
                ai_cost=idea.ai_cost,
                ai_tokens=idea.ai_tokens,
                ai_model=idea.ai_model,
                created_at=idea.created_at.isoformat(),
                updated_at=idea.updated_at.isoformat()
            )
            for idea in ideas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Character Development Worksheet Endpoints =====

@router.post("/sessions/{session_id}/generate/character-worksheet")
async def generate_character_worksheet(
    session_id: str,
    request: CharacterWorksheetRequest,
    db: Session = Depends(get_db)
):
    """Generate a deep character development worksheet"""
    try:
        service = BrainstormingService(db)

        # Get session
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get character entity if specified
        character = None
        if request.character_id:
            character = db.query(Entity).filter(
                Entity.id == request.character_id,
                Entity.type == 'CHARACTER'
            ).first()
            if not character:
                raise HTTPException(status_code=404, detail="Character not found")

        # Get other characters for relationship context
        other_characters = db.query(Entity).filter(
            Entity.manuscript_id == session.manuscript_id,
            Entity.type == 'CHARACTER'
        ).all()
        if character:
            other_characters = [c for c in other_characters if c.id != character.id]

        # Generate worksheet
        worksheet = await service.generate_character_worksheet(
            session_id=session_id,
            api_key=request.api_key,
            character=character,
            character_name=request.character_name,
            worksheet_type=request.worksheet_type,
            other_characters=other_characters
        )

        return {
            "success": True,
            "worksheet": worksheet
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== AI Entity Expansion Endpoints =====

@router.post("/entities/{entity_id}/expand")
async def expand_entity(
    entity_id: str,
    request: ExpandEntityRequest,
    db: Session = Depends(get_db)
):
    """Expand an existing entity with AI-generated content"""
    try:
        service = BrainstormingService(db)

        # Get the entity
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Get other entities for context
        other_entities = db.query(Entity).filter(
            Entity.manuscript_id == entity.manuscript_id,
            Entity.id != entity_id
        ).all()

        # Expand the entity
        expansion = await service.expand_entity(
            entity=entity,
            api_key=request.api_key,
            expansion_type=request.expansion_type,
            other_entities=other_entities
        )

        return {
            "success": True,
            "entity_id": entity_id,
            "expansion": expansion
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/{entity_id}/generate-related")
async def generate_related_entities(
    entity_id: str,
    request: ExpandEntityRequest,
    db: Session = Depends(get_db)
):
    """Generate new entities that are related to an existing entity"""
    try:
        service = BrainstormingService(db)

        # Get the source entity
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Get existing entities to avoid duplicates
        existing_entities = db.query(Entity).filter(
            Entity.manuscript_id == entity.manuscript_id
        ).all()

        # Generate related entities
        related = await service.generate_related_entities(
            source_entity=entity,
            api_key=request.api_key,
            relationship_type=request.expansion_type,
            existing_entities=existing_entities
        )

        return {
            "success": True,
            "source_entity_id": entity_id,
            "related_entities": related
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Character to Outline Integration =====

class OutlineFromCharactersRequest(BaseModel):
    api_key: str
    manuscript_id: str
    genre: str
    premise: str
    target_word_count: int = 80000


class GeneratePremiseRequest(BaseModel):
    api_key: str
    manuscript_id: str


@router.post("/outline-from-characters")
async def generate_outline_from_characters(
    request: OutlineFromCharactersRequest,
    db: Session = Depends(get_db)
):
    """Generate an outline based on existing character entities"""
    try:
        service = BrainstormingService(db)

        # Get all CHARACTER entities for this manuscript
        characters = db.query(Entity).filter(
            Entity.manuscript_id == request.manuscript_id,
            Entity.type == "CHARACTER"
        ).all()

        if not characters:
            raise HTTPException(
                status_code=400,
                detail="No characters found. Create some characters first to generate an outline from them."
            )

        # Generate outline
        result = await service.generate_outline_from_characters(
            api_key=request.api_key,
            characters=characters,
            genre=request.genre,
            premise=request.premise,
            target_word_count=request.target_word_count
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

        return {
            "success": True,
            "data": result["outline_data"],
            "cost": {
                "total": result.get("cost", 0),
                "formatted": f"${result.get('cost', 0):.4f}"
            },
            "characters_used": len(characters)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Story Premise Generation =====

@router.post("/generate-premise")
async def generate_story_premise(
    request: GeneratePremiseRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a story premise from manuscript content.

    Analyzes the manuscript text to derive a compelling premise/logline
    that can be stored and reused across brainstorming sessions.
    """
    try:
        service = BrainstormingService(db)

        # Get manuscript
        manuscript = db.query(Manuscript).filter(
            Manuscript.id == request.manuscript_id
        ).first()

        if not manuscript:
            raise HTTPException(status_code=404, detail="Manuscript not found")

        # Get manuscript content from chapters
        chapters = db.query(Chapter).filter(
            Chapter.manuscript_id == request.manuscript_id
        ).order_by(Chapter.order_index).all()

        # Combine chapter content for analysis
        manuscript_content = ""
        for chapter in chapters[:10]:  # Limit to first 10 chapters
            if chapter.content:
                manuscript_content += f"\n\n--- {chapter.title} ---\n{chapter.content}"

        if not manuscript_content.strip():
            raise HTTPException(
                status_code=400,
                detail="No manuscript content found. Write some chapters first."
            )

        # Get existing characters for context
        characters = db.query(Entity).filter(
            Entity.manuscript_id == request.manuscript_id,
            Entity.type == "CHARACTER"
        ).all()

        # Get existing genre from outline if available
        outline = db.query(Outline).filter(
            Outline.manuscript_id == request.manuscript_id,
            Outline.is_active == True
        ).first()
        existing_genre = outline.genre if outline else None

        # Generate premise
        result = await service.generate_story_premise(
            api_key=request.api_key,
            manuscript_content=manuscript_content,
            existing_characters=characters,
            existing_genre=existing_genre
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

        return {
            "success": True,
            "premise": result["premise"],
            "genre": result["genre"],
            "themes": result.get("themes", []),
            "tone": result.get("tone", ""),
            "confidence": result.get("confidence", 0.5),
            "cost": {
                "total": result.get("cost", 0),
                "formatted": f"${result.get('cost', 0):.4f}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
