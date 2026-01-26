"""
Writing Assistant Orchestrator

Coordinates multiple specialized agents to provide comprehensive writing analysis.
Runs agents in parallel and synthesizes their recommendations.

Features:
- Parallel execution of Continuity, Style, Structure, and Voice agents
- Intelligent recommendation deduplication
- Priority-based sorting
- Cost aggregation
- Teaching point collection
- Author learning integration
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from app.agents.base.agent_config import AgentConfig, AgentType, ModelConfig, ModelProvider
from app.agents.base.agent_base import AgentResult
from app.agents.specialized.continuity_agent import create_continuity_agent
from app.agents.specialized.style_agent import create_style_agent
from app.agents.specialized.structure_agent import create_structure_agent
from app.agents.specialized.voice_agent import create_voice_agent
from app.services.author_learning_service import author_learning_service


@dataclass
class OrchestratorResult:
    """Combined result from all agents"""
    success: bool
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    teaching_points: List[str] = field(default_factory=list)
    praise: List[Dict[str, Any]] = field(default_factory=list)

    # Individual agent results
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)

    # Aggregated metrics
    total_cost: float = 0.0
    total_tokens: int = 0
    execution_time_ms: int = 0

    # Author learning
    author_insights: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "recommendations": self.recommendations,
            "issues": self.issues,
            "teaching_points": self.teaching_points,
            "praise": self.praise,
            "agent_results": {
                k: v.to_dict() for k, v in self.agent_results.items()
            },
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "execution_time_ms": self.execution_time_ms,
            "author_insights": self.author_insights
        }


class WritingAssistantOrchestrator:
    """
    Orchestrates multiple specialized agents for comprehensive writing analysis.

    Usage:
        orchestrator = WritingAssistantOrchestrator(api_key="sk-...")
        result = await orchestrator.analyze(
            text="The knight rode through the forest...",
            user_id="user123",
            manuscript_id="ms456"
        )
    """

    def __init__(
        self,
        api_key: str,
        model_config: Optional[ModelConfig] = None,
        enabled_agents: Optional[List[AgentType]] = None
    ):
        """
        Initialize the orchestrator.

        Args:
            api_key: API key for LLM provider
            model_config: Optional model configuration (uses default if not provided)
            enabled_agents: Which agents to run (defaults to all four)
        """
        self.api_key = api_key
        self.model_config = model_config

        self.enabled_agents = enabled_agents or [
            AgentType.CONTINUITY,
            AgentType.STYLE,
            AgentType.STRUCTURE,
            AgentType.VOICE,
        ]

    def _create_agents(self) -> Dict[AgentType, Any]:
        """Create configured agent instances"""
        agents = {}

        if AgentType.CONTINUITY in self.enabled_agents:
            config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
            if self.model_config:
                config.model_config = self.model_config
            agents[AgentType.CONTINUITY] = create_continuity_agent(
                self.api_key, config
            )

        if AgentType.STYLE in self.enabled_agents:
            config = AgentConfig.for_agent_type(AgentType.STYLE)
            if self.model_config:
                config.model_config = self.model_config
            agents[AgentType.STYLE] = create_style_agent(
                self.api_key, config
            )

        if AgentType.STRUCTURE in self.enabled_agents:
            config = AgentConfig.for_agent_type(AgentType.STRUCTURE)
            if self.model_config:
                config.model_config = self.model_config
            agents[AgentType.STRUCTURE] = create_structure_agent(
                self.api_key, config
            )

        if AgentType.VOICE in self.enabled_agents:
            config = AgentConfig.for_agent_type(AgentType.VOICE)
            if self.model_config:
                config.model_config = self.model_config
            agents[AgentType.VOICE] = create_voice_agent(
                self.api_key, config
            )

        return agents

    async def analyze(
        self,
        text: str,
        user_id: str,
        manuscript_id: str,
        current_chapter_id: Optional[str] = None,
        include_author_insights: bool = True
    ) -> OrchestratorResult:
        """
        Run comprehensive writing analysis with all enabled agents.

        Args:
            text: Text to analyze
            user_id: User ID for context
            manuscript_id: Manuscript ID for context
            current_chapter_id: Optional current chapter
            include_author_insights: Whether to include author learning data

        Returns:
            OrchestratorResult with combined recommendations
        """
        start_time = datetime.utcnow()

        # Create agents
        agents = self._create_agents()

        if not agents:
            return OrchestratorResult(
                success=False,
                issues=[{
                    "type": "error",
                    "severity": "high",
                    "description": "No agents enabled"
                }]
            )

        # Run all agents in parallel
        tasks = []
        agent_order = []

        for agent_type, agent in agents.items():
            agent_order.append(agent_type)
            tasks.append(
                agent.analyze(
                    text=text,
                    user_id=user_id,
                    manuscript_id=manuscript_id,
                    current_chapter_id=current_chapter_id
                )
            )

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results = {}
        all_recommendations = []
        all_issues = []
        all_teaching_points = []
        all_praise = []
        total_cost = 0.0
        total_tokens = 0

        for agent_type, result in zip(agent_order, results):
            if isinstance(result, Exception):
                # Handle agent failure
                agent_results[agent_type.value] = AgentResult(
                    agent_type=agent_type,
                    success=False,
                    issues=[{
                        "type": "agent_error",
                        "severity": "medium",
                        "description": f"{agent_type.value} agent failed: {str(result)}"
                    }]
                )
                continue

            agent_results[agent_type.value] = result

            # Collect recommendations with agent source
            for rec in result.recommendations:
                rec["source_agent"] = agent_type.value
                all_recommendations.append(rec)

            # Collect issues with agent source
            for issue in result.issues:
                issue["source_agent"] = agent_type.value
                all_issues.append(issue)

            # Collect teaching points
            all_teaching_points.extend(result.teaching_points)

            # Collect praise
            for rec in result.recommendations:
                if rec.get("type") == "praise":
                    all_praise.append(rec)

            # Aggregate costs
            total_cost += result.cost
            total_tokens += result.usage.get("total_tokens", 0)

        # Deduplicate and prioritize recommendations
        recommendations = self._deduplicate_recommendations(all_recommendations)
        issues = self._deduplicate_issues(all_issues)
        teaching_points = list(set(all_teaching_points))[:10]  # Limit

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2, "positive": 3}
        recommendations.sort(
            key=lambda x: severity_order.get(x.get("severity", "medium"), 1)
        )
        issues.sort(
            key=lambda x: severity_order.get(x.get("severity", "medium"), 1)
        )

        # Get author insights if requested
        author_insights = None
        if include_author_insights:
            try:
                author_insights = author_learning_service.get_author_insights(user_id)
            except Exception:
                pass  # Don't fail if insights unavailable

        # Filter out suppressed suggestion types based on author learning
        recommendations = self._filter_suppressed_suggestions(
            recommendations, user_id
        )

        # Calculate execution time
        execution_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )

        return OrchestratorResult(
            success=True,
            recommendations=recommendations,
            issues=issues,
            teaching_points=teaching_points,
            praise=all_praise,
            agent_results=agent_results,
            total_cost=total_cost,
            total_tokens=total_tokens,
            execution_time_ms=execution_time_ms,
            author_insights=author_insights
        )

    def _deduplicate_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate recommendations from different agents.

        Uses text similarity and type matching.
        """
        if not recommendations:
            return []

        seen_keys = set()
        unique = []

        for rec in recommendations:
            # Create a key from type and text prefix
            rec_type = rec.get("type", "general")
            rec_text = rec.get("text", "")[:100].lower()
            key = f"{rec_type}:{rec_text}"

            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(rec)

        return unique

    def _deduplicate_issues(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate issues from different agents."""
        if not issues:
            return []

        seen_keys = set()
        unique = []

        for issue in issues:
            issue_type = issue.get("type", "general")
            description = issue.get("description", "")[:100].lower()
            key = f"{issue_type}:{description}"

            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(issue)

        return unique

    def _filter_suppressed_suggestions(
        self,
        recommendations: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Filter out suggestion types the author consistently rejects.

        Based on author learning data, reduces frequency of disliked suggestions.
        """
        filtered = []

        for rec in recommendations:
            suggestion_type = rec.get("type", "general")

            # Check if this type should be suppressed
            if author_learning_service.should_suppress_suggestion_type(
                user_id, suggestion_type
            ):
                # Only suppress medium/low severity
                if rec.get("severity") in ["medium", "low"]:
                    continue

            filtered.append(rec)

        return filtered

    async def quick_check(
        self,
        text: str,
        user_id: str,
        manuscript_id: str,
        focus_area: AgentType
    ) -> AgentResult:
        """
        Run a single agent for quick feedback.

        Useful for real-time checks while writing.
        """
        agents = self._create_agents()
        agent = agents.get(focus_area)

        if not agent:
            return AgentResult(
                agent_type=focus_area,
                success=False,
                issues=[{
                    "type": "error",
                    "description": f"Agent {focus_area.value} not available"
                }]
            )

        return await agent.analyze(
            text=text,
            user_id=user_id,
            manuscript_id=manuscript_id
        )
