"""
Test chapter API serialization to prevent SQLAlchemy metadata leaks

This test file specifically addresses the regression where SQLAlchemy's
internal metadata (_sa_instance_state) was leaking into API responses,
corrupting the JSON and causing text to disappear in the frontend.
"""
import pytest
from fastapi.testclient import TestClient


class TestChapterSerializationRegression:
    """Tests to prevent SQLAlchemy metadata from appearing in API responses"""

    def test_get_chapter_no_sqlalchemy_metadata(self, client, sample_chapter):
        """
        CRITICAL: Verify chapter responses don't contain SQLAlchemy internal fields

        This is the primary regression test. If this fails, it means the backend
        is leaking SQLAlchemy metadata which will corrupt the frontend editor.
        """
        response = client.get(f"/api/chapters/{sample_chapter.id}")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] == True
        assert "data" in data
        chapter_data = data["data"]

        # CRITICAL: Ensure no SQLAlchemy metadata leaked
        assert "_sa_instance_state" not in chapter_data, \
            "SQLAlchemy _sa_instance_state leaked into API response! This will corrupt frontend data."
        assert "_sa_adapter" not in chapter_data, \
            "SQLAlchemy _sa_adapter leaked into API response!"
        assert "_sa_class_manager" not in chapter_data, \
            "SQLAlchemy _sa_class_manager leaked into API response!"

        # Verify required fields are present and correct
        assert chapter_data["id"] == sample_chapter.id
        assert chapter_data["manuscript_id"] == sample_chapter.manuscript_id
        assert chapter_data["title"] == sample_chapter.title
        assert chapter_data["lexical_state"] == sample_chapter.lexical_state
        assert chapter_data["content"] == sample_chapter.content
        assert chapter_data["word_count"] == sample_chapter.word_count
        assert isinstance(chapter_data["is_folder"], bool)
        assert chapter_data["is_folder"] == False

    def test_create_chapter_no_metadata(self, client, sample_manuscript):
        """Verify chapter creation responses are clean"""
        response = client.post(
            "/api/chapters",
            json={
                "manuscript_id": sample_manuscript.id,
                "title": "New Test Chapter",
                "is_folder": False,
                "lexical_state": '{"root": {"children": []}}',
                "content": "New content",
            }
        )

        assert response.status_code == 200
        data = response.json()
        chapter_data = data["data"]

        # Verify no metadata pollution
        assert "_sa_instance_state" not in chapter_data
        assert "_sa_adapter" not in chapter_data

        # Verify content integrity
        assert chapter_data["lexical_state"] == '{"root": {"children": []}}'
        assert chapter_data["content"] == "New content"

    def test_list_chapters_no_metadata(self, client, multiple_chapters):
        """Verify chapter list responses are clean"""
        manuscript_id = multiple_chapters[0].manuscript_id

        response = client.get(f"/api/chapters/manuscript/{manuscript_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        chapters = data["data"]
        assert len(chapters) == 3

        for chapter in chapters:
            # Each chapter in the list should be clean
            assert "_sa_instance_state" not in chapter, \
                f"Chapter {chapter.get('id')} has SQLAlchemy metadata in list response"
            assert "lexical_state" in chapter
            assert "content" in chapter
            assert chapter["lexical_state"] is not None
            assert chapter["content"] is not None

    def test_update_chapter_preserves_content(self, client, sample_chapter):
        """Verify updates don't corrupt content fields"""
        new_content = "Updated content with more words here"
        new_lexical = '{"root": {"children": [{"type": "paragraph", "children": [{"type": "text", "text": "Updated content with more words here"}]}]}}'

        response = client.put(
            f"/api/chapters/{sample_chapter.id}",
            json={
                "content": new_content,
                "lexical_state": new_lexical
            }
        )

        assert response.status_code == 200
        data = response.json()

        chapter_data = data["data"]

        # Verify no metadata pollution
        assert "_sa_instance_state" not in chapter_data

        # Verify content was updated correctly
        assert chapter_data["content"] == new_content
        assert chapter_data["lexical_state"] == new_lexical

        # Verify word count was calculated
        assert chapter_data["word_count"] > 0


class TestChapterDataIntegrity:
    """Tests to ensure chapter data integrity throughout lifecycle"""

    def test_full_chapter_lifecycle(self, client, sample_manuscript):
        """
        Integration test simulating full chapter lifecycle

        This test creates a chapter, updates it multiple times (simulating
        auto-save), and verifies content is preserved correctly at each step.
        """

        # 1. Create chapter
        create_response = client.post(
            "/api/chapters",
            json={
                "manuscript_id": sample_manuscript.id,
                "title": "Lifecycle Test Chapter",
                "is_folder": False,
                "lexical_state": '{"root": {"children": []}}',
                "content": "Initial content",
            }
        )

        assert create_response.status_code == 200
        chapter_data = create_response.json()["data"]
        chapter_id = chapter_data["id"]

        # Verify no metadata pollution on create
        assert "_sa_instance_state" not in chapter_data

        # 2. Update chapter multiple times (simulating auto-save)
        for i in range(5):
            lexical_state = f'{{"root": {{"children": [{{"type": "paragraph", "iteration": {i}}}]}}}}'
            content = f"Updated content iteration {i} with some text"
            word_count = len(content.split())

            update_response = client.put(
                f"/api/chapters/{chapter_id}",
                json={
                    "lexical_state": lexical_state,
                    "content": content,
                    "word_count": word_count,
                }
            )

            assert update_response.status_code == 200, \
                f"Update {i} failed with status {update_response.status_code}"

            updated_data = update_response.json()["data"]

            # Verify content persisted correctly
            assert updated_data["content"] == content, \
                f"Content mismatch at iteration {i}"
            assert updated_data["word_count"] == word_count, \
                f"Word count mismatch at iteration {i}"
            assert "_sa_instance_state" not in updated_data, \
                f"Metadata leak at iteration {i}"

        # 3. Retrieve chapter and verify final state
        final_response = client.get(f"/api/chapters/{chapter_id}")

        assert final_response.status_code == 200
        final_data = final_response.json()["data"]

        assert final_data["content"] == "Updated content iteration 4 with some text"
        assert final_data["word_count"] == 7  # "Updated content iteration 4 with some text" = 7 words
        assert final_data["lexical_state"] is not None
        assert len(final_data["lexical_state"]) > 0

        print("✅ Full chapter lifecycle test passed - no data loss detected")

    def test_chapter_with_empty_content(self, client, sample_manuscript):
        """Test that chapters with no content don't have corrupted empty fields"""
        response = client.post(
            "/api/chapters",
            json={
                "manuscript_id": sample_manuscript.id,
                "title": "Empty Chapter",
                "is_folder": False,
                "lexical_state": "",
                "content": "",
            }
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Even empty chapters should have clean responses
        assert "_sa_instance_state" not in data
        assert "lexical_state" in data
        assert "content" in data
        assert data["lexical_state"] == ""
        assert data["content"] == ""

    def test_chapter_word_count_integrity(self, client, sample_chapter):
        """
        Test that word count mismatches are detectable

        This simulates the scenario where word_count > 0 but content is empty,
        which was the data integrity issue reported by the user.
        """
        # Get the chapter
        response = client.get(f"/api/chapters/{sample_chapter.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        # If word_count > 0, both lexical_state and content should have data
        if data["word_count"] > 0:
            assert data["lexical_state"] is not None and data["lexical_state"] != "", \
                "DATA INTEGRITY ISSUE: word_count > 0 but lexical_state is empty!"
            assert data["content"] is not None and data["content"] != "", \
                "DATA INTEGRITY ISSUE: word_count > 0 but content is empty!"


class TestResponseFieldTypes:
    """Tests to verify correct data types in API responses"""

    def test_chapter_field_types(self, client, sample_chapter):
        """Verify all fields have correct types"""
        response = client.get(f"/api/chapters/{sample_chapter.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        # Type checks
        assert isinstance(data["id"], str)
        assert isinstance(data["manuscript_id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["is_folder"], bool)
        assert isinstance(data["order_index"], int)
        assert isinstance(data["word_count"], int)
        assert isinstance(data["lexical_state"], str)
        assert isinstance(data["content"], str)

        # Verify dates are properly serialized (should be strings or None)
        if data.get("created_at") is not None:
            assert isinstance(data["created_at"], str)
        if data.get("updated_at") is not None:
            assert isinstance(data["updated_at"], str)
