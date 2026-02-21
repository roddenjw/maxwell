"""
Tests for Consistency and Research Agents

Tests for: ConsistencyAgent, ResearchAgent
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base.agent_config import AgentType, AgentConfig
from app.agents.specialized.consistency_agent import (
    ConsistencyAgent,
    ConsistencyFocus,
    ConsistencyIssue,
    ConsistencyResult,
    create_consistency_agent
)
from app.agents.specialized.research_agent import (
    ResearchAgent,
    WorldbuildingCategory,
    WorldbuildingElement,
    ResearchResult,
    create_research_agent
)
from app.services.llm_service import LLMResponse, LLMProvider


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response"""
    return LLMResponse(
        content=json.dumps({
            "recommendations": [],
            "issues": [
                {
                    "type": "character_contradiction",
                    "severity": "high",
                    "description": "Character eye color changed",
                    "source_text": "His blue eyes",
                    "conflicting_fact": "Previously described as having brown eyes",
                    "suggestion": "Update to match established description"
                }
            ],
            "praise": [],
            "overall_assessment": "Found one consistency issue."
        }),
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={"prompt_tokens": 500, "completion_tokens": 150, "total_tokens": 650},
        cost=0.0008
    )


@pytest.fixture
def mock_worldbuilding_response():
    """Create a mock worldbuilding response"""
    return LLMResponse(
        content=json.dumps({
            "recommendations": [
                {
                    "type": "worldbuilding",
                    "category": "culture",
                    "name": "The Merchant Guilds of Voria",
                    "text": "A powerful network of trading houses controlling sea commerce.",
                    "details": {
                        "key_aspects": ["trade monopoly", "political influence"],
                        "story_hooks": ["guild rivalry", "smuggling operations"]
                    },
                    "connections": ["Port City of Voria", "Royal Treasury"],
                    "draft_entity": {
                        "name": "Merchant Guilds of Voria",
                        "type": "FACTION",
                        "description": "Powerful trading consortium"
                    }
                }
            ],
            "issues": [],
            "praise": [],
            "overall_assessment": "Generated worldbuilding content."
        }),
        model="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        usage={"prompt_tokens": 400, "completion_tokens": 200, "total_tokens": 600},
        cost=0.0007
    )


class TestConsistencyIssue:
    """Tests for ConsistencyIssue dataclass"""

    def test_consistency_issue_creation(self):
        """Test basic ConsistencyIssue creation"""
        issue = ConsistencyIssue(
            issue_type="character_contradiction",
            severity="high",
            description="Eye color changed",
            source_text="His blue eyes sparkled",
            conflicting_fact="Previously described as brown eyes"
        )

        assert issue.issue_type == "character_contradiction"
        assert issue.severity == "high"
        assert "blue eyes" in issue.source_text

    def test_consistency_issue_to_dict(self):
        """Test ConsistencyIssue serialization"""
        issue = ConsistencyIssue(
            issue_type="timeline_error",
            severity="medium",
            description="Event occurs before character was born",
            source_text="She attended the coronation",
            conflicting_fact="Character born 10 years after coronation",
            location="Chapter 5",
            suggestion="Adjust timeline or age"
        )

        data = issue.to_dict()

        assert data["issue_type"] == "timeline_error"
        assert data["severity"] == "medium"
        assert data["location"] == "Chapter 5"
        assert data["suggestion"] == "Adjust timeline or age"


class TestConsistencyResult:
    """Tests for ConsistencyResult dataclass"""

    def test_consistency_result_creation(self):
        """Test basic ConsistencyResult creation"""
        result = ConsistencyResult(
            success=True,
            mode="realtime",
            issues=[],
            entities_checked=5,
            events_checked=10
        )

        assert result.success is True
        assert result.mode == "realtime"
        assert result.entities_checked == 5

    def test_consistency_result_to_dict(self):
        """Test ConsistencyResult serialization"""
        issue = ConsistencyIssue(
            issue_type="test",
            severity="high",
            description="Test issue",
            source_text="Test",
            conflicting_fact="Test"
        )

        result = ConsistencyResult(
            success=True,
            mode="full_scan",
            issues=[issue],
            entities_checked=10,
            events_checked=20,
            execution_time_ms=5000,
            cost=0.01
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["mode"] == "full_scan"
        assert data["issue_count"] == 1
        assert data["high_severity_count"] == 1
        assert data["execution_time_ms"] == 5000


class TestConsistencyFocus:
    """Tests for ConsistencyFocus enum"""

    def test_all_focus_areas_exist(self):
        """Test all focus areas are defined"""
        assert ConsistencyFocus.CHARACTER.value == "character"
        assert ConsistencyFocus.TIMELINE.value == "timeline"
        assert ConsistencyFocus.WORLD.value == "world"
        assert ConsistencyFocus.RELATIONSHIP.value == "relationship"
        assert ConsistencyFocus.LOCATION.value == "location"
        assert ConsistencyFocus.ALL.value == "all"


class TestConsistencyAgent:
    """Tests for ConsistencyAgent"""

    def test_consistency_agent_type(self):
        """Test ConsistencyAgent returns correct agent type"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        assert agent.agent_type == AgentType.CONTINUITY

    def test_consistency_agent_system_prompt(self):
        """Test ConsistencyAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "consistency" in prompt
        assert "character" in prompt
        assert "timeline" in prompt

    def test_consistency_agent_tools(self):
        """Test ConsistencyAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_entities" in tool_names
        assert "query_timeline" in tool_names

    def test_create_consistency_agent_factory(self):
        """Test create_consistency_agent factory function"""
        agent = create_consistency_agent(api_key="test-key")

        assert isinstance(agent, ConsistencyAgent)

    @pytest.mark.asyncio
    async def test_quick_check(self, mock_llm_response):
        """Test quick_check method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_entity_context', new_callable=AsyncMock, return_value="Entity context"), \
             patch.object(agent, '_load_timeline_context', new_callable=AsyncMock, return_value="Timeline context"), \
             patch.object(agent, '_load_world_context', new_callable=AsyncMock, return_value="World context"), \
             patch.object(agent, '_load_culture_context', new_callable=AsyncMock, return_value="Culture context"), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.quick_check(
                text="His blue eyes sparkled in the morning light.",
                user_id="test-user",
                manuscript_id="test-ms",
                focus=ConsistencyFocus.CHARACTER
            )

            assert isinstance(result, ConsistencyResult)
            assert result.mode == "realtime"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_quick_check_with_chapter_id(self, mock_llm_response):
        """Test quick_check with chapter_id parameter"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_entity_context', new_callable=AsyncMock, return_value="Entity context"), \
             patch.object(agent, '_load_timeline_context', new_callable=AsyncMock, return_value="Timeline context"), \
             patch.object(agent, '_load_world_context', new_callable=AsyncMock, return_value="World context"), \
             patch.object(agent, '_load_culture_context', new_callable=AsyncMock, return_value="Culture context"), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.quick_check(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms",
                focus=ConsistencyFocus.ALL,
                chapter_id="ch-123"
            )

            assert result.success is True

    @pytest.mark.asyncio
    async def test_quick_check_error_handling(self):
        """Test quick_check handles errors gracefully"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        with patch.object(agent, '_load_entity_context', side_effect=Exception("Context error")):
            result = await agent.quick_check(
                text="Test text",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is False
            assert "Context error" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_full_scan(self, mock_llm_response):
        """Test full_scan method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_character_profiles', new_callable=AsyncMock, return_value="Character profiles"), \
             patch.object(agent, '_load_full_timeline', new_callable=AsyncMock, return_value="Timeline"), \
             patch.object(agent, '_load_world_context', new_callable=AsyncMock, return_value="World"), \
             patch.object(agent, '_load_relationships', new_callable=AsyncMock, return_value="Relationships"), \
             patch.object(agent, '_load_culture_context', new_callable=AsyncMock, return_value="Culture"), \
             patch.object(agent, '_load_chapters', new_callable=AsyncMock, return_value=[{"id": "ch1", "title": "Chapter 1", "content": "Test content"}]), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_llm_response)

            result = await agent.full_scan(
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert isinstance(result, ConsistencyResult)
            assert result.mode == "full_scan"

    def test_parse_issues(self, mock_llm_response):
        """Test _parse_issues method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ConsistencyAgent(config=config, api_key="test-key")

        from app.agents.base.agent_base import AgentResult

        agent_result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=True,
            issues=[
                {
                    "type": "character_contradiction",
                    "severity": "high",
                    "description": "Eye color changed",
                    "source_text": "Blue eyes",
                    "conflicting_fact": "Brown eyes"
                }
            ]
        )

        issues = agent._parse_issues(agent_result)

        assert len(issues) == 1
        assert isinstance(issues[0], ConsistencyIssue)
        assert issues[0].severity == "high"


class TestWorldbuildingElement:
    """Tests for WorldbuildingElement dataclass"""

    def test_worldbuilding_element_creation(self):
        """Test basic WorldbuildingElement creation"""
        element = WorldbuildingElement(
            category="culture",
            name="Merchant Guild",
            description="A powerful trading organization.",
            details={"influence": "high"},
            connections=["Royal Court"]
        )

        assert element.category == "culture"
        assert element.name == "Merchant Guild"
        assert "trading" in element.description

    def test_worldbuilding_element_with_draft_entity(self):
        """Test WorldbuildingElement with draft_entity"""
        element = WorldbuildingElement(
            category="geography",
            name="Crystal Mountains",
            description="A mountain range with unique crystal formations.",
            details={"height": "very high", "resources": ["crystals", "iron"]},
            connections=["Dwarven Kingdom"],
            draft_entity={
                "name": "Crystal Mountains",
                "type": "LOCATION",
                "description": "Mountain range in the north"
            }
        )

        data = element.to_dict()

        assert data["draft_entity"] is not None
        assert data["draft_entity"]["type"] == "LOCATION"


class TestResearchResult:
    """Tests for ResearchResult dataclass"""

    def test_research_result_creation(self):
        """Test basic ResearchResult creation"""
        result = ResearchResult(
            success=True,
            topic="medieval castles",
            summary="Overview of castle defenses."
        )

        assert result.success is True
        assert result.topic == "medieval castles"
        assert result.elements == []

    def test_research_result_to_dict(self):
        """Test ResearchResult serialization"""
        element = WorldbuildingElement(
            category="geography",
            name="Test Location",
            description="Test description",
            details={},
            connections=[]
        )

        result = ResearchResult(
            success=True,
            topic="test topic",
            elements=[element],
            summary="Test summary",
            sources=["AI-generated"],
            suggestions=["Consider adding more detail"],
            execution_time_ms=1500,
            cost=0.005
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["element_count"] == 1
        assert len(data["suggestions"]) == 1


class TestWorldbuildingCategory:
    """Tests for WorldbuildingCategory enum"""

    def test_all_categories_exist(self):
        """Test all worldbuilding categories are defined"""
        expected = [
            "culture", "magic_system", "technology", "geography",
            "history", "politics", "religion", "economy", "creature", "language"
        ]

        for cat in expected:
            assert WorldbuildingCategory(cat) is not None


class TestResearchAgent:
    """Tests for ResearchAgent"""

    def test_research_agent_type(self):
        """Test ResearchAgent returns agent type"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        # Note: ResearchAgent reuses CONTINUITY type
        assert agent.agent_type == AgentType.CONTINUITY

    def test_research_agent_system_prompt(self):
        """Test ResearchAgent has appropriate system prompt"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        prompt = agent.system_prompt.lower()
        assert "worldbuilding" in prompt
        assert "culture" in prompt or "magic" in prompt

    def test_research_agent_tools(self):
        """Test ResearchAgent has correct tools"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        tools = agent._get_tools()
        tool_names = [t.name for t in tools]

        assert "query_entities" in tool_names
        assert "query_world_settings" in tool_names

    def test_create_research_agent_factory(self):
        """Test create_research_agent factory function"""
        agent = create_research_agent(api_key="test-key")

        assert isinstance(agent, ResearchAgent)

    @pytest.mark.asyncio
    async def test_generate_worldbuilding(self, mock_worldbuilding_response):
        """Test generate_worldbuilding method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_world_context', return_value="World context"), \
             patch.object(agent, '_load_relevant_entities', return_value="Entity context"), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_worldbuilding_response)

            result = await agent.generate_worldbuilding(
                topic="merchant guilds",
                user_id="test-user",
                manuscript_id="test-ms",
                constraints=["low magic", "medieval setting"],
                count=3
            )

            assert isinstance(result, ResearchResult)
            assert result.topic == "merchant guilds"

    @pytest.mark.asyncio
    async def test_generate_worldbuilding_with_category(self, mock_worldbuilding_response):
        """Test generate_worldbuilding with specific category"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_world_context', return_value="World context"), \
             patch.object(agent, '_load_relevant_entities', return_value="Entity context"), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_worldbuilding_response)

            result = await agent.generate_worldbuilding(
                topic="magic system",
                user_id="test-user",
                manuscript_id="test-ms",
                category=WorldbuildingCategory.MAGIC_SYSTEM
            )

            assert result.success

    @pytest.mark.asyncio
    async def test_generate_worldbuilding_error_handling(self):
        """Test generate_worldbuilding handles errors gracefully"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        with patch.object(agent, '_load_world_context', side_effect=Exception("World error")):
            result = await agent.generate_worldbuilding(
                topic="test",
                user_id="test-user",
                manuscript_id="test-ms"
            )

            assert result.success is False
            assert "World error" in result.summary

    @pytest.mark.asyncio
    async def test_research_topic(self, mock_worldbuilding_response):
        """Test research_topic method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch.object(agent, '_load_world_context', return_value="World context"), \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_worldbuilding_response)

            result = await agent.research_topic(
                topic="medieval castle defenses",
                user_id="test-user",
                purpose="worldbuilding for fantasy novel",
                questions=["What were common defensive features?"]
            )

            assert isinstance(result, ResearchResult)
            assert result.topic == "medieval castle defenses"
            assert any("AI-generated" in source for source in result.sources)

    @pytest.mark.asyncio
    async def test_research_topic_without_manuscript(self, mock_worldbuilding_response):
        """Test research_topic without manuscript context"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        with patch.object(agent, '_context_loader') as mock_loader, \
             patch('app.agents.base.agent_base.llm_service') as mock_service:

            mock_context = MagicMock()
            mock_context.to_prompt_context.return_value = "Test context"
            mock_loader.load_full_context = MagicMock(return_value=mock_context)
            mock_service.generate = AsyncMock(return_value=mock_worldbuilding_response)

            result = await agent.research_topic(
                topic="feudal society",
                user_id="test-user"
            )

            assert result.success

    def test_parse_elements(self, mock_worldbuilding_response):
        """Test _parse_elements method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        from app.agents.base.agent_base import AgentResult

        agent_result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=True,
            recommendations=[
                {
                    "type": "worldbuilding",
                    "category": "culture",
                    "name": "Test Culture",
                    "text": "A fascinating culture",
                    "details": {},
                    "connections": []
                }
            ]
        )

        elements = agent._parse_elements(agent_result)

        assert len(elements) == 1
        assert isinstance(elements[0], WorldbuildingElement)
        assert elements[0].category == "culture"

    def test_parse_elements_fallback(self):
        """Test _parse_elements falls back to raw response"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        from app.agents.base.agent_base import AgentResult

        agent_result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=True,
            recommendations=[],
            raw_response="This is raw research content."
        )

        elements = agent._parse_elements(agent_result)

        assert len(elements) == 1
        assert elements[0].name == "Research Results"
        assert "raw research" in elements[0].description

    def test_extract_summary(self):
        """Test _extract_summary method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        from app.agents.base.agent_base import AgentResult

        agent_result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=True,
            raw_response=json.dumps({"summary": "Test summary text"})
        )

        summary = agent._extract_summary(agent_result)

        assert summary == "Test summary text"

    def test_extract_suggestions(self):
        """Test _extract_suggestions method"""
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        agent = ResearchAgent(config=config, api_key="test-key")

        from app.agents.base.agent_base import AgentResult

        agent_result = AgentResult(
            agent_type=AgentType.CONTINUITY,
            success=True,
            raw_response=json.dumps({"suggestions": ["Suggestion 1", "Suggestion 2"]})
        )

        suggestions = agent._extract_suggestions(agent_result)

        assert len(suggestions) == 2
        assert "Suggestion 1" in suggestions
