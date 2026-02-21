"""
Tests for WikiService - CRUD, change queue, cross-references, and consistency engine.
"""
import pytest
import uuid

from app.services.wiki_service import WikiService, WikiConsistencyEngine
from app.models.wiki import (
    WikiEntry, WikiEntryType, WikiEntryStatus,
    WikiChange, WikiChangeType, WikiChangeStatus,
    WikiCrossReference, WikiReferenceType,
)
from app.models.world import World
from app.models.world_rule import WorldRule


class TestWikiServiceCRUD:
    """Tests for WikiEntry create/read/update/delete."""

    def test_create_entry(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry = svc.create_entry(
            world_id=sample_world.id,
            entry_type=WikiEntryType.CHARACTER.value,
            title="Alice Wonderland",
            content="A curious girl",
            summary="Protagonist",
            tags=["hero"],
            aliases=["Alice"],
        )
        assert entry is not None
        assert entry.title == "Alice Wonderland"
        assert entry.slug == "alice-wonderland"
        assert entry.entry_type == WikiEntryType.CHARACTER.value
        assert entry.status == WikiEntryStatus.DRAFT.value
        assert entry.confidence_score == 1.0
        assert entry.created_by == "author"

    def test_create_entry_ai_source(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry = svc.create_entry(
            world_id=sample_world.id,
            entry_type=WikiEntryType.LOCATION.value,
            title="Dark Forest",
            created_by="ai",
        )
        assert entry.confidence_score == 0.8
        assert entry.created_by == "ai"

    def test_get_entry(self, test_db, sample_wiki_entry):
        svc = WikiService(test_db)
        entry = svc.get_entry(sample_wiki_entry.id)
        assert entry is not None
        assert entry.id == sample_wiki_entry.id

    def test_get_entry_not_found(self, test_db):
        svc = WikiService(test_db)
        assert svc.get_entry("nonexistent") is None

    def test_get_entry_by_slug(self, test_db, sample_world, sample_wiki_entry):
        svc = WikiService(test_db)
        entry = svc.get_entry_by_slug(sample_world.id, "test-character")
        assert entry is not None
        assert entry.id == sample_wiki_entry.id

    def test_get_entries_by_world(self, test_db, sample_world):
        svc = WikiService(test_db)
        # Create multiple entries
        svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice")
        svc.create_entry(sample_world.id, WikiEntryType.LOCATION.value, "Forest")
        svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Bob")

        # All entries
        entries = svc.get_entries_by_world(sample_world.id)
        assert len(entries) == 3

        # Filter by type
        chars = svc.get_entries_by_world(sample_world.id, entry_type=WikiEntryType.CHARACTER.value)
        assert len(chars) == 2

    def test_search_entries(self, test_db, sample_world):
        svc = WikiService(test_db)
        svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice Wonderland", content="curious girl")
        svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Bob Builder", content="handy man")

        results = svc.search_entries(sample_world.id, "alice")
        assert len(results) >= 1
        assert any(e.title == "Alice Wonderland" for e in results)

    def test_update_entry(self, test_db, sample_wiki_entry):
        svc = WikiService(test_db)
        updated = svc.update_entry(sample_wiki_entry.id, {"title": "Updated Character", "content": "New content"})
        assert updated is not None
        assert updated.title == "Updated Character"
        assert updated.slug == "updated-character"
        assert updated.content == "New content"

    def test_update_entry_not_found(self, test_db):
        svc = WikiService(test_db)
        assert svc.update_entry("nonexistent", {"title": "X"}) is None

    def test_delete_entry(self, test_db, sample_wiki_entry):
        svc = WikiService(test_db)
        assert svc.delete_entry(sample_wiki_entry.id) is True
        assert svc.get_entry(sample_wiki_entry.id) is None

    def test_delete_entry_not_found(self, test_db):
        svc = WikiService(test_db)
        assert svc.delete_entry("nonexistent") is False

    def test_slug_generation_special_chars(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry = svc.create_entry(
            world_id=sample_world.id,
            entry_type=WikiEntryType.LOCATION.value,
            title="Mount Doom's Peak!",
        )
        assert entry.slug == "mount-dooms-peak"

    def test_entries_pagination(self, test_db, sample_world):
        svc = WikiService(test_db)
        for i in range(5):
            svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, f"Char {i}")
        page1 = svc.get_entries_by_world(sample_world.id, limit=2, offset=0)
        page2 = svc.get_entries_by_world(sample_world.id, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestWikiChangeQueue:
    """Tests for wiki change approval queue."""

    def test_create_change(self, test_db, sample_world, sample_wiki_entry):
        svc = WikiService(test_db)
        change = svc.create_change(
            world_id=sample_world.id,
            change_type=WikiChangeType.UPDATE.value,
            new_value={"content": "updated content"},
            wiki_entry_id=sample_wiki_entry.id,
            field_changed="content",
            reason="AI detected update",
            confidence=0.85,
        )
        assert change is not None
        assert change.status == WikiChangeStatus.PENDING.value
        assert change.confidence == 0.85

    def test_get_pending_changes(self, test_db, sample_world, sample_wiki_entry):
        svc = WikiService(test_db)
        svc.create_change(sample_world.id, WikiChangeType.UPDATE.value, {"x": 1}, wiki_entry_id=sample_wiki_entry.id)
        svc.create_change(sample_world.id, WikiChangeType.UPDATE.value, {"x": 2}, wiki_entry_id=sample_wiki_entry.id)

        changes = svc.get_pending_changes(sample_world.id)
        assert len(changes) >= 2

    def test_approve_change_update(self, test_db, sample_world, sample_wiki_entry):
        svc = WikiService(test_db)
        change = svc.create_change(
            world_id=sample_world.id,
            change_type=WikiChangeType.UPDATE.value,
            new_value={"content": "AI updated content"},
            wiki_entry_id=sample_wiki_entry.id,
        )
        result = svc.approve_change(change.id, reviewer_note="Looks good")
        assert result is not None
        assert result.content == "AI updated content"

    def test_approve_change_create(self, test_db, sample_world):
        svc = WikiService(test_db)
        change = svc.create_change(
            world_id=sample_world.id,
            change_type=WikiChangeType.CREATE.value,
            new_value={"title": "New AI Entry", "entry_type": WikiEntryType.LOCATION.value},
            proposed_entry={"title": "New AI Entry", "entry_type": WikiEntryType.LOCATION.value, "content": "Discovered location"},
        )
        result = svc.approve_change(change.id)
        assert result is not None
        assert result.title == "New AI Entry"

    def test_reject_change(self, test_db, sample_world, sample_wiki_entry):
        svc = WikiService(test_db)
        change = svc.create_change(
            world_id=sample_world.id,
            change_type=WikiChangeType.UPDATE.value,
            new_value={"content": "bad update"},
            wiki_entry_id=sample_wiki_entry.id,
        )
        assert svc.reject_change(change.id, reviewer_note="Not accurate") is True
        # Verify change status
        rejected = test_db.query(WikiChange).filter(WikiChange.id == change.id).first()
        assert rejected.status == WikiChangeStatus.REJECTED.value


class TestWikiCrossReferences:
    """Tests for wiki cross-references."""

    def test_create_reference(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry_a = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice")
        entry_b = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Bob")

        ref = svc.create_reference(entry_a.id, entry_b.id, WikiReferenceType.ALLY_OF.value)
        assert ref is not None
        assert ref.source_entry_id == entry_a.id
        assert ref.target_entry_id == entry_b.id

    def test_get_entry_references(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry_a = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice")
        entry_b = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Bob")
        svc.create_reference(entry_a.id, entry_b.id, WikiReferenceType.ALLY_OF.value)

        refs = svc.get_entry_references(entry_a.id)
        assert "outgoing" in refs
        assert "incoming" in refs
        assert len(refs["outgoing"]) >= 1

    def test_delete_reference(self, test_db, sample_world):
        svc = WikiService(test_db)
        entry_a = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice")
        entry_b = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Bob")
        ref = svc.create_reference(entry_a.id, entry_b.id, WikiReferenceType.MENTIONS.value)

        assert svc.delete_reference(ref.id) is True
        refs = svc.get_entry_references(entry_a.id)
        assert len(refs["outgoing"]) == 0


class TestMergeEntries:
    """Tests for wiki entry merging."""

    def test_merge_entries(self, test_db, sample_world):
        svc = WikiService(test_db)
        source = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice (draft)", content="Version A")
        target = svc.create_entry(sample_world.id, WikiEntryType.CHARACTER.value, "Alice", content="Version B")

        merged = svc.merge_entries(source.id, target.id, {"content": "Merged content"})
        assert merged is not None
        assert merged.content == "Merged content"
        # Source should be deleted
        assert svc.get_entry(source.id) is None
