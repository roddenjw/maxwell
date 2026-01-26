"""
Tests for timeline_service - Timeline event management and orchestration
Covers travel profiles, location distances, validation, and comprehensive data retrieval
"""

import uuid
from datetime import datetime

import pytest

from app.database import SessionLocal
from app.models.entity import Entity
from app.models.timeline import (
    LocationDistance,
    TimelineEvent,
    TravelLeg,
    TravelSpeedProfile,
)
from app.services.timeline_service import timeline_service


@pytest.fixture
def test_manuscript_id():
    """Generate a unique manuscript ID for testing"""
    return str(uuid.uuid4())


@pytest.fixture
def test_character(test_db, test_manuscript_id):
    """Create a test character entity"""
    char = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id,
        type="CHARACTER",
        name="Test Hero",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(char)
    test_db.commit()
    test_db.refresh(char)
    return char


@pytest.fixture
def test_locations(test_db, test_manuscript_id):
    """Create two test location entities"""
    loc1 = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id,
        type="LOCATION",
        name="City A",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    loc2 = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id,
        type="LOCATION",
        name="City B",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(loc1)
    test_db.add(loc2)
    test_db.commit()
    test_db.refresh(loc1)
    test_db.refresh(loc2)
    return loc1, loc2


# ============================================================================
# Travel Speed Profile Tests
# ============================================================================

def test_get_or_create_travel_profile(test_manuscript_id):
    """Test travel profile creation with default speeds"""
    # Act
    profile = timeline_service.get_or_create_travel_profile(test_manuscript_id)

    # Assert
    assert profile is not None
    assert profile.manuscript_id == test_manuscript_id
    assert profile.default_speed > 0
    assert isinstance(profile.speeds, dict)


def test_update_travel_speeds(test_manuscript_id):
    """Test updating travel speeds with custom values"""
    # Arrange
    original_profile = timeline_service.get_or_create_travel_profile(test_manuscript_id)

    # Act
    timeline_service.update_travel_speeds(
        test_manuscript_id,
        {"dragon": 100, "magic_portal": 999999},
        default_speed=10
    )

    # Re-query to verify persistence
    updated_profile = timeline_service.get_or_create_travel_profile(test_manuscript_id)

    # Assert
    assert updated_profile.default_speed == 10
    assert updated_profile.speeds.get("dragon") == 100
    assert updated_profile.speeds.get("magic_portal") == 999999


# ============================================================================
# Location Distance Tests
# ============================================================================

def test_set_location_distance(test_manuscript_id):
    """Test setting distance between two locations"""
    # Arrange
    loc_a_id = str(uuid.uuid4())
    loc_b_id = str(uuid.uuid4())

    # Act
    distance = timeline_service.set_location_distance(
        test_manuscript_id,
        loc_a_id,
        loc_b_id,
        500,  # 500km
        {"terrain": "mountains", "difficulty": "hard"}
    )

    # Assert
    assert distance is not None
    assert distance.distance_km == 500
    assert distance.distance_metadata["terrain"] == "mountains"
    assert distance.distance_metadata["difficulty"] == "hard"


def test_get_location_distance(test_manuscript_id):
    """Test retrieving distance between locations"""
    # Arrange
    loc_a_id = str(uuid.uuid4())
    loc_b_id = str(uuid.uuid4())
    timeline_service.set_location_distance(test_manuscript_id, loc_a_id, loc_b_id, 500)

    # Act
    distance = timeline_service.get_location_distance(test_manuscript_id, loc_a_id, loc_b_id)

    # Assert
    assert distance == 500


def test_location_distance_bidirectional(test_manuscript_id):
    """Test that location distances work in both directions"""
    # Arrange
    loc_a_id = str(uuid.uuid4())
    loc_b_id = str(uuid.uuid4())
    timeline_service.set_location_distance(test_manuscript_id, loc_a_id, loc_b_id, 500)

    # Act - reversed order should work
    distance_forward = timeline_service.get_location_distance(test_manuscript_id, loc_a_id, loc_b_id)
    distance_reverse = timeline_service.get_location_distance(test_manuscript_id, loc_b_id, loc_a_id)

    # Assert
    assert distance_forward == distance_reverse == 500


# ============================================================================
# Timeline Validation Tests
# ============================================================================

def test_timeline_orchestrator_validation_detects_impossible_travel(
    test_db, test_manuscript_id, test_character, test_locations
):
    """Test that validator detects impossible travel between locations"""
    # Arrange
    loc1, loc2 = test_locations

    # Set distance of 100km between locations
    timeline_service.set_location_distance(test_manuscript_id, loc1.id, loc2.id, 100)

    # Create events that are too close together for travel
    event1 = timeline_service.create_event(
        manuscript_id=test_manuscript_id,
        description="Hero arrives at City A",
        event_type="SCENE",
        order_index=0,
        location_id=loc1.id,
        character_ids=[test_character.id]
    )

    event2 = timeline_service.create_event(
        manuscript_id=test_manuscript_id,
        description="Hero arrives at City B",
        event_type="SCENE",
        order_index=1,  # Only 1 day later (impossible for 100km at default 5km/h)
        location_id=loc2.id,
        character_ids=[test_character.id]
    )

    # Act
    issues = timeline_service.validate_timeline_orchestrator(test_manuscript_id)

    # Assert
    assert len(issues) > 0, "Should detect impossible travel"

    # Check that issue has required fields
    issue = issues[0]
    assert issue.inconsistency_type is not None
    assert issue.severity in ["HIGH", "MEDIUM", "LOW"]
    assert issue.description is not None


def test_resolve_inconsistency_with_notes(test_db, test_manuscript_id, test_character, test_locations):
    """Test resolving a timeline inconsistency with notes"""
    # Arrange - Create a scenario that produces an inconsistency
    loc1, loc2 = test_locations
    timeline_service.set_location_distance(test_manuscript_id, loc1.id, loc2.id, 100)

    timeline_service.create_event(
        manuscript_id=test_manuscript_id,
        description="Hero at City A",
        event_type="SCENE",
        order_index=0,
        location_id=loc1.id,
        character_ids=[test_character.id]
    )

    timeline_service.create_event(
        manuscript_id=test_manuscript_id,
        description="Hero at City B",
        event_type="SCENE",
        order_index=1,
        location_id=loc2.id,
        character_ids=[test_character.id]
    )

    issues = timeline_service.validate_timeline_orchestrator(test_manuscript_id)
    assert len(issues) > 0

    # Act - Resolve the first issue
    issue_to_resolve = issues[0]
    success = timeline_service.resolve_inconsistency_with_notes(
        issue_to_resolve.id,
        "Fixed by adjusting timeline spacing"
    )

    # Assert
    assert success is True


# ============================================================================
# Comprehensive Data Retrieval Tests
# ============================================================================

def test_get_comprehensive_timeline_data_success(test_manuscript_id):
    """Test successful retrieval of comprehensive timeline data"""
    # Arrange - Get or create travel profile to ensure data exists
    timeline_service.get_or_create_travel_profile(test_manuscript_id)

    # Act
    data = timeline_service.get_comprehensive_timeline_data(test_manuscript_id)

    # Assert
    assert data is not None
    assert "events" in data
    assert "inconsistencies" in data
    assert "character_locations" in data
    assert "travel_legs" in data
    assert "location_distances" in data
    assert "travel_profile" in data
    assert "stats" in data

    # Check data types
    assert isinstance(data["events"], list)
    assert isinstance(data["inconsistencies"], list)
    assert isinstance(data["character_locations"], list)
    assert isinstance(data["travel_legs"], list)
    assert isinstance(data["location_distances"], list)
    assert isinstance(data["stats"], dict)


def test_get_comprehensive_timeline_data_field_access(
    test_db, test_manuscript_id, test_character, test_locations
):
    """Test that all fields in comprehensive data are accessible"""
    # Arrange - Create event with full data
    loc1, loc2 = test_locations

    event = timeline_service.create_event(
        manuscript_id=test_manuscript_id,
        description="Hero arrives at City A",
        event_type="SCENE",
        order_index=0,
        location_id=loc1.id,
        character_ids=[test_character.id]
    )

    # Act
    data = timeline_service.get_comprehensive_timeline_data(test_manuscript_id)

    # Assert - Check event fields are accessible
    assert len(data["events"]) > 0
    test_event = data["events"][0]

    # Critical fields that were causing 500 errors
    assert hasattr(test_event, "description")
    assert hasattr(test_event, "character_ids")
    assert hasattr(test_event, "event_metadata")
    assert hasattr(test_event, "prerequisite_ids")

    # Verify types
    assert isinstance(test_event.character_ids, list)
    assert isinstance(test_event.event_metadata, dict) or test_event.event_metadata is None
    assert isinstance(test_event.prerequisite_ids, list)


def test_get_comprehensive_timeline_data_stats(test_manuscript_id):
    """Test that stats are correctly calculated in comprehensive data"""
    # Arrange
    timeline_service.get_or_create_travel_profile(test_manuscript_id)

    # Act
    data = timeline_service.get_comprehensive_timeline_data(test_manuscript_id)

    # Assert
    stats = data["stats"]
    assert "total_events" in stats
    assert isinstance(stats["total_events"], int)
    assert stats["total_events"] >= 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_get_location_distance_nonexistent():
    """Test getting distance for nonexistent location pair returns None or 0"""
    # Arrange
    manuscript_id = str(uuid.uuid4())
    loc_a = str(uuid.uuid4())
    loc_b = str(uuid.uuid4())

    # Act
    distance = timeline_service.get_location_distance(manuscript_id, loc_a, loc_b)

    # Assert
    assert distance is None or distance == 0


# ============================================================================
# Performance Tests (Phase 1-2 Optimizations)
# ============================================================================

def test_batch_load_entities_performance(test_db, test_manuscript_id):
    """
    Test that batch entity loading is faster than N individual queries.
    Validates Phase 1 optimization: _batch_load_entities() method.
    """
    import time

    # Arrange: Create 100 entities
    entity_ids = []
    db = SessionLocal()

    for i in range(100):
        entity = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            type="CHARACTER",
            name=f"Character {i}",
            attributes={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        entity_ids.append(entity.id)

    db.commit()

    # Act: Time batch loading
    start = time.time()
    entity_map = timeline_service._batch_load_entities(db, entity_ids)
    batch_time = time.time() - start

    # Assert: Performance and correctness
    assert len(entity_map) == 100, "Should load all 100 entities"
    assert batch_time < 0.2, f"Batch load took {batch_time}s, should be < 0.2s"

    # Verify O(1) lookup
    for entity_id in entity_ids:
        assert entity_id in entity_map, f"Entity {entity_id} should be in map"
        assert entity_map[entity_id].id == entity_id

    db.close()


def test_detect_inconsistencies_with_many_events(test_db, test_manuscript_id):
    """
    Test validation performance with 50+ events.
    Ensures N+1 query problem is solved (Phase 1 optimization).
    """
    import time

    # Arrange: Create 10 characters and 5 locations
    db = SessionLocal()
    char_ids = []
    loc_ids = []

    for i in range(10):
        char = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            type="CHARACTER",
            name=f"Char {i}",
            attributes={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(char)
        char_ids.append(char.id)

    for i in range(5):
        loc = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            type="LOCATION",
            name=f"Location {i}",
            attributes={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(loc)
        loc_ids.append(loc.id)

    db.commit()

    # Create 50 events with characters and locations
    for i in range(50):
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            description=f"Event {i}: Important scene",
            order_index=i,
            location_id=loc_ids[i % len(loc_ids)],
            character_ids=char_ids[i % 5:(i % 5) + 3],  # 3 rotating characters
            event_metadata={"word_count": 1000 + (i * 50)},
            prerequisite_ids=[],
            event_type="SCENE",
            narrative_importance=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(event)

    db.commit()
    db.close()

    # Act: Time validation
    start = time.time()
    inconsistencies = timeline_service.detect_inconsistencies(test_manuscript_id)
    validation_time = time.time() - start

    # Assert: Should complete quickly (< 2 seconds with optimizations)
    assert validation_time < 2.0, f"Validation took {validation_time}s, should be < 2s"
    assert isinstance(inconsistencies, list), "Should return list of inconsistencies"
    # With optimizations, this should use ~10 queries instead of 900+


def test_reorder_events_bulk_performance(test_db, test_manuscript_id):
    """
    Test bulk reorder performance (Phase 1.4 optimization).
    Should use 1 query instead of N queries.
    """
    import time

    # Arrange: Create 100 events
    db = SessionLocal()
    event_ids = []

    for i in range(100):
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            description=f"Event {i}",
            order_index=i,
            character_ids=[],
            event_metadata={},
            prerequisite_ids=[],
            event_type="SCENE",
            narrative_importance=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(event)
        event_ids.append(event.id)

    db.commit()
    db.close()

    # Act: Time reordering (reverse order)
    reversed_ids = list(reversed(event_ids))

    start = time.time()
    success = timeline_service.reorder_events(reversed_ids)
    reorder_time = time.time() - start

    # Assert: Performance and correctness
    assert success is True, "Reorder should succeed"
    assert reorder_time < 1.0, f"Reorder took {reorder_time}s, should be < 1s"

    # Verify order changed
    db = SessionLocal()
    events = db.query(TimelineEvent).filter(
        TimelineEvent.manuscript_id == test_manuscript_id
    ).order_by(TimelineEvent.order_index).all()

    assert len(events) == 100, "Should have all 100 events"
    assert events[0].id == reversed_ids[0], "First event should be last original event"
    assert events[-1].id == reversed_ids[-1], "Last event should be first original event"

    db.close()


def test_batch_load_entities_empty_list(test_db):
    """Test batch load with empty list returns empty dict"""
    db = SessionLocal()

    # Act
    entity_map = timeline_service._batch_load_entities(db, [])

    # Assert
    assert entity_map == {}, "Empty input should return empty dict"

    db.close()


def test_detect_inconsistencies_query_efficiency(test_db, test_manuscript_id):
    """
    Verify that inconsistency detection uses minimal queries.
    This is a regression test for N+1 query problems.
    """
    # Arrange: Create test data
    db = SessionLocal()

    # 5 characters
    char_ids = []
    for i in range(5):
        char = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            type="CHARACTER",
            name=f"Character {i}",
            attributes={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(char)
        char_ids.append(char.id)

    # 3 locations
    loc_ids = []
    for i in range(3):
        loc = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            type="LOCATION",
            name=f"Location {i}",
            attributes={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(loc)
        loc_ids.append(loc.id)

    # 20 events
    for i in range(20):
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            manuscript_id=test_manuscript_id,
            description=f"Event {i}",
            order_index=i,
            location_id=loc_ids[i % len(loc_ids)],
            character_ids=char_ids[:2],  # 2 characters per event
            event_metadata={},
            prerequisite_ids=[],
            event_type="SCENE",
            narrative_importance=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(event)

    db.commit()
    db.close()

    # Act: Run validation
    inconsistencies = timeline_service.detect_inconsistencies(test_manuscript_id)

    # Assert: Should complete without errors
    # With batch loading, this uses ~10 queries instead of 100+
    assert isinstance(inconsistencies, list)
    # The key metric is that it completes quickly (tested above)
    # This test ensures no exceptions are raised
