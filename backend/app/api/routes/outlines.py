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
from app.models.outline import (
    Outline, PlotBeat, ITEM_TYPE_BEAT, ITEM_TYPE_SCENE,
    OUTLINE_SCOPE_MANUSCRIPT, OUTLINE_SCOPE_SERIES, OUTLINE_SCOPE_WORLD
)
from app.models.manuscript import Chapter
from app.services.openrouter_service import OpenRouterService
from app.services.ai_outline_service import AIOutlineService
from app.services.story_structures import (
    create_plot_beats_from_template,
    get_available_structures,
    get_structure_template,
)
from app.services.series_structure_templates import (
    get_series_structure,
    get_series_structure_for_db,
    list_series_structures,
)
from app.services.manuscript_aggregation_service import manuscript_aggregation_service

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/outlines", tags=["outlines"])


def serialize_plot_beat(beat: PlotBeat) -> dict:
    """Serialize a PlotBeat SQLAlchemy object to dict"""
    return {
        "id": beat.id,
        "outline_id": beat.outline_id,
        "item_type": beat.item_type or ITEM_TYPE_BEAT,  # BEAT or SCENE
        "parent_beat_id": beat.parent_beat_id,  # For scenes: the beat this scene follows
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
        # Series outline linking
        "linked_manuscript_outline_id": beat.linked_manuscript_outline_id,
        "target_book_index": beat.target_book_index,
        "created_at": beat.created_at.isoformat() if beat.created_at else None,
        "updated_at": beat.updated_at.isoformat() if beat.updated_at else None,
        "completed_at": beat.completed_at.isoformat() if beat.completed_at else None,
    }


def serialize_outline(outline: Outline) -> dict:
    """Serialize an Outline SQLAlchemy object to dict with plot_beats"""
    return {
        "id": outline.id,
        "manuscript_id": outline.manuscript_id,
        "series_id": outline.series_id,
        "world_id": outline.world_id,
        "scope": outline.scope or OUTLINE_SCOPE_MANUSCRIPT,
        "structure_type": outline.structure_type,
        "genre": outline.genre,
        "arc_type": outline.arc_type,
        "book_count": outline.book_count,
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


class SceneCreate(BaseModel):
    """Request model for creating a scene between beats"""
    scene_label: str  # User-facing title for the scene
    scene_description: Optional[str] = ""  # What should happen in this scene
    after_beat_id: str  # The beat ID this scene should follow
    target_word_count: Optional[int] = 1000  # Default 1000 words for scenes (lower than beats)
    user_notes: Optional[str] = ""


class PlotBeatResponse(BaseModel):
    id: str
    outline_id: str
    item_type: str  # BEAT or SCENE
    parent_beat_id: Optional[str]  # For scenes: the beat this scene follows
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


# === AI ANALYSIS ENDPOINTS (BEFORE GENERIC ROUTES) ===

class AIAnalysisRequest(BaseModel):
    """Request for AI analysis of outline"""
    api_key: str
    analysis_types: Optional[List[str]] = None  # ["beat_descriptions", "plot_holes", "pacing"]


@router.post("/{outline_id}/ai-analyze")
async def analyze_outline_with_ai(
    outline_id: str,
    request: AIAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run AI analysis on outline using Claude 3.5 Sonnet

    Provides intelligent suggestions for:
    - Beat descriptions based on premise
    - Plot hole detection
    - Pacing analysis

    Requires user's OpenRouter API key (BYOK pattern)

    Returns analysis results with cost breakdown
    """
    try:
        # Validate outline exists
        outline = db.query(Outline).filter(Outline.id == outline_id).first()
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")

        # Validate API key format
        if not request.api_key or len(request.api_key) < 10:
            raise HTTPException(status_code=400, detail="Invalid API key")

        # Validate we have enough context for meaningful analysis
        has_premise = bool(outline.premise and len(outline.premise) > 20)
        has_chapters = db.query(Chapter).filter(
            Chapter.manuscript_id == outline.manuscript_id,
            Chapter.is_folder == 0
        ).count() > 0

        if not has_premise and not has_chapters:
            raise HTTPException(
                status_code=400,
                detail="Not enough context for AI analysis. Please either: (1) Add a premise/logline in outline settings, or (2) Write at least 1-2 chapters of your manuscript."
            )

        # NOTE: Auto-extraction disabled - premise should be set manually by user
        # See: OutlineSettingsModal.tsx for premise editing UI

        # Initialize AI service with user's key
        ai_service = AIOutlineService(request.api_key)

        # Run analysis
        result = await ai_service.run_full_analysis(
            outline_id=outline_id,
            db=db,
            analysis_types=request.analysis_types
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"AI analysis failed: {result.get('error', 'Unknown error')}"
            )

        return {
            "success": True,
            "data": result["data"],
            "usage": result.get("usage", {}),
            "cost": result.get("cost", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/beats/{beat_id}/ai-suggest")
async def get_beat_content_suggestions(
    beat_id: str,
    request: AIAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered content suggestions for a specific plot beat

    Returns 3-5 specific scene ideas, character moments, and content suggestions

    Requires user's OpenRouter API key (BYOK pattern)
    """
    try:
        # Fetch beat and outline
        beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
        if not beat:
            raise HTTPException(status_code=404, detail="Plot beat not found")

        outline = db.query(Outline).filter(Outline.id == beat.outline_id).first()
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")

        # Get previous beats for context
        previous_beats = (
            db.query(PlotBeat)
            .filter(
                PlotBeat.outline_id == beat.outline_id,
                PlotBeat.order_index < beat.order_index
            )
            .order_by(PlotBeat.order_index.desc())
            .limit(3)
            .all()
        )

        # Validate API key
        if not request.api_key or len(request.api_key) < 10:
            raise HTTPException(status_code=400, detail="Invalid API key")

        # Initialize AI service
        ai_service = AIOutlineService(request.api_key)

        # Get suggestions
        result = await ai_service.generate_beat_content_suggestions(
            beat=beat,
            outline=outline,
            previous_beats=previous_beats
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Suggestion generation failed: {result.get('error', 'Unknown error')}"
            )

        # Calculate cost
        usage = result.get("usage", {})
        cost = OpenRouterService.calculate_cost(usage)

        return {
            "success": True,
            "data": {
                "beat_id": beat_id,
                "suggestions": result.get("suggestions", [])
            },
            "usage": usage,
            "cost": {
                "total_usd": round(cost, 4),
                "formatted": f"${cost:.4f}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Beat suggestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion generation failed: {str(e)}"
        )


class BridgeScenesRequest(BaseModel):
    """Request model for generating bridge scene suggestions"""
    from_beat_id: str  # The beat to start from
    to_beat_id: str  # The beat to arrive at
    api_key: str  # OpenRouter API key


@router.post("/{outline_id}/ai-bridge-scenes")
async def generate_bridge_scenes(
    outline_id: str,
    request: BridgeScenesRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered scene suggestions to bridge the gap between two beats.

    This feature helps writers create scenes that naturally connect major story
    beats, ensuring smooth narrative flow. Returns 2-3 scene suggestions with
    titles, descriptions, emotional purposes, and suggested word counts.

    Requires user's OpenRouter API key (BYOK pattern)
    """
    try:
        # Fetch outline
        outline = db.query(Outline).filter(Outline.id == outline_id).first()
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")

        # Fetch from_beat
        from_beat = db.query(PlotBeat).filter(
            PlotBeat.id == request.from_beat_id,
            PlotBeat.outline_id == outline_id
        ).first()
        if not from_beat:
            raise HTTPException(status_code=404, detail="From beat not found in this outline")

        # Fetch to_beat
        to_beat = db.query(PlotBeat).filter(
            PlotBeat.id == request.to_beat_id,
            PlotBeat.outline_id == outline_id
        ).first()
        if not to_beat:
            raise HTTPException(status_code=404, detail="To beat not found in this outline")

        # Validate beats are adjacent (to_beat should come after from_beat)
        if from_beat.order_index >= to_beat.order_index:
            raise HTTPException(
                status_code=400,
                detail="From beat must come before to beat in the outline"
            )

        # Validate API key
        if not request.api_key or len(request.api_key) < 10:
            raise HTTPException(status_code=400, detail="Invalid API key")

        # Initialize AI service
        ai_service = AIOutlineService(request.api_key)

        # Generate bridge scene suggestions
        result = await ai_service.generate_bridge_scenes(
            from_beat=from_beat,
            to_beat=to_beat,
            outline=outline,
            db=db
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", result.get("error", "Bridge scene generation failed"))
            )

        return {
            "success": True,
            "data": {
                "scenes": result.get("scenes", []),
                "bridging_analysis": result.get("bridging_analysis", ""),
                "from_beat_id": request.from_beat_id,
                "to_beat_id": request.to_beat_id
            },
            "usage": result.get("usage", {}),
            "cost": result.get("cost", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bridge scene generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bridge scene generation failed: {str(e)}"
        )


class GenerateChaptersRequest(BaseModel):
    """Request model for chapter generation"""
    generation_strategy: str = "one-per-beat"  # "one-per-beat", "act-folders", "custom"
    chapter_naming: str = "beat-label"  # "beat-label", "numbered", "custom"
    include_beat_description: bool = True
    create_act_folders: bool = False


@router.post("/{outline_id}/generate-chapters")
async def generate_chapters_from_outline(
    outline_id: str,
    request: GenerateChaptersRequest,
    db: Session = Depends(get_db)
):
    """
    Generate chapter scaffolding from outline plot beats

    Creates chapter placeholders automatically from plot beats with optional
    act folder organization. Chapters are automatically linked to beats.

    Strategies:
    - one-per-beat: Creates one chapter for each plot beat
    - act-folders: Groups chapters into Act 1/2/3 folders based on beat position
    """
    try:
        # Fetch outline with beats
        outline = db.query(Outline).filter(Outline.id == outline_id).first()
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")

        beats = db.query(PlotBeat).filter(
            PlotBeat.outline_id == outline_id
        ).order_by(PlotBeat.order_index).all()

        if not beats:
            raise HTTPException(status_code=400, detail="Outline has no plot beats")

        # Check how many beats already have chapters linked
        beats_with_chapters = sum(1 for beat in beats if beat.chapter_id)
        if beats_with_chapters > 0:
            logger.warning(f"{beats_with_chapters}/{len(beats)} beats already have chapters linked")

        # Group beats by act based on target_position_percent
        act_folders = {}
        chapters_created = []
        folder_structure = {}

        # Create act folders if requested
        if request.create_act_folders:
            # Act 1: 0-25%, Act 2: 25-75%, Act 3: 75-100%
            act_definitions = [
                ("Act 1", 0.0, 0.25, 0),
                ("Act 2", 0.25, 0.75, 1),
                ("Act 3", 0.75, 1.0, 2)
            ]

            for act_name, min_pos, max_pos, order in act_definitions:
                # Check if any beats fall in this act
                act_beats = [b for b in beats if min_pos <= b.target_position_percent < max_pos or
                            (b.target_position_percent == 1.0 and act_name == "Act 3")]

                if act_beats:
                    # Create act folder
                    folder = Chapter(
                        id=str(uuid.uuid4()),
                        manuscript_id=outline.manuscript_id,
                        title=act_name,
                        content="",
                        lexical_state="{}",
                        is_folder=1,
                        parent_id=None,
                        order_index=order,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(folder)
                    db.flush()  # Get folder ID
                    act_folders[act_name] = folder.id
                    folder_structure[act_name] = []
                    logger.info(f"Created act folder: {act_name}")

        # Create chapters for each beat
        for idx, beat in enumerate(beats):
            # Skip if beat already has a chapter (unless we want to override)
            if beat.chapter_id:
                logger.info(f"Skipping beat {beat.beat_name} - already has chapter {beat.chapter_id}")
                continue

            # Determine parent folder if using act folders
            parent_id = None
            act_name = None
            if request.create_act_folders:
                if beat.target_position_percent < 0.25:
                    act_name = "Act 1"
                elif beat.target_position_percent < 0.75:
                    act_name = "Act 2"
                else:
                    act_name = "Act 3"
                parent_id = act_folders.get(act_name)

            # Generate chapter title based on naming strategy
            if request.chapter_naming == "beat-label":
                chapter_title = beat.beat_label
            elif request.chapter_naming == "numbered":
                chapter_title = f"Chapter {idx + 1}"
            else:  # custom or fallback
                chapter_title = f"Chapter {idx + 1}: {beat.beat_label}"

            # Generate chapter content from beat description
            chapter_content = ""
            lexical_state = '{"root":{"children":[],"direction":null,"format":"","indent":0,"type":"root","version":1}}'

            if request.include_beat_description and beat.beat_description:
                # Create simple Lexical JSON with beat description as writing prompt
                chapter_content = f"[Writing Prompt]\n\n{beat.beat_description}\n\n---\n\nStart writing here..."

                # Convert to Lexical JSON format (simple paragraph node)
                lexical_state = f'''{{
                    "root": {{
                        "children": [
                            {{
                                "children": [
                                    {{
                                        "detail": 0,
                                        "format": 2,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "[Writing Prompt]",
                                        "type": "text",
                                        "version": 1
                                    }}
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [],
                                "direction": null,
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [
                                    {{
                                        "detail": 0,
                                        "format": 0,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "{beat.beat_description.replace('"', '\\"')}",
                                        "type": "text",
                                        "version": 1
                                    }}
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [],
                                "direction": null,
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [
                                    {{
                                        "detail": 0,
                                        "format": 0,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "---",
                                        "type": "text",
                                        "version": 1
                                    }}
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [],
                                "direction": null,
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }},
                            {{
                                "children": [
                                    {{
                                        "detail": 0,
                                        "format": 0,
                                        "mode": "normal",
                                        "style": "",
                                        "text": "Start writing here...",
                                        "type": "text",
                                        "version": 1
                                    }}
                                ],
                                "direction": "ltr",
                                "format": "",
                                "indent": 0,
                                "type": "paragraph",
                                "version": 1
                            }}
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "root",
                        "version": 1
                    }}
                }}'''

            # Create chapter
            chapter = Chapter(
                id=str(uuid.uuid4()),
                manuscript_id=outline.manuscript_id,
                title=chapter_title,
                content=chapter_content,
                lexical_state=lexical_state,
                is_folder=0,
                parent_id=parent_id,
                order_index=idx,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(chapter)
            db.flush()  # Get chapter ID

            # Link beat to chapter
            beat.chapter_id = chapter.id
            beat.updated_at = datetime.utcnow()

            chapters_created.append({
                "id": chapter.id,
                "title": chapter_title,
                "beat_id": beat.id,
                "beat_name": beat.beat_name
            })

            # Track in folder structure
            if act_name and act_name in folder_structure:
                folder_structure[act_name].append(chapter_title)

            logger.info(f"Created chapter '{chapter_title}' for beat {beat.beat_name}")

        # Commit all changes
        db.commit()

        # Return result
        result = {
            "success": True,
            "chapters_created": len(chapters_created),
            "beats_linked": len(chapters_created),
            "chapters": chapters_created
        }

        if request.create_act_folders:
            result["folder_structure"] = folder_structure

        logger.info(f"Generated {len(chapters_created)} chapters for outline {outline_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chapter generation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Chapter generation failed: {str(e)}"
        )


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


@router.post("/{outline_id}/reset-premise")
async def reset_premise(
    outline_id: str,
    db: Session = Depends(get_db)
):
    """Clear auto-extracted premise so user can set it manually via Settings UI"""
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    outline.premise = ""
    outline.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Premise cleared successfully"}


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

    # Track old chapter_id for aggregation sync
    old_chapter_id = beat.chapter_id

    # Update fields
    update_data = beat_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(beat, key, value)

    # If marking as completed, set timestamp
    if update_data.get('is_completed') and not beat.completed_at:
        beat.completed_at = datetime.utcnow()

    beat.updated_at = datetime.utcnow()

    # Check if chapter_id changed
    chapter_id_changed = ('chapter_id' in update_data and beat.chapter_id != old_chapter_id)

    db.commit()
    db.refresh(beat)

    # Sync word count if chapter link changed
    if chapter_id_changed:
        manuscript_aggregation_service.sync_plot_beat_on_link_change(
            db,
            beat_id,
            old_chapter_id,
            beat.chapter_id
        )

    return {"success": True, "data": serialize_plot_beat(beat)}


@router.delete("/beats/{beat_id}")
async def delete_plot_beat(
    beat_id: str,
    db: Session = Depends(get_db)
):
    """Delete a plot beat or scene"""
    beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
    if not beat:
        raise HTTPException(status_code=404, detail="Plot beat not found")

    # Get outline ID for reordering after deletion
    outline_id = beat.outline_id
    deleted_order = beat.order_index

    db.delete(beat)

    # Reorder remaining items to close the gap
    remaining_items = db.query(PlotBeat).filter(
        PlotBeat.outline_id == outline_id,
        PlotBeat.order_index > deleted_order
    ).all()
    for item in remaining_items:
        item.order_index -= 1

    db.commit()

    return {"success": True, "message": "Plot beat deleted"}


@router.post("/{outline_id}/scenes")
async def create_scene(
    outline_id: str,
    scene: SceneCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new scene between beats in an outline.

    Scenes are user-added outline items that bridge major story beats.
    They have lower default word counts (500-1500 words) and are inserted
    after a specified beat, shifting all subsequent items.
    """
    # Validate outline exists
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    # Validate the parent beat exists and belongs to this outline
    parent_beat = db.query(PlotBeat).filter(
        PlotBeat.id == scene.after_beat_id,
        PlotBeat.outline_id == outline_id
    ).first()
    if not parent_beat:
        raise HTTPException(status_code=404, detail="Parent beat not found in this outline")

    # Calculate new scene's order_index (insert after parent beat)
    new_order_index = parent_beat.order_index + 1

    # Shift all items after the insertion point
    items_to_shift = db.query(PlotBeat).filter(
        PlotBeat.outline_id == outline_id,
        PlotBeat.order_index >= new_order_index
    ).all()
    for item in items_to_shift:
        item.order_index += 1

    # Count existing scenes after this beat to generate unique name
    existing_scenes = db.query(PlotBeat).filter(
        PlotBeat.outline_id == outline_id,
        PlotBeat.item_type == ITEM_TYPE_SCENE,
        PlotBeat.parent_beat_id == scene.after_beat_id
    ).count()

    # Calculate position percent (midway between parent beat and next beat)
    next_beat = db.query(PlotBeat).filter(
        PlotBeat.outline_id == outline_id,
        PlotBeat.order_index == new_order_index + 1,  # After our new scene
        PlotBeat.item_type == ITEM_TYPE_BEAT
    ).first()

    if next_beat:
        # Position scene between parent beat and next beat
        position = (parent_beat.target_position_percent + next_beat.target_position_percent) / 2
    else:
        # No next beat, position at 90% of the way to 1.0
        position = parent_beat.target_position_percent + (1.0 - parent_beat.target_position_percent) * 0.5

    # Create the scene
    new_scene = PlotBeat(
        id=str(uuid.uuid4()),
        outline_id=outline_id,
        item_type=ITEM_TYPE_SCENE,
        parent_beat_id=scene.after_beat_id,
        beat_name=f"scene-{parent_beat.beat_name}-{existing_scenes + 1}",
        beat_label=scene.scene_label,
        beat_description=scene.scene_description or "",
        target_position_percent=position,
        target_word_count=scene.target_word_count or 1000,
        order_index=new_order_index,
        user_notes=scene.user_notes or "",
    )

    db.add(new_scene)
    db.commit()
    db.refresh(new_scene)

    return {"success": True, "data": serialize_plot_beat(new_scene)}


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


# ===== SERIES/WORLD OUTLINE ENDPOINTS =====

class SeriesOutlineCreate(BaseModel):
    """Request model for creating a series-level outline"""
    series_id: str
    structure_type: str  # 'trilogy-arc', 'duology-arc', 'ongoing-series', 'saga-arc'
    genre: Optional[str] = None
    target_word_count: Optional[int] = 240000  # Default trilogy length
    premise: Optional[str] = ""
    logline: Optional[str] = ""
    synopsis: Optional[str] = ""


class WorldOutlineCreate(BaseModel):
    """Request model for creating a world-level outline"""
    world_id: str
    structure_type: str
    genre: Optional[str] = None
    target_word_count: Optional[int] = 500000  # Default saga length
    premise: Optional[str] = ""
    logline: Optional[str] = ""
    synopsis: Optional[str] = ""


class LinkBeatToManuscriptRequest(BaseModel):
    """Request model for linking a series beat to a manuscript outline"""
    beat_id: str
    manuscript_outline_id: str


@router.get("/series-structures")
async def list_series_structure_templates():
    """Get list of available series structure templates"""
    return {
        "success": True,
        "structures": list_series_structures()
    }


@router.get("/series-structures/{structure_type}")
async def get_series_structure_template(structure_type: str):
    """Get detailed information about a specific series structure"""
    try:
        structure = get_series_structure(structure_type)
        return {
            "success": True,
            "structure": structure
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/series/{series_id}")
async def create_series_outline(
    series_id: str,
    outline: SeriesOutlineCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new series-level outline from a series structure template.

    Series outlines span multiple books and track the overall arc of a series.
    """
    from app.models.world import Series

    # Validate series exists
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Validate structure type
    try:
        structure = get_series_structure_for_db(outline.structure_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Deactivate other outlines for this series
    db.query(Outline).filter(
        Outline.series_id == series_id,
        Outline.scope == OUTLINE_SCOPE_SERIES,
        Outline.is_active == True
    ).update({"is_active": False})

    # Create series outline
    new_outline = Outline(
        id=str(uuid.uuid4()),
        series_id=series_id,
        scope=OUTLINE_SCOPE_SERIES,
        structure_type=outline.structure_type,
        genre=outline.genre,
        arc_type=structure["arc_type"],
        book_count=structure["book_count"],
        target_word_count=outline.target_word_count,
        premise=outline.premise,
        logline=outline.logline,
        synopsis=outline.synopsis,
        is_active=True
    )

    db.add(new_outline)
    db.flush()

    # Create plot beats from series template
    for beat_data in structure["beats"]:
        target_wc = int(outline.target_word_count * beat_data["target_position_percent"])
        new_beat = PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=new_outline.id,
            beat_name=beat_data["beat_name"],
            beat_label=beat_data["beat_label"],
            beat_description=beat_data["beat_description"],
            target_position_percent=beat_data["target_position_percent"],
            target_word_count=target_wc,
            order_index=beat_data["order_index"],
            target_book_index=beat_data["target_book_index"],
        )
        db.add(new_beat)

    db.commit()
    db.refresh(new_outline)
    _ = new_outline.plot_beats

    return {"success": True, "data": serialize_outline(new_outline)}


@router.get("/series/{series_id}")
async def get_series_outlines(
    series_id: str,
    db: Session = Depends(get_db)
):
    """Get all outlines for a series"""
    outlines = db.query(Outline).filter(
        Outline.series_id == series_id,
        Outline.scope == OUTLINE_SCOPE_SERIES
    ).order_by(Outline.created_at.desc()).all()

    return {
        "success": True,
        "data": [serialize_outline(o) for o in outlines]
    }


@router.get("/series/{series_id}/active")
async def get_active_series_outline(
    series_id: str,
    db: Session = Depends(get_db)
):
    """Get the active outline for a series"""
    outline = db.query(Outline).filter(
        Outline.series_id == series_id,
        Outline.scope == OUTLINE_SCOPE_SERIES,
        Outline.is_active == True
    ).first()

    if not outline:
        raise HTTPException(status_code=404, detail="No active outline found for series")

    _ = outline.plot_beats
    return {"success": True, "data": serialize_outline(outline)}


@router.get("/series/{series_id}/structure")
async def get_series_structure_with_manuscripts(
    series_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full series structure including linked manuscript outlines.

    Returns the series outline with information about how manuscript outlines
    are linked to series-level beats.
    """
    from app.models.world import Series
    from app.models.manuscript import Manuscript

    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Get active series outline
    series_outline = db.query(Outline).filter(
        Outline.series_id == series_id,
        Outline.scope == OUTLINE_SCOPE_SERIES,
        Outline.is_active == True
    ).first()

    # Get all manuscripts in the series
    manuscripts = db.query(Manuscript).filter(
        Manuscript.series_id == series_id
    ).order_by(Manuscript.order_index).all()

    # Get manuscript outlines
    manuscript_outlines = {}
    for ms in manuscripts:
        ms_outline = db.query(Outline).filter(
            Outline.manuscript_id == ms.id,
            Outline.scope == OUTLINE_SCOPE_MANUSCRIPT,
            Outline.is_active == True
        ).first()
        if ms_outline:
            _ = ms_outline.plot_beats
            manuscript_outlines[ms.id] = serialize_outline(ms_outline)

    result = {
        "series": {
            "id": series.id,
            "name": series.name,
            "description": series.description,
        },
        "series_outline": serialize_outline(series_outline) if series_outline else None,
        "manuscripts": [
            {
                "id": ms.id,
                "title": ms.title,
                "order_index": ms.order_index,
                "outline": manuscript_outlines.get(ms.id)
            }
            for ms in manuscripts
        ]
    }

    return {"success": True, "data": result}


@router.post("/world/{world_id}")
async def create_world_outline(
    world_id: str,
    outline: WorldOutlineCreate,
    db: Session = Depends(get_db)
):
    """
    Create a world-level meta-arc outline.

    World outlines provide the highest-level narrative arc that spans
    all series within a world.
    """
    from app.models.world import World

    # Validate world exists
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # Validate structure type (use series structures for world too)
    try:
        structure = get_series_structure_for_db(outline.structure_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Deactivate other outlines for this world
    db.query(Outline).filter(
        Outline.world_id == world_id,
        Outline.scope == OUTLINE_SCOPE_WORLD,
        Outline.is_active == True
    ).update({"is_active": False})

    # Create world outline
    new_outline = Outline(
        id=str(uuid.uuid4()),
        world_id=world_id,
        scope=OUTLINE_SCOPE_WORLD,
        structure_type=outline.structure_type,
        genre=outline.genre,
        arc_type=structure["arc_type"],
        book_count=structure["book_count"],
        target_word_count=outline.target_word_count,
        premise=outline.premise,
        logline=outline.logline,
        synopsis=outline.synopsis,
        is_active=True
    )

    db.add(new_outline)
    db.flush()

    # Create plot beats
    for beat_data in structure["beats"]:
        target_wc = int(outline.target_word_count * beat_data["target_position_percent"])
        new_beat = PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=new_outline.id,
            beat_name=beat_data["beat_name"],
            beat_label=beat_data["beat_label"],
            beat_description=beat_data["beat_description"],
            target_position_percent=beat_data["target_position_percent"],
            target_word_count=target_wc,
            order_index=beat_data["order_index"],
            target_book_index=beat_data["target_book_index"],
        )
        db.add(new_beat)

    db.commit()
    db.refresh(new_outline)
    _ = new_outline.plot_beats

    return {"success": True, "data": serialize_outline(new_outline)}


@router.get("/world/{world_id}")
async def get_world_outlines(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get all outlines for a world"""
    outlines = db.query(Outline).filter(
        Outline.world_id == world_id,
        Outline.scope == OUTLINE_SCOPE_WORLD
    ).order_by(Outline.created_at.desc()).all()

    return {
        "success": True,
        "data": [serialize_outline(o) for o in outlines]
    }


@router.post("/{outline_id}/link-manuscript")
async def link_beat_to_manuscript_outline(
    outline_id: str,
    request: LinkBeatToManuscriptRequest,
    db: Session = Depends(get_db)
):
    """
    Link a series/world beat to a manuscript outline.

    This creates a connection between high-level series arcs and
    specific manuscript implementations.
    """
    # Validate the outline exists and is series/world scope
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    if outline.scope == OUTLINE_SCOPE_MANUSCRIPT:
        raise HTTPException(
            status_code=400,
            detail="Cannot link beats from manuscript-level outlines. Use series or world outlines."
        )

    # Validate the beat exists and belongs to this outline
    beat = db.query(PlotBeat).filter(
        PlotBeat.id == request.beat_id,
        PlotBeat.outline_id == outline_id
    ).first()
    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found in this outline")

    # Validate the manuscript outline exists and is manuscript scope
    ms_outline = db.query(Outline).filter(
        Outline.id == request.manuscript_outline_id
    ).first()
    if not ms_outline:
        raise HTTPException(status_code=404, detail="Manuscript outline not found")

    if ms_outline.scope != OUTLINE_SCOPE_MANUSCRIPT:
        raise HTTPException(
            status_code=400,
            detail="Target outline must be a manuscript-level outline"
        )

    # Link the beat
    beat.linked_manuscript_outline_id = request.manuscript_outline_id
    beat.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(beat)

    return {"success": True, "data": serialize_plot_beat(beat)}