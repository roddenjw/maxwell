"""
Tests for CharacterArcService - arc CRUD, templates, and detection.
"""
import pytest
import uuid

from app.services.character_arc_service import CharacterArcService
from app.models.character_arc import CharacterArc, ArcTemplate, ARC_TEMPLATE_DEFINITIONS


class TestArcCRUD:
    """Tests for character arc create/read/update/delete."""

    def test_create_arc(self, test_db, sample_wiki_entry, sample_manuscript):
        svc = CharacterArcService(test_db)
        arc = svc.create_arc(
            wiki_entry_id=sample_wiki_entry.id,
            manuscript_id=sample_manuscript.id,
            arc_template=ArcTemplate.REDEMPTION.value,
            arc_name="Hero's Journey",
        )
        assert arc is not None
        assert arc.arc_template == ArcTemplate.REDEMPTION.value
        assert arc.arc_name == "Hero's Journey"
        assert arc.arc_completion == 0.0
        assert arc.arc_health == "healthy"

    def test_create_arc_custom(self, test_db, sample_wiki_entry, sample_manuscript):
        svc = CharacterArcService(test_db)
        arc = svc.create_arc(
            wiki_entry_id=sample_wiki_entry.id,
            manuscript_id=sample_manuscript.id,
            arc_template=ArcTemplate.CUSTOM.value,
            custom_stages=[
                {"id": "start", "name": "Beginning", "description": "The start"},
                {"id": "end", "name": "Ending", "description": "The end"},
            ],
        )
        assert arc is not None
        assert arc.arc_template == ArcTemplate.CUSTOM.value
        assert len(arc.custom_stages) == 2

    def test_get_arc(self, test_db, sample_character_arc):
        svc = CharacterArcService(test_db)
        arc = svc.get_arc(sample_character_arc.id)
        assert arc is not None
        assert arc.id == sample_character_arc.id

    def test_get_arc_not_found(self, test_db):
        svc = CharacterArcService(test_db)
        assert svc.get_arc("nonexistent") is None

    def test_get_character_arcs(self, test_db, sample_wiki_entry, sample_manuscript):
        svc = CharacterArcService(test_db)
        svc.create_arc(sample_wiki_entry.id, sample_manuscript.id, ArcTemplate.REDEMPTION.value)
        svc.create_arc(sample_wiki_entry.id, sample_manuscript.id, ArcTemplate.FALL.value)

        arcs = svc.get_character_arcs(sample_wiki_entry.id)
        assert len(arcs) >= 2

    def test_get_character_arcs_filtered(self, test_db, sample_wiki_entry, sample_manuscript):
        svc = CharacterArcService(test_db)
        svc.create_arc(sample_wiki_entry.id, sample_manuscript.id, ArcTemplate.REDEMPTION.value)

        arcs = svc.get_character_arcs(sample_wiki_entry.id, manuscript_id=sample_manuscript.id)
        assert len(arcs) >= 1

    def test_get_manuscript_arcs(self, test_db, sample_character_arc, sample_manuscript):
        svc = CharacterArcService(test_db)
        arcs = svc.get_manuscript_arcs(sample_manuscript.id)
        assert len(arcs) >= 1

    def test_update_arc(self, test_db, sample_character_arc):
        svc = CharacterArcService(test_db)
        updated = svc.update_arc(sample_character_arc.id, {
            "arc_name": "Updated Arc Name",
            "arc_completion": 0.5,
            "arc_health": "at_risk",
        })
        assert updated is not None
        assert updated.arc_name == "Updated Arc Name"
        assert updated.arc_completion == 0.5
        assert updated.arc_health == "at_risk"

    def test_update_arc_not_found(self, test_db):
        svc = CharacterArcService(test_db)
        assert svc.update_arc("nonexistent", {"arc_name": "X"}) is None

    def test_delete_arc(self, test_db, sample_character_arc):
        svc = CharacterArcService(test_db)
        assert svc.delete_arc(sample_character_arc.id) is True
        assert svc.get_arc(sample_character_arc.id) is None

    def test_delete_arc_not_found(self, test_db):
        svc = CharacterArcService(test_db)
        assert svc.delete_arc("nonexistent") is False


class TestArcTemplates:
    """Tests for arc template definitions."""

    def test_get_arc_templates(self, test_db):
        svc = CharacterArcService(test_db)
        templates = svc.get_arc_templates()
        assert len(templates) > 0
        # Should have redemption
        names = [t["id"] for t in templates]
        assert ArcTemplate.REDEMPTION.value in names

    def test_get_template_definition(self, test_db):
        svc = CharacterArcService(test_db)
        defn = svc.get_template_definition(ArcTemplate.REDEMPTION.value)
        assert defn is not None
        assert "stages" in defn
        assert len(defn["stages"]) > 0

    def test_get_template_definition_not_found(self, test_db):
        svc = CharacterArcService(test_db)
        assert svc.get_template_definition("nonexistent") is None
