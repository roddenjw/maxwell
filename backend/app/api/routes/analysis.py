"""
Analysis API Routes - Deep narrative analysis endpoints.

Endpoints for:
- POV Consistency checking
- Scene Purpose analysis
- Relationship Evolution tracking
- Emotional Beat mapping
- Subplot tracking
- Pacing optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.services.pov_consistency_service import POVConsistencyService
from app.services.scene_purpose_service import ScenePurposeService
from app.services.relationship_evolution_service import RelationshipEvolutionService
from app.services.emotional_beat_service import EmotionalBeatService
from app.services.subplot_tracker_service import SubplotTrackerService
from app.services.pacing_optimizer_service import PacingOptimizerService


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


# ==================== Unified Dashboard Endpoint ====================

class DashboardIssue(BaseModel):
    """Standardized issue format for dashboard"""
    id: str
    category: str
    severity: str
    title: str
    description: str
    location: Optional[str] = None
    fix_suggestion: Optional[str] = None
    related_wiki_entry: Optional[str] = None


@router.post("/dashboard/issues")
def get_dashboard_issues(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Get aggregated issues from all analyzers for dashboard display.
    Issues are sorted by severity and category.
    """
    issues = []

    # POV Issues
    pov_service = POVConsistencyService(db)
    pov_result = pov_service.analyze_manuscript(request.manuscript_id)
    if "error" not in pov_result:
        for ch in pov_result.get("chapter_analyses", []):
            # Head hopping
            for switch in ch.get("head_hopping", {}).get("pov_switches", [])[:3]:
                issues.append({
                    "id": f"pov-hh-{ch.get('chapter_id')}-{switch.get('paragraph_index')}",
                    "category": "pov",
                    "severity": "high",
                    "title": "Head-Hopping Detected",
                    "description": f"POV switches in {ch.get('chapter_title')}",
                    "location": f"{ch.get('chapter_title')}, paragraph {switch.get('paragraph_index')}",
                    "fix_suggestion": "Add a scene break or rewrite from single POV"
                })

    # Scene Purpose Issues
    purpose_service = ScenePurposeService(db)
    purpose_result = purpose_service.analyze_manuscript(request.manuscript_id, request.genre)
    if "error" not in purpose_result:
        for ch in purpose_result.get("chapter_analyses", []):
            for scene in ch.get("scene_analyses", []):
                if scene.get("is_purposeless"):
                    issues.append({
                        "id": f"purpose-{ch.get('chapter_id')}-{scene.get('title')}",
                        "category": "scene_purpose",
                        "severity": "medium",
                        "title": "Scene Lacks Clear Purpose",
                        "description": f"Scene in {ch.get('chapter_title')} has no clear narrative purpose",
                        "location": ch.get("chapter_title"),
                        "fix_suggestion": "Add clear plot, character, or world-building purpose"
                    })

    # Relationship Issues
    rel_service = RelationshipEvolutionService(db)
    rel_result = rel_service.analyze_all_relationships(request.manuscript_id)
    if "error" not in rel_result:
        for rel in rel_result.get("relationships", []):
            for change in rel.get("unearned_change_details", []):
                issues.append({
                    "id": f"rel-{rel.get('character_a')}-{rel.get('character_b')}-{change.get('chapter_index')}",
                    "category": "relationships",
                    "severity": "high",
                    "title": f"Unearned Relationship Change",
                    "description": f"{rel.get('character_a')} and {rel.get('character_b')}: sudden shift from {change.get('from_state')} to {change.get('to_state')}",
                    "location": change.get("chapter_title"),
                    "fix_suggestion": "Add transitional scenes showing relationship development"
                })

    # Emotional Beat Issues
    emotion_service = EmotionalBeatService(db)
    emotion_result = emotion_service.analyze_manuscript(request.manuscript_id, request.genre)
    if "error" not in emotion_result:
        for beat in emotion_result.get("missing_beats", [])[:3]:
            issues.append({
                "id": f"emotion-missing-{beat}",
                "category": "emotional_beats",
                "severity": "low",
                "title": f"Missing Emotional Beat",
                "description": f"No scenes with {emotion_service._beat_label(beat)} emotions",
                "fix_suggestion": "Consider adding scenes that evoke this emotion"
            })

    # Subplot Issues
    subplot_service = SubplotTrackerService(db)
    subplot_result = subplot_service.analyze_manuscript(request.manuscript_id)
    if "error" not in subplot_result:
        for subplot in subplot_result.get("abandoned_subplots", []):
            health = subplot_result.get("subplot_health", {}).get(subplot, {})
            issues.append({
                "id": f"subplot-abandoned-{subplot}",
                "category": "subplots",
                "severity": "high",
                "title": f"Abandoned Subplot",
                "description": f"{subplot_service._subplot_label(subplot)} subplot disappears after chapter {health.get('last_chapter', '?') + 1}",
                "fix_suggestion": "Resolve this subplot or remove early references"
            })

        for subplot in subplot_result.get("unresolved_subplots", []):
            issues.append({
                "id": f"subplot-unresolved-{subplot}",
                "category": "subplots",
                "severity": "medium",
                "title": f"Unresolved Subplot",
                "description": f"{subplot_service._subplot_label(subplot)} subplot may need resolution",
                "fix_suggestion": "Add a resolution scene or clarify continuation"
            })

    # Pacing Issues
    pacing_service = PacingOptimizerService(db)
    pacing_result = pacing_service.analyze_manuscript_pacing(request.manuscript_id, request.genre)
    if "error" not in pacing_result:
        for valley in pacing_result.get("tension_valleys", []):
            issues.append({
                "id": f"pacing-valley-{valley.get('start_chapter_index')}",
                "category": "pacing",
                "severity": valley.get("severity", "medium"),
                "title": "Tension Valley",
                "description": f"{valley.get('length')} consecutive chapters with low tension",
                "location": f"Starting at {valley.get('start_chapter_title')}",
                "fix_suggestion": "Add conflict, deadline, or revelation in this stretch"
            })

        for slow in pacing_result.get("slow_sections", [])[:3]:
            issues.append({
                "id": f"pacing-slow-{slow.get('chapter_id')}",
                "category": "pacing",
                "severity": "medium",
                "title": "Slow Section",
                "description": f"{slow.get('chapter_title')} is description-heavy",
                "location": slow.get("chapter_title"),
                "fix_suggestion": "Add dialogue or action beats"
            })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda x: (severity_order.get(x.get("severity", "low"), 3), x.get("category", "")))

    # Group by category
    by_category = {}
    for issue in issues:
        cat = issue.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(issue)

    return {
        "manuscript_id": request.manuscript_id,
        "total_issues": len(issues),
        "by_severity": {
            "high": len([i for i in issues if i.get("severity") == "high"]),
            "medium": len([i for i in issues if i.get("severity") == "medium"]),
            "low": len([i for i in issues if i.get("severity") == "low"])
        },
        "by_category": {cat: len(items) for cat, items in by_category.items()},
        "issues": issues
    }


@router.get("/dashboard/categories")
def get_issue_categories():
    """Get all issue categories with labels"""
    return [
        {"value": "pov", "label": "POV Consistency", "icon": "eye"},
        {"value": "scene_purpose", "label": "Scene Purpose", "icon": "target"},
        {"value": "relationships", "label": "Relationships", "icon": "users"},
        {"value": "emotional_beats", "label": "Emotional Beats", "icon": "heart"},
        {"value": "subplots", "label": "Subplots", "icon": "git-branch"},
        {"value": "pacing", "label": "Pacing", "icon": "activity"}
    ]


# ==================== Emotional Beat Endpoints ====================

@router.post("/emotional-beats/chapter")
def analyze_chapter_emotional_beats(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze emotional beats in a chapter"""
    service = EmotionalBeatService(db)
    result = service.analyze_chapter(request.chapter_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/emotional-beats/manuscript")
def analyze_manuscript_emotional_beats(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze emotional beats across entire manuscript"""
    service = EmotionalBeatService(db)
    result = service.analyze_manuscript(
        request.manuscript_id,
        genre=request.genre
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add suggestions
    result["suggestions"] = service.get_emotional_suggestions(result)

    return result


@router.post("/emotional-beats/detect")
def detect_emotional_beats(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Detect emotional beats in a text passage"""
    service = EmotionalBeatService(db)
    return service.detect_emotional_beats(request.text)


@router.get("/emotional-beats/genre/{genre}")
def get_genre_emotional_expectations(
    genre: str,
    db: Session = Depends(get_db)
):
    """Get expected emotional patterns for a genre"""
    from app.services.emotional_beat_service import GENRE_EMOTIONAL_PATTERNS, EmotionalBeat

    genre_lower = genre.lower()
    if genre_lower not in GENRE_EMOTIONAL_PATTERNS:
        return {
            "genre": genre,
            "supported": False,
            "available_genres": list(GENRE_EMOTIONAL_PATTERNS.keys())
        }

    service = EmotionalBeatService(db)
    expectations = GENRE_EMOTIONAL_PATTERNS[genre_lower]

    return {
        "genre": genre,
        "supported": True,
        "primary_beats": [
            {"beat": b, "label": service._beat_label(b)}
            for b in expectations.get("primary", [])
        ],
        "required_beats": [
            {"beat": b, "label": service._beat_label(b)}
            for b in expectations.get("required", [])
        ],
        "emphasis_beat": expectations.get("emphasis")
    }


# ==================== Subplot Tracker Endpoints ====================

@router.post("/subplots/chapter")
def analyze_chapter_subplots(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze subplot presence in a chapter"""
    service = SubplotTrackerService(db)
    result = service.analyze_chapter(request.chapter_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/subplots/manuscript")
def analyze_manuscript_subplots(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze subplot threads across entire manuscript"""
    service = SubplotTrackerService(db)
    result = service.analyze_manuscript(request.manuscript_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add suggestions
    result["suggestions"] = service.get_subplot_suggestions(result)

    return result


@router.post("/subplots/detect")
def detect_subplots_in_text(
    request: TextAnalysisRequest,
    characters: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Detect potential subplots in a text passage"""
    service = SubplotTrackerService(db)
    return service.detect_subplots_in_text(request.text, characters)


class SubplotSyncRequest(BaseModel):
    manuscript_id: str
    world_id: str


@router.post("/subplots/sync-to-wiki")
def sync_subplots_to_wiki(
    request: SubplotSyncRequest,
    db: Session = Depends(get_db)
):
    """Create wiki entries for tracked subplots"""
    service = SubplotTrackerService(db)

    # First analyze manuscript
    analysis = service.analyze_manuscript(request.manuscript_id)

    if "error" in analysis:
        raise HTTPException(status_code=400, detail=analysis["error"])

    # Sync to wiki
    result = service.sync_subplots_to_wiki(
        request.manuscript_id,
        request.world_id,
        analysis
    )

    return result


@router.get("/subplots/types")
def get_subplot_types():
    """Get all available subplot types"""
    from app.services.subplot_tracker_service import SubplotType

    types = []
    for attr in dir(SubplotType):
        if not attr.startswith('_'):
            value = getattr(SubplotType, attr)
            types.append({
                "value": value,
                "label": value.replace('_', ' ').title()
            })

    return types


# ==================== Pacing Optimizer Endpoints ====================

@router.post("/pacing/chapter")
def analyze_chapter_pacing(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze pacing metrics for a chapter"""
    service = PacingOptimizerService(db)
    result = service.analyze_chapter_pacing(request.chapter_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/pacing/manuscript")
def analyze_manuscript_pacing(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze pacing across entire manuscript"""
    service = PacingOptimizerService(db)
    result = service.analyze_manuscript_pacing(
        request.manuscript_id,
        genre=request.genre
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Add suggestions
    result["suggestions"] = service.get_pacing_suggestions(result)

    return result


@router.get("/pacing/genre/{genre}")
def get_genre_pacing_norms(
    genre: str,
    db: Session = Depends(get_db)
):
    """Get pacing norms for a genre"""
    from app.services.pacing_optimizer_service import GENRE_PACING

    genre_lower = genre.lower()
    if genre_lower not in GENRE_PACING:
        return {
            "genre": genre,
            "supported": False,
            "available_genres": list(GENRE_PACING.keys())
        }

    return {
        "genre": genre,
        "supported": True,
        "norms": GENRE_PACING[genre_lower]
    }


# ==================== Complete Analysis Endpoint ====================

@router.post("/complete-manuscript")
def complete_manuscript_analysis(
    request: ManuscriptAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run comprehensive narrative analysis on a manuscript.
    Includes all analysis types: POV, Scene Purpose, Relationships,
    Emotional Beats, Subplots, and Pacing.
    """
    results = {
        "manuscript_id": request.manuscript_id,
        "genre": request.genre,
        "analyses": {}
    }

    # POV Analysis
    pov_service = POVConsistencyService(db)
    pov_result = pov_service.analyze_manuscript(request.manuscript_id)
    if "error" not in pov_result:
        results["analyses"]["pov"] = {
            "dominant_pov": pov_result.get("dominant_pov"),
            "is_consistent": pov_result.get("pov_consistency", {}).get("is_consistent"),
            "head_hopping_instances": pov_result.get("total_head_hopping_instances", 0),
            "knowledge_issues": pov_result.get("total_knowledge_issues", 0)
        }

    # Scene Purpose
    purpose_service = ScenePurposeService(db)
    purpose_result = purpose_service.analyze_manuscript(request.manuscript_id, request.genre)
    if "error" not in purpose_result:
        results["analyses"]["scene_purpose"] = {
            "total_scenes": purpose_result.get("total_scenes"),
            "purposeless_scenes": purpose_result.get("purposeless_scenes", 0),
            "purpose_distribution": purpose_result.get("purpose_distribution")
        }

    # Relationships
    rel_service = RelationshipEvolutionService(db)
    rel_result = rel_service.analyze_all_relationships(request.manuscript_id)
    if "error" not in rel_result:
        results["analyses"]["relationships"] = {
            "tracked": rel_result.get("relationships_analyzed", 0),
            "unearned_changes": rel_result.get("total_unearned_changes", 0),
            "health_summary": rel_result.get("health_summary")
        }

    # Emotional Beats
    emotion_service = EmotionalBeatService(db)
    emotion_result = emotion_service.analyze_manuscript(request.manuscript_id, request.genre)
    if "error" not in emotion_result:
        results["analyses"]["emotional_beats"] = {
            "beat_distribution": emotion_result.get("beat_distribution"),
            "missing_beats": emotion_result.get("missing_beats", []),
            "genre_fit_score": emotion_result.get("genre_analysis", {}).get("fit_score")
        }

    # Subplots
    subplot_service = SubplotTrackerService(db)
    subplot_result = subplot_service.analyze_manuscript(request.manuscript_id)
    if "error" not in subplot_result:
        results["analyses"]["subplots"] = {
            "found": subplot_result.get("subplots_found", 0),
            "abandoned": len(subplot_result.get("abandoned_subplots", [])),
            "unresolved": len(subplot_result.get("unresolved_subplots", []))
        }

    # Pacing
    pacing_service = PacingOptimizerService(db)
    pacing_result = pacing_service.analyze_manuscript_pacing(request.manuscript_id, request.genre)
    if "error" not in pacing_result:
        results["analyses"]["pacing"] = {
            "avg_chapter_length": pacing_result.get("manuscript_metrics", {}).get("avg_chapter_length"),
            "length_consistency": pacing_result.get("manuscript_metrics", {}).get("length_consistency"),
            "tension_valleys": len(pacing_result.get("tension_valleys", [])),
            "slow_sections": len(pacing_result.get("slow_sections", []))
        }

    # Calculate overall score
    issues = 0
    if results["analyses"].get("pov"):
        issues += results["analyses"]["pov"].get("head_hopping_instances", 0)
        issues += results["analyses"]["pov"].get("knowledge_issues", 0)
    if results["analyses"].get("scene_purpose"):
        issues += results["analyses"]["scene_purpose"].get("purposeless_scenes", 0)
    if results["analyses"].get("relationships"):
        issues += results["analyses"]["relationships"].get("unearned_changes", 0)
    if results["analyses"].get("subplots"):
        issues += results["analyses"]["subplots"].get("abandoned", 0)
        issues += results["analyses"]["subplots"].get("unresolved", 0)
    if results["analyses"].get("pacing"):
        issues += results["analyses"]["pacing"].get("tension_valleys", 0)
        issues += len(pacing_result.get("slow_sections", []))

    # Health assessment
    if issues == 0:
        results["overall_health"] = "excellent"
        results["health_score"] = 100
    elif issues < 5:
        results["overall_health"] = "good"
        results["health_score"] = 80
    elif issues < 10:
        results["overall_health"] = "fair"
        results["health_score"] = 60
    elif issues < 20:
        results["overall_health"] = "needs_work"
        results["health_score"] = 40
    else:
        results["overall_health"] = "significant_issues"
        results["health_score"] = 20

    results["total_issues"] = issues

    return results
