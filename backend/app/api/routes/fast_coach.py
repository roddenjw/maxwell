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
    DialogueAnalyzer,
    ConsistencyChecker,
    Suggestion
)
from app.services.openrouter_service import OpenRouterService


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


class AIAnalyzeRequest(BaseModel):
    """Request for AI-enhanced analysis"""
    text: str
    api_key: str
    manuscript_id: str | None = None
    context: str = ""
    suggestion_type: str = "general"


class AIAnalyzeResponse(BaseModel):
    """Response with AI-enhanced suggestions"""
    success: bool
    suggestion: str | None = None
    usage: Dict[str, int] | None = None
    cost: float | None = None
    error: str | None = None


# Initialize analyzers (singleton pattern)
style_analyzer = StyleAnalyzer()
word_analyzer = WordAnalyzer()
dialogue_analyzer = DialogueAnalyzer()


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

        # Run dialogue analysis
        dialogue_suggestions = dialogue_analyzer.analyze(request.text)
        all_suggestions.extend(dialogue_suggestions)

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


@router.post("/ai-analyze", response_model=AIAnalyzeResponse)
async def ai_analyze_text(
    request: AIAnalyzeRequest,
    db: Session = Depends(get_db)
) -> AIAnalyzeResponse:
    """
    Get AI-powered writing suggestion using OpenRouter

    Args:
        request: AI analysis request with text, API key, and options
        db: Database session

    Returns:
        AI suggestion with usage and cost info
    """
    if not request.text or len(request.text.strip()) < 10:
        return AIAnalyzeResponse(
            success=False,
            error="Text too short for analysis"
        )

    if not request.api_key:
        return AIAnalyzeResponse(
            success=False,
            error="API key required"
        )

    try:
        # Initialize OpenRouter service with user's key
        openrouter = OpenRouterService(request.api_key)

        # Get AI suggestion
        result = await openrouter.get_writing_suggestion(
            text=request.text,
            context=request.context,
            suggestion_type=request.suggestion_type,
            max_tokens=500
        )

        if not result["success"]:
            return AIAnalyzeResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )

        # Calculate cost
        usage = result.get("usage", {})
        cost = OpenRouterService.calculate_cost(usage, result.get("model", ""))

        return AIAnalyzeResponse(
            success=True,
            suggestion=result["suggestion"],
            usage=usage,
            cost=cost
        )

    except Exception as e:
        print(f"AI analysis error: {e}")
        return AIAnalyzeResponse(
            success=False,
            error=str(e)
        )


@router.post("/test-api-key")
async def test_api_key(api_key: str) -> Dict[str, Any]:
    """
    Test OpenRouter API key validity

    Args:
        api_key: User's OpenRouter API key

    Returns:
        Validation status and credit info
    """
    try:
        openrouter = OpenRouterService(api_key)
        result = await openrouter.validate_api_key()
        return {"success": True, "data": result}
    except Exception as e:
        return {
            "success": False,
            "error": {
                "message": str(e),
                "valid": False
            }
        }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "fast-coach",
            "analyzers": ["style", "word", "dialogue", "consistency"],
            "ai_enabled": True
        }
    }
