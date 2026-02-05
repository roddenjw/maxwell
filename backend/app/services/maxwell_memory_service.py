"""
Maxwell Memory Service

Handles persistent conversation history and insight extraction.
Enables Maxwell to reference previous feedback and maintain context
across sessions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import re

from app.models.agent import MaxwellConversation, MaxwellInsight, MaxwellPreferences


class MaxwellMemoryService:
    """
    Service for managing Maxwell's conversation memory.

    Enables:
    - Persistent conversation storage
    - Insight extraction and retrieval
    - Context-aware responses ("You mentioned before...")
    - User preference management
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Conversation Management ====================

    def save_conversation(
        self,
        user_id: str,
        maxwell_response: str,
        response_type: str,
        interaction_type: str,
        manuscript_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        user_message: Optional[str] = None,
        analyzed_text: Optional[str] = None,
        feedback_data: Optional[Dict[str, Any]] = None,
        agents_consulted: Optional[List[str]] = None,
        focus_area: Optional[str] = None,
        cost: float = 0.0,
        tokens: int = 0,
        execution_time_ms: int = 0,
    ) -> MaxwellConversation:
        """
        Save a Maxwell conversation to the database.

        Args:
            user_id: User identifier
            maxwell_response: Maxwell's response text
            response_type: Type of response (chat, analysis, quick_check, explanation)
            interaction_type: How user interacted (chat, analysis, quick_check, explain)
            manuscript_id: Optional manuscript context
            chapter_id: Optional chapter context
            user_message: User's input message (for chat)
            analyzed_text: Text that was analyzed (for analysis)
            feedback_data: Synthesized feedback structure
            agents_consulted: List of agents that contributed
            focus_area: Focus area for quick checks
            cost: API cost
            tokens: Token count
            execution_time_ms: Execution time

        Returns:
            The created MaxwellConversation record
        """
        conversation = MaxwellConversation(
            user_id=user_id,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            interaction_type=interaction_type,
            user_message=user_message,
            analyzed_text=analyzed_text,
            maxwell_response=maxwell_response,
            response_type=response_type,
            feedback_data=feedback_data or {},
            agents_consulted=agents_consulted or [],
            focus_area=focus_area,
            cost=cost,
            tokens=tokens,
            execution_time_ms=execution_time_ms,
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        # Auto-extract insights from feedback data
        if feedback_data:
            self.extract_and_save_insights(conversation)

        return conversation

    def get_recent_conversations(
        self,
        user_id: str,
        manuscript_id: Optional[str] = None,
        limit: int = 20,
        interaction_type: Optional[str] = None,
    ) -> List[MaxwellConversation]:
        """
        Get recent conversations for a user.

        Args:
            user_id: User identifier
            manuscript_id: Optional filter by manuscript
            limit: Maximum number of conversations to return
            interaction_type: Optional filter by interaction type

        Returns:
            List of recent conversations, newest first
        """
        query = self.db.query(MaxwellConversation).filter(
            MaxwellConversation.user_id == user_id
        )

        if manuscript_id:
            query = query.filter(MaxwellConversation.manuscript_id == manuscript_id)

        if interaction_type:
            query = query.filter(MaxwellConversation.interaction_type == interaction_type)

        return query.order_by(desc(MaxwellConversation.created_at)).limit(limit).all()

    def get_conversation_context(
        self,
        user_id: str,
        manuscript_id: Optional[str] = None,
        lookback_days: int = 30,
        max_conversations: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for Maxwell to reference.

        Returns a summary of recent feedback that Maxwell can use
        for "You mentioned before..." references.

        Args:
            user_id: User identifier
            manuscript_id: Optional filter by manuscript
            lookback_days: How far back to look
            max_conversations: Maximum conversations to include

        Returns:
            List of conversation summaries
        """
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        query = self.db.query(MaxwellConversation).filter(
            and_(
                MaxwellConversation.user_id == user_id,
                MaxwellConversation.created_at >= cutoff
            )
        )

        if manuscript_id:
            query = query.filter(MaxwellConversation.manuscript_id == manuscript_id)

        conversations = query.order_by(
            desc(MaxwellConversation.created_at)
        ).limit(max_conversations).all()

        # Build context summaries
        context = []
        for conv in conversations:
            summary = {
                "id": conv.id,
                "type": conv.interaction_type,
                "date": conv.created_at.isoformat(),
                "focus": conv.focus_area,
                "agents": conv.agents_consulted,
            }

            # Add key feedback points if available
            if conv.feedback_data:
                if "priorities" in conv.feedback_data:
                    summary["key_issues"] = [
                        p.get("text", "")[:100] for p in conv.feedback_data.get("priorities", [])[:3]
                    ]
                if "highlights" in conv.feedback_data:
                    summary["strengths"] = [
                        h.get("text", "")[:100] for h in conv.feedback_data.get("highlights", [])[:2]
                    ]

            context.append(summary)

        return context

    # ==================== Insight Management ====================

    def extract_and_save_insights(
        self,
        conversation: MaxwellConversation,
    ) -> List[MaxwellInsight]:
        """
        Extract key insights from a conversation and save them.

        Insights enable quick retrieval for context-aware responses.

        Args:
            conversation: The conversation to extract insights from

        Returns:
            List of created insights
        """
        insights = []

        # Extract insights from feedback data
        feedback = conversation.feedback_data or {}

        # Extract from priorities (issues/suggestions)
        for priority in feedback.get("priorities", []):
            insight = MaxwellInsight(
                user_id=conversation.user_id,
                manuscript_id=conversation.manuscript_id,
                conversation_id=conversation.id,
                category=self._categorize_insight(priority.get("text", "")),
                insight_text=priority.get("text", ""),
                subject=self._extract_subject(priority.get("text", "")),
                sentiment="suggestion" if priority.get("severity") != "high" else "negative",
                importance=self._severity_to_importance(priority.get("severity", "medium")),
                resolved="pending",
            )
            insights.append(insight)

        # Extract from highlights (strengths)
        for highlight in feedback.get("highlights", []):
            insight = MaxwellInsight(
                user_id=conversation.user_id,
                manuscript_id=conversation.manuscript_id,
                conversation_id=conversation.id,
                category=highlight.get("aspect", "style"),
                insight_text=highlight.get("text", ""),
                subject=self._extract_subject(highlight.get("text", "")),
                sentiment="positive",
                importance=0.6,  # Positive feedback is moderately important
                resolved="addressed",  # Strengths don't need resolution
            )
            insights.append(insight)

        # Save all insights
        for insight in insights:
            self.db.add(insight)

        if insights:
            self.db.commit()

        return insights

    def get_relevant_insights(
        self,
        user_id: str,
        manuscript_id: Optional[str] = None,
        category: Optional[str] = None,
        subject: Optional[str] = None,
        include_resolved: bool = False,
        limit: int = 10,
    ) -> List[MaxwellInsight]:
        """
        Get relevant insights for context.

        Args:
            user_id: User identifier
            manuscript_id: Optional filter by manuscript
            category: Optional filter by category
            subject: Optional filter by subject
            include_resolved: Whether to include resolved insights
            limit: Maximum insights to return

        Returns:
            List of relevant insights, most important first
        """
        query = self.db.query(MaxwellInsight).filter(
            MaxwellInsight.user_id == user_id
        )

        if manuscript_id:
            query = query.filter(MaxwellInsight.manuscript_id == manuscript_id)

        if category:
            query = query.filter(MaxwellInsight.category == category)

        if subject:
            query = query.filter(MaxwellInsight.subject.ilike(f"%{subject}%"))

        if not include_resolved:
            query = query.filter(MaxwellInsight.resolved == "pending")

        return query.order_by(desc(MaxwellInsight.importance)).limit(limit).all()

    def mark_insight_resolved(
        self,
        insight_id: str,
        resolution: str = "addressed",
    ) -> Optional[MaxwellInsight]:
        """
        Mark an insight as resolved.

        Args:
            insight_id: Insight identifier
            resolution: Resolution status (addressed, dismissed)

        Returns:
            Updated insight or None if not found
        """
        insight = self.db.query(MaxwellInsight).filter(
            MaxwellInsight.id == insight_id
        ).first()

        if insight:
            insight.resolved = resolution
            self.db.commit()
            self.db.refresh(insight)

        return insight

    # ==================== Preferences Management ====================

    def get_preferences(self, user_id: str) -> MaxwellPreferences:
        """
        Get or create user preferences for Maxwell.

        Args:
            user_id: User identifier

        Returns:
            User's Maxwell preferences
        """
        prefs = self.db.query(MaxwellPreferences).filter(
            MaxwellPreferences.user_id == user_id
        ).first()

        if not prefs:
            prefs = MaxwellPreferences(user_id=user_id)
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)

        return prefs

    def update_preferences(
        self,
        user_id: str,
        preferred_tone: Optional[str] = None,
        feedback_depth: Optional[str] = None,
        teaching_mode: Optional[str] = None,
        priority_focus: Optional[str] = None,
        proactive_suggestions: Optional[str] = None,
        extra_preferences: Optional[Dict[str, Any]] = None,
    ) -> MaxwellPreferences:
        """
        Update user preferences for Maxwell.

        Args:
            user_id: User identifier
            preferred_tone: Tone preference (encouraging, direct, etc.)
            feedback_depth: Depth preference (brief, standard, comprehensive)
            teaching_mode: Teaching mode (on, off, auto)
            priority_focus: What to prioritize (plot, character, etc.)
            proactive_suggestions: Whether to give proactive suggestions
            extra_preferences: Additional preferences as JSON

        Returns:
            Updated preferences
        """
        prefs = self.get_preferences(user_id)

        if preferred_tone:
            prefs.preferred_tone = preferred_tone
        if feedback_depth:
            prefs.feedback_depth = feedback_depth
        if teaching_mode:
            prefs.teaching_mode = teaching_mode
        if priority_focus:
            prefs.priority_focus = priority_focus
        if proactive_suggestions:
            prefs.proactive_suggestions = proactive_suggestions
        if extra_preferences:
            prefs.extra_preferences = {**(prefs.extra_preferences or {}), **extra_preferences}

        self.db.commit()
        self.db.refresh(prefs)

        return prefs

    # ==================== Helper Methods ====================

    def _categorize_insight(self, text: str) -> str:
        """Categorize an insight based on its text content."""
        text_lower = text.lower()

        category_keywords = {
            "character": ["character", "protagonist", "antagonist", "motivation", "arc"],
            "plot": ["plot", "story", "conflict", "tension", "pacing"],
            "dialogue": ["dialogue", "conversation", "said", "speaks"],
            "style": ["style", "voice", "tone", "writing", "prose"],
            "worldbuilding": ["world", "setting", "magic", "system", "culture"],
            "pacing": ["pace", "pacing", "slow", "fast", "momentum"],
            "theme": ["theme", "message", "meaning", "symbolism"],
            "technique": ["technique", "show", "tell", "description"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return "general"

    def _extract_subject(self, text: str) -> Optional[str]:
        """Extract the main subject from insight text."""
        # Look for quoted text
        quotes = re.findall(r'"([^"]+)"', text)
        if quotes:
            return quotes[0][:50]

        # Look for proper nouns (capitalized words not at start)
        words = text.split()
        for i, word in enumerate(words):
            if i > 0 and word and word[0].isupper() and len(word) > 2:
                return word[:50]

        return None

    def _severity_to_importance(self, severity: str) -> float:
        """Convert severity to importance score."""
        mapping = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3,
        }
        return mapping.get(severity, 0.5)


def create_maxwell_memory_service(db: Session) -> MaxwellMemoryService:
    """Factory function to create a MaxwellMemoryService instance."""
    return MaxwellMemoryService(db)
