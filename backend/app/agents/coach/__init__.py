"""
Smart Coach Agent for Maxwell

Conversational coaching agent with memory and tool access.
"""

from app.agents.coach.smart_coach_agent import (
    SmartCoachAgent,
    CoachResponse,
    create_smart_coach,
)

__all__ = [
    "SmartCoachAgent",
    "CoachResponse",
    "create_smart_coach",
]
