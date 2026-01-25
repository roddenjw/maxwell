"""
Achievement Model
Tracks user achievements and gamification progress
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON
from datetime import datetime
import uuid

from app.database import Base


# Achievement type constants
class AchievementType:
    # First actions
    FIRST_MANUSCRIPT = "FIRST_MANUSCRIPT"
    FIRST_CHAPTER = "FIRST_CHAPTER"
    FIRST_ENTITY = "FIRST_ENTITY"
    FIRST_TIMELINE_EVENT = "FIRST_TIMELINE_EVENT"
    FIRST_OUTLINE = "FIRST_OUTLINE"

    # Word milestones
    WORD_MILESTONE_1K = "WORD_MILESTONE_1K"
    WORD_MILESTONE_5K = "WORD_MILESTONE_5K"
    WORD_MILESTONE_10K = "WORD_MILESTONE_10K"
    WORD_MILESTONE_25K = "WORD_MILESTONE_25K"
    WORD_MILESTONE_50K = "WORD_MILESTONE_50K"

    # Streaks
    STREAK_3_DAYS = "STREAK_3_DAYS"
    STREAK_7_DAYS = "STREAK_7_DAYS"
    STREAK_14_DAYS = "STREAK_14_DAYS"
    STREAK_30_DAYS = "STREAK_30_DAYS"

    # AI features
    FIRST_AI_USE = "FIRST_AI_USE"
    FIRST_RECAP = "FIRST_RECAP"
    FIRST_BRAINSTORM = "FIRST_BRAINSTORM"

    # Social
    FIRST_SHARE = "FIRST_SHARE"
    FIRST_EXPORT = "FIRST_EXPORT"

    # Codex
    CODEX_10_ENTITIES = "CODEX_10_ENTITIES"
    CODEX_50_ENTITIES = "CODEX_50_ENTITIES"
    FIRST_RELATIONSHIP = "FIRST_RELATIONSHIP"

    # Story structure
    OUTLINE_COMPLETE = "OUTLINE_COMPLETE"
    ALL_BEATS_WRITTEN = "ALL_BEATS_WRITTEN"

    # World building
    FIRST_WORLD = "FIRST_WORLD"
    FIRST_SERIES = "FIRST_SERIES"


# Achievement metadata
ACHIEVEMENT_METADATA = {
    AchievementType.FIRST_MANUSCRIPT: {
        "name": "The Journey Begins",
        "description": "Created your first manuscript",
        "icon": "📝",
        "points": 10,
        "category": "getting_started"
    },
    AchievementType.FIRST_CHAPTER: {
        "name": "Chapter One",
        "description": "Created your first chapter",
        "icon": "📖",
        "points": 10,
        "category": "getting_started"
    },
    AchievementType.FIRST_ENTITY: {
        "name": "Character Creator",
        "description": "Added your first entity to the Codex",
        "icon": "👤",
        "points": 15,
        "category": "codex"
    },
    AchievementType.FIRST_TIMELINE_EVENT: {
        "name": "Time Keeper",
        "description": "Created your first timeline event",
        "icon": "📅",
        "points": 15,
        "category": "timeline"
    },
    AchievementType.FIRST_OUTLINE: {
        "name": "Story Architect",
        "description": "Created your first outline",
        "icon": "🏗️",
        "points": 20,
        "category": "outline"
    },
    AchievementType.WORD_MILESTONE_1K: {
        "name": "First Thousand",
        "description": "Wrote 1,000 words",
        "icon": "✍️",
        "points": 25,
        "category": "writing"
    },
    AchievementType.WORD_MILESTONE_5K: {
        "name": "Five Thousand Strong",
        "description": "Wrote 5,000 words",
        "icon": "📚",
        "points": 50,
        "category": "writing"
    },
    AchievementType.WORD_MILESTONE_10K: {
        "name": "Ten K Club",
        "description": "Wrote 10,000 words",
        "icon": "🏆",
        "points": 100,
        "category": "writing"
    },
    AchievementType.WORD_MILESTONE_25K: {
        "name": "Quarter Century",
        "description": "Wrote 25,000 words",
        "icon": "⭐",
        "points": 200,
        "category": "writing"
    },
    AchievementType.WORD_MILESTONE_50K: {
        "name": "NaNoWriMo Champion",
        "description": "Wrote 50,000 words",
        "icon": "👑",
        "points": 500,
        "category": "writing"
    },
    AchievementType.STREAK_3_DAYS: {
        "name": "Getting Started",
        "description": "Wrote for 3 days in a row",
        "icon": "🔥",
        "points": 30,
        "category": "consistency"
    },
    AchievementType.STREAK_7_DAYS: {
        "name": "Week Warrior",
        "description": "Wrote for 7 days in a row",
        "icon": "🔥",
        "points": 75,
        "category": "consistency"
    },
    AchievementType.STREAK_14_DAYS: {
        "name": "Two Week Titan",
        "description": "Wrote for 14 days in a row",
        "icon": "💪",
        "points": 150,
        "category": "consistency"
    },
    AchievementType.STREAK_30_DAYS: {
        "name": "Monthly Master",
        "description": "Wrote for 30 days in a row",
        "icon": "🌟",
        "points": 300,
        "category": "consistency"
    },
    AchievementType.FIRST_AI_USE: {
        "name": "AI Enabled",
        "description": "Used your first AI feature",
        "icon": "🤖",
        "points": 15,
        "category": "ai"
    },
    AchievementType.FIRST_RECAP: {
        "name": "Story Recap",
        "description": "Generated your first chapter recap",
        "icon": "📋",
        "points": 20,
        "category": "ai"
    },
    AchievementType.FIRST_BRAINSTORM: {
        "name": "Idea Generator",
        "description": "Completed your first brainstorm session",
        "icon": "💡",
        "points": 20,
        "category": "ai"
    },
    AchievementType.FIRST_SHARE: {
        "name": "Sharing is Caring",
        "description": "Shared your first recap card",
        "icon": "🔗",
        "points": 25,
        "category": "social"
    },
    AchievementType.FIRST_EXPORT: {
        "name": "Ready to Publish",
        "description": "Exported your manuscript for the first time",
        "icon": "📤",
        "points": 25,
        "category": "social"
    },
    AchievementType.CODEX_10_ENTITIES: {
        "name": "World Builder",
        "description": "Created 10 entities in the Codex",
        "icon": "🌍",
        "points": 50,
        "category": "codex"
    },
    AchievementType.CODEX_50_ENTITIES: {
        "name": "Master Worldsmith",
        "description": "Created 50 entities in the Codex",
        "icon": "🏰",
        "points": 150,
        "category": "codex"
    },
    AchievementType.FIRST_RELATIONSHIP: {
        "name": "Relationship Web",
        "description": "Created your first entity relationship",
        "icon": "🕸️",
        "points": 15,
        "category": "codex"
    },
    AchievementType.OUTLINE_COMPLETE: {
        "name": "Planned Perfection",
        "description": "Completed all beats in an outline",
        "icon": "✅",
        "points": 100,
        "category": "outline"
    },
    AchievementType.ALL_BEATS_WRITTEN: {
        "name": "Story Complete",
        "description": "Wrote content for all beats in an outline",
        "icon": "🎉",
        "points": 250,
        "category": "outline"
    },
    AchievementType.FIRST_WORLD: {
        "name": "World Creator",
        "description": "Created your first world",
        "icon": "🌐",
        "points": 25,
        "category": "world"
    },
    AchievementType.FIRST_SERIES: {
        "name": "Series Starter",
        "description": "Created your first series",
        "icon": "📚",
        "points": 30,
        "category": "world"
    },
}


class Achievement(Base):
    """Tracks earned achievements"""
    __tablename__ = "achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # User identifier (for future multi-user support)
    # For now, can be "default" or a user ID
    user_id = Column(String, default="default", nullable=False, index=True)

    # Achievement type (from AchievementType constants)
    achievement_type = Column(String, nullable=False)

    # Optional manuscript reference (for manuscript-specific achievements)
    manuscript_id = Column(String, nullable=True)

    # Achievement extra data at time of earning
    extra_data = Column(JSON, default=dict)

    # Timestamps
    earned_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Achievement(type={self.achievement_type}, earned_at={self.earned_at})>"

    @property
    def info(self):
        """Get achievement metadata"""
        return ACHIEVEMENT_METADATA.get(self.achievement_type, {
            "name": self.achievement_type,
            "description": "Unknown achievement",
            "icon": "🏅",
            "points": 0,
            "category": "other"
        })


class AchievementProgress(Base):
    """Tracks progress toward achievements (e.g., word counts, streaks)"""
    __tablename__ = "achievement_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, default="default", nullable=False, index=True)

    # Progress type (e.g., "total_words", "current_streak", "entity_count")
    progress_type = Column(String, nullable=False)

    # Current value
    current_value = Column(Integer, default=0)

    # Additional tracking data
    extra_data = Column(JSON, default=dict)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AchievementProgress(type={self.progress_type}, value={self.current_value})>"
