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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
