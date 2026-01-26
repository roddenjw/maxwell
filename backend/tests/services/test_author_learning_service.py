"""
Tests for Author Learning Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.author_learning_service import (
    AuthorLearningService,
    ISSUE_CATEGORIES,
    author_learning_service
)


class TestIssueCategories:
    """Tests for ISSUE_CATEGORIES constant"""

    def test_all_categories_have_required_fields(self):
        """Test all issue categories have required fields"""
        required_fields = ["name", "description", "teaching"]

        for category_key, category_data in ISSUE_CATEGORIES.items():
            for field in required_fields:
                assert field in category_data, f"Category {category_key} missing {field}"

    def test_common_categories_exist(self):
        """Test common writing issue categories exist"""
        expected_categories = [
            "show_vs_tell",
            "overused_words",
            "passive_voice",
            "weak_verbs",
            "dialogue_tags",
            "pacing",
            "continuity"
        ]

        for category in expected_categories:
            assert category in ISSUE_CATEGORIES, f"Missing category: {category}"

    def test_category_names_are_human_readable(self):
        """Test category names are human-readable"""
        for key, data in ISSUE_CATEGORIES.items():
            # Name should be title case or have spaces
            name = data["name"]
            assert len(name) > 0
            # Should not be snake_case
            assert "_" not in name


class TestAuthorLearningService:
    """Tests for AuthorLearningService class"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return AuthorLearningService()

    def test_service_instantiation(self, service):
        """Test service can be instantiated"""
        assert service is not None

    def test_record_suggestion_feedback_accepted(self, service, test_db):
        """Test recording accepted suggestion feedback"""
        mock_feedback = MagicMock()
        mock_feedback.id = "feedback-123"
        mock_feedback.action = "accepted"

        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            mock_db.close = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch.object(service, '_update_learning_patterns'):
                feedback = service.record_suggestion_feedback(
                    user_id="test-user",
                    agent_type="style",
                    suggestion_type="show_vs_tell",
                    suggestion_text="Consider showing this emotion through action.",
                    action="accepted"
                )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_record_suggestion_feedback_rejected(self, service):
        """Test recording rejected suggestion feedback"""
        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            mock_db.close = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch.object(service, '_update_learning_patterns'):
                feedback = service.record_suggestion_feedback(
                    user_id="test-user",
                    agent_type="style",
                    suggestion_type="passive_voice",
                    suggestion_text="Consider using active voice.",
                    action="rejected",
                    user_explanation="I prefer passive voice here for stylistic reasons."
                )

            mock_db.add.assert_called_once()

    def test_record_suggestion_feedback_modified(self, service):
        """Test recording modified suggestion feedback"""
        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            mock_db.close = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch.object(service, '_update_learning_patterns'):
                feedback = service.record_suggestion_feedback(
                    user_id="test-user",
                    agent_type="voice",
                    suggestion_type="dialogue_tags",
                    suggestion_text="Use action beat instead of said.",
                    action="modified",
                    original_text='"Hello," she said quietly.',
                    modified_text='"Hello." She spoke barely above a whisper.'
                )

            mock_db.add.assert_called_once()

    def test_update_learning_patterns_new_pattern(self, service):
        """Test updating learning patterns creates new record"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service._update_learning_patterns(
            db=mock_db,
            user_id="test-user",
            suggestion_type="show_vs_tell",
            action="accepted"
        )

        mock_db.add.assert_called_once()

    def test_update_learning_patterns_existing_pattern(self, service):
        """Test updating existing learning pattern"""
        mock_learning = MagicMock()
        mock_learning.pattern_data = {
            "accepted": 5,
            "rejected": 2,
            "modified": 1,
            "ignored": 0,
            "total": 8,
            "history": []
        }
        mock_learning.observation_count = 8

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_learning

        service._update_learning_patterns(
            db=mock_db,
            user_id="test-user",
            suggestion_type="show_vs_tell",
            action="accepted"
        )

        # Pattern data should be updated
        assert mock_learning.pattern_data["accepted"] == 6
        assert mock_learning.pattern_data["total"] == 9
        assert mock_learning.observation_count == 9

    def test_should_suppress_suggestion_type_high_rejection(self, service):
        """Test suppression for frequently rejected suggestions"""
        mock_learning = MagicMock()
        mock_learning.pattern_data = {
            "accepted": 1,
            "rejected": 9,
            "modified": 0,
            "ignored": 0,
            "total": 10
        }
        mock_learning.observation_count = 10

        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_learning
            mock_db.close = MagicMock()

            should_suppress = service.should_suppress_suggestion_type(
                user_id="test-user",
                suggestion_type="passive_voice"
            )

        # 90% rejection rate should lead to suppression
        assert should_suppress is True

    def test_should_suppress_suggestion_type_high_acceptance(self, service):
        """Test no suppression for accepted suggestions"""
        mock_learning = MagicMock()
        mock_learning.pattern_data = {
            "accepted": 8,
            "rejected": 2,
            "modified": 0,
            "ignored": 0,
            "total": 10
        }

        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_learning
            mock_db.close = MagicMock()

            should_suppress = service.should_suppress_suggestion_type(
                user_id="test-user",
                suggestion_type="show_vs_tell"
            )

        assert should_suppress is False

    def test_should_suppress_suggestion_type_no_data(self, service):
        """Test no suppression when no data exists"""
        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.close = MagicMock()

            should_suppress = service.should_suppress_suggestion_type(
                user_id="test-user",
                suggestion_type="new_type"
            )

        assert should_suppress is False

    def test_get_author_insights_success(self, service):
        """Test getting author insights"""
        mock_profile = MagicMock()
        mock_profile.profile_data = {
            "strengths": ["dialogue", "pacing"],
            "weaknesses": ["show-don't-tell"],
            "style_metrics": {"avg_sentence_length": 15}
        }
        mock_profile.total_words_analyzed = 50000
        mock_profile.sessions_count = 10

        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.close = MagicMock()

            insights = service.get_author_insights("test-user")

        assert insights is not None
        assert "strengths" in insights or "common_issues" in insights

    def test_get_author_insights_no_profile(self, service):
        """Test getting insights when no profile exists"""
        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.close = MagicMock()

            insights = service.get_author_insights("new-user")

        # Should return empty/default insights, not error
        assert insights is not None


class TestAuthorLearningServiceIntegration:
    """Integration tests for author learning service"""

    @pytest.fixture
    def service(self):
        return AuthorLearningService()

    def test_full_feedback_cycle(self, service):
        """Test complete feedback recording and pattern learning cycle"""
        # This test would use actual database in integration testing
        # For unit testing, we verify the flow works
        with patch('app.services.author_learning_service.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            mock_db.close = MagicMock()

            # No existing pattern
            mock_db.query.return_value.filter.return_value.first.return_value = None

            # Record first feedback
            service.record_suggestion_feedback(
                user_id="test-user",
                agent_type="style",
                suggestion_type="passive_voice",
                suggestion_text="Use active voice",
                action="rejected"
            )

            # Verify pattern was created
            assert mock_db.add.call_count >= 1


class TestGlobalServiceInstance:
    """Tests for global author_learning_service instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        assert author_learning_service is not None
        assert isinstance(author_learning_service, AuthorLearningService)
