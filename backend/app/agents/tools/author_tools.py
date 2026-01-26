"""
Author Tools for Maxwell Agents

Tools for querying author profile, preferences, and feedback history.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.coach import WritingProfile, CoachingHistory, FeedbackPattern


class QueryAuthorProfileInput(BaseModel):
    """Input for querying author profile"""
    user_id: str = Field(description="The user ID")


class QueryAuthorProfile(BaseTool):
    """Query author's writing profile"""

    name: str = "query_author_profile"
    description: str = """Get the author's writing profile including style metrics, strengths, weaknesses, and preferences.
    Use this to personalize feedback and understand the author's writing patterns."""
    args_schema: Type[BaseModel] = QueryAuthorProfileInput

    def _run(self, user_id: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            profile = db.query(WritingProfile).filter(
                WritingProfile.user_id == user_id
            ).first()

            if not profile:
                return f"No writing profile found for user {user_id}"

            data = profile.profile_data or {}

            lines = [f"## Author Profile"]

            # Style metrics
            if data.get("style_metrics"):
                lines.append("\n### Style Metrics")
                for metric, value in data["style_metrics"].items():
                    lines.append(f"- {metric}: {value}")

            # Strengths
            if data.get("strengths"):
                lines.append("\n### Strengths")
                for s in data["strengths"]:
                    lines.append(f"- {s}")

            # Weaknesses
            if data.get("weaknesses"):
                lines.append("\n### Areas for Improvement")
                for w in data["weaknesses"]:
                    lines.append(f"- {w}")

            # Preferences
            if data.get("preferences"):
                lines.append("\n### Preferences")
                for key, value in data["preferences"].items():
                    lines.append(f"- {key}: {value}")

            # Overused words
            if data.get("overused_words"):
                lines.append("\n### Watch Words (Overused)")
                sorted_words = sorted(
                    data["overused_words"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                for word, count in sorted_words:
                    lines.append(f"- \"{word}\" (used {count}x)")

            # Favorite techniques
            if data.get("favorite_techniques"):
                lines.append("\n### Favorite Techniques")
                for tech in data["favorite_techniques"]:
                    lines.append(f"- {tech}")

            # Get feedback patterns
            patterns = db.query(FeedbackPattern).filter(
                FeedbackPattern.user_id == user_id
            ).order_by(FeedbackPattern.frequency.desc()).limit(5).all()

            if patterns:
                lines.append("\n### Recurring Patterns")
                for p in patterns:
                    lines.append(f"- {p.pattern_type}: {p.pattern_description} (seen {p.frequency}x)")

            if len(lines) == 1:
                lines.append("\nNo profile data available yet.")
                lines.append("Profile builds as the author writes and receives feedback.")

            return "\n".join(lines)

        finally:
            db.close()


class QueryFeedbackHistoryInput(BaseModel):
    """Input for querying feedback history"""
    user_id: str = Field(description="The user ID")
    manuscript_id: Optional[str] = Field(
        default=None,
        description="Optional: filter to specific manuscript"
    )
    feedback_type: Optional[str] = Field(
        default=None,
        description="Optional: filter by type (SUGGESTION, WARNING, PRAISE, CRITIQUE)"
    )
    reaction: Optional[str] = Field(
        default=None,
        description="Optional: filter by reaction (ACCEPTED, REJECTED, MODIFIED, IGNORED)"
    )
    limit: int = Field(default=10, description="Maximum number of entries to return")


class QueryFeedbackHistory(BaseTool):
    """Query author's feedback history"""

    name: str = "query_feedback_history"
    description: str = """Get the history of coaching feedback given to the author.
    Shows what suggestions were accepted, rejected, or modified.
    Use this to understand what feedback works well for this author."""
    args_schema: Type[BaseModel] = QueryFeedbackHistoryInput

    def _run(
        self,
        user_id: str,
        manuscript_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
        reaction: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            query = db.query(CoachingHistory).filter(
                CoachingHistory.user_id == user_id
            )

            if manuscript_id:
                query = query.filter(CoachingHistory.manuscript_id == manuscript_id)

            if feedback_type:
                query = query.filter(CoachingHistory.feedback_type == feedback_type)

            if reaction:
                query = query.filter(CoachingHistory.user_reaction == reaction)

            history = query.order_by(
                CoachingHistory.created_at.desc()
            ).limit(limit).all()

            if not history:
                return "No feedback history found"

            # Calculate statistics
            all_history = db.query(CoachingHistory).filter(
                CoachingHistory.user_id == user_id
            ).all()

            total = len(all_history)
            accepted = sum(1 for h in all_history if h.user_reaction == "ACCEPTED")
            rejected = sum(1 for h in all_history if h.user_reaction == "REJECTED")
            modified = sum(1 for h in all_history if h.user_reaction == "MODIFIED")

            lines = [
                f"## Feedback History",
                f"\n### Statistics",
                f"- Total feedback given: {total}",
                f"- Accepted: {accepted} ({accepted*100//max(total,1)}%)",
                f"- Rejected: {rejected} ({rejected*100//max(total,1)}%)",
                f"- Modified: {modified} ({modified*100//max(total,1)}%)",
            ]

            lines.append(f"\n### Recent Entries ({len(history)}):")

            for entry in history:
                reaction_badge = {
                    "ACCEPTED": "[OK]",
                    "REJECTED": "[NO]",
                    "MODIFIED": "[~]",
                    "IGNORED": "[--]"
                }.get(entry.user_reaction, "[?]")

                lines.append(f"\n{reaction_badge} {entry.feedback_type}")
                lines.append(f"   Date: {entry.created_at.strftime('%Y-%m-%d')}")

                # Show feedback summary
                feedback = entry.agent_feedback or {}
                if isinstance(feedback, dict):
                    if feedback.get("summary"):
                        lines.append(f"   Summary: {feedback['summary'][:100]}")
                    elif feedback.get("text"):
                        lines.append(f"   Text: {feedback['text'][:100]}")
                else:
                    lines.append(f"   Feedback: {str(feedback)[:100]}")

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_author_profile = QueryAuthorProfile()
query_feedback_history = QueryFeedbackHistory()
