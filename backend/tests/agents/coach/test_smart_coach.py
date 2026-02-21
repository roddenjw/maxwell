"""
Tests for Smart Coach Agent
"""
import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.coach.smart_coach_agent import (
    SmartCoachAgent,
    CoachResponse,
    create_smart_coach,
    COACH_SYSTEM_PROMPT
)
from app.agents.base.agent_config import ModelConfig, ModelProvider
from app.services.llm_service import LLMResponse, LLMProvider


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response"""
    return LLMResponse(
        content="I'd be happy to help you with your story! Based on your codex, your main character is Sarah, a 28-year-old detective.",
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={"prompt_tokens": 500, "completion_tokens": 100, "total_tokens": 600},
        cost=0.0007
    )


@pytest.fixture
def mock_session():
    """Create a mock coaching session"""
    session = MagicMock()
    session.id = "session-123"
    session.user_id = "test-user"
    session.manuscript_id = "test-ms"
    session.title = "Test Session"
    session.initial_context = {}
    session.message_count = 0
    session.total_cost = 0.0
    session.total_tokens = 0
    session.status = "active"
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    session.last_message_at = None
    return session


class TestCoachResponse:
    """Tests for CoachResponse dataclass"""

    def test_coach_response_creation(self):
        """Test basic CoachResponse creation"""
        response = CoachResponse(
            content="Hello! How can I help?",
            tools_used=["query_entities"],
            cost=0.001,
            tokens=150,
            session_id="session-123"
        )

        assert response.content == "Hello! How can I help?"
        assert "query_entities" in response.tools_used
        assert response.cost == 0.001
        assert response.session_id == "session-123"

    def test_coach_response_defaults(self):
        """Test CoachResponse default values"""
        response = CoachResponse(content="Test")

        assert response.tools_used == []
        assert response.tool_results == {}
        assert response.cost == 0.0
        assert response.tokens == 0
        assert response.session_id == ""

    def test_coach_response_to_dict(self):
        """Test CoachResponse serialization"""
        response = CoachResponse(
            content="Response text",
            tools_used=["query_entities", "query_timeline"],
            tool_results={"entities": ["Sarah", "John"]},
            cost=0.002,
            tokens=250,
            session_id="session-456"
        )

        data = response.to_dict()

        assert data["content"] == "Response text"
        assert len(data["tools_used"]) == 2
        assert "entities" in data["tool_results"]
        assert data["cost"] == 0.002


class TestSmartCoachAgent:
    """Tests for SmartCoachAgent"""

    def test_coach_initialization(self):
        """Test coach initialization"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        assert coach.api_key == "test-key"
        assert coach.user_id == "test-user"
        assert coach.model_config.provider == ModelProvider.ANTHROPIC
        assert coach.model_config.model_name == "claude-3-haiku-20240307"

    def test_coach_with_custom_model(self):
        """Test coach with custom model configuration"""
        custom_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            temperature=0.5,
            max_tokens=4096
        )

        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user",
            model_config=custom_config
        )

        assert coach.model_config.provider == ModelProvider.OPENAI
        assert coach.model_config.model_name == "gpt-4o"

    def test_create_smart_coach_factory(self):
        """Test create_smart_coach factory function"""
        coach = create_smart_coach(
            api_key="test-key",
            user_id="test-user"
        )

        assert isinstance(coach, SmartCoachAgent)
        assert coach.user_id == "test-user"

    def test_build_llm_config(self):
        """Test _build_llm_config method"""
        coach = SmartCoachAgent(
            api_key="test-api-key",
            user_id="test-user"
        )

        config = coach._build_llm_config()

        assert config.api_key == "test-api-key"
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-haiku-20240307"

    def test_tools_available(self):
        """Test coach has tools loaded for tool calling"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        # Coach should have ALL_TOOLS available
        assert len(coach._tools) > 0
        tool_names = [t.name for t in coach._tools]
        assert "query_entities" in tool_names
        assert "query_timeline" in tool_names

    @pytest.mark.asyncio
    async def test_start_session(self):
        """Test starting a new coaching session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_session_instance = MagicMock()
            mock_db.return_value = mock_session_instance
            mock_session_instance.add = MagicMock()
            mock_session_instance.commit = MagicMock()
            mock_session_instance.refresh = MagicMock()
            mock_session_instance.close = MagicMock()

            session = await coach.start_session(
                manuscript_id="test-ms",
                title="My Writing Session"
            )

            mock_session_instance.add.assert_called_once()
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, mock_session):
        """Test getting an existing session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_session
            mock_db_instance.close = MagicMock()

            session = await coach.get_session("session-123")

            assert session is not None
            assert session.id == "session-123"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test getting a non-existent session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = None
            mock_db_instance.close = MagicMock()

            session = await coach.get_session("nonexistent")

            assert session is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_session):
        """Test listing sessions"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_query = MagicMock()
            mock_db_instance.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = [mock_session]
            mock_db_instance.close = MagicMock()

            sessions = await coach.list_sessions()

            assert len(sessions) == 1
            assert sessions[0].id == "session-123"

    @pytest.mark.asyncio
    async def test_chat(self, mock_session, mock_llm_response):
        """Test chat method with real tool calling"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db, \
             patch('app.agents.coach.smart_coach_agent.llm_service') as mock_llm:

            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_session
            mock_db_instance.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db_instance.add = MagicMock()
            mock_db_instance.commit = MagicMock()
            mock_db_instance.close = MagicMock()

            # Mock the model that supports tool calling
            mock_model = MagicMock()
            mock_model_with_tools = AsyncMock()
            # LLM returns final answer (no tool calls)
            final_response = MagicMock()
            final_response.tool_calls = []
            final_response.content = mock_llm_response.content
            final_response.response_metadata = {"usage": {"prompt_tokens": 500, "completion_tokens": 100}}
            mock_model_with_tools.ainvoke = AsyncMock(return_value=final_response)
            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)

            mock_llm.get_langchain_model = MagicMock(return_value=mock_model)
            mock_llm.convert_messages = MagicMock(return_value=[])

            with patch.object(coach, '_context_loader') as mock_loader:
                mock_context = MagicMock()
                mock_context.to_prompt_context.return_value = "Test context"
                mock_loader.load_full_context.return_value = mock_context

                response = await coach.chat(
                    session_id="session-123",
                    message="Who is my main character?"
                )

        assert isinstance(response, CoachResponse)
        assert response.session_id == "session-123"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_chat_session_not_found(self):
        """Test chat with non-existent session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = None
            mock_db_instance.close = MagicMock()

            response = await coach.chat(
                session_id="nonexistent",
                message="Hello?"
            )

        assert "Session not found" in response.content
        assert response.session_id == ""

    @pytest.mark.asyncio
    async def test_chat_with_context(self, mock_session, mock_llm_response):
        """Test chat with additional context (agent routing disabled)"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user",
            enable_agent_routing=False
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db, \
             patch('app.agents.coach.smart_coach_agent.llm_service') as mock_llm:

            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_session
            mock_db_instance.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db_instance.add = MagicMock()
            mock_db_instance.commit = MagicMock()
            mock_db_instance.close = MagicMock()

            # Mock tool-calling model
            mock_model = MagicMock()
            mock_model_with_tools = AsyncMock()
            final_response = MagicMock()
            final_response.tool_calls = []
            final_response.content = mock_llm_response.content
            final_response.response_metadata = {"usage": {"prompt_tokens": 500, "completion_tokens": 100}}
            mock_model_with_tools.ainvoke = AsyncMock(return_value=final_response)
            mock_model.bind_tools = MagicMock(return_value=mock_model_with_tools)

            mock_llm.get_langchain_model = MagicMock(return_value=mock_model)
            mock_llm.convert_messages = MagicMock(return_value=[])

            with patch.object(coach, '_context_loader') as mock_loader:
                mock_context = MagicMock()
                mock_context.to_prompt_context.return_value = "Test context"
                mock_loader.load_full_context.return_value = mock_context

                response = await coach.chat(
                    session_id="session-123",
                    message="What do you think of this passage?",
                    context={
                        "selected_text": "The knight rode into the sunset.",
                        "chapter_title": "Chapter 5"
                    }
                )

        assert isinstance(response, CoachResponse)

    @pytest.mark.asyncio
    async def test_archive_session(self, mock_session):
        """Test archiving a session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = mock_session
            mock_db_instance.commit = MagicMock()
            mock_db_instance.close = MagicMock()

            result = await coach.archive_session("session-123")

        assert result is True
        assert mock_session.status == "archived"

    @pytest.mark.asyncio
    async def test_archive_session_not_found(self):
        """Test archiving non-existent session"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.first.return_value = None
            mock_db_instance.close = MagicMock()

            result = await coach.archive_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_messages(self):
        """Test getting session messages"""
        coach = SmartCoachAgent(
            api_key="test-key",
            user_id="test-user"
        )

        mock_message = MagicMock()
        mock_message.id = "msg-1"
        mock_message.role = "user"
        mock_message.content = "Hello"
        mock_message.tools_used = []
        mock_message.cost = 0.0
        mock_message.tokens = 0
        mock_message.created_at = datetime.utcnow()

        with patch('app.agents.coach.smart_coach_agent.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_message]
            mock_db_instance.close = MagicMock()

            messages = await coach.get_session_messages("session-123")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"


class TestCoachSystemPrompt:
    """Tests for coach system prompt"""

    def test_system_prompt_contains_capabilities(self):
        """Test system prompt describes capabilities"""
        assert "Codex" in COACH_SYSTEM_PROMPT
        assert "Timeline" in COACH_SYSTEM_PROMPT
        assert "Outline" in COACH_SYSTEM_PROMPT

    def test_system_prompt_describes_personality(self):
        """Test system prompt describes personality"""
        assert "encouraging" in COACH_SYSTEM_PROMPT.lower()
        assert "supportive" in COACH_SYSTEM_PROMPT.lower() or "teaching" in COACH_SYSTEM_PROMPT.lower()

    def test_system_prompt_has_context_placeholder(self):
        """Test system prompt has context placeholder"""
        assert "{context}" in COACH_SYSTEM_PROMPT
