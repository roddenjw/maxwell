"""
Agent Orchestration for Maxwell

Coordinates multiple specialized agents to provide unified analysis.

Components:
- MaxwellUnified: Primary entry point - single cohesive entity
- SupervisorAgent: Intelligent query routing
- MaxwellSynthesizer: Unified voice synthesis
- WritingAssistantOrchestrator: Parallel agent execution
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
    create_maxwell_synthesizer
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
    "create_maxwell_synthesizer",

    # Legacy orchestrator (still available for direct access)
    "WritingAssistantOrchestrator",
    "OrchestratorResult",
]
