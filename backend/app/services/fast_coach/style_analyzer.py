"""
Style Analyzer - Real-time style checking
Analyzes writing style for readability, sentence variance, passive voice, etc.
"""

import re
import numpy as np
from typing import List
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

from .types import Suggestion, SuggestionType, SeverityLevel


# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class StyleAnalyzer:
    """Analyzes writing style in real-time"""

    def __init__(self):
        # Passive voice patterns
        self.passive_patterns = [
            r'\b(am|is|are|was|were|been|being)\s+\w+ed\b',
            r'\b(am|is|are|was|were|been|being)\s+\w+en\b'
        ]

        # Common adverbs ending in -ly
        self.adverb_pattern = r'\b\w+ly\b'

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze text for style issues

        Args:
            text: The text to analyze

        Returns:
            List of style suggestions
        """
        if not text or len(text.strip()) < 50:
            return []  # Too short to analyze

        suggestions = []

        # Sentence variance check
        suggestions.extend(self._check_sentence_variance(text))

        # Passive voice check
        suggestions.extend(self._check_passive_voice(text))

        # Adverb density check
        suggestions.extend(self._check_adverb_density(text))

        # Paragraph length check
        suggestions.extend(self._check_paragraph_length(text))

        return suggestions

    def _check_sentence_variance(self, text: str) -> List[Suggestion]:
        """Check if sentence lengths are too uniform"""
        suggestions = []

        try:
            sentences = sent_tokenize(text)
            if len(sentences) < 3:
                return suggestions  # Need at least 3 sentences

            lengths = [len(word_tokenize(s)) for s in sentences]
            std_dev = np.std(lengths)
            avg_length = np.mean(lengths)

            # Low variance = monotonous rhythm
            if std_dev < 3 and len(sentences) >= 5:
                suggestions.append(Suggestion(
                    type=SuggestionType.STYLE,
                    severity=SeverityLevel.INFO,
                    message="Sentence lengths are very uniform",
                    suggestion="Consider varying sentence length for better rhythm. Mix short punchy sentences with longer flowing ones.",
                    metadata={
                        "avg_length": float(avg_length),
                        "std_dev": float(std_dev),
                        "sentence_count": len(sentences)
                    }
                ))

            # Very long average = readability issue
            if avg_length > 25:
                suggestions.append(Suggestion(
                    type=SuggestionType.STYLE,
                    severity=SeverityLevel.WARNING,
                    message=f"Average sentence length is {avg_length:.1f} words",
                    suggestion="Consider breaking up some longer sentences for better readability.",
                    metadata={"avg_length": float(avg_length)}
                ))

        except Exception as e:
            # Silently fail - don't interrupt user
            pass

        return suggestions

    def _check_passive_voice(self, text: str) -> List[Suggestion]:
        """Detect excessive passive voice"""
        suggestions = []

        try:
            sentences = sent_tokenize(text)
            if len(sentences) == 0:
                return suggestions

            passive_count = 0
            for pattern in self.passive_patterns:
                passive_count += len(re.findall(pattern, text, re.IGNORECASE))

            passive_ratio = passive_count / len(sentences)

            # More than 30% passive voice is excessive
            if passive_ratio > 0.3:
                suggestions.append(Suggestion(
                    type=SuggestionType.VOICE,
                    severity=SeverityLevel.WARNING,
                    message=f"High passive voice usage ({passive_count} instances in {len(sentences)} sentences)",
                    suggestion="Consider using active voice for stronger, more direct prose. Active voice often creates more engaging scenes.",
                    metadata={
                        "passive_count": passive_count,
                        "sentence_count": len(sentences),
                        "passive_ratio": float(passive_ratio)
                    }
                ))

        except Exception:
            pass

        return suggestions

    def _check_adverb_density(self, text: str) -> List[Suggestion]:
        """Check for overuse of -ly adverbs"""
        suggestions = []

        try:
            words = word_tokenize(text)
            if len(words) == 0:
                return suggestions

            adverbs = re.findall(self.adverb_pattern, text, re.IGNORECASE)
            # Filter out common acceptable ones
            acceptable = {'early', 'only', 'daily', 'weekly', 'monthly', 'yearly', 'friendly', 'lovely'}
            adverbs = [adv for adv in adverbs if adv.lower() not in acceptable]

            adverb_ratio = len(adverbs) / len(words)

            # More than 5% adverbs is excessive
            if adverb_ratio > 0.05:
                suggestions.append(Suggestion(
                    type=SuggestionType.STYLE,
                    severity=SeverityLevel.INFO,
                    message=f"High adverb density ({len(adverbs)} -ly words)",
                    suggestion="Too many adverbs can weaken prose. Consider replacing with stronger verbs or showing actions instead.",
                    metadata={
                        "adverb_count": len(adverbs),
                        "word_count": len(words),
                        "examples": adverbs[:5]  # Show first 5
                    }
                ))

        except Exception:
            pass

        return suggestions

    def _check_paragraph_length(self, text: str) -> List[Suggestion]:
        """Check for overly long paragraphs"""
        suggestions = []

        try:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

            for i, para in enumerate(paragraphs):
                word_count = len(word_tokenize(para))

                # Paragraphs longer than 200 words can be daunting
                if word_count > 200:
                    suggestions.append(Suggestion(
                        type=SuggestionType.STYLE,
                        severity=SeverityLevel.INFO,
                        message=f"Long paragraph ({word_count} words)",
                        suggestion="Consider breaking this paragraph into smaller chunks for better readability.",
                        metadata={
                            "paragraph_index": i,
                            "word_count": word_count
                        }
                    ))

        except Exception:
            pass

        return suggestions
