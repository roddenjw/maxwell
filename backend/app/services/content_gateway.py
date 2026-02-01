"""
Content Gateway Service

Central privacy layer that controls all data flowing to AI providers.
This ensures manuscripts are protected from training while allowing
AI assistance features.

Key Responsibilities:
1. Verify author privacy preferences before any AI request
2. Sanitize content (remove metadata, PII if any)
3. Apply token budgets to minimize data exposure
4. Add privacy headers to all requests
5. Audit all AI interactions (without storing raw content)
"""

import hashlib
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.privacy import AuthorPrivacyPreferences, AIInteractionAudit, ContentSharingLevel
from app.services.privacy_config import (
    AIPrivacyConfig,
    DEFAULT_PRIVACY_CONFIG,
    AIProvider,
)


@dataclass
class SafeAIRequest:
    """A sanitized, privacy-compliant AI request"""
    content: str
    system_prompt: str
    headers: Dict[str, str]
    metadata: Dict[str, Any]

    # Privacy flags
    training_opted_out: bool
    content_hash: str
    original_token_count: int
    sanitized_token_count: int


@dataclass
class ContentGatewayResult:
    """Result from content gateway processing"""
    allowed: bool
    request: Optional[SafeAIRequest] = None
    error: Optional[str] = None
    feature_disabled: Optional[str] = None


class AIFeatureDisabledException(Exception):
    """Raised when an AI feature is disabled by author preferences"""
    def __init__(self, feature: str, message: str = None):
        self.feature = feature
        self.message = message or f"AI feature '{feature}' is disabled by author preferences"
        super().__init__(self.message)


class ContentGateway:
    """
    Central gateway for all AI content interactions.

    All manuscript content MUST pass through this gateway before being
    sent to any AI provider. This ensures privacy compliance.
    """

    def __init__(self, db: Session, config: AIPrivacyConfig = None):
        self.db = db
        self.config = config or DEFAULT_PRIVACY_CONFIG

    async def prepare_ai_request(
        self,
        manuscript_id: str,
        content: str,
        request_type: str,
        chapter_id: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> ContentGatewayResult:
        """
        Prepare content for AI processing with full privacy protection.

        Args:
            manuscript_id: The manuscript ID
            content: Raw content to process
            request_type: Type of AI request (e.g., 'grammar_check', 'plot_analysis')
            chapter_id: Optional chapter ID for more specific tracking
            additional_context: Optional additional context (already sanitized)

        Returns:
            ContentGatewayResult with either a SafeAIRequest or an error
        """
        # 1. Get author preferences
        preferences = await self._get_preferences(manuscript_id)

        # 2. Check if AI assistance is allowed
        if not preferences.allow_ai_assistance:
            return ContentGatewayResult(
                allowed=False,
                error="AI assistance is disabled for this manuscript"
            )

        # 3. Check if specific feature is allowed
        feature_name = self._map_request_type_to_feature(request_type)
        if not preferences.allows_feature(feature_name):
            return ContentGatewayResult(
                allowed=False,
                feature_disabled=feature_name,
                error=f"AI feature '{feature_name}' is disabled by author preferences"
            )

        # 4. Check content sharing level
        if preferences.content_sharing_level == ContentSharingLevel.PRIVATE.value:
            return ContentGatewayResult(
                allowed=False,
                error="Content sharing is set to private - no AI access allowed"
            )

        # 5. Sanitize content
        sanitized = self._sanitize_content(content)

        # 6. Apply token budget
        limited = self._apply_token_budget(sanitized)

        # 7. Build privacy headers
        headers = self.config.build_request_headers()

        # 8. Calculate content hash for audit (not the content itself)
        content_hash = self._hash_content(content)

        # 9. Build system prompt with privacy instructions
        system_prompt = self._build_system_prompt(request_type, preferences)

        # 10. Prepare the safe request
        safe_request = SafeAIRequest(
            content=limited,
            system_prompt=system_prompt,
            headers=headers,
            metadata={
                "manuscript_id": manuscript_id,
                "chapter_id": chapter_id,
                "request_type": request_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
            training_opted_out=not preferences.allow_training_data,
            content_hash=content_hash,
            original_token_count=self._estimate_tokens(content),
            sanitized_token_count=self._estimate_tokens(limited),
        )

        return ContentGatewayResult(allowed=True, request=safe_request)

    async def audit_interaction(
        self,
        manuscript_id: str,
        request_type: str,
        provider: str,
        model: str,
        tokens_sent: int,
        tokens_received: int,
        content_hash: str,
        chapter_id: Optional[str] = None,
        cost_usd: float = 0.0,
    ) -> AIInteractionAudit:
        """
        Record an AI interaction for audit purposes.

        IMPORTANT: This does NOT store the actual content, only metadata.
        """
        preferences = await self._get_preferences(manuscript_id)

        audit = AIInteractionAudit(
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            interaction_type=request_type,
            provider=provider,
            model=model,
            tokens_sent=tokens_sent,
            tokens_received=tokens_received,
            training_opted_out=not preferences.allow_training_data,
            zero_data_retention=False,  # Would need enterprise tier verification
            content_hash=content_hash,
            estimated_cost_usd=int(cost_usd * 1_000_000),  # Convert to microdollars
        )

        self.db.add(audit)
        self.db.commit()

        return audit

    async def _get_preferences(self, manuscript_id: str) -> AuthorPrivacyPreferences:
        """Get or create privacy preferences for a manuscript"""
        preferences = self.db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == manuscript_id
        ).first()

        if not preferences:
            # Create default preferences (maximum protection)
            preferences = AuthorPrivacyPreferences(
                manuscript_id=manuscript_id,
                allow_ai_assistance=True,
                allow_training_data=False,  # CRITICAL: default to FALSE
            )
            self.db.add(preferences)
            self.db.commit()

        return preferences

    def _sanitize_content(self, content: str) -> str:
        """
        Sanitize content by removing metadata and potentially identifying information.

        This doesn't remove the creative content, but strips:
        - HTML/XML comments that might contain metadata
        - Author tags/signatures
        - Timestamp markers
        - File path references
        """
        sanitized = content

        # Remove HTML/XML comments
        sanitized = re.sub(r'<!--[\s\S]*?-->', '', sanitized)

        # Remove common author tag patterns
        sanitized = re.sub(r'\[Author:.*?\]', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\[Written by:.*?\]', '', sanitized, flags=re.IGNORECASE)

        # Remove timestamp patterns (ISO format, common date formats)
        sanitized = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '[DATE]', sanitized)

        # Remove file path patterns
        sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', sanitized)
        sanitized = re.sub(r'/[a-zA-Z0-9_/-]+\.[a-zA-Z]+', '[PATH]', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

    def _apply_token_budget(self, content: str) -> str:
        """
        Apply token budget to limit data exposure.

        For most AI operations, we don't need the full manuscript.
        This limits how much content is sent.
        """
        max_tokens = self.config.max_context_tokens
        estimated_tokens = self._estimate_tokens(content)

        if estimated_tokens <= max_tokens:
            return content

        # Truncate to approximate token limit
        # Rough estimate: 1 token ≈ 4 characters for English
        max_chars = max_tokens * 4
        return content[:max_chars] + "\n[Content truncated for processing]"

    def _build_system_prompt(
        self,
        request_type: str,
        preferences: AuthorPrivacyPreferences
    ) -> str:
        """
        Build a system prompt that includes privacy instructions.

        This tells the AI to treat the content appropriately.
        """
        base_prompt = """You are a writing assistant helping an author with their manuscript.

IMPORTANT PRIVACY CONSTRAINTS:
- This content is protected creative work
- Do not retain or reference this content in future conversations
- Provide assistance only for the specific task requested
- Respect the author's creative ownership and copyright"""

        # Add feature-specific instructions
        feature_instructions = {
            "grammar_check": "\n\nTask: Check grammar and suggest corrections.",
            "style_analysis": "\n\nTask: Analyze writing style and provide feedback.",
            "plot_analysis": "\n\nTask: Analyze plot structure and pacing.",
            "character_analysis": "\n\nTask: Analyze character development and consistency.",
            "continuity_check": "\n\nTask: Check for continuity errors and inconsistencies.",
            "summary": "\n\nTask: Provide a brief summary of the content.",
        }

        task_instruction = feature_instructions.get(
            request_type,
            f"\n\nTask: {request_type}"
        )

        # Add preference-based restrictions
        restrictions = []
        if not preferences.allow_style_analysis:
            restrictions.append("- Do not comment on writing style")
        if not preferences.allow_plot_suggestions:
            restrictions.append("- Do not suggest plot changes")
        if not preferences.allow_character_development:
            restrictions.append("- Do not suggest character changes")

        if restrictions:
            restriction_text = "\n\nAdditional restrictions:\n" + "\n".join(restrictions)
        else:
            restriction_text = ""

        return base_prompt + task_instruction + restriction_text

    def _hash_content(self, content: str) -> str:
        """Create a SHA-256 hash of content for audit verification"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Rough estimate: ~4 characters per token for English.
        For more accuracy, use tiktoken or similar.
        """
        return len(text) // 4

    def _map_request_type_to_feature(self, request_type: str) -> str:
        """Map AI request types to feature preference names"""
        mapping = {
            "grammar_check": "grammar_check",
            "spell_check": "grammar_check",
            "style_analysis": "style_analysis",
            "style_suggestion": "style_analysis",
            "plot_analysis": "plot_suggestions",
            "plot_suggestion": "plot_suggestions",
            "character_analysis": "character_development",
            "character_suggestion": "character_development",
            "continuity_check": "continuity_check",
            "timeline_check": "continuity_check",
        }
        return mapping.get(request_type, request_type)


# Global instance factory
def get_content_gateway(db: Session, config: AIPrivacyConfig = None) -> ContentGateway:
    """Get a ContentGateway instance"""
    return ContentGateway(db, config)
