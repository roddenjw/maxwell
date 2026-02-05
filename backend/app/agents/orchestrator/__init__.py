"""
Agent Orchestration for Maxwell

Coordinates multiple specialized agents to provide unified analysis.

Components:
- MaxwellUnified: Primary entry point - single cohesive entity
- SupervisorAgent: Intelligent query routing
- MaxwellSynthesizer: Unified voice synthesis
- WritingAssistantOrchestrator: Parallel agent execution
- CrossAgentReasoner: Conflict detection and mediation
"""

from app.agents.orchestrator.writing_assistant import (
    WritingAssistantOrchestrator,
    OrchestratorResult
)

from app.agents.orchestrator.maxwell_unified import (
    MaxwellUnified,
    MaxwellResponse,
    create_maxwell
)

from app.agents.orchestrator.supervisor_agent import (
    SupervisorAgent,
    RouteDecision,
    QueryIntent,
    QueryClassifier,
    create_supervisor_agent
)

from app.agents.orchestrator.maxwell_synthesizer import (
    MaxwellSynthesizer,
    SynthesizedFeedback,
    SynthesisTone,
    FeedbackDepth,
    TeachingMode,
    VoicePreferences,
    create_maxwell_synthesizer
)

from app.agents.orchestrator.cross_agent_reasoner import (
    CrossAgentReasoner,
    AgentConflict,
    StoryHealthAssessment,
    ConflictType,
    ConflictSeverity,
    create_cross_agent_reasoner
)

__all__ = [
    # Primary interface
    "MaxwellUnified",
    "MaxwellResponse",
    "create_maxwell",

    # Routing
    "SupervisorAgent",
    "RouteDecision",
    "QueryIntent",
    "QueryClassifier",
    "create_supervisor_agent",

    # Synthesis
    "MaxwellSynthesizer",
    "SynthesizedFeedback",
    "SynthesisTone",
    "FeedbackDepth",
    "TeachingMode",
    "VoicePreferences",
    "create_maxwell_synthesizer",

    # Legacy orchestrator (still available for direct access)
    "WritingAssistantOrchestrator",
    "OrchestratorResult",

    # Cross-agent reasoning
    "CrossAgentReasoner",
    "AgentConflict",
    "StoryHealthAssessment",
    "ConflictType",
    "ConflictSeverity",
    "create_cross_agent_reasoner",
]
