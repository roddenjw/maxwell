"""
Timeline API Routes
Endpoints for timeline event management, analysis, and inconsistency detection
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.timeline_service import timeline_service
from app.services.nlp_service import nlp_service
from app.services.codex_service import codex_service

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


# ==================== Request/Response Models ====================

class EventCreateRequest(BaseModel):
    """Request to create a new timeline event"""
    manuscript_id: str
    description: str
    event_type: str = "SCENE"  # SCENE, CHAPTER, FLASHBACK, DREAM
    order_index: Optional[int] = None
    timestamp: Optional[str] = None
    location_id: Optional[str] = None
    character_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventUpdateRequest(BaseModel):
    """Request to update an existing event"""
    description: Optional[str] = None
    event_type: Optional[str] = None
    order_index: Optional[int] = None
    timestamp: Optional[str] = None
    location_id: Optional[str] = None
    character_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Timeline event response"""
    id: str
    manuscript_id: str
    description: str
    event_type: str
    order_index: int
    timestamp: Optional[str]
    location_id: Optional[str]
    character_ids: List[str]
    event_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyzeTimelineRequest(BaseModel):
    """Request to analyze text and extract timeline events"""
    manuscript_id: str
    text: str


class ReorderEventsRequest(BaseModel):
    """Request to reorder events"""
    event_ids: List[str]


class CharacterLocationRequest(BaseModel):
    """Request to track character location"""
    character_id: str
    event_id: str
    location_id: str
    manuscript_id: str


class InconsistencyResponse(BaseModel):
    """Timeline inconsistency response"""
    id: str
    manuscript_id: str
    inconsistency_type: str
    description: str
    severity: str
    affected_event_ids: List[str]
    extra_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Event CRUD Endpoints ====================

@router.post("/events", response_model=EventResponse)
async def create_event(request: EventCreateRequest):
    """Create a new timeline event"""
    try:
        event = timeline_service.create_event(
            manuscript_id=request.manuscript_id,
            description=request.description,
            event_type=request.event_type,
            order_index=request.order_index,
            timestamp=request.timestamp,
            location_id=request.location_id,
            character_ids=request.character_ids,
            metadata=request.metadata
        )
        return EventResponse.from_orm(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{manuscript_id}", response_model=List[EventResponse])
async def list_events(
    manuscript_id: str,
    event_type: Optional[str] = None,
    character_id: Optional[str] = None,
    location_id: Optional[str] = None
):
    """Get all timeline events for a manuscript with optional filters"""
    try:
        events = timeline_service.get_events(
            manuscript_id=manuscript_id,
            event_type=event_type,
            character_id=character_id,
            location_id=location_id
        )
        return [EventResponse.from_orm(event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/single/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    """Get a single event by ID"""
    event = timeline_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse.from_orm(event)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, request: EventUpdateRequest):
    """Update an existing event"""
    try:
        event = timeline_service.update_event(
            event_id=event_id,
            description=request.description,
            event_type=request.event_type,
            order_index=request.order_index,
            timestamp=request.timestamp,
            location_id=request.location_id,
            character_ids=request.character_ids,
            metadata=request.metadata
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventResponse.from_orm(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event"""
    success = timeline_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": "Event deleted"}


@router.post("/events/reorder")
async def reorder_events(request: ReorderEventsRequest):
    """Reorder events by providing list of IDs in desired order"""
    try:
        success = timeline_service.reorder_events(request.event_ids)
        return {"success": success, "message": f"Reordered {len(request.event_ids)} events"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Timeline Analysis Endpoint ====================

@router.post("/analyze")
async def analyze_timeline(request: AnalyzeTimelineRequest, background_tasks: BackgroundTasks):
    """
    Analyze text and extract timeline events using NLP
    Runs as background task
    """
    if not nlp_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="NLP service not available. Install spaCy and download en_core_web_lg model."
        )

    # Start background analysis
    background_tasks.add_task(
        _process_timeline_analysis,
        request.manuscript_id,
        request.text
    )

    return {
        "success": True,
        "message": "Timeline analysis started. Events will be created automatically.",
        "manuscript_id": request.manuscript_id
    }


async def _process_timeline_analysis(manuscript_id: str, text: str):
    """Background task to process timeline analysis"""
    try:
        print(f"🔍 Starting timeline analysis for manuscript {manuscript_id}...")

        # Get existing entities (for character/location detection)
        existing_entities = codex_service.get_entities(manuscript_id)
        existing_dicts = [
            {
                "name": e.name,
                "type": e.type,
                "aliases": e.aliases
            }
            for e in existing_entities
        ]

        # Analyze timeline
        results = nlp_service.analyze_timeline(text, manuscript_id, existing_dicts)

        print(f"📊 Found {len(results['events'])} events")

        # Create timeline events
        for event_data in results["events"]:
            # Map character names to IDs
            character_ids = []
            for char_name in event_data.get("characters", []):
                char_entity = next((e for e in existing_entities if e.name == char_name), None)
                if char_entity:
                    character_ids.append(char_entity.id)

            # Map location name to ID
            location_id = None
            if event_data.get("location"):
                loc_entity = next((e for e in existing_entities if e.name == event_data["location"]), None)
                if loc_entity:
                    location_id = loc_entity.id

            # Create event
            timeline_service.create_event(
                manuscript_id=manuscript_id,
                description=event_data["description"],
                event_type=event_data["event_type"],
                order_index=event_data["order_index"],
                timestamp=event_data.get("timestamp"),
                location_id=location_id,
                character_ids=character_ids,
                metadata=event_data.get("metadata", {})
            )

            # Track character locations if both character and location exist
            if location_id and character_ids:
                for char_id in character_ids:
                    try:
                        timeline_service.track_character_location(
                            character_id=char_id,
                            event_id=event_data["order_index"],  # Use order_index temporarily
                            location_id=location_id,
                            manuscript_id=manuscript_id
                        )
                    except Exception as e:
                        print(f"⚠️ Failed to track character location: {e}")

        print(f"✅ Timeline analysis complete. Created {len(results['events'])} events.")

        # Run inconsistency detection
        try:
            inconsistencies = timeline_service.detect_inconsistencies(manuscript_id)
            print(f"🔍 Detected {len(inconsistencies)} timeline inconsistencies")
        except Exception as e:
            print(f"⚠️ Failed to detect inconsistencies: {e}")

    except Exception as e:
        print(f"❌ Timeline analysis failed: {e}")
        import traceback
        traceback.print_exc()


# ==================== Character Location Tracking ====================

@router.post("/character-locations")
async def track_character_location(request: CharacterLocationRequest):
    """Track a character's location at a specific event"""
    try:
        location = timeline_service.track_character_location(
            character_id=request.character_id,
            event_id=request.event_id,
            location_id=request.location_id,
            manuscript_id=request.manuscript_id
        )
        return {
            "success": True,
            "data": {
                "id": location.id,
                "character_id": location.character_id,
                "event_id": location.event_id,
                "location_id": location.location_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/character-locations/{character_id}")
async def get_character_locations(character_id: str, manuscript_id: str):
    """Get all location tracking for a character"""
    try:
        locations = timeline_service.get_character_locations(character_id, manuscript_id)
        return {
            "success": True,
            "data": [
                {
                    "id": loc.id,
                    "character_id": loc.character_id,
                    "event_id": loc.event_id,
                    "location_id": loc.location_id,
                    "created_at": loc.created_at
                }
                for loc in locations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Inconsistency Detection ====================

@router.post("/inconsistencies/detect/{manuscript_id}")
async def detect_inconsistencies(manuscript_id: str):
    """Detect timeline inconsistencies for a manuscript"""
    try:
        inconsistencies = timeline_service.detect_inconsistencies(manuscript_id)
        # Convert to dict immediately while session is still open
        result = []
        for inc in inconsistencies:
            result.append({
                "id": inc.id,
                "manuscript_id": inc.manuscript_id,
                "inconsistency_type": inc.inconsistency_type,
                "description": inc.description,
                "severity": inc.severity,
                "affected_event_ids": inc.affected_event_ids,
                "extra_data": inc.extra_data,
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
            })
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inconsistencies/{manuscript_id}", response_model=List[InconsistencyResponse])
async def list_inconsistencies(manuscript_id: str, severity: Optional[str] = None):
    """Get all timeline inconsistencies for a manuscript"""
    try:
        inconsistencies = timeline_service.get_inconsistencies(manuscript_id, severity)
        return [InconsistencyResponse.from_orm(inc) for inc in inconsistencies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/inconsistencies/{inconsistency_id}")
async def resolve_inconsistency(inconsistency_id: str):
    """Mark an inconsistency as resolved (delete it)"""
    success = timeline_service.resolve_inconsistency(inconsistency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inconsistency not found")
    return {"success": True, "message": "Inconsistency resolved"}


# ==================== Timeline Statistics ====================

@router.get("/stats/{manuscript_id}")
async def get_timeline_stats(manuscript_id: str):
    """Get timeline statistics for a manuscript"""
    try:
        stats = timeline_service.get_timeline_stats(manuscript_id)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
