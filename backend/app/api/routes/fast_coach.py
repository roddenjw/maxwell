"""
Fast Coach API Routes
Real-time writing analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.services.nlp_service import nlp_service
from app.services.fast_coach import (
    StyleAnalyzer,
    WordAnalyzer,
    ConsistencyChecker,
    Suggestion
)


router = APIRouter(prefix="/api/fast-coach", tags=["fast-coach"])


class AnalyzeRequest(BaseModel):
    """Request to analyze text"""
    text: str
    manuscript_id: str | None = None
    check_consistency: bool = True


class AnalyzeResponse(BaseModel):
    """Response with suggestions"""
    suggestions: List[Dict[str, Any]]
    stats: Dict[str, Any]


# Initialize analyzers (singleton pattern)
style_analyzer = StyleAnalyzer()
word_analyzer = WordAnalyzer()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
) -> AnalyzeResponse:
    """
    Analyze text for style, word usage, and consistency issues

    Args:
        request: Analysis request with text and options
        db: Database session

    Returns:
        Suggestions and statistics
    """
    if not request.text or len(request.text.strip()) < 10:
        return AnalyzeResponse(suggestions=[], stats={})

    all_suggestions: List[Suggestion] = []

    try:
        # Run style analysis
        style_suggestions = style_analyzer.analyze(request.text)
        all_suggestions.extend(style_suggestions)

        # Run word analysis
        word_suggestions = word_analyzer.analyze(request.text)
        all_suggestions.extend(word_suggestions)

        # Run consistency check if requested and manuscript_id provided
        if request.check_consistency and request.manuscript_id:
            consistency_checker = ConsistencyChecker(db, nlp_service)
            consistency_suggestions = consistency_checker.check(
                request.text,
                request.manuscript_id
            )
            all_suggestions.extend(consistency_suggestions)

    except Exception as e:
        # Don't fail the request - return what we have
        print(f"Fast Coach analysis error: {e}")

    # Convert suggestions to dicts
    suggestion_dicts = [s.to_dict() for s in all_suggestions]

    # Calculate stats
    stats = {
        "total_suggestions": len(suggestion_dicts),
        "by_type": _count_by_type(all_suggestions),
        "by_severity": _count_by_severity(all_suggestions)
    }

    return AnalyzeResponse(
        suggestions=suggestion_dicts,
        stats=stats
    )


def _count_by_type(suggestions: List[Suggestion]) -> Dict[str, int]:
    """Count suggestions by type"""
    counts = {}
    for suggestion in suggestions:
        type_name = suggestion.type.value
        counts[type_name] = counts.get(type_name, 0) + 1
    return counts


def _count_by_severity(suggestions: List[Suggestion]) -> Dict[str, int]:
    """Count suggestions by severity"""
    counts = {}
    for suggestion in suggestions:
        severity = suggestion.severity.value
        counts[severity] = counts.get(severity, 0) + 1
    return counts


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "fast-coach",
        "analyzers": ["style", "word", "consistency"]
    }
