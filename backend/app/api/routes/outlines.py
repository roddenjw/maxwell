"""
Outline CRUD API Routes
Handles story structure outlines and plot beats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.database import get_db
from app.models.outline import Outline, PlotBeat
from app.services.story_structures import (
    get_available_structures,
    get_structure_template,
    create_plot_beats_from_template
)


router = APIRouter(prefix="/api/outlines", tags=["outlines"])


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
    structure_type: str  # 'km-weiland', 'save-the-cat', 'heros-journey', '3-act', 'custom'
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

@router.post("", response_model=OutlineResponse)
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

    return new_outline


@router.get("/{outline_id}", response_model=OutlineResponse)
async def get_outline(
    outline_id: str,
    db: Session = Depends(get_db)
):
    """Get outline by ID with all plot beats"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    return outline


@router.get("/manuscript/{manuscript_id}", response_model=List[OutlineListResponse])
async def get_manuscript_outlines(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get all outlines for a manuscript"""
    outlines = db.query(Outline).filter(
        Outline.manuscript_id == manuscript_id
    ).order_by(Outline.created_at.desc()).all()

    return outlines


@router.get("/manuscript/{manuscript_id}/active", response_model=OutlineResponse)
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

    return outline


@router.put("/{outline_id}", response_model=OutlineResponse)
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

    return outline


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

@router.post("/{outline_id}/beats", response_model=PlotBeatResponse)
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

    return new_beat


@router.put("/beats/{beat_id}", response_model=PlotBeatResponse)
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

    return beat


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
        "outline_id": outline_id,
        "total_beats": total_beats,
        "completed_beats": completed_beats,
        "completion_percentage": (completed_beats / total_beats * 100) if total_beats > 0 else 0,
        "target_word_count": outline.target_word_count,
        "actual_word_count": sum(beat.actual_word_count for beat in beats),
    }


# Story Structure Template Endpoints

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


@router.post("/from-template", response_model=OutlineResponse)
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

    return new_outline
