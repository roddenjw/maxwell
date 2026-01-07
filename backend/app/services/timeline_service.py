"""
Timeline Service - Event tracking and chronology validation

Manages:
- Timeline events (create, read, update, delete)
- Chronological ordering
- Character location tracking across events
- Timeline inconsistency detection
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entity import Entity
from app.models.timeline import (
    CharacterLocation,
    LocationDistance,
    TimelineEvent,
    TimelineInconsistency,
    TravelLeg,
    TravelSpeedProfile,
)


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

    # ==================== Timeline Orchestrator: Travel Configuration ====================

    def get_or_create_travel_profile(self, manuscript_id: str) -> TravelSpeedProfile:
        """Get existing travel speed profile or create default one"""
        db = SessionLocal()
        try:
            profile = db.query(TravelSpeedProfile).filter(
                TravelSpeedProfile.manuscript_id == manuscript_id
            ).first()

            if profile:
                return profile

            # Create default profile
            profile = TravelSpeedProfile(
                manuscript_id=manuscript_id,
                speeds={
                    "walking": 5,
                    "horse": 15,
                    "carriage": 10,
                    "ship": 20,
                    "running": 10,
                    "cart": 8
                },
                default_speed=5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

            print(f"✅ Created default travel speed profile for manuscript {manuscript_id}")
            return profile
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to get/create travel profile: {e}")
            raise
        finally:
            db.close()

    def update_travel_speeds(
        self,
        manuscript_id: str,
        speeds: Dict[str, int],
        default_speed: Optional[int] = None
    ) -> TravelSpeedProfile:
        """Update travel speed profile for a manuscript"""
        db = SessionLocal()
        try:
            profile = self.get_or_create_travel_profile(manuscript_id)

            # Update speeds (merge with existing)
            current_speeds = profile.speeds if isinstance(profile.speeds, dict) else {}
            current_speeds.update(speeds)
            profile.speeds = current_speeds

            if default_speed is not None:
                profile.default_speed = default_speed
            profile.updated_at = datetime.utcnow()

            db.add(profile)
            db.commit()
            db.refresh(profile)

            print(f"✅ Updated travel speeds for manuscript {manuscript_id}")
            return profile
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to update travel speeds: {e}")
            raise
        finally:
            db.close()

    def set_location_distance(
        self,
        manuscript_id: str,
        location_a_id: str,
        location_b_id: str,
        distance_km: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LocationDistance:
        """Set distance between two locations (bidirectional)"""
        db = SessionLocal()
        try:
            # Normalize order (always store smaller ID first)
            loc_a, loc_b = sorted([location_a_id, location_b_id])

            # Check if distance already exists
            existing = db.query(LocationDistance).filter(
                and_(
                    LocationDistance.manuscript_id == manuscript_id,
                    LocationDistance.location_a_id == loc_a,
                    LocationDistance.location_b_id == loc_b
                )
            ).first()

            if existing:
                existing.distance_km = distance_km
                if metadata:
                    existing.distance_metadata = metadata
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing

            # Create new distance entry
            distance = LocationDistance(
                manuscript_id=manuscript_id,
                location_a_id=loc_a,
                location_b_id=loc_b,
                distance_km=distance_km,
                distance_metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(distance)
            db.commit()
            db.refresh(distance)

            print(f"✅ Set distance between locations: {distance_km}km")
            return distance
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to set location distance: {e}")
            raise
        finally:
            db.close()

    def get_location_distance(
        self,
        manuscript_id: str,
        location_a_id: str,
        location_b_id: str
    ) -> Optional[int]:
        """Get distance between two locations (returns None if not defined)"""
        db = SessionLocal()
        try:
            # Normalize order
            loc_a, loc_b = sorted([location_a_id, location_b_id])

            distance = db.query(LocationDistance).filter(
                and_(
                    LocationDistance.manuscript_id == manuscript_id,
                    LocationDistance.location_a_id == loc_a,
                    LocationDistance.location_b_id == loc_b
                )
            ).first()

            return distance.distance_km if distance else None
        finally:
            db.close()

    def create_travel_leg(
        self,
        manuscript_id: str,
        character_id: str,
        from_location_id: str,
        to_location_id: str,
        departure_event_id: str,
        arrival_event_id: str,
        travel_mode: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TravelLeg:
        """Create a travel leg for a character (automatically calculates feasibility)"""
        db = SessionLocal()
        try:
            # Get distance
            distance_km = self.get_location_distance(manuscript_id, from_location_id, to_location_id)

            # Get speed
            profile = self.get_or_create_travel_profile(manuscript_id)
            speed_kmh = profile.speeds.get(travel_mode, profile.default_speed) if isinstance(profile.speeds, dict) else profile.default_speed

            # Calculate required hours
            required_hours = None
            if distance_km:
                required_hours = int((distance_km / speed_kmh))

            # Get events to calculate available time
            dep_event = self.get_event(departure_event_id)
            arr_event = self.get_event(arrival_event_id)

            available_hours = None
            is_feasible = 1
            if dep_event and arr_event:
                # Calculate time difference based on order_index (simple approach)
                # Each order_index unit = 1 day = 24 hours
                available_hours = (arr_event.order_index - dep_event.order_index) * 24

                if required_hours and available_hours:
                    is_feasible = 1 if available_hours >= required_hours else 0

            leg = TravelLeg(
                manuscript_id=manuscript_id,
                character_id=character_id,
                from_location_id=from_location_id,
                to_location_id=to_location_id,
                departure_event_id=departure_event_id,
                arrival_event_id=arrival_event_id,
                travel_mode=travel_mode,
                distance_km=distance_km,
                speed_kmh=speed_kmh,
                required_hours=required_hours,
                available_hours=available_hours,
                is_feasible=is_feasible,
                leg_metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(leg)
            db.commit()
            db.refresh(leg)

            print(f"✅ Created travel leg: {travel_mode} from {from_location_id[:8]} to {to_location_id[:8]}")
            return leg
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to create travel leg: {e}")
            raise
        finally:
            db.close()

    def get_travel_legs(self, manuscript_id: str) -> List[TravelLeg]:
        """Get all travel legs for a manuscript"""
        db = SessionLocal()
        try:
            legs = db.query(TravelLeg).filter(
                TravelLeg.manuscript_id == manuscript_id
            ).all()
            return legs
        finally:
            db.close()

    # ==================== Timeline Orchestrator: Validators ====================

    def _detect_impossible_travel(
        self,
        manuscript_id: str,
        db: Session
    ) -> List[TimelineInconsistency]:
        """
        VALIDATOR 1: Impossible Travel Detector

        Detects when characters must travel distances that are impossible
        given the available time and travel speeds.
        """
        inconsistencies = []
        events = self.get_events(manuscript_id)
        profile = self.get_or_create_travel_profile(manuscript_id)

        # Sort events by order_index
        events_sorted = sorted(events, key=lambda e: e.order_index)

        for i in range(len(events_sorted) - 1):
            curr_event = events_sorted[i]
            next_event = events_sorted[i + 1]

            # Skip if no location change
            if not curr_event.location_id or not next_event.location_id:
                continue
            if curr_event.location_id == next_event.location_id:
                continue

            # Find common characters who must travel
            common_chars = set(curr_event.character_ids) & set(next_event.character_ids)
            if not common_chars:
                continue

            # Get distance
            distance = self.get_location_distance(
                manuscript_id,
                curr_event.location_id,
                next_event.location_id
            )

            if not distance:
                # No distance defined, skip validation
                continue

            # Calculate time available (1 order_index = 1 day = 24 hours)
            available_hours = (next_event.order_index - curr_event.order_index) * 24

            # Assume default travel mode (walking)
            speed = profile.default_speed
            required_hours = distance / speed

            if required_hours > available_hours:
                # IMPOSSIBLE TRAVEL DETECTED
                curr_loc = db.query(Entity).filter(Entity.id == curr_event.location_id).first()
                next_loc = db.query(Entity).filter(Entity.id == next_event.location_id).first()

                char_names = []
                for char_id in list(common_chars)[:2]:
                    char = db.query(Entity).filter(Entity.id == char_id).first()
                    if char:
                        char_names.append(char.name)

                inconsistency = TimelineInconsistency(
                    manuscript_id=manuscript_id,
                    inconsistency_type="IMPOSSIBLE_TRAVEL",
                    description=f"{', '.join(char_names)} must travel {distance}km from {curr_loc.name if curr_loc else 'unknown'} to {next_loc.name if next_loc else 'unknown'} in {available_hours}h (requires {int(required_hours)}h at {speed}km/h)",
                    severity="HIGH",
                    affected_event_ids=[curr_event.id, next_event.id],
                    extra_data={
                        "distance_km": distance,
                        "required_hours": int(required_hours),
                        "available_hours": available_hours,
                        "speed_kmh": speed,
                        "characters": list(common_chars)
                    },
                    suggestion="""Consider these options:
1. Add intermediate events showing the journey (builds tension, shows world)
2. Increase the time between events to allow realistic travel
3. Introduce faster travel method (magic, portals, mounts) and establish it earlier
4. Reconsider if all these characters need to be present at both locations""",
                    teaching_point="""Readers subconsciously track time and distance. When characters arrive "too fast," it breaks immersion and signals careless plotting. Realistic travel pacing:
- Creates anticipation and tension
- Allows for character development during journeys
- Makes the world feel larger and more believable
- Provides natural breaks for subplots""",
                    is_resolved=0,
                    created_at=datetime.utcnow()
                )
                inconsistencies.append(inconsistency)

        return inconsistencies

    def _detect_dependency_violations(
        self,
        manuscript_id: str,
        db: Session
    ) -> List[TimelineInconsistency]:
        """
        VALIDATOR 2: Dependency Violation Checker

        Ensures prerequisites occur before dependent events (causality).
        """
        inconsistencies = []
        events = self.get_events(manuscript_id)
        event_map = {e.id: e for e in events}

        for event in events:
            if not event.prerequisite_ids:
                continue

            for prereq_id in event.prerequisite_ids:
                prereq = event_map.get(prereq_id)
                if not prereq:
                    # Prerequisite event doesn't exist
                    inconsistencies.append(TimelineInconsistency(
                        manuscript_id=manuscript_id,
                        inconsistency_type="DEPENDENCY_VIOLATION",
                        description=f"Event '{event.description[:50]}' depends on non-existent event {prereq_id}",
                        severity="HIGH",
                        affected_event_ids=[event.id],
                        extra_data={"missing_prerequisite": prereq_id},
                        suggestion="""Consider these options:
1. Remove the dependency if the prerequisite is no longer relevant
2. Create the missing prerequisite event
3. Verify the prerequisite ID is correct (may be a typo)""",
                        teaching_point="""Missing dependencies indicate incomplete story logic. Readers need to see causes before effects to maintain narrative coherence.""",
                        is_resolved=0,
                        created_at=datetime.utcnow()
                    ))
                    continue

                if prereq.order_index >= event.order_index:
                    # Prerequisite occurs AFTER or AT SAME TIME as dependent event
                    inconsistencies.append(TimelineInconsistency(
                        manuscript_id=manuscript_id,
                        inconsistency_type="DEPENDENCY_VIOLATION",
                        description=f"Event '{event.description[:50]}' (order {event.order_index}) depends on '{prereq.description[:50]}' (order {prereq.order_index}) which occurs later",
                        severity="HIGH",
                        affected_event_ids=[event.id, prereq.id],
                        extra_data={
                            "dependent_event": event.id,
                            "prerequisite_event": prereq.id,
                            "order_violation": prereq.order_index - event.order_index
                        },
                        suggestion="""Consider these options:
1. Reorder events so the prerequisite occurs first
2. Remove the dependency if it's not actually required
3. Use flashback/reveal structure if you want effect before cause (but signal this clearly)
4. Split the dependent event into setup (after prereq) and payoff""",
                        teaching_point="""Causality is fundamental to storytelling. When effects precede causes, readers feel confused or cheated. Even in non-linear narratives:
- The reader must understand the causal chain eventually
- Deliberate violations (flashbacks) should be clearly signaled
- Mystery works by hiding causes, not reversing causality
- Payoffs feel earned only when setup came first""",
                        is_resolved=0,
                        created_at=datetime.utcnow()
                    ))

        return inconsistencies

    def _detect_character_presence_issues(
        self,
        manuscript_id: str,
        db: Session
    ) -> List[TimelineInconsistency]:
        """
        VALIDATOR 3: Character Presence Analyzer

        Detects under-utilized characters (Chekhov's gun violation).
        """
        inconsistencies = []
        events = self.get_events(manuscript_id)

        # Get all characters in manuscript
        all_chars = db.query(Entity).filter(
            and_(
                Entity.manuscript_id == manuscript_id,
                Entity.type == "CHARACTER"
            )
        ).all()

        # Count appearances
        appearance_count = {}
        appearance_events = {}
        for char in all_chars:
            appearance_count[char.id] = 0
            appearance_events[char.id] = []

        for event in events:
            for char_id in event.character_ids:
                if char_id in appearance_count:
                    appearance_count[char_id] += 1
                    appearance_events[char_id].append(event.id)

        # Detect issues
        for char in all_chars:
            count = appearance_count[char.id]

            if count == 0:
                # Character never appears
                inconsistencies.append(TimelineInconsistency(
                    manuscript_id=manuscript_id,
                    inconsistency_type="CHARACTER_NEVER_APPEARS",
                    description=f"Character '{char.name}' is defined but never appears in any timeline event",
                    severity="LOW",
                    affected_event_ids=[],
                    extra_data={"character_id": char.id},
                    suggestion="""Consider these options:
1. Delete the character if they're not needed (reduces reader confusion)
2. Add them to relevant scenes where they should logically be present
3. If they're mentioned but not present, add events showing them
4. Keep them if they're intentionally off-screen (but note this)""",
                    teaching_point="""Unused characters clutter the story and waste reader mental bandwidth. Readers invest attention in every named character, expecting them to matter. If a character doesn't appear in events:
- They may be unnecessary to the plot
- You may have forgotten to include them in scenes where they should be
- Consider whether they could be merged with another character""",
                    is_resolved=0,
                    created_at=datetime.utcnow()
                ))

            elif count == 1:
                # Character appears only once (Chekhov's gun violation)
                event = db.query(TimelineEvent).filter(
                    TimelineEvent.id == appearance_events[char.id][0]
                ).first()

                inconsistencies.append(TimelineInconsistency(
                    manuscript_id=manuscript_id,
                    inconsistency_type="ONE_SCENE_WONDER",
                    description=f"Character '{char.name}' appears in only one event: '{event.description[:50] if event else 'unknown'}'",
                    severity="MEDIUM",
                    affected_event_ids=appearance_events[char.id],
                    extra_data={
                        "character_id": char.id,
                        "appearance_count": 1
                    },
                    suggestion="""Consider these options:
1. Give them a second appearance to create an arc (setup + payoff)
2. Merge them with another minor character to strengthen both
3. Expand their role if they're interesting and worth developing
4. Cut them if their function can be served by existing characters""",
                    teaching_point="""Chekhov's gun principle: every element should serve the story. One-scene characters feel like false starts because:
- Readers invest attention in new characters
- Single appearances suggest incomplete arcs
- They may indicate earlier drafts where the character had more to do
- Exception: deliberate one-scene roles (messenger, guard) should be unnamed extras""",
                    is_resolved=0,
                    created_at=datetime.utcnow()
                ))

        return inconsistencies

    def _detect_timing_gaps(
        self,
        manuscript_id: str,
        db: Session
    ) -> List[TimelineInconsistency]:
        """
        VALIDATOR 4: Timing Gap Detector

        Detects large time gaps between consecutive events.
        """
        inconsistencies = []
        events = self.get_events(manuscript_id)

        # Sort by order_index
        events_sorted = sorted(events, key=lambda e: e.order_index)

        # Define gap threshold (in order_index units, assuming 1 unit = 1 day)
        GAP_THRESHOLD = 30

        for i in range(len(events_sorted) - 1):
            curr = events_sorted[i]
            next = events_sorted[i + 1]

            gap = next.order_index - curr.order_index

            if gap > GAP_THRESHOLD:
                inconsistencies.append(TimelineInconsistency(
                    manuscript_id=manuscript_id,
                    inconsistency_type="TIMING_GAP",
                    description=f"Large time gap ({gap} days) between '{curr.description[:40]}' and '{next.description[:40]}'",
                    severity="MEDIUM",
                    affected_event_ids=[curr.id, next.id],
                    extra_data={
                        "gap_days": gap,
                        "threshold": GAP_THRESHOLD
                    },
                    suggestion="""Consider these options:
1. Add a summary event or montage showing what happened during the gap
2. Show characters acknowledging the time passage ("Three weeks later...")
3. Demonstrate consequences of the time gap (relationships changed, world evolved)
4. If the gap is intentional, add narrative importance to events to justify the skip""",
                    teaching_point="""Time gaps affect pacing and reader immersion. When significant time passes:
- Readers notice if characters/relationships haven't evolved proportionally
- World state should reflect the passage of time
- Unacknowledged gaps feel like missing scenes
- Deliberate time skips work best with:
  * Clear signposting ("A month passed...")
  * Visible consequences (seasons changed, conflict evolved)
  * Character reflection on what happened""",
                    is_resolved=0,
                    created_at=datetime.utcnow()
                ))

        return inconsistencies

    def _detect_temporal_paradoxes(
        self,
        manuscript_id: str,
        db: Session
    ) -> List[TimelineInconsistency]:
        """
        VALIDATOR 5: Temporal Paradox Detector

        Uses DFS to detect circular dependencies in prerequisite chain.
        """
        inconsistencies = []
        events = self.get_events(manuscript_id)
        event_map = {e.id: e for e in events}

        # Build dependency graph from prerequisite_ids
        graph = {e.id: e.prerequisite_ids for e in events}

        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {e.id: WHITE for e in events}
        path = []

        def dfs(event_id):
            """DFS to detect cycles"""
            if color[event_id] == BLACK:
                return None  # Already processed
            if color[event_id] == GRAY:
                # Cycle detected! Return cycle path
                cycle_start = path.index(event_id)
                return path[cycle_start:] + [event_id]

            color[event_id] = GRAY
            path.append(event_id)

            for prereq_id in graph.get(event_id, []):
                if prereq_id not in event_map:
                    continue  # Skip missing prerequisites

                cycle = dfs(prereq_id)
                if cycle:
                    return cycle

            path.pop()
            color[event_id] = BLACK
            return None

        # Check all events for cycles
        for event_id in graph:
            if color[event_id] == WHITE:
                cycle = dfs(event_id)
                if cycle:
                    # Cycle detected!
                    cycle_desc = []
                    for eid in cycle:
                        evt = event_map.get(eid)
                        if evt:
                            cycle_desc.append(f"'{evt.description[:30]}'")

                    inconsistencies.append(TimelineInconsistency(
                        manuscript_id=manuscript_id,
                        inconsistency_type="TEMPORAL_PARADOX",
                        description=f"Circular dependency detected: {' → '.join(cycle_desc)}",
                        severity="HIGH",
                        affected_event_ids=cycle,
                        extra_data={"cycle": cycle},
                        suggestion="""Consider these options:
1. Remove one dependency in the cycle to break the loop
2. Reorder events to eliminate the circular logic
3. Split one event into two parts to break the cycle
4. Verify dependencies are correctly specified (may be data entry error)""",
                        teaching_point="""Circular dependencies are logically impossible and confuse readers. In storytelling:
- Cause must precede effect (even in non-linear narratives)
- Circular logic signals plot holes or unclear thinking
- Time travel stories handle this with parallel timelines or paradox resolution
- Mystery stories can hide causes, but the revelation must make logical sense""",
                        is_resolved=0,
                        created_at=datetime.utcnow()
                    ))

                    # Only report first cycle to avoid overwhelming user
                    break

        return inconsistencies

    def validate_timeline_orchestrator(
        self,
        manuscript_id: str
    ) -> List[TimelineInconsistency]:
        """
        MAIN ORCHESTRATOR: Run all 5 validators + existing validators

        Returns combined list of all issues detected and saves them to database.
        """
        db = SessionLocal()
        try:
            print(f"🔍 Running Timeline Orchestrator validation for manuscript {manuscript_id}...")

            all_inconsistencies = []

            # Run all 5 new validators
            print("  → Checking impossible travel...")
            all_inconsistencies.extend(self._detect_impossible_travel(manuscript_id, db))

            print("  → Checking dependency violations...")
            all_inconsistencies.extend(self._detect_dependency_violations(manuscript_id, db))

            print("  → Checking character presence...")
            all_inconsistencies.extend(self._detect_character_presence_issues(manuscript_id, db))

            print("  → Checking timing gaps...")
            all_inconsistencies.extend(self._detect_timing_gaps(manuscript_id, db))

            print("  → Checking temporal paradoxes...")
            all_inconsistencies.extend(self._detect_temporal_paradoxes(manuscript_id, db))

            # Also run existing validators (location conflicts, etc.)
            print("  → Running existing validators...")
            existing = self.detect_inconsistencies(manuscript_id)
            all_inconsistencies.extend(existing)

            # Save all to database
            for inc in all_inconsistencies:
                db.add(inc)
            db.commit()

            # Refresh all objects
            for inc in all_inconsistencies:
                db.refresh(inc)

            print(f"✅ Timeline Orchestrator validation complete. Found {len(all_inconsistencies)} issues.")
            return all_inconsistencies

        except Exception as e:
            db.rollback()
            print(f"❌ Timeline Orchestrator validation failed: {e}")
            raise
        finally:
            db.close()

    def resolve_inconsistency_with_notes(
        self,
        inconsistency_id: str,
        resolution_notes: str
    ) -> bool:
        """Mark inconsistency as resolved with notes on how it was addressed"""
        db = SessionLocal()
        try:
            inc = db.query(TimelineInconsistency).filter(
                TimelineInconsistency.id == inconsistency_id
            ).first()

            if not inc:
                return False

            inc.is_resolved = 1
            inc.resolved_at = datetime.utcnow()
            inc.resolution_notes = resolution_notes

            db.commit()
            print(f"✅ Resolved inconsistency: {inconsistency_id}")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to resolve inconsistency: {e}")
            raise
        finally:
            db.close()

    def get_comprehensive_timeline_data(
        self,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """
        Get ALL timeline data in one optimized query

        Used by frontend to load orchestrator view efficiently.
        """
        db = SessionLocal()
        try:
            # Query all data in same session to avoid detached instance issues
            events = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == manuscript_id
            ).order_by(TimelineEvent.order_index).all()

            inconsistencies = db.query(TimelineInconsistency).filter(
                TimelineInconsistency.manuscript_id == manuscript_id
            ).all()

            char_locations = db.query(CharacterLocation).filter(
                CharacterLocation.manuscript_id == manuscript_id
            ).all()

            travel_legs = db.query(TravelLeg).filter(
                TravelLeg.manuscript_id == manuscript_id
            ).all()

            travel_profile = self.get_or_create_travel_profile(manuscript_id)

            location_distances = db.query(LocationDistance).filter(
                LocationDistance.manuscript_id == manuscript_id
            ).all()

            stats = self.get_timeline_stats(manuscript_id)

            # Eagerly access all JSON fields while session is still open
            # This prevents lazy loading issues when session closes
            for event in events:
                _ = event.character_ids
                _ = event.event_metadata
                _ = event.prerequisite_ids

            for inc in inconsistencies:
                _ = inc.affected_event_ids
                _ = inc.extra_data

            for leg in travel_legs:
                _ = leg.leg_metadata

            for ld in location_distances:
                _ = ld.distance_metadata

            print(f"📚 Retrieved comprehensive data: {len(events)} events, {len(inconsistencies)} inconsistencies")

            return {
                "events": events,
                "inconsistencies": inconsistencies,
                "character_locations": char_locations,
                "travel_legs": travel_legs,
                "travel_profile": travel_profile,
                "location_distances": location_distances,
                "stats": stats
            }
        finally:
            db.close()


# Singleton instance
timeline_service = TimelineService()
