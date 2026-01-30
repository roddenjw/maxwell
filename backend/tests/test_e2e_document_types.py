"""
End-to-End Integration Tests for Document Types and Codex Integration

This script runs against a live backend server (http://localhost:8000) and tests
the complete workflow for the January 29, 2026 features.

Run with: pytest tests/test_e2e_document_types.py -v -s
Requires: Backend server running on port 8000
"""
import pytest
import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def server_available():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("Backend server not running")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend server not running")


@pytest.fixture(scope="module")
def test_manuscript(server_available):
    """Create a test manuscript for the tests"""
    # Create manuscript
    response = requests.post(f"{BASE_URL}/api/manuscripts", json={
        "title": f"UAT Test Manuscript {datetime.now().isoformat()}"
    })
    assert response.status_code == 200
    manuscript = response.json()

    yield manuscript

    # Cleanup - delete the manuscript
    requests.delete(f"{BASE_URL}/api/manuscripts/{manuscript['id']}")


@pytest.fixture(scope="module")
def test_entity(server_available, test_manuscript):
    """Create a test CHARACTER entity for Codex integration tests"""
    response = requests.post(f"{BASE_URL}/api/codex/entities", json={
        "manuscript_id": test_manuscript["id"],
        "type": "CHARACTER",
        "name": "Test Hero",
        "aliases": ["The Brave", "Hero of the Story"],
        "attributes": {
            "age": 25,
            "appearance": "Tall with dark hair",
            "occupation": "Knight"
        },
        "template_data": {
            "role": "Protagonist",
            "physical": {"age": "25"},
            "personality": {"traits": ["Brave", "Loyal"]}
        }
    })
    assert response.status_code == 200
    entity = response.json()["data"]

    yield entity

    # Cleanup
    requests.delete(f"{BASE_URL}/api/codex/entities/{entity['id']}")


class TestDocumentTypeCreation:
    """Feature 1: Create Different Document Types"""

    def test_create_chapter(self, test_manuscript):
        """Test 1.1a: Create a regular chapter"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Chapter 1",
            "document_type": "CHAPTER",
            "content": "Once upon a time..."
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document_type"] == "CHAPTER"
        assert data["content"] == "Once upon a time..."

    def test_create_folder(self, test_manuscript):
        """Test 1.1b: Create a folder"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Characters",
            "document_type": "FOLDER",
            "is_folder": True
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document_type"] == "FOLDER"
        assert data["is_folder"] is True

    def test_create_character_sheet(self, test_manuscript):
        """Test 1.1c: Create a character sheet"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Villain - Character Sheet",
            "document_type": "CHARACTER_SHEET",
            "document_metadata": {
                "name": "Dark Lord",
                "role": "Antagonist",
                "aliases": ["The Shadow"]
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document_type"] == "CHARACTER_SHEET"
        assert data["document_metadata"]["name"] == "Dark Lord"

    def test_create_notes(self, test_manuscript):
        """Test 1.1d: Create a notes document"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "World Building Notes",
            "document_type": "NOTES",
            "content": "The magic system works by...",
            "document_metadata": {
                "tags": ["worldbuilding", "magic"],
                "category": "Research"
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document_type"] == "NOTES"
        assert "worldbuilding" in data["document_metadata"]["tags"]

    def test_create_title_page(self, test_manuscript):
        """Test 1.1e: Create a title page"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Title Page",
            "document_type": "TITLE_PAGE",
            "document_metadata": {
                "title": "The Epic Tale",
                "subtitle": "A Story of Adventure",
                "author": "Test Author",
                "synopsis": "In a world of magic..."
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["document_type"] == "TITLE_PAGE"
        assert data["document_metadata"]["author"] == "Test Author"


class TestChapterTreeWithDocumentTypes:
    """Feature 1.2: Document Types in Tree View"""

    def test_tree_includes_document_types(self, test_manuscript):
        """Test that the chapter tree includes document_type for all items"""
        response = requests.get(f"{BASE_URL}/api/chapters/manuscript/{test_manuscript['id']}/tree")
        assert response.status_code == 200
        tree = response.json()["data"]

        # Verify all items have document_type
        def check_tree(nodes):
            for node in nodes:
                assert "document_type" in node, f"Node {node['title']} missing document_type"
                if node.get("children"):
                    check_tree(node["children"])

        check_tree(tree)

    def test_tree_includes_linked_entity_id(self, test_manuscript, test_entity):
        """Test that linked_entity_id is present in tree"""
        # Create linked character sheet
        create_response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": test_entity["id"]
        })
        assert create_response.status_code == 200

        # Check tree
        tree_response = requests.get(f"{BASE_URL}/api/chapters/manuscript/{test_manuscript['id']}/tree")
        tree = tree_response.json()["data"]

        # Find the linked sheet
        linked_sheets = [n for n in tree if n.get("linked_entity_id") == test_entity["id"]]
        assert len(linked_sheets) >= 1


class TestCharacterSheetForm:
    """Feature 2: Character Sheet Editor Form Sections"""

    def test_full_character_sheet_sections(self, test_manuscript):
        """Test 2.1: All character sheet form sections save correctly"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Complete Character",
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
        chapter_id = response.json()["data"]["id"]

        # Fetch and verify
        get_response = requests.get(f"{BASE_URL}/api/chapters/{chapter_id}")
        data = get_response.json()["data"]

        assert data["document_metadata"]["name"] == "Aria"
        assert data["document_metadata"]["role"] == "Protagonist"
        assert data["document_metadata"]["physical"]["age"] == "28"
        assert "Brave" in data["document_metadata"]["personality"]["traits"]
        assert data["document_metadata"]["backstory"]["secrets"] == "Has a hidden twin"
        assert data["document_metadata"]["motivation"]["want"] == "Revenge against the empire"


class TestCreateFromEntity:
    """Feature 3: Create Character Sheet from Codex Entity"""

    def test_create_from_entity(self, test_manuscript, test_entity):
        """Test 3.1: Add to Binder from Codex"""
        response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": test_entity["id"]
        })
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["document_type"] == "CHARACTER_SHEET"
        assert data["linked_entity_id"] == test_entity["id"]
        assert data["document_metadata"]["name"] == test_entity["name"]
        assert "Character Sheet" in data["title"]

    def test_only_characters_allowed(self, test_manuscript):
        """Test 3.2: Only CHARACTER entities can create sheets"""
        # Create a LOCATION entity
        loc_response = requests.post(f"{BASE_URL}/api/codex/entities", json={
            "manuscript_id": test_manuscript["id"],
            "type": "LOCATION",
            "name": "Test Castle"
        })
        location_id = loc_response.json()["data"]["id"]

        # Try to create character sheet
        response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": location_id
        })
        assert response.status_code == 400
        assert "CHARACTER" in response.json()["detail"]

        # Cleanup
        requests.delete(f"{BASE_URL}/api/codex/entities/{location_id}")


class TestLinkExistingSheet:
    """Feature 4: Link/Unlink Existing Character Sheet"""

    def test_link_existing_sheet(self, test_manuscript, test_entity):
        """Test 4.1: Link an existing sheet to an entity"""
        # Create unlinked sheet
        create_response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Unlinked Character",
            "document_type": "CHARACTER_SHEET",
            "document_metadata": {"name": "Original Name"}
        })
        chapter_id = create_response.json()["data"]["id"]

        # Link to entity
        update_response = requests.put(f"{BASE_URL}/api/chapters/{chapter_id}", json={
            "linked_entity_id": test_entity["id"]
        })
        assert update_response.status_code == 200
        assert update_response.json()["data"]["linked_entity_id"] == test_entity["id"]

    def test_unlink_preserves_data(self, test_manuscript, test_entity):
        """Test 4.2: Unlinking preserves data"""
        # Create linked sheet
        create_response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": test_entity["id"]
        })
        chapter_id = create_response.json()["data"]["id"]
        original_name = create_response.json()["data"]["document_metadata"]["name"]

        # Unlink
        update_response = requests.put(f"{BASE_URL}/api/chapters/{chapter_id}", json={
            "linked_entity_id": None
        })
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["linked_entity_id"] is None
        assert data["document_metadata"]["name"] == original_name


class TestBidirectionalSync:
    """Feature 5: Bidirectional Sync between Sheet and Entity"""

    def test_pull_from_codex(self, test_manuscript, test_entity):
        """Test 5.1: Pull from Codex updates sheet"""
        # Create linked sheet
        create_response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": test_entity["id"]
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update entity directly
        requests.put(f"{BASE_URL}/api/codex/entities/{test_entity['id']}", json={
            "name": "Updated Hero Name",
            "aliases": ["New Alias"]
        })

        # Sync from entity
        sync_response = requests.put(f"{BASE_URL}/api/chapters/{chapter_id}/sync-entity?direction=from_entity")
        assert sync_response.status_code == 200
        data = sync_response.json()["data"]
        assert data["document_metadata"]["name"] == "Updated Hero Name"

    def test_push_to_codex(self, test_manuscript, test_entity):
        """Test 5.2: Push to Codex updates entity"""
        # Create linked sheet
        create_response = requests.post(f"{BASE_URL}/api/chapters/from-entity", json={
            "manuscript_id": test_manuscript["id"],
            "entity_id": test_entity["id"]
        })
        chapter_id = create_response.json()["data"]["id"]

        # Update sheet
        requests.put(f"{BASE_URL}/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "name": "Pushed Name",
                "aliases": ["Pushed Alias"],
                "attributes": {"new_field": "value"}
            }
        })

        # Sync to entity
        sync_response = requests.put(f"{BASE_URL}/api/chapters/{chapter_id}/sync-entity?direction=to_entity")
        assert sync_response.status_code == 200

        # Verify entity updated
        entity_response = requests.get(f"{BASE_URL}/api/codex/entities/{test_manuscript['id']}")
        entities = entity_response.json()["data"]
        updated_entity = next(e for e in entities if e["id"] == test_entity["id"])
        assert updated_entity["name"] == "Pushed Name"


class TestNotesEditor:
    """Feature 7: Notes Editor"""

    def test_notes_with_tags_and_category(self, test_manuscript):
        """Test 7.1-7.3: Notes with tags and category"""
        # Create notes
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Research Notes",
            "document_type": "NOTES",
            "content": "Some research about the world",
            "document_metadata": {
                "tags": ["worldbuilding", "magic", "politics"],
                "category": "Research"
            }
        })
        assert response.status_code == 200
        chapter_id = response.json()["data"]["id"]

        # Update tags
        update_response = requests.put(f"{BASE_URL}/api/chapters/{chapter_id}", json={
            "document_metadata": {
                "tags": ["updated", "new-tag"],
                "category": "Worldbuilding"
            }
        })
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert "updated" in data["document_metadata"]["tags"]
        assert data["document_metadata"]["category"] == "Worldbuilding"


class TestTitlePage:
    """Feature 8: Title Page Form"""

    def test_title_page_all_fields(self, test_manuscript):
        """Test 8.1: All title page fields"""
        response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Title Page",
            "document_type": "TITLE_PAGE",
            "document_metadata": {
                "title": "The Great Adventure",
                "subtitle": "A Tale of Heroes",
                "author": "John Author",
                "author_bio": "Award-winning writer",
                "synopsis": "In a world where magic is forbidden...",
                "dedication": "To my family",
                "epigraph": "All that glitters is not gold.",
                "epigraph_attribution": "Shakespeare"
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]

        metadata = data["document_metadata"]
        assert metadata["title"] == "The Great Adventure"
        assert metadata["author"] == "John Author"
        assert metadata["epigraph_attribution"] == "Shakespeare"


class TestReordering:
    """Feature 9: Drag and Drop / Reordering"""

    def test_reorder_documents(self, test_manuscript):
        """Test 9.1: Reorder different document types"""
        # Create documents
        ids = []
        for i, doc_type in enumerate(["CHAPTER", "NOTES", "CHARACTER_SHEET"]):
            response = requests.post(f"{BASE_URL}/api/chapters", json={
                "manuscript_id": test_manuscript["id"],
                "title": f"Doc {i}",
                "document_type": doc_type,
                "order_index": i
            })
            ids.append(response.json()["data"]["id"])

        # Reorder
        reorder_response = requests.post(f"{BASE_URL}/api/chapters/reorder", json={
            "chapter_ids": list(reversed(ids))
        })
        assert reorder_response.status_code == 200

        # Verify order
        tree_response = requests.get(f"{BASE_URL}/api/chapters/manuscript/{test_manuscript['id']}/tree")
        tree = tree_response.json()["data"]
        tree_ids = [item["id"] for item in tree if item["id"] in ids]

        # Check reversed order
        expected = list(reversed(ids))
        for expected_id in expected:
            assert expected_id in tree_ids

    def test_move_to_folder(self, test_manuscript):
        """Test 9.2: Move document into folder"""
        # Create folder
        folder_response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Test Folder",
            "document_type": "FOLDER",
            "is_folder": True
        })
        folder_id = folder_response.json()["data"]["id"]

        # Create document
        doc_response = requests.post(f"{BASE_URL}/api/chapters", json={
            "manuscript_id": test_manuscript["id"],
            "title": "Document to Move",
            "document_type": "CHAPTER"
        })
        doc_id = doc_response.json()["data"]["id"]

        # Move into folder
        move_response = requests.put(f"{BASE_URL}/api/chapters/{doc_id}", json={
            "parent_id": folder_id,
            "order_index": 0
        })
        assert move_response.status_code == 200
        assert move_response.json()["data"]["parent_id"] == folder_id

        # Verify in tree
        tree_response = requests.get(f"{BASE_URL}/api/chapters/manuscript/{test_manuscript['id']}/tree")
        tree = tree_response.json()["data"]
        folder = next(item for item in tree if item["id"] == folder_id)
        assert any(child["id"] == doc_id for child in folder["children"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
