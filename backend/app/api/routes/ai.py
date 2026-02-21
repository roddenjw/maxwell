"""
AI Routes - Standalone AI endpoints for Maxwell

Provides reusable AI capabilities:
- POST /api/ai/refine - Generic refinement loop for any suggestion type
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.refinement_service import refinement_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


class RefineRequest(BaseModel):
    """Request body for the refinement endpoint"""
    api_key: str
    domain: str
    original: Dict[str, Any]
    feedback: str
    context: Dict[str, str] = {}
    history: List[Dict[str, str]] = []


@router.post("/refine")
async def refine_suggestion(request: RefineRequest):
    """
    Refine an AI suggestion based on user feedback.

    Generic endpoint that works across all suggestion types:
    - beat_suggestion: Scene/beat ideas for outlines
    - beat_description: Plot beat descriptions
    - beat_mapping: Chapter-to-beat mappings
    - brainstorm_idea: Brainstorming ideas
    - entity_suggestion: Character/location/item descriptions
    - wiki_entry: Wiki entries
    - plot_hole_fix: Plot hole fix suggestions
    - writing_feedback: Writing feedback
    """
    if not request.api_key or len(request.api_key) < 10:
        raise HTTPException(status_code=400, detail="Invalid API key")

    try:
        result = await refinement_service.refine(
            api_key=request.api_key,
            domain=request.domain,
            original=request.original,
            feedback=request.feedback,
            context=request.context,
            history=request.history,
        )

        return {
            "success": True,
            "data": result.get("refined", request.original),
            "error": result.get("error"),
            "usage": result.get("usage", {}),
            "cost": result.get("cost", {"total_usd": 0, "formatted": "$0.00"}),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Refinement error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Refinement failed: {str(e)}"
        )
