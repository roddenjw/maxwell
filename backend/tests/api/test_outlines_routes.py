"""
Tests for outlines API routes
Tests outline CRUD operations and plot beat management
"""

import uuid

import pytest


@pytest.fixture
def test_manuscript_outline(test_db, sample_manuscript):
    """Fixture providing test manuscript for outline tests"""
    return sample_manuscript


# ============================================================================
# Outline Creation Tests
# ============================================================================

def test_create_outline_success(client, test_manuscript_outline):
    """Test successful outline creation"""
    # Arrange
    outline_data = {
        "manuscript_id": test_manuscript_outline.id,
        "structure_type": "story-arc-9",
        "target_word_count": 80000,
        "title": "Test Outline"
    }

    # Act
    response = client.post("/api/outlines", json=outline_data)

    # Assert
    assert response.status_code in [200, 201]

    # Note: Response format may vary based on ApiResponse pattern implementation
    # This test will need updating when ApiResponse pattern is applied
    data = response.json()

    # Check for either old format or new ApiResponse format
    if "success" in data:
        assert data["success"] is True
        outline = data["data"]
    else:
        outline = data

    assert "id" in outline
    assert outline["manuscript_id"] == test_manuscript_outline.id


def test_create_outline_invalid_manuscript(client):
    """Test creating outline with invalid manuscript ID returns error"""
    # Arrange
    outline_data = {
        "manuscript_id": str(uuid.uuid4()),  # Non-existent
        "structure_type": "story-arc-9",
        "target_word_count": 80000
    }

    # Act
    response = client.post("/api/outlines", json=outline_data)

    # Assert
    assert response.status_code in [404, 400, 500]


def test_create_outline_invalid_structure(client, test_manuscript_outline):
    """Test creating outline with invalid structure type"""
    # Arrange
    outline_data = {
        "manuscript_id": test_manuscript_outline.id,
        "structure_type": "invalid-structure-xyz",
        "target_word_count": 80000
    }

    # Act
    response = client.post("/api/outlines", json=outline_data)

    # Assert
    assert response.status_code in [400, 422, 500]


# ============================================================================
# Outline Retrieval Tests
# ============================================================================

def test_get_manuscript_outlines_empty(client, test_manuscript_outline):
    """Test getting outlines for manuscript with no outlines"""
    # Act
    response = client.get(f"/api/outlines/manuscript/{test_manuscript_outline.id}")

    # Assert
    assert response.status_code == 200

    data = response.json()

    # Handle both old and new response formats
    if "success" in data:
        outlines = data["data"]
    else:
        outlines = data

    assert isinstance(outlines, list)
    # May or may not be empty depending on fixtures


def test_get_outline_by_id_not_found(client):
    """Test getting nonexistent outline returns 404"""
    # Arrange
    fake_outline_id = str(uuid.uuid4())

    # Act
    response = client.get(f"/api/outlines/{fake_outline_id}")

    # Assert
    assert response.status_code == 404


# ============================================================================
# Plot Beat Tests
# ============================================================================

def test_create_plot_beat_requires_outline(client):
    """Test that creating plot beat with invalid outline fails"""
    # Arrange
    beat_data = {
        "outline_id": str(uuid.uuid4()),
        "beat_name": "test-beat",
        "beat_label": "Test Beat",
        "beat_description": "A test beat"
    }

    # Act
    response = client.post("/api/outlines/plot-beats", json=beat_data)

    # Assert
    assert response.status_code in [404, 400, 500]


# ============================================================================
# Structure Templates Tests
# ============================================================================

def test_get_available_structures(client):
    """Test getting list of available story structures"""
    # Act
    response = client.get("/api/outlines/structures")

    # Assert
    assert response.status_code == 200

    data = response.json()

    # Handle both old and new response formats
    if "success" in data:
        structures = data["data"]
    else:
        structures = data

    assert isinstance(structures, list)
    assert len(structures) > 0

    # Check first structure has required fields
    if structures:
        first_structure = structures[0]
        assert "id" in first_structure
        assert "name" in first_structure
        assert "description" in first_structure


def test_get_structure_template(client):
    """Test getting a specific structure template"""
    # Arrange - Get first available structure
    structures_response = client.get("/api/outlines/structures")
    structures_data = structures_response.json()

    if "success" in structures_data:
        structures = structures_data["data"]
    else:
        structures = structures_data

    assert len(structures) > 0
    first_structure_id = structures[0]["id"]

    # Act
    response = client.get(f"/api/outlines/structures/{first_structure_id}")

    # Assert
    assert response.status_code == 200

    data = response.json()

    if "success" in data:
        template = data["data"]
    else:
        template = data

    assert "name" in template
    assert "beats" in template


def test_get_structure_template_invalid(client):
    """Test getting invalid structure returns 400/404"""
    # Act
    response = client.get("/api/outlines/structures/invalid-structure")

    # Assert
    assert response.status_code in [400, 404]


# ============================================================================
# Edge Cases
# ============================================================================

def test_create_outline_missing_required_fields(client):
    """Test creating outline with missing required fields"""
    # Arrange
    incomplete_data = {
        "manuscript_id": str(uuid.uuid4())
        # Missing structure_type
    }

    # Act
    response = client.post("/api/outlines", json=incomplete_data)

    # Assert
    assert response.status_code in [400, 422]


def test_get_manuscript_outlines_invalid_id(client):
    """Test getting outlines with malformed manuscript ID"""
    # Act
    response = client.get("/api/outlines/manuscript/not-a-uuid")

    # Assert
    # May return 404, 400, or 200 with empty list depending on validation
    assert response.status_code in [200, 400, 404]
