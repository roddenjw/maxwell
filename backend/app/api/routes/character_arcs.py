"""
Character Arc API Routes - Managing character arcs integrated with Wiki and Outline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.character_arc_service import CharacterArcService
from app.models.character_arc import ArcTemplate


router = APIRouter(prefix="/character-arcs", tags=["character-arcs"])


# ==================== Pydantic Models ====================

class ArcCreate(BaseModel):
    wiki_entry_id: str
    manuscript_id: str
    arc_template: str = ArcTemplate.CUSTOM.value
    arc_name: Optional[str] = None
    planned_arc: Optional[Dict[str, Any]] = None
    custom_stages: Optional[List[Dict]] = None


class ArcUpdate(BaseModel):
    arc_template: Optional[str] = None
    arc_name: Optional[str] = None
    planned_arc: Optional[Dict[str, Any]] = None
    custom_stages: Optional[List[Dict]] = None
    arc_deviation_notes: Optional[str] = None


class ArcResponse(BaseModel):
    id: str
    wiki_entry_id: str
    manuscript_id: str
    arc_template: str
    arc_name: Optional[str] = None
    planned_arc: Dict = {}
    detected_arc: Dict = {}
    arc_beats: List[Dict] = []
    custom_stages: List[Dict] = []
    arc_completion: float
    arc_health: str
    arc_deviation_notes: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None
    analysis_confidence: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BeatLinkRequest(BaseModel):
    beat_id: str
    arc_stage: str
    chapter_id: Optional[str] = None
    description: Optional[str] = None
    is_planned: bool = True


class AnalyzeRequest(BaseModel):
    manuscript_text: str
    character_name: str


# ==================== Arc CRUD Endpoints ====================

@router.post("", response_model=ArcResponse)
def create_arc(
    data: ArcCreate,
    db: Session = Depends(get_db)
):
    """Create a new character arc"""
    service = CharacterArcService(db)

    arc = service.create_arc(
        wiki_entry_id=data.wiki_entry_id,
        manuscript_id=data.manuscript_id,
        arc_template=data.arc_template,
        arc_name=data.arc_name,
        planned_arc=data.planned_arc,
        custom_stages=data.custom_stages
    )

    return arc


@router.get("/{arc_id}", response_model=ArcResponse)
def get_arc(
    arc_id: str,
    db: Session = Depends(get_db)
):
    """Get an arc by ID"""
    service = CharacterArcService(db)
    arc = service.get_arc(arc_id)

    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")

    return arc


@router.get("/character/{wiki_entry_id}", response_model=List[ArcResponse])
def get_character_arcs(
    wiki_entry_id: str,
    manuscript_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all arcs for a character"""
    service = CharacterArcService(db)
    arcs = service.get_character_arcs(wiki_entry_id, manuscript_id)
    return arcs


@router.get("/manuscript/{manuscript_id}", response_model=List[ArcResponse])
def get_manuscript_arcs(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get all character arcs for a manuscript"""
    service = CharacterArcService(db)
    arcs = service.get_manuscript_arcs(manuscript_id)
    return arcs


@router.put("/{arc_id}", response_model=ArcResponse)
def update_arc(
    arc_id: str,
    updates: ArcUpdate,
    db: Session = Depends(get_db)
):
    """Update a character arc"""
    service = CharacterArcService(db)

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    arc = service.update_arc(arc_id, update_dict)

    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")

    return arc


@router.delete("/{arc_id}")
def delete_arc(
    arc_id: str,
    db: Session = Depends(get_db)
):
    """Delete a character arc"""
    service = CharacterArcService(db)

    if not service.delete_arc(arc_id):
        raise HTTPException(status_code=404, detail="Arc not found")

    return {"status": "deleted", "id": arc_id}


# ==================== Template Endpoints ====================

@router.get("/templates/all")
def get_arc_templates(
    db: Session = Depends(get_db)
):
    """Get all available arc templates"""
    service = CharacterArcService(db)
    return service.get_arc_templates()


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific template definition"""
    service = CharacterArcService(db)
    template = service.get_template_definition(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


# ==================== Beat Mapping Endpoints ====================

@router.get("/{arc_id}/map-to-outline/{outline_id}")
def map_arc_to_outline(
    arc_id: str,
    outline_id: str,
    structure_type: str = Query("three_act"),
    db: Session = Depends(get_db)
):
    """Get suggested mapping of arc stages to outline beats"""
    service = CharacterArcService(db)
    mappings = service.map_arc_to_outline(arc_id, outline_id, structure_type)
    return {"mappings": mappings}


@router.post("/{arc_id}/link-beat", response_model=ArcResponse)
def link_beat_to_arc(
    arc_id: str,
    data: BeatLinkRequest,
    db: Session = Depends(get_db)
):
    """Link an outline beat to an arc stage"""
    service = CharacterArcService(db)

    arc = service.link_beat_to_arc_stage(
        arc_id=arc_id,
        beat_id=data.beat_id,
        arc_stage=data.arc_stage,
        chapter_id=data.chapter_id,
        description=data.description,
        is_planned=data.is_planned
    )

    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")

    return arc


@router.delete("/{arc_id}/unlink-beat")
def unlink_beat_from_arc(
    arc_id: str,
    beat_id: str = Query(...),
    arc_stage: str = Query(...),
    db: Session = Depends(get_db)
):
    """Remove a beat link from an arc stage"""
    service = CharacterArcService(db)

    arc = service.unlink_beat_from_arc(arc_id, beat_id, arc_stage)

    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")

    return {"status": "unlinked", "arc_id": arc_id, "beat_id": beat_id}


# ==================== Analysis Endpoints ====================

@router.post("/{arc_id}/analyze")
def analyze_arc(
    arc_id: str,
    data: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Analyze manuscript text to detect arc progression"""
    service = CharacterArcService(db)

    result = service.detect_arc_from_manuscript(
        arc_id=arc_id,
        manuscript_text=data.manuscript_text,
        character_name=data.character_name
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{arc_id}/compare")
def compare_arcs(
    arc_id: str,
    db: Session = Depends(get_db)
):
    """Compare planned arc to detected arc"""
    service = CharacterArcService(db)

    result = service.compare_arcs(arc_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ==================== Outline Integration Endpoints ====================

@router.get("/outline/{outline_id}/character/{wiki_entry_id}")
def get_character_outline_view(
    outline_id: str,
    wiki_entry_id: str,
    manuscript_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get outline view filtered and annotated for a specific character"""
    service = CharacterArcService(db)

    result = service.get_character_outline_view(
        outline_id=outline_id,
        wiki_entry_id=wiki_entry_id,
        manuscript_id=manuscript_id
    )

    return result
