"""
UAT Tests for January 29, 2026 Features - Document Types and Codex Integration

This test module covers:
1. Scrivener-Style Document Types (CHAPTER, FOLDER, CHARACTER_SHEET, NOTES, TITLE_PAGE)
2. Character Sheet Editor
3. Codex Integration - Create from Entity
4. Codex Integration - Link Existing Sheet
5. Bidirectional Sync (Pull/Push from Codex)
6. Visual Link Indicator
7. Notes Editor
8. Title Page Form
9. Drag and Drop / Reordering
"""
import pytest
import uuid
from datetime import datetime

from app.models.manuscript import (
    Chapter,
    Manuscript,
    DOCUMENT_TYPE_CHAPTER,
    DOCUMENT_TYPE_FOLDER,
    DOCUMENT_TYPE_CHARACTER_SHEET,
    DOCUMENT_TYPE_NOTES,
    DOCUMENT_TYPE_TITLE_PAGE,
)
from app.models.entity import Entity


# ========================================
# Feature 1: Scrivener-Style Document Types
# ========================================

class TestDocumentTypes:
    """Test 1.1-1.3: Document type creation, icons, and routing"""

    def test_create_chapter(self, client, sample_manuscript):
        """Test creating a regular CHAPTER document"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Test Chapter",
            "document_type": "CHAPTER"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "CHAPTER"
        assert data["data"]["is_folder"] is False

    def test_create_folder(self, client, sample_manuscript):
        """Test creating a FOLDER document"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Test Folder",
            "document_type": "FOLDER",
            "is_folder": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "FOLDER"
        assert data["data"]["is_folder"] is True

    def test_create_character_sheet(self, client, sample_manuscript):
        """Test creating a CHARACTER_SHEET document"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Character - Hero",
            "document_type": "CHARACTER_SHEET",
            "document_metadata": {
                "name": "Hero",
                "aliases": ["The Chosen One"],
                "role": "Protagonist"
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "CHARACTER_SHEET"
        assert data["data"]["document_metadata"]["name"] == "Hero"
        assert data["data"]["document_metadata"]["role"] == "Protagonist"

    def test_create_notes_document(self, client, sample_manuscript):
        """Test creating a NOTES document"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Research Notes",
            "document_type": "NOTES",
            "content": "Some research notes about the world",
            "document_metadata": {
                "tags": ["worldbuilding", "history"],
                "category": "Research"
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "NOTES"
        assert "worldbuilding" in data["data"]["document_metadata"]["tags"]
        assert data["data"]["document_metadata"]["category"] == "Research"

    def test_create_title_page(self, client, sample_manuscript):
        """Test creating a TITLE_PAGE document"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Title Page",
            "document_type": "TITLE_PAGE",
            "document_metadata": {
                "title": "The Epic Novel",
                "subtitle": "A Tale of Adventure",
                "author": "Jane Writer",
                "synopsis": "An epic tale...",
                "dedication": "To my readers",
                "epigraph": "In the beginning...",
                "epigraph_attribution": "Ancient Text"
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "TITLE_PAGE"
        assert data["data"]["document_metadata"]["title"] == "The Epic Novel"
        assert data["data"]["document_metadata"]["author"] == "Jane Writer"

    def test_nested_documents_in_folder(self, client, sample_manuscript):
        """Test creating documents inside a folder"""
        # Create folder
        folder_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Characters Folder",
            "document_type": "FOLDER",
            "is_folder": True
        })
        folder_id = folder_response.json()["data"]["id"]

        # Create character sheet inside folder
        sheet_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Hero Character",
            "document_type": "CHARACTER_SHEET",
            "parent_id": folder_id,
            "order_index": 0
        })
        assert sheet_response.status_code == 200
        sheet_data = sheet_response.json()["data"]
        assert sheet_data["parent_id"] == folder_id

        # Verify tree structure
        tree_response = client.get(f"/api/chapters/manuscript/{sample_manuscript.id}/tree")
        tree = tree_response.json()["data"]
        folder = next(item for item in tree if item["id"] == folder_id)
        assert len(folder["children"]) == 1
        assert folder["children"][0]["document_type"] == "CHARACTER_SHEET"

    def test_document_type_in_tree(self, client, sample_manuscript):
        """Test that document types are included in tree response"""
        # Create one of each type
        client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Chapter 1",
            "document_type": "CHAPTER",
            "order_index": 0
        })
        client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Notes",
            "document_type": "NOTES",
            "order_index": 1
        })

        tree_response = client.get(f"/api/chapters/manuscript/{sample_manuscript.id}/tree")
        tree = tree_response.json()["data"]

        assert len(tree) == 2
        doc_types = {item["document_type"] for item in tree}
        assert "CHAPTER" in doc_types
        assert "NOTES" in doc_types


# ========================================
# Feature 2 & 3: Character Sheet Editor & Create from Entity
# ========================================

class TestCharacterSheetEditor:
    """Test 2.1-2.2 and 3.1-3.2: Character sheet form and entity linking"""

    def test_character_sheet_form_sections(self, client, sample_manuscript):
        """Test that character sheet saves all form sections"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Full Character",
            "document_type": "CHARACTER_SHEET",
            "document_metadata": {
                "name": "Aria",
                "aliases": ["The Shadow", "Lady A"],
                "role": "Protagonist",
                "physical": {
                    "age": "28",
                    "appearance": "Tall with dark hair",
                    "distinguishing_features": "Scar on left cheek"
                },
                "personality": {
                    "traits": ["Brave", "Stubborn", "Loyal"],
                    "strengths": "Strategic thinking",
                    "flaws": "Too trusting"
                },
                "backstory": {
                    "origin": "Born in a small village",
                    "key_events": "Lost family in the war",
                    "secrets": "Has a hidden twin"
                },
                "motivation": {
                    "want": "Revenge against the empire",
                    "need": "To learn forgiveness"
                },
                "notes": "Important character arc in Act 2"
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]

        # Verify all sections saved
        metadata = data["document_metadata"]
        assert metadata["name"] == "Aria"
        assert "The Shadow" in metadata["aliases"]
        assert metadata["role"] == "Protagonist"
        assert metadata["physical"]["age"] == "28"
        assert "Brave" in metadata["personality"]["traits"]
        assert metadata["backstory"]["secrets"] == "Has a hidden twin"
        assert metadata["motivation"]["want"] == "Revenge against the empire"

    def test_create_from_entity(self, client, sample_manuscript, sample_entity):
        """Test creating a character sheet from a Codex entity"""
        response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["document_type"] == "CHARACTER_SHEET"
        assert data["linked_entity_id"] == sample_entity.id
        assert data["document_metadata"]["name"] == sample_entity.name
        assert "Character Sheet" in data["title"]

    def test_create_from_entity_only_characters(self, client, test_db, sample_manuscript):
        """Test that only CHARACTER entities can create character sheets"""
        # Create a LOCATION entity
        location = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=sample_manuscript.id,
            name="Test City",
            type="LOCATION",
            attributes={"description": "A bustling metropolis"}
        )
        test_db.add(location)
        test_db.commit()

        # Try to create character sheet from location
        response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": location.id
        })
        assert response.status_code == 400
        assert "CHARACTER" in response.json()["detail"]

    def test_linked_entity_indicator(self, client, sample_manuscript, sample_entity):
        """Test that linked_entity_id is returned in tree"""
        # Create linked character sheet
        client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })

        # Create unlinked character sheet
        client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Unlinked Character",
            "document_type": "CHARACTER_SHEET"
        })

        tree_response = client.get(f"/api/chapters/manuscript/{sample_manuscript.id}/tree")
        tree = tree_response.json()["data"]

        linked = [item for item in tree if item.get("linked_entity_id")]
        unlinked = [item for item in tree if not item.get("linked_entity_id")]

        assert len(linked) == 1
        assert linked[0]["linked_entity_id"] == sample_entity.id
        assert len(unlinked) == 1


# ========================================
# Feature 4: Link Existing Sheet to Entity
# ========================================

class TestLinkExistingSheet:
    """Test 4.1-4.2: Link and unlink existing character sheets"""

    def test_link_existing_sheet(self, client, sample_manuscript, sample_entity):
        """Test linking an existing character sheet to an entity"""
        # Create unlinked character sheet
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Unlinked Character",
            "document_type": "CHARACTER_SHEET",
            "document_metadata": {"name": "Original Name"}
        })
        chapter_id = create_response.json()["data"]["id"]

        # Link to entity
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "linked_entity_id": sample_entity.id,
            "document_metadata": {
                "name": sample_entity.name,
                "synced_at": datetime.utcnow().isoformat()
            }
        })
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["linked_entity_id"] == sample_entity.id

    def test_unlink_sheet_preserves_data(self, client, sample_manuscript, sample_entity):
        """Test that unlinking preserves character data"""
        # Create linked character sheet
        create_response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        chapter_id = create_response.json()["data"]["id"]
        original_name = create_response.json()["data"]["document_metadata"]["name"]

        # Unlink by setting linked_entity_id to None
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "linked_entity_id": None
        })
        assert update_response.status_code == 200
        data = update_response.json()["data"]

        # Verify unlinked but data preserved
        assert data["linked_entity_id"] is None
        assert data["document_metadata"]["name"] == original_name


# ========================================
# Feature 5: Bidirectional Sync
# ========================================

class TestBidirectionalSync:
    """Test 5.1-5.3: Pull from and push to Codex"""

    def test_pull_from_codex(self, client, test_db, sample_manuscript, sample_entity):
        """Test pulling latest entity data into character sheet"""
        # Create linked character sheet
        create_response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update entity directly in database
        sample_entity.name = "Updated Name"
        sample_entity.aliases = ["New Alias"]
        sample_entity.attributes = {"age": 35}
        test_db.commit()

        # Sync from entity
        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=from_entity"
        )
        assert sync_response.status_code == 200
        data = sync_response.json()["data"]

        # Verify sheet updated
        assert data["document_metadata"]["name"] == "Updated Name"
        assert "New Alias" in data["document_metadata"]["aliases"]
        assert data["document_metadata"]["attributes"]["age"] == 35

    def test_push_to_codex(self, client, test_db, sample_manuscript, sample_entity):
        """Test pushing character sheet changes to entity"""
        # Create linked character sheet
        create_response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update character sheet
        client.put(f"/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "name": "Sheet Updated Name",
                "aliases": ["Sheet Alias"],
                "attributes": {"occupation": "Warrior"},
                "template_data": {"role": "Antagonist"}
            }
        })

        # Sync to entity
        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=to_entity"
        )
        assert sync_response.status_code == 200

        # Verify entity updated
        test_db.refresh(sample_entity)
        assert sample_entity.name == "Sheet Updated Name"
        assert "Sheet Alias" in sample_entity.aliases
        assert sample_entity.attributes["occupation"] == "Warrior"

    def test_sync_requires_linked_entity(self, client, sample_manuscript):
        """Test that sync fails for unlinked sheets"""
        # Create unlinked character sheet
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Unlinked Character",
            "document_type": "CHARACTER_SHEET"
        })
        chapter_id = create_response.json()["data"]["id"]

        # Try to sync
        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=from_entity"
        )
        assert sync_response.status_code == 400
        assert "not linked" in sync_response.json()["detail"]

    def test_sync_only_character_sheets(self, client, sample_manuscript):
        """Test that sync only works for CHARACTER_SHEET documents"""
        # Create a regular chapter
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Regular Chapter",
            "document_type": "CHAPTER"
        })
        chapter_id = create_response.json()["data"]["id"]

        # Try to sync
        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=from_entity"
        )
        assert sync_response.status_code == 400
        assert "CHARACTER_SHEET" in sync_response.json()["detail"]


# ========================================
# Feature 7: Notes Editor
# ========================================

class TestNotesEditor:
    """Test 7.1-7.3: Notes editing, tags, and categories"""

    def test_notes_basic_editing(self, client, sample_manuscript):
        """Test creating and updating notes content"""
        # Create notes
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Research Notes",
            "document_type": "NOTES",
            "content": "Initial notes content"
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update content
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "content": "Updated notes with more detail about the world"
        })
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert "Updated notes" in data["content"]
        assert data["word_count"] > 0

    def test_notes_tags(self, client, sample_manuscript):
        """Test notes tag functionality"""
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Tagged Notes",
            "document_type": "NOTES",
            "document_metadata": {
                "tags": ["worldbuilding", "magic", "history"]
            }
        })
        chapter_id = create_response.json()["data"]["id"]

        # Get notes and verify tags
        get_response = client.get(f"/api/chapters/{chapter_id}")
        data = get_response.json()["data"]
        assert len(data["document_metadata"]["tags"]) == 3
        assert "magic" in data["document_metadata"]["tags"]

        # Update tags
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "tags": ["worldbuilding", "politics"]
            }
        })
        updated_tags = update_response.json()["data"]["document_metadata"]["tags"]
        assert len(updated_tags) == 2
        assert "politics" in updated_tags
        assert "magic" not in updated_tags

    def test_notes_category(self, client, sample_manuscript):
        """Test notes category selection"""
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Categorized Notes",
            "document_type": "NOTES",
            "document_metadata": {
                "category": "Research"
            }
        })
        chapter_id = create_response.json()["data"]["id"]

        # Verify category
        get_response = client.get(f"/api/chapters/{chapter_id}")
        assert get_response.json()["data"]["document_metadata"]["category"] == "Research"

        # Update category
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "category": "Worldbuilding"
            }
        })
        assert update_response.json()["data"]["document_metadata"]["category"] == "Worldbuilding"


# ========================================
# Feature 8: Title Page Form
# ========================================

class TestTitlePageForm:
    """Test 8.1: Title page form fields"""

    def test_title_page_all_fields(self, client, sample_manuscript):
        """Test that all title page fields save correctly"""
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Title Page",
            "document_type": "TITLE_PAGE",
            "document_metadata": {
                "title": "The Great Adventure",
                "subtitle": "A Tale of Heroes",
                "author": "John Author",
                "author_bio": "John is an award-winning writer.",
                "synopsis": "In a world where magic is forbidden...",
                "dedication": "To my family",
                "epigraph": "All that glitters is not gold.",
                "epigraph_attribution": "William Shakespeare"
            }
        })
        assert create_response.status_code == 200
        data = create_response.json()["data"]

        # Verify all fields
        metadata = data["document_metadata"]
        assert metadata["title"] == "The Great Adventure"
        assert metadata["subtitle"] == "A Tale of Heroes"
        assert metadata["author"] == "John Author"
        assert metadata["author_bio"] == "John is an award-winning writer."
        assert "magic is forbidden" in metadata["synopsis"]
        assert metadata["dedication"] == "To my family"
        assert metadata["epigraph"] == "All that glitters is not gold."
        assert metadata["epigraph_attribution"] == "William Shakespeare"

    def test_title_page_update(self, client, sample_manuscript):
        """Test updating title page fields"""
        # Create title page
        create_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Title Page",
            "document_type": "TITLE_PAGE",
            "document_metadata": {
                "title": "Working Title"
            }
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update with more fields
        update_response = client.put(f"/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "title": "Final Title",
                "subtitle": "Added Later",
                "author": "Added Author"
            }
        })
        data = update_response.json()["data"]
        assert data["document_metadata"]["title"] == "Final Title"
        assert data["document_metadata"]["subtitle"] == "Added Later"


# ========================================
# Feature 9: Drag and Drop / Reordering
# ========================================

class TestReordering:
    """Test 9.1-9.2: Drag and drop reordering"""

    def test_reorder_different_types(self, client, sample_manuscript):
        """Test reordering documents of different types"""
        # Create documents in initial order
        ids = []
        for i, doc_type in enumerate(["CHAPTER", "CHARACTER_SHEET", "NOTES"]):
            response = client.post("/api/chapters", json={
                "manuscript_id": sample_manuscript.id,
                "title": f"Doc {i}",
                "document_type": doc_type,
                "order_index": i
            })
            ids.append(response.json()["data"]["id"])

        # Reorder: reverse the order
        reorder_response = client.post("/api/chapters/reorder", json={
            "chapter_ids": list(reversed(ids))
        })
        assert reorder_response.status_code == 200

        # Verify new order
        tree_response = client.get(f"/api/chapters/manuscript/{sample_manuscript.id}/tree")
        tree = tree_response.json()["data"]
        ordered_ids = [item["id"] for item in tree]
        assert ordered_ids == list(reversed(ids))

    def test_move_into_folder(self, client, sample_manuscript):
        """Test moving documents into a folder"""
        # Create folder
        folder_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Folder",
            "document_type": "FOLDER",
            "is_folder": True,
            "order_index": 0
        })
        folder_id = folder_response.json()["data"]["id"]

        # Create document at root level
        doc_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Document",
            "document_type": "CHAPTER",
            "order_index": 1
        })
        doc_id = doc_response.json()["data"]["id"]

        # Move document into folder
        move_response = client.put(f"/api/chapters/{doc_id}", json={
            "parent_id": folder_id,
            "order_index": 0
        })
        assert move_response.status_code == 200
        assert move_response.json()["data"]["parent_id"] == folder_id

        # Verify in tree
        tree_response = client.get(f"/api/chapters/manuscript/{sample_manuscript.id}/tree")
        tree = tree_response.json()["data"]

        # Find folder and check children
        folder = next(item for item in tree if item["id"] == folder_id)
        assert len(folder["children"]) == 1
        assert folder["children"][0]["id"] == doc_id

    def test_move_out_of_folder(self, client, sample_manuscript):
        """Test moving document out of folder to root"""
        # Create folder with document inside
        folder_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Folder",
            "document_type": "FOLDER",
            "is_folder": True
        })
        folder_id = folder_response.json()["data"]["id"]

        doc_response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Document",
            "document_type": "CHAPTER",
            "parent_id": folder_id
        })
        doc_id = doc_response.json()["data"]["id"]

        # Move to root
        move_response = client.put(f"/api/chapters/{doc_id}", json={
            "parent_id": None,
            "order_index": 0
        })
        assert move_response.status_code == 200
        assert move_response.json()["data"]["parent_id"] is None


# ========================================
# Edge Cases and Error Handling
# ========================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_create_entity_not_found(self, client, sample_manuscript):
        """Test creating from non-existent entity"""
        response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": str(uuid.uuid4())  # Non-existent
        })
        assert response.status_code == 404

    def test_sync_entity_not_found(self, client, test_db, sample_manuscript, sample_entity):
        """Test syncing when linked entity has been deleted"""
        # Create linked sheet
        create_response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        chapter_id = create_response.json()["data"]["id"]

        # Delete entity
        test_db.delete(sample_entity)
        test_db.commit()

        # Try to sync
        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=from_entity"
        )
        assert sync_response.status_code == 404

    def test_invalid_sync_direction(self, client, sample_manuscript, sample_entity):
        """Test invalid sync direction parameter"""
        create_response = client.post("/api/chapters/from-entity", json={
            "manuscript_id": sample_manuscript.id,
            "entity_id": sample_entity.id
        })
        chapter_id = create_response.json()["data"]["id"]

        sync_response = client.put(
            f"/api/chapters/{chapter_id}/sync-entity?direction=invalid"
        )
        assert sync_response.status_code == 400

    def test_default_document_type_is_chapter(self, client, sample_manuscript):
        """Test that default document type is CHAPTER when not specified"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "No Type Specified"
        })
        assert response.status_code == 200
        assert response.json()["data"]["document_type"] == "CHAPTER"

    def test_folder_word_count_is_zero(self, client, sample_manuscript):
        """Test that folders have word count of 0"""
        response = client.post("/api/chapters", json={
            "manuscript_id": sample_manuscript.id,
            "title": "Folder",
            "document_type": "FOLDER",
            "is_folder": True,
            "content": "This should not count"
        })
        assert response.status_code == 200
        assert response.json()["data"]["word_count"] == 0
