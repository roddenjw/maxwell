"""
Readability Analyzer for Fast Coach.

Calculates readability metrics (Flesch-Kincaid, Gunning Fog, etc.)
and provides suggestions based on target genre/audience.
"""

import re
import math
from typing import List, Dict, Optional, Tuple
from .types import Suggestion, SuggestionType, SeverityLevel


class ReadabilityAnalyzer:
    """
    Analyzes text readability using multiple established metrics.

    Metrics calculated:
    - Flesch-Kincaid Grade Level
    - Flesch Reading Ease
    - Gunning Fog Index
    - Coleman-Liau Index
    - Automated Readability Index (ARI)
    """

    # Genre-specific target grade levels (min, max, ideal)
    GENRE_TARGETS: Dict[str, Tuple[int, int, int]] = {
        "young_adult": (5, 8, 6),
        "middle_grade": (4, 6, 5),
        "adult_fiction": (7, 11, 8),
        "literary_fiction": (9, 14, 11),
        "thriller": (5, 9, 7),
        "romance": (5, 8, 6),
        "fantasy": (7, 12, 9),
        "sci_fi": (8, 13, 10),
        "horror": (6, 10, 8),
        "mystery": (6, 10, 8),
        "historical": (8, 12, 10),
    }

    # Reading ease interpretations
    EASE_LEVELS = [
        (90, 100, "Very Easy", "5th grade"),
        (80, 89, "Easy", "6th grade"),
        (70, 79, "Fairly Easy", "7th grade"),
        (60, 69, "Standard", "8th-9th grade"),
        (50, 59, "Fairly Difficult", "10th-12th grade"),
        (30, 49, "Difficult", "College"),
        (0, 29, "Very Difficult", "College graduate"),
    ]

    def analyze(
        self,
        text: str,
        genre: str = "adult_fiction",
        include_details: bool = True
    ) -> List[Suggestion]:
        """
        Analyze text readability and return suggestions.

        Args:
            text: Text to analyze
            genre: Target genre for appropriate difficulty
            include_details: Whether to include detailed metrics

        Returns:
            List of suggestions about readability
        """
        if not text or len(text.strip()) < 100:
            return []

        suggestions = []

        # Calculate all metrics
        metrics = self.calculate_metrics(text)

        if not metrics:
            return []

        # Get target range for genre
        target_min, target_max, target_ideal = self.GENRE_TARGETS.get(
            genre, self.GENRE_TARGETS["adult_fiction"]
        )

        # Average grade level across metrics
        avg_grade = metrics["average_grade"]

        # Determine if readability is appropriate
        if avg_grade > target_max + 2:
            # Text is too complex
            severity = SeverityLevel.WARNING if avg_grade > target_max + 4 else SeverityLevel.INFO
            suggestions.append(Suggestion(
                type=SuggestionType.READABILITY,
                severity=severity,
                message=f"Reading level ({avg_grade:.1f}) is above target for {genre.replace('_', ' ')} ({target_min}-{target_max})",
                suggestion=self._get_simplify_suggestion(metrics),
                metadata={
                    "metrics": metrics,
                    "genre": genre,
                    "target_min": target_min,
                    "target_max": target_max,
                    "direction": "simplify",
                    "teaching_point": (
                        "Complex prose can fatigue readers and slow pacing. "
                        "For broader accessibility, consider shorter sentences "
                        "and more common vocabulary. Literary fiction can support "
                        "higher complexity, but genre fiction typically benefits "
                        "from cleaner prose."
                    )
                }
            ))
        elif avg_grade < target_min - 2:
            # Text is too simple
            suggestions.append(Suggestion(
                type=SuggestionType.READABILITY,
                severity=SeverityLevel.INFO,
                message=f"Reading level ({avg_grade:.1f}) is below target for {genre.replace('_', ' ')} ({target_min}-{target_max})",
                suggestion=self._get_enrich_suggestion(metrics),
                metadata={
                    "metrics": metrics,
                    "genre": genre,
                    "target_min": target_min,
                    "target_max": target_max,
                    "direction": "enrich",
                    "teaching_point": (
                        "Simple prose is often good, but readers of "
                        f"{genre.replace('_', ' ')} may expect more sophisticated "
                        "vocabulary and sentence structures. Consider varying "
                        "sentence length and adding descriptive depth."
                    )
                }
            ))
        else:
            # On target - provide informational summary
            if include_details:
                ease_desc = self._get_ease_description(metrics["flesch_reading_ease"])
                suggestions.append(Suggestion(
                    type=SuggestionType.READABILITY,
                    severity=SeverityLevel.INFO,
                    message=f"Readability: {ease_desc} (Grade {avg_grade:.1f})",
                    suggestion=f"Your prose complexity matches {genre.replace('_', ' ')} expectations well.",
                    metadata={
                        "metrics": metrics,
                        "genre": genre,
                        "on_target": True,
                        "teaching_point": (
                            "Readability scores are guidelines, not rules. "
                            "What matters most is that your prose serves your story. "
                            "Complex passages may be appropriate for introspective moments, "
                            "while simpler prose can heighten action scenes."
                        )
                    }
                ))

        return suggestions

    def calculate_metrics(self, text: str) -> Optional[Dict[str, float]]:
        """
        Calculate all readability metrics for the text.

        Returns dict with:
        - flesch_kincaid_grade
        - flesch_reading_ease
        - gunning_fog
        - coleman_liau
        - ari (Automated Readability Index)
        - average_grade
        - sentence_count
        - word_count
        - avg_words_per_sentence
        - avg_syllables_per_word
        """
        # Count basic elements
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)
        characters = len(re.findall(r'[a-zA-Z]', text))
        complex_words = self._count_complex_words(text)

        if sentences == 0 or words == 0:
            return None

        # Calculate derived values
        words_per_sentence = words / sentences
        syllables_per_word = syllables / words
        chars_per_word = characters / words

        # Flesch-Kincaid Grade Level
        fk_grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59

        # Flesch Reading Ease (0-100, higher = easier)
        fk_ease = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        fk_ease = max(0, min(100, fk_ease))  # Clamp to 0-100

        # Gunning Fog Index
        fog = 0.4 * (words_per_sentence + 100 * (complex_words / words))

        # Coleman-Liau Index
        L = (characters / words) * 100  # Letters per 100 words
        S = (sentences / words) * 100   # Sentences per 100 words
        coleman_liau = (0.0588 * L) - (0.296 * S) - 15.8

        # Automated Readability Index
        ari = (4.71 * chars_per_word) + (0.5 * words_per_sentence) - 21.43

        # Average grade across metrics (excluding reading ease which is inverted)
        grade_metrics = [fk_grade, fog, coleman_liau, ari]
        # Filter out extreme values
        valid_grades = [g for g in grade_metrics if 0 <= g <= 20]
        avg_grade = sum(valid_grades) / len(valid_grades) if valid_grades else fk_grade

        return {
            "flesch_kincaid_grade": round(fk_grade, 1),
            "flesch_reading_ease": round(fk_ease, 1),
            "gunning_fog": round(fog, 1),
            "coleman_liau": round(coleman_liau, 1),
            "ari": round(ari, 1),
            "average_grade": round(avg_grade, 1),
            "sentence_count": sentences,
            "word_count": words,
            "avg_words_per_sentence": round(words_per_sentence, 1),
            "avg_syllables_per_word": round(syllables_per_word, 2),
            "complex_word_percentage": round(100 * complex_words / words, 1),
        }

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Match sentence-ending punctuation
        # Account for abbreviations, ellipses, etc.
        sentences = re.split(r'[.!?]+(?:\s|$)', text)
        return len([s for s in sentences if s.strip()])

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        words = re.findall(r'\b[a-zA-Z\']+\b', text)
        return len(words)

    def _count_syllables(self, text: str) -> int:
        """Count total syllables in text."""
        words = re.findall(r'\b[a-zA-Z\']+\b', text.lower())
        return sum(self._syllables_in_word(word) for word in words)

    def _syllables_in_word(self, word: str) -> int:
        """
        Count syllables in a single word.
        Uses vowel-counting heuristic with adjustments.
        """
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1

        # Adjust for -le endings (e.g., "table")
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1

        # Adjust for -ed endings that don't add syllable
        if word.endswith('ed') and count > 1:
            if len(word) > 3 and word[-3] not in 'dt':
                count -= 1

        return max(1, count)

    def _count_complex_words(self, text: str) -> int:
        """
        Count complex words (3+ syllables, excluding common suffixes).
        Used for Gunning Fog calculation.
        """
        words = re.findall(r'\b[a-zA-Z\']+\b', text.lower())
        count = 0

        # Common suffixes that don't really add complexity
        simple_suffixes = ('ing', 'ed', 'es', 'ly', 'er', 'est')

        for word in words:
            syllables = self._syllables_in_word(word)
            if syllables >= 3:
                # Check if complexity is from simple suffix
                is_simple = False
                for suffix in simple_suffixes:
                    if word.endswith(suffix):
                        base = word[:-len(suffix)]
                        if self._syllables_in_word(base) < 3:
                            is_simple = True
                            break

                if not is_simple:
                    count += 1

        return count

    def _get_ease_description(self, ease_score: float) -> str:
        """Get description for Flesch Reading Ease score."""
        for low, high, desc, grade in self.EASE_LEVELS:
            if low <= ease_score <= high:
                return f"{desc} ({grade})"
        return "Standard"

    def _get_simplify_suggestion(self, metrics: Dict[str, float]) -> str:
        """Generate suggestion for simplifying text."""
        suggestions = []

        if metrics["avg_words_per_sentence"] > 20:
            suggestions.append("break long sentences into shorter ones")

        if metrics["avg_syllables_per_word"] > 1.6:
            suggestions.append("use simpler words where possible")

        if metrics["complex_word_percentage"] > 15:
            suggestions.append("reduce complex vocabulary")

        if not suggestions:
            suggestions.append("consider varying sentence length for better flow")

        return "To improve accessibility: " + ", ".join(suggestions) + "."

    def _get_enrich_suggestion(self, metrics: Dict[str, float]) -> str:
        """Generate suggestion for enriching text."""
        suggestions = []

        if metrics["avg_words_per_sentence"] < 12:
            suggestions.append("vary sentence length with some longer, more complex sentences")

        if metrics["avg_syllables_per_word"] < 1.3:
            suggestions.append("incorporate more varied vocabulary")

        if not suggestions:
            suggestions.append("add descriptive depth and sentence variety")

        return "To add sophistication: " + ", ".join(suggestions) + "."


# Singleton instance
readability_analyzer = ReadabilityAnalyzer()
