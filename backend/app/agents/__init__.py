"""
Maxwell LangChain Agent Framework

This module provides a comprehensive agent system for writing assistance,
including specialized agents for continuity, style, structure, and voice,
plus a Smart Coach for interactive writing guidance.
"""

from app.agents.base.agent_base import BaseMaxwellAgent
from app.agents.base.agent_config import AgentConfig, AgentType
from app.agents.base.context_loader import ContextLoader, AgentContext

__all__ = [
    "BaseMaxwellAgent",
    "AgentConfig",
    "AgentType",
    "ContextLoader",
    "AgentContext",
]
