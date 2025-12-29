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
            first_passive_match = None

            for pattern in self.passive_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                passive_count += len(matches)
                if matches and first_passive_match is None:
                    first_passive_match = matches[0]

            passive_ratio = passive_count / len(sentences)

            # More than 30% passive voice is excessive
            if passive_ratio > 0.3:
                suggestion_data = {
                    "type": SuggestionType.VOICE,
                    "severity": SeverityLevel.WARNING,
                    "message": f"High passive voice usage ({passive_count} instances in {len(sentences)} sentences)",
                    "suggestion": "Consider using active voice for stronger, more direct prose. Active voice often creates more engaging scenes.",
                    "metadata": {
                        "passive_count": passive_count,
                        "sentence_count": len(sentences),
                        "passive_ratio": float(passive_ratio)
                    }
                }

                # Add position if we found a match
                if first_passive_match:
                    suggestion_data["start_char"] = first_passive_match.start()
                    suggestion_data["end_char"] = first_passive_match.end()
                    suggestion_data["highlight_word"] = first_passive_match.group()

                suggestions.append(Suggestion(**suggestion_data))

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

            # Find all adverb matches with positions
            acceptable = {'early', 'only', 'daily', 'weekly', 'monthly', 'yearly', 'friendly', 'lovely'}
            adverb_matches = [m for m in re.finditer(self.adverb_pattern, text, re.IGNORECASE)
                            if m.group().lower() not in acceptable]

            adverb_ratio = len(adverb_matches) / len(words)

            # More than 5% adverbs is excessive
            if adverb_ratio > 0.05:
                # Use first adverb match for position
                first_match = adverb_matches[0] if adverb_matches else None

                suggestion_data = {
                    "type": SuggestionType.STYLE,
                    "severity": SeverityLevel.INFO,
                    "message": f"High adverb density ({len(adverb_matches)} -ly words)",
                    "suggestion": "Too many adverbs can weaken prose. Consider replacing with stronger verbs or showing actions instead.",
                    "metadata": {
                        "adverb_count": len(adverb_matches),
                        "word_count": len(words),
                        "examples": [m.group() for m in adverb_matches[:5]]  # Show first 5
                    }
                }

                if first_match:
                    suggestion_data["start_char"] = first_match.start()
                    suggestion_data["end_char"] = first_match.end()
                    suggestion_data["highlight_word"] = first_match.group()

                suggestions.append(Suggestion(**suggestion_data))

        except Exception:
            pass

        return suggestions

    def _check_paragraph_length(self, text: str) -> List[Suggestion]:
        """Check for overly long paragraphs"""
        suggestions = []

        try:
            # Split by newlines but track positions
            current_pos = 0
            for para_raw in text.split('\n'):
                para = para_raw.strip()

                if para:  # Skip empty paragraphs
                    word_count = len(word_tokenize(para))

                    # Paragraphs longer than 200 words can be daunting
                    if word_count > 200:
                        # Find the actual start position of this paragraph in the original text
                        # Search for the paragraph starting from current_pos
                        para_start = text.find(para, current_pos)
                        para_end = para_start + len(para) if para_start != -1 else current_pos + len(para_raw)

                        suggestion_data = {
                            "type": SuggestionType.STYLE,
                            "severity": SeverityLevel.INFO,
                            "message": f"Long paragraph ({word_count} words)",
                            "suggestion": "Consider breaking this paragraph into smaller chunks for better readability.",
                            "metadata": {
                                "word_count": word_count
                            }
                        }

                        # Add position if found
                        if para_start != -1:
                            # Highlight just the first ~100 chars for context
                            highlight_end = min(para_start + 100, para_end)
                            suggestion_data["start_char"] = para_start
                            suggestion_data["end_char"] = highlight_end

                        suggestions.append(Suggestion(**suggestion_data))

                # Move position forward (include newline)
                current_pos += len(para_raw) + 1

        except Exception:
            pass

        return suggestions
