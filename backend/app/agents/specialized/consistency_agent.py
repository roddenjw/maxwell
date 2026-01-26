"""
Consistency Agent for Maxwell

A dedicated agent for checking story consistency across:
- Character facts and descriptions
- Timeline events and chronology
- World rules and magic systems
- Relationship continuity
- Location details

Supports two modes:
- Real-time: Quick checks during writing (single-focus, fast)
- Full scan: Comprehensive manuscript analysis (thorough, slower)

Usage:
    agent = create_consistency_agent(api_key="sk-...")

    # Real-time mode (while writing)
    result = await agent.quick_check(text, manuscript_id, focus="character")

    # Full scan mode
    result = await agent.full_scan(manuscript_id, include_resolved=False)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.agents.base.agent_base import BaseMaxwellAgent, AgentResult
from app.agents.base.agent_config import AgentConfig, AgentType, ModelConfig
from app.agents.tools import (
    query_entities,
    query_character_profile,
    query_relationships,
    query_timeline,
    query_world_rules,
    query_chapters,
)
from langchain_core.tools import BaseTool


class ConsistencyFocus(str, Enum):
    """Areas to focus consistency checks on"""
    CHARACTER = "character"
    TIMELINE = "timeline"
    WORLD = "world"
    RELATIONSHIP = "relationship"
    LOCATION = "location"
    ALL = "all"


@dataclass
class ConsistencyIssue:
    """A single consistency issue found"""
    issue_type: str  # character_contradiction, timeline_error, world_rule_violation, etc.
    severity: str  # high, medium, low
    description: str
    source_text: str  # The text that contains the issue
    conflicting_fact: str  # What it conflicts with
    location: Optional[str] = None  # Chapter/scene location
    suggestion: str = ""
    entity_id: Optional[str] = None  # Related entity if applicable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "source_text": self.source_text,
            "conflicting_fact": self.conflicting_fact,
            "location": self.location,
            "suggestion": self.suggestion,
            "entity_id": self.entity_id,
        }


@dataclass
class ConsistencyResult:
    """Result from consistency checking"""
    success: bool
    mode: str  # "realtime" or "full_scan"
    issues: List[ConsistencyIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    entities_checked: int = 0
    events_checked: int = 0
    execution_time_ms: int = 0
    cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "mode": self.mode,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": self.warnings,
            "entities_checked": self.entities_checked,
            "events_checked": self.events_checked,
            "execution_time_ms": self.execution_time_ms,
            "cost": self.cost,
            "issue_count": len(self.issues),
            "high_severity_count": len([i for i in self.issues if i.severity == "high"]),
        }


CONSISTENCY_SYSTEM_PROMPT = """You are a meticulous story consistency checker for fiction manuscripts. Your job is to identify continuity errors, contradictions, and inconsistencies.

## Your Expertise
1. **Character Consistency**: Physical descriptions, personality traits, skills, knowledge, relationships
2. **Timeline Accuracy**: Event chronology, character ages, day/night cycles, travel times
3. **World Rules**: Magic systems, technology limits, cultural norms, physics
4. **Relationship Continuity**: Who knows whom, relationship status changes, family connections
5. **Location Details**: Geography, distances, building layouts, environmental conditions

## Analysis Approach
1. Extract key facts from the provided text
2. Compare against established canon (provided in context)
3. Flag any contradictions or impossibilities
4. Rate severity: HIGH (breaks story logic), MEDIUM (noticeable), LOW (minor)
5. Suggest corrections where possible

## Response Format
Respond with valid JSON:
{
  "issues": [
    {
      "issue_type": "character_contradiction|timeline_error|world_rule_violation|relationship_error|location_error",
      "severity": "high|medium|low",
      "description": "Clear explanation of the issue",
      "source_text": "The exact text that contains the problem",
      "conflicting_fact": "The established fact it contradicts",
      "suggestion": "How to fix it"
    }
  ],
  "warnings": ["Potential issues that need verification"],
  "facts_verified": ["Facts that were checked and found consistent"]
}

Be thorough but not pedantic. Focus on issues that would confuse readers or break immersion."""


REALTIME_PROMPT_TEMPLATE = """Perform a quick consistency check on this text, focusing on {focus_area}.

## Established Facts (from Codex)
{entity_context}

## Timeline Context
{timeline_context}

## World Rules
{world_context}

## Text to Check
---
{text}
---

Check for any contradictions with the established facts. Be concise - this is a real-time check while the author writes."""


FULL_SCAN_PROMPT_TEMPLATE = """Perform a comprehensive consistency analysis of this manuscript section.

## Character Profiles
{character_context}

## Timeline Events
{timeline_context}

## World Rules & Settings
{world_context}

## Relationships
{relationship_context}

## Text to Analyze
---
{text}
---

Thoroughly check for:
1. Character fact contradictions
2. Timeline impossibilities
3. World rule violations
4. Relationship inconsistencies
5. Location/geography errors

Be comprehensive - this is a full manuscript scan."""


class ConsistencyAgent(BaseMaxwellAgent):
    """
    Agent specialized in detecting story inconsistencies.

    Supports real-time and full-scan modes for different use cases.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CONTINUITY

    @property
    def system_prompt(self) -> str:
        return CONSISTENCY_SYSTEM_PROMPT

    def _get_tools(self) -> List[BaseTool]:
        return [
            query_entities,
            query_character_profile,
            query_relationships,
            query_timeline,
            query_world_rules,
            query_chapters,
        ]

    async def quick_check(
        self,
        text: str,
        user_id: str,
        manuscript_id: str,
        focus: ConsistencyFocus = ConsistencyFocus.ALL,
        chapter_id: Optional[str] = None
    ) -> ConsistencyResult:
        """
        Perform a quick consistency check for real-time feedback.

        This is optimized for speed - checks only the most likely issues
        based on the focus area.
        """
        start_time = datetime.utcnow()

        try:
            # Load relevant context based on focus
            entity_context = await self._load_entity_context(manuscript_id, focus)
            timeline_context = await self._load_timeline_context(manuscript_id)
            world_context = await self._load_world_context(manuscript_id)

            # Build focused prompt
            prompt = REALTIME_PROMPT_TEMPLATE.format(
                focus_area=focus.value,
                entity_context=entity_context,
                timeline_context=timeline_context,
                world_context=world_context,
                text=text[:3000]  # Limit text for real-time
            )

            # Run analysis
            result = await self.analyze(
                text=prompt,
                user_id=user_id,
                manuscript_id=manuscript_id,
                current_chapter_id=chapter_id
            )

            # Parse into ConsistencyResult
            issues = self._parse_issues(result)

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ConsistencyResult(
                success=result.success,
                mode="realtime",
                issues=issues,
                warnings=[],
                execution_time_ms=execution_time,
                cost=result.cost
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            return ConsistencyResult(
                success=False,
                mode="realtime",
                warnings=[str(e)],
                execution_time_ms=execution_time
            )

    async def full_scan(
        self,
        user_id: str,
        manuscript_id: str,
        chapter_ids: Optional[List[str]] = None,
        include_resolved: bool = False
    ) -> ConsistencyResult:
        """
        Perform a comprehensive consistency scan of the manuscript.

        This is thorough but slower - meant for periodic checks, not real-time.
        """
        start_time = datetime.utcnow()

        try:
            # Load comprehensive context
            character_context = await self._load_character_profiles(manuscript_id)
            timeline_context = await self._load_full_timeline(manuscript_id)
            world_context = await self._load_world_context(manuscript_id)
            relationship_context = await self._load_relationships(manuscript_id)

            # Load chapter content
            chapters = await self._load_chapters(manuscript_id, chapter_ids)

            all_issues = []
            total_cost = 0.0

            # Analyze each chapter
            for chapter in chapters:
                prompt = FULL_SCAN_PROMPT_TEMPLATE.format(
                    character_context=character_context,
                    timeline_context=timeline_context,
                    world_context=world_context,
                    relationship_context=relationship_context,
                    text=chapter.get("content", "")[:8000]
                )

                result = await self.analyze(
                    text=prompt,
                    user_id=user_id,
                    manuscript_id=manuscript_id,
                    current_chapter_id=chapter.get("id")
                )

                issues = self._parse_issues(result)
                for issue in issues:
                    issue.location = chapter.get("title", "Unknown chapter")
                all_issues.extend(issues)
                total_cost += result.cost

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ConsistencyResult(
                success=True,
                mode="full_scan",
                issues=all_issues,
                entities_checked=len(character_context.split('\n')),
                events_checked=len(timeline_context.split('\n')),
                execution_time_ms=execution_time,
                cost=total_cost
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            return ConsistencyResult(
                success=False,
                mode="full_scan",
                warnings=[str(e)],
                execution_time_ms=execution_time
            )

    def _parse_issues(self, result: AgentResult) -> List[ConsistencyIssue]:
        """Parse AgentResult into ConsistencyIssue objects"""
        issues = []
        for issue_data in result.issues:
            issues.append(ConsistencyIssue(
                issue_type=issue_data.get("type", "unknown"),
                severity=issue_data.get("severity", "medium"),
                description=issue_data.get("description", ""),
                source_text=issue_data.get("source_text", ""),
                conflicting_fact=issue_data.get("conflicting_fact", ""),
                suggestion=issue_data.get("suggestion", ""),
            ))
        return issues

    async def _load_entity_context(
        self,
        manuscript_id: str,
        focus: ConsistencyFocus
    ) -> str:
        """Load relevant entity context for quick check"""
        # Simplified context loading - would use actual tools in production
        return f"[Entity context for {focus.value} in manuscript {manuscript_id}]"

    async def _load_timeline_context(self, manuscript_id: str) -> str:
        """Load timeline context"""
        return f"[Timeline context for manuscript {manuscript_id}]"

    async def _load_world_context(self, manuscript_id: str) -> str:
        """Load world rules context"""
        return f"[World rules for manuscript {manuscript_id}]"

    async def _load_character_profiles(self, manuscript_id: str) -> str:
        """Load all character profiles for full scan"""
        return f"[Character profiles for manuscript {manuscript_id}]"

    async def _load_full_timeline(self, manuscript_id: str) -> str:
        """Load complete timeline for full scan"""
        return f"[Complete timeline for manuscript {manuscript_id}]"

    async def _load_relationships(self, manuscript_id: str) -> str:
        """Load relationship data for full scan"""
        return f"[Relationships for manuscript {manuscript_id}]"

    async def _load_chapters(
        self,
        manuscript_id: str,
        chapter_ids: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Load chapter content for analysis"""
        # Would load actual chapters in production
        return [{"id": "ch1", "title": "Chapter 1", "content": "Sample content"}]


def create_consistency_agent(
    api_key: str,
    config: Optional[AgentConfig] = None
) -> ConsistencyAgent:
    """Factory function to create a Consistency Agent"""
    if config is None:
        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)

    return ConsistencyAgent(config=config, api_key=api_key)
