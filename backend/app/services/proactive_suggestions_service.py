"""
Proactive Suggestions Service

Provides background analysis and gentle nudges to help writers
catch issues before they become problems.

Features:
- Create nudges based on detected issues
- Track dismissed nudges to avoid repetition
- Weekly insights summary generation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.agent import ProactiveNudge, WeeklyInsight, MaxwellPreferences


class NudgeType(Enum):
    """Types of proactive nudges Maxwell can give."""
    CONSISTENCY_ISSUE = "consistency_issue"
    PACING_CONCERN = "pacing_concern"
    CHARACTER_DRIFT = "character_drift"
    STYLE_PATTERN = "style_pattern"
    PLOT_HOLE = "plot_hole"
    DIALOGUE_ISSUE = "dialogue_issue"
    WORLDBUILDING_GAP = "worldbuilding_gap"
    WRITING_STREAK = "writing_streak"
    MILESTONE = "milestone"


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
    title: str
    message: str
    chapter_id: Optional[str] = None
    manuscript_id: Optional[str] = None
    details: Dict[str, Any] = None
    created_at: datetime = None
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
            "details": self.details or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "dismissed": self.dismissed,
        }


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

        Automatically deduplicates - won't create same nudge twice within 24 hours.

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
            Created nudge (or existing if duplicate)
        """
        # Generate content hash to avoid duplicates
        content = f"{user_id}:{nudge_type.value}:{title}:{chapter_id or manuscript_id}"
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Check for existing similar nudge in last 24 hours
        existing = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.user_id == user_id,
                ProactiveNudge.content_hash == content_hash,
                ProactiveNudge.dismissed == False,
                ProactiveNudge.created_at >= datetime.utcnow() - timedelta(hours=24)
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
            List of pending nudges, newest first
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

        # Order by priority (high first), then date
        return query.order_by(
            desc(ProactiveNudge.priority == "high"),
            desc(ProactiveNudge.created_at)
        ).limit(limit).all()

    def dismiss_nudge(
        self,
        nudge_id: str,
        user_id: str,
    ) -> Optional[ProactiveNudge]:
        """
        Dismiss a nudge.

        Args:
            nudge_id: Nudge to dismiss
            user_id: User dismissing (for verification)

        Returns:
            Dismissed nudge or None if not found
        """
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
            self.db.refresh(nudge)

        return nudge

    def mark_nudge_viewed(
        self,
        nudge_id: str,
        user_id: str,
    ) -> Optional[ProactiveNudge]:
        """
        Mark a nudge as viewed.

        Args:
            nudge_id: Nudge to mark
            user_id: User viewing (for verification)

        Returns:
            Updated nudge or None if not found
        """
        nudge = self.db.query(ProactiveNudge).filter(
            and_(
                ProactiveNudge.id == nudge_id,
                ProactiveNudge.user_id == user_id
            )
        ).first()

        if nudge and not nudge.viewed:
            nudge.viewed = True
            nudge.viewed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(nudge)

        return nudge

    def check_proactive_enabled(self, user_id: str) -> bool:
        """
        Check if proactive suggestions are enabled for a user.

        Args:
            user_id: User to check

        Returns:
            True if proactive suggestions are enabled
        """
        prefs = self.db.query(MaxwellPreferences).filter(
            MaxwellPreferences.user_id == user_id
        ).first()

        if not prefs:
            return True  # Default to enabled

        return prefs.proactive_suggestions != "off"

    # ==================== Weekly Insights ====================

    def create_weekly_insight(
        self,
        user_id: str,
        summary: str,
        highlights: List[str],
        areas_to_improve: List[str],
        word_count_total: int = 0,
        chapters_worked_on: int = 0,
        most_active_day: Optional[str] = None,
        analyses_run: int = 0,
        issues_found: int = 0,
        issues_addressed: int = 0,
    ) -> WeeklyInsight:
        """
        Create a weekly insight summary.

        Args:
            user_id: User ID
            summary: Overall summary text
            highlights: List of positive highlights
            areas_to_improve: List of improvement suggestions
            word_count_total: Total words written
            chapters_worked_on: Number of chapters edited
            most_active_day: Most productive day
            analyses_run: Number of Maxwell analyses
            issues_found: Issues detected
            issues_addressed: Issues resolved

        Returns:
            Created WeeklyInsight
        """
        # Calculate week boundaries
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        insight = WeeklyInsight(
            id=str(uuid.uuid4()),
            user_id=user_id,
            week_start=datetime.combine(week_start, datetime.min.time()),
            week_end=datetime.combine(week_end, datetime.max.time()),
            summary=summary,
            highlights=highlights,
            areas_to_improve=areas_to_improve,
            word_count_total=word_count_total,
            chapters_worked_on=chapters_worked_on,
            most_active_day=most_active_day,
            analyses_run=analyses_run,
            issues_found=issues_found,
            issues_addressed=issues_addressed,
        )

        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)

        return insight

    def get_weekly_insight(
        self,
        user_id: str,
        week_offset: int = 0,
    ) -> Optional[WeeklyInsight]:
        """
        Get weekly insight for a specific week.

        Args:
            user_id: User ID
            week_offset: Weeks ago (0 = current week, 1 = last week, etc.)

        Returns:
            WeeklyInsight or None
        """
        today = datetime.utcnow().date()
        target_week_start = today - timedelta(days=today.weekday() + (7 * week_offset))

        return self.db.query(WeeklyInsight).filter(
            and_(
                WeeklyInsight.user_id == user_id,
                WeeklyInsight.week_start >= datetime.combine(target_week_start, datetime.min.time()),
                WeeklyInsight.week_start < datetime.combine(target_week_start + timedelta(days=7), datetime.min.time())
            )
        ).first()

    def get_recent_weekly_insights(
        self,
        user_id: str,
        limit: int = 4,
    ) -> List[WeeklyInsight]:
        """
        Get recent weekly insights.

        Args:
            user_id: User ID
            limit: Maximum insights to return

        Returns:
            List of WeeklyInsight, newest first
        """
        return self.db.query(WeeklyInsight).filter(
            WeeklyInsight.user_id == user_id
        ).order_by(desc(WeeklyInsight.week_start)).limit(limit).all()

    # ==================== Nudge Generation Helpers ====================

    def generate_consistency_nudge(
        self,
        user_id: str,
        manuscript_id: str,
        issue_description: str,
        chapter_id: Optional[str] = None,
    ) -> ProactiveNudge:
        """Generate a consistency issue nudge."""
        return self.create_nudge(
            user_id=user_id,
            nudge_type=NudgeType.CONSISTENCY_ISSUE,
            title="Consistency Check",
            message=f"I noticed a potential consistency issue: {issue_description}",
            priority=NudgePriority.MEDIUM,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            details={"issue": issue_description},
        )

    def generate_pacing_nudge(
        self,
        user_id: str,
        manuscript_id: str,
        pacing_issue: str,
        chapter_id: Optional[str] = None,
    ) -> ProactiveNudge:
        """Generate a pacing concern nudge."""
        return self.create_nudge(
            user_id=user_id,
            nudge_type=NudgeType.PACING_CONCERN,
            title="Pacing Note",
            message=f"The pacing in this section might need attention: {pacing_issue}",
            priority=NudgePriority.LOW,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            details={"issue": pacing_issue},
        )

    def generate_character_drift_nudge(
        self,
        user_id: str,
        manuscript_id: str,
        character_name: str,
        drift_description: str,
        chapter_id: Optional[str] = None,
    ) -> ProactiveNudge:
        """Generate a character drift nudge."""
        return self.create_nudge(
            user_id=user_id,
            nudge_type=NudgeType.CHARACTER_DRIFT,
            title=f"Character Check: {character_name}",
            message=f"{character_name}'s behavior might be drifting: {drift_description}",
            priority=NudgePriority.MEDIUM,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            details={"character": character_name, "drift": drift_description},
        )

    def generate_milestone_nudge(
        self,
        user_id: str,
        manuscript_id: str,
        milestone_type: str,
        milestone_value: Any,
    ) -> ProactiveNudge:
        """Generate a milestone celebration nudge."""
        messages = {
            "word_count": f"Congratulations! You've written {milestone_value:,} words!",
            "chapter_count": f"You've completed {milestone_value} chapters!",
            "streak": f"Amazing! You've maintained a {milestone_value}-day writing streak!",
        }
        return self.create_nudge(
            user_id=user_id,
            nudge_type=NudgeType.MILESTONE,
            title="Milestone Achieved!",
            message=messages.get(milestone_type, f"You've hit a milestone: {milestone_value}"),
            priority=NudgePriority.LOW,
            manuscript_id=manuscript_id,
            details={"milestone_type": milestone_type, "value": milestone_value},
            expires_in_days=14,  # Milestones stick around longer
        )


def create_proactive_suggestions_service(db: Session) -> ProactiveSuggestionsService:
    """Factory function to create a ProactiveSuggestionsService."""
    return ProactiveSuggestionsService(db)
