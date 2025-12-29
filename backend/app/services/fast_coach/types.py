"""
Type definitions for Fast Coach suggestions
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


class SuggestionType(str, Enum):
    """Types of suggestions"""
    STYLE = "STYLE"
    WORD_CHOICE = "WORD_CHOICE"
    CONSISTENCY = "CONSISTENCY"
    PACING = "PACING"
    VOICE = "VOICE"
    REPETITION = "REPETITION"
    SHOW_NOT_TELL = "SHOW_NOT_TELL"
    DIALOGUE = "DIALOGUE"


class SeverityLevel(str, Enum):
    """Severity of the suggestion"""
    INFO = "INFO"           # Gentle suggestion
    WARNING = "WARNING"     # Should probably address
    ERROR = "ERROR"         # Definite issue


class Suggestion(BaseModel):
    """A single writing suggestion from Fast Coach"""
    type: SuggestionType
    severity: SeverityLevel
    message: str
    suggestion: str

    # Optional location info
    line: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None

    # Optional highlight
    highlight_word: Optional[str] = None

    # Optional replacement text (for quick-fix suggestions)
    replacement: Optional[str] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "line": self.line,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "highlight_word": self.highlight_word,
            "replacement": self.replacement,
            "metadata": self.metadata or {}
        }
