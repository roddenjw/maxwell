"""
LanguageTool integration service for grammar and spelling checks.
Uses language-tool-python library for local operation (no external API calls).
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Try to import language_tool_python, gracefully handle if not installed
try:
    import language_tool_python
    LANGUAGETOOL_AVAILABLE = True
except ImportError:
    language_tool_python = None
    LANGUAGETOOL_AVAILABLE = False
    logger.warning("language-tool-python not installed. Grammar checking unavailable.")


@dataclass
class GrammarIssue:
    """A grammar or spelling issue detected by LanguageTool"""
    message: str
    replacements: List[str]
    offset: int
    length: int
    rule_id: str
    category: str  # GRAMMAR, SPELLING, STYLE, PUNCTUATION, etc.
    context: str
    context_offset: int = 0  # Offset within context string


@dataclass
class LanguageToolSettings:
    """Settings for grammar checking"""
    enabled: bool = True
    language: str = "en-US"
    ignore_rules: List[str] = field(default_factory=list)
    custom_dictionary: List[str] = field(default_factory=list)

    # Category toggles
    check_spelling: bool = True
    check_grammar: bool = True
    check_style: bool = False  # Style checks can be noisy
    check_punctuation: bool = True


class LanguageToolService:
    """
    Service for grammar and spelling checking via LanguageTool.

    Uses language-tool-python which runs LanguageTool locally via Java.
    No external API calls - all processing is local.
    """

    # Default rules to ignore (commonly false positives for fiction)
    DEFAULT_IGNORE_RULES = {
        "WHITESPACE_RULE",           # Whitespace issues
        "EN_QUOTES",                 # Smart quote issues
        "DASH_RULE",                 # En-dash vs em-dash
        "MORFOLOGIK_RULE_EN_US",     # Sometimes too aggressive on proper nouns
        "UPPERCASE_SENTENCE_START",   # Intentional for style
        "SENTENCE_FRAGMENT",          # Often intentional in dialogue
        "COMMA_PARENTHESIS_WHITESPACE",
    }

    # Categories that map to our issue types
    CATEGORY_MAP = {
        "TYPOS": "spelling",
        "MISSPELLING": "spelling",
        "SPELLING": "spelling",
        "GRAMMAR": "grammar",
        "PUNCTUATION": "grammar",
        "STYLE": "style",
        "TYPOGRAPHY": "style",
        "REDUNDANCY": "style",
        "CASING": "grammar",
    }

    def __init__(self):
        self._tool: Optional["language_tool_python.LanguageTool"] = None
        self._language = "en-US"
        self._personal_dict: Set[str] = set()

    def is_available(self) -> bool:
        """Check if LanguageTool is available"""
        return LANGUAGETOOL_AVAILABLE

    def _get_tool(self) -> "language_tool_python.LanguageTool":
        """Lazy initialization of LanguageTool"""
        if not LANGUAGETOOL_AVAILABLE:
            raise RuntimeError(
                "LanguageTool not available. Install with: pip install language-tool-python"
            )

        if self._tool is None:
            logger.info(f"Initializing LanguageTool with language: {self._language}")
            self._tool = language_tool_python.LanguageTool(self._language)
        return self._tool

    def check_text(
        self,
        text: str,
        settings: Optional[LanguageToolSettings] = None
    ) -> List[GrammarIssue]:
        """
        Check text for grammar and spelling issues.

        Args:
            text: Text to check
            settings: Optional settings for customization

        Returns:
            List of GrammarIssue objects with positions and suggestions
        """
        if not text or len(text.strip()) < 3:
            return []

        if not self.is_available():
            logger.warning("LanguageTool not available, skipping grammar check")
            return []

        settings = settings or LanguageToolSettings()

        if not settings.enabled:
            return []

        tool = self._get_tool()

        # Build set of rules to ignore
        ignore_rules = self.DEFAULT_IGNORE_RULES.copy()
        if settings.ignore_rules:
            ignore_rules.update(settings.ignore_rules)

        # Add custom dictionary words
        if settings.custom_dictionary:
            for word in settings.custom_dictionary:
                if word not in self._personal_dict:
                    try:
                        tool.add_to_personal_dict(word)
                        self._personal_dict.add(word)
                    except Exception as e:
                        logger.debug(f"Could not add '{word}' to dictionary: {e}")

        try:
            matches = tool.check(text)
        except Exception as e:
            logger.error(f"LanguageTool check failed: {e}")
            return []

        issues = []
        for match in matches:
            # Skip ignored rules
            if match.ruleId in ignore_rules:
                continue

            # Get category and map to our type
            category = match.category or "GRAMMAR"

            # Filter by category settings
            if category in ("TYPOS", "MISSPELLING", "SPELLING") and not settings.check_spelling:
                continue
            if category == "GRAMMAR" and not settings.check_grammar:
                continue
            if category in ("STYLE", "TYPOGRAPHY", "REDUNDANCY") and not settings.check_style:
                continue
            if category == "PUNCTUATION" and not settings.check_punctuation:
                continue

            # Extract context around the error
            context_start = max(0, match.offset - 20)
            context_end = min(len(text), match.offset + match.errorLength + 20)
            context = text[context_start:context_end]

            issues.append(GrammarIssue(
                message=match.message,
                replacements=match.replacements[:5] if match.replacements else [],
                offset=match.offset,
                length=match.errorLength,
                rule_id=match.ruleId,
                category=category,
                context=context,
                context_offset=match.offset - context_start
            ))

        return issues

    def configure_language(self, language: str):
        """
        Change the language for checking.

        Args:
            language: Language code (e.g., 'en-US', 'en-GB', 'en-AU')
        """
        if language != self._language:
            self._language = language
            self._tool = None  # Force re-initialization
            self._personal_dict.clear()
            logger.info(f"LanguageTool language changed to: {language}")

    def add_to_dictionary(self, word: str):
        """
        Add a word to the personal dictionary.

        Args:
            word: Word to add (e.g., character name, made-up word)
        """
        if not self.is_available():
            return

        if word in self._personal_dict:
            return

        tool = self._get_tool()
        try:
            tool.add_to_personal_dict(word)
            self._personal_dict.add(word)
            logger.debug(f"Added '{word}' to personal dictionary")
        except Exception as e:
            logger.warning(f"Failed to add '{word}' to dictionary: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "en-US",  # American English
            "en-GB",  # British English
            "en-AU",  # Australian English
            "en-CA",  # Canadian English
            "en-NZ",  # New Zealand English
        ]

    def get_rule_categories(self) -> List[str]:
        """Get available rule categories"""
        return list(self.CATEGORY_MAP.keys())

    def close(self):
        """Clean up resources"""
        if self._tool is not None:
            try:
                self._tool.close()
            except Exception:
                pass
            self._tool = None


# Singleton instance
languagetool_service = LanguageToolService()
