"""
Privacy Middleware for AI Operations

This module provides middleware that enforces user privacy settings
before any AI operation. It integrates with the ContentGateway to:

1. Check author privacy preferences before AI calls
2. Block requests when AI assistance is disabled
3. Block specific features (style analysis, plot suggestions, etc.)
4. Log all AI interactions for audit
5. Track carbon emissions

Usage:
    from app.services.privacy_middleware import privacy_check, PrivacyMiddleware

    # As a decorator
    @privacy_check
    async def analyze_text(manuscript_id, content, ...):
        ...

    # As context manager
    async with PrivacyMiddleware(db, manuscript_id) as pm:
        if pm.allows_feature("style_analysis"):
            result = await ai_call(...)
            await pm.log_interaction(...)
"""

from typing import Optional, Dict, Any, Callable
from functools import wraps
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.privacy import AuthorPrivacyPreferences, AIInteractionAudit, ContentSharingLevel
from app.services.carbon_tracker import CarbonTracker, get_carbon_tracker, OperationType


class PrivacyBlockedException(Exception):
    """Raised when an AI operation is blocked by privacy settings"""
    def __init__(self, reason: str, feature: Optional[str] = None):
        self.reason = reason
        self.feature = feature
        super().__init__(f"AI operation blocked: {reason}")


class FeatureDisabledException(PrivacyBlockedException):
    """Raised when a specific AI feature is disabled"""
    def __init__(self, feature: str):
        super().__init__(f"Feature '{feature}' is disabled by user preferences", feature)


@dataclass
class PrivacyCheckResult:
    """Result of a privacy check"""
    allowed: bool
    reason: Optional[str] = None
    feature_disabled: Optional[str] = None
    preferences: Optional[AuthorPrivacyPreferences] = None


class PrivacyMiddleware:
    """
    Middleware for enforcing privacy settings on AI operations.

    Usage as context manager:
        async with PrivacyMiddleware(db, manuscript_id) as pm:
            if pm.is_allowed:
                result = await ai_operation()
                await pm.log_interaction("analysis", "anthropic", "claude-3", tokens)
    """

    # Map operation types to preference fields
    FEATURE_MAP = {
        "style_analysis": "allow_style_analysis",
        "style_suggestion": "allow_style_analysis",
        "plot_analysis": "allow_plot_suggestions",
        "plot_suggestion": "allow_plot_suggestions",
        "character_analysis": "allow_character_development",
        "character_suggestion": "allow_character_development",
        "grammar_check": "allow_grammar_check",
        "spell_check": "allow_grammar_check",
        "continuity_check": "allow_continuity_check",
        "timeline_check": "allow_continuity_check",
    }

    def __init__(
        self,
        db: Session,
        manuscript_id: str,
        feature: Optional[str] = None,
        region: str = "unknown"
    ):
        self.db = db
        self.manuscript_id = manuscript_id
        self.feature = feature
        self.region = region
        self._preferences: Optional[AuthorPrivacyPreferences] = None
        self._check_result: Optional[PrivacyCheckResult] = None
        self._carbon_tracker = get_carbon_tracker(db, region)

    async def __aenter__(self) -> "PrivacyMiddleware":
        """Check privacy settings on entry"""
        self._check_result = await self.check_privacy()
        if not self._check_result.allowed:
            raise PrivacyBlockedException(
                self._check_result.reason,
                self._check_result.feature_disabled
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up on exit"""
        pass

    @property
    def is_allowed(self) -> bool:
        """Check if the operation is allowed"""
        if self._check_result is None:
            return False
        return self._check_result.allowed

    @property
    def preferences(self) -> Optional[AuthorPrivacyPreferences]:
        """Get the loaded preferences"""
        return self._preferences

    async def check_privacy(self, feature: Optional[str] = None) -> PrivacyCheckResult:
        """
        Check if an AI operation is allowed based on user preferences.

        Args:
            feature: Optional specific feature to check

        Returns:
            PrivacyCheckResult with allowed status and reason
        """
        feature = feature or self.feature

        # Load preferences
        self._preferences = await self._get_or_create_preferences()

        # Check if AI assistance is globally disabled
        if not self._preferences.allow_ai_assistance:
            return PrivacyCheckResult(
                allowed=False,
                reason="AI assistance is disabled for this manuscript",
                preferences=self._preferences
            )

        # Check content sharing level - only block if explicitly set to NO_AI (paranoid mode)
        # ASSIST_NO_TRAINING (default) allows AI to help but blocks training
        if self._preferences.content_sharing_level in ["no_ai", ContentSharingLevel.NO_AI.value]:
            return PrivacyCheckResult(
                allowed=False,
                reason="Content sharing is set to 'no AI' mode - all AI features disabled",
                preferences=self._preferences
            )

        # Check specific feature if provided
        if feature:
            pref_field = self.FEATURE_MAP.get(feature)
            if pref_field:
                if not getattr(self._preferences, pref_field, True):
                    return PrivacyCheckResult(
                        allowed=False,
                        reason=f"Feature '{feature}' is disabled",
                        feature_disabled=feature,
                        preferences=self._preferences
                    )

        return PrivacyCheckResult(
            allowed=True,
            preferences=self._preferences
        )

    def allows_feature(self, feature: str) -> bool:
        """Quick check if a specific feature is allowed"""
        if not self._preferences:
            return False

        if not self._preferences.allow_ai_assistance:
            return False

        pref_field = self.FEATURE_MAP.get(feature)
        if pref_field:
            return getattr(self._preferences, pref_field, True)

        return True

    async def log_interaction(
        self,
        interaction_type: str,
        provider: str,
        model: str,
        tokens_sent: int,
        tokens_received: int,
        chapter_id: Optional[str] = None,
        cost_usd: float = 0.0,
        content_hash: Optional[str] = None,
    ) -> AIInteractionAudit:
        """
        Log an AI interaction for audit purposes.

        This also tracks carbon emissions automatically.
        """
        # Create audit record
        audit = AIInteractionAudit(
            manuscript_id=self.manuscript_id,
            chapter_id=chapter_id,
            interaction_type=interaction_type,
            provider=provider,
            model=model,
            tokens_sent=tokens_sent,
            tokens_received=tokens_received,
            training_opted_out=not (self._preferences.allow_training_data if self._preferences else True),
            zero_data_retention=False,
            content_hash=content_hash,
            estimated_cost_usd=int(cost_usd * 1_000_000),
        )
        self.db.add(audit)

        # Track carbon emissions
        await self._carbon_tracker.track_ai_operation(
            provider=provider,
            model=model,
            tokens=tokens_sent + tokens_received,
            manuscript_id=self.manuscript_id,
            request_type=interaction_type,
        )

        self.db.commit()
        return audit

    async def _get_or_create_preferences(self) -> AuthorPrivacyPreferences:
        """Get or create privacy preferences for the manuscript"""
        preferences = self.db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == self.manuscript_id
        ).first()

        if not preferences:
            # Create default preferences:
            # - AI assistance enabled (helps you write)
            # - Training data disabled (your content is never used to train AI)
            preferences = AuthorPrivacyPreferences(
                manuscript_id=self.manuscript_id,
                allow_ai_assistance=True,  # AI can help you write
                allow_training_data=False,  # CRITICAL: your content is NEVER used to train AI
                content_sharing_level=ContentSharingLevel.ASSIST_NO_TRAINING.value,  # AI helps, no training
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences


def privacy_check(feature: Optional[str] = None):
    """
    Decorator to enforce privacy checks on async functions.

    The decorated function must have 'db' and 'manuscript_id' as parameters
    (either positional or keyword).

    Usage:
        @privacy_check(feature="style_analysis")
        async def analyze_style(db: Session, manuscript_id: str, content: str):
            ...

    Raises:
        PrivacyBlockedException: If the operation is not allowed
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract db and manuscript_id from args/kwargs
            db = kwargs.get('db')
            manuscript_id = kwargs.get('manuscript_id')

            # Try to get from positional args if not in kwargs
            if db is None and len(args) > 0:
                # Assume first arg might be self, second might be db
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break

            if manuscript_id is None:
                for key in ['manuscript_id', 'ms_id', 'id']:
                    if key in kwargs:
                        manuscript_id = kwargs[key]
                        break

            # If we can't find required params, skip the check
            if db is None or manuscript_id is None:
                return await func(*args, **kwargs)

            # Perform privacy check
            middleware = PrivacyMiddleware(db, manuscript_id, feature)
            result = await middleware.check_privacy()

            if not result.allowed:
                raise PrivacyBlockedException(result.reason, result.feature_disabled)

            return await func(*args, **kwargs)

        return wrapper
    return decorator


async def check_ai_allowed(
    db: Session,
    manuscript_id: str,
    feature: Optional[str] = None
) -> PrivacyCheckResult:
    """
    Standalone function to check if AI is allowed for a manuscript.

    Args:
        db: Database session
        manuscript_id: Manuscript ID
        feature: Optional specific feature to check

    Returns:
        PrivacyCheckResult with allowed status
    """
    middleware = PrivacyMiddleware(db, manuscript_id, feature)
    return await middleware.check_privacy()
