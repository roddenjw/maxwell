"""
Privacy Configuration for AI Interactions

This module defines the privacy headers and configurations used to
ensure manuscripts are NOT used for AI training while still allowing
AI assistance features.

Key Principles:
1. Default to maximum privacy (opt-out of training by default)
2. Use API-level controls (commercial API tiers don't train on data)
3. Add explicit headers where supported
4. Minimize data retention
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class AIProvider(str, Enum):
    """AI providers with their training policies"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    LOCAL = "local"


@dataclass
class ProviderPrivacyPolicy:
    """Privacy policy for an AI provider"""
    name: str
    trains_on_api_data: bool  # Does the API tier train on data?
    supports_zdr: bool  # Zero Data Retention option available?
    default_retention_days: int  # How long they keep data
    supports_opt_out_header: bool  # Can we send opt-out headers?
    opt_out_header_name: Optional[str] = None
    documentation_url: Optional[str] = None


# Provider privacy policies (as of 2025-2026)
PROVIDER_POLICIES: Dict[AIProvider, ProviderPrivacyPolicy] = {
    AIProvider.ANTHROPIC: ProviderPrivacyPolicy(
        name="Anthropic",
        trains_on_api_data=False,  # API data not used for training by default
        supports_zdr=True,  # Zero Data Retention available for enterprise
        default_retention_days=30,  # 30 days for safety monitoring
        supports_opt_out_header=True,
        opt_out_header_name="anthropic-beta",
        documentation_url="https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training"
    ),
    AIProvider.OPENAI: ProviderPrivacyPolicy(
        name="OpenAI",
        trains_on_api_data=False,  # API data not used for training since March 2023
        supports_zdr=True,  # Zero retention available
        default_retention_days=30,
        supports_opt_out_header=True,
        opt_out_header_name="OpenAI-Training-Opt-Out",
        documentation_url="https://help.openai.com/en/articles/5722486-how-your-data-is-used-to-improve-model-performance"
    ),
    AIProvider.OPENROUTER: ProviderPrivacyPolicy(
        name="OpenRouter",
        trains_on_api_data=False,  # Routing service, doesn't train
        supports_zdr=False,  # Depends on underlying provider
        default_retention_days=7,
        supports_opt_out_header=False,
        documentation_url="https://openrouter.ai/docs"
    ),
    AIProvider.LOCAL: ProviderPrivacyPolicy(
        name="Local",
        trains_on_api_data=False,  # Local models can't train
        supports_zdr=True,  # Data never leaves machine
        default_retention_days=0,  # No retention
        supports_opt_out_header=False,
    ),
}


@dataclass
class PrivacyHeaders:
    """HTTP headers to send with AI requests for privacy"""
    # Standard opt-out headers
    training_opt_out: str = "true"
    data_retention: str = "minimal"
    content_type: str = "creative-work"
    rights_reserved: str = "true"

    def to_dict(self) -> Dict[str, str]:
        """Convert to header dictionary"""
        return {
            "X-Training-Opt-Out": self.training_opt_out,
            "X-Data-Retention": self.data_retention,
            "X-Content-Type": self.content_type,
            "X-Rights-Reserved": self.rights_reserved,
        }


@dataclass
class AIPrivacyConfig:
    """
    Configuration for privacy-preserving AI interactions.

    This is used by the ContentGateway to ensure all AI requests
    respect author privacy preferences.
    """
    # Provider settings
    provider: AIProvider = AIProvider.ANTHROPIC

    # Privacy settings (defaults protect the author)
    training_opt_out: bool = True
    zero_data_retention: bool = False  # Requires enterprise tier usually
    minimal_context: bool = True  # Only send necessary content

    # Content controls
    max_context_tokens: int = 8000  # Limit data exposure
    strip_metadata: bool = True  # Remove author info, timestamps, etc.
    hash_for_audit: bool = True  # Store content hash for verification

    # Headers to include
    privacy_headers: PrivacyHeaders = field(default_factory=PrivacyHeaders)

    def get_provider_policy(self) -> ProviderPrivacyPolicy:
        """Get the privacy policy for the configured provider"""
        return PROVIDER_POLICIES.get(
            self.provider,
            PROVIDER_POLICIES[AIProvider.LOCAL]  # Safest default
        )

    def build_request_headers(self) -> Dict[str, str]:
        """Build headers for AI API requests"""
        headers = self.privacy_headers.to_dict()

        policy = self.get_provider_policy()
        if policy.supports_opt_out_header and policy.opt_out_header_name:
            headers[policy.opt_out_header_name] = "training-opt-out"

        return headers


# AI crawlers to block via robots.txt (for any web-exposed content)
AI_CRAWLERS = [
    "GPTBot",
    "ChatGPT-User",
    "CCBot",
    "anthropic-ai",
    "ClaudeBot",
    "Claude-Web",
    "Google-Extended",
    "PerplexityBot",
    "Bytespider",
    "Diffbot",
    "Omgilibot",
    "FacebookBot",
    "cohere-ai",
    "Applebot-Extended",
    "amazonbot",
]


# HTTP headers for web responses containing manuscripts
WEB_PROTECTION_HEADERS = {
    "X-Robots-Tag": "noai, noimageai, noarchive",
    "X-Content-Training-Opt-Out": "true",
    "TDMRep": "0",  # TDM Reservation Protocol - 0 means no permission
}


def generate_robots_txt(protected_paths: List[str] = None) -> str:
    """
    Generate robots.txt content that blocks AI crawlers from manuscript content.

    Args:
        protected_paths: List of URL paths to protect. Defaults to common manuscript paths.

    Returns:
        robots.txt content as a string
    """
    if protected_paths is None:
        protected_paths = [
            "/manuscripts/",
            "/chapters/",
            "/api/manuscripts/",
            "/api/chapters/",
            "/preview/",
            "/export/",
        ]

    lines = [
        "# Maxwell Platform - AI Training Protection",
        "# Writers' manuscripts are protected creative works",
        "",
    ]

    # Block each AI crawler
    for crawler in AI_CRAWLERS:
        lines.append(f"User-agent: {crawler}")
        for path in protected_paths:
            lines.append(f"Disallow: {path}")
        lines.append("")

    # Allow regular search engines for discoverability (public pages only)
    lines.extend([
        "# Allow regular search engines for public pages",
        "User-agent: Googlebot",
        "Allow: /",
    ])
    for path in protected_paths:
        lines.append(f"Disallow: {path}")
    lines.append("")

    lines.extend([
        "User-agent: *",
        "Allow: /",
    ])
    for path in protected_paths:
        lines.append(f"Disallow: {path}")

    return "\n".join(lines)


# Default privacy configuration (maximum protection)
DEFAULT_PRIVACY_CONFIG = AIPrivacyConfig(
    training_opt_out=True,
    zero_data_retention=False,
    minimal_context=True,
    max_context_tokens=8000,
    strip_metadata=True,
    hash_for_audit=True,
)
