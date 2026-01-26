"""
Timeline Tools for Maxwell Agents

Tools for querying timeline events, character locations, and temporal data.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.timeline import TimelineEvent, CharacterLocation, TravelLeg
from app.models.entity import Entity


class QueryTimelineInput(BaseModel):
    """Input for querying timeline"""
    manuscript_id: str = Field(description="The manuscript ID")
    character_name: Optional[str] = Field(
        default=None,
        description="Optional: filter to events involving this character"
    )
    event_type: Optional[str] = Field(
        default=None,
        description="Optional: filter by event type (SCENE, CHAPTER, FLASHBACK, DREAM)"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of events to return"
    )


class QueryTimeline(BaseTool):
    """Query timeline events"""

    name: str = "query_timeline"
    description: str = """Query timeline events from the manuscript.
    Returns chronological events with descriptions, timestamps, and characters involved.
    Use this to understand the story's sequence of events and check temporal consistency."""
    args_schema: Type[BaseModel] = QueryTimelineInput

    def _run(
        self,
        manuscript_id: str,
        character_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Build query
            query = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == manuscript_id
            )

            if event_type:
                query = query.filter(TimelineEvent.event_type == event_type)

            # Order by chronological position
            query = query.order_by(TimelineEvent.order_index)

            events = query.limit(limit).all()

            if not events:
                return f"No timeline events found for manuscript {manuscript_id}"

            # If filtering by character, get character ID
            character_id = None
            if character_name:
                character = db.query(Entity).filter(
                    Entity.manuscript_id == manuscript_id,
                    Entity.type == "CHARACTER",
                    Entity.name.ilike(f"%{character_name}%")
                ).first()
                if character:
                    character_id = character.id

            # Get entity names for display
            entity_ids = set()
            for event in events:
                entity_ids.update(event.character_ids or [])
                if event.location_id:
                    entity_ids.add(event.location_id)

            entities = db.query(Entity).filter(Entity.id.in_(entity_ids)).all()
            entity_names = {e.id: e.name for e in entities}

            # Format output
            lines = [f"Timeline ({len(events)} events):"]

            for event in events:
                # Filter by character if specified
                if character_id and character_id not in (event.character_ids or []):
                    continue

                # Format event
                timestamp_str = f"[{event.timestamp}]" if event.timestamp else ""
                type_str = f"({event.event_type})" if event.event_type != "SCENE" else ""

                lines.append(f"\n{event.order_index}. {timestamp_str} {type_str}")
                lines.append(f"   {event.description[:200]}")

                # Show characters
                if event.character_ids:
                    char_names = [
                        entity_names.get(cid, "Unknown")
                        for cid in event.character_ids
                    ]
                    lines.append(f"   Characters: {', '.join(char_names)}")

                # Show location
                if event.location_id:
                    loc_name = entity_names.get(event.location_id, "Unknown")
                    lines.append(f"   Location: {loc_name}")

            return "\n".join(lines)

        finally:
            db.close()


class QueryCharacterLocationsInput(BaseModel):
    """Input for querying character locations"""
    manuscript_id: str = Field(description="The manuscript ID")
    character_name: str = Field(description="The character to track")


class QueryCharacterLocations(BaseTool):
    """Track character's location throughout the story"""

    name: str = "query_character_locations"
    description: str = """Track where a character is at each point in the timeline.
    Use this to detect if a character is in two places at once or to understand their journey."""
    args_schema: Type[BaseModel] = QueryCharacterLocationsInput

    def _run(self, manuscript_id: str, character_name: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Find character
            character = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id,
                Entity.type == "CHARACTER",
                Entity.name.ilike(f"%{character_name}%")
            ).first()

            if not character:
                return f"Character '{character_name}' not found"

            # Get character locations
            locations = db.query(CharacterLocation).filter(
                CharacterLocation.manuscript_id == manuscript_id,
                CharacterLocation.character_id == character.id
            ).all()

            if not locations:
                return f"No location data for {character.name}"

            # Get related events and locations
            event_ids = [loc.event_id for loc in locations]
            location_ids = [loc.location_id for loc in locations]

            events = db.query(TimelineEvent).filter(
                TimelineEvent.id.in_(event_ids)
            ).all()
            event_map = {e.id: e for e in events}

            loc_entities = db.query(Entity).filter(Entity.id.in_(location_ids)).all()
            loc_names = {e.id: e.name for e in loc_entities}

            # Get travel legs
            travels = db.query(TravelLeg).filter(
                TravelLeg.manuscript_id == manuscript_id,
                TravelLeg.character_id == character.id
            ).all()

            # Format output
            lines = [f"Location history for {character.name}:"]

            for loc in sorted(locations, key=lambda l: event_map.get(l.event_id, TimelineEvent()).order_index or 0):
                event = event_map.get(loc.event_id)
                loc_name = loc_names.get(loc.location_id, "Unknown")

                if event:
                    timestamp = f"[{event.timestamp}]" if event.timestamp else ""
                    lines.append(f"- {timestamp} At {loc_name}")
                    lines.append(f"  Event: {event.description[:100]}")

            if travels:
                lines.append("\nTravel Legs:")
                for travel in travels:
                    from_loc = loc_names.get(travel.from_location_id, "?")
                    to_loc = loc_names.get(travel.to_location_id, "?")
                    feasible = "OK" if travel.is_feasible else "IMPOSSIBLE"
                    lines.append(
                        f"- {from_loc} → {to_loc} ({travel.travel_mode}) [{feasible}]"
                    )

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_timeline = QueryTimeline()
query_character_locations = QueryCharacterLocations()
