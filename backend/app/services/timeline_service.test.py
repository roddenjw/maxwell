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
    updated_profile = timeline_service.update_travel_speeds(
        test_manuscript_id,
        {"dragon": 100, "magic_portal": 999999},
        default_speed=10
    )

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
    assert issue.severity in ["CRITICAL", "WARNING", "INFO"]
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
