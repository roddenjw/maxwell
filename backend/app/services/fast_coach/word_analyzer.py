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
            # Track positions of each weak word
            word_positions = defaultdict(list)

            for weak_word in self.WEAK_WORDS:
                # Case-insensitive word boundary search
                pattern = rf'\b{weak_word}\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    word_positions[weak_word.lower()].append({
                        'start': match.start(),
                        'end': match.end(),
                        'text': match.group()
                    })

            # Flag if used more than 3 times
            for weak_word, positions in word_positions.items():
                count = len(positions)
                if count > 3:
                    # Create one suggestion with first occurrence position
                    first_pos = positions[0]

                    # Extract the text around the weak word to create a replacement
                    highlighted_text = first_pos['text']
                    # Replacement is empty string (removes the word)
                    replacement_text = ""

                    suggestions.append(Suggestion(
                        type=SuggestionType.WORD_CHOICE,
                        severity=SeverityLevel.INFO,
                        message=f"'{weak_word}' used {count} times",
                        suggestion=f"'{weak_word}' often weakens prose. Consider removing or replacing for stronger writing.",
                        highlight_word=weak_word,
                        start_char=first_pos['start'],
                        end_char=first_pos['end'],
                        replacement=replacement_text,
                        metadata={"count": count, "all_positions": positions}
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
                    # Use first match for position
                    first_match = matches[0]
                    all_positions = [{'start': m.start(), 'end': m.end(), 'text': m.group()} for m in matches]

                    # Generate replacement suggestions based on the verb
                    replacement_suggestions = {
                        'felt': '[Show the emotion through actions or physical sensations]',
                        'thought': '[Show through internal dialogue or action]',
                        'knew': '[Show through evidence or realization]',
                        'realized': '[Show the moment of discovery]',
                        'wondered': '[Show through questioning dialogue or behavior]',
                        'believed': '[Show through actions that demonstrate belief]',
                        'understood': '[Show through changed behavior or expression]',
                        'noticed': '[Describe what was seen directly]',
                        'saw': '[Describe what is visible]',
                        'heard': '[Describe the sound directly]',
                        'seemed': '[Describe the appearance directly]'
                    }

                    replacement_hint = replacement_suggestions.get(verb, '[Show, don\'t tell]')

                    suggestions.append(Suggestion(
                        type=SuggestionType.SHOW_NOT_TELL,
                        severity=SeverityLevel.INFO,
                        message=f"Potential telling: '{verb}' used {len(matches)} times",
                        suggestion="Consider showing the emotion or thought through action, dialogue, or physical description instead.",
                        highlight_word=verb,
                        start_char=first_match.start(),
                        end_char=first_match.end(),
                        replacement=replacement_hint,
                        metadata={"verb": verb, "count": len(matches), "all_positions": all_positions}
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

        # Common words to exclude from repetition checks (even if long)
        EXCLUDE_WORDS = {
            'said', 'asked', 'that', 'this', 'then', 'when', 'with',
            'were', 'have', 'been', 'their', 'there', 'would', 'could',
            'should', 'about', 'which', 'where', 'these', 'those', 'from',
            'some', 'into', 'than', 'them', 'other', 'after', 'before',
            'through', 'over', 'under', 'between', 'during', 'until',
            'looked', 'turned', 'walked', 'came', 'went', 'took', 'made'
        }

        try:
            words = word_tokenize(text.lower())
            word_positions = defaultdict(list)

            # Track positions of words (tokenized index)
            for i, word in enumerate(words):
                # Only track significant words (length > 5, exclude common words)
                if len(word) > 5 and word.isalpha() and word not in EXCLUDE_WORDS:
                    word_positions[word].append(i)

            # Check for repetition within 12 words
            for word, positions in word_positions.items():
                # Need at least 3 occurrences for it to be significant
                if len(positions) < 3:
                    continue

                # Find the closest repetition
                min_distance = float('inf')
                for i in range(len(positions) - 1):
                    distance = positions[i + 1] - positions[i]
                    if distance < min_distance:
                        min_distance = distance

                # Only flag if repeated within 12 words
                if min_distance < 12:
                    # Find actual character positions of first occurrence in original text
                    pattern = rf'\b{re.escape(word)}\b'
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))

                    suggestion_data = {
                        "type": SuggestionType.REPETITION,
                        "severity": SeverityLevel.INFO,
                        "message": f"'{word}' repeated {len(positions)} times (closest: {min_distance} words apart)",
                        "suggestion": "Consider using a synonym or rephrasing to avoid repetition.",
                        "highlight_word": word,
                        "metadata": {
                            "distance": min_distance,
                            "occurrences": len(positions)
                        }
                    }

                    # Add position of first match if found
                    if matches:
                        first_match = matches[0]
                        suggestion_data["start_char"] = first_match.start()
                        suggestion_data["end_char"] = first_match.end()

                    suggestions.append(Suggestion(**suggestion_data))

        except Exception:
            pass

        return suggestions

    def _check_cliches(self, text: str) -> List[Suggestion]:
        """Check for common clichés"""
        suggestions = []

        try:
            for cliche_pattern in self.CLICHES:
                for match in re.finditer(cliche_pattern, text, re.IGNORECASE):
                    suggestions.append(Suggestion(
                        type=SuggestionType.WORD_CHOICE,
                        severity=SeverityLevel.INFO,
                        message=f"Cliché detected: '{match.group()}'",
                        suggestion="Consider replacing this cliché with fresh, original phrasing.",
                        highlight_word=match.group(),
                        start_char=match.start(),
                        end_char=match.end()
                    ))

        except Exception:
            pass

        return suggestions
