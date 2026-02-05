"""
Sentence Starter Variety Analyzer for Fast Coach.

Detects repetitive sentence openings that can make prose feel monotonous.
Analyzes patterns like:
- Consecutive sentences starting with the same word
- Over-reliance on pronoun starters (He, She, I, They)
- Too many "The" starters
"""

import re
from typing import List, Tuple, Dict, Set
from collections import Counter
from .types import Suggestion, SuggestionType, SeverityLevel


class SentenceStarterAnalyzer:
    """
    Detects repetitive sentence starters and suggests variety.

    Repetitive sentence openings create a monotonous rhythm that can
    fatigue readers. This analyzer identifies patterns and provides
    specific suggestions for improvement.
    """

    # Pronoun starters (first-person and third-person)
    PRONOUN_STARTERS: Set[str] = {
        'he', 'she', 'they', 'i', 'we', 'it', 'you',
        'his', 'her', 'their', 'my', 'our', 'your'
    }

    # Article starters
    ARTICLE_STARTERS: Set[str] = {'the', 'a', 'an'}

    # Common weak starters
    WEAK_STARTERS: Set[str] = {
        'there', 'this', 'that', 'these', 'those',
        'here', 'it', 'what', 'which'
    }

    # Alternatives to suggest
    STARTER_ALTERNATIVES = [
        "an action or movement",
        "a sensory detail (sight, sound, smell)",
        "dialogue",
        "a prepositional phrase (In the distance..., Beyond the wall...)",
        "a dependent clause (When she arrived..., Although tired...)",
        "a participial phrase (-ing opener: Running quickly..., Sighing deeply...)",
        "an adverb (Slowly, Suddenly, Carefully)",
    ]

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze sentence starters for repetition patterns.

        Args:
            text: Text to analyze

        Returns:
            List of suggestions about sentence variety
        """
        if not text or len(text.strip()) < 100:
            return []

        suggestions = []

        # Extract sentence starters with positions
        starters = self._extract_sentence_starters(text)

        if len(starters) < 5:
            return []

        # Check for consecutive repetition (3+ in a row)
        consecutive_issues = self._find_consecutive_repetition(starters, text)
        suggestions.extend(consecutive_issues)

        # Check for overall distribution problems
        distribution_issues = self._check_distribution(starters, text)
        suggestions.extend(distribution_issues)

        # Check for weak starter overuse
        weak_starter_issues = self._check_weak_starters(starters, text)
        suggestions.extend(weak_starter_issues)

        return suggestions

    def _extract_sentence_starters(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract the first word of each sentence with positions.

        Returns:
            List of (first_word, start_position, end_position)
        """
        starters = []

        # Split into sentences (accounting for dialogue and abbreviations)
        # This regex finds sentence boundaries
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z"\'])|(?<=["\']\s)(?=[A-Z])'

        # Find all sentence starts
        sentences = re.split(sentence_pattern, text)
        position = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Find the first word (skip quotes and whitespace)
            match = re.match(r'^["\'\s]*([A-Za-z]+)', sentence)
            if match:
                first_word = match.group(1).lower()
                word_start = text.find(match.group(1), position)
                word_end = word_start + len(match.group(1)) if word_start >= 0 else position

                starters.append((first_word, word_start, word_end))

            position += len(sentence) + 1

        return starters

    def _find_consecutive_repetition(
        self,
        starters: List[Tuple[str, int, int]],
        text: str
    ) -> List[Suggestion]:
        """Find 3+ consecutive sentences starting with the same word."""
        suggestions = []
        words = [s[0] for s in starters]

        i = 0
        while i < len(words) - 2:
            word = words[i]
            count = 1

            # Count consecutive same starters
            j = i + 1
            while j < len(words) and words[j] == word:
                count += 1
                j += 1

            if count >= 3:
                start_pos = starters[i][1]
                end_pos = starters[j - 1][2]

                # Choose severity based on count
                severity = SeverityLevel.WARNING if count >= 4 else SeverityLevel.INFO

                # Generate specific suggestion
                alt_suggestion = self._get_alternative_suggestion(word)

                suggestions.append(Suggestion(
                    type=SuggestionType.SENTENCE_VARIETY,
                    severity=severity,
                    message=f"{count} consecutive sentences start with '{word.capitalize()}'",
                    suggestion=alt_suggestion,
                    start_char=start_pos,
                    end_char=end_pos,
                    highlight_word=word,
                    metadata={
                        "repeated_word": word,
                        "consecutive_count": count,
                        "pattern_type": "consecutive",
                        "teaching_point": (
                            "Repetitive sentence starters create a predictable rhythm "
                            "that can make prose feel mechanical. Varying your openings "
                            "keeps readers engaged and creates a more natural flow. "
                            "Try starting with action, dialogue, or descriptive phrases."
                        )
                    }
                ))
                i = j
            else:
                i += 1

        return suggestions

    def _check_distribution(
        self,
        starters: List[Tuple[str, int, int]],
        text: str
    ) -> List[Suggestion]:
        """Check overall distribution of starter types."""
        suggestions = []
        words = [s[0] for s in starters]
        total = len(words)

        if total < 10:
            return []

        # Count categories
        pronoun_count = sum(1 for w in words if w in self.PRONOUN_STARTERS)
        article_count = sum(1 for w in words if w in self.ARTICLE_STARTERS)
        the_count = sum(1 for w in words if w == 'the')

        # Check pronoun overuse (>40%)
        pronoun_pct = 100 * pronoun_count / total
        if pronoun_pct > 40:
            suggestions.append(Suggestion(
                type=SuggestionType.SENTENCE_VARIETY,
                severity=SeverityLevel.INFO,
                message=f"{pronoun_pct:.0f}% of sentences start with pronouns",
                suggestion=(
                    f"About {pronoun_count} of {total} sentences begin with pronouns "
                    f"(he, she, they, I). Try varying with action beats, "
                    f"dialogue, or descriptive phrases to create rhythm."
                ),
                metadata={
                    "pronoun_percentage": round(pronoun_pct, 1),
                    "pronoun_count": pronoun_count,
                    "total_sentences": total,
                    "pattern_type": "pronoun_overuse",
                    "teaching_point": (
                        "Pronoun-heavy openings often indicate a 'subject-verb' "
                        "sentence pattern. While grammatically correct, this pattern "
                        "can feel repetitive. Professional authors typically keep "
                        "pronoun starters under 35% of sentences."
                    )
                }
            ))

        # Check "The" overuse (>25%)
        the_pct = 100 * the_count / total
        if the_pct > 25:
            suggestions.append(Suggestion(
                type=SuggestionType.SENTENCE_VARIETY,
                severity=SeverityLevel.INFO,
                message=f"{the_pct:.0f}% of sentences start with 'The'",
                suggestion=(
                    f"Starting {the_count} of {total} sentences with 'The' creates "
                    f"a list-like feeling. Try leading with the subject's action "
                    f"or introducing variety through other openings."
                ),
                metadata={
                    "the_percentage": round(the_pct, 1),
                    "the_count": the_count,
                    "total_sentences": total,
                    "pattern_type": "the_overuse",
                    "teaching_point": (
                        "'The' starters often indicate declarative, tell-style prose. "
                        "While sometimes necessary, overuse can make writing feel "
                        "like a catalog of observations rather than an immersive "
                        "narrative. Show the reader through action and sensation."
                    )
                }
            ))

        return suggestions

    def _check_weak_starters(
        self,
        starters: List[Tuple[str, int, int]],
        text: str
    ) -> List[Suggestion]:
        """Check for overuse of weak starters like 'There was', 'It was'."""
        suggestions = []
        words = [s[0] for s in starters]
        total = len(words)

        if total < 10:
            return []

        # Count "there" and "it" starters
        there_count = sum(1 for w in words if w == 'there')
        it_count = sum(1 for w in words if w == 'it')

        # Check "There was/were" overuse
        if there_count >= 3 and (100 * there_count / total) > 10:
            suggestions.append(Suggestion(
                type=SuggestionType.SENTENCE_VARIETY,
                severity=SeverityLevel.INFO,
                message=f"'There' starts {there_count} sentences",
                suggestion=(
                    "'There was/were' constructions delay the real subject. "
                    "Instead of 'There was a man standing by the door,' "
                    "try 'A man stood by the door' for more immediate prose."
                ),
                metadata={
                    "there_count": there_count,
                    "pattern_type": "there_overuse",
                    "teaching_point": (
                        "Expletive constructions ('There was', 'It was') add words "
                        "without adding meaning. They distance readers from the action. "
                        "Strong prose puts the true subject first."
                    )
                }
            ))

        return suggestions

    def _get_alternative_suggestion(self, repeated_word: str) -> str:
        """Generate specific alternatives based on the repeated word."""
        word_lower = repeated_word.lower()

        if word_lower in self.PRONOUN_STARTERS:
            return (
                f"Vary from '{repeated_word.capitalize()}' starters by trying: "
                f"action beats ('Running a hand through her hair, she...'), "
                f"dialogue, or descriptive openings ('The cold wind made her...')."
            )
        elif word_lower == 'the':
            return (
                "Instead of 'The [noun]...', try starting with: "
                "the character's action, a sensory detail, "
                "or a dependent clause ('When the door opened...')."
            )
        elif word_lower in self.WEAK_STARTERS:
            return (
                f"'{repeated_word.capitalize()}' is a weak opener. "
                "Try starting with the true subject and its action, "
                "or use a more specific, concrete detail."
            )
        else:
            return (
                f"Vary from repeated '{repeated_word}' starters. "
                "Consider: action, dialogue, sensory details, "
                "prepositional phrases, or dependent clauses."
            )


# Singleton instance
sentence_starter_analyzer = SentenceStarterAnalyzer()
