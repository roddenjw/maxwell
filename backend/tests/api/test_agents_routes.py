"""
Tests for Agent API Routes

Tests endpoints for:
- Multi-agent analysis
- Single-agent quick checks
- Suggestion feedback
- Author insights
- Smart Coach
- Consistency checking
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.agents.base.agent_config import AgentType
from app.agents.base.agent_base import AgentResult
from app.agents.orchestrator.writing_assistant import OrchestratorResult
from app.agents.coach.smart_coach_agent import CoachResponse


client = TestClient(app)


@pytest.fixture
def mock_orchestrator_result():
    """Create a mock orchestrator result"""
    return OrchestratorResult(
        success=True,
        recommendations=[
            {"type": "style", "severity": "medium", "text": "Vary sentence length.", "source_agent": "style"}
        ],
        issues=[],
        teaching_points=["Sentence variety improves rhythm."],
        praise=[{"aspect": "dialogue", "text": "Strong voices."}],
        agent_results={},
        total_cost=0.005,
        total_tokens=500,
        execution_time_ms=2500,
        author_insights={"strengths": ["dialogue"]}
    )


@pytest.fixture
def mock_agent_result():
    """Create a mock agent result"""
    return AgentResult(
        agent_type=AgentType.STYLE,
        success=True,
        recommendations=[{"type": "style", "text": "Test recommendation"}],
        issues=[],
        teaching_points=["Test teaching point"],
        usage={"total_tokens": 150},
        cost=0.001,
        execution_time_ms=1000
    )


@pytest.fixture
def mock_coach_response():
    """Create a mock coach response"""
    return CoachResponse(
        content="I'd be happy to help with your story!",
        tools_used=["query_entities"],
        tool_results={},
        cost=0.0007,
        tokens=200,
        session_id="session-123"
    )


class TestAnalyzeEndpoint:
    """Tests for POST /api/agents/analyze"""

    def test_analyze_success(self, mock_orchestrator_result):
        """Test successful multi-agent analysis"""
        with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(return_value=mock_orchestrator_result)
            MockOrchestrator.return_value = mock_instance

            with patch('app.api.routes.agents._store_analysis'):
                response = client.post("/api/agents/analyze", json={
                    "api_key": "test-key",
                    "text": "Test text for analysis.",
                    "user_id": "test-user",
                    "manuscript_id": "test-ms"
                })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "cost" in data

    def test_analyze_with_specific_agents(self, mock_orchestrator_result):
        """Test analysis with specific agents"""
        with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(return_value=mock_orchestrator_result)
            MockOrchestrator.return_value = mock_instance

            with patch('app.api.routes.agents._store_analysis'):
                response = client.post("/api/agents/analyze", json={
                    "api_key": "test-key",
                    "text": "Test text.",
                    "user_id": "test-user",
                    "manuscript_id": "test-ms",
                    "agents": ["style", "voice"]
                })

        assert response.status_code == 200
        # Verify orchestrator was called with limited agents
        call_args = MockOrchestrator.call_args
        assert call_args is not None

    def test_analyze_with_model_selection(self, mock_orchestrator_result):
        """Test analysis with custom model"""
        with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(return_value=mock_orchestrator_result)
            MockOrchestrator.return_value = mock_instance

            with patch('app.api.routes.agents._store_analysis'):
                response = client.post("/api/agents/analyze", json={
                    "api_key": "test-key",
                    "text": "Test text.",
                    "user_id": "test-user",
                    "manuscript_id": "test-ms",
                    "model_provider": "openai",
                    "model_name": "gpt-4o"
                })

        assert response.status_code == 200

    def test_analyze_error_handling(self):
        """Test error handling in analysis"""
        with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock(side_effect=Exception("API Error"))
            MockOrchestrator.return_value = mock_instance

            response = client.post("/api/agents/analyze", json={
                "api_key": "test-key",
                "text": "Test text.",
                "user_id": "test-user",
                "manuscript_id": "test-ms"
            })

        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]


class TestQuickCheckEndpoint:
    """Tests for POST /api/agents/quick-check"""

    def test_quick_check_success(self, mock_agent_result):
        """Test successful quick check"""
        with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
            mock_instance = MagicMock()
            mock_instance.quick_check = AsyncMock(return_value=mock_agent_result)
            MockOrchestrator.return_value = mock_instance

            response = client.post("/api/agents/quick-check", json={
                "api_key": "test-key",
                "text": "Test text.",
                "user_id": "test-user",
                "manuscript_id": "test-ms",
                "agent_type": "style"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_quick_check_invalid_agent_type(self):
        """Test quick check with invalid agent type"""
        response = client.post("/api/agents/quick-check", json={
            "api_key": "test-key",
            "text": "Test text.",
            "user_id": "test-user",
            "manuscript_id": "test-ms",
            "agent_type": "invalid_agent"
        })

        assert response.status_code == 400
        assert "Invalid agent type" in response.json()["detail"]

    def test_quick_check_all_agent_types(self, mock_agent_result):
        """Test quick check works with all valid agent types"""
        valid_types = ["continuity", "style", "structure", "voice"]

        for agent_type in valid_types:
            with patch('app.api.routes.agents.WritingAssistantOrchestrator') as MockOrchestrator:
                mock_instance = MagicMock()
                mock_instance.quick_check = AsyncMock(return_value=mock_agent_result)
                MockOrchestrator.return_value = mock_instance

                response = client.post("/api/agents/quick-check", json={
                    "api_key": "test-key",
                    "text": "Test text.",
                    "user_id": "test-user",
                    "manuscript_id": "test-ms",
                    "agent_type": agent_type
                })

                assert response.status_code == 200, f"Failed for agent type: {agent_type}"


class TestFeedbackEndpoint:
    """Tests for POST /api/agents/feedback"""

    def test_record_feedback_accepted(self):
        """Test recording accepted feedback"""
        mock_feedback = MagicMock()
        mock_feedback.id = "feedback-123"
        mock_feedback.action = "accepted"

        with patch('app.api.routes.agents.author_learning_service') as mock_service:
            mock_service.record_suggestion_feedback.return_value = mock_feedback

            response = client.post("/api/agents/feedback", json={
                "user_id": "test-user",
                "agent_type": "style",
                "suggestion_type": "sentence_variety",
                "suggestion_text": "Vary sentence length.",
                "action": "accepted"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["action"] == "accepted"

    def test_record_feedback_rejected(self):
        """Test recording rejected feedback"""
        mock_feedback = MagicMock()
        mock_feedback.id = "feedback-456"
        mock_feedback.action = "rejected"

        with patch('app.api.routes.agents.author_learning_service') as mock_service:
            mock_service.record_suggestion_feedback.return_value = mock_feedback

            response = client.post("/api/agents/feedback", json={
                "user_id": "test-user",
                "agent_type": "style",
                "suggestion_type": "word_choice",
                "suggestion_text": "Change 'very' to 'extremely'.",
                "action": "rejected",
                "user_explanation": "I prefer 'very' here."
            })

        assert response.status_code == 200

    def test_record_feedback_modified(self):
        """Test recording modified feedback"""
        mock_feedback = MagicMock()
        mock_feedback.id = "feedback-789"
        mock_feedback.action = "modified"

        with patch('app.api.routes.agents.author_learning_service') as mock_service:
            mock_service.record_suggestion_feedback.return_value = mock_feedback

            response = client.post("/api/agents/feedback", json={
                "user_id": "test-user",
                "agent_type": "voice",
                "suggestion_type": "dialogue",
                "suggestion_text": "Make dialogue more distinct.",
                "action": "modified",
                "original_text": "He said hello.",
                "modified_text": "He grunted a greeting."
            })

        assert response.status_code == 200

    def test_record_feedback_invalid_action(self):
        """Test feedback with invalid action"""
        response = client.post("/api/agents/feedback", json={
            "user_id": "test-user",
            "agent_type": "style",
            "suggestion_type": "test",
            "suggestion_text": "Test suggestion.",
            "action": "invalid_action"
        })

        assert response.status_code == 400
        assert "Invalid action" in response.json()["detail"]


class TestInsightsEndpoint:
    """Tests for GET /api/agents/insights/{user_id}"""

    def test_get_insights_success(self):
        """Test getting author insights"""
        mock_insights = {
            "common_issues": [
                {"category": "passive_voice", "total_occurrences": 15}
            ],
            "strengths": [{"area": "dialogue", "consistency_score": 85}],
            "improvement_areas": [],
            "progress": {"overall_improvement": 20}
        }

        with patch('app.api.routes.agents.author_learning_service') as mock_service:
            mock_service.get_author_insights.return_value = mock_insights

            response = client.get("/api/agents/insights/test-user")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "common_issues" in data["data"]

    def test_get_insights_error(self):
        """Test insights error handling"""
        with patch('app.api.routes.agents.author_learning_service') as mock_service:
            mock_service.get_author_insights.side_effect = Exception("Database error")

            response = client.get("/api/agents/insights/test-user")

        assert response.status_code == 500


class TestAgentTypesEndpoint:
    """Tests for GET /api/agents/types"""

    def test_get_agent_types(self):
        """Test getting available agent types"""
        response = client.get("/api/agents/types")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 4

        types = [item["type"] for item in data["data"]]
        assert "continuity" in types
        assert "style" in types
        assert "structure" in types
        assert "voice" in types

    def test_agent_types_have_descriptions(self):
        """Test agent types have descriptions"""
        response = client.get("/api/agents/types")

        for agent in response.json()["data"]:
            assert "name" in agent
            assert "description" in agent
            assert len(agent["description"]) > 10


class TestCoachSessionEndpoint:
    """Tests for POST /api/agents/coach/session"""

    def test_start_session_success(self):
        """Test starting a coach session"""
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session.title = "Test Session"
        mock_session.manuscript_id = "test-ms"
        mock_session.status = "active"
        mock_session.created_at = MagicMock()
        mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        with patch('app.api.routes.agents.create_smart_coach') as mock_create:
            mock_coach = MagicMock()
            mock_coach.start_session = AsyncMock(return_value=mock_session)
            mock_create.return_value = mock_coach

            response = client.post("/api/agents/coach/session", json={
                "api_key": "test-key",
                "user_id": "test-user",
                "manuscript_id": "test-ms",
                "title": "Test Session"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "session-123"

    def test_start_session_with_initial_context(self):
        """Test starting session with initial context"""
        mock_session = MagicMock()
        mock_session.id = "session-456"
        mock_session.title = "Context Session"
        mock_session.manuscript_id = "test-ms"
        mock_session.status = "active"
        mock_session.created_at = MagicMock()
        mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        with patch('app.api.routes.agents.create_smart_coach') as mock_create:
            mock_coach = MagicMock()
            mock_coach.start_session = AsyncMock(return_value=mock_session)
            mock_create.return_value = mock_coach

            response = client.post("/api/agents/coach/session", json={
                "api_key": "test-key",
                "user_id": "test-user",
                "manuscript_id": "test-ms",
                "initial_context": {"chapter_id": "ch-1", "selected_text": "Test"}
            })

        assert response.status_code == 200


class TestCoachChatEndpoint:
    """Tests for POST /api/agents/coach/chat"""

    def test_chat_success(self, mock_coach_response):
        """Test successful chat message"""
        with patch('app.api.routes.agents.create_smart_coach') as mock_create:
            mock_coach = MagicMock()
            mock_coach.chat = AsyncMock(return_value=mock_coach_response)
            mock_create.return_value = mock_coach

            response = client.post("/api/agents/coach/chat", json={
                "api_key": "test-key",
                "user_id": "test-user",
                "session_id": "session-123",
                "message": "Who is my main character?"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content" in data["data"]
        assert "cost" in data

    def test_chat_with_context(self, mock_coach_response):
        """Test chat with additional context"""
        with patch('app.api.routes.agents.create_smart_coach') as mock_create:
            mock_coach = MagicMock()
            mock_coach.chat = AsyncMock(return_value=mock_coach_response)
            mock_create.return_value = mock_coach

            response = client.post("/api/agents/coach/chat", json={
                "api_key": "test-key",
                "user_id": "test-user",
                "session_id": "session-123",
                "message": "What do you think of this?",
                "context": {
                    "selected_text": "The knight rode into battle.",
                    "chapter_id": "ch-5"
                }
            })

        assert response.status_code == 200

    def test_chat_error_handling(self):
        """Test chat error handling"""
        with patch('app.api.routes.agents.create_smart_coach') as mock_create:
            mock_coach = MagicMock()
            mock_coach.chat = AsyncMock(side_effect=Exception("Session error"))
            mock_create.return_value = mock_coach

            response = client.post("/api/agents/coach/chat", json={
                "api_key": "test-key",
                "user_id": "test-user",
                "session_id": "nonexistent",
                "message": "Hello?"
            })

        assert response.status_code == 500


class TestListCoachSessionsEndpoint:
    """Tests for GET /api/agents/coach/sessions/{user_id}"""

    def test_list_sessions_success(self, test_db):
        """Test listing coach sessions"""
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session.title = "Test Session"
        mock_session.manuscript_id = "test-ms"
        mock_session.message_count = 5
        mock_session.total_cost = 0.01
        mock_session.status = "active"
        mock_session.created_at = MagicMock()
        mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_session.updated_at = MagicMock()
        mock_session.updated_at.isoformat.return_value = "2024-01-02T00:00:00"
        mock_session.last_message_at = None

        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = [mock_session]
            mock_db.close = MagicMock()

            response = client.get("/api/agents/coach/sessions/test-user")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

    def test_list_sessions_with_manuscript_filter(self, test_db):
        """Test filtering sessions by manuscript"""
        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = []
            mock_db.close = MagicMock()

            response = client.get("/api/agents/coach/sessions/test-user?manuscript_id=test-ms")

        assert response.status_code == 200


class TestArchiveCoachSessionEndpoint:
    """Tests for PUT /api/agents/coach/session/{session_id}/archive"""

    def test_archive_session_success(self, test_db):
        """Test archiving a session"""
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session.user_id = "test-user"
        mock_session.status = "active"

        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            mock_db.commit = MagicMock()
            mock_db.close = MagicMock()

            response = client.put(
                "/api/agents/coach/session/session-123/archive",
                params={"user_id": "test-user"}
            )

        assert response.status_code == 200
        assert mock_session.status == "archived"

    def test_archive_session_not_found(self, test_db):
        """Test archiving non-existent session"""
        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.close = MagicMock()

            response = client.put(
                "/api/agents/coach/session/nonexistent/archive",
                params={"user_id": "test-user"}
            )

        assert response.status_code == 404


class TestConsistencyCheckEndpoint:
    """Tests for POST /api/agents/consistency/check

    Note: These tests are skipped because the endpoint uses dynamic imports
    which are difficult to mock. The ConsistencyAgent is tested separately
    in tests/agents/specialized/test_consistency_research_agents.py
    """

    @pytest.mark.skip(reason="Dynamic import inside endpoint is difficult to mock. Agent tested separately.")
    def test_consistency_check_success(self):
        """Test quick consistency check"""
        pass

    @pytest.mark.skip(reason="Dynamic import inside endpoint is difficult to mock. Agent tested separately.")
    def test_consistency_check_with_all_focus(self):
        """Test consistency check with 'all' focus"""
        pass


class TestAnalysisHistoryEndpoint:
    """Tests for GET /api/agents/history/{user_id}"""

    def test_get_history_success(self, test_db):
        """Test getting analysis history"""
        mock_analysis = MagicMock()
        mock_analysis.id = "analysis-123"
        mock_analysis.manuscript_id = "test-ms"
        mock_analysis.agent_types = ["style", "voice"]
        mock_analysis.total_cost = 0.005
        mock_analysis.created_at = MagicMock()
        mock_analysis.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_analysis.recommendations = [{"text": "Test"}]
        mock_analysis.issues = []
        mock_analysis.user_rating = 4

        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = [mock_analysis]
            mock_db.close = MagicMock()

            response = client.get("/api/agents/history/test-user")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["recommendation_count"] == 1


class TestRateAnalysisEndpoint:
    """Tests for PUT /api/agents/analysis/{analysis_id}/rate"""

    def test_rate_analysis_success(self, test_db):
        """Test rating an analysis"""
        mock_analysis = MagicMock()
        mock_analysis.id = "analysis-123"
        mock_analysis.user_rating = None

        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
            mock_db.commit = MagicMock()
            mock_db.close = MagicMock()

            response = client.put(
                "/api/agents/analysis/analysis-123/rate",
                params={"rating": 4}
            )

        assert response.status_code == 200
        assert mock_analysis.user_rating == 4

    def test_rate_analysis_invalid_rating(self, test_db):
        """Test rating with invalid value"""
        response = client.put(
            "/api/agents/analysis/analysis-123/rate",
            params={"rating": 6}  # Invalid - must be 1-5
        )

        assert response.status_code == 400

    def test_rate_analysis_not_found(self, test_db):
        """Test rating non-existent analysis"""
        with patch('app.api.routes.agents.SessionLocal') as MockSession:
            mock_db = MagicMock()
            MockSession.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.close = MagicMock()

            response = client.put(
                "/api/agents/analysis/nonexistent/rate",
                params={"rating": 4}
            )

        assert response.status_code == 404
