"""
Timeline Service - Event tracking and chronology validation

Manages:
- Timeline events (create, read, update, delete)
- Chronological ordering
- Character location tracking across events
- Timeline inconsistency detection
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.timeline import TimelineEvent, TimelineInconsistency, CharacterLocation
from app.models.entity import Entity


class TimelineService:
    """Service for managing timeline events and chronology"""

    def __init__(self):
        pass

    # ==================== Event CRUD ====================

    def create_event(
        self,
        manuscript_id: str,
        description: str,
        event_type: str = "SCENE",
        order_index: Optional[int] = None,
        timestamp: Optional[str] = None,
        location_id: Optional[str] = None,
        character_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TimelineEvent:
        """
        Create a new timeline event

        Args:
            manuscript_id: ID of the manuscript
            description: Description of the event
            event_type: Type (SCENE, CHAPTER, FLASHBACK, etc.)
            order_index: Numerical order in timeline (auto-assigned if None)
            timestamp: In-story timestamp (e.g., "Day 3, Morning")
            location_id: Entity ID of location where event occurs
            character_ids: List of character entity IDs involved
            metadata: Additional data (dialogue_count, word_count, etc.)
        """
        db = SessionLocal()
        try:
            # Auto-assign order_index if not provided
            if order_index is None:
                max_order = db.query(TimelineEvent).filter(
                    TimelineEvent.manuscript_id == manuscript_id
                ).count()
                order_index = max_order

            event = TimelineEvent(
                manuscript_id=manuscript_id,
                description=description,
                event_type=event_type,
                order_index=order_index,
                timestamp=timestamp,
                location_id=location_id,
                character_ids=character_ids or [],
                event_metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            print(f"✅ Created event: {event.description[:50]}...")
            return event
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to create event: {e}")
            raise
        finally:
            db.close()

    def get_events(
        self,
        manuscript_id: str,
        event_type: Optional[str] = None,
        character_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> List[TimelineEvent]:
        """
        Get timeline events with optional filters

        Args:
            manuscript_id: Filter by manuscript
            event_type: Filter by event type (SCENE, CHAPTER, etc.)
            character_id: Filter by character involvement
            location_id: Filter by location
        """
        db = SessionLocal()
        try:
            query = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == manuscript_id
            )

            if event_type:
                query = query.filter(TimelineEvent.event_type == event_type)

            if location_id:
                query = query.filter(TimelineEvent.location_id == location_id)

            if character_id:
                query = query.filter(
                    TimelineEvent.character_ids.contains([character_id])
                )

            events = query.order_by(TimelineEvent.order_index).all()
            print(f"📚 Retrieved {len(events)} events for manuscript {manuscript_id}")
            return events
        finally:
            db.close()

    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        """Get single event by ID"""
        db = SessionLocal()
        try:
            event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
            return event
        finally:
            db.close()

    def update_event(
        self,
        event_id: str,
        description: Optional[str] = None,
        event_type: Optional[str] = None,
        order_index: Optional[int] = None,
        timestamp: Optional[str] = None,
        location_id: Optional[str] = None,
        character_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TimelineEvent]:
        """Update an existing event"""
        db = SessionLocal()
        try:
            event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
            if not event:
                return None

            if description is not None:
                event.description = description
            if event_type is not None:
                event.event_type = event_type
            if order_index is not None:
                event.order_index = order_index
            if timestamp is not None:
                event.timestamp = timestamp
            if location_id is not None:
                event.location_id = location_id
            if character_ids is not None:
                event.character_ids = character_ids
            if metadata is not None:
                event.event_metadata = metadata

            event.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(event)

            print(f"✅ Updated event: {event.id}")
            return event
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to update event: {e}")
            raise
        finally:
            db.close()

    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        db = SessionLocal()
        try:
            event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
            if not event:
                return False

            db.delete(event)
            db.commit()
            print(f"✅ Deleted event: {event_id}")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to delete event: {e}")
            raise
        finally:
            db.close()

    def reorder_events(self, event_ids_in_order: List[str]) -> bool:
        """
        Reorder events by providing list of IDs in desired order
        Updates order_index for each event
        """
        db = SessionLocal()
        try:
            for index, event_id in enumerate(event_ids_in_order):
                event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
                if event:
                    event.order_index = index
                    event.updated_at = datetime.utcnow()

            db.commit()
            print(f"✅ Reordered {len(event_ids_in_order)} events")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to reorder events: {e}")
            raise
        finally:
            db.close()

    # ==================== Character Location Tracking ====================

    def track_character_location(
        self,
        character_id: str,
        event_id: str,
        location_id: str,
        manuscript_id: str
    ) -> CharacterLocation:
        """
        Track where a character is at a specific event
        """
        db = SessionLocal()
        try:
            # Check if already tracked
            existing = db.query(CharacterLocation).filter(
                and_(
                    CharacterLocation.character_id == character_id,
                    CharacterLocation.event_id == event_id
                )
            ).first()

            if existing:
                existing.location_id = location_id
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing

            char_location = CharacterLocation(
                character_id=character_id,
                event_id=event_id,
                location_id=location_id,
                manuscript_id=manuscript_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(char_location)
            db.commit()
            db.refresh(char_location)

            print(f"✅ Tracked character location: {character_id} at {location_id}")
            return char_location
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to track character location: {e}")
            raise
        finally:
            db.close()

    def get_character_locations(
        self,
        character_id: str,
        manuscript_id: str
    ) -> List[CharacterLocation]:
        """Get all location tracking for a character"""
        db = SessionLocal()
        try:
            locations = db.query(CharacterLocation).filter(
                and_(
                    CharacterLocation.character_id == character_id,
                    CharacterLocation.manuscript_id == manuscript_id
                )
            ).all()
            return locations
        finally:
            db.close()

    def get_character_at_event(
        self,
        event_id: str
    ) -> List[CharacterLocation]:
        """Get all character locations at a specific event"""
        db = SessionLocal()
        try:
            locations = db.query(CharacterLocation).filter(
                CharacterLocation.event_id == event_id
            ).all()
            return locations
        finally:
            db.close()

    # ==================== Timeline Inconsistency Detection ====================

    def detect_inconsistencies(
        self,
        manuscript_id: str
    ) -> List[TimelineInconsistency]:
        """
        Detect timeline inconsistencies:
        - Character in two places at once
        - Conflicting timestamps
        - Event order violations
        - Character death/resurrection
        """
        db = SessionLocal()
        inconsistencies = []

        try:
            events = self.get_events(manuscript_id)

            # 1. Detect characters in multiple locations simultaneously
            for i, event in enumerate(events):
                if not event.character_ids:
                    continue

                # Get all character locations at this event
                char_locs = self.get_character_at_event(event.id)
                char_loc_map = {cl.character_id: cl.location_id for cl in char_locs}

                # Check if event location conflicts with character locations
                if event.location_id:
                    for char_id in event.character_ids:
                        tracked_loc = char_loc_map.get(char_id)
                        if tracked_loc and tracked_loc != event.location_id:
                            # Character is supposed to be elsewhere
                            char_entity = db.query(Entity).filter(Entity.id == char_id).first()
                            event_loc = db.query(Entity).filter(Entity.id == event.location_id).first()
                            tracked_loc_entity = db.query(Entity).filter(Entity.id == tracked_loc).first()

                            inconsistency = TimelineInconsistency(
                                manuscript_id=manuscript_id,
                                inconsistency_type="LOCATION_CONFLICT",
                                description=f"{char_entity.name if char_entity else 'Character'} is in {event_loc.name if event_loc else 'unknown location'} but also tracked at {tracked_loc_entity.name if tracked_loc_entity else 'another location'}",
                                affected_event_ids=[event.id],
                                severity="HIGH",
                                extra_data={
                                    "character_id": char_id,
                                    "event_location": event.location_id,
                                    "tracked_location": tracked_loc
                                },
                                created_at=datetime.utcnow()
                            )
                            db.add(inconsistency)
                            inconsistencies.append(inconsistency)

            # 2. Detect timestamp order violations
            for i in range(len(events) - 1):
                current_event = events[i]
                next_event = events[i + 1]

                if current_event.timestamp and next_event.timestamp:
                    # Simple string comparison (assumes format like "Day 3, Morning")
                    if current_event.timestamp > next_event.timestamp:
                        inconsistency = TimelineInconsistency(
                            manuscript_id=manuscript_id,
                            inconsistency_type="TIMESTAMP_VIOLATION",
                            description=f"Event '{current_event.description[:50]}' occurs at {current_event.timestamp} but is followed by '{next_event.description[:50]}' at earlier time {next_event.timestamp}",
                            affected_event_ids=[current_event.id, next_event.id],
                            severity="MEDIUM",
                            extra_data={
                                "current_timestamp": current_event.timestamp,
                                "next_timestamp": next_event.timestamp
                            },
                            created_at=datetime.utcnow()
                        )
                        db.add(inconsistency)
                        inconsistencies.append(inconsistency)

            # 3. Check for character appearing after death/disappearance
            # Track character states through events
            character_states = {}  # {char_id: "alive"|"dead"|"missing"}

            for event in events:
                for char_id in event.character_ids:
                    # Check event_metadata for death/disappearance
                    if event.event_metadata.get("character_deaths"):
                        if char_id in event.event_metadata["character_deaths"]:
                            character_states[char_id] = "dead"

                    # If character is marked as dead but appears in this event
                    if character_states.get(char_id) == "dead":
                        char_entity = db.query(Entity).filter(Entity.id == char_id).first()
                        inconsistency = TimelineInconsistency(
                            manuscript_id=manuscript_id,
                            inconsistency_type="CHARACTER_RESURRECTION",
                            description=f"{char_entity.name if char_entity else 'Character'} appears in '{event.description[:50]}' after being marked as dead",
                            affected_event_ids=[event.id],
                            severity="HIGH",
                            extra_data={"character_id": char_id},
                            created_at=datetime.utcnow()
                        )
                        db.add(inconsistency)
                        inconsistencies.append(inconsistency)

            # 4. Detect missing transitions (large location jumps without explanation)
            for i in range(len(events) - 1):
                current_event = events[i]
                next_event = events[i + 1]

                # Skip if events don't have locations
                if not current_event.location_id or not next_event.location_id:
                    continue

                # Skip if same location
                if current_event.location_id == next_event.location_id:
                    continue

                # Check if transition is explained in metadata
                if next_event.event_metadata.get("has_transition"):
                    continue  # Transition is explained

                # Check for common characters that need to travel
                common_chars = set(current_event.character_ids) & set(next_event.character_ids)

                if common_chars:
                    curr_loc = db.query(Entity).filter(Entity.id == current_event.location_id).first()
                    next_loc = db.query(Entity).filter(Entity.id == next_event.location_id).first()

                    char_names = []
                    for char_id in list(common_chars)[:2]:  # Limit to 2 names for readability
                        char_entity = db.query(Entity).filter(Entity.id == char_id).first()
                        if char_entity:
                            char_names.append(char_entity.name)

                    inconsistency = TimelineInconsistency(
                        manuscript_id=manuscript_id,
                        inconsistency_type="MISSING_TRANSITION",
                        description=f"{', '.join(char_names)} move(s) from {curr_loc.name if curr_loc else 'unknown'} to {next_loc.name if next_loc else 'unknown'} without transition",
                        affected_event_ids=[current_event.id, next_event.id],
                        severity="MEDIUM",
                        extra_data={
                            "from_location": current_event.location_id,
                            "to_location": next_event.location_id,
                            "characters": list(common_chars)
                        },
                        created_at=datetime.utcnow()
                    )
                    db.add(inconsistency)
                    inconsistencies.append(inconsistency)

            # 5. Detect pacing issues (very short or very long events)
            if len(events) > 0:
                word_counts = [e.event_metadata.get("word_count", 0) for e in events if e.event_metadata.get("word_count")]

                if word_counts:
                    avg_word_count = sum(word_counts) / len(word_counts)

                    for event in events:
                        word_count = event.event_metadata.get("word_count", 0)

                        # Flag events that are too short (less than 20% of average)
                        if word_count > 0 and word_count < avg_word_count * 0.2:
                            inconsistency = TimelineInconsistency(
                                manuscript_id=manuscript_id,
                                inconsistency_type="PACING_ISSUE",
                                description=f"Scene '{event.description[:50]}...' is unusually short ({word_count} words vs avg {int(avg_word_count)})",
                                affected_event_ids=[event.id],
                                severity="LOW",
                                extra_data={
                                    "word_count": word_count,
                                    "average": avg_word_count,
                                    "issue": "too_short"
                                },
                                created_at=datetime.utcnow()
                            )
                            db.add(inconsistency)
                            inconsistencies.append(inconsistency)

                        # Flag events that are too long (more than 300% of average)
                        elif word_count > avg_word_count * 3:
                            inconsistency = TimelineInconsistency(
                                manuscript_id=manuscript_id,
                                inconsistency_type="PACING_ISSUE",
                                description=f"Scene '{event.description[:50]}...' is unusually long ({word_count} words vs avg {int(avg_word_count)})",
                                affected_event_ids=[event.id],
                                severity="LOW",
                                extra_data={
                                    "word_count": word_count,
                                    "average": avg_word_count,
                                    "issue": "too_long"
                                },
                                created_at=datetime.utcnow()
                            )
                            db.add(inconsistency)
                            inconsistencies.append(inconsistency)

            db.commit()

            # Refresh all objects to load their attributes before closing session
            for inc in inconsistencies:
                db.refresh(inc)

            print(f"🔍 Detected {len(inconsistencies)} timeline inconsistencies")
            return inconsistencies
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to detect inconsistencies: {e}")
            raise
        finally:
            db.close()

    def get_inconsistencies(
        self,
        manuscript_id: str,
        severity: Optional[str] = None
    ) -> List[TimelineInconsistency]:
        """Get all timeline inconsistencies for a manuscript"""
        db = SessionLocal()
        try:
            query = db.query(TimelineInconsistency).filter(
                TimelineInconsistency.manuscript_id == manuscript_id
            )

            if severity:
                query = query.filter(TimelineInconsistency.severity == severity)

            inconsistencies = query.order_by(TimelineInconsistency.created_at.desc()).all()
            return inconsistencies
        finally:
            db.close()

    def resolve_inconsistency(self, inconsistency_id: str) -> bool:
        """Mark an inconsistency as resolved"""
        db = SessionLocal()
        try:
            inconsistency = db.query(TimelineInconsistency).filter(
                TimelineInconsistency.id == inconsistency_id
            ).first()

            if not inconsistency:
                return False

            db.delete(inconsistency)
            db.commit()
            print(f"✅ Resolved inconsistency: {inconsistency_id}")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to resolve inconsistency: {e}")
            raise
        finally:
            db.close()

    # ==================== Timeline Statistics ====================

    def get_timeline_stats(self, manuscript_id: str) -> Dict[str, Any]:
        """Get statistics about the timeline"""
        db = SessionLocal()
        try:
            events = self.get_events(manuscript_id)
            inconsistencies = self.get_inconsistencies(manuscript_id)

            # Count event types
            event_type_counts = {}
            for event in events:
                event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

            # Count locations
            locations_used = set()
            for event in events:
                if event.location_id:
                    locations_used.add(event.location_id)

            # Count characters involved
            characters_involved = set()
            for event in events:
                characters_involved.update(event.character_ids)

            # Severity breakdown
            severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for inc in inconsistencies:
                severity_counts[inc.severity] = severity_counts.get(inc.severity, 0) + 1

            return {
                "total_events": len(events),
                "event_types": event_type_counts,
                "locations_used": len(locations_used),
                "characters_involved": len(characters_involved),
                "total_inconsistencies": len(inconsistencies),
                "inconsistency_severity": severity_counts
            }
        finally:
            db.close()


# Singleton instance
timeline_service = TimelineService()
