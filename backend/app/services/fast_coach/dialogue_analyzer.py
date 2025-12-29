"""
Dialogue Analyzer for Fast Coach
Detects dialogue issues: tags, attribution, crutches, punctuation
"""

import re
from typing import List
from .types import Suggestion, SuggestionType, SeverityLevel


class DialogueAnalyzer:
    """Analyzes dialogue for common issues in fiction writing"""

    # Dialogue tag verbs (common attribution)
    DIALOGUE_TAGS = {
        'said', 'asked', 'replied', 'answered', 'whispered', 'shouted',
        'yelled', 'screamed', 'muttered', 'murmured', 'stated', 'exclaimed',
        'demanded', 'questioned', 'added', 'continued', 'responded', 'nodded',
        'agreed', 'disagreed', 'laughed', 'cried', 'sighed', 'gasped',
    }

    # Dialogue crutches - words that weaken dialogue
    DIALOGUE_CRUTCHES = {
        'um', 'uh', 'er', 'ah', 'hmm', 'hm', 'well', 'like', 'you know',
        'i mean', 'kind of', 'sort of', 'just', 'actually', 'basically',
        'literally', 'honestly', 'obviously', 'totally', 'really',
    }

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze text for dialogue issues

        Args:
            text: The text to analyze

        Returns:
            List of dialogue-related suggestions
        """
        suggestions = []

        # Extract dialogue from text
        dialogue_info = self._extract_dialogue(text)

        if not dialogue_info['lines']:
            # No dialogue found
            return suggestions

        # Check for various dialogue issues
        suggestions.extend(self._check_dialogue_tags(text, dialogue_info))
        suggestions.extend(self._check_unattributed_dialogue(dialogue_info))
        suggestions.extend(self._check_dialogue_crutches(dialogue_info))
        suggestions.extend(self._check_exclamation_overuse(dialogue_info))
        suggestions.extend(self._check_ellipsis_overuse(dialogue_info))
        suggestions.extend(self._check_dialogue_ratio(text, dialogue_info))

        return suggestions

    def _extract_dialogue(self, text: str) -> dict:
        """
        Extract dialogue lines from text

        Returns dict with:
        - lines: list of dialogue strings
        - positions: list of (start, end) tuples
        - total_length: total character count of dialogue
        """
        dialogue_lines = []
        dialogue_positions = []
        total_dialogue_chars = 0

        # Match dialogue in quotes (both single and double)
        # Pattern: Opening quote, content, closing quote
        dialogue_pattern = r'["""\'](.*?)["""\']'

        for match in re.finditer(dialogue_pattern, text, re.DOTALL):
            dialogue_text = match.group(1)
            # Skip very short matches (likely not dialogue)
            if len(dialogue_text) > 2:
                dialogue_lines.append(dialogue_text)
                dialogue_positions.append((match.start(), match.end()))
                total_dialogue_chars += len(dialogue_text)

        return {
            'lines': dialogue_lines,
            'positions': dialogue_positions,
            'total_length': total_dialogue_chars
        }

    def _check_dialogue_tags(self, text: str, dialogue_info: dict) -> List[Suggestion]:
        """Check for overused or misused dialogue tags"""
        suggestions = []

        # Count "said" usage
        said_count = len(re.findall(r'\bsaid\b', text, re.IGNORECASE))
        if said_count > 10:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE,
                severity=SeverityLevel.INFO,
                message=f"'Said' used {said_count} times",
                suggestion="While 'said' is generally fine, consider varying dialogue attribution or using action beats instead of tags in some cases.",
                metadata={'said_count': said_count}
            ))

        # Check for fancy dialogue tags
        fancy_tags = ['exclaimed', 'proclaimed', 'ejaculated', 'interjected', 'opined']
        for tag in fancy_tags:
            matches = list(re.finditer(rf'\b{tag}\b', text, re.IGNORECASE))
            if matches:
                first_match = matches[0]
                suggestions.append(Suggestion(
                    type=SuggestionType.DIALOGUE,
                    severity=SeverityLevel.INFO,
                    message=f"Fancy dialogue tag: '{tag}'",
                    suggestion="Consider using 'said' or action beats instead of fancy dialogue tags. They can draw attention away from the dialogue itself.",
                    highlight_word=first_match.group(),
                    start_char=first_match.start(),
                    end_char=first_match.end()
                ))

        # Check for adverb + tag combinations (e.g., "said angrily")
        adverb_tag_pattern = r'\b(said|asked|replied)\s+(quickly|slowly|angrily|sadly|happily|quietly|loudly|nervously|carefully|eagerly)\b'
        matches = list(re.finditer(adverb_tag_pattern, text, re.IGNORECASE))
        if matches:
            first_match = matches[0]
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE,
                severity=SeverityLevel.WARNING,
                message=f"Dialogue tag with adverb: '{first_match.group()}'",
                suggestion="Avoid adverbs with dialogue tags. Show emotion through the dialogue itself or action beats instead of telling (e.g., 'said angrily').",
                highlight_word=first_match.group(),
                start_char=first_match.start(),
                end_char=first_match.end(),
                metadata={'total_count': len(matches)}
            ))

        return suggestions

    def _check_unattributed_dialogue(self, dialogue_info: dict) -> List[Suggestion]:
        """
        Check for potentially confusing unattributed dialogue
        (Multiple consecutive dialogue lines without attribution)
        """
        suggestions = []

        lines = dialogue_info['lines']
        if len(lines) >= 3:
            # If there are 3+ dialogue lines, warn about potential confusion
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE,
                severity=SeverityLevel.INFO,
                message=f"{len(lines)} dialogue lines detected",
                suggestion="With multiple dialogue exchanges, ensure readers can easily track who's speaking. Consider adding occasional dialogue tags or action beats for clarity.",
                metadata={'dialogue_count': len(lines)}
            ))

        return suggestions

    def _check_dialogue_crutches(self, dialogue_info: dict) -> List[Suggestion]:
        """Check for overuse of dialogue crutch words"""
        suggestions = []

        all_dialogue = ' '.join(dialogue_info['lines']).lower()

        for crutch in self.DIALOGUE_CRUTCHES:
            # Count occurrences
            count = len(re.findall(rf'\b{re.escape(crutch)}\b', all_dialogue))

            if count > 2:  # More than 2 uses
                suggestions.append(Suggestion(
                    type=SuggestionType.DIALOGUE,
                    severity=SeverityLevel.INFO,
                    message=f"Dialogue crutch '{crutch}' used {count} times",
                    suggestion=f"'{crutch}' is a common dialogue crutch. While occasional use can add realism, overuse weakens dialogue. Consider if each instance is necessary.",
                    highlight_word=crutch,
                    metadata={'crutch': crutch, 'count': count}
                ))

        return suggestions

    def _check_exclamation_overuse(self, dialogue_info: dict) -> List[Suggestion]:
        """Check for excessive exclamation marks in dialogue"""
        suggestions = []

        all_dialogue = ' '.join(dialogue_info['lines'])
        exclamation_count = all_dialogue.count('!')

        if exclamation_count > 3:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE,
                severity=SeverityLevel.WARNING,
                message=f"{exclamation_count} exclamation marks in dialogue",
                suggestion="Too many exclamation marks can feel melodramatic and reduce their impact. Reserve them for moments of genuine surprise or strong emotion.",
                metadata={'count': exclamation_count}
            ))

        return suggestions

    def _check_ellipsis_overuse(self, dialogue_info: dict) -> List[Suggestion]:
        """Check for excessive ellipsis (...) in dialogue"""
        suggestions = []

        all_dialogue = ' '.join(dialogue_info['lines'])
        # Count both ... and … (unicode ellipsis)
        ellipsis_count = all_dialogue.count('...') + all_dialogue.count('…')

        if ellipsis_count > 3:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE,
                severity=SeverityLevel.INFO,
                message=f"{ellipsis_count} ellipses in dialogue",
                suggestion="Frequent ellipses can make dialogue feel tentative or slow-paced. Use them sparingly for trailing off or hesitation.",
                metadata={'count': ellipsis_count}
            ))

        return suggestions

    def _check_dialogue_ratio(self, text: str, dialogue_info: dict) -> List[Suggestion]:
        """Check dialogue-to-narrative ratio"""
        suggestions = []

        total_text_length = len(text)
        dialogue_length = dialogue_info['total_length']

        if total_text_length == 0:
            return suggestions

        dialogue_ratio = dialogue_length / total_text_length

        if dialogue_ratio > 0.7:  # More than 70% dialogue
            suggestions.append(Suggestion(
                type=SuggestionType.PACING,
                severity=SeverityLevel.INFO,
                message=f"High dialogue ratio ({dialogue_ratio:.0%})",
                suggestion="Over 70% of this text is dialogue. Consider adding more action beats, internal thoughts, or description to balance the scene and ground readers in the setting.",
                metadata={'dialogue_ratio': dialogue_ratio, 'dialogue_percent': int(dialogue_ratio * 100)}
            ))
        elif dialogue_ratio < 0.1 and dialogue_length > 0:  # Less than 10% dialogue
            suggestions.append(Suggestion(
                type=SuggestionType.PACING,
                severity=SeverityLevel.INFO,
                message=f"Low dialogue ratio ({dialogue_ratio:.0%})",
                suggestion="Less than 10% dialogue. Dialogue can help bring scenes to life and reveal character. Consider if your characters could speak more.",
                metadata={'dialogue_ratio': dialogue_ratio, 'dialogue_percent': int(dialogue_ratio * 100)}
            ))

        return suggestions
