"""
Word Analyzer - Track word usage patterns
Detects weak words, repetition, clichés, and "telling" verbs
"""

import re
from typing import List, Dict
from collections import defaultdict
from nltk.tokenize import word_tokenize

from .types import Suggestion, SuggestionType, SeverityLevel


class WordAnalyzer:
    """Analyzes word usage patterns"""

    # Weak intensifiers that often add no value
    WEAK_WORDS = {
        "just", "really", "very", "quite", "rather",
        "actually", "basically", "literally", "simply",
        "fairly", "pretty", "somewhat", "slightly"
    }

    # Verbs that often indicate "telling" instead of "showing"
    TELLING_VERBS = {
        "felt", "thought", "knew", "realized",
        "wondered", "believed", "understood",
        "noticed", "saw", "heard", "seemed"
    }

    # Filter words that can make prose weaker
    FILTER_WORDS = {
        "started to", "began to", "tried to",
        "seemed to", "appeared to", "managed to"
    }

    # Common clichés (simple patterns)
    CLICHES = [
        r"\bbite the dust\b",
        r"\btime will tell\b",
        r"\bat the end of the day\b",
        r"\bthink outside the box\b",
        r"\blow-hanging fruit\b",
        r"\bpush the envelope\b",
        r"\bshe turned on her heel\b",
        r"\bhe let out a breath\b"
    ]

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze text for word usage issues

        Args:
            text: The text to analyze

        Returns:
            List of word usage suggestions
        """
        if not text or len(text.strip()) < 20:
            return []

        suggestions = []

        # Check for weak words
        suggestions.extend(self._check_weak_words(text))

        # Check for telling verbs
        suggestions.extend(self._check_telling_verbs(text))

        # Check for filter words
        suggestions.extend(self._check_filter_words(text))

        # Check for word repetition
        suggestions.extend(self._check_repetition(text))

        # Check for clichés
        suggestions.extend(self._check_cliches(text))

        return suggestions

    def _check_weak_words(self, text: str) -> List[Suggestion]:
        """Check for overused weak words"""
        suggestions = []

        try:
            words = word_tokenize(text.lower())
            word_counts = defaultdict(int)

            for word in words:
                if word in self.WEAK_WORDS:
                    word_counts[word] += 1

            # Flag if used more than 3 times
            for weak_word, count in word_counts.items():
                if count > 3:
                    suggestions.append(Suggestion(
                        type=SuggestionType.WORD_CHOICE,
                        severity=SeverityLevel.INFO,
                        message=f"'{weak_word}' used {count} times",
                        suggestion=f"'{weak_word}' often weakens prose. Consider removing or replacing for stronger writing.",
                        highlight_word=weak_word,
                        metadata={"count": count}
                    ))

        except Exception:
            pass

        return suggestions

    def _check_telling_verbs(self, text: str) -> List[Suggestion]:
        """Check for 'telling' instead of 'showing'"""
        suggestions = []

        try:
            # Look for telling verbs in context
            for verb in self.TELLING_VERBS:
                # Pattern: character + telling verb
                pattern = rf"\b(he|she|they|I)\s+{verb}\b"
                matches = list(re.finditer(pattern, text, re.IGNORECASE))

                if len(matches) > 2:  # More than 2 instances
                    suggestions.append(Suggestion(
                        type=SuggestionType.SHOW_NOT_TELL,
                        severity=SeverityLevel.INFO,
                        message=f"Potential telling: '{verb}' used {len(matches)} times",
                        suggestion="Consider showing the emotion or thought through action, dialogue, or physical description instead.",
                        highlight_word=verb,
                        metadata={"verb": verb, "count": len(matches)}
                    ))

        except Exception:
            pass

        return suggestions

    def _check_filter_words(self, text: str) -> List[Suggestion]:
        """Check for filter words that distance readers"""
        suggestions = []

        try:
            filter_count = 0
            found_filters = []

            for phrase in self.FILTER_WORDS:
                count = len(re.findall(rf"\b{phrase}\b", text, re.IGNORECASE))
                if count > 0:
                    filter_count += count
                    found_filters.append((phrase, count))

            if filter_count > 3:
                examples = ", ".join([f"'{phrase}' ({count}x)" for phrase, count in found_filters[:3]])
                suggestions.append(Suggestion(
                    type=SuggestionType.WORD_CHOICE,
                    severity=SeverityLevel.INFO,
                    message=f"Filter words found: {examples}",
                    suggestion="Filter words can distance readers from the action. Try removing them for more immediate prose.",
                    metadata={"filter_count": filter_count, "examples": found_filters}
                ))

        except Exception:
            pass

        return suggestions

    def _check_repetition(self, text: str) -> List[Suggestion]:
        """Check for repeated words in close proximity"""
        suggestions = []

        try:
            words = word_tokenize(text.lower())
            word_positions = defaultdict(list)

            # Track positions of words
            for i, word in enumerate(words):
                # Only track significant words (length > 3)
                if len(word) > 3 and word.isalpha():
                    word_positions[word].append(i)

            # Check for repetition within 20 words
            for word, positions in word_positions.items():
                if len(positions) < 2:
                    continue

                for i in range(len(positions) - 1):
                    distance = positions[i + 1] - positions[i]
                    if distance < 20:  # Within 20 words
                        suggestions.append(Suggestion(
                            type=SuggestionType.REPETITION,
                            severity=SeverityLevel.INFO,
                            message=f"'{word}' repeated within {distance} words",
                            suggestion="Consider using a synonym or rephrasing to avoid repetition.",
                            highlight_word=word,
                            metadata={"distance": distance}
                        ))
                        break  # Only report once per word

        except Exception:
            pass

        return suggestions

    def _check_cliches(self, text: str) -> List[Suggestion]:
        """Check for common clichés"""
        suggestions = []

        try:
            for cliche_pattern in self.CLICHES:
                matches = re.findall(cliche_pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        suggestions.append(Suggestion(
                            type=SuggestionType.WORD_CHOICE,
                            severity=SeverityLevel.INFO,
                            message=f"Cliché detected: '{match}'",
                            suggestion="Consider replacing this cliché with fresh, original phrasing.",
                            highlight_word=match
                        ))

        except Exception:
            pass

        return suggestions
