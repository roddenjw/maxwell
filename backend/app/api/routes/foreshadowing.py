"""
Foreshadowing API Routes

Endpoints for managing foreshadowing setup/payoff pairs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.foreshadowing_service import foreshadowing_service


router = APIRouter(prefix="/api/foreshadowing", tags=["foreshadowing"])


# ==================== Request/Response Models ====================

class ForeshadowingCreateRequest(BaseModel):
    """Request to create a new foreshadowing pair"""
    manuscript_id: str
    foreshadowing_event_id: str
    foreshadowing_type: str = "HINT"  # CHEKHOV_GUN, PROPHECY, SYMBOL, HINT, PARALLEL
    foreshadowing_text: str
    payoff_event_id: Optional[str] = None
    payoff_text: Optional[str] = None
    confidence: int = Field(default=5, ge=1, le=10)
    notes: Optional[str] = None


class ForeshadowingUpdateRequest(BaseModel):
    """Request to update an existing foreshadowing pair"""
    foreshadowing_type: Optional[str] = None
    foreshadowing_text: Optional[str] = None
    payoff_event_id: Optional[str] = None
    payoff_text: Optional[str] = None
    confidence: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None


class LinkPayoffRequest(BaseModel):
    """Request to link a payoff event to a foreshadowing setup"""
    payoff_event_id: str
    payoff_text: str


class ForeshadowingResponse(BaseModel):
    """Foreshadowing pair response"""
    id: str
    manuscript_id: str
    foreshadowing_event_id: str
    foreshadowing_type: str
    foreshadowing_text: str
    payoff_event_id: Optional[str]
    payoff_text: Optional[str]
    is_resolved: bool
    confidence: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def _pair_to_response(pair) -> dict:
    """Convert ForeshadowingPair to response dict"""
    return {
        "id": pair.id,
        "manuscript_id": pair.manuscript_id,
        "foreshadowing_event_id": pair.foreshadowing_event_id,
        "foreshadowing_type": pair.foreshadowing_type,
        "foreshadowing_text": pair.foreshadowing_text,
        "payoff_event_id": pair.payoff_event_id,
        "payoff_text": pair.payoff_text,
        "is_resolved": bool(pair.is_resolved),
        "confidence": pair.confidence,
        "notes": pair.notes,
        "created_at": pair.created_at.isoformat() if pair.created_at else None,
        "updated_at": pair.updated_at.isoformat() if pair.updated_at else None,
    }


# ==================== CRUD Endpoints ====================

@router.post("/pairs")
async def create_foreshadowing_pair(request: ForeshadowingCreateRequest):
    """Create a new foreshadowing setup/payoff pair"""
    try:
        pair = foreshadowing_service.create_foreshadowing_pair(
            manuscript_id=request.manuscript_id,
            foreshadowing_event_id=request.foreshadowing_event_id,
            foreshadowing_type=request.foreshadowing_type,
            foreshadowing_text=request.foreshadowing_text,
            payoff_event_id=request.payoff_event_id,
            payoff_text=request.payoff_text,
            confidence=request.confidence,
            notes=request.notes,
        )
        return {
            "success": True,
            "data": _pair_to_response(pair)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pairs/{manuscript_id}")
async def list_foreshadowing_pairs(
    manuscript_id: str,
    include_resolved: bool = True,
    foreshadowing_type: Optional[str] = None,
):
    """Get all foreshadowing pairs for a manuscript"""
    try:
        pairs = foreshadowing_service.get_foreshadowing_pairs(
            manuscript_id=manuscript_id,
            include_resolved=include_resolved,
            foreshadowing_type=foreshadowing_type,
        )
        return {
            "success": True,
            "data": [_pair_to_response(p) for p in pairs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pairs/single/{pair_id}")
async def get_foreshadowing_pair(pair_id: str):
    """Get a single foreshadowing pair by ID"""
    pair = foreshadowing_service.get_foreshadowing_pair(pair_id)
    if not pair:
        raise HTTPException(status_code=404, detail="Foreshadowing pair not found")
    return {
        "success": True,
        "data": _pair_to_response(pair)
    }


@router.put("/pairs/{pair_id}")
async def update_foreshadowing_pair(pair_id: str, request: ForeshadowingUpdateRequest):
    """Update an existing foreshadowing pair"""
    try:
        pair = foreshadowing_service.update_foreshadowing_pair(
            pair_id=pair_id,
            foreshadowing_type=request.foreshadowing_type,
            foreshadowing_text=request.foreshadowing_text,
            payoff_event_id=request.payoff_event_id,
            payoff_text=request.payoff_text,
            confidence=request.confidence,
            notes=request.notes,
        )
        if not pair:
            raise HTTPException(status_code=404, detail="Foreshadowing pair not found")
        return {
            "success": True,
            "data": _pair_to_response(pair)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pairs/{pair_id}")
async def delete_foreshadowing_pair(pair_id: str):
    """Delete a foreshadowing pair"""
    success = foreshadowing_service.delete_foreshadowing_pair(pair_id)
    if not success:
        raise HTTPException(status_code=404, detail="Foreshadowing pair not found")
    return {"success": True, "message": "Foreshadowing pair deleted"}


# ==================== Payoff Linking Endpoints ====================

@router.post("/pairs/{pair_id}/link-payoff")
async def link_payoff(pair_id: str, request: LinkPayoffRequest):
    """Link a payoff event to an existing foreshadowing setup"""
    try:
        pair = foreshadowing_service.link_payoff(
            pair_id=pair_id,
            payoff_event_id=request.payoff_event_id,
            payoff_text=request.payoff_text,
        )
        if not pair:
            raise HTTPException(status_code=404, detail="Foreshadowing pair not found")
        return {
            "success": True,
            "data": _pair_to_response(pair),
            "message": "Payoff linked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pairs/{pair_id}/unlink-payoff")
async def unlink_payoff(pair_id: str):
    """Remove the payoff from a foreshadowing pair"""
    try:
        pair = foreshadowing_service.unlink_payoff(pair_id)
        if not pair:
            raise HTTPException(status_code=404, detail="Foreshadowing pair not found")
        return {
            "success": True,
            "data": _pair_to_response(pair),
            "message": "Payoff unlinked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Query Endpoints ====================

@router.get("/unresolved/{manuscript_id}")
async def get_unresolved_foreshadowing(manuscript_id: str):
    """
    Get all unresolved foreshadowing setups (Chekhov violations).

    These are setups that haven't been linked to a payoff event.
    Useful for finding plot threads that need resolution.
    """
    try:
        pairs = foreshadowing_service.get_unresolved_foreshadowing(manuscript_id)
        return {
            "success": True,
            "data": [_pair_to_response(p) for p in pairs],
            "count": len(pairs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}")
async def get_foreshadowing_for_event(event_id: str):
    """
    Get all foreshadowing pairs involving a specific event.

    Returns pairs where the event is either a setup or a payoff.
    """
    try:
        result = foreshadowing_service.get_foreshadowing_for_event(event_id)
        return {
            "success": True,
            "data": {
                "setups": [_pair_to_response(p) for p in result["setups"]],
                "payoffs": [_pair_to_response(p) for p in result["payoffs"]],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{manuscript_id}")
async def get_foreshadowing_stats(manuscript_id: str):
    """Get foreshadowing statistics for a manuscript"""
    try:
        stats = foreshadowing_service.get_foreshadowing_stats(manuscript_id)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{pair_id}")
async def suggest_potential_payoffs(pair_id: str):
    """
    Get suggested potential payoff events for an unresolved foreshadowing setup.

    Uses keyword matching to find candidate events that could resolve the setup.
    """
    try:
        suggestions = foreshadowing_service.suggest_potential_payoffs(pair_id)
        return {
            "success": True,
            "data": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
