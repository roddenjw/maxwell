"""
Tests for WorldService - world/series CRUD, manuscript assignment, entity scoping.
"""
import pytest
import uuid

from app.services.world_service import WorldService
from app.models.world import World, Series
from app.models.manuscript import Manuscript


@pytest.fixture
def svc():
    """Create a WorldService instance."""
    return WorldService()


class TestWorldCRUD:
    """Tests for World create/read/update/delete."""

    def test_create_world(self, test_db, svc):
        world = svc.create_world(test_db, "Middle Earth", "Tolkien's world", {"genre": "fantasy"})
        assert world is not None
        assert world.name == "Middle Earth"
        assert world.settings == {"genre": "fantasy"}

    def test_get_world(self, test_db, svc, sample_world):
        world = svc.get_world(test_db, sample_world.id)
        assert world is not None
        assert world.name == sample_world.name

    def test_get_world_not_found(self, test_db, svc):
        assert svc.get_world(test_db, "nonexistent") is None

    def test_list_worlds(self, test_db, svc):
        svc.create_world(test_db, "World A")
        svc.create_world(test_db, "World B")
        worlds = svc.list_worlds(test_db)
        assert len(worlds) >= 2

    def test_update_world(self, test_db, svc, sample_world):
        updated = svc.update_world(test_db, sample_world.id, name="Updated World")
        assert updated is not None
        assert updated.name == "Updated World"

    def test_update_world_not_found(self, test_db, svc):
        assert svc.update_world(test_db, "nonexistent", name="X") is None

    def test_delete_world(self, test_db, svc, sample_world):
        assert svc.delete_world(test_db, sample_world.id) is True
        assert svc.get_world(test_db, sample_world.id) is None

    def test_delete_world_not_found(self, test_db, svc):
        assert svc.delete_world(test_db, "nonexistent") is False


class TestSeriesCRUD:
    """Tests for Series create/read/update/delete."""

    def test_create_series(self, test_db, svc, sample_world):
        series = svc.create_series(test_db, sample_world.id, "Book Series 1", "First series")
        assert series is not None
        assert series.name == "Book Series 1"
        assert series.world_id == sample_world.id

    def test_create_series_invalid_world(self, test_db, svc):
        series = svc.create_series(test_db, "nonexistent", "Bad Series")
        assert series is None

    def test_get_series(self, test_db, svc, sample_series):
        series = svc.get_series(test_db, sample_series.id)
        assert series is not None
        assert series.name == sample_series.name

    def test_list_series_in_world(self, test_db, svc, sample_world):
        svc.create_series(test_db, sample_world.id, "Series A", order_index=0)
        svc.create_series(test_db, sample_world.id, "Series B", order_index=1)
        series_list = svc.list_series_in_world(test_db, sample_world.id)
        assert len(series_list) >= 2

    def test_update_series(self, test_db, svc, sample_series):
        updated = svc.update_series(test_db, sample_series.id, name="Updated Series")
        assert updated is not None
        assert updated.name == "Updated Series"

    def test_delete_series(self, test_db, svc, sample_series):
        assert svc.delete_series(test_db, sample_series.id) is True


class TestManuscriptAssignment:
    """Tests for assigning manuscripts to series."""

    def test_assign_manuscript_to_series(self, test_db, svc, sample_manuscript, sample_series):
        result = svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        assert result is not None
        assert result.series_id == sample_series.id

    def test_remove_manuscript_from_series(self, test_db, svc, sample_manuscript, sample_series):
        svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        result = svc.remove_manuscript_from_series(test_db, sample_manuscript.id)
        assert result is not None
        assert result.series_id is None

    def test_list_manuscripts_in_series(self, test_db, svc, sample_manuscript, sample_series):
        svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        manuscripts = svc.list_manuscripts_in_series(test_db, sample_series.id)
        assert len(manuscripts) >= 1

    def test_list_manuscripts_in_world(self, test_db, svc, sample_manuscript, sample_world, sample_series):
        svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        manuscripts = svc.list_manuscripts_in_world(test_db, sample_world.id)
        assert len(manuscripts) >= 1


class TestWorldHelpers:
    """Tests for helper methods."""

    def test_get_world_for_manuscript(self, test_db, svc, sample_manuscript, sample_world, sample_series):
        svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        world = svc.get_world_for_manuscript(test_db, sample_manuscript.id)
        assert world is not None
        assert world.id == sample_world.id

    def test_get_world_for_manuscript_no_series(self, test_db, svc, sample_manuscript):
        world = svc.get_world_for_manuscript(test_db, sample_manuscript.id)
        assert world is None

    def test_ensure_manuscript_has_world(self, test_db, svc, sample_manuscript):
        world = svc.ensure_manuscript_has_world(test_db, sample_manuscript.id)
        assert world is not None
        assert world.name  # Should have a name
        # Verify manuscript is now assigned
        found_world = svc.get_world_for_manuscript(test_db, sample_manuscript.id)
        assert found_world is not None
        assert found_world.id == world.id

    def test_ensure_manuscript_already_has_world(self, test_db, svc, sample_manuscript, sample_world, sample_series):
        svc.assign_manuscript_to_series(test_db, sample_manuscript.id, sample_series.id)
        world = svc.ensure_manuscript_has_world(test_db, sample_manuscript.id)
        assert world.id == sample_world.id
