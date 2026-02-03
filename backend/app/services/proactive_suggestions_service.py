"""
Proactive Suggestions Service

Provides background analysis and gentle nudges to help writers
catch issues before they become problems.

Features:
- Queue chapters for background analysis
- Generate nudges based on detected issues
- Track dismissed nudges to avoid repetition
- Weekly insights summary generation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON, ForeignKey, desc, and_
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.agent import MaxwellPreferences


class NudgeType(Enum):
    """Types of proactive nudges Maxwell can give."""
    CONSISTENCY_ISSUE = "consistency_issue"
    PACING_CONCERN = "pacing_concern"
    CHARACTER_DRIFT = "character_drift"
    STYLE_PATTERN = "style_pattern"
    PLOT_HOLE = "plot_hole"
    DIALOGUE_ISSUE = "dialogue_issue"
    WORLDBUILDING_GAP = "worldbuilding_gap"
    WEEKLY_INSIGHT = "weekly_insight"


class NudgePriority(Enum):
    """Priority level for nudges."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Nudge:
    """A proactive suggestion from Maxwell."""
    id: str
    nudge_type: NudgeType
    priority: NudgePriority
    title: str  # Short title for the nudge
    message: str  # Full message content
    chapter_id: Optional[str] = None
    manuscript_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    dismissed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.nudge_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "chapter_id": self.chapter_id,
            "manuscript_id": self.manuscript_id,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "dismissed": self.dismissed,
        }


class ProactiveNudge(Base):
    """Database model for storing proactive nudges."""
    __tablename__ = "proactive_nudges"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # Nudge content
    nudge_type = Column(String, nullable=False)
    priority = Column(String, default="medium")
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)

    # Content hash to avoid duplicate nudges
    content_hash = Column(String, nullable=True, index=True)

    # Status
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)
    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Nudges can expire

    def __repr__(self):
        return f"<ProactiveNudge(id={self.id}, type={self.nudge_type})>"


class WeeklyInsight(Base):
    """Weekly writing insights for users."""
    __tablename__ = "weekly_insights"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)

    # Insight content
    summary = Column(Text, nullable=False)
    highlights = Column(JSON, default=list)  # What went well
    areas_to_improve = Column(JSON, default=list)  # Suggestions
    word_count_total = Column(Integer, default=0)
    chapters_worked_on = Column(Integer, default=0)
    most_active_day = Column(String, nullable=True)

    # Analysis stats
    analyses_run = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    issues_addressed = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeeklyInsight(user={self.user_id}, week={self.week_start})>"


class ProactiveSuggestionsService:
    """
    Service for managing proactive suggestions.

    Generates nudges based on:
    - Recent analysis results
    - Writing patterns
    - Unaddressed issues
    - Weekly writing activity
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Nudge Management ====================

    def create_nudge(
        self,
        user_id: str,
        nudge_type: NudgeType,
        title: str,
        message: str,
        priority: NudgePriority = NudgePriority.MEDIUM,
        manuscript_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        expires_in_days: int = 7,
    ) -> ProactiveNudge:
        """
        Create a new proactive nudge.

        Args:
            user_id: User to nudge
            nudge_type: Type of nudge
            title: Short title
            message: Full message
            priority: Priority level
            manuscript_id: Related manuscript
            chapter_id: Related chapter
            details: Additional details
            expires_in_days: When nudge expires

        Returns:
            Created nudge
        """
        import uuid

        # Generate content hash to avoid duplicates
        content = f"{user_id}:{nudge_type.value}:{title}:{chapter_id or manuscript_id}"
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Check for existing similar nudge
        existing = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.user_id == user_id,
                ProactiveNudge.content_hash == content_hash,
                ProactiveNudge.dismissed == False,
                ProactiveNudge.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).first()

        if existing:
            return existing

        nudge = ProactiveNudge(
            id=str(uuid.uuid4()),
            user_id=user_id,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            nudge_type=nudge_type.value,
            priority=priority.value,
            title=title,
            message=message,
            details=details or {},
            content_hash=content_hash,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )

        self.db.add(nudge)
        self.db.commit()
        self.db.refresh(nudge)

        return nudge

    def get_pending_nudges(
        self,
        user_id: str,
        manuscript_id: Optional[str] = None,
        limit: int = 10,
        include_viewed: bool = False,
    ) -> List[ProactiveNudge]:
        """
        Get pending nudges for a user.

        Args:
            user_id: User ID
            manuscript_id: Optional filter by manuscript
            limit: Maximum nudges to return
            include_viewed: Whether to include already viewed nudges

        Returns:
            List of pending nudges
        """
        query = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.user_id == user_id,
                ProactiveNudge.dismissed == False,
                (ProactiveNudge.expires_at == None) | (ProactiveNudge.expires_at > datetime.utcnow())
            )
        )

        if manuscript_id:
            query = query.filter(ProactiveNudge.manuscript_id == manuscript_id)

        if not include_viewed:
            query = query.filter(ProactiveNudge.viewed == False)

        # Order by priority (high first) and creation date
        priority_order = {
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        return query.order_by(
            ProactiveNudge.priority.asc(),  # high < medium < low alphabetically works backwards
            desc(ProactiveNudge.created_at)
        ).limit(limit).all()

    def dismiss_nudge(self, nudge_id: str, user_id: str) -> bool:
        """Dismiss a nudge."""
        nudge = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.id == nudge_id,
                ProactiveNudge.user_id == user_id
            )
        ).first()

        if nudge:
            nudge.dismissed = True
            nudge.dismissed_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def mark_nudge_viewed(self, nudge_id: str, user_id: str) -> bool:
        """Mark a nudge as viewed."""
        nudge = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.id == nudge_id,
                ProactiveNudge.user_id == user_id
            )
        ).first()

        if nudge:
            nudge.viewed = True
            nudge.viewed_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def dismiss_all_for_chapter(self, chapter_id: str, user_id: str) -> int:
        """Dismiss all nudges for a specific chapter."""
        count = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.chapter_id == chapter_id,
                ProactiveNudge.user_id == user_id,
                ProactiveNudge.dismissed == False
            )
        ).update({"dismissed": True, "dismissed_at": datetime.utcnow()})

        self.db.commit()
        return count

    # ==================== Nudge Generation ====================

    def generate_nudges_from_analysis(
        self,
        user_id: str,
        manuscript_id: str,
        chapter_id: Optional[str],
        analysis_result: Dict[str, Any],
    ) -> List[ProactiveNudge]:
        """
        Generate nudges from analysis results.

        Args:
            user_id: User ID
            manuscript_id: Manuscript ID
            chapter_id: Chapter ID if applicable
            analysis_result: Results from agent analysis

        Returns:
            List of created nudges
        """
        # Check if user has proactive suggestions enabled
        prefs = self.db.query(MaxwellPreferences).filter(
            MaxwellPreferences.user_id == user_id
        ).first()

        if prefs and prefs.proactive_suggestions == "off":
            return []

        nudges = []

        # Extract issues from analysis
        issues = analysis_result.get("issues", [])
        recommendations = analysis_result.get("recommendations", [])

        # Count issues by category
        issue_counts = {}
        for issue in issues:
            category = issue.get("category", "general")
            issue_counts[category] = issue_counts.get(category, 0) + 1

        # Generate nudges for significant issue clusters
        for category, count in issue_counts.items():
            if count >= 3:
                nudge_type = self._category_to_nudge_type(category)
                nudge = self.create_nudge(
                    user_id=user_id,
                    nudge_type=nudge_type,
                    title=f"I noticed {count} {category} items",
                    message=f"While reviewing your writing, I noticed {count} potential {category} issues. Would you like me to walk through them with you?",
                    priority=NudgePriority.MEDIUM if count < 5 else NudgePriority.HIGH,
                    manuscript_id=manuscript_id,
                    chapter_id=chapter_id,
                    details={"issue_count": count, "category": category},
                )
                nudges.append(nudge)

        # Check for high-priority issues
        high_priority_issues = [i for i in issues if i.get("severity") == "high"]
        if high_priority_issues:
            nudge = self.create_nudge(
                user_id=user_id,
                nudge_type=NudgeType.PLOT_HOLE,
                title="Something needs your attention",
                message=f"I found {len(high_priority_issues)} important items that might affect your story's impact. Want to take a look?",
                priority=NudgePriority.HIGH,
                manuscript_id=manuscript_id,
                chapter_id=chapter_id,
                details={"high_priority_count": len(high_priority_issues)},
            )
            nudges.append(nudge)

        return nudges

    def _category_to_nudge_type(self, category: str) -> NudgeType:
        """Map issue category to nudge type."""
        mapping = {
            "consistency": NudgeType.CONSISTENCY_ISSUE,
            "continuity": NudgeType.CONSISTENCY_ISSUE,
            "pacing": NudgeType.PACING_CONCERN,
            "character": NudgeType.CHARACTER_DRIFT,
            "style": NudgeType.STYLE_PATTERN,
            "plot": NudgeType.PLOT_HOLE,
            "dialogue": NudgeType.DIALOGUE_ISSUE,
            "worldbuilding": NudgeType.WORLDBUILDING_GAP,
        }
        return mapping.get(category.lower(), NudgeType.STYLE_PATTERN)

    # ==================== Weekly Insights ====================

    def generate_weekly_insight(
        self,
        user_id: str,
        force: bool = False,
    ) -> Optional[WeeklyInsight]:
        """
        Generate a weekly insight summary.

        Args:
            user_id: User ID
            force: Generate even if recent insight exists

        Returns:
            Weekly insight or None if too soon
        """
        import uuid

        # Calculate week boundaries
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday() + 7)
        week_end = week_start + timedelta(days=7)

        # Check for existing insight
        if not force:
            existing = self.db.query(WeeklyInsight).filter(
                and_(
                    WeeklyInsight.user_id == user_id,
                    WeeklyInsight.week_start >= week_start - timedelta(days=1)
                )
            ).first()

            if existing:
                return existing

        # Gather data from the past week
        from app.models.agent import MaxwellConversation, MaxwellInsight as InsightModel

        # Get conversations from the week
        conversations = self.db.query(MaxwellConversation).filter(
            and_(
                MaxwellConversation.user_id == user_id,
                MaxwellConversation.created_at >= week_start,
                MaxwellConversation.created_at < week_end
            )
        ).all()

        # Get insights from the week
        insights = self.db.query(InsightModel).filter(
            and_(
                InsightModel.user_id == user_id,
                InsightModel.created_at >= week_start,
                InsightModel.created_at < week_end
            )
        ).all()

        # Analyze the data
        analyses_run = len(conversations)
        issues_found = sum(len(c.feedback_data.get("priorities", [])) for c in conversations if c.feedback_data)
        resolved_insights = len([i for i in insights if i.resolved == "addressed"])

        # Generate highlights and areas to improve
        highlights = []
        areas_to_improve = []

        positive_insights = [i for i in insights if i.sentiment == "positive"]
        if positive_insights:
            highlights.append(f"Great work on {positive_insights[0].category}!")

        negative_insights = [i for i in insights if i.sentiment in ["negative", "suggestion"]]
        if negative_insights:
            areas_to_improve.append(f"Consider focusing on {negative_insights[0].category}")

        # Generate summary
        if analyses_run == 0:
            summary = "No analyses were run this week. Try running a quick check on your latest chapter!"
        elif issues_found == 0:
            summary = "Your writing was solid this week! Keep up the great work."
        else:
            addressed_pct = (resolved_insights / max(issues_found, 1)) * 100
            summary = f"You ran {analyses_run} analyses this week and addressed {addressed_pct:.0f}% of the suggestions. "
            if addressed_pct > 70:
                summary += "Excellent progress!"
            elif addressed_pct > 40:
                summary += "Good momentum, keep it up!"
            else:
                summary += "Consider reviewing some of the outstanding suggestions."

        insight = WeeklyInsight(
            id=str(uuid.uuid4()),
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            summary=summary,
            highlights=highlights,
            areas_to_improve=areas_to_improve,
            analyses_run=analyses_run,
            issues_found=issues_found,
            issues_addressed=resolved_insights,
        )

        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)

        return insight

    def get_latest_weekly_insight(self, user_id: str) -> Optional[WeeklyInsight]:
        """Get the most recent weekly insight for a user."""
        return self.db.query(WeeklyInsight).filter(
            WeeklyInsight.user_id == user_id
        ).order_by(desc(WeeklyInsight.week_start)).first()


def create_proactive_suggestions_service(db: Session) -> ProactiveSuggestionsService:
    """Factory function to create a ProactiveSuggestionsService instance."""
    return ProactiveSuggestionsService(db)
