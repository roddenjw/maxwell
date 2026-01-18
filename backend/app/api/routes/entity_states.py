"""
Entity States API routes for tracking entity states at different narrative points.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.entity_state_service import entity_state_service


router = APIRouter(prefix="/api/entities", tags=["entity-states"])


# Request/Response Models

class CreateStateRequest(BaseModel):
    """Request to create a new state snapshot"""
    state_data: Dict[str, Any]
    manuscript_id: Optional[str] = None
    chapter_id: Optional[str] = None
    timeline_event_id: Optional[str] = None
    order_index: int = 0
    narrative_timestamp: Optional[str] = None
    label: Optional[str] = None
    is_canonical: bool = True


class UpdateStateRequest(BaseModel):
    """Request to update a state snapshot"""
    state_data: Optional[Dict[str, Any]] = None
    narrative_timestamp: Optional[str] = None
    label: Optional[str] = None
    is_canonical: Optional[bool] = None
    order_index: Optional[int] = None


class BulkCreateStatesRequest(BaseModel):
    """Request to create multiple state snapshots"""
    states: List[CreateStateRequest]


class StateDiffRequest(BaseModel):
    """Request to compare two states"""
    from_state_id: str
    to_state_id: str


# Helper function to serialize state
def serialize_state(state) -> Dict[str, Any]:
    """Convert EntityTimelineState to dict"""
    return {
        "id": state.id,
        "entity_id": state.entity_id,
        "manuscript_id": state.manuscript_id,
        "chapter_id": state.chapter_id,
        "timeline_event_id": state.timeline_event_id,
        "order_index": state.order_index,
        "narrative_timestamp": state.narrative_timestamp,
        "state_data": state.state_data,
        "label": state.label,
        "is_canonical": bool(state.is_canonical),
        "created_at": state.created_at.isoformat() if state.created_at else None,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None
    }


# Endpoints

@router.post("/{entity_id}/states")
async def create_state_snapshot(entity_id: str, request: CreateStateRequest):
    """
    Create a new state snapshot for an entity.

    State snapshots track how an entity changes at different narrative points
    (e.g., character age, status, allegiances at different chapters/books).
    """
    try:
        state = entity_state_service.create_state_snapshot(
            entity_id=entity_id,
            state_data=request.state_data,
            manuscript_id=request.manuscript_id,
            chapter_id=request.chapter_id,
            timeline_event_id=request.timeline_event_id,
            order_index=request.order_index,
            narrative_timestamp=request.narrative_timestamp,
            label=request.label,
            is_canonical=request.is_canonical
        )

        return {
            "success": True,
            "data": serialize_state(state)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}/states")
async def list_entity_states(
    entity_id: str,
    manuscript_id: Optional[str] = Query(None),
    canonical_only: bool = Query(False)
):
    """
    List all state snapshots for an entity.

    Optionally filter by manuscript or canonical status.
    """
    try:
        states = entity_state_service.get_entity_states(
            entity_id=entity_id,
            manuscript_id=manuscript_id,
            canonical_only=canonical_only
        )

        return {
            "success": True,
            "data": [serialize_state(state) for state in states]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}/states/at")
async def get_state_at_point(
    entity_id: str,
    manuscript_id: Optional[str] = Query(None),
    chapter_id: Optional[str] = Query(None),
    timeline_event_id: Optional[str] = Query(None)
):
    """
    Get the effective entity state at a specific narrative point.

    Returns the most relevant state snapshot based on the specified anchors.
    Priority: timeline_event_id > chapter_id > manuscript_id
    """
    try:
        state = entity_state_service.get_state_at_point(
            entity_id=entity_id,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            timeline_event_id=timeline_event_id
        )

        if not state:
            return {
                "success": True,
                "data": None,
                "message": "No state found for the specified point"
            }

        return {
            "success": True,
            "data": serialize_state(state)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{entity_id}/states/diff")
async def get_state_diff(entity_id: str, request: StateDiffRequest):
    """
    Compare two state snapshots and return the differences.

    Returns added, removed, and changed fields between the two states.
    """
    try:
        diff = entity_state_service.get_state_diff(
            entity_id=entity_id,
            from_state_id=request.from_state_id,
            to_state_id=request.to_state_id
        )

        if "error" in diff:
            raise HTTPException(status_code=404, detail=diff["error"])

        return {
            "success": True,
            "data": diff
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_id}/journey")
async def get_character_journey(
    entity_id: str,
    manuscript_id: Optional[str] = Query(None)
):
    """
    Get a character's journey through the narrative.

    Returns chronological state changes with context, useful for
    visualizing character arcs and development.
    """
    try:
        journey = entity_state_service.get_character_journey(
            character_id=entity_id,
            manuscript_id=manuscript_id
        )

        return {
            "success": True,
            "data": journey
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entity_id}/states/{state_id}")
async def update_state(entity_id: str, state_id: str, request: UpdateStateRequest):
    """
    Update a state snapshot.
    """
    try:
        state = entity_state_service.update_state(
            state_id=state_id,
            state_data=request.state_data,
            narrative_timestamp=request.narrative_timestamp,
            label=request.label,
            is_canonical=request.is_canonical,
            order_index=request.order_index
        )

        if not state:
            raise HTTPException(status_code=404, detail="State not found")

        return {
            "success": True,
            "data": serialize_state(state)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entity_id}/states/{state_id}")
async def delete_state(entity_id: str, state_id: str):
    """
    Delete a state snapshot.
    """
    try:
        deleted = entity_state_service.delete_state(state_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="State not found")

        return {
            "success": True,
            "message": "State deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{entity_id}/states/bulk")
async def bulk_create_states(entity_id: str, request: BulkCreateStatesRequest):
    """
    Create multiple state snapshots at once.

    Useful for setting up a character's journey across multiple chapters/books.
    """
    try:
        states_data = [
            {
                "state_data": s.state_data,
                "manuscript_id": s.manuscript_id,
                "chapter_id": s.chapter_id,
                "timeline_event_id": s.timeline_event_id,
                "order_index": s.order_index,
                "narrative_timestamp": s.narrative_timestamp,
                "label": s.label,
                "is_canonical": s.is_canonical
            }
            for s in request.states
        ]

        states = entity_state_service.bulk_create_states(
            entity_id=entity_id,
            states=states_data
        )

        return {
            "success": True,
            "data": [serialize_state(state) for state in states]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
