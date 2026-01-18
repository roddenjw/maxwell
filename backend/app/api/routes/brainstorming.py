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
    """Get manuscript context for brainstorming (outline + entities)"""
    try:
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

        # Filter out auto-extracted premises (they're chapter content, not actual premises)
        premise_value = None
        if outline and outline.premise:
            # Skip if it's auto-extracted chapter content
            if not outline.premise.startswith("[Auto-extracted from manuscript]"):
                premise_value = outline.premise

        return {
            "outline": {
                "genre": outline.genre if outline else None,
                "premise": premise_value,
                "logline": outline.logline if outline else None,
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
