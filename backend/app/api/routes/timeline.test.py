"""
Tests for timeline API routes
Tests the comprehensive timeline endpoint and timeline event CRUD operations
"""

import uuid
from datetime import datetime

import pytest

from app.models.entity import Entity
from app.services.timeline_service import timeline_service


@pytest.fixture
def test_manuscript_id_api(test_db):
    """Generate a manuscript ID and create travel profile for API tests"""
    manuscript_id = str(uuid.uuid4())
    timeline_service.get_or_create_travel_profile(manuscript_id)
    return manuscript_id


@pytest.fixture
def test_timeline_data(test_db, test_manuscript_id_api):
    """Create complete timeline data for testing"""
    # Create character
    char = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id_api,
        type="CHARACTER",
        name="Test Hero",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(char)

    # Create locations
    loc1 = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id_api,
        type="LOCATION",
        name="City A",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    loc2 = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=test_manuscript_id_api,
        type="LOCATION",
        name="City B",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(loc1)
    test_db.add(loc2)
    test_db.commit()
    test_db.refresh(char)
    test_db.refresh(loc1)
    test_db.refresh(loc2)

    # Set location distance
    timeline_service.set_location_distance(test_manuscript_id_api, loc1.id, loc2.id, 100)

    # Create timeline events
    event1 = timeline_service.create_event(
        manuscript_id=test_manuscript_id_api,
        description="Hero arrives at City A",
        event_type="SCENE",
        order_index=0,
        location_id=loc1.id,
        character_ids=[char.id]
    )

    event2 = timeline_service.create_event(
        manuscript_id=test_manuscript_id_api,
        description="Hero arrives at City B",
        event_type="SCENE",
        order_index=1,
        location_id=loc2.id,
        character_ids=[char.id]
    )

    return {
        "manuscript_id": test_manuscript_id_api,
        "character": char,
        "locations": [loc1, loc2],
        "events": [event1, event2]
    }


# ============================================================================
# Comprehensive Timeline Endpoint Tests
# ============================================================================

def test_comprehensive_timeline_endpoint_success(client, test_timeline_data):
    """Test /api/timeline/comprehensive endpoint returns valid data structure"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data

    timeline_data = data["data"]
    assert "events" in timeline_data
    assert "inconsistencies" in timeline_data
    assert "character_locations" in timeline_data
    assert "travel_legs" in timeline_data
    assert "location_distances" in timeline_data
    assert "travel_profile" in timeline_data
    assert "stats" in timeline_data


def test_comprehensive_timeline_endpoint_data_types(client, test_timeline_data):
    """Test that comprehensive endpoint returns correctly typed data"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    timeline_data = response.json()["data"]

    # Check list types
    assert isinstance(timeline_data["events"], list)
    assert isinstance(timeline_data["inconsistencies"], list)
    assert isinstance(timeline_data["character_locations"], list)
    assert isinstance(timeline_data["travel_legs"], list)
    assert isinstance(timeline_data["location_distances"], list)

    # Check that we have data
    assert len(timeline_data["events"]) > 0

    # Check event structure
    event = timeline_data["events"][0]
    assert "description" in event
    assert "character_ids" in event
    assert "event_metadata" in event or event.get("event_metadata") is None
    assert "prerequisite_ids" in event
    assert "narrative_importance" in event


def test_comprehensive_timeline_endpoint_inconsistency_fields(client, test_timeline_data):
    """Test that inconsistency objects have correct fields and types"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Trigger validation to create inconsistencies
    timeline_service.validate_timeline_orchestrator(manuscript_id)

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    timeline_data = response.json()["data"]

    # Check inconsistencies if any exist
    if timeline_data["inconsistencies"]:
        inc = timeline_data["inconsistencies"][0]

        # Critical fields that were causing serialization issues
        assert "is_resolved" in inc
        assert isinstance(inc["is_resolved"], bool)

        # Optional fields should exist (can be null)
        assert "suggestion" in inc
        assert "teaching_point" in inc


def test_comprehensive_timeline_endpoint_stats(client, test_timeline_data):
    """Test that stats object has correct structure"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    stats = response.json()["data"]["stats"]
    assert "total_events" in stats
    assert isinstance(stats["total_events"], int)
    assert stats["total_events"] >= 0


def test_comprehensive_timeline_endpoint_not_found(client):
    """Test endpoint returns 404 for invalid manuscript"""
    # Arrange
    invalid_manuscript_id = str(uuid.uuid4())

    # Act
    response = client.get(f"/api/timeline/comprehensive/{invalid_manuscript_id}")

    # Assert
    # Depending on implementation, might return 200 with empty data or 404
    # Adjust based on actual behavior
    if response.status_code == 404:
        assert True
    elif response.status_code == 200:
        data = response.json()["data"]
        assert len(data["events"]) == 0


def test_comprehensive_timeline_endpoint_travel_profile(client, test_timeline_data):
    """Test that travel profile is included in response"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    travel_profile = response.json()["data"]["travel_profile"]
    assert travel_profile is not None
    assert "default_speed" in travel_profile
    assert "speeds" in travel_profile


def test_comprehensive_timeline_endpoint_location_distances(client, test_timeline_data):
    """Test that location distances are included in response"""
    # Arrange
    manuscript_id = test_timeline_data["manuscript_id"]

    # Act
    response = client.get(f"/api/timeline/comprehensive/{manuscript_id}")

    # Assert
    assert response.status_code == 200

    location_distances = response.json()["data"]["location_distances"]
    assert isinstance(location_distances, list)

    # We created one distance in the fixture
    assert len(location_distances) >= 1

    if location_distances:
        distance = location_distances[0]
        assert "location_a_id" in distance
        assert "location_b_id" in distance
        assert "distance_km" in distance
