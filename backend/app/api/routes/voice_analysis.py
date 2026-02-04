"""
Voice Analysis API Routes

Endpoints for analyzing character voice consistency,
building voice profiles, and comparing character voices.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.voice_analysis_service import VoiceAnalysisService
from app.models.voice_profile import (
    CharacterVoiceProfile,
    VoiceInconsistency,
    VoiceComparison
)

router = APIRouter(prefix="/api/voice-analysis", tags=["voice-analysis"])


# --- Response Models ---

class VoiceProfileResponse(BaseModel):
    """Voice profile for a character"""
    id: str
    character_id: str
    character_name: str
    manuscript_id: str
    confidence_score: float
    profile_data: dict
    calculated_at: Optional[str]

    class Config:
        from_attributes = True


class VoiceInconsistencyResponse(BaseModel):
    """A detected voice inconsistency"""
    id: str
    character_id: str
    character_name: str
    chapter_id: str
    inconsistency_type: str
    severity: str
    description: str
    dialogue_excerpt: str
    expected_value: Optional[str]
    actual_value: Optional[str]
    suggestion: Optional[str]
    teaching_point: Optional[str]
    is_resolved: int
    start_offset: Optional[int]
    end_offset: Optional[int]

    class Config:
        from_attributes = True


class VoiceComparisonResponse(BaseModel):
    """Comparison between two character voices"""
    id: str
    character_a_id: str
    character_a_name: str
    character_b_id: str
    character_b_name: str
    overall_similarity: float
    vocabulary_similarity: float
    structure_similarity: float
    formality_similarity: float
    comparison_data: dict

    class Config:
        from_attributes = True


class ManuscriptVoiceSummary(BaseModel):
    """Summary of all character voices in a manuscript"""
    characters: List[dict]
    total_characters: int
    characters_with_profiles: int
    open_inconsistencies: int


# --- Endpoints ---

@router.get("/profile/{character_id}")
async def get_voice_profile(
    character_id: str,
    manuscript_id: str = Query(..., description="Manuscript ID"),
    rebuild: bool = Query(False, description="Force rebuild profile"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get or build a voice profile for a character.

    The profile contains analyzed metrics from the character's dialogue,
    including vocabulary patterns, sentence structure, and speech habits.
    """
    service = VoiceAnalysisService(db)

    try:
        profile = service.build_voice_profile(
            manuscript_id=manuscript_id,
            character_id=character_id,
            force_rebuild=rebuild
        )

        # Get character name
        from app.models.entity import Entity
        character = db.query(Entity).filter(Entity.id == character_id).first()
        character_name = character.name if character else "Unknown"

        return {
            "success": True,
            "data": {
                "id": profile.id,
                "character_id": profile.character_id,
                "character_name": character_name,
                "manuscript_id": profile.manuscript_id,
                "confidence_score": profile.confidence_score,
                "profile_data": profile.profile_data,
                "calculated_at": profile.calculated_at.isoformat() if profile.calculated_at else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{manuscript_id}")
async def analyze_voice_consistency(
    manuscript_id: str,
    character_id: Optional[str] = Query(None, description="Specific character to analyze"),
    chapter_id: Optional[str] = Query(None, description="Specific chapter to analyze"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Analyze voice consistency for characters in a manuscript.

    If character_id is provided, analyzes only that character.
    If chapter_id is provided, analyzes only that chapter.
    Otherwise, analyzes all characters across all chapters.
    """
    service = VoiceAnalysisService(db)

    try:
        all_inconsistencies = []

        if character_id:
            # Analyze specific character
            inconsistencies = service.detect_inconsistencies(
                manuscript_id=manuscript_id,
                character_id=character_id,
                chapter_id=chapter_id
            )
            all_inconsistencies.extend(inconsistencies)
        else:
            # Analyze all characters
            from app.models.entity import Entity
            characters = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id,
                Entity.type == "CHARACTER"
            ).all()

            for char in characters:
                inconsistencies = service.detect_inconsistencies(
                    manuscript_id=manuscript_id,
                    character_id=char.id,
                    chapter_id=chapter_id
                )
                all_inconsistencies.extend(inconsistencies)

        # Format response
        results = []
        for issue in all_inconsistencies:
            character = db.query(Entity).filter(Entity.id == issue.character_id).first()
            results.append({
                "id": issue.id,
                "character_id": issue.character_id,
                "character_name": character.name if character else "Unknown",
                "chapter_id": issue.chapter_id,
                "inconsistency_type": issue.inconsistency_type,
                "severity": issue.severity,
                "description": issue.description,
                "dialogue_excerpt": issue.dialogue_excerpt,
                "expected_value": issue.expected_value,
                "actual_value": issue.actual_value,
                "suggestion": issue.suggestion,
                "teaching_point": issue.teaching_point,
                "is_resolved": issue.is_resolved,
                "start_offset": issue.start_offset,
                "end_offset": issue.end_offset,
            })

        return {
            "success": True,
            "data": {
                "inconsistencies": results,
                "total_found": len(results),
                "by_severity": {
                    "high": sum(1 for r in results if r["severity"] == "high"),
                    "medium": sum(1 for r in results if r["severity"] == "medium"),
                    "low": sum(1 for r in results if r["severity"] == "low"),
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{character_a_id}/{character_b_id}")
async def compare_character_voices(
    character_a_id: str,
    character_b_id: str,
    manuscript_id: str = Query(..., description="Manuscript ID"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Compare two character voices for distinctiveness.

    Returns similarity scores and recommendations for
    making the voices more distinct if needed.
    """
    service = VoiceAnalysisService(db)

    try:
        comparison = service.compare_voices(
            manuscript_id=manuscript_id,
            character_a_id=character_a_id,
            character_b_id=character_b_id
        )

        return {
            "success": True,
            "data": {
                "id": comparison.id,
                "character_a_id": comparison.character_a_id,
                "character_a_name": comparison.comparison_data.get("character_a_name", "Unknown"),
                "character_b_id": comparison.character_b_id,
                "character_b_name": comparison.comparison_data.get("character_b_name", "Unknown"),
                "overall_similarity": comparison.overall_similarity,
                "vocabulary_similarity": comparison.vocabulary_similarity,
                "structure_similarity": comparison.structure_similarity,
                "formality_similarity": comparison.formality_similarity,
                "distinguishing_features_a": comparison.comparison_data.get("distinguishing_features_a", []),
                "distinguishing_features_b": comparison.comparison_data.get("distinguishing_features_b", []),
                "shared_traits": comparison.comparison_data.get("shared_traits", []),
                "recommendations": comparison.comparison_data.get("recommendations", []),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inconsistencies/{manuscript_id}")
async def get_inconsistencies(
    manuscript_id: str,
    character_id: Optional[str] = Query(None, description="Filter by character"),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    resolved: bool = Query(False, description="Include resolved issues"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get all voice inconsistencies for a manuscript.

    Can be filtered by character, severity, and resolution status.
    """
    from app.models.entity import Entity

    query = db.query(VoiceInconsistency).filter(
        VoiceInconsistency.manuscript_id == manuscript_id
    )

    if character_id:
        query = query.filter(VoiceInconsistency.character_id == character_id)

    if severity:
        query = query.filter(VoiceInconsistency.severity == severity)

    if not resolved:
        query = query.filter(VoiceInconsistency.is_resolved == 0)

    issues = query.order_by(VoiceInconsistency.created_at.desc()).all()

    results = []
    for issue in issues:
        character = db.query(Entity).filter(Entity.id == issue.character_id).first()
        results.append({
            "id": issue.id,
            "character_id": issue.character_id,
            "character_name": character.name if character else "Unknown",
            "chapter_id": issue.chapter_id,
            "inconsistency_type": issue.inconsistency_type,
            "severity": issue.severity,
            "description": issue.description,
            "dialogue_excerpt": issue.dialogue_excerpt,
            "suggestion": issue.suggestion,
            "is_resolved": issue.is_resolved,
        })

    return {
        "success": True,
        "data": results
    }


@router.put("/inconsistencies/{issue_id}/resolve")
async def resolve_inconsistency(
    issue_id: str,
    feedback: Optional[str] = Query(None, description="User feedback: correct, incorrect, uncertain"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Mark a voice inconsistency as resolved.

    Optionally provide feedback on whether the detection was correct.
    """
    from datetime import datetime

    issue = db.query(VoiceInconsistency).filter(
        VoiceInconsistency.id == issue_id
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Inconsistency not found")

    issue.is_resolved = 1
    issue.resolved_at = datetime.utcnow()
    if feedback:
        issue.user_feedback = feedback

    db.commit()

    return {
        "success": True,
        "message": "Inconsistency marked as resolved"
    }


@router.put("/inconsistencies/{issue_id}/dismiss")
async def dismiss_inconsistency(
    issue_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dismiss a voice inconsistency (false positive).
    """
    issue = db.query(VoiceInconsistency).filter(
        VoiceInconsistency.id == issue_id
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Inconsistency not found")

    issue.is_resolved = 2  # 2 = dismissed
    issue.user_feedback = "incorrect"

    db.commit()

    return {
        "success": True,
        "message": "Inconsistency dismissed"
    }


@router.get("/summary/{manuscript_id}")
async def get_voice_summary(
    manuscript_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get a summary of all character voices in a manuscript.

    Returns an overview of which characters have profiles,
    their confidence levels, and open inconsistencies.
    """
    service = VoiceAnalysisService(db)

    try:
        summary = service.get_manuscript_voice_summary(manuscript_id)
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/build-all/{manuscript_id}")
async def build_all_voice_profiles(
    manuscript_id: str,
    force_rebuild: bool = Query(False, description="Force rebuild existing profiles"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Build voice profiles for all characters in a manuscript.

    This analyzes all character dialogue and creates/updates profiles.
    """
    from app.models.entity import Entity

    service = VoiceAnalysisService(db)

    characters = db.query(Entity).filter(
        Entity.manuscript_id == manuscript_id,
        Entity.type == "CHARACTER"
    ).all()

    profiles_built = []
    for char in characters:
        try:
            profile = service.build_voice_profile(
                manuscript_id=manuscript_id,
                character_id=char.id,
                force_rebuild=force_rebuild
            )
            profiles_built.append({
                "character_id": char.id,
                "character_name": char.name,
                "confidence_score": profile.confidence_score,
                "dialogue_samples": profile.profile_data.get("dialogue_samples", 0) if profile.profile_data else 0,
            })
        except Exception as e:
            profiles_built.append({
                "character_id": char.id,
                "character_name": char.name,
                "error": str(e)
            })

    return {
        "success": True,
        "data": {
            "profiles_built": len([p for p in profiles_built if "error" not in p]),
            "profiles": profiles_built
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "voice-analysis",
            "features": [
                "voice_profiles",
                "inconsistency_detection",
                "voice_comparison",
                "formality_analysis",
                "vocabulary_analysis"
            ]
        }
    }
