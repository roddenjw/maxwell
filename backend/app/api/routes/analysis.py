"""
Analysis API Routes - Deep narrative analysis endpoints.

Endpoints for:
- POV Consistency checking
- Scene Purpose analysis
- Relationship Evolution tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.services.pov_consistency_service import POVConsistencyService
from app.services.scene_purpose_service import ScenePurposeService
from app.services.relationship_evolution_service import RelationshipEvolutionService


router = APIRouter(prefix="/analysis", tags=["analysis"])


# ==================== Pydantic Models ====================

class ChapterAnalysisRequest(BaseModel):
    chapter_id: str


class ManuscriptAnalysisRequest(BaseModel):
    manuscript_id: str
    genre: Optional[str] = None


class RelationshipAnalysisRequest(BaseModel):
    manuscript_id: str
    character_a: str
    character_b: str


class AllRelationshipsRequest(BaseModel):
    manuscript_id: str
    world_id: Optional[str] = None


class TextAnalysisRequest(BaseModel):
    text: str
    pov_character: Optional[str] = None
    known_characters: Optional[List[str]] = None


# ==================== POV Consistency Endpoints ====================

@router.post("/pov/chapter")
def analyze_chapter_pov(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze a chapter for POV consistency"""
    service = POVConsistencyService(db)
    result = service.analyze_chapter(request.chapter_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add fix suggestions
    result["suggestions"] = service.get_fix_suggestions(result)

    return result


@router.post("/pov/manuscript")
def analyze_manuscript_pov(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze entire manuscript for POV consistency"""
    service = POVConsistencyService(db)
    result = service.analyze_manuscript(request.manuscript_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/pov/detect")
def detect_pov_type(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Detect POV type in a text passage"""
    service = POVConsistencyService(db)
    return service.detect_pov_type(request.text)


@router.post("/pov/head-hopping")
def detect_head_hopping(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Detect head-hopping in a text passage"""
    service = POVConsistencyService(db)
    return service.detect_head_hopping(request.text)


@router.post("/pov/inappropriate-knowledge")
def detect_inappropriate_knowledge(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Detect POV-inappropriate knowledge in text"""
    if not request.pov_character:
        raise HTTPException(
            status_code=400,
            detail="pov_character is required for this analysis"
        )

    service = POVConsistencyService(db)
    return service.detect_inappropriate_knowledge(
        request.text,
        request.pov_character,
        request.known_characters or []
    )


# ==================== Scene Purpose Endpoints ====================

@router.post("/scene-purpose/chapter")
def analyze_chapter_scene_purposes(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze scene purposes in a chapter"""
    service = ScenePurposeService(db)
    result = service.analyze_chapter(request.chapter_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/scene-purpose/manuscript")
def analyze_manuscript_scene_purposes(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze scene purposes across entire manuscript"""
    service = ScenePurposeService(db)
    result = service.analyze_manuscript(
        request.manuscript_id,
        genre=request.genre
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add suggestions
    result["suggestions"] = service.get_purpose_suggestions(result)

    return result


@router.post("/scene-purpose/detect")
def detect_scene_purpose(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Detect the purpose of a scene from text"""
    service = ScenePurposeService(db)
    return service.detect_scene_purpose(request.text)


@router.post("/scene-purpose/analyze-scene")
def analyze_single_scene(
    request: TextAnalysisRequest,
    title: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Analyze a single scene for purpose and quality"""
    service = ScenePurposeService(db)
    return service.analyze_scene(request.text, title)


@router.get("/scene-purpose/genre-expectations/{genre}")
def get_genre_scene_expectations(
    genre: str,
    db: Session = Depends(get_db)
):
    """Get expected scene types for a genre"""
    from app.services.scene_purpose_service import GENRE_SCENE_EXPECTATIONS, ScenePurpose

    genre_lower = genre.lower()
    if genre_lower not in GENRE_SCENE_EXPECTATIONS:
        return {
            "genre": genre,
            "supported": False,
            "available_genres": list(GENRE_SCENE_EXPECTATIONS.keys())
        }

    service = ScenePurposeService(db)
    expected = GENRE_SCENE_EXPECTATIONS[genre_lower]

    return {
        "genre": genre,
        "supported": True,
        "expected_purposes": [
            {
                "purpose": p,
                "label": service._get_purpose_label(p)
            }
            for p in expected
        ]
    }


# ==================== Relationship Evolution Endpoints ====================

@router.post("/relationships/track")
def track_relationship_evolution(
    request: RelationshipAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Track how a specific relationship evolves across a manuscript"""
    service = RelationshipEvolutionService(db)
    result = service.track_relationship_evolution(
        request.manuscript_id,
        request.character_a,
        request.character_b
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add suggestions
    result["suggestions"] = service.get_relationship_suggestions(result)

    return result


@router.post("/relationships/manuscript")
def analyze_all_relationships(
    request: AllRelationshipsRequest,
    db: Session = Depends(get_db)
):
    """Analyze all character relationships in a manuscript"""
    service = RelationshipEvolutionService(db)
    result = service.analyze_all_relationships(
        request.manuscript_id,
        world_id=request.world_id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/relationships/detect-state")
def detect_relationship_state(
    text: str = Query(..., description="Text to analyze"),
    char_a: str = Query(..., description="First character name"),
    char_b: str = Query(..., description="Second character name"),
    db: Session = Depends(get_db)
):
    """Detect the relationship state between two characters in text"""
    service = RelationshipEvolutionService(db)
    return service.detect_relationship_state(text, char_a, char_b)


@router.post("/relationships/sync-to-wiki")
def sync_relationship_to_wiki(
    request: RelationshipAnalysisRequest,
    world_id: str = Query(..., description="World ID for wiki"),
    db: Session = Depends(get_db)
):
    """Sync a relationship analysis to the world wiki"""
    service = RelationshipEvolutionService(db)

    # First track the evolution
    evolution = service.track_relationship_evolution(
        request.manuscript_id,
        request.character_a,
        request.character_b
    )

    if "error" in evolution:
        raise HTTPException(status_code=400, detail=evolution["error"])

    # Sync to wiki
    ref = service.sync_relationship_to_wiki(evolution, world_id)

    if not ref:
        raise HTTPException(
            status_code=400,
            detail="Could not sync to wiki - characters may not have wiki entries"
        )

    return {
        "status": "synced",
        "reference_id": ref.id,
        "evolution_summary": {
            "starting_state": evolution.get("starting_state"),
            "ending_state": evolution.get("ending_state"),
            "total_changes": evolution.get("total_state_changes")
        }
    }


@router.get("/relationships/states")
def get_relationship_states():
    """Get all available relationship states"""
    from app.services.relationship_evolution_service import RelationshipState, STATE_PROGRESSIONS

    states = []
    for attr in dir(RelationshipState):
        if not attr.startswith('_'):
            value = getattr(RelationshipState, attr)
            states.append({
                "value": value,
                "label": value.replace('_', ' ').title(),
                "can_progress_to": STATE_PROGRESSIONS.get(value, [])
            })

    return states


# ==================== Combined Analysis Endpoint ====================

@router.post("/full-manuscript")
def full_manuscript_analysis(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run full narrative analysis on a manuscript.
    Includes POV, Scene Purpose, and Relationship analysis.
    """
    results = {
        "manuscript_id": request.manuscript_id,
        "analyses": {}
    }

    # POV Analysis
    pov_service = POVConsistencyService(db)
    pov_result = pov_service.analyze_manuscript(request.manuscript_id)
    if "error" not in pov_result:
        results["analyses"]["pov"] = {
            "dominant_pov": pov_result.get("dominant_pov"),
            "is_consistent": pov_result.get("pov_consistency", {}).get("is_consistent"),
            "total_head_hopping": pov_result.get("total_head_hopping_instances"),
            "total_knowledge_issues": pov_result.get("total_knowledge_issues"),
            "chapters_analyzed": pov_result.get("chapters_analyzed")
        }

    # Scene Purpose Analysis
    purpose_service = ScenePurposeService(db)
    purpose_result = purpose_service.analyze_manuscript(
        request.manuscript_id,
        genre=request.genre
    )
    if "error" not in purpose_result:
        results["analyses"]["scene_purpose"] = {
            "total_scenes": purpose_result.get("total_scenes"),
            "purposeless_scenes": purpose_result.get("purposeless_scenes"),
            "purposeless_percentage": purpose_result.get("purposeless_percentage"),
            "purpose_distribution": purpose_result.get("purpose_distribution"),
            "missing_genre_purposes": len(purpose_result.get("missing_genre_purposes", []))
        }
        results["analyses"]["scene_purpose"]["suggestions"] = purpose_service.get_purpose_suggestions(purpose_result)

    # Relationship Analysis
    rel_service = RelationshipEvolutionService(db)
    rel_result = rel_service.analyze_all_relationships(request.manuscript_id)
    if "error" not in rel_result:
        results["analyses"]["relationships"] = {
            "relationships_analyzed": rel_result.get("relationships_analyzed"),
            "total_state_changes": rel_result.get("total_state_changes"),
            "total_unearned_changes": rel_result.get("total_unearned_changes"),
            "health_summary": rel_result.get("health_summary")
        }

    # Overall health score
    issues = 0
    if results["analyses"].get("pov"):
        issues += results["analyses"]["pov"].get("total_head_hopping", 0)
        issues += results["analyses"]["pov"].get("total_knowledge_issues", 0)
    if results["analyses"].get("scene_purpose"):
        issues += results["analyses"]["scene_purpose"].get("purposeless_scenes", 0)
    if results["analyses"].get("relationships"):
        issues += results["analyses"]["relationships"].get("total_unearned_changes", 0)

    if issues == 0:
        results["overall_health"] = "excellent"
    elif issues < 5:
        results["overall_health"] = "good"
    elif issues < 15:
        results["overall_health"] = "fair"
    else:
        results["overall_health"] = "needs_work"

    results["total_issues"] = issues

    return results
