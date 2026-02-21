"""
Tests for CodexService - entity CRUD, relationships, and suggestions.

Note: CodexService uses SessionLocal() internally, so tests must patch it.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock

from app.services.codex_service import CodexService
from app.models.entity import Entity, Relationship, EntitySuggestion


@pytest.fixture
def codex_service(test_db):
    """Create a CodexService with patched SessionLocal returning test_db."""
    with patch("app.services.codex_service.SessionLocal", return_value=test_db):
        svc = CodexService()
        # Patch _trigger_wiki_sync to be a no-op (avoids threading issues in tests)
        svc._trigger_wiki_sync = MagicMock()
        # Prevent CodexService methods from closing the shared test session
        original_close = test_db.close
        test_db.close = lambda: None
        yield svc
        test_db.close = original_close


class TestCodexEntityCRUD:
    """Tests for entity CRUD operations."""

    def test_create_entity(self, codex_service, sample_manuscript):
        entity = codex_service.create_entity(
            manuscript_id=sample_manuscript.id,
            entity_type="CHARACTER",
            name="Test Hero",
            aliases=["Hero", "The Brave One"],
            attributes={"age": 30},
        )
        assert entity is not None
        assert entity.name == "Test Hero"
        assert entity.type == "CHARACTER"
        assert "Hero" in entity.aliases

    def test_get_entities(self, codex_service, sample_manuscript):
        codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        codex_service.create_entity(sample_manuscript.id, "LOCATION", "Forest")
        codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Bob")

        all_entities = codex_service.get_entities(sample_manuscript.id)
        assert len(all_entities) == 3

        chars = codex_service.get_entities(sample_manuscript.id, entity_type="CHARACTER")
        assert len(chars) == 2

    def test_get_entity(self, codex_service, sample_manuscript):
        entity = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        found = codex_service.get_entity(entity.id)
        assert found is not None
        assert found.name == "Alice"

    def test_get_entity_not_found(self, codex_service):
        assert codex_service.get_entity("nonexistent") is None

    def test_update_entity(self, codex_service, sample_manuscript):
        entity = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        updated = codex_service.update_entity(entity.id, name="Alice Updated", aliases=["Al"])
        assert updated is not None
        assert updated.name == "Alice Updated"
        assert "Al" in updated.aliases

    def test_delete_entity(self, codex_service, sample_manuscript):
        entity = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        assert codex_service.delete_entity(entity.id) is True
        assert codex_service.get_entity(entity.id) is None

    def test_delete_entity_not_found(self, codex_service):
        assert codex_service.delete_entity("nonexistent") is False


class TestCodexRelationships:
    """Tests for entity relationships."""

    def test_create_relationship(self, codex_service, sample_manuscript):
        alice = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        bob = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Bob")

        rel = codex_service.create_relationship(alice.id, bob.id, "ALLY")
        assert rel is not None
        assert rel.source_entity_id == alice.id
        assert rel.target_entity_id == bob.id
        assert rel.relationship_type == "ALLY"

    def test_relationship_upsert(self, codex_service, sample_manuscript):
        alice = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        bob = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Bob")

        rel1 = codex_service.create_relationship(alice.id, bob.id, "ALLY")
        rel2 = codex_service.create_relationship(alice.id, bob.id, "ALLY")
        # Should be same relationship with incremented strength
        assert rel1.id == rel2.id
        assert rel2.strength >= 2

    def test_get_relationships(self, codex_service, sample_manuscript):
        alice = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        bob = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Bob")
        codex_service.create_relationship(alice.id, bob.id, "ALLY")

        rels = codex_service.get_relationships(sample_manuscript.id)
        assert len(rels) >= 1

    def test_delete_relationship(self, codex_service, sample_manuscript):
        alice = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        bob = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Bob")
        rel = codex_service.create_relationship(alice.id, bob.id, "ALLY")
        assert codex_service.delete_relationship(rel.id) is True


class TestCodexSuggestions:
    """Tests for entity suggestion queue."""

    def test_create_suggestion(self, codex_service, sample_manuscript):
        suggestion = codex_service.create_suggestion(
            manuscript_id=sample_manuscript.id,
            name="Alice",
            entity_type="CHARACTER",
            context="Alice walked into the room",
        )
        assert suggestion is not None
        assert suggestion.name == "Alice"

    def test_create_suggestion_duplicate(self, codex_service, sample_manuscript):
        s1 = codex_service.create_suggestion(sample_manuscript.id, "Alice", "CHARACTER", "ctx1")
        s2 = codex_service.create_suggestion(sample_manuscript.id, "Alice", "CHARACTER", "ctx2")
        # Should return existing
        assert s1.id == s2.id

    def test_create_suggestion_existing_entity(self, codex_service, sample_manuscript):
        codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice")
        suggestion = codex_service.create_suggestion(sample_manuscript.id, "Alice", "CHARACTER", "ctx")
        # Should return None (entity already exists)
        assert suggestion is None

    def test_approve_suggestion(self, codex_service, sample_manuscript):
        suggestion = codex_service.create_suggestion(sample_manuscript.id, "Alice", "CHARACTER", "ctx")
        entity = codex_service.approve_suggestion(suggestion.id)
        assert entity is not None
        assert entity.name == "Alice"

    def test_reject_suggestion(self, codex_service, sample_manuscript):
        suggestion = codex_service.create_suggestion(sample_manuscript.id, "Alice", "CHARACTER", "ctx")
        assert codex_service.reject_suggestion(suggestion.id) is True


class TestCodexMerge:
    """Tests for entity merging."""

    def test_merge_entities(self, codex_service, sample_manuscript):
        alice = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice", aliases=["Al"])
        alice_dup = codex_service.create_entity(sample_manuscript.id, "CHARACTER", "Alice W.", aliases=["Alice"])

        merged = codex_service.merge_entities(
            primary_entity_id=alice.id,
            secondary_entity_ids=[alice_dup.id],
            merge_strategy={"aliases": "combine", "attributes": "merge"},
        )
        assert merged is not None
        # Aliases should be combined
        assert "Alice" in merged.aliases or "Al" in merged.aliases
        # Secondary should be deleted
        assert codex_service.get_entity(alice_dup.id) is None
