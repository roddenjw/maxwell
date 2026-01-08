"""
Outline CRUD API Routes
Handles story structure outlines and plot beats
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outline import Outline, PlotBeat
from app.services.openrouter_service import OpenRouterService
from app.services.story_structures import (
    create_plot_beats_from_template,
    get_available_structures,
    get_structure_template,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/outlines", tags=["outlines"])


def serialize_plot_beat(beat: PlotBeat) -> dict:
    """Serialize a PlotBeat SQLAlchemy object to dict"""
    return {
        "id": beat.id,
        "outline_id": beat.outline_id,
        "beat_name": beat.beat_name,
        "beat_label": beat.beat_label,
        "beat_description": beat.beat_description or "",
        "target_position_percent": beat.target_position_percent,
        "target_word_count": beat.target_word_count,
        "actual_word_count": beat.actual_word_count,
        "order_index": beat.order_index,
        "user_notes": beat.user_notes or "",
        "content_summary": beat.content_summary or "",
        "chapter_id": beat.chapter_id,
        "is_completed": beat.is_completed,
        "created_at": beat.created_at.isoformat() if beat.created_at else None,
        "updated_at": beat.updated_at.isoformat() if beat.updated_at else None,
        "completed_at": beat.completed_at.isoformat() if beat.completed_at else None,
    }


def serialize_outline(outline: Outline) -> dict:
    """Serialize an Outline SQLAlchemy object to dict with plot_beats"""
    return {
        "id": outline.id,
        "manuscript_id": outline.manuscript_id,
        "structure_type": outline.structure_type,
        "genre": outline.genre,
        "target_word_count": outline.target_word_count,
        "premise": outline.premise or "",
        "logline": outline.logline or "",
        "synopsis": outline.synopsis or "",
        "notes": outline.notes or "",
        "is_active": outline.is_active,
        "settings": outline.settings or {},
        "created_at": outline.created_at.isoformat() if outline.created_at else None,
        "updated_at": outline.updated_at.isoformat() if outline.updated_at else None,
        "plot_beats": [serialize_plot_beat(beat) for beat in outline.plot_beats],
    }


# Pydantic schemas for request/response
class PlotBeatCreate(BaseModel):
    beat_name: str
    beat_label: str
    beat_description: Optional[str] = ""
    target_position_percent: float
    order_index: int
    user_notes: Optional[str] = ""


class PlotBeatUpdate(BaseModel):
    beat_label: Optional[str] = None
    beat_description: Optional[str] = None
    user_notes: Optional[str] = None
    content_summary: Optional[str] = None
    chapter_id: Optional[str] = None
    is_completed: Optional[bool] = None


class PlotBeatResponse(BaseModel):
    id: str
    outline_id: str
    beat_name: str
    beat_label: str
    beat_description: str
    target_position_percent: float
    target_word_count: int
    actual_word_count: int
    order_index: int
    user_notes: str
    content_summary: str
    chapter_id: Optional[str]
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class OutlineCreate(BaseModel):
    manuscript_id: str
    structure_type: str  # 'story-arc-9', 'screenplay-15', 'mythic-quest', '3-act', 'custom'
    genre: Optional[str] = None
    target_word_count: Optional[int] = 80000
    premise: Optional[str] = ""
    logline: Optional[str] = ""
    synopsis: Optional[str] = ""


class OutlineUpdate(BaseModel):
    structure_type: Optional[str] = None
    genre: Optional[str] = None
    target_word_count: Optional[int] = None
    premise: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class OutlineResponse(BaseModel):
    id: str
    manuscript_id: str
    structure_type: str
    genre: Optional[str]
    target_word_count: int
    premise: str
    logline: str
    synopsis: str
    notes: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    plot_beats: List[PlotBeatResponse] = []

    class Config:
        from_attributes = True


class OutlineListResponse(BaseModel):
    id: str
    manuscript_id: str
    structure_type: str
    genre: Optional[str]
    target_word_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# CRUD Endpoints

@router.post("")
async def create_outline(
    outline: OutlineCreate,
    db: Session = Depends(get_db)
):
    """Create a new story outline"""
    # Check if manuscript exists
    from app.models.manuscript import Manuscript
    manuscript = db.query(Manuscript).filter(Manuscript.id == outline.manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Deactivate other outlines for this manuscript
    db.query(Outline).filter(
        Outline.manuscript_id == outline.manuscript_id,
        Outline.is_active == True
    ).update({"is_active": False})

    # Create new outline
    new_outline = Outline(
        id=str(uuid.uuid4()),
        **outline.model_dump()
    )
    new_outline.is_active = True  # New outline is always active

    db.add(new_outline)
    db.commit()
    db.refresh(new_outline)

    # Trigger lazy load of plot_beats relationship (will be empty for new outline)
    _ = new_outline.plot_beats

    return {"success": True, "data": serialize_outline(new_outline)}


# Story Structure Template Endpoints (MUST be before /{outline_id} to avoid route conflicts)

@router.get("/structures")
async def list_story_structures():
    """Get list of available story structure templates"""
    return {
        "success": True,
        "structures": get_available_structures()
    }


@router.get("/structures/{structure_type}")
async def get_story_structure(structure_type: str):
    """Get detailed information about a specific story structure"""
    try:
        template = get_structure_template(structure_type)
        return {
            "success": True,
            "structure": {
                "id": structure_type,
                "name": template["name"],
                "description": template["description"],
                "recommended_for": template["recommended_for"],
                "word_count_range": template["word_count_range"],
                "beats": [beat.to_dict() for beat in template["beats"]]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class GeneratePremiseRequest(BaseModel):
    brainstorm_text: str
    api_key: str
    genre: Optional[str] = None


@router.post("/generate-premise")
async def generate_premise(request: GeneratePremiseRequest):
    """
    Generate a concise premise from freeform brainstorming text using AI

    Args:
        request: Contains the brainstorm text and OpenRouter API key

    Returns:
        Generated premise and logline
    """
    if not request.brainstorm_text or len(request.brainstorm_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Brainstorm text too short. Please write at least 20 characters.")

    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key required for AI generation")

    try:
        openrouter = OpenRouterService(request.api_key)

        # Build prompt for premise generation
        genre_context = f" in the {request.genre} genre" if request.genre else ""
        system_prompt = """You are an expert story consultant helping authors refine their story concepts.
Your task is to distill freeform brainstorming into clear, compelling story elements."""

        user_prompt = f"""Based on this author's brainstorming about their story{genre_context}, create:

1. A PREMISE (2-3 sentences): A clear, engaging summary of the core story concept, including the protagonist's goal, the central conflict, and what's at stake.

2. A LOGLINE (1 sentence): A punchy, one-sentence hook that captures the essence of the story.

Author's brainstorming:
{request.brainstorm_text}

Respond in exactly this format:
PREMISE: [your 2-3 sentence premise]

LOGLINE: [your 1 sentence logline]"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{openrouter.BASE_URL}/chat/completions",
                headers=openrouter.headers,
                json={
                    "model": openrouter.DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"AI service error: {response.status_code}")

            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]

            # Parse the response
            premise = ""
            logline = ""

            lines = ai_response.strip().split('\n')
            for i, line in enumerate(lines):
                if line.startswith("PREMISE:"):
                    premise = line.replace("PREMISE:", "").strip()
                    # Check if premise continues on next lines
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("LOGLINE:"):
                        if lines[j].strip():
                            premise += " " + lines[j].strip()
                        j += 1
                elif line.startswith("LOGLINE:"):
                    logline = line.replace("LOGLINE:", "").strip()

            return {
                "success": True,
                "premise": premise,
                "logline": logline,
                "usage": data.get("usage", {})
            }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout. Please try again.")
    except Exception as e:
        logger.error(f"Premise generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SwitchStructureRequest(BaseModel):
    current_outline_id: str
    new_structure_type: str
    beat_mappings: Optional[Dict[str, str]] = None  # old_beat_id -> new_beat_name


@router.post("/switch-structure")
async def switch_story_structure(
    request: SwitchStructureRequest,
    db: Session = Depends(get_db)
):
    """
    Switch an existing outline to a different story structure
    Intelligently migrates user notes, completion status, and chapter links

    Args:
        request: Contains current outline ID, new structure type, and optional beat mappings

    Returns:
        Suggested beat mappings if beat_mappings not provided, or new outline if complete
    """
    # Get current outline
    current_outline = db.query(Outline).filter(Outline.id == request.current_outline_id).first()
    if not current_outline:
        raise HTTPException(status_code=404, detail="Current outline not found")

    # Validate new structure type
    try:
        new_template = get_structure_template(request.new_structure_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If no mappings provided, return suggested mappings for user review
    if not request.beat_mappings:
        old_beats = current_outline.plot_beats
        new_beat_templates = new_template["beats"]

        # Create mapping suggestions based on beat names and positions
        suggested_mappings = []
        for old_beat in old_beats:
            best_match = None
            best_score = 0

            for new_beat in new_beat_templates:
                score = 0

                # Exact beat name match (highest priority)
                if old_beat.beat_name == new_beat.beat_name:
                    score += 100
                # Similar beat names (e.g., both contain "midpoint")
                elif new_beat.beat_name in old_beat.beat_name or old_beat.beat_name in new_beat.beat_name:
                    score += 50

                # Similar position in story (closer = better)
                position_diff = abs(old_beat.target_position_percent - new_beat.position_percent)
                score += (1.0 - position_diff) * 30

                if score > best_score:
                    best_score = score
                    best_match = new_beat.beat_name

            suggested_mappings.append({
                "old_beat_id": old_beat.id,
                "old_beat_name": old_beat.beat_name,
                "old_beat_label": old_beat.beat_label,
                "old_position": old_beat.target_position_percent,
                "suggested_new_beat": best_match,
                "has_notes": bool(old_beat.user_notes),
                "has_chapter": bool(old_beat.chapter_id),
                "is_completed": old_beat.is_completed,
                "confidence": min(100, int(best_score))
            })

        return {
            "success": True,
            "requires_mapping": True,
            "old_structure": current_outline.structure_type,
            "new_structure": request.new_structure_type,
            "new_beats": [
                {
                    "beat_name": beat.beat_name,
                    "beat_label": beat.beat_label,
                    "position": beat.position_percent
                }
                for beat in new_beat_templates
            ],
            "suggested_mappings": suggested_mappings
        }

    # User provided mappings - create new outline with migration
    # Deactivate current outline
    current_outline.is_active = False

    # Create new outline with same premise/genre/target
    new_outline = Outline(
        id=str(uuid.uuid4()),
        manuscript_id=current_outline.manuscript_id,
        structure_type=request.new_structure_type,
        genre=current_outline.genre,
        target_word_count=current_outline.target_word_count,
        premise=current_outline.premise,
        logline=current_outline.logline,
        synopsis=current_outline.synopsis,
        is_active=True
    )

    db.add(new_outline)
    db.flush()  # Get the outline ID

    # Create new plot beats from template
    old_beats_map = {beat.id: beat for beat in current_outline.plot_beats}
    beat_templates = create_plot_beats_from_template(request.new_structure_type, current_outline.target_word_count)

    for beat_data in beat_templates:
        new_beat = PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=new_outline.id,
            **beat_data
        )

        # Find if this beat was mapped from an old beat
        old_beat_id = None
        for old_id, new_beat_name in request.beat_mappings.items():
            if new_beat_name == beat_data["beat_name"]:
                old_beat_id = old_id
                break

        # If mapped, copy data from old beat
        if old_beat_id and old_beat_id in old_beats_map:
            old_beat = old_beats_map[old_beat_id]
            new_beat.user_notes = old_beat.user_notes
            new_beat.is_completed = old_beat.is_completed
            new_beat.chapter_id = old_beat.chapter_id
            new_beat.completed_at = old_beat.completed_at
            new_beat.content_summary = old_beat.content_summary

        db.add(new_beat)

    db.commit()
    db.refresh(new_outline)

    # Trigger lazy load of plot_beats relationship
    _ = new_outline.plot_beats

    return {
        "success": True,
        "data": serialize_outline(new_outline)
    }


@router.post("/from-template")
async def create_outline_from_template(
    manuscript_id: str,
    structure_type: str,
    genre: Optional[str] = None,
    target_word_count: int = 80000,
    db: Session = Depends(get_db)
):
    """
    Create a new outline from a story structure template
    Automatically generates plot beats based on the chosen structure
    """
    # Check if manuscript exists
    from app.models.manuscript import Manuscript
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Validate structure type
    try:
        template = get_structure_template(structure_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Deactivate other outlines for this manuscript
    db.query(Outline).filter(
        Outline.manuscript_id == manuscript_id,
        Outline.is_active == True
    ).update({"is_active": False})

    # Create new outline
    new_outline = Outline(
        id=str(uuid.uuid4()),
        manuscript_id=manuscript_id,
        structure_type=structure_type,
        genre=genre,
        target_word_count=target_word_count,
        is_active=True
    )

    db.add(new_outline)
    db.flush()  # Get the outline ID

    # Create plot beats from template
    beat_templates = create_plot_beats_from_template(structure_type, target_word_count)

    for beat_data in beat_templates:
        new_beat = PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=new_outline.id,
            **beat_data
        )
        db.add(new_beat)

    db.commit()
    db.refresh(new_outline)

    # Trigger lazy load of plot_beats relationship
    _ = new_outline.plot_beats

    return {"success": True, "data": serialize_outline(new_outline)}


# Regular CRUD Endpoints (generic routes like /{outline_id} go after specific routes)

@router.get("/{outline_id}")
async def get_outline(
    outline_id: str,
    db: Session = Depends(get_db)
):
    """Get outline by ID with all plot beats"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    # Trigger lazy load of plot_beats relationship
    _ = outline.plot_beats

    return {"success": True, "data": serialize_outline(outline)}


@router.get("/manuscript/{manuscript_id}")
async def get_manuscript_outlines(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get all outlines for a manuscript"""
    outlines = db.query(Outline).filter(
        Outline.manuscript_id == manuscript_id
    ).order_by(Outline.created_at.desc()).all()

    return {"success": True, "data": outlines}


@router.get("/manuscript/{manuscript_id}/active")
async def get_active_outline(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get the active outline for a manuscript"""
    outline = db.query(Outline).filter(
        Outline.manuscript_id == manuscript_id,
        Outline.is_active == True
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="No active outline found for manuscript")

    # Trigger lazy load of plot_beats relationship
    _ = outline.plot_beats

    return {"success": True, "data": serialize_outline(outline)}


@router.put("/{outline_id}")
async def update_outline(
    outline_id: str,
    outline_update: OutlineUpdate,
    db: Session = Depends(get_db)
):
    """Update an outline"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    # Update fields
    update_data = outline_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(outline, key, value)

    outline.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(outline)

    # Trigger lazy load of plot_beats relationship
    _ = outline.plot_beats

    return {"success": True, "data": serialize_outline(outline)}


@router.delete("/{outline_id}")
async def delete_outline(
    outline_id: str,
    db: Session = Depends(get_db)
):
    """Delete an outline and all its plot beats"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    db.delete(outline)
    db.commit()

    return {"success": True, "message": "Outline deleted"}


# Plot Beat Endpoints

@router.post("/{outline_id}/beats")
async def create_plot_beat(
    outline_id: str,
    beat: PlotBeatCreate,
    db: Session = Depends(get_db)
):
    """Create a new plot beat for an outline"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    # Calculate target word count
    target_word_count = int(outline.target_word_count * beat.target_position_percent)

    new_beat = PlotBeat(
        id=str(uuid.uuid4()),
        outline_id=outline_id,
        **beat.model_dump(),
        target_word_count=target_word_count
    )

    db.add(new_beat)
    db.commit()
    db.refresh(new_beat)

    return {"success": True, "data": serialize_plot_beat(new_beat)}


@router.put("/beats/{beat_id}")
async def update_plot_beat(
    beat_id: str,
    beat_update: PlotBeatUpdate,
    db: Session = Depends(get_db)
):
    """Update a plot beat"""
    beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
    if not beat:
        raise HTTPException(status_code=404, detail="Plot beat not found")

    # Update fields
    update_data = beat_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(beat, key, value)

    # If marking as completed, set timestamp
    if update_data.get('is_completed') and not beat.completed_at:
        beat.completed_at = datetime.utcnow()

    beat.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(beat)

    return {"success": True, "data": serialize_plot_beat(beat)}


@router.delete("/beats/{beat_id}")
async def delete_plot_beat(
    beat_id: str,
    db: Session = Depends(get_db)
):
    """Delete a plot beat"""
    beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
    if not beat:
        raise HTTPException(status_code=404, detail="Plot beat not found")

    db.delete(beat)
    db.commit()

    return {"success": True, "message": "Plot beat deleted"}


@router.get("/{outline_id}/progress")
async def get_outline_progress(
    outline_id: str,
    db: Session = Depends(get_db)
):
    """Get outline completion progress"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    beats = db.query(PlotBeat).filter(PlotBeat.outline_id == outline_id).all()
    total_beats = len(beats)
    completed_beats = sum(1 for beat in beats if beat.is_completed)

    return {
        "success": True,
        "data": {
            "outline_id": outline_id,
            "total_beats": total_beats,
            "completed_beats": completed_beats,
            "completion_percentage": (completed_beats / total_beats * 100) if total_beats > 0 else 0,
            "target_word_count": outline.target_word_count,
            "actual_word_count": sum(beat.actual_word_count for beat in beats),
        }
    }
