"""
Entity State Service for tracking entity states at different narrative points.

Enables tracking how characters, locations, or other entities change throughout
the story across multiple manuscripts in a series/world.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.entity_state import EntityTimelineState
from app.models.entity import Entity


class EntityStateService:
    """Service for managing entity timeline states"""

    def create_state_snapshot(
        self,
        entity_id: str,
        state_data: Dict[str, Any],
        manuscript_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        timeline_event_id: Optional[str] = None,
        order_index: int = 0,
        narrative_timestamp: Optional[str] = None,
        label: Optional[str] = None,
        is_canonical: bool = True
    ) -> EntityTimelineState:
        """
        Create a new state snapshot for an entity.

        Args:
            entity_id: ID of the entity
            state_data: Flexible state data (age, status, location, etc.)
            manuscript_id: Optional manuscript anchor
            chapter_id: Optional chapter anchor
            timeline_event_id: Optional timeline event anchor
            order_index: Order within the same scope
            narrative_timestamp: In-story timestamp (e.g., "Day 5", "Year 1052")
            label: User-friendly label (e.g., "End of Book 1")
            is_canonical: Whether this is the canonical state

        Returns:
            Created EntityTimelineState
        """
        db = SessionLocal()
        try:
            state = EntityTimelineState(
                entity_id=entity_id,
                state_data=state_data,
                manuscript_id=manuscript_id,
                chapter_id=chapter_id,
                timeline_event_id=timeline_event_id,
                order_index=order_index,
                narrative_timestamp=narrative_timestamp,
                label=label,
                is_canonical=1 if is_canonical else 0
            )
            db.add(state)
            db.commit()
            db.refresh(state)
            db.expunge(state)
            return state
        finally:
            db.close()

    def get_entity_states(
        self,
        entity_id: str,
        manuscript_id: Optional[str] = None,
        canonical_only: bool = False
    ) -> List[EntityTimelineState]:
        """
        Get all state snapshots for an entity.

        Args:
            entity_id: ID of the entity
            manuscript_id: Optional filter by manuscript
            canonical_only: Only return canonical states

        Returns:
            List of EntityTimelineState ordered by order_index
        """
        db = SessionLocal()
        try:
            query = db.query(EntityTimelineState).filter(
                EntityTimelineState.entity_id == entity_id
            )

            if manuscript_id:
                query = query.filter(EntityTimelineState.manuscript_id == manuscript_id)

            if canonical_only:
                query = query.filter(EntityTimelineState.is_canonical == 1)

            states = query.order_by(
                EntityTimelineState.manuscript_id,
                EntityTimelineState.order_index
            ).all()

            result = []
            for state in states:
                db.expunge(state)
                result.append(state)

            return result
        finally:
            db.close()

    def get_state_by_id(self, state_id: str) -> Optional[EntityTimelineState]:
        """
        Get a specific state snapshot by ID.

        Args:
            state_id: State snapshot ID

        Returns:
            EntityTimelineState or None
        """
        db = SessionLocal()
        try:
            state = db.query(EntityTimelineState).filter(
                EntityTimelineState.id == state_id
            ).first()
            if state:
                db.expunge(state)
            return state
        finally:
            db.close()

    def get_state_at_point(
        self,
        entity_id: str,
        manuscript_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        timeline_event_id: Optional[str] = None
    ) -> Optional[EntityTimelineState]:
        """
        Get the effective entity state at a specific narrative point.

        Returns the most recent state snapshot at or before the specified point.
        Priority: timeline_event_id > chapter_id > manuscript_id

        Args:
            entity_id: ID of the entity
            manuscript_id: Manuscript to search in
            chapter_id: Chapter to find state at
            timeline_event_id: Timeline event to find state at

        Returns:
            Most relevant EntityTimelineState or None
        """
        db = SessionLocal()
        try:
            # Build query based on specificity
            query = db.query(EntityTimelineState).filter(
                EntityTimelineState.entity_id == entity_id,
                EntityTimelineState.is_canonical == 1
            )

            if timeline_event_id:
                # First try exact match
                state = query.filter(
                    EntityTimelineState.timeline_event_id == timeline_event_id
                ).first()
                if state:
                    db.expunge(state)
                    return state

            if chapter_id:
                # Try chapter match
                state = query.filter(
                    EntityTimelineState.chapter_id == chapter_id
                ).first()
                if state:
                    db.expunge(state)
                    return state

            if manuscript_id:
                # Get latest state for manuscript
                state = query.filter(
                    EntityTimelineState.manuscript_id == manuscript_id
                ).order_by(EntityTimelineState.order_index.desc()).first()
                if state:
                    db.expunge(state)
                    return state

            # Fallback: get most recent state overall
            state = query.order_by(EntityTimelineState.order_index.desc()).first()
            if state:
                db.expunge(state)
            return state
        finally:
            db.close()

    def update_state(
        self,
        state_id: str,
        state_data: Optional[Dict[str, Any]] = None,
        narrative_timestamp: Optional[str] = None,
        label: Optional[str] = None,
        is_canonical: Optional[bool] = None,
        order_index: Optional[int] = None
    ) -> Optional[EntityTimelineState]:
        """
        Update a state snapshot.

        Args:
            state_id: State snapshot ID
            state_data: New state data (replaces entirely if provided)
            narrative_timestamp: New timestamp
            label: New label
            is_canonical: New canonical status
            order_index: New order index

        Returns:
            Updated EntityTimelineState or None
        """
        db = SessionLocal()
        try:
            state = db.query(EntityTimelineState).filter(
                EntityTimelineState.id == state_id
            ).first()

            if not state:
                return None

            if state_data is not None:
                state.state_data = state_data
            if narrative_timestamp is not None:
                state.narrative_timestamp = narrative_timestamp
            if label is not None:
                state.label = label
            if is_canonical is not None:
                state.is_canonical = 1 if is_canonical else 0
            if order_index is not None:
                state.order_index = order_index

            state.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(state)
            db.expunge(state)
            return state
        finally:
            db.close()

    def delete_state(self, state_id: str) -> bool:
        """
        Delete a state snapshot.

        Args:
            state_id: State snapshot ID

        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            state = db.query(EntityTimelineState).filter(
                EntityTimelineState.id == state_id
            ).first()

            if not state:
                return False

            db.delete(state)
            db.commit()
            return True
        finally:
            db.close()

    def get_state_diff(
        self,
        entity_id: str,
        from_state_id: str,
        to_state_id: str
    ) -> Dict[str, Any]:
        """
        Compare two state snapshots and return differences.

        Args:
            entity_id: Entity ID (for validation)
            from_state_id: Starting state ID
            to_state_id: Ending state ID

        Returns:
            Dict with added, removed, and changed fields
        """
        db = SessionLocal()
        try:
            from_state = db.query(EntityTimelineState).filter(
                EntityTimelineState.id == from_state_id,
                EntityTimelineState.entity_id == entity_id
            ).first()

            to_state = db.query(EntityTimelineState).filter(
                EntityTimelineState.id == to_state_id,
                EntityTimelineState.entity_id == entity_id
            ).first()

            if not from_state or not to_state:
                return {"error": "One or both states not found"}

            from_data = from_state.state_data or {}
            to_data = to_state.state_data or {}

            diff = {
                "from_state": {
                    "id": from_state.id,
                    "label": from_state.label,
                    "narrative_timestamp": from_state.narrative_timestamp
                },
                "to_state": {
                    "id": to_state.id,
                    "label": to_state.label,
                    "narrative_timestamp": to_state.narrative_timestamp
                },
                "added": {},
                "removed": {},
                "changed": {}
            }

            # Find added and changed fields
            for key, value in to_data.items():
                if key not in from_data:
                    diff["added"][key] = value
                elif from_data[key] != value:
                    diff["changed"][key] = {
                        "from": from_data[key],
                        "to": value
                    }

            # Find removed fields
            for key, value in from_data.items():
                if key not in to_data:
                    diff["removed"][key] = value

            return diff
        finally:
            db.close()

    def get_character_journey(
        self,
        character_id: str,
        manuscript_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a character's journey through the narrative.

        Returns chronological state changes with context, useful for
        visualizing character arcs and development.

        Args:
            character_id: Character entity ID
            manuscript_id: Optional filter by manuscript

        Returns:
            List of journey points with state changes
        """
        db = SessionLocal()
        try:
            # Get entity to verify it's a character
            entity = db.query(Entity).filter(Entity.id == character_id).first()
            if not entity:
                return []

            # Get all states for the character
            query = db.query(EntityTimelineState).filter(
                EntityTimelineState.entity_id == character_id,
                EntityTimelineState.is_canonical == 1
            )

            if manuscript_id:
                query = query.filter(EntityTimelineState.manuscript_id == manuscript_id)

            states = query.order_by(
                EntityTimelineState.manuscript_id,
                EntityTimelineState.order_index
            ).all()

            journey = []
            prev_state = None

            for state in states:
                point = {
                    "state_id": state.id,
                    "manuscript_id": state.manuscript_id,
                    "chapter_id": state.chapter_id,
                    "timeline_event_id": state.timeline_event_id,
                    "order_index": state.order_index,
                    "narrative_timestamp": state.narrative_timestamp,
                    "label": state.label,
                    "state_data": state.state_data,
                    "changes": None
                }

                # Calculate changes from previous state
                if prev_state:
                    prev_data = prev_state.state_data or {}
                    curr_data = state.state_data or {}
                    changes = {}

                    for key, value in curr_data.items():
                        if key not in prev_data:
                            changes[key] = {"type": "added", "value": value}
                        elif prev_data[key] != value:
                            changes[key] = {
                                "type": "changed",
                                "from": prev_data[key],
                                "to": value
                            }

                    for key, value in prev_data.items():
                        if key not in curr_data:
                            changes[key] = {"type": "removed", "value": value}

                    if changes:
                        point["changes"] = changes

                journey.append(point)
                prev_state = state

            return journey
        finally:
            db.close()

    def bulk_create_states(
        self,
        entity_id: str,
        states: List[Dict[str, Any]]
    ) -> List[EntityTimelineState]:
        """
        Create multiple state snapshots at once.

        Args:
            entity_id: Entity ID
            states: List of state definitions

        Returns:
            List of created states
        """
        db = SessionLocal()
        try:
            created = []
            for i, state_def in enumerate(states):
                state = EntityTimelineState(
                    entity_id=entity_id,
                    state_data=state_def.get("state_data", {}),
                    manuscript_id=state_def.get("manuscript_id"),
                    chapter_id=state_def.get("chapter_id"),
                    timeline_event_id=state_def.get("timeline_event_id"),
                    order_index=state_def.get("order_index", i),
                    narrative_timestamp=state_def.get("narrative_timestamp"),
                    label=state_def.get("label"),
                    is_canonical=1 if state_def.get("is_canonical", True) else 0
                )
                db.add(state)
                created.append(state)

            db.commit()

            result = []
            for state in created:
                db.refresh(state)
                db.expunge(state)
                result.append(state)

            return result
        finally:
            db.close()


# Global instance
entity_state_service = EntityStateService()
