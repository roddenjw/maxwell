"""
Pytest configuration and fixtures for backend tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import json

from app.main import app
from app.database import Base, get_db
from app.models.manuscript import Manuscript, Chapter
from app.models.entity import Entity
from app.models.timeline import TimelineEvent
from app.models.outline import Outline, PlotBeat
from app.models.coach import WritingProfile, CoachingHistory, FeedbackPattern


# Create test database engine
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    yield db

    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_manuscript(test_db):
    """Create a sample manuscript for testing"""
    manuscript = Manuscript(
        id=str(uuid.uuid4()),
        title="Test Manuscript",
        word_count=0
    )
    test_db.add(manuscript)
    test_db.commit()
    test_db.refresh(manuscript)

    return manuscript


@pytest.fixture
def sample_chapter(test_db, sample_manuscript):
    """Create a sample chapter for testing"""
    chapter = Chapter(
        id=str(uuid.uuid4()),
        manuscript_id=sample_manuscript.id,
        title="Test Chapter",
        is_folder=0,
        order_index=0,
        lexical_state='{"root": {"children": [{"type": "paragraph", "children": [{"type": "text", "text": "Test content"}]}]}}',
        content="Test content",
        word_count=2
    )
    test_db.add(chapter)
    test_db.commit()
    test_db.refresh(chapter)

    return chapter


@pytest.fixture
def multiple_chapters(test_db, sample_manuscript):
    """Create multiple chapters for testing"""
    chapters = []
    for i in range(3):
        chapter = Chapter(
            id=str(uuid.uuid4()),
            manuscript_id=sample_manuscript.id,
            title=f"Chapter {i+1}",
            is_folder=0,
            order_index=i,
            lexical_state=f'{{"root": {{"children": [{i}]}}}}',
            content=f"Content for chapter {i+1}",
            word_count=i + 1
        )
        test_db.add(chapter)
        chapters.append(chapter)

    test_db.commit()
    for chapter in chapters:
        test_db.refresh(chapter)

    return chapters


# ========================================
# Agent Testing Fixtures
# ========================================

@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response for testing agents"""
    from app.services.llm_service import LLMResponse, LLMProvider

    return LLMResponse(
        content=json.dumps({
            "recommendations": [
                {
                    "type": "style",
                    "severity": "medium",
                    "text": "Consider varying sentence length for better rhythm.",
                    "suggestion": "Mix short and long sentences.",
                    "teaching_point": "Sentence variety creates engaging prose."
                }
            ],
            "issues": [
                {
                    "type": "continuity",
                    "severity": "high",
                    "description": "Character eye color inconsistency detected.",
                    "location": "paragraph 3",
                    "suggestion": "Verify character attributes in Codex."
                }
            ],
            "praise": [
                {
                    "aspect": "dialogue",
                    "text": "Strong character voice differentiation."
                }
            ],
            "overall_assessment": "Good progress with minor consistency issues."
        }),
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={
            "prompt_tokens": 500,
            "completion_tokens": 150,
            "total_tokens": 650
        },
        cost=0.0008
    )


@pytest.fixture
def mock_llm_response_text():
    """Create a mock text (non-JSON) LLM response"""
    from app.services.llm_service import LLMResponse, LLMProvider

    return LLMResponse(
        content="Your writing shows strong character development. Consider adding more sensory details to the scene descriptions.",
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={
            "prompt_tokens": 300,
            "completion_tokens": 50,
            "total_tokens": 350
        },
        cost=0.0004
    )


@pytest.fixture
def mock_llm_service(mock_llm_response):
    """
    Create a patched LLM service for testing.

    Usage:
        def test_agent(mock_llm_service):
            # Service is already mocked
            result = await agent.analyze(...)
    """
    with patch('app.services.llm_service.llm_service') as mock:
        mock.generate = AsyncMock(return_value=mock_llm_response)
        mock.generate_json = AsyncMock(return_value=json.loads(mock_llm_response.content))
        yield mock


@pytest.fixture
def mock_context_loader():
    """
    Create a mock context loader for testing agents.

    Returns a mock that provides sample context data.
    """
    from app.agents.base.context_loader import (
        AgentContext, AuthorContext, ManuscriptContext
    )

    mock_author = AuthorContext(
        user_id="test-user-id",
        style_metrics={"avg_sentence_length": 15, "adverb_ratio": 0.02},
        strengths=["dialogue", "pacing"],
        weaknesses=["show-don't-tell"],
        preferences={"feedback_detail": "detailed"},
        overused_words={"very": 15, "really": 12, "just": 20},
        favorite_techniques=["in medias res", "unreliable narrator"],
        feedback_patterns=[],
        learning_history=[]
    )

    mock_manuscript = ManuscriptContext(
        manuscript_id="test-manuscript-id",
        title="Test Novel",
        description="A test manuscript for unit testing.",
        word_count=50000,
        chapters=[
            {"id": "ch-1", "title": "Chapter 1", "is_folder": False, "word_count": 3000, "order_index": 0},
            {"id": "ch-2", "title": "Chapter 2", "is_folder": False, "word_count": 2500, "order_index": 1},
        ],
        entities=[
            {"id": "ent-1", "name": "Alice", "type": "CHARACTER", "aliases": ["Al"], "attributes": {"age": 25}},
            {"id": "ent-2", "name": "Bob", "type": "CHARACTER", "aliases": [], "attributes": {"age": 30}},
        ],
        timeline_events=[
            {"id": "evt-1", "description": "Story begins", "timestamp": "Day 1", "event_type": "SCENE"},
        ],
        outline={"id": "outline-1", "structure_type": "three_act", "premise": "Test premise", "logline": None},
        current_position={"chapter_id": "ch-1", "chapter_title": "Chapter 1", "chapter_index": 0}
    )

    mock_context = AgentContext(
        author=mock_author,
        world=None,
        series=None,
        manuscript=mock_manuscript,
        author_weight=0.5,
        world_weight=0.0,
        series_weight=0.0,
        manuscript_weight=1.0
    )

    with patch('app.agents.base.context_loader.ContextLoader') as MockLoader:
        instance = MockLoader.return_value
        instance.load_full_context = MagicMock(return_value=mock_context)
        instance.load_author_context = MagicMock(return_value=mock_author)
        instance.load_manuscript_context = MagicMock(return_value=mock_manuscript)
        yield instance, mock_context


@pytest.fixture
def sample_writing_profile(test_db):
    """Create a sample writing profile for coaching tests"""
    profile = WritingProfile(
        id=str(uuid.uuid4()),
        user_id="test-user-id",
        profile_data={
            "style_metrics": {
                "avg_sentence_length": 15.5,
                "vocabulary_richness": 0.72,
                "adverb_ratio": 0.015
            },
            "strengths": ["dialogue", "character voice", "pacing"],
            "weaknesses": ["show-don't-tell", "passive voice"],
            "preferences": {
                "feedback_detail": "detailed",
                "tone": "encouraging"
            },
            "overused_words": {"very": 25, "really": 18, "just": 22},
            "favorite_techniques": ["in medias res"]
        },
        total_words_analyzed=50000,
        sessions_count=5
    )
    test_db.add(profile)
    test_db.commit()
    test_db.refresh(profile)
    return profile


@pytest.fixture
def sample_entity(test_db, sample_manuscript):
    """Create a sample codex entity for testing"""
    entity = Entity(
        id=str(uuid.uuid4()),
        manuscript_id=sample_manuscript.id,
        name="Test Character",
        type="CHARACTER",
        attributes={
            "age": 28,
            "hair_color": "brown",
            "occupation": "blacksmith",
            "description": "A brave adventurer with a mysterious past."
        },
        aliases=["The Smith", "Alex"]
    )
    test_db.add(entity)
    test_db.commit()
    test_db.refresh(entity)
    return entity


@pytest.fixture
def sample_timeline_event(test_db, sample_manuscript):
    """Create a sample timeline event for testing"""
    event = TimelineEvent(
        id=str(uuid.uuid4()),
        manuscript_id=sample_manuscript.id,
        description="The hero meets the mentor",
        timestamp="Year 1, Spring",
        event_type="SCENE",
        order_index=0,
        chapter_ids=[]
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


@pytest.fixture
def sample_outline(test_db, sample_manuscript):
    """Create a sample outline with plot beats for testing"""
    outline = Outline(
        id=str(uuid.uuid4()),
        manuscript_id=sample_manuscript.id,
        structure_type="three_act",
        premise="A young hero must overcome their fears to save the kingdom.",
        logline="When a peaceful village is threatened, a reluctant blacksmith must embrace their destiny.",
        is_active=True
    )
    test_db.add(outline)
    test_db.commit()
    test_db.refresh(outline)

    # Add plot beats
    beats = [
        PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=outline.id,
            beat_type="OPENING IMAGE",
            title="Village Life",
            description="Establish the protagonist's ordinary world",
            act_number=1,
            sequence_number=1,
            order_index=0,
            target_word_count=1000
        ),
        PlotBeat(
            id=str(uuid.uuid4()),
            outline_id=outline.id,
            beat_type="INCITING INCIDENT",
            title="The Attack",
            description="The village is attacked, forcing the hero to act",
            act_number=1,
            sequence_number=2,
            order_index=1,
            target_word_count=2000
        ),
    ]
    for beat in beats:
        test_db.add(beat)
    test_db.commit()

    return outline


@pytest.fixture
def agent_config():
    """Create a test agent configuration"""
    from app.agents.base.agent_config import (
        AgentConfig, AgentType, ModelConfig, ModelProvider, ModelCapability
    )

    model_config = ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0.7,
        capability=ModelCapability.STANDARD
    )

    return AgentConfig(
        agent_type=AgentType.STYLE,
        model_config=model_config,
        author_context_weight=0.5,
        world_context_weight=0.0,
        series_context_weight=0.0,
        manuscript_context_weight=1.0,
        max_context_tokens=8000,
        include_teaching=True,
        response_format="json"
    )


@pytest.fixture
def sample_text():
    """Sample text for agent analysis testing"""
    return """
    Sarah walked into the room very quietly. She was really nervous about the meeting.

    "Hello," she said softly.

    John looked up from his desk. His blue eyes sparkled with interest. "Sarah! I didn't
    expect to see you here today. Please, have a seat."

    She sat down carefully, her hands trembling slightly. The office was just as she
    remembered it - dark wood paneling, the smell of old books, and that massive painting
    of the countryside hanging behind his desk.

    "I need to tell you something important," she began, her voice barely above a whisper.
    """.strip()


# ========================================
# Async Test Helpers
# ========================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_client(test_db):
    """Create an async test client"""
    from httpx import AsyncClient

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # We yield the ASGITransport-based client
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")

    yield client

    app.dependency_overrides.clear()
