"""
Dialogue Analyzer for Fast Coach.

Detects dialogue issues including:
- Said-ism analysis (balance of 'said' vs alternative tags vs action beats)
- Dialogue tags overuse/underuse
- Attribution problems
- Dialogue crutches
- Punctuation issues
"""

import re
from typing import List, Dict, Tuple, Set
from .types import Suggestion, SuggestionType, SeverityLevel


class DialogueAnalyzer:
    """
    Analyzes dialogue for common issues in fiction writing.

    Said-ism Philosophy:
    - 'Said' is largely invisible to readers (good default)
    - Fancy tags ('exclaimed', 'interjected') draw attention
    - Action beats show character while maintaining flow
    - Balance is key: too much 'said' can feel monotonous,
      but fancy tags are worse than said-bookism fears
    """

    # Invisible tags (readers gloss over these)
    INVISIBLE_TAGS: Set[str] = {'said', 'asked'}

    # Acceptable alternative tags (use sparingly)
    ALTERNATIVE_TAGS: Set[str] = {
        'replied', 'answered', 'whispered', 'shouted', 'yelled',
        'screamed', 'muttered', 'murmured', 'called', 'added',
        'continued', 'responded',
    }

    # Fancy/problematic tags (avoid or minimize)
    FANCY_TAGS: Set[str] = {
        'exclaimed', 'proclaimed', 'ejaculated', 'interjected',
        'opined', 'stated', 'queried', 'inquired', 'declared',
        'announced', 'asserted', 'averred', 'remarked', 'observed',
        'commented', 'noted', 'mentioned', 'uttered', 'vocalized',
        'articulated', 'enunciated', 'verbalized', 'expounded',
    }

    # Impossible tags (can't be spoken)
    IMPOSSIBLE_TAGS: Set[str] = {
        'smiled', 'laughed', 'grinned', 'chuckled', 'giggled',
        'snorted', 'frowned', 'nodded', 'shrugged', 'sighed',
        'shook', 'winked', 'grimaced', 'smirked',
    }

    # All dialogue tags combined
    DIALOGUE_TAGS: Set[str] = INVISIBLE_TAGS | ALTERNATIVE_TAGS | FANCY_TAGS

    # Dialogue crutches - words that weaken dialogue
    DIALOGUE_CRUTCHES: Set[str] = {
        'um', 'uh', 'er', 'ah', 'hmm', 'hm', 'well', 'like', 'you know',
        'i mean', 'kind of', 'sort of', 'just', 'actually', 'basically',
        'literally', 'honestly', 'obviously', 'totally', 'really',
    }

    # Action beat verbs (show character instead of tagging)
    ACTION_BEAT_INDICATORS: Set[str] = {
        'turned', 'looked', 'glanced', 'stepped', 'moved', 'reached',
        'grabbed', 'picked', 'set', 'put', 'took', 'stood', 'sat',
        'leaned', 'crossed', 'uncrossed', 'rubbed', 'scratched',
        'ran', 'walked', 'paced', 'shifted', 'settled', 'adjusted',
    }

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze text for dialogue issues.

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

        # Said-ism analysis (most important for dialogue quality)
        suggestions.extend(self._analyze_said_ism(text, dialogue_info))

        # Check for various dialogue issues
        suggestions.extend(self._check_dialogue_tags(text, dialogue_info))
        suggestions.extend(self._check_impossible_tags(text))
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

    def _analyze_said_ism(self, text: str, dialogue_info: dict) -> List[Suggestion]:
        """
        Comprehensive said-ism analysis.

        Analyzes the balance between:
        - Invisible tags ('said', 'asked')
        - Alternative tags ('whispered', 'shouted', etc.)
        - Fancy tags ('exclaimed', 'proclaimed', etc.)
        - Action beats (show instead of tell)

        Returns suggestions for improving dialogue attribution balance.
        """
        suggestions = []

        if len(dialogue_info['lines']) < 3:
            # Not enough dialogue for meaningful analysis
            return suggestions

        # Count different attribution types
        counts = self._count_attribution_types(text)

        # Sum only numeric counts (exclude fancy_tags_found list)
        total_attributions = (
            counts['invisible'] +
            counts['alternative'] +
            counts['fancy'] +
            counts['action_beats']
        )
        if total_attributions == 0:
            return suggestions

        # Calculate percentages
        invisible_pct = 100 * counts['invisible'] / total_attributions if total_attributions > 0 else 0
        alternative_pct = 100 * counts['alternative'] / total_attributions if total_attributions > 0 else 0
        fancy_pct = 100 * counts['fancy'] / total_attributions if total_attributions > 0 else 0
        action_beat_pct = 100 * counts['action_beats'] / total_attributions if total_attributions > 0 else 0

        # Ideal balance (rough guidelines):
        # - Invisible (said/asked): 40-60%
        # - Alternative tags: 10-20%
        # - Action beats: 20-40%
        # - Fancy tags: <5%

        # Check for fancy tag overuse (most common amateur mistake)
        if fancy_pct > 10:
            fancy_tags_found = counts.get('fancy_tags_found', [])
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.WARNING,
                message=f"Fancy dialogue tags at {fancy_pct:.0f}% of attributions",
                suggestion=(
                    f"You're using elaborate dialogue tags like {', '.join(fancy_tags_found[:3])}. "
                    "These draw attention away from your dialogue. 'Said' is invisible to readers—"
                    "embrace it, or use action beats to show character."
                ),
                metadata={
                    "counts": counts,
                    "fancy_percentage": round(fancy_pct, 1),
                    "fancy_tags_found": fancy_tags_found,
                    "teaching_point": (
                        "'Said-bookism' is when writers avoid 'said' by using elaborate alternatives. "
                        "Ironically, 'said' is nearly invisible to readers, while fancy tags like "
                        "'exclaimed' or 'interjected' stick out and slow down reading. Most published "
                        "authors use 'said' for 70-80% of their dialogue tags."
                    )
                }
            ))
        elif counts['fancy'] > 0 and fancy_pct > 5:
            # Gentle warning for moderate fancy tag use
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.INFO,
                message=f"Some fancy dialogue tags detected ({counts['fancy']} instances)",
                suggestion=(
                    "A few elaborate dialogue tags are fine for emphasis, but 'said' remains "
                    "the workhorse of dialogue. Consider whether each fancy tag earns its place."
                ),
                metadata={
                    "counts": counts,
                    "fancy_percentage": round(fancy_pct, 1),
                }
            ))

        # Check for too few action beats
        if action_beat_pct < 15 and total_attributions >= 5:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.INFO,
                message="Few action beats in dialogue attribution",
                suggestion=(
                    f"Only {action_beat_pct:.0f}% of your dialogue uses action beats. "
                    "Action beats (character movements and gestures) can replace tags while "
                    "showing character and grounding the scene. Example: Instead of "
                    "\"I don't know,\" she said, try: She twisted the ring on her finger. "
                    "\"I don't know.\""
                ),
                metadata={
                    "action_beat_percentage": round(action_beat_pct, 1),
                    "counts": counts,
                    "teaching_point": (
                        "Action beats serve multiple purposes: they attribute dialogue, "
                        "reveal character through gesture, maintain scene grounding, and "
                        "control pacing. They're often better than any dialogue tag."
                    )
                }
            ))

        # Check for 'said' overuse (less common but still worth noting)
        if invisible_pct > 80 and total_attributions >= 8:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.INFO,
                message=f"'Said/asked' used for {invisible_pct:.0f}% of dialogue",
                suggestion=(
                    "While 'said' is appropriately invisible, using it for nearly every "
                    "line can create a rhythmic monotony. Mix in occasional action beats "
                    "to show character and vary the prose rhythm."
                ),
                metadata={
                    "invisible_percentage": round(invisible_pct, 1),
                    "counts": counts,
                }
            ))

        # Provide overall balance summary for significant dialogue
        if total_attributions >= 10:
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.INFO,
                message="Dialogue attribution breakdown",
                suggestion=(
                    f"Said/asked: {invisible_pct:.0f}%, "
                    f"Alternative tags: {alternative_pct:.0f}%, "
                    f"Action beats: {action_beat_pct:.0f}%, "
                    f"Fancy tags: {fancy_pct:.0f}%"
                ),
                metadata={
                    "counts": counts,
                    "percentages": {
                        "invisible": round(invisible_pct, 1),
                        "alternative": round(alternative_pct, 1),
                        "action_beats": round(action_beat_pct, 1),
                        "fancy": round(fancy_pct, 1),
                    },
                    "teaching_point": (
                        "Professional fiction typically shows: 'said/asked' 50-70%, "
                        "action beats 20-35%, alternative tags 10-15%, fancy tags <5%. "
                        "These aren't rules—some authors use almost no 'said'—but they're "
                        "useful benchmarks."
                    )
                }
            ))

        return suggestions

    def _count_attribution_types(self, text: str) -> Dict[str, int]:
        """
        Count different types of dialogue attribution in text.

        Returns dict with counts for:
        - invisible: 'said', 'asked'
        - alternative: 'whispered', 'shouted', etc.
        - fancy: 'exclaimed', 'proclaimed', etc.
        - action_beats: estimated action beat attributions
        """
        counts = {
            'invisible': 0,
            'alternative': 0,
            'fancy': 0,
            'action_beats': 0,
            'fancy_tags_found': [],
        }

        text_lower = text.lower()

        # Count invisible tags
        for tag in self.INVISIBLE_TAGS:
            pattern = rf'\b{tag}(?:s|ed|ing)?\b'
            matches = re.findall(pattern, text_lower)
            counts['invisible'] += len(matches)

        # Count alternative tags
        for tag in self.ALTERNATIVE_TAGS:
            pattern = rf'\b{tag}(?:s|ed|ing)?\b'
            matches = re.findall(pattern, text_lower)
            counts['alternative'] += len(matches)

        # Count fancy tags
        for tag in self.FANCY_TAGS:
            pattern = rf'\b{tag}(?:s|ed|ing)?\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                counts['fancy'] += len(matches)
                if tag not in counts['fancy_tags_found']:
                    counts['fancy_tags_found'].append(tag)

        # Estimate action beats (verbs near dialogue that aren't tags)
        # Look for patterns like: He/She + verb or Name + verb near quotes
        action_pattern = r'(?:^|\.\s+)([A-Z][a-z]+|[Hh]e|[Ss]he|[Tt]hey)\s+([a-z]+ed|[a-z]+s)\b'
        for match in re.finditer(action_pattern, text):
            verb = match.group(2).lower()
            # Remove common suffixes for matching
            verb_base = re.sub(r'(ed|s|ing)$', '', verb)
            if verb_base in self.ACTION_BEAT_INDICATORS or verb in self.ACTION_BEAT_INDICATORS:
                counts['action_beats'] += 1

        return counts

    def _check_impossible_tags(self, text: str) -> List[Suggestion]:
        """
        Detect impossible dialogue tags (actions that can't produce speech).

        E.g., "I love you," she smiled. (You can't smile words)
        """
        suggestions = []
        found_tags = []

        # Pattern: dialogue followed by name/pronoun + impossible tag
        for tag in self.IMPOSSIBLE_TAGS:
            # Match: "dialogue," pronoun/name tag
            pattern = rf'["""][^"""]+[,]["""][\s]+(?:\w+\s+)?{tag}(?:d|s|ing)?\b'
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                found_tags.append((tag, matches[0]))

        if found_tags:
            first_tag, first_match = found_tags[0]
            suggestions.append(Suggestion(
                type=SuggestionType.DIALOGUE_TAGS,
                severity=SeverityLevel.WARNING,
                message=f"Impossible dialogue tag: '{first_tag}'",
                suggestion=(
                    f"You can't {first_tag} words—this should be an action beat, not a tag. "
                    f"Try: '...\" She {first_tag}d.' (period instead of comma, "
                    f"making it a separate action) or use 'said' with the action: "
                    f"'...\" she said, {first_tag[:-1] if first_tag.endswith('e') else first_tag}ing.'"
                ),
                start_char=first_match.start(),
                end_char=first_match.end(),
                highlight_word=first_tag,
                metadata={
                    "impossible_tags_found": [t[0] for t in found_tags],
                    "total_count": len(found_tags),
                    "teaching_point": (
                        "Dialogue tags must be verbs of speech. 'Smiled', 'laughed', "
                        "'shrugged', etc. are physical actions, not ways of speaking. "
                        "To combine them with dialogue, use a period to separate: "
                        "\"Great.\" She smiled. Or: \"Great,\" she said, smiling."
                    )
                }
            ))

        return suggestions

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
