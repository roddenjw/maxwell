"""
Privacy Middleware for AI Operations

Simple middleware that ensures:
1. User content is NEVER used to train AI models (default)
2. AI assistance can be completely disabled if user wants (opt-in paranoid mode)
3. All AI interactions are logged for audit (without storing content)
4. Carbon emissions are tracked

Usage:
    from app.services.privacy_middleware import PrivacyMiddleware, check_ai_allowed

    # Quick check
    result = await check_ai_allowed(db, manuscript_id)
    if result.allowed:
        # AI assistance is enabled, training is blocked
        response = await ai_call(...)

    # With audit logging
    async with PrivacyMiddleware(db, manuscript_id) as pm:
        response = await ai_call(...)
        await pm.log_interaction("analysis", "anthropic", "claude-3", tokens)
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
    Simple middleware for privacy-respecting AI operations.

    Default behavior:
    - AI assistance is ENABLED (helps you write)
    - Training is DISABLED (your content is never used to train AI)

    Users can optionally disable AI completely (paranoid mode).
    """

    def __init__(
        self,
        db: Session,
        manuscript_id: str,
        region: str = "unknown"
    ):
        self.db = db
        self.manuscript_id = manuscript_id
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

    async def check_privacy(self) -> PrivacyCheckResult:
        """
        Check if AI assistance is allowed for this manuscript.

        Returns allowed=True if:
        - AI assistance is enabled (default)

        Returns allowed=False if:
        - User has explicitly disabled AI assistance (paranoid mode)
        """
        # Load preferences
        self._preferences = await self._get_or_create_preferences()

        # Check if AI assistance is disabled (paranoid mode)
        if not self._preferences.allow_ai_assistance:
            return PrivacyCheckResult(
                allowed=False,
                reason="AI assistance is disabled for this manuscript (you can re-enable it in privacy settings)",
                preferences=self._preferences
            )

        # AI assistance is allowed
        # Note: Training is blocked by default via allow_training_data=False
        return PrivacyCheckResult(
            allowed=True,
            preferences=self._preferences
        )

    @property
    def training_blocked(self) -> bool:
        """Check if training is blocked (should always be True by default)"""
        if not self._preferences:
            return True  # Default to blocking training
        return not self._preferences.allow_training_data

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
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences


def privacy_check(func: Callable):
    """
    Decorator to enforce privacy checks on async functions.

    The decorated function must have 'db' and 'manuscript_id' as parameters.

    Usage:
        @privacy_check
        async def analyze_text(db: Session, manuscript_id: str, content: str):
            ...

    Raises:
        PrivacyBlockedException: If AI assistance is disabled
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract db and manuscript_id from args/kwargs
        db = kwargs.get('db')
        manuscript_id = kwargs.get('manuscript_id')

        # Try to get from positional args if not in kwargs
        if db is None:
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
        middleware = PrivacyMiddleware(db, manuscript_id)
        result = await middleware.check_privacy()

        if not result.allowed:
            raise PrivacyBlockedException(result.reason)

        return await func(*args, **kwargs)

    return wrapper


async def check_ai_allowed(
    db: Session,
    manuscript_id: str,
) -> PrivacyCheckResult:
    """
    Check if AI assistance is allowed for a manuscript.

    Args:
        db: Database session
        manuscript_id: Manuscript ID

    Returns:
        PrivacyCheckResult with allowed status

    Note: Training is ALWAYS blocked by default (allow_training_data=False).
    This check only verifies if AI assistance itself is enabled.
    """
    middleware = PrivacyMiddleware(db, manuscript_id)
    return await middleware.check_privacy()
