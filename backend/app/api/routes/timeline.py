"""
Timeline API Routes
Endpoints for timeline event management, analysis, and inconsistency detection
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.codex_service import codex_service
from app.services.nlp_service import nlp_service
from app.services.timeline_service import timeline_service

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
    chapter_id: Optional[str] = None  # Optional chapter ID to track source


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

@router.post("/events")
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
        event_data = EventResponse.from_orm(event)
        return {
            "success": True,
            "data": event_data.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{manuscript_id}")
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
        return {
            "success": True,
            "data": [EventResponse.from_orm(event).dict() for event in events]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/single/{event_id}")
async def get_event(event_id: str):
    """Get a single event by ID"""
    event = timeline_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "success": True,
        "data": EventResponse.from_orm(event).dict()
    }


@router.put("/events/{event_id}")
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
        return {
            "success": True,
            "data": EventResponse.from_orm(event).dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event"""
    success = timeline_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": "Event deleted"}


@router.delete("/events/auto-generated/{manuscript_id}")
async def delete_auto_generated_events(manuscript_id: str):
    """Delete all auto-generated events for a manuscript"""
    try:
        events = timeline_service.get_events(manuscript_id)
        deleted_count = 0

        for event in events:
            # Check if event is auto-generated
            if event.event_metadata.get("auto_generated"):
                timeline_service.delete_event(event.id)
                deleted_count += 1

        return {
            "success": True,
            "message": f"Deleted {deleted_count} auto-generated events",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/mark-auto-generated/{manuscript_id}")
async def mark_events_as_auto_generated(manuscript_id: str):
    """Mark all existing events as auto-generated (migration helper)"""
    try:
        events = timeline_service.get_events(manuscript_id)
        marked_count = 0

        for event in events:
            # Only mark if not already marked
            if not event.event_metadata.get("auto_generated"):
                event.event_metadata["auto_generated"] = True
                timeline_service.update_event(
                    event.id,
                    metadata=event.event_metadata
                )
                marked_count += 1

        return {
            "success": True,
            "message": f"Marked {marked_count} events as auto-generated",
            "marked_count": marked_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/all/{manuscript_id}")
async def delete_all_events(manuscript_id: str):
    """Delete ALL events for a manuscript (use with caution)"""
    try:
        events = timeline_service.get_events(manuscript_id)
        deleted_count = 0

        for event in events:
            timeline_service.delete_event(event.id)
            deleted_count += 1

        return {
            "success": True,
            "message": f"Deleted {deleted_count} events",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        request.text,
        request.chapter_id
    )

    return {
        "success": True,
        "message": "Timeline analysis started. Events will be created automatically.",
        "manuscript_id": request.manuscript_id
    }


async def _process_timeline_analysis(manuscript_id: str, text: str, chapter_id: Optional[str] = None):
    """Background task to process timeline analysis"""
    try:
        print(f"🔍 Starting timeline analysis for manuscript {manuscript_id}" + (f", chapter {chapter_id}" if chapter_id else "") + "...")

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

        # Get existing events for deduplication
        existing_events = timeline_service.get_events(manuscript_id)
        existing_descriptions = {e.description.lower().strip() for e in existing_events}

        # Create timeline events with deduplication
        created_count = 0
        skipped_count = 0

        for event_data in results["events"]:
            # Deduplication check - skip if exact description already exists
            event_desc = event_data["description"].strip()
            if event_desc.lower() in existing_descriptions:
                skipped_count += 1
                print(f"⏭️  Skipping duplicate event: {event_desc[:50]}...")
                continue

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

            # Create event with auto_generated flag and chapter_id
            event_metadata = event_data.get("metadata", {})
            event_metadata["auto_generated"] = True  # Mark as auto-generated
            if chapter_id:
                event_metadata["chapter_id"] = chapter_id  # Track source chapter

            timeline_service.create_event(
                manuscript_id=manuscript_id,
                description=event_desc,
                event_type=event_data["event_type"],
                order_index=event_data["order_index"],
                timestamp=event_data.get("timestamp"),
                location_id=location_id,
                character_ids=character_ids,
                metadata=event_metadata
            )

            # Add to our deduplication set
            existing_descriptions.add(event_desc.lower())
            created_count += 1

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

        print(f"✅ Timeline analysis complete. Created {created_count} new events, skipped {skipped_count} duplicates.")

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


@router.get("/inconsistencies/{manuscript_id}")
async def list_inconsistencies(manuscript_id: str, severity: Optional[str] = None):
    """Get all timeline inconsistencies for a manuscript"""
    try:
        inconsistencies = timeline_service.get_inconsistencies(manuscript_id, severity)
        return {
            "success": True,
            "data": [InconsistencyResponse.from_orm(inc).dict() for inc in inconsistencies]
        }
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


# ==================== Character Journey API ====================

@router.get("/character-journey/{character_id}")
async def get_character_journey_summary(character_id: str, manuscript_id: str):
    """
    Get comprehensive journey summary for a character.

    Returns total distance traveled, unique locations visited,
    key events, emotional arc data, and location timeline.
    """
    try:
        summary = timeline_service.get_character_journey_summary(
            character_id=character_id,
            manuscript_id=manuscript_id
        )
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Timeline Orchestrator API ====================

class TravelSpeedRequest(BaseModel):
    """Request to update travel speeds"""
    speeds: Dict[str, int]
    default_speed: Optional[int] = None


class LocationDistanceRequest(BaseModel):
    """Request to set location distance"""
    location_a_id: str
    location_b_id: str
    distance_km: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelLegRequest(BaseModel):
    """Request to create travel leg"""
    character_id: str
    from_location_id: str
    to_location_id: str
    departure_event_id: str
    arrival_event_id: str
    travel_mode: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResolveInconsistencyRequest(BaseModel):
    """Request to resolve inconsistency with notes"""
    resolution_notes: str


# Travel Configuration Endpoints

@router.put("/travel-speeds/{manuscript_id}")
async def update_travel_speeds(manuscript_id: str, request: TravelSpeedRequest):
    """Update travel speed profile for a manuscript"""
    try:
        profile = timeline_service.update_travel_speeds(
            manuscript_id=manuscript_id,
            speeds=request.speeds,
            default_speed=request.default_speed
        )
        return {
            "success": True,
            "data": {
                "id": profile.id,
                "manuscript_id": profile.manuscript_id,
                "speeds": profile.speeds,
                "default_speed": profile.default_speed
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-speeds/{manuscript_id}")
async def get_travel_speeds(manuscript_id: str):
    """Get travel speed profile for a manuscript"""
    try:
        profile = timeline_service.get_or_create_travel_profile(manuscript_id)
        return {
            "success": True,
            "data": {
                "id": profile.id,
                "manuscript_id": profile.manuscript_id,
                "speeds": profile.speeds,
                "default_speed": profile.default_speed
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/location-distance")
async def set_location_distance(request: LocationDistanceRequest):
    """Set distance between two locations"""
    try:
        # Get manuscript_id from one of the locations
        loc_a = codex_service.get_entity(request.location_a_id)
        if not loc_a:
            raise HTTPException(status_code=404, detail="Location A not found")

        distance = timeline_service.set_location_distance(
            manuscript_id=loc_a.manuscript_id,
            location_a_id=request.location_a_id,
            location_b_id=request.location_b_id,
            distance_km=request.distance_km,
            metadata=request.metadata
        )
        return {
            "success": True,
            "data": {
                "id": distance.id,
                "location_a_id": distance.location_a_id,
                "location_b_id": distance.location_b_id,
                "distance_km": distance.distance_km,
                "metadata": distance.distance_metadata
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/location-distance/{manuscript_id}/{location_a_id}/{location_b_id}")
async def get_location_distance(manuscript_id: str, location_a_id: str, location_b_id: str):
    """Get distance between two locations"""
    try:
        distance = timeline_service.get_location_distance(
            manuscript_id=manuscript_id,
            location_a_id=location_a_id,
            location_b_id=location_b_id
        )
        return {
            "success": True,
            "data": {"distance_km": distance} if distance else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Travel Leg Endpoints

@router.post("/travel-legs")
async def create_travel_leg(request: TravelLegRequest):
    """Create a travel leg for a character"""
    try:
        # Get manuscript_id from character
        char = codex_service.get_entity(request.character_id)
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")

        leg = timeline_service.create_travel_leg(
            manuscript_id=char.manuscript_id,
            character_id=request.character_id,
            from_location_id=request.from_location_id,
            to_location_id=request.to_location_id,
            departure_event_id=request.departure_event_id,
            arrival_event_id=request.arrival_event_id,
            travel_mode=request.travel_mode,
            metadata=request.metadata
        )
        return {
            "success": True,
            "data": {
                "id": leg.id,
                "character_id": leg.character_id,
                "from_location_id": leg.from_location_id,
                "to_location_id": leg.to_location_id,
                "travel_mode": leg.travel_mode,
                "distance_km": leg.distance_km,
                "required_hours": leg.required_hours,
                "available_hours": leg.available_hours,
                "is_feasible": leg.is_feasible
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-legs/{manuscript_id}")
async def get_travel_legs(manuscript_id: str):
    """Get all travel legs for a manuscript"""
    try:
        legs = timeline_service.get_travel_legs(manuscript_id)
        return {
            "success": True,
            "data": [
                {
                    "id": leg.id,
                    "character_id": leg.character_id,
                    "from_location_id": leg.from_location_id,
                    "to_location_id": leg.to_location_id,
                    "departure_event_id": leg.departure_event_id,
                    "arrival_event_id": leg.arrival_event_id,
                    "travel_mode": leg.travel_mode,
                    "distance_km": leg.distance_km,
                    "speed_kmh": leg.speed_kmh,
                    "required_hours": leg.required_hours,
                    "available_hours": leg.available_hours,
                    "is_feasible": leg.is_feasible,
                    "metadata": leg.leg_metadata
                }
                for leg in legs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Main Validation Endpoint

@router.post("/validate/{manuscript_id}")
async def validate_timeline(manuscript_id: str):
    """
    Run Timeline Orchestrator validation
    Runs all 5 validators and returns comprehensive results
    """
    try:
        inconsistencies = timeline_service.validate_timeline_orchestrator(manuscript_id)

        # Convert to dict immediately to avoid session issues
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
                "suggestion": inc.suggestion,
                "teaching_point": inc.teaching_point,
                "is_resolved": bool(inc.is_resolved),
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
                "resolution_notes": inc.resolution_notes,
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
            })

        return {
            "success": True,
            "data": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Comprehensive Data Endpoint

@router.get("/comprehensive/{manuscript_id}")
async def get_comprehensive_timeline(manuscript_id: str):
    """
    Get ALL timeline data in one request (optimized for orchestrator UI)
    Returns events, inconsistencies, travel data, stats, etc.
    """
    try:
        data = timeline_service.get_comprehensive_timeline_data(manuscript_id)

        # Add safety check for travel_profile
        if not data.get("travel_profile"):
            raise ValueError("Travel profile is None - this should not happen")

        # Convert events to dict
        events_data = []
        try:
            for e in data["events"]:
                events_data.append({
                    "id": e.id,
                    "manuscript_id": e.manuscript_id,
                    "description": e.description,
                    "event_type": e.event_type,
                    "order_index": e.order_index,
                    "timestamp": e.timestamp,
                    "location_id": e.location_id,
                    "character_ids": e.character_ids if e.character_ids else [],
                    "event_metadata": e.event_metadata if e.event_metadata else {},
                    "narrative_importance": e.narrative_importance if e.narrative_importance is not None else 5,
                    "prerequisite_ids": e.prerequisite_ids if e.prerequisite_ids else [],
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "updated_at": e.updated_at.isoformat() if e.updated_at else None
                })
        except Exception as e_err:
            print(f"ERROR converting events: {e_err}")
            raise ValueError(f"Failed to convert events: {e_err}")

        # Convert inconsistencies to dict
        inconsistencies_data = []
        try:
            for inc in data["inconsistencies"]:
                inconsistencies_data.append({
                    "id": inc.id,
                    "manuscript_id": inc.manuscript_id,
                    "inconsistency_type": inc.inconsistency_type,
                    "description": inc.description,
                    "severity": inc.severity,
                    "affected_event_ids": inc.affected_event_ids if inc.affected_event_ids else [],
                    "extra_data": inc.extra_data if inc.extra_data else {},
                    "suggestion": inc.suggestion,
                    "teaching_point": inc.teaching_point,
                    "is_resolved": bool(inc.is_resolved),
                    "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
                    "resolution_notes": inc.resolution_notes,
                    "created_at": inc.created_at.isoformat() if inc.created_at else None,
                })
        except Exception as inc_err:
            print(f"ERROR converting inconsistencies: {inc_err}")
            raise ValueError(f"Failed to convert inconsistencies: {inc_err}")

        # Convert other data
        try:
            char_locations_data = [
                {
                    "id": cl.id,
                    "character_id": cl.character_id,
                    "event_id": cl.event_id,
                    "location_id": cl.location_id,
                    "manuscript_id": cl.manuscript_id,
                    "created_at": cl.created_at.isoformat() if cl.created_at else None,
                    "updated_at": cl.updated_at.isoformat() if cl.updated_at else None,
                }
                for cl in data["character_locations"]
            ]
        except Exception as cl_err:
            print(f"ERROR converting character_locations: {cl_err}")
            raise ValueError(f"Failed to convert character_locations: {cl_err}")

        try:
            travel_legs_data = [
                {
                    "id": leg.id,
                    "character_id": leg.character_id,
                    "from_location_id": leg.from_location_id,
                    "to_location_id": leg.to_location_id,
                    "departure_event_id": leg.departure_event_id,
                    "arrival_event_id": leg.arrival_event_id,
                    "travel_mode": leg.travel_mode,
                    "is_feasible": bool(leg.is_feasible),
                    "distance_km": leg.distance_km,
                    "speed_kmh": leg.speed_kmh,
                    "required_hours": leg.required_hours,
                    "available_hours": leg.available_hours,
                    "metadata": leg.leg_metadata if leg.leg_metadata else {},
                }
                for leg in data["travel_legs"]
            ]
        except Exception as leg_err:
            print(f"ERROR converting travel_legs: {leg_err}")
            raise ValueError(f"Failed to convert travel_legs: {leg_err}")

        try:
            location_distances_data = [
                {
                    "location_a_id": ld.location_a_id,
                    "location_b_id": ld.location_b_id,
                    "distance_km": ld.distance_km,
                    "metadata": ld.distance_metadata if ld.distance_metadata else {}
                }
                for ld in data["location_distances"]
            ]
        except Exception as ld_err:
            print(f"ERROR converting location_distances: {ld_err}")
            raise ValueError(f"Failed to convert location_distances: {ld_err}")

        return {
            "success": True,
            "data": {
                "events": events_data,
                "inconsistencies": inconsistencies_data,
                "character_locations": char_locations_data,
                "travel_legs": travel_legs_data,
                "travel_profile": {
                    "speeds": data["travel_profile"].speeds,
                    "default_speed": data["travel_profile"].default_speed
                },
                "location_distances": location_distances_data,
                "stats": data["stats"]
            }
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR in get_comprehensive_timeline: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


# Issue Resolution Endpoint

@router.patch("/inconsistencies/{inconsistency_id}/resolve")
async def resolve_inconsistency_with_notes(
    inconsistency_id: str,
    request: ResolveInconsistencyRequest
):
    """Mark inconsistency as resolved with resolution notes"""
    try:
        success = timeline_service.resolve_inconsistency_with_notes(
            inconsistency_id=inconsistency_id,
            resolution_notes=request.resolution_notes
        )
        if not success:
            raise HTTPException(status_code=404, detail="Inconsistency not found")
        return {
            "success": True,
            "message": "Inconsistency resolved with notes"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
