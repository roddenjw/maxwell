"""
Fast Coach - Real-time writing analysis
Provides instant, lightweight feedback without AI API calls
"""

from .types import Suggestion, SuggestionType, SeverityLevel
from .style_analyzer import StyleAnalyzer
from .word_analyzer import WordAnalyzer
from .dialogue_analyzer import DialogueAnalyzer
from .consistency_checker import ConsistencyChecker

__all__ = [
    'Suggestion',
    'SuggestionType',
    'SeverityLevel',
    'StyleAnalyzer',
    'WordAnalyzer',
    'DialogueAnalyzer',
    'ConsistencyChecker',
]
