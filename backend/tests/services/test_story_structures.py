"""
Tests for story_structures - Story structure templates and beat generation
Tests template retrieval, available structures listing, and plot beat creation
"""

import pytest

from app.services.story_structures import (
    PlotBeatTemplate,
    create_plot_beats_from_template,
    get_available_structures,
    get_structure_template,
)


# ============================================================================
# PlotBeatTemplate Tests
# ============================================================================

def test_plot_beat_template_creation():
    """Test creating a PlotBeatTemplate instance"""
    # Arrange & Act
    beat = PlotBeatTemplate(
        beat_name="test-beat",
        beat_label="Test Beat",
        description="A test beat description",
        position_percent=0.25,
        order_index=1,
        tips="Some helpful tips"
    )

    # Assert
    assert beat.beat_name == "test-beat"
    assert beat.beat_label == "Test Beat"
    assert beat.description == "A test beat description"
    assert beat.position_percent == 0.25
    assert beat.order_index == 1
    assert beat.tips == "Some helpful tips"


def test_plot_beat_template_to_dict():
    """Test PlotBeatTemplate.to_dict() includes all fields including tips"""
    # Arrange
    beat = PlotBeatTemplate(
        beat_name="hook",
        beat_label="Hook",
        description="Opening scene",
        position_percent=0.0,
        order_index=0,
        tips="Start strong"
    )

    # Act
    beat_dict = beat.to_dict()

    # Assert
    assert beat_dict["beat_name"] == "hook"
    assert beat_dict["beat_label"] == "Hook"
    assert beat_dict["beat_description"] == "Opening scene"
    assert beat_dict["target_position_percent"] == 0.0
    assert beat_dict["order_index"] == 0
    assert beat_dict["tips"] == "Start strong"


def test_plot_beat_template_to_db_dict():
    """Test PlotBeatTemplate.to_db_dict() excludes tips field"""
    # Arrange
    beat = PlotBeatTemplate(
        beat_name="hook",
        beat_label="Hook",
        description="Opening scene",
        position_percent=0.0,
        order_index=0,
        tips="Start strong"
    )

    # Act
    db_dict = beat.to_db_dict()

    # Assert
    assert "beat_name" in db_dict
    assert "beat_label" in db_dict
    assert "beat_description" in db_dict
    assert "target_position_percent" in db_dict
    assert "order_index" in db_dict
    assert "tips" not in db_dict  # Should be excluded for DB


# ============================================================================
# get_available_structures() Tests
# ============================================================================

def test_get_available_structures_returns_list():
    """Test that get_available_structures returns a non-empty list"""
    # Act
    structures = get_available_structures()

    # Assert
    assert isinstance(structures, list)
    assert len(structures) > 0


def test_get_available_structures_has_required_fields():
    """Test that each structure has all required metadata fields"""
    # Act
    structures = get_available_structures()

    # Assert
    for structure in structures:
        assert "id" in structure
        assert "name" in structure
        assert "description" in structure
        assert "beat_count" in structure
        assert "recommended_for" in structure
        assert "word_count_range" in structure

        # Verify types
        assert isinstance(structure["id"], str)
        assert isinstance(structure["name"], str)
        assert isinstance(structure["description"], str)
        assert isinstance(structure["beat_count"], int)
        assert isinstance(structure["recommended_for"], list)
        assert isinstance(structure["word_count_range"], dict)


def test_get_available_structures_includes_common_structures():
    """Test that common story structures are available"""
    # Act
    structures = get_available_structures()
    structure_ids = [s["id"] for s in structures]

    # Assert - Check for well-known structures
    # At least one of these should exist (adjust based on actual implementation)
    common_structures = [
        "story-arc-9",
        "heros-journey",
        "save-the-cat",
        "three-act",
        "fichtean-curve"
    ]

    # At least some common structures should be present
    found_count = sum(1 for struct in common_structures if struct in structure_ids)
    assert found_count > 0, f"Expected at least one common structure, got IDs: {structure_ids}"


# ============================================================================
# get_structure_template() Tests
# ============================================================================

def test_get_structure_template_valid_id():
    """Test getting a valid structure template"""
    # Arrange - Get first available structure
    available = get_available_structures()
    assert len(available) > 0, "No structures available for testing"

    first_structure_id = available[0]["id"]

    # Act
    template = get_structure_template(first_structure_id)

    # Assert
    assert template is not None
    assert "name" in template
    assert "description" in template
    assert "beats" in template
    assert isinstance(template["beats"], list)
    assert len(template["beats"]) > 0


def test_get_structure_template_invalid_id():
    """Test that invalid structure ID raises ValueError"""
    # Arrange
    invalid_id = "nonexistent-structure-12345"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        get_structure_template(invalid_id)

    assert "Unknown structure type" in str(exc_info.value)


def test_get_structure_template_beat_structure():
    """Test that beats in template have correct structure"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]

    # Act
    template = get_structure_template(first_structure_id)

    # Assert
    for beat in template["beats"]:
        # Check that beat is a PlotBeatTemplate instance
        assert isinstance(beat, PlotBeatTemplate)

        # Check required attributes
        assert hasattr(beat, "beat_name")
        assert hasattr(beat, "beat_label")
        assert hasattr(beat, "description")
        assert hasattr(beat, "position_percent")
        assert hasattr(beat, "order_index")


# ============================================================================
# create_plot_beats_from_template() Tests
# ============================================================================

def test_create_plot_beats_from_template_default_word_count():
    """Test creating plot beats with default word count"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]

    # Act
    beats = create_plot_beats_from_template(first_structure_id)

    # Assert
    assert isinstance(beats, list)
    assert len(beats) > 0

    # Check first beat structure
    first_beat = beats[0]
    assert "beat_name" in first_beat
    assert "beat_label" in first_beat
    assert "beat_description" in first_beat
    assert "target_position_percent" in first_beat
    assert "order_index" in first_beat
    assert "target_word_count" in first_beat


def test_create_plot_beats_from_template_custom_word_count():
    """Test creating plot beats with custom target word count"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]
    custom_word_count = 120000

    # Act
    beats = create_plot_beats_from_template(first_structure_id, custom_word_count)

    # Assert
    assert len(beats) > 0

    # Verify word counts are calculated based on position percentages
    for beat in beats:
        assert "target_word_count" in beat
        expected_word_count = int(beat["target_position_percent"] * custom_word_count)
        assert beat["target_word_count"] == expected_word_count


def test_create_plot_beats_from_template_beat_ordering():
    """Test that created beats maintain correct order_index sequence"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]

    # Act
    beats = create_plot_beats_from_template(first_structure_id)

    # Assert - Check that order_index values are sequential starting from 0
    for i, beat in enumerate(beats):
        assert beat["order_index"] == i


def test_create_plot_beats_from_template_position_percentages():
    """Test that position percentages are within valid range [0.0, 1.0]"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]

    # Act
    beats = create_plot_beats_from_template(first_structure_id)

    # Assert
    for beat in beats:
        assert 0.0 <= beat["target_position_percent"] <= 1.0


def test_create_plot_beats_from_template_invalid_structure():
    """Test that invalid structure type raises ValueError"""
    # Arrange
    invalid_id = "invalid-structure-xyz"

    # Act & Assert
    with pytest.raises(ValueError):
        create_plot_beats_from_template(invalid_id)


def test_create_plot_beats_excludes_tips():
    """Test that created beats for DB insertion exclude tips field"""
    # Arrange
    available = get_available_structures()
    first_structure_id = available[0]["id"]

    # Act
    beats = create_plot_beats_from_template(first_structure_id)

    # Assert - tips should not be in DB-ready beats
    for beat in beats:
        assert "tips" not in beat, "tips field should be excluded from DB beats"


# ============================================================================
# Integration Tests
# ============================================================================

def test_all_available_structures_can_generate_beats():
    """Test that all available structures can successfully generate beats"""
    # Arrange
    available = get_available_structures()

    # Act & Assert
    for structure in available:
        structure_id = structure["id"]

        # Should not raise exception
        beats = create_plot_beats_from_template(structure_id, 80000)

        assert len(beats) > 0
        assert len(beats) == structure["beat_count"]


def test_structure_beat_count_matches_generated_beats():
    """Test that beat_count in metadata matches actual generated beat count"""
    # Arrange
    available = get_available_structures()

    # Act & Assert
    for structure in available:
        structure_id = structure["id"]
        expected_count = structure["beat_count"]

        beats = create_plot_beats_from_template(structure_id)

        assert len(beats) == expected_count, (
            f"Structure '{structure_id}' metadata says {expected_count} beats, "
            f"but generated {len(beats)} beats"
        )
