"""
Unified Writing Feedback Service.

Coordinates all writing analyzers (grammar, style, readability, etc.)
and returns a unified WritingIssue format for the frontend.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid
import time
import logging

from sqlalchemy.orm import Session

from app.services.languagetool_service import (
    languagetool_service,
    LanguageToolSettings,
    GrammarIssue
)
from app.services.fast_coach.style_analyzer import StyleAnalyzer
from app.services.fast_coach.word_analyzer import WordAnalyzer
from app.services.fast_coach.dialogue_analyzer import DialogueAnalyzer
from app.services.fast_coach.readability_analyzer import ReadabilityAnalyzer
from app.services.fast_coach.sentence_starter_analyzer import SentenceStarterAnalyzer
from app.services.fast_coach.overused_phrases_analyzer import OverusedPhrasesAnalyzer
from app.services.fast_coach.types import Suggestion, SuggestionType, SeverityLevel

logger = logging.getLogger(__name__)


class IssueType(str, Enum):
    """Types of writing issues"""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    STYLE = "style"
    WORD_CHOICE = "word_choice"
    DIALOGUE = "dialogue"
    CONSISTENCY = "consistency"
    READABILITY = "readability"
    SENTENCE_VARIETY = "sentence_variety"
    OVERUSED_PHRASE = "overused_phrase"


class IssueSeverity(str, Enum):
    """Severity levels for issues"""
    ERROR = "error"      # Definite mistake (spelling, grammar)
    WARNING = "warning"  # Likely issue (style, consistency)
    INFO = "info"        # Suggestion (readability, variety)


@dataclass
class WritingIssue:
    """A unified writing issue for the frontend"""
    id: str
    type: str
    severity: str

    # Position in text
    start_offset: int
    end_offset: int

    # Issue details
    message: str
    original_text: str
    suggestions: List[str] = field(default_factory=list)

    # Teaching moment (optional)
    teaching_point: Optional[str] = None

    # Metadata for filtering/ignoring
    rule_id: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackSettings:
    """Settings for writing feedback"""
    # Enable/disable by type
    spelling: bool = True
    grammar: bool = True
    style: bool = True
    word_choice: bool = True
    dialogue: bool = True
    consistency: bool = False  # Requires Codex context
    readability: bool = True  # Readability metrics
    sentence_variety: bool = True  # Sentence starter analysis
    overused_phrases: bool = True  # Clichés and overused phrases

    # Genre for readability targets
    genre: str = "adult_fiction"

    # Sensitivity
    show_info_level: bool = False
    min_confidence: float = 0.5

    # Custom dictionary for fiction terms
    custom_dictionary: List[str] = field(default_factory=list)

    # Ignored rules
    ignored_rules: List[str] = field(default_factory=list)

    # Language
    language: str = "en-US"


@dataclass
class FeedbackResponse:
    """Response from writing feedback analysis"""
    issues: List[WritingIssue]
    stats: Dict[str, int]
    analysis_time_ms: int
    text_length: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "stats": self.stats,
            "analysis_time_ms": self.analysis_time_ms,
            "text_length": self.text_length
        }


# Teaching points for different issue types
TEACHING_POINTS = {
    "spelling": "Spelling errors break reader immersion. In fiction, ensure character names and made-up words are added to your custom dictionary.",
    "grammar": "Grammar issues can confuse readers. While some rules can be bent for voice or style, basic grammar maintains clarity.",
    "passive_voice": "Passive voice ('was eaten by') distances readers from the action. Active voice ('ate') creates immediacy. Use passive intentionally for effect.",
    "adverb_overuse": "Adverbs often signal weak verbs. Instead of 'ran quickly', try 'sprinted' or 'dashed'. Strong verbs create vivid prose.",
    "weak_words": "Words like 'very', 'really', and 'just' often dilute impact. Delete them or find stronger alternatives.",
    "telling_verbs": "Verbs like 'felt', 'thought', and 'realized' can distance readers. Show emotions through action and dialogue instead.",
    "cliche": "Familiar phrases slide past readers without impact. Fresh language makes your prose memorable.",
    "dialogue_tags": "'Said' is invisible to readers. Fancy tags like 'exclaimed' or 'interjected' draw unwanted attention. Use action beats for variety.",
    "repetition": "Repeated words within close proximity can feel clunky. Vary your vocabulary or restructure sentences.",
    "readability": "Readability scores help calibrate prose complexity for your audience. Genre fiction typically targets 6th-9th grade level.",
    "sentence_variety": "Varied sentence openings create rhythm and flow. Repetitive starters (He..., She..., The...) can feel monotonous.",
    "overused_phrase": "Overused phrases like 'took a deep breath' or 'heart pounded' slide past readers. Fresh, specific language creates impact.",
}


class WritingFeedbackService:
    """
    Unified service for all writing feedback.

    Coordinates grammar checking (LanguageTool), style analysis,
    word choice, dialogue analysis, and more.
    """

    def __init__(self):
        self.style_analyzer = StyleAnalyzer()
        self.word_analyzer = WordAnalyzer()
        self.dialogue_analyzer = DialogueAnalyzer()
        self.readability_analyzer = ReadabilityAnalyzer()
        self.sentence_starter_analyzer = SentenceStarterAnalyzer()
        self.overused_phrases_analyzer = OverusedPhrasesAnalyzer()

    def analyze_realtime(
        self,
        text: str,
        settings: Optional[FeedbackSettings] = None,
        manuscript_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> FeedbackResponse:
        """
        Fast analysis for real-time feedback while typing.

        Only runs quick checks: spelling, basic grammar.
        Designed to complete in <500ms for responsive UX.

        Args:
            text: Text to analyze
            settings: Feedback settings
            manuscript_id: Optional manuscript for custom dictionary
            db: Optional database session

        Returns:
            FeedbackResponse with issues found
        """
        start_time = time.time()
        settings = settings or FeedbackSettings()
        issues: List[WritingIssue] = []

        # Only run grammar/spelling for real-time (fast)
        if settings.spelling or settings.grammar:
            grammar_issues = self._check_grammar(text, settings)
            issues.extend(grammar_issues)

        # Calculate stats
        stats = self._calculate_stats(issues)
        analysis_time_ms = int((time.time() - start_time) * 1000)

        return FeedbackResponse(
            issues=issues,
            stats=stats,
            analysis_time_ms=analysis_time_ms,
            text_length=len(text)
        )

    def analyze_paragraph(
        self,
        text: str,
        settings: Optional[FeedbackSettings] = None,
        manuscript_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> FeedbackResponse:
        """
        Paragraph-level analysis.

        Runs grammar + style checks. Triggered on paragraph completion.
        Target: <2s response time.

        Args:
            text: Text to analyze
            settings: Feedback settings
            manuscript_id: Optional manuscript for context
            db: Optional database session

        Returns:
            FeedbackResponse with issues found
        """
        start_time = time.time()
        settings = settings or FeedbackSettings()
        issues: List[WritingIssue] = []

        # Grammar/spelling
        if settings.spelling or settings.grammar:
            grammar_issues = self._check_grammar(text, settings)
            issues.extend(grammar_issues)

        # Style analysis
        if settings.style:
            style_issues = self._check_style(text, settings)
            issues.extend(style_issues)

        # Word choice
        if settings.word_choice:
            word_issues = self._check_word_choice(text, settings)
            issues.extend(word_issues)

        # Overused phrases (quick check)
        if settings.overused_phrases:
            overused_issues = self._check_overused_phrases(text, settings)
            issues.extend(overused_issues)

        # Filter by confidence and severity
        issues = self._filter_issues(issues, settings)

        # Calculate stats
        stats = self._calculate_stats(issues)
        analysis_time_ms = int((time.time() - start_time) * 1000)

        return FeedbackResponse(
            issues=issues,
            stats=stats,
            analysis_time_ms=analysis_time_ms,
            text_length=len(text)
        )

    def analyze_chapter(
        self,
        text: str,
        settings: Optional[FeedbackSettings] = None,
        manuscript_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> FeedbackResponse:
        """
        Full chapter analysis.

        Runs all analyzers including dialogue analysis.
        Triggered manually or on save. Target: <10s response time.

        Args:
            text: Full chapter text
            settings: Feedback settings
            manuscript_id: Manuscript ID for context
            chapter_id: Chapter ID
            db: Database session for Codex lookup

        Returns:
            FeedbackResponse with all issues found
        """
        start_time = time.time()
        settings = settings or FeedbackSettings()
        issues: List[WritingIssue] = []

        # Grammar/spelling
        if settings.spelling or settings.grammar:
            grammar_issues = self._check_grammar(text, settings)
            issues.extend(grammar_issues)

        # Style analysis
        if settings.style:
            style_issues = self._check_style(text, settings)
            issues.extend(style_issues)

        # Word choice
        if settings.word_choice:
            word_issues = self._check_word_choice(text, settings)
            issues.extend(word_issues)

        # Dialogue analysis
        if settings.dialogue:
            dialogue_issues = self._check_dialogue(text, settings)
            issues.extend(dialogue_issues)

        # Readability metrics
        if settings.readability:
            readability_issues = self._check_readability(text, settings)
            issues.extend(readability_issues)

        # Sentence variety
        if settings.sentence_variety:
            variety_issues = self._check_sentence_variety(text, settings)
            issues.extend(variety_issues)

        # Overused phrases
        if settings.overused_phrases:
            overused_issues = self._check_overused_phrases(text, settings)
            issues.extend(overused_issues)

        # Filter by confidence and severity
        issues = self._filter_issues(issues, settings)

        # Sort by position
        issues.sort(key=lambda x: x.start_offset)

        # Calculate stats
        stats = self._calculate_stats(issues)
        analysis_time_ms = int((time.time() - start_time) * 1000)

        return FeedbackResponse(
            issues=issues,
            stats=stats,
            analysis_time_ms=analysis_time_ms,
            text_length=len(text)
        )

    def _check_grammar(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check grammar and spelling with LanguageTool"""
        issues = []

        if not languagetool_service.is_available():
            logger.debug("LanguageTool not available, skipping grammar check")
            return issues

        lt_settings = LanguageToolSettings(
            enabled=True,
            language=settings.language,
            ignore_rules=settings.ignored_rules,
            custom_dictionary=settings.custom_dictionary,
            check_spelling=settings.spelling,
            check_grammar=settings.grammar,
            check_style=False,  # We have our own style checker
            check_punctuation=settings.grammar
        )

        grammar_issues = languagetool_service.check_text(text, lt_settings)

        for gi in grammar_issues:
            # Map LanguageTool category to our type
            issue_type = self._map_lt_category(gi.category)
            severity = IssueSeverity.ERROR if issue_type == IssueType.SPELLING else IssueSeverity.WARNING

            # Get original text
            original = text[gi.offset:gi.offset + gi.length] if gi.offset + gi.length <= len(text) else ""

            issues.append(WritingIssue(
                id=str(uuid.uuid4()),
                type=issue_type.value,
                severity=severity.value,
                start_offset=gi.offset,
                end_offset=gi.offset + gi.length,
                message=gi.message,
                original_text=original,
                suggestions=gi.replacements,
                teaching_point=TEACHING_POINTS.get(issue_type.value),
                rule_id=gi.rule_id,
                category=gi.category,
                confidence=0.9  # LanguageTool is generally reliable
            ))

        return issues

    def _check_style(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check style issues using StyleAnalyzer"""
        issues = []

        try:
            suggestions = self.style_analyzer.analyze(text)

            for s in suggestions:
                issue_type = self._map_suggestion_type(s.type)

                # Get original text
                original = ""
                if s.start_char is not None and s.end_char is not None:
                    original = text[s.start_char:s.end_char] if s.end_char <= len(text) else ""

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=issue_type.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text=original,
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("rule_id") if s.metadata else None,
                    category="STYLE",
                    confidence=0.7
                ))
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")

        return issues

    def _check_word_choice(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check word choice issues using WordAnalyzer"""
        issues = []

        try:
            suggestions = self.word_analyzer.analyze(text)

            for s in suggestions:
                # Get original text
                original = ""
                if s.start_char is not None and s.end_char is not None:
                    original = text[s.start_char:s.end_char] if s.end_char <= len(text) else ""

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=IssueType.WORD_CHOICE.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text=original,
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("rule_id") if s.metadata else None,
                    category="WORD_CHOICE",
                    confidence=0.6
                ))
        except Exception as e:
            logger.error(f"Word choice analysis failed: {e}")

        return issues

    def _check_dialogue(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check dialogue issues using DialogueAnalyzer"""
        issues = []

        try:
            suggestions = self.dialogue_analyzer.analyze(text)

            for s in suggestions:
                # Get original text
                original = ""
                if s.start_char is not None and s.end_char is not None:
                    original = text[s.start_char:s.end_char] if s.end_char <= len(text) else ""

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=IssueType.DIALOGUE.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text=original,
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("rule_id") if s.metadata else None,
                    category="DIALOGUE",
                    confidence=0.7
                ))
        except Exception as e:
            logger.error(f"Dialogue analysis failed: {e}")

        return issues

    def _check_readability(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check readability metrics using ReadabilityAnalyzer"""
        issues = []

        try:
            suggestions = self.readability_analyzer.analyze(
                text,
                genre=settings.genre,
                include_details=True
            )

            for s in suggestions:
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=IssueType.READABILITY.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text="",  # Readability is document-level
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("rule_id") if s.metadata else None,
                    category="READABILITY",
                    confidence=0.8
                ))
        except Exception as e:
            logger.error(f"Readability analysis failed: {e}")

        return issues

    def _check_sentence_variety(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check sentence starter variety using SentenceStarterAnalyzer"""
        issues = []

        try:
            suggestions = self.sentence_starter_analyzer.analyze(text)

            for s in suggestions:
                # Get original text if position available
                original = ""
                if s.start_char is not None and s.end_char is not None:
                    original = text[s.start_char:s.end_char] if s.end_char <= len(text) else ""

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=IssueType.SENTENCE_VARIETY.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text=original,
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("rule_id") if s.metadata else None,
                    category="SENTENCE_VARIETY",
                    confidence=0.7
                ))
        except Exception as e:
            logger.error(f"Sentence variety analysis failed: {e}")

        return issues

    def _check_overused_phrases(
        self,
        text: str,
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Check for overused phrases using OverusedPhrasesAnalyzer"""
        issues = []

        try:
            suggestions = self.overused_phrases_analyzer.analyze(text)

            for s in suggestions:
                # Get original text
                original = ""
                if s.start_char is not None and s.end_char is not None:
                    original = text[s.start_char:s.end_char] if s.end_char <= len(text) else ""

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    type=IssueType.OVERUSED_PHRASE.value,
                    severity=self._map_severity(s.severity).value,
                    start_offset=s.start_char or 0,
                    end_offset=s.end_char or len(text),
                    message=s.message,
                    original_text=original,
                    suggestions=[s.suggestion] if s.suggestion else [],
                    teaching_point=self._get_teaching_point(s),
                    rule_id=s.metadata.get("phrase") if s.metadata else None,
                    category=s.metadata.get("category", "OVERUSED_PHRASE") if s.metadata else "OVERUSED_PHRASE",
                    confidence=0.8
                ))
        except Exception as e:
            logger.error(f"Overused phrases analysis failed: {e}")

        return issues

    def _map_lt_category(self, category: str) -> IssueType:
        """Map LanguageTool category to our issue type"""
        category_map = {
            "TYPOS": IssueType.SPELLING,
            "MISSPELLING": IssueType.SPELLING,
            "SPELLING": IssueType.SPELLING,
            "GRAMMAR": IssueType.GRAMMAR,
            "PUNCTUATION": IssueType.GRAMMAR,
            "STYLE": IssueType.STYLE,
            "TYPOGRAPHY": IssueType.STYLE,
            "REDUNDANCY": IssueType.STYLE,
            "CASING": IssueType.GRAMMAR,
        }
        return category_map.get(category, IssueType.GRAMMAR)

    def _map_suggestion_type(self, stype: SuggestionType) -> IssueType:
        """Map Fast Coach suggestion type to our issue type"""
        type_map = {
            SuggestionType.STYLE: IssueType.STYLE,
            SuggestionType.WORD_CHOICE: IssueType.WORD_CHOICE,
            SuggestionType.DIALOGUE: IssueType.DIALOGUE,
            SuggestionType.DIALOGUE_TAGS: IssueType.DIALOGUE,
            SuggestionType.CONSISTENCY: IssueType.CONSISTENCY,
            SuggestionType.READABILITY: IssueType.READABILITY,
            SuggestionType.SENTENCE_VARIETY: IssueType.SENTENCE_VARIETY,
            SuggestionType.OVERUSED_PHRASE: IssueType.OVERUSED_PHRASE,
        }
        return type_map.get(stype, IssueType.STYLE)

    def _map_severity(self, severity: SeverityLevel) -> IssueSeverity:
        """Map Fast Coach severity to our severity"""
        severity_map = {
            SeverityLevel.ERROR: IssueSeverity.ERROR,
            SeverityLevel.WARNING: IssueSeverity.WARNING,
            SeverityLevel.INFO: IssueSeverity.INFO,
        }
        return severity_map.get(severity, IssueSeverity.WARNING)

    def _get_teaching_point(self, suggestion: Suggestion) -> Optional[str]:
        """Get teaching point for a suggestion"""
        if suggestion.metadata and "teaching_point" in suggestion.metadata:
            return suggestion.metadata["teaching_point"]

        # Look up by message keywords
        msg_lower = suggestion.message.lower()
        if "passive" in msg_lower:
            return TEACHING_POINTS.get("passive_voice")
        elif "adverb" in msg_lower:
            return TEACHING_POINTS.get("adverb_overuse")
        elif "weak" in msg_lower or "very" in msg_lower or "really" in msg_lower:
            return TEACHING_POINTS.get("weak_words")
        elif "telling" in msg_lower or "felt" in msg_lower:
            return TEACHING_POINTS.get("telling_verbs")
        elif "clich" in msg_lower or "overused" in msg_lower:
            return TEACHING_POINTS.get("overused_phrase")
        elif "dialogue" in msg_lower or "tag" in msg_lower or "said" in msg_lower:
            return TEACHING_POINTS.get("dialogue_tags")
        elif "repet" in msg_lower:
            return TEACHING_POINTS.get("repetition")
        elif "readab" in msg_lower or "grade" in msg_lower or "flesch" in msg_lower:
            return TEACHING_POINTS.get("readability")
        elif "sentence" in msg_lower and ("start" in msg_lower or "variety" in msg_lower):
            return TEACHING_POINTS.get("sentence_variety")

        return None

    def _filter_issues(
        self,
        issues: List[WritingIssue],
        settings: FeedbackSettings
    ) -> List[WritingIssue]:
        """Filter issues by settings"""
        filtered = []

        for issue in issues:
            # Filter by severity
            if not settings.show_info_level and issue.severity == IssueSeverity.INFO.value:
                continue

            # Filter by confidence
            if issue.confidence and issue.confidence < settings.min_confidence:
                continue

            # Filter by ignored rules
            if issue.rule_id and issue.rule_id in settings.ignored_rules:
                continue

            filtered.append(issue)

        return filtered

    def _calculate_stats(self, issues: List[WritingIssue]) -> Dict[str, int]:
        """Calculate issue statistics"""
        stats: Dict[str, int] = {
            "total": len(issues),
            "spelling": 0,
            "grammar": 0,
            "style": 0,
            "word_choice": 0,
            "dialogue": 0,
            "readability": 0,
            "sentence_variety": 0,
            "overused_phrase": 0,
            "errors": 0,
            "warnings": 0,
            "info": 0
        }

        for issue in issues:
            # Count by type
            if issue.type in stats:
                stats[issue.type] += 1

            # Count by severity
            if issue.severity == "error":
                stats["errors"] += 1
            elif issue.severity == "warning":
                stats["warnings"] += 1
            else:
                stats["info"] += 1

        return stats


# Singleton instance
writing_feedback_service = WritingFeedbackService()
