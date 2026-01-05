"""
Timeline Database Models

Tables:
- timeline_events: Story events with chronological ordering
- character_locations: Track character positions across events
- timeline_inconsistencies: Detected timeline issues
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base
import uuid
from datetime import datetime


class TimelineEvent(Base):
    """
    Represents a story event in the timeline

    Tracks:
    - Chronological order (order_index)
    - In-story timestamp (e.g., "Day 3, Morning")
    - Location where event occurs
    - Characters involved
    - Event type (SCENE, CHAPTER, FLASHBACK, etc.)
    """
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # Event details
    description = Column(Text, nullable=False)  # Brief description of what happens
    event_type = Column(String, nullable=False, default="SCENE")  # SCENE, CHAPTER, FLASHBACK, DREAM, etc.

    # Ordering
    order_index = Column(Integer, nullable=False, default=0)  # Chronological order (0, 1, 2, ...)
    timestamp = Column(String, nullable=True)  # In-story time (e.g., "Day 3, Morning", "July 1850")

    # Relationships
    location_id = Column(String, ForeignKey("entities.id"), nullable=True)  # Where event happens
    character_ids = Column(JSON, nullable=False, default=list)  # List of character entity IDs involved

    # Event metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    event_metadata = Column(JSON, nullable=False, default=dict)  # Additional data (word_count, dialogue_count, etc.)

    # Timeline Orchestrator fields
    narrative_importance = Column(Integer, nullable=False, default=5)  # 1-10 scale for teaching priority
    prerequisite_ids = Column(JSON, nullable=False, default=list)  # Event IDs that must occur before this event

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CharacterLocation(Base):
    """
    Tracks character location at specific events

    Enables:
    - Location tracking across timeline
    - Detection of characters in two places at once
    - Character journey visualization
    """
    __tablename__ = "character_locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # References
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    event_id = Column(String, ForeignKey("timeline_events.id"), nullable=False)
    location_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TimelineInconsistency(Base):
    """
    Detected timeline inconsistencies

    Types:
    - LOCATION_CONFLICT: Character in two places at once
    - TIMESTAMP_VIOLATION: Events out of chronological order
    - CHARACTER_RESURRECTION: Character appears after death
    - MISSING_TRANSITION: Unexplained location/state change
    """
    __tablename__ = "timeline_inconsistencies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # Inconsistency details
    inconsistency_type = Column(String, nullable=False)  # LOCATION_CONFLICT, TIMESTAMP_VIOLATION, etc.
    description = Column(Text, nullable=False)  # Human-readable explanation
    severity = Column(String, nullable=False, default="MEDIUM")  # HIGH, MEDIUM, LOW

    # References
    affected_event_ids = Column(JSON, nullable=False, default=list)  # Events involved in inconsistency

    # Additional data (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    extra_data = Column(JSON, nullable=False, default=dict)  # Context-specific data

    # Timeline Orchestrator fields
    suggestion = Column(Text, nullable=True)  # 3-4 non-prescriptive options for fixing the issue
    teaching_point = Column(Text, nullable=True)  # Reader psychology explanation
    is_resolved = Column(Integer, default=0)  # 0 = pending, 1 = resolved
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)  # How author addressed the issue

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TravelLeg(Base):
    """
    Tracks character travel between locations

    Used by Timeline Orchestrator to:
    - Record character journeys with departure/arrival dates
    - Calculate travel feasibility (distance vs. available time)
    - Detect impossible travel scenarios
    """
    __tablename__ = "travel_legs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # Journey details
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    from_location_id = Column(String, ForeignKey("entities.id"), nullable=False)
    to_location_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Timeline anchoring
    departure_event_id = Column(String, ForeignKey("timeline_events.id"), nullable=False)
    arrival_event_id = Column(String, ForeignKey("timeline_events.id"), nullable=False)

    # Travel mode (references TravelSpeedProfile)
    travel_mode = Column(String, nullable=False)  # "walking", "horse", "ship", "teleport", etc.

    # Auto-calculated fields (populated by validator)
    distance_km = Column(Integer, nullable=True)  # Distance between locations
    speed_kmh = Column(Integer, nullable=True)  # Speed from profile
    required_hours = Column(Integer, nullable=True)  # Calculated: distance / speed
    available_hours = Column(Integer, nullable=True)  # Time between events
    is_feasible = Column(Integer, default=1)  # 0 = impossible, 1 = feasible

    # Metadata
    leg_metadata = Column(JSON, nullable=False, default=dict)  # Route notes, rest stops, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TravelSpeedProfile(Base):
    """
    World-specific travel speeds for different modes of transport

    One profile per manuscript - allows for fantasy/sci-fi customization
    (e.g., dragons fly faster than horses, magic portals are instant)
    """
    __tablename__ = "travel_speed_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True, unique=True)

    # Speed definitions (stored as JSON dict for flexibility)
    # Example: {"walking": 5, "horse": 15, "carriage": 10, "ship": 20, "dragon": 80, "teleport": 999999}
    speeds = Column(JSON, nullable=False, default=dict)

    # Default speed if mode not specified (km/h)
    default_speed = Column(Integer, nullable=False, default=5)  # Walking speed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LocationDistance(Base):
    """
    Distance matrix between locations

    Allows authors to define world geography
    (e.g., King's Landing to Winterfell = 900km)
    """
    __tablename__ = "location_distances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # Location pair (bidirectional: A->B and B->A should have same distance)
    # Stored with smaller ID first for consistency
    location_a_id = Column(String, ForeignKey("entities.id"), nullable=False)
    location_b_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Distance in kilometers
    distance_km = Column(Integer, nullable=False)

    # Optional metadata
    distance_metadata = Column(JSON, nullable=False, default=dict)
    # Example: {"terrain": "mountain", "road_quality": "poor", "notes": "Dangerous pass"}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
