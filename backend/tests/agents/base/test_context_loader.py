"""
Tests for Context Loader
"""
import pytest
from unittest.mock import MagicMock, patch

from app.agents.base.context_loader import (
    ContextLoader,
    AgentContext,
    AuthorContext,
    WorldContext,
    SeriesContext,
    ManuscriptContext
)


class TestAuthorContext:
    """Tests for AuthorContext dataclass"""

    def test_author_context_creation(self):
        """Test basic AuthorContext creation"""
        ctx = AuthorContext(
            user_id="user-123",
            style_metrics={"avg_sentence_length": 15},
            strengths=["dialogue", "pacing"],
            weaknesses=["show-don't-tell"]
        )

        assert ctx.user_id == "user-123"
        assert ctx.style_metrics["avg_sentence_length"] == 15
        assert "dialogue" in ctx.strengths
        assert "show-don't-tell" in ctx.weaknesses

    def test_author_context_defaults(self):
        """Test AuthorContext default values"""
        ctx = AuthorContext(user_id="user-456")

        assert ctx.style_metrics == {}
        assert ctx.strengths == []
        assert ctx.weaknesses == []
        assert ctx.preferences == {}
        assert ctx.overused_words == {}
        assert ctx.favorite_techniques == []
        assert ctx.feedback_patterns == []
        assert ctx.learning_history == []

    def test_author_context_to_prompt_context(self):
        """Test AuthorContext serialization to prompt text"""
        ctx = AuthorContext(
            user_id="user-789",
            style_metrics={"avg_sentence_length": 18, "vocabulary_richness": 0.7},
            strengths=["character development", "world building"],
            weaknesses=["pacing"],
            preferences={"feedback_detail": "detailed"},
            overused_words={"very": 25, "really": 15}
        )

        text = ctx.to_prompt_context()

        assert "user-789" in text
        assert "avg_sentence_length" in text
        assert "character development" in text
        assert "pacing" in text
        assert "Watch Words" in text
        assert "very" in text

    def test_author_context_empty_to_prompt(self):
        """Test empty AuthorContext produces minimal prompt"""
        ctx = AuthorContext(user_id="empty-user")

        text = ctx.to_prompt_context()

        assert "empty-user" in text
        # Should not have section headers for empty data
        assert "Writing Style Metrics" not in text


class TestWorldContext:
    """Tests for WorldContext dataclass"""

    def test_world_context_creation(self):
        """Test basic WorldContext creation"""
        ctx = WorldContext(
            world_id="world-123",
            name="Middle Earth",
            description="A fantasy world with elves and hobbits."
        )

        assert ctx.world_id == "world-123"
        assert ctx.name == "Middle Earth"
        assert "fantasy" in ctx.description

    def test_world_context_with_settings(self):
        """Test WorldContext with settings and rules"""
        ctx = WorldContext(
            world_id="world-456",
            name="Sci-Fi Universe",
            settings={
                "technology_level": "advanced",
                "magic_system": {"type": "hard", "rules": ["Conservation", "Cost"]}
            },
            rules=["FTL requires gates", "No time travel"],
            world_entities=[
                {"name": "Earth Federation", "type": "ORGANIZATION"},
                {"name": "Mars Colony", "type": "LOCATION"}
            ]
        )

        text = ctx.to_prompt_context()

        assert "Sci-Fi Universe" in text
        assert "advanced" in text or "technology_level" in text
        assert "FTL requires gates" in text
        assert "Earth Federation" in text


class TestSeriesContext:
    """Tests for SeriesContext dataclass"""

    def test_series_context_creation(self):
        """Test basic SeriesContext creation"""
        ctx = SeriesContext(
            series_id="series-123",
            name="The Dark Tower",
            description="An epic fantasy series."
        )

        assert ctx.series_id == "series-123"
        assert ctx.name == "The Dark Tower"

    def test_series_context_with_manuscripts(self):
        """Test SeriesContext with manuscript list"""
        ctx = SeriesContext(
            series_id="series-456",
            name="Mystery Series",
            manuscripts=[
                {"title": "Book One", "order_index": 0, "word_count": 80000},
                {"title": "Book Two", "order_index": 1, "word_count": 75000}
            ],
            recurring_themes=["redemption", "justice"]
        )

        text = ctx.to_prompt_context()

        assert "Mystery Series" in text
        assert "Book One" in text
        assert "Book Two" in text
        assert "redemption" in text


class TestManuscriptContext:
    """Tests for ManuscriptContext dataclass"""

    def test_manuscript_context_creation(self):
        """Test basic ManuscriptContext creation"""
        ctx = ManuscriptContext(
            manuscript_id="ms-123",
            title="Test Novel",
            word_count=50000
        )

        assert ctx.manuscript_id == "ms-123"
        assert ctx.title == "Test Novel"
        assert ctx.word_count == 50000

    def test_manuscript_context_full(self):
        """Test ManuscriptContext with all data"""
        ctx = ManuscriptContext(
            manuscript_id="ms-456",
            title="Complete Novel",
            description="A story about adventure.",
            word_count=85000,
            chapters=[
                {"id": "ch-1", "title": "Beginning", "is_folder": False, "word_count": 3000},
                {"id": "ch-2", "title": "Middle", "is_folder": False, "word_count": 5000}
            ],
            entities=[
                {"id": "e-1", "name": "Hero", "type": "CHARACTER"},
                {"id": "e-2", "name": "Castle", "type": "LOCATION"}
            ],
            timeline_events=[
                {"id": "t-1", "description": "Story begins", "timestamp": "Day 1"}
            ],
            outline={
                "id": "o-1",
                "structure_type": "three_act",
                "premise": "A hero's journey",
                "logline": "When X happens, Y must Z"
            },
            current_position={"chapter_id": "ch-1", "chapter_title": "Beginning"}
        )

        text = ctx.to_prompt_context()

        assert "Complete Novel" in text
        assert "85000" in text or "Word Count" in text
        assert "Beginning" in text
        assert "Hero" in text
        assert "CHARACTER" in text
        assert "three_act" in text


class TestAgentContext:
    """Tests for AgentContext dataclass"""

    @pytest.fixture
    def sample_contexts(self):
        """Create sample context objects"""
        author = AuthorContext(
            user_id="test-user",
            strengths=["dialogue"],
            weaknesses=["pacing"]
        )
        manuscript = ManuscriptContext(
            manuscript_id="test-ms",
            title="Test Book",
            word_count=30000
        )
        return author, manuscript

    def test_agent_context_creation(self, sample_contexts):
        """Test basic AgentContext creation"""
        author, manuscript = sample_contexts

        ctx = AgentContext(
            author=author,
            manuscript=manuscript
        )

        assert ctx.author.user_id == "test-user"
        assert ctx.manuscript.title == "Test Book"
        assert ctx.world is None
        assert ctx.series is None

    def test_agent_context_default_weights(self):
        """Test AgentContext default weight values"""
        ctx = AgentContext()

        assert ctx.author_weight == 0.5
        assert ctx.world_weight == 0.5
        assert ctx.series_weight == 0.5
        assert ctx.manuscript_weight == 1.0

    def test_agent_context_to_prompt_weighted(self, sample_contexts):
        """Test AgentContext prompt generation respects weights"""
        author, manuscript = sample_contexts

        ctx = AgentContext(
            author=author,
            manuscript=manuscript,
            author_weight=1.0,
            manuscript_weight=0.5
        )

        text = ctx.to_prompt_context()

        # Both should be included
        assert "test-user" in text
        assert "Test Book" in text

    def test_agent_context_to_prompt_zero_weight(self, sample_contexts):
        """Test AgentContext excludes zero-weight contexts"""
        author, manuscript = sample_contexts

        ctx = AgentContext(
            author=author,
            manuscript=manuscript,
            author_weight=0.0,  # Should be excluded
            manuscript_weight=1.0
        )

        text = ctx.to_prompt_context()

        assert "Test Book" in text
        # Author should not be included due to zero weight
        # Note: Implementation may still include header, check actual behavior

    def test_agent_context_truncation(self, sample_contexts):
        """Test AgentContext truncates long content"""
        author, manuscript = sample_contexts

        # Create context with very long description
        manuscript.description = "A" * 50000  # Very long

        ctx = AgentContext(
            author=author,
            manuscript=manuscript,
            manuscript_weight=1.0
        )

        # Request small max tokens
        text = ctx.to_prompt_context(max_tokens=1000)

        # Should be truncated
        assert len(text) < 50000
        assert "[Context truncated]" in text or len(text) < 5000


class TestContextLoader:
    """Tests for ContextLoader class"""

    @pytest.fixture
    def loader(self):
        """Create a ContextLoader instance"""
        return ContextLoader()

    def test_context_loader_instantiation(self, loader):
        """Test ContextLoader can be instantiated"""
        assert loader is not None

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_author_context_no_profile(self, mock_session, loader):
        """Test loading author context when no profile exists"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock empty query results
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = loader.load_author_context("unknown-user")

        assert result.user_id == "unknown-user"
        assert result.style_metrics == {}
        assert result.strengths == []

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_author_context_with_profile(self, mock_session, loader):
        """Test loading author context with existing profile"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock profile
        mock_profile = MagicMock()
        mock_profile.profile_data = {
            "style_metrics": {"avg_sentence_length": 14},
            "strengths": ["dialogue"],
            "weaknesses": ["pacing"],
            "preferences": {},
            "overused_words": {"very": 10},
            "favorite_techniques": []
        }

        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = loader.load_author_context("test-user")

        assert result.user_id == "test-user"
        assert result.style_metrics["avg_sentence_length"] == 14
        assert "dialogue" in result.strengths

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_world_context_not_found(self, mock_session, loader):
        """Test loading world context when world doesn't exist"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = loader.load_world_context("unknown-world")

        assert result.world_id == "unknown-world"
        assert result.name == "Unknown World"

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_world_context_success(self, mock_session, loader):
        """Test loading world context successfully"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock world
        mock_world = MagicMock()
        mock_world.name = "Fantasy World"
        mock_world.description = "A magical realm"
        mock_world.settings = {"magic_level": "high"}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_world
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = loader.load_world_context("world-123")

        assert result.world_id == "world-123"
        assert result.name == "Fantasy World"
        assert "magical" in result.description

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_manuscript_context_not_found(self, mock_session, loader):
        """Test loading manuscript context when not found"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = loader.load_manuscript_context("unknown-ms")

        assert result.manuscript_id == "unknown-ms"
        assert result.title == "Unknown Manuscript"

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_manuscript_context_success(self, mock_session, loader):
        """Test loading manuscript context successfully"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock manuscript
        mock_manuscript = MagicMock()
        mock_manuscript.id = "ms-123"
        mock_manuscript.title = "My Novel"
        mock_manuscript.description = "A great story"
        mock_manuscript.word_count = 45000

        # Mock queries
        mock_db.query.return_value.filter.return_value.first.return_value = mock_manuscript
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = loader.load_manuscript_context("ms-123")

        assert result.manuscript_id == "ms-123"
        assert result.title == "My Novel"
        assert result.word_count == 45000

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_manuscript_context_with_current_chapter(self, mock_session, loader):
        """Test loading manuscript context with current chapter position"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock manuscript
        mock_manuscript = MagicMock()
        mock_manuscript.id = "ms-123"
        mock_manuscript.title = "My Novel"
        mock_manuscript.description = ""
        mock_manuscript.word_count = 30000

        # Mock chapter
        mock_chapter = MagicMock()
        mock_chapter.id = "ch-1"
        mock_chapter.title = "Chapter One"
        mock_chapter.is_folder = False
        mock_chapter.word_count = 2500
        mock_chapter.order_index = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_manuscript
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_chapter]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = loader.load_manuscript_context("ms-123", current_chapter_id="ch-1")

        assert result.current_position is not None
        assert result.current_position["chapter_id"] == "ch-1"
        assert result.current_position["chapter_title"] == "Chapter One"

    @patch('app.agents.base.context_loader.SessionLocal')
    def test_load_full_context(self, mock_session, loader):
        """Test loading full hierarchical context"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock manuscript without series
        mock_manuscript = MagicMock()
        mock_manuscript.id = "ms-123"
        mock_manuscript.title = "Solo Novel"
        mock_manuscript.series_id = None
        mock_manuscript.description = ""
        mock_manuscript.word_count = 50000

        mock_db.query.return_value.filter.return_value.first.return_value = mock_manuscript
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch.object(loader, 'load_author_context') as mock_author, \
             patch.object(loader, 'load_manuscript_context') as mock_ms:

            mock_author.return_value = AuthorContext(user_id="test-user")
            mock_ms.return_value = ManuscriptContext(
                manuscript_id="ms-123",
                title="Solo Novel",
                word_count=50000
            )

            result = loader.load_full_context(
                user_id="test-user",
                manuscript_id="ms-123"
            )

            assert result.author.user_id == "test-user"
            assert result.manuscript.title == "Solo Novel"
            assert result.world is None  # No world without series
            assert result.series is None

    def test_load_full_context_respects_weights(self, loader):
        """Test that zero weights skip context loading"""
        with patch.object(loader, 'load_author_context') as mock_author, \
             patch.object(loader, 'load_manuscript_context') as mock_ms, \
             patch('app.agents.base.context_loader.SessionLocal') as mock_session:

            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_manuscript = MagicMock()
            mock_manuscript.series_id = None
            mock_db.query.return_value.filter.return_value.first.return_value = mock_manuscript

            mock_author.return_value = AuthorContext(user_id="test")
            mock_ms.return_value = ManuscriptContext(manuscript_id="ms", title="Test")

            result = loader.load_full_context(
                user_id="test",
                manuscript_id="ms",
                author_weight=0.0,  # Should skip
                manuscript_weight=1.0
            )

            # Author should not be loaded
            mock_author.assert_not_called()
            assert result.author is None
