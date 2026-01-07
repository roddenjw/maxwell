"""
Tests for brainstorming_service - AI-powered idea generation service
Tests session management, character prompt building, and response parsing
"""

import json
import uuid

import pytest

from app.models.brainstorm import BrainstormSession
from app.services.brainstorming_service import BrainstormingService


@pytest.fixture
def brainstorm_service(test_db):
    """Create a BrainstormingService instance with test database"""
    return BrainstormingService(test_db)


@pytest.fixture
def test_manuscript_id_brainstorm():
    """Generate a unique manuscript ID for brainstorming tests"""
    return str(uuid.uuid4())


# ============================================================================
# Session Management Tests
# ============================================================================

def test_create_session(brainstorm_service, test_manuscript_id_brainstorm):
    """Test creating a new brainstorming session"""
    # Arrange
    context_data = {"genre": "Fantasy", "premise": "A wizard's apprentice"}

    # Act
    session = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="CHARACTER",
        context_data=context_data
    )

    # Assert
    assert session is not None
    assert session.manuscript_id == test_manuscript_id_brainstorm
    assert session.session_type == "CHARACTER"
    assert session.context_data == context_data
    assert session.status == "IN_PROGRESS"
    assert session.id is not None


def test_get_session(brainstorm_service, test_manuscript_id_brainstorm):
    """Test retrieving a session by ID"""
    # Arrange
    created_session = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="CHARACTER",
        context_data={}
    )

    # Act
    retrieved_session = brainstorm_service.get_session(created_session.id)

    # Assert
    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.manuscript_id == test_manuscript_id_brainstorm


def test_get_session_nonexistent(brainstorm_service):
    """Test getting a nonexistent session returns None"""
    # Arrange
    fake_session_id = str(uuid.uuid4())

    # Act
    session = brainstorm_service.get_session(fake_session_id)

    # Assert
    assert session is None


def test_get_manuscript_sessions(brainstorm_service, test_manuscript_id_brainstorm):
    """Test getting all sessions for a manuscript"""
    # Arrange - Create multiple sessions
    session1 = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="CHARACTER",
        context_data={}
    )
    session2 = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="PLOT",
        context_data={}
    )

    # Act
    sessions = brainstorm_service.get_manuscript_sessions(test_manuscript_id_brainstorm)

    # Assert
    assert len(sessions) == 2
    session_ids = [s.id for s in sessions]
    assert session1.id in session_ids
    assert session2.id in session_ids


def test_update_session_status(brainstorm_service, test_manuscript_id_brainstorm):
    """Test updating a session's status"""
    # Arrange
    session = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="CHARACTER",
        context_data={}
    )
    assert session.status == "IN_PROGRESS"

    # Act
    updated_session = brainstorm_service.update_session_status(session.id, "COMPLETED")

    # Assert
    assert updated_session.status == "COMPLETED"


# ============================================================================
# Character Prompt Building Tests
# ============================================================================

def test_build_character_prompt_basic(brainstorm_service):
    """Test building character prompt with basic inputs"""
    # Arrange
    genre = "Science Fiction"
    story_premise = "Humanity's last stand against alien invaders"
    num_ideas = 3

    # Act
    system_prompt, user_prompt = brainstorm_service._build_character_prompt(
        genre=genre,
        existing_characters=[],
        story_premise=story_premise,
        num_ideas=num_ideas
    )

    # Assert
    assert system_prompt is not None
    assert user_prompt is not None

    # Check system prompt contains methodology
    assert "Brandon Sanderson" in system_prompt
    assert "WANT" in system_prompt
    assert "NEED" in system_prompt
    assert "FLAW" in system_prompt
    assert "STRENGTH" in system_prompt
    assert "ARC" in system_prompt
    assert genre in system_prompt

    # Check user prompt contains story context
    assert story_premise in user_prompt
    assert str(num_ideas) in user_prompt
    assert "JSON" in user_prompt


def test_build_character_prompt_with_existing_characters(brainstorm_service):
    """Test building prompt with existing characters for context"""
    # Arrange
    genre = "Fantasy"
    story_premise = "A kingdom at war"
    existing_characters = ["King Arthur", "Merlin", "Lancelot"]
    num_ideas = 2

    # Act
    system_prompt, user_prompt = brainstorm_service._build_character_prompt(
        genre=genre,
        existing_characters=existing_characters,
        story_premise=story_premise,
        num_ideas=num_ideas
    )

    # Assert
    # Existing characters should be mentioned in user prompt
    for char_name in existing_characters:
        assert char_name in user_prompt

    assert "Existing Characters" in user_prompt


def test_build_character_prompt_structure_requirements(brainstorm_service):
    """Test that prompt includes all required character fields"""
    # Arrange & Act
    _, user_prompt = brainstorm_service._build_character_prompt(
        genre="Mystery",
        existing_characters=[],
        story_premise="A detective's first case",
        num_ideas=1
    )

    # Assert - Check that all required fields are specified
    required_fields = [
        "name",
        "role",
        "want",
        "need",
        "flaw",
        "strength",
        "arc",
        "hook",
        "relationships",
        "story_potential"
    ]

    for field in required_fields:
        assert field in user_prompt


# ============================================================================
# Character Response Parsing Tests
# ============================================================================

def test_parse_character_response_valid_json_array(brainstorm_service):
    """Test parsing a valid JSON array response"""
    # Arrange
    valid_response = json.dumps([
        {
            "name": "Alice",
            "role": "Protagonist",
            "want": "Find the truth",
            "need": "Learn to trust",
            "flaw": "Too cynical",
            "strength": "Analytical mind",
            "arc": "Learns to believe in others"
        },
        {
            "name": "Bob",
            "role": "Mentor",
            "want": "Protect Alice",
            "need": "Let go of guilt",
            "flaw": "Overprotective",
            "strength": "Experienced fighter",
            "arc": "Finds redemption"
        }
    ])

    # Act
    characters = brainstorm_service._parse_character_response(valid_response)

    # Assert
    assert isinstance(characters, list)
    assert len(characters) == 2
    assert characters[0]["name"] == "Alice"
    assert characters[1]["name"] == "Bob"


def test_parse_character_response_single_object(brainstorm_service):
    """Test parsing a single character object (not array)"""
    # Arrange
    single_char = json.dumps({
        "name": "Solo Character",
        "role": "Hero",
        "want": "Save the world"
    })

    # Act
    characters = brainstorm_service._parse_character_response(single_char)

    # Assert
    assert isinstance(characters, list)
    assert len(characters) == 1
    assert characters[0]["name"] == "Solo Character"


def test_parse_character_response_markdown_json(brainstorm_service):
    """Test parsing JSON wrapped in markdown code blocks"""
    # Arrange
    markdown_response = """Here are some characters:

```json
[
  {
    "name": "Markdown Character",
    "role": "Protagonist",
    "want": "Escape markdown"
  }
]
```

Hope this helps!"""

    # Act
    characters = brainstorm_service._parse_character_response(markdown_response)

    # Assert
    assert isinstance(characters, list)
    assert len(characters) == 1
    assert characters[0]["name"] == "Markdown Character"


def test_parse_character_response_embedded_json(brainstorm_service):
    """Test extracting JSON from response with extra text"""
    # Arrange
    embedded_response = """Sure, here are your characters:
[{"name": "Embedded Char", "role": "Sidekick"}]
That's all!"""

    # Act
    characters = brainstorm_service._parse_character_response(embedded_response)

    # Assert
    assert isinstance(characters, list)
    assert len(characters) == 1
    assert characters[0]["name"] == "Embedded Char"


def test_parse_character_response_invalid_raises_error(brainstorm_service):
    """Test that completely invalid response raises ValueError"""
    # Arrange
    invalid_response = "This is just plain text with no JSON at all."

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        brainstorm_service._parse_character_response(invalid_response)

    assert "Could not parse AI response" in str(exc_info.value)


# ============================================================================
# Character Description Formatting Tests
# ============================================================================

def test_format_character_description_complete_data(brainstorm_service):
    """Test formatting a character with all fields"""
    # Arrange
    char_data = {
        "name": "Aeliana Starweaver",
        "role": "Protagonist",
        "hook": "A mage who lost her magic but gained foresight",
        "want": "Regain her magical powers",
        "need": "Accept her new gift and its burden",
        "flaw": "Refuses to accept change",
        "strength": "Strategic thinking from years of combat",
        "arc": "Learns that losing one gift opened door to greater purpose",
        "relationships": "Rivals with the Academy Chancellor, mentor to young orphans",
        "story_potential": "Her visions drive the main plot and create moral dilemmas"
    }

    # Act
    description = brainstorm_service._format_character_description(char_data)

    # Assert
    assert "Aeliana Starweaver" in description
    assert "Protagonist" in description
    assert "Regain her magical powers" in description
    assert "Accept her new gift" in description
    assert "Refuses to accept change" in description
    assert "Strategic thinking" in description


def test_format_character_description_missing_fields(brainstorm_service):
    """Test formatting with missing optional fields uses defaults"""
    # Arrange
    minimal_data = {
        "name": "Minimal Character"
    }

    # Act
    description = brainstorm_service._format_character_description(minimal_data)

    # Assert
    assert "Minimal Character" in description
    assert "Unknown" in description  # Default value for missing fields


def test_format_character_description_structure(brainstorm_service):
    """Test that formatted description has expected structure"""
    # Arrange
    char_data = {
        "name": "Test Hero",
        "role": "Hero",
        "want": "Win",
        "need": "Grow",
        "flaw": "Pride",
        "strength": "Courage",
        "arc": "Humility"
    }

    # Act
    description = brainstorm_service._format_character_description(char_data)

    # Assert
    # Check that all section headers are present
    assert "**What They Want**:" in description
    assert "**What They Need**:" in description
    assert "**Fatal Flaw**:" in description
    assert "**Key Strength**:" in description
    assert "**Character Arc**:" in description
    assert "**Relationships**:" in description
    assert "**Story Potential**:" in description


# ============================================================================
# Edge Cases and Integration
# ============================================================================

def test_create_session_with_outline_id(brainstorm_service, test_manuscript_id_brainstorm):
    """Test creating session associated with an outline"""
    # Arrange
    outline_id = str(uuid.uuid4())

    # Act
    session = brainstorm_service.create_session(
        manuscript_id=test_manuscript_id_brainstorm,
        session_type="PLOT",
        context_data={},
        outline_id=outline_id
    )

    # Assert
    assert session.outline_id == outline_id


def test_get_manuscript_sessions_empty(brainstorm_service):
    """Test getting sessions for manuscript with no sessions"""
    # Arrange
    manuscript_id = str(uuid.uuid4())

    # Act
    sessions = brainstorm_service.get_manuscript_sessions(manuscript_id)

    # Assert
    assert isinstance(sessions, list)
    assert len(sessions) == 0
