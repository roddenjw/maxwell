"""
Tests for CultureService - culture links, queries, and context resolution.
"""
import pytest
import uuid

from app.services.culture_service import CultureService
from app.services.wiki_service import WikiService
from app.models.wiki import WikiEntry, WikiEntryType, WikiEntryStatus, WikiReferenceType


@pytest.fixture
def culture_entry(test_db, sample_world):
    """Create a culture wiki entry."""
    entry = WikiEntry(
        id=str(uuid.uuid4()),
        world_id=sample_world.id,
        entry_type=WikiEntryType.CULTURE.value,
        title="Elven Culture",
        slug="elven-culture",
        content="Ancient and wise culture of the elves",
        summary="Elven traditions and customs",
        structured_data={
            "values": ["honor", "nature", "wisdom"],
            "taboos": ["deforestation", "betrayal"],
            "customs": ["moon ceremony", "tree planting"],
            "speech_patterns": ["formal address", "poetic speech"],
        },
        status=WikiEntryStatus.PUBLISHED.value,
        confidence_score=1.0,
        tags=["elves"],
        aliases=["Elvish Culture"],
        source_manuscripts=[],
        source_chapters=[],
    )
    test_db.add(entry)
    test_db.commit()
    test_db.refresh(entry)
    return entry


@pytest.fixture
def character_entry(test_db, sample_world):
    """Create a character wiki entry."""
    entry = WikiEntry(
        id=str(uuid.uuid4()),
        world_id=sample_world.id,
        entry_type=WikiEntryType.CHARACTER.value,
        title="Legolas",
        slug="legolas",
        content="An elven prince",
        summary="Elven archer and warrior",
        structured_data={"age": 2931},
        status=WikiEntryStatus.PUBLISHED.value,
        confidence_score=1.0,
        tags=[],
        aliases=["Prince Legolas"],
        source_manuscripts=[],
        source_chapters=[],
    )
    test_db.add(entry)
    test_db.commit()
    test_db.refresh(entry)
    return entry


class TestCultureLinks:
    """Tests for linking entities to cultures."""

    def test_link_entity_to_culture(self, test_db, character_entry, culture_entry):
        svc = CultureService(test_db)
        ref = svc.link_entity_to_culture(
            entity_entry_id=character_entry.id,
            culture_entry_id=culture_entry.id,
            reference_type=WikiReferenceType.MEMBER_OF.value,
            context="Born into this culture",
        )
        assert ref is not None
        assert ref.source_entry_id == character_entry.id
        assert ref.target_entry_id == culture_entry.id

    def test_unlink_entity_from_culture(self, test_db, character_entry, culture_entry):
        svc = CultureService(test_db)
        ref = svc.link_entity_to_culture(character_entry.id, culture_entry.id, WikiReferenceType.MEMBER_OF.value)
        assert svc.unlink_entity_from_culture(ref.id) is True


class TestCultureQueries:
    """Tests for culture query methods."""

    def test_get_entity_cultures(self, test_db, character_entry, culture_entry):
        svc = CultureService(test_db)
        svc.link_entity_to_culture(character_entry.id, culture_entry.id, WikiReferenceType.MEMBER_OF.value)

        cultures = svc.get_entity_cultures(character_entry.id)
        assert len(cultures) >= 1
        assert any(c["culture_title"] == "Elven Culture" for c in cultures)

    def test_get_culture_members(self, test_db, character_entry, culture_entry):
        svc = CultureService(test_db)
        svc.link_entity_to_culture(character_entry.id, culture_entry.id, WikiReferenceType.MEMBER_OF.value)

        members = svc.get_culture_members(culture_entry.id)
        assert len(members) >= 1
        assert any(m["entity_title"] == "Legolas" for m in members)

    def test_get_world_cultures(self, test_db, sample_world, culture_entry):
        svc = CultureService(test_db)
        cultures = svc.get_world_cultures(sample_world.id)
        assert len(cultures) >= 1
        assert any(c["title"] == "Elven Culture" for c in cultures)


class TestCultureContext:
    """Tests for culture context resolution for agents."""

    def test_get_culture_facts(self, test_db, culture_entry):
        svc = CultureService(test_db)
        facts = svc.get_culture_facts(culture_entry.id)
        assert facts["found"] is True
        assert facts["title"] == "Elven Culture"
        assert "values" in facts.get("structured_data", {})

    def test_get_culture_facts_not_found(self, test_db):
        svc = CultureService(test_db)
        facts = svc.get_culture_facts("nonexistent")
        assert facts["found"] is False

    def test_format_culture_for_prompt(self, test_db, culture_entry):
        svc = CultureService(test_db)
        prompt = svc.format_culture_for_prompt(culture_entry.id)
        assert "Elven Culture" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_character_cultural_context(self, test_db, sample_world, character_entry, culture_entry):
        svc = CultureService(test_db)
        svc.link_entity_to_culture(character_entry.id, culture_entry.id, WikiReferenceType.MEMBER_OF.value)

        ctx = svc.get_character_cultural_context("Legolas", sample_world.id)
        assert ctx["found"] is True
        assert ctx["has_cultures"] is True
        assert len(ctx["cultures"]) >= 1
