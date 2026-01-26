"""
Author Learning Service

Tracks author's writing patterns, suggestion responses, and improvement over time.
Provides personalized insights and tracks progress on common issues.

Key Features:
1. Track suggestion acceptance/rejection patterns
2. Identify common writing issues
3. Show strengths and areas for improvement
4. Track improvement over time with visual progress
5. Adapt agent suggestions based on learning
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import json

from app.database import SessionLocal
from app.models.agent import AuthorLearning, SuggestionFeedback
from app.models.coach import WritingProfile, CoachingHistory, FeedbackPattern


# Issue categories for tracking
ISSUE_CATEGORIES = {
    "show_vs_tell": {
        "name": "Show vs Tell",
        "description": "Opportunities to show action/emotion rather than state it",
        "teaching": "Showing engages readers by letting them experience moments"
    },
    "overused_words": {
        "name": "Overused Words",
        "description": "Words or phrases used too frequently",
        "teaching": "Varied vocabulary keeps prose fresh and engaging"
    },
    "passive_voice": {
        "name": "Passive Voice",
        "description": "Sentences where the subject receives the action",
        "teaching": "Active voice creates more engaging, direct prose"
    },
    "weak_verbs": {
        "name": "Weak Verbs",
        "description": "Generic verbs that could be more specific",
        "teaching": "Strong verbs do more work and create vivid images"
    },
    "dialogue_tags": {
        "name": "Dialogue Tags",
        "description": "Overuse of said-bookisms or adverbs in tags",
        "teaching": "Said is invisible; action beats show character"
    },
    "pacing": {
        "name": "Pacing Issues",
        "description": "Sections that move too slow or too fast",
        "teaching": "Pacing controls reader engagement and emotional impact"
    },
    "continuity": {
        "name": "Continuity Errors",
        "description": "Inconsistencies in character or world details",
        "teaching": "Consistency builds reader trust and immersion"
    },
    "filter_words": {
        "name": "Filter Words",
        "description": "Words that distance readers (felt, saw, heard)",
        "teaching": "Removing filters puts readers directly in the scene"
    },
    "purple_prose": {
        "name": "Overwriting",
        "description": "Overly elaborate or flowery descriptions",
        "teaching": "Precise language often has more impact than elaborate"
    },
    "head_hopping": {
        "name": "POV Consistency",
        "description": "Switching between character perspectives",
        "teaching": "Consistent POV helps readers connect with characters"
    },
}


class AuthorLearningService:
    """
    Service for tracking author learning and improvement.

    Tracks:
    - What issues are flagged most often
    - How the author responds to suggestions (accept/reject/modify)
    - Improvement over time for each issue type
    - Strengths to celebrate
    """

    def record_suggestion_feedback(
        self,
        user_id: str,
        agent_type: str,
        suggestion_type: str,
        suggestion_text: str,
        action: str,
        original_text: Optional[str] = None,
        modified_text: Optional[str] = None,
        manuscript_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        user_explanation: Optional[str] = None
    ) -> SuggestionFeedback:
        """
        Record how the author responded to a suggestion.

        Args:
            user_id: The user ID
            agent_type: Which agent made the suggestion
            suggestion_type: Category of suggestion (show_vs_tell, etc.)
            suggestion_text: The actual suggestion text
            action: User's action (accepted, rejected, modified, ignored)
            original_text: The text being analyzed
            modified_text: If modified, what did they change to
            manuscript_id: Associated manuscript
            analysis_id: Associated analysis
            user_explanation: Optional user explanation of why

        Returns:
            The created SuggestionFeedback record
        """
        db = SessionLocal()
        try:
            feedback = SuggestionFeedback(
                user_id=user_id,
                agent_type=agent_type,
                suggestion_type=suggestion_type,
                suggestion_text=suggestion_text,
                action=action,
                original_text=original_text,
                modified_text=modified_text,
                manuscript_id=manuscript_id,
                analysis_id=analysis_id,
                user_explanation=user_explanation
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)

            # Update learning patterns
            self._update_learning_patterns(db, user_id, suggestion_type, action)

            return feedback
        finally:
            db.close()

    def _update_learning_patterns(
        self,
        db,
        user_id: str,
        suggestion_type: str,
        action: str
    ):
        """Update AuthorLearning records based on feedback"""
        # Find or create learning record for this pattern
        learning = db.query(AuthorLearning).filter(
            AuthorLearning.user_id == user_id,
            AuthorLearning.pattern_key == suggestion_type
        ).first()

        if not learning:
            learning = AuthorLearning(
                user_id=user_id,
                category="style",
                pattern_type="suggestion_response",
                pattern_key=suggestion_type,
                pattern_data={
                    "accepted": 0,
                    "rejected": 0,
                    "modified": 0,
                    "ignored": 0,
                    "total": 0,
                    "history": []  # Track trend over time
                },
                confidence=0.5,
                observation_count=0
            )
            db.add(learning)

        # Update counts
        data = learning.pattern_data or {}
        data[action] = data.get(action, 0) + 1
        data["total"] = data.get("total", 0) + 1

        # Add to history for trend tracking (keep last 50)
        history = data.get("history", [])
        history.append({
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        })
        data["history"] = history[-50:]

        learning.pattern_data = data
        learning.observation_count += 1

        # Update confidence based on response rate
        total = data.get("total", 0)
        if total >= 5:
            # High confidence if consistent behavior
            accepted = data.get("accepted", 0)
            rejected = data.get("rejected", 0)
            learning.confidence = max(accepted / total, rejected / total)

        db.commit()

    def get_author_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive insights about an author's writing patterns.

        Returns:
        {
            "common_issues": [...],  # Most frequently flagged
            "strengths": [...],      # What they do well
            "improvement_areas": [...],  # Where to focus
            "progress": {...},       # Improvement tracking
            "personalization": {...} # How we've adapted to them
        }
        """
        db = SessionLocal()
        try:
            # Get all feedback for this user
            feedbacks = db.query(SuggestionFeedback).filter(
                SuggestionFeedback.user_id == user_id
            ).all()

            # Get learning patterns
            learnings = db.query(AuthorLearning).filter(
                AuthorLearning.user_id == user_id
            ).all()

            # Get writing profile
            profile = db.query(WritingProfile).filter(
                WritingProfile.user_id == user_id
            ).first()

            # Analyze feedback patterns
            issue_counts: Dict[str, int] = defaultdict(int)
            acceptance_rates: Dict[str, Tuple[int, int]] = defaultdict(lambda: (0, 0))

            for f in feedbacks:
                issue_counts[f.suggestion_type] += 1
                accepted, total = acceptance_rates[f.suggestion_type]
                if f.action == "accepted":
                    acceptance_rates[f.suggestion_type] = (accepted + 1, total + 1)
                else:
                    acceptance_rates[f.suggestion_type] = (accepted, total + 1)

            # Build common issues list (sorted by frequency)
            common_issues = []
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                issue_info = ISSUE_CATEGORIES.get(issue_type, {})
                accepted, total = acceptance_rates[issue_type]
                acceptance_rate = (accepted / total * 100) if total > 0 else 0

                common_issues.append({
                    "type": issue_type,
                    "name": issue_info.get("name", issue_type),
                    "description": issue_info.get("description", ""),
                    "teaching": issue_info.get("teaching", ""),
                    "count": count,
                    "acceptance_rate": round(acceptance_rate, 1),
                    "trend": self._calculate_trend(issue_type, learnings)
                })

            # Identify strengths (issues they rarely have or have improved on)
            strengths = []
            for learning in learnings:
                data = learning.pattern_data or {}
                history = data.get("history", [])

                # Check if improving (more accepted over time)
                if len(history) >= 10:
                    recent = history[-10:]
                    earlier = history[:10] if len(history) >= 20 else history[:len(history)//2]

                    recent_accepted = sum(1 for h in recent if h.get("action") == "accepted")
                    earlier_accepted = sum(1 for h in earlier if h.get("action") == "accepted")

                    if recent_accepted > earlier_accepted * 1.5:
                        issue_info = ISSUE_CATEGORIES.get(learning.pattern_key, {})
                        strengths.append({
                            "type": learning.pattern_key,
                            "name": issue_info.get("name", learning.pattern_key),
                            "improvement_percent": round((recent_accepted - earlier_accepted) / max(earlier_accepted, 1) * 100)
                        })

            # Identify areas for improvement (high frequency, low acceptance)
            improvement_areas = []
            for issue in common_issues[:5]:
                if issue["count"] >= 3 and issue["acceptance_rate"] < 50:
                    improvement_areas.append({
                        "type": issue["type"],
                        "name": issue["name"],
                        "suggestion": f"Focus on {issue['name'].lower()}. {issue['teaching']}"
                    })

            # Calculate overall progress
            progress = self._calculate_overall_progress(feedbacks, learnings)

            # Build personalization info (what we've learned about them)
            personalization = {}
            for learning in learnings:
                data = learning.pattern_data or {}
                total = data.get("total", 0)
                rejected = data.get("rejected", 0)

                # If they reject this type often, we should reduce it
                if total >= 5 and (rejected / total) > 0.7:
                    personalization[learning.pattern_key] = {
                        "reduce_frequency": True,
                        "reason": f"Author consistently declines {learning.pattern_key} suggestions"
                    }

            return {
                "common_issues": common_issues[:10],
                "strengths": strengths[:5],
                "improvement_areas": improvement_areas[:3],
                "progress": progress,
                "personalization": personalization,
                "total_feedback_given": len(feedbacks),
                "learning_confidence": self._calculate_learning_confidence(learnings)
            }
        finally:
            db.close()

    def _calculate_trend(self, issue_type: str, learnings: List[AuthorLearning]) -> str:
        """Calculate trend for an issue type (improving, declining, stable)"""
        learning = next((l for l in learnings if l.pattern_key == issue_type), None)
        if not learning:
            return "unknown"

        history = (learning.pattern_data or {}).get("history", [])
        if len(history) < 10:
            return "insufficient_data"

        # Compare recent vs earlier
        recent = history[-10:]
        earlier = history[:10] if len(history) >= 20 else history[:len(history)//2]

        recent_accepted = sum(1 for h in recent if h.get("action") == "accepted")
        earlier_accepted = sum(1 for h in earlier if h.get("action") == "accepted")

        if recent_accepted > earlier_accepted * 1.2:
            return "improving"
        elif recent_accepted < earlier_accepted * 0.8:
            return "declining"
        else:
            return "stable"

    def _calculate_overall_progress(
        self,
        feedbacks: List[SuggestionFeedback],
        learnings: List[AuthorLearning]
    ) -> Dict[str, Any]:
        """Calculate overall writing improvement metrics"""
        if not feedbacks:
            return {"status": "no_data", "message": "Start writing to track progress"}

        # Get time-based metrics
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)

        recent_feedbacks = [f for f in feedbacks if f.created_at >= week_ago]
        month_feedbacks = [f for f in feedbacks if f.created_at >= month_ago]

        # Calculate acceptance rates over time
        def acceptance_rate(fbs):
            if not fbs:
                return 0
            return sum(1 for f in fbs if f.action == "accepted") / len(fbs) * 100

        recent_rate = acceptance_rate(recent_feedbacks)
        month_rate = acceptance_rate(month_feedbacks)
        all_time_rate = acceptance_rate(feedbacks)

        # Count issues addressed
        improving_issues = 0
        for learning in learnings:
            if self._calculate_trend(learning.pattern_key, learnings) == "improving":
                improving_issues += 1

        return {
            "status": "tracking",
            "all_time_acceptance_rate": round(all_time_rate, 1),
            "month_acceptance_rate": round(month_rate, 1),
            "week_acceptance_rate": round(recent_rate, 1),
            "trending": "up" if recent_rate > month_rate else ("down" if recent_rate < month_rate else "stable"),
            "improving_issues": improving_issues,
            "total_issues_tracked": len(learnings),
            "suggestions_received": len(feedbacks),
            "suggestions_this_week": len(recent_feedbacks)
        }

    def _calculate_learning_confidence(self, learnings: List[AuthorLearning]) -> float:
        """How confident are we in our understanding of this author?"""
        if not learnings:
            return 0.0

        total_observations = sum(l.observation_count for l in learnings)
        if total_observations < 10:
            return 0.2
        elif total_observations < 25:
            return 0.4
        elif total_observations < 50:
            return 0.6
        elif total_observations < 100:
            return 0.8
        else:
            return 0.95

    def should_suppress_suggestion_type(
        self,
        user_id: str,
        suggestion_type: str,
        threshold: float = 0.7
    ) -> bool:
        """
        Check if we should reduce suggestions of this type for this author.

        Returns True if the author consistently rejects this type of suggestion.
        """
        db = SessionLocal()
        try:
            learning = db.query(AuthorLearning).filter(
                AuthorLearning.user_id == user_id,
                AuthorLearning.pattern_key == suggestion_type
            ).first()

            if not learning:
                return False

            data = learning.pattern_data or {}
            total = data.get("total", 0)
            rejected = data.get("rejected", 0)

            if total < 5:
                return False  # Not enough data

            rejection_rate = rejected / total
            return rejection_rate >= threshold
        finally:
            db.close()

    def get_suggestions_for_feedback(self, user_id: str, issue_type: str) -> List[str]:
        """
        Get improvement suggestions for a specific issue type.

        Based on the author's history and common patterns.
        """
        issue_info = ISSUE_CATEGORIES.get(issue_type, {})
        base_suggestions = [issue_info.get("teaching", "")]

        # Add specific suggestions based on issue type
        specific_suggestions = {
            "show_vs_tell": [
                "Try using action verbs: instead of 'She was angry', show her slamming a door",
                "Describe physical sensations: tight chest, clenched fists, racing heart",
                "Use dialogue to reveal emotion without stating it"
            ],
            "overused_words": [
                "Keep a list of your frequent words to watch for during editing",
                "Read your work aloud - repetition becomes obvious",
                "Use your word processor's 'Find' feature to check frequency"
            ],
            "passive_voice": [
                "Look for 'was' + past participle patterns",
                "Ask: 'Who is doing the action?' and make them the subject",
                "Some passive voice is fine - use it intentionally"
            ],
            "weak_verbs": [
                "Replace 'walked' with strode, ambled, shuffled, marched",
                "Check if your verb needs adverbs to work - find a stronger verb instead",
                "Action verbs create movement and energy"
            ]
        }

        return base_suggestions + specific_suggestions.get(issue_type, [])


# Global instance
author_learning_service = AuthorLearningService()
