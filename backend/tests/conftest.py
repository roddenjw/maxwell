"""
Pytest configuration and fixtures for backend tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.database import Base, get_db
from app.models.manuscript import Manuscript, Chapter


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
