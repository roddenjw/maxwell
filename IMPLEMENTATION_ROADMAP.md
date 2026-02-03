# Maxwell Feature Implementation Roadmap

**Based on Competitive Analysis**
**Date:** February 3, 2026
**Version:** 1.0

---

## Overview

This roadmap details six priority features identified in the competitive analysis. Implementation follows Maxwell's existing architectural patterns:

- **Backend:** Three-tier (Routes → Services → Models) with FastAPI
- **Frontend:** Component-Store-API pattern with React + Zustand
- **API:** ApiResponse<T> pattern with standardized error handling

---

## Implementation Timeline

```
Week 1-2:  LanguageTool Integration (Feature 1)
Week 2-3:  Fast Coach Expansion (Feature 2)
Week 3-4:  Scrivener Import (Feature 3)
Week 5-7:  Character Voice Consistency Analyzer (Feature 4)
Week 7-9:  Visual Timeline Enhancement (Feature 5)
Week 9-11: Foreshadowing Tracker Expansion (Feature 6)
```

---

## IMMEDIATE PRIORITY (4 Weeks)

---

## Feature 1: LanguageTool Integration for Grammar/Spelling

**Objective:** Add grammar and spelling checking without competing with Grammarly - integrate LanguageTool as an optional, toggleable layer.

**Effort:** 5-7 days

### 1.1 Backend Implementation

#### New Files to Create

**`backend/app/services/languagetool_service.py`**
```python
"""
LanguageTool integration service for grammar and spelling checks.
Uses local LanguageTool server or Python library for offline operation.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import language_tool_python

@dataclass
class GrammarIssue:
    """A grammar or spelling issue detected by LanguageTool"""
    message: str
    replacements: List[str]
    offset: int
    length: int
    rule_id: str
    category: str  # GRAMMAR, SPELLING, STYLE, etc.
    context: str

class LanguageToolService:
    """Service for grammar and spelling checking via LanguageTool"""

    def __init__(self):
        self._tool = None
        self._language = "en-US"

    def _get_tool(self) -> language_tool_python.LanguageTool:
        """Lazy initialization of LanguageTool"""
        if self._tool is None:
            self._tool = language_tool_python.LanguageTool(self._language)
        return self._tool

    def check_text(
        self,
        text: str,
        ignore_rules: Optional[List[str]] = None,
        custom_dictionary: Optional[List[str]] = None
    ) -> List[GrammarIssue]:
        """
        Check text for grammar and spelling issues.

        Args:
            text: Text to check
            ignore_rules: Rule IDs to ignore (e.g., WHITESPACE_RULE)
            custom_dictionary: Words to treat as correct (fantasy names, etc.)
        """
        tool = self._get_tool()

        # Add custom words to ignore
        if custom_dictionary:
            for word in custom_dictionary:
                tool.add_to_personal_dict(word)

        matches = tool.check(text)

        issues = []
        for match in matches:
            # Skip ignored rules
            if ignore_rules and match.ruleId in ignore_rules:
                continue

            issues.append(GrammarIssue(
                message=match.message,
                replacements=match.replacements[:5],  # Top 5 suggestions
                offset=match.offset,
                length=match.errorLength,
                rule_id=match.ruleId,
                category=match.category,
                context=match.context
            ))

        return issues

    def configure_language(self, language: str):
        """Change the language (e.g., 'en-US', 'en-GB')"""
        self._language = language
        self._tool = None  # Reset for lazy re-init

    def get_rule_categories(self) -> List[str]:
        """Get available rule categories for filtering"""
        return ["GRAMMAR", "SPELLING", "STYLE", "PUNCTUATION", "TYPOGRAPHY"]


# Singleton instance
languagetool_service = LanguageToolService()
```

**`backend/app/services/fast_coach/grammar_analyzer.py`**
```python
"""
Grammar analyzer for Fast Coach integration.
Bridges LanguageTool to the Fast Coach suggestion system.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .types import Suggestion, SuggestionType, SeverityLevel
from ..languagetool_service import languagetool_service, GrammarIssue


class GrammarAnalyzer:
    """Analyze text for grammar and spelling issues"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session

    def analyze(
        self,
        text: str,
        manuscript_id: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> List[Suggestion]:
        """
        Analyze text for grammar and spelling issues.

        Args:
            text: Text to analyze
            manuscript_id: Optional manuscript for custom dictionary
            settings: Grammar checking settings (enabled, ignore_rules, etc.)
        """
        if not text or len(text.strip()) < 10:
            return []

        # Check if enabled (defaults to True)
        if settings and not settings.get("enabled", True):
            return []

        # Get custom dictionary (fantasy names, etc.)
        custom_dict = settings.get("custom_dictionary", []) if settings else []
        ignore_rules = settings.get("ignore_rules", []) if settings else []

        # Run LanguageTool check
        issues = languagetool_service.check_text(
            text=text,
            ignore_rules=ignore_rules,
            custom_dictionary=custom_dict
        )

        # Convert to Fast Coach suggestions
        suggestions = []
        for issue in issues:
            suggestion_type = self._map_category_to_type(issue.category)
            severity = self._determine_severity(issue)

            suggestions.append(Suggestion(
                type=suggestion_type,
                severity=severity,
                message=issue.message,
                suggestion=self._format_suggestion(issue),
                start_char=issue.offset,
                end_char=issue.offset + issue.length,
                metadata={
                    "rule_id": issue.rule_id,
                    "category": issue.category,
                    "replacements": issue.replacements,
                    "context": issue.context
                }
            ))

        return suggestions

    def _map_category_to_type(self, category: str) -> SuggestionType:
        """Map LanguageTool category to SuggestionType"""
        mapping = {
            "SPELLING": SuggestionType.SPELLING,
            "GRAMMAR": SuggestionType.GRAMMAR,
            "STYLE": SuggestionType.STYLE,
            "PUNCTUATION": SuggestionType.GRAMMAR,
            "TYPOGRAPHY": SuggestionType.STYLE,
        }
        return mapping.get(category, SuggestionType.GRAMMAR)

    def _determine_severity(self, issue: GrammarIssue) -> SeverityLevel:
        """Determine severity based on issue type"""
        if issue.category == "SPELLING":
            return SeverityLevel.WARNING
        elif issue.category == "GRAMMAR":
            return SeverityLevel.WARNING
        else:
            return SeverityLevel.INFO

    def _format_suggestion(self, issue: GrammarIssue) -> str:
        """Format suggestion text"""
        if issue.replacements:
            alts = ", ".join(issue.replacements[:3])
            return f"Consider: {alts}"
        return "Review this for potential issues."
```

#### Files to Modify

**`backend/app/services/fast_coach/types.py`** - Add new types:
```python
# Add to SuggestionType enum:
GRAMMAR = "grammar"
SPELLING = "spelling"
```

**`backend/app/services/fast_coach/__init__.py`** - Export new analyzer:
```python
from .grammar_analyzer import GrammarAnalyzer
```

**`backend/app/api/routes/fast_coach.py`** - Add endpoints:
```python
@router.post("/grammar-check")
async def check_grammar(
    text: str = Body(...),
    manuscript_id: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Check text for grammar and spelling issues"""
    settings = None
    if manuscript_id:
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if manuscript and manuscript.settings:
            settings = manuscript.settings.get("grammar_checking", {})

    analyzer = GrammarAnalyzer(db)
    suggestions = analyzer.analyze(text, manuscript_id, settings)

    return {"suggestions": [s.to_dict() for s in suggestions]}

@router.post("/add-to-dictionary/{manuscript_id}")
async def add_to_dictionary(
    manuscript_id: str,
    word: str = Body(...),
    db: Session = Depends(get_db)
):
    """Add word to manuscript's custom dictionary"""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    settings = manuscript.settings or {}
    grammar_settings = settings.get("grammar_checking", {"custom_dictionary": []})

    if word not in grammar_settings.get("custom_dictionary", []):
        grammar_settings.setdefault("custom_dictionary", []).append(word)
        settings["grammar_checking"] = grammar_settings
        manuscript.settings = settings
        db.commit()

    return {"status": "added", "word": word}
```

### 1.2 Frontend Implementation

#### New Files

**`frontend/src/components/FastCoach/GrammarPanel.tsx`**
```typescript
import React, { useState } from 'react';
import { useManuscriptStore } from '../../stores/manuscriptStore';
import { useFastCoachStore } from '../../stores/fastCoachStore';
import { fastCoachApi } from '../../lib/api';

interface GrammarPanelProps {
  manuscriptId: string;
}

export const GrammarPanel: React.FC<GrammarPanelProps> = ({ manuscriptId }) => {
  const [isEnabled, setIsEnabled] = useState(true);
  const [customWords, setCustomWords] = useState<string[]>([]);
  const { grammarSuggestions, setGrammarSuggestions } = useFastCoachStore();

  const handleAddToDict = async (word: string) => {
    await fastCoachApi.addToDictionary(manuscriptId, word);
    setCustomWords([...customWords, word]);
    // Remove suggestions for this word
    setGrammarSuggestions(
      grammarSuggestions.filter(s => !s.metadata?.context?.includes(word))
    );
  };

  return (
    <div className="grammar-panel">
      <div className="grammar-header">
        <h3>Grammar & Spelling</h3>
        <label className="toggle">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
          />
          <span>Enabled</span>
        </label>
      </div>

      {grammarSuggestions.length === 0 ? (
        <p className="no-issues">No grammar issues detected</p>
      ) : (
        <ul className="suggestion-list">
          {grammarSuggestions.map((suggestion, idx) => (
            <li key={idx} className={`suggestion ${suggestion.severity}`}>
              <div className="message">{suggestion.message}</div>
              <div className="suggestion-text">{suggestion.suggestion}</div>
              {suggestion.type === 'spelling' && (
                <button
                  onClick={() => handleAddToDict(suggestion.metadata?.context)}
                  className="add-to-dict"
                >
                  Add to Dictionary
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

#### Files to Modify

- `frontend/src/stores/fastCoachStore.ts` - Add `grammarSuggestions` state
- `frontend/src/lib/api.ts` - Add `fastCoachApi.checkGrammar()` and `fastCoachApi.addToDictionary()`

### 1.3 Dependencies

Add to `backend/requirements.txt`:
```
language-tool-python==2.7.1
```

---

## Feature 2: Fast Coach Expansion

**Objective:** Expand from 4 analyzers to 8, narrowing the gap with ProWritingAid.

**Effort:** 5-6 days

### 2.1 Readability Scores Analyzer

**`backend/app/services/fast_coach/readability_analyzer.py`**
```python
"""
Readability analyzer for measuring text complexity.
Implements Flesch-Kincaid, Gunning Fog, SMOG, and Coleman-Liau indices.
"""

import re
import math
from typing import List
from .types import Suggestion, SuggestionType, SeverityLevel


class ReadabilityAnalyzer:
    """Analyzes text readability using multiple metrics"""

    # Genre-specific target grade levels
    GENRE_TARGETS = {
        "young_adult": (6, 8),
        "adult_fiction": (7, 10),
        "literary_fiction": (9, 12),
        "thriller": (6, 9),
        "romance": (6, 8),
        "fantasy": (8, 11),
        "sci_fi": (9, 12),
    }

    def analyze(self, text: str, genre: str = "adult_fiction") -> List[Suggestion]:
        """
        Analyze text readability.

        Returns suggestions if readability is significantly off-target for genre.
        """
        if not text or len(text.strip()) < 100:
            return []

        # Calculate metrics
        fk_grade = self._flesch_kincaid_grade(text)
        fk_ease = self._flesch_reading_ease(text)
        fog = self._gunning_fog_index(text)

        suggestions = []
        target_min, target_max = self.GENRE_TARGETS.get(genre, (7, 10))

        # Check if readability is appropriate for genre
        avg_grade = (fk_grade + fog) / 2

        if avg_grade > target_max + 2:
            suggestions.append(Suggestion(
                type=SuggestionType.READABILITY,
                severity=SeverityLevel.INFO,
                message=f"Readability: Grade {avg_grade:.1f} (target: {target_min}-{target_max})",
                suggestion=f"This text may be complex for {genre.replace('_', ' ')} readers. "
                          f"Consider shorter sentences or simpler vocabulary for accessibility.",
                metadata={
                    "flesch_kincaid_grade": round(fk_grade, 1),
                    "flesch_reading_ease": round(fk_ease, 1),
                    "gunning_fog": round(fog, 1),
                    "target_grade_min": target_min,
                    "target_grade_max": target_max,
                    "genre": genre
                }
            ))
        elif avg_grade < target_min - 2:
            suggestions.append(Suggestion(
                type=SuggestionType.READABILITY,
                severity=SeverityLevel.INFO,
                message=f"Readability: Grade {avg_grade:.1f} (target: {target_min}-{target_max})",
                suggestion=f"This text is quite simple. For {genre.replace('_', ' ')}, "
                          f"you might enrich the prose with more varied vocabulary.",
                metadata={
                    "flesch_kincaid_grade": round(fk_grade, 1),
                    "flesch_reading_ease": round(fk_ease, 1),
                    "gunning_fog": round(fog, 1),
                    "target_grade_min": target_min,
                    "target_grade_max": target_max,
                    "genre": genre
                }
            ))
        else:
            # Add informational readability stats even when on target
            suggestions.append(Suggestion(
                type=SuggestionType.READABILITY,
                severity=SeverityLevel.INFO,
                message=f"Readability: Grade {avg_grade:.1f} - appropriate for {genre.replace('_', ' ')}",
                suggestion="Your text complexity matches your target audience well.",
                metadata={
                    "flesch_kincaid_grade": round(fk_grade, 1),
                    "flesch_reading_ease": round(fk_ease, 1),
                    "gunning_fog": round(fog, 1),
                    "on_target": True
                }
            ))

        return suggestions

    def _flesch_kincaid_grade(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid Grade Level.
        Returns the U.S. grade level needed to understand the text.
        """
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)

        if sentences == 0 or words == 0:
            return 0.0

        return (0.39 * (words / sentences) +
                11.8 * (syllables / words) - 15.59)

    def _flesch_reading_ease(self, text: str) -> float:
        """
        Calculate Flesch Reading Ease score.
        Score 0-100, higher = easier to read.
        90-100: Very Easy (5th grade)
        60-70: Standard (8th-9th grade)
        30-50: Difficult (college)
        0-30: Very Difficult (professional)
        """
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)

        if sentences == 0 or words == 0:
            return 100.0

        return (206.835 -
                1.015 * (words / sentences) -
                84.6 * (syllables / words))

    def _gunning_fog_index(self, text: str) -> float:
        """
        Calculate Gunning Fog Index.
        Estimates years of formal education needed to understand text.
        """
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        complex_words = self._count_complex_words(text)

        if sentences == 0 or words == 0:
            return 0.0

        return 0.4 * ((words / sentences) + 100 * (complex_words / words))

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        return len(re.findall(r'[.!?]+', text))

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(re.findall(r'\b\w+\b', text))

    def _count_syllables(self, text: str) -> int:
        """Count total syllables in text"""
        words = re.findall(r'\b\w+\b', text.lower())
        return sum(self._syllables_in_word(word) for word in words)

    def _syllables_in_word(self, word: str) -> int:
        """Count syllables in a single word"""
        word = word.lower()
        if len(word) <= 3:
            return 1

        # Count vowel groups
        count = len(re.findall(r'[aeiouy]+', word))

        # Subtract silent e
        if word.endswith('e'):
            count -= 1

        # Ensure at least 1 syllable
        return max(1, count)

    def _count_complex_words(self, text: str) -> int:
        """Count complex words (3+ syllables, excluding common suffixes)"""
        words = re.findall(r'\b\w+\b', text.lower())
        count = 0
        for word in words:
            # Skip proper nouns (rough heuristic)
            if self._syllables_in_word(word) >= 3:
                # Exclude words with common suffixes that don't add complexity
                if not re.search(r'(ing|ed|es|ly|ment|tion|ness)$', word):
                    count += 1
        return count
```

### 2.2 Sentence Starter Variety Analyzer

**`backend/app/services/fast_coach/sentence_starter_analyzer.py`**
```python
"""
Sentence starter variety analyzer.
Detects repetitive sentence openings that can make prose feel monotonous.
"""

import re
from typing import List, Tuple, Dict
from collections import Counter
from .types import Suggestion, SuggestionType, SeverityLevel


class SentenceStarterAnalyzer:
    """Detects repetitive sentence starters"""

    PRONOUN_STARTERS = {'he', 'she', 'they', 'i', 'we', 'it', 'you'}
    ARTICLE_STARTERS = {'the', 'a', 'an'}
    COMMON_STARTERS = {'there', 'this', 'that', 'these', 'those', 'here'}

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze sentence starters for repetition.

        Checks:
        1. Consecutive sentences starting with same word
        2. High percentage of pronoun starters
        3. Overuse of "The" starts
        """
        if not text or len(text.strip()) < 100:
            return []

        suggestions = []
        starters = self._extract_sentence_starters(text)

        if len(starters) < 5:
            return []

        # Check for consecutive repetition
        consecutive_issues = self._find_consecutive_repetition(starters)
        suggestions.extend(consecutive_issues)

        # Check for overall distribution
        distribution_issues = self._check_distribution(starters)
        suggestions.extend(distribution_issues)

        return suggestions

    def _extract_sentence_starters(self, text: str) -> List[Tuple[str, int]]:
        """Extract first word of each sentence with position"""
        starters = []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        position = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Get first word
                match = re.match(r'^["\']?\s*(\w+)', sentence)
                if match:
                    first_word = match.group(1).lower()
                    starters.append((first_word, position))
                position += len(sentence) + 1

        return starters

    def _find_consecutive_repetition(
        self,
        starters: List[Tuple[str, int]]
    ) -> List[Suggestion]:
        """Find 3+ consecutive sentences starting with same word"""
        suggestions = []

        i = 0
        while i < len(starters) - 2:
            word = starters[i][0]
            count = 1

            # Count consecutive same starters
            j = i + 1
            while j < len(starters) and starters[j][0] == word:
                count += 1
                j += 1

            if count >= 3:
                suggestions.append(Suggestion(
                    type=SuggestionType.SENTENCE_VARIETY,
                    severity=SeverityLevel.WARNING,
                    message=f"{count} consecutive sentences start with '{word.capitalize()}'",
                    suggestion=f"Vary your sentence openings. Try starting with: an action, "
                              f"a prepositional phrase, a dependent clause, or dialogue.",
                    start_char=starters[i][1],
                    end_char=starters[j-1][1] + 50,  # Approximate end
                    metadata={
                        "repeated_word": word,
                        "count": count,
                        "teaching_point": "Repetitive sentence starters create a monotonous "
                                         "rhythm that can fatigue readers. Varying your openings "
                                         "keeps prose dynamic and engaging."
                    }
                ))
                i = j
            else:
                i += 1

        return suggestions

    def _check_distribution(self, starters: List[Tuple[str, int]]) -> List[Suggestion]:
        """Check overall distribution of starter types"""
        suggestions = []
        words = [s[0] for s in starters]
        total = len(words)

        # Count categories
        pronoun_count = sum(1 for w in words if w in self.PRONOUN_STARTERS)
        article_count = sum(1 for w in words if w in self.ARTICLE_STARTERS)
        the_count = sum(1 for w in words if w == 'the')

        # Check pronoun overuse (>40%)
        pronoun_pct = pronoun_count / total * 100
        if pronoun_pct > 40:
            suggestions.append(Suggestion(
                type=SuggestionType.SENTENCE_VARIETY,
                severity=SeverityLevel.INFO,
                message=f"{pronoun_pct:.0f}% of sentences start with pronouns (he/she/they/I)",
                suggestion="Consider more variety: action verbs, descriptions, dialogue, "
                          "or prepositional phrases can create a more varied rhythm.",
                metadata={
                    "pronoun_percentage": round(pronoun_pct, 1),
                    "pronoun_count": pronoun_count,
                    "total_sentences": total,
                    "teaching_point": "While pronouns are natural sentence starters, "
                                     "overusing them can make prose feel repetitive. "
                                     "Aim for under 35% pronoun starts."
                }
            ))

        # Check "The" overuse (>20%)
        the_pct = the_count / total * 100
        if the_pct > 20:
            suggestions.append(Suggestion(
                type=SuggestionType.SENTENCE_VARIETY,
                severity=SeverityLevel.INFO,
                message=f"{the_pct:.0f}% of sentences start with 'The'",
                suggestion="Too many 'The' starters can feel like a list. "
                          "Try leading with the subject's action or emotion instead.",
                metadata={
                    "the_percentage": round(the_pct, 1),
                    "the_count": the_count,
                    "total_sentences": total
                }
            ))

        return suggestions
```

### 2.3 Overused Phrases Analyzer

**`backend/app/services/fast_coach/overused_phrases_analyzer.py`**
```python
"""
Overused phrases analyzer.
Detects clichés, overused physical reactions, and tired transitions.
"""

import re
from typing import List, Set
from .types import Suggestion, SuggestionType, SeverityLevel


class OverusedPhrasesAnalyzer:
    """Detects overused phrases beyond basic clichés"""

    # Categorized overused phrases with alternatives
    OVERUSED_PHRASES = {
        # Physical reactions (most overused in amateur fiction)
        "physical_reactions": {
            "let out a breath": "Show the emotion causing the breath instead",
            "took a deep breath": "What emotion drives this? Show it directly",
            "released a breath": "Same as above - show don't tell the emotion",
            "held her breath": "Consider showing the tension differently",
            "rolled her eyes": "Describe the irritation more specifically",
            "rolled his eyes": "Describe the irritation more specifically",
            "clenched his jaw": "What emotion? Anger, frustration? Show it",
            "clenched her jaw": "What emotion? Anger, frustration? Show it",
            "bit her lip": "Often used for nervousness - find a unique tell",
            "bit his lip": "Often used for nervousness - find a unique tell",
            "heart pounded": "Very common - try a more specific sensation",
            "heart raced": "Very common - try a more specific sensation",
            "heart skipped a beat": "Cliché - find a fresh way to show surprise",
            "stomach dropped": "Common - describe the specific sensation",
            "stomach churned": "Common - be more specific about the feeling",
            "knot in her stomach": "Overused - describe the specific anxiety",
            "knot in his stomach": "Overused - describe the specific anxiety",
            "blood ran cold": "Cliché - find a fresh way to show fear",
            "shiver ran down": "Very common - try a different physical reaction",
            "goosebumps": "Common - what specifically causes them?",
            "let out a sigh": "Show what emotion drives the sigh",
        },
        # Transitions
        "transitions": {
            "all of a sudden": "Use 'suddenly' or show the suddenness through action",
            "before long": "Be more specific about the time that passed",
            "in the blink of an eye": "Cliché - show the speed through action",
            "without warning": "Show the surprise through character reaction",
            "out of nowhere": "Show where it came from or make the surprise vivid",
            "the next thing he knew": "Often a POV break - stay in the moment",
            "the next thing she knew": "Often a POV break - stay in the moment",
        },
        # Descriptions
        "descriptions": {
            "crystal clear": "Be specific about what's clear and why",
            "pitch black": "Describe what the darkness feels like",
            "blood red": "Just say 'red' or describe the specific shade",
            "deafening silence": "Oxymoron cliché - describe the silence uniquely",
            "pregnant pause": "Show the weight of the pause through character",
            "piercing blue eyes": "Overused - find a fresh description",
            "emerald green eyes": "Overused - find a fresh description",
            "chiseled features": "Cliché - be more specific",
        },
        # Actions
        "actions": {
            "nodded in agreement": "'Nodded' implies agreement - redundant",
            "shook his head in disbelief": "Often 'shook his head' is enough",
            "shook her head in disbelief": "Often 'shook her head' is enough",
            "turned on her heel": "Cliché action - describe the departure uniquely",
            "turned on his heel": "Cliché action - describe the departure uniquely",
            "spun around": "Common - try a more specific action",
            "whipped around": "Common - try a more specific action",
            "leaned in close": "Common - what's the intent? Show it",
        },
        # Emotions
        "emotions": {
            "couldn't help but": "Often unnecessary - just show the action",
            "couldn't believe": "Show the disbelief through reaction",
            "didn't know what to say": "Show the speechlessness",
            "at a loss for words": "Cliché - show the character's struggle",
            "tears streamed down": "Very common - find a fresh way to show crying",
            "tears welled up": "Common - show the emotion causing the tears",
            "couldn't contain": "Just show them not containing it",
        },
    }

    def analyze(self, text: str) -> List[Suggestion]:
        """Check for overused phrases"""
        if not text or len(text.strip()) < 50:
            return []

        suggestions = []
        text_lower = text.lower()

        for category, phrases in self.OVERUSED_PHRASES.items():
            for phrase, alternative in phrases.items():
                # Find all occurrences
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                for match in pattern.finditer(text_lower):
                    suggestions.append(Suggestion(
                        type=SuggestionType.OVERUSED_PHRASE,
                        severity=SeverityLevel.INFO,
                        message=f"Overused phrase: '{match.group()}'",
                        suggestion=alternative,
                        start_char=match.start(),
                        end_char=match.end(),
                        metadata={
                            "phrase": phrase,
                            "category": category,
                            "teaching_point": f"Phrases become clichés when readers encounter "
                                             f"them too often. Finding fresh ways to express "
                                             f"the same idea makes your prose more memorable."
                        }
                    ))

        return suggestions
```

### 2.4 Update Types

**Modify `backend/app/services/fast_coach/types.py`:**
```python
class SuggestionType(str, Enum):
    # Existing
    STYLE = "style"
    WORD_CHOICE = "word_choice"
    DIALOGUE = "dialogue"
    CONSISTENCY = "consistency"

    # New
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    READABILITY = "readability"
    SENTENCE_VARIETY = "sentence_variety"
    OVERUSED_PHRASE = "overused_phrase"
```

---

## Feature 3: Scrivener Import

**Objective:** Enable import of .scriv (Scrivener 3) project folders.

**Effort:** 8-10 days

### 3.1 Backend Implementation

**`backend/app/services/scrivener_import_service.py`**
```python
"""
Scrivener project import service.
Handles parsing of .scriv project folders and conversion to Maxwell format.
"""

import os
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import tempfile
import shutil

from striprtf.striprtf import rtf_to_text


@dataclass
class ScrivenerDocument:
    """Represents a document in Scrivener binder"""
    uuid: str
    title: str
    doc_type: str  # "Text", "Folder", "Research", "Character", "Location"
    parent_uuid: Optional[str] = None
    children: List[str] = field(default_factory=list)
    synopsis: Optional[str] = None
    content_rtf: Optional[str] = None
    content_plain: Optional[str] = None
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrivenerProject:
    """Parsed Scrivener project"""
    title: str
    author: Optional[str] = None
    draft_folder_uuid: Optional[str] = None
    research_folder_uuid: Optional[str] = None
    characters_folder_uuid: Optional[str] = None
    documents: Dict[str, ScrivenerDocument] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


class ScrivenerImportService:
    """Service for importing Scrivener projects"""

    def __init__(self):
        self.temp_dir = None

    async def parse_scrivener_project(
        self,
        file_path: str,
        is_zip: bool = True
    ) -> ScrivenerProject:
        """
        Parse Scrivener project from .zip or extracted folder.

        Args:
            file_path: Path to .zip file or .scriv folder
            is_zip: If True, extract from zip first
        """
        if is_zip:
            # Extract to temp directory
            self.temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)

            # Find .scriv folder
            scriv_path = self._find_scriv_folder(self.temp_dir)
            if not scriv_path:
                raise ValueError("No .scriv folder found in zip")
        else:
            scriv_path = file_path

        try:
            # Parse the project
            project = self._parse_scrivx(scriv_path)

            # Extract content for each document
            await self._extract_all_content(project, scriv_path)

            return project
        finally:
            # Cleanup temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

    def _find_scriv_folder(self, base_path: str) -> Optional[str]:
        """Find .scriv folder in extracted zip"""
        for root, dirs, files in os.walk(base_path):
            for d in dirs:
                if d.endswith('.scriv'):
                    return os.path.join(root, d)
            # Also check if we're inside the scriv folder
            if 'Files' in dirs and any(f.endswith('.scrivx') for f in files):
                return root
        return None

    def _parse_scrivx(self, scriv_path: str) -> ScrivenerProject:
        """Parse the .scrivx XML manifest"""
        # Find .scrivx file
        scrivx_file = None
        for f in os.listdir(scriv_path):
            if f.endswith('.scrivx'):
                scrivx_file = os.path.join(scriv_path, f)
                break

        if not scrivx_file:
            raise ValueError("No .scrivx file found in project")

        tree = ET.parse(scrivx_file)
        root = tree.getroot()

        # Get project title
        title = root.get('Title', 'Untitled')

        project = ScrivenerProject(title=title)

        # Parse binder items
        binder = root.find('.//Binder')
        if binder is not None:
            self._parse_binder_items(binder, project, None)

        # Identify special folders
        self._identify_special_folders(project)

        return project

    def _parse_binder_items(
        self,
        parent_element: ET.Element,
        project: ScrivenerProject,
        parent_uuid: Optional[str]
    ):
        """Recursively parse binder items"""
        for idx, item in enumerate(parent_element.findall('./BinderItem')):
            uuid = item.get('UUID')
            title = item.find('Title')
            title_text = title.text if title is not None else 'Untitled'
            doc_type = item.get('Type', 'Text')

            doc = ScrivenerDocument(
                uuid=uuid,
                title=title_text,
                doc_type=doc_type,
                parent_uuid=parent_uuid,
                order=idx
            )

            # Parse children
            children_elem = item.find('Children')
            if children_elem is not None:
                for child in children_elem.findall('BinderItem'):
                    child_uuid = child.get('UUID')
                    doc.children.append(child_uuid)
                self._parse_binder_items(children_elem, project, uuid)

            project.documents[uuid] = doc

    def _identify_special_folders(self, project: ScrivenerProject):
        """Identify Draft, Research, Characters folders"""
        for uuid, doc in project.documents.items():
            title_lower = doc.title.lower()
            if doc.doc_type == 'Folder' or doc.doc_type == 'DraftFolder':
                if 'draft' in title_lower or 'manuscript' in title_lower:
                    project.draft_folder_uuid = uuid
                elif 'research' in title_lower:
                    project.research_folder_uuid = uuid
                elif 'character' in title_lower:
                    project.characters_folder_uuid = uuid

    async def _extract_all_content(
        self,
        project: ScrivenerProject,
        scriv_path: str
    ):
        """Extract content for all documents"""
        files_path = os.path.join(scriv_path, 'Files', 'Data')

        for uuid, doc in project.documents.items():
            # Skip folders
            if doc.doc_type in ['Folder', 'DraftFolder', 'ResearchFolder']:
                continue

            doc_path = os.path.join(files_path, uuid)

            # Try to read RTF content
            rtf_path = os.path.join(doc_path, 'content.rtf')
            if os.path.exists(rtf_path):
                with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
                    doc.content_rtf = f.read()
                    # Convert to plain text
                    try:
                        doc.content_plain = rtf_to_text(doc.content_rtf)
                    except Exception:
                        doc.content_plain = doc.content_rtf

            # Try to read synopsis
            synopsis_path = os.path.join(doc_path, 'synopsis.txt')
            if os.path.exists(synopsis_path):
                with open(synopsis_path, 'r', encoding='utf-8', errors='ignore') as f:
                    doc.synopsis = f.read()

    def convert_to_maxwell(
        self,
        project: ScrivenerProject,
        import_research: bool = False,
        import_characters: bool = True
    ) -> Dict[str, Any]:
        """
        Convert Scrivener project to Maxwell format.

        Returns:
            {
                "title": str,
                "chapters": List[dict],  # For Manuscript chapters
                "entities": List[dict],   # For Codex entities
            }
        """
        result = {
            "title": project.title,
            "chapters": [],
            "entities": []
        }

        # Convert draft folder to chapters
        if project.draft_folder_uuid:
            self._convert_folder_to_chapters(
                project,
                project.draft_folder_uuid,
                result["chapters"],
                parent_id=None
            )

        # Convert character documents to entities
        if import_characters and project.characters_folder_uuid:
            self._convert_to_entities(
                project,
                project.characters_folder_uuid,
                result["entities"],
                "CHARACTER"
            )

        # Optionally convert research
        if import_research and project.research_folder_uuid:
            self._convert_folder_to_chapters(
                project,
                project.research_folder_uuid,
                result["chapters"],
                parent_id=None,
                doc_type="NOTES"
            )

        return result

    def _convert_folder_to_chapters(
        self,
        project: ScrivenerProject,
        folder_uuid: str,
        chapters: List[dict],
        parent_id: Optional[str],
        doc_type: str = "CHAPTER"
    ):
        """Recursively convert folder contents to chapters"""
        folder = project.documents.get(folder_uuid)
        if not folder:
            return

        for child_uuid in folder.children:
            child = project.documents.get(child_uuid)
            if not child:
                continue

            if child.doc_type in ['Folder', 'DraftFolder']:
                # Create folder in Maxwell
                folder_data = {
                    "title": child.title,
                    "content": "",
                    "document_type": "FOLDER",
                    "order": child.order,
                    "children": []
                }
                chapters.append(folder_data)

                # Recurse into folder
                self._convert_folder_to_chapters(
                    project,
                    child_uuid,
                    folder_data["children"],
                    child_uuid,
                    doc_type
                )
            else:
                # Create chapter/document
                chapters.append({
                    "title": child.title,
                    "content": child.content_plain or "",
                    "synopsis": child.synopsis,
                    "document_type": doc_type,
                    "order": child.order
                })

    def _convert_to_entities(
        self,
        project: ScrivenerProject,
        folder_uuid: str,
        entities: List[dict],
        entity_type: str
    ):
        """Convert folder contents to Codex entities"""
        folder = project.documents.get(folder_uuid)
        if not folder:
            return

        for child_uuid in folder.children:
            child = project.documents.get(child_uuid)
            if not child:
                continue

            if child.doc_type not in ['Folder', 'DraftFolder']:
                entities.append({
                    "name": child.title,
                    "type": entity_type,
                    "description": child.synopsis or "",
                    "content": child.content_plain or ""
                })
            else:
                # Recurse into subfolders (e.g., "Main Characters", "Side Characters")
                self._convert_to_entities(project, child_uuid, entities, entity_type)


# Singleton
scrivener_import_service = ScrivenerImportService()
```

### 3.2 API Endpoint

**Add to `backend/app/api/routes/import_routes.py`:**
```python
from fastapi import UploadFile, File, Query
from app.services.scrivener_import_service import scrivener_import_service

@router.post("/scrivener")
async def import_scrivener_project(
    file: UploadFile = File(...),
    import_research: bool = Query(False, description="Import research folder as notes"),
    import_characters: bool = Query(True, description="Import character sheets as entities"),
    db: Session = Depends(get_db)
):
    """
    Import a Scrivener project.

    Upload a .zip file containing the .scriv folder.
    """
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # Parse Scrivener project
        project = await scrivener_import_service.parse_scrivener_project(temp_path)

        # Convert to Maxwell format
        maxwell_data = scrivener_import_service.convert_to_maxwell(
            project,
            import_research=import_research,
            import_characters=import_characters
        )

        # Create manuscript
        manuscript = Manuscript(
            id=str(uuid.uuid4()),
            title=maxwell_data["title"],
            settings={"imported_from": "scrivener"}
        )
        db.add(manuscript)

        # Create chapters
        def create_chapters(chapter_list, parent_id=None):
            for idx, chapter_data in enumerate(chapter_list):
                chapter = Chapter(
                    id=str(uuid.uuid4()),
                    manuscript_id=manuscript.id,
                    title=chapter_data["title"],
                    content=chapter_data["content"],
                    document_type=chapter_data.get("document_type", "CHAPTER"),
                    order=idx,
                    parent_id=parent_id
                )
                db.add(chapter)

                # Handle nested children
                if chapter_data.get("children"):
                    create_chapters(chapter_data["children"], chapter.id)

        create_chapters(maxwell_data["chapters"])

        # Create entities
        for entity_data in maxwell_data["entities"]:
            entity = Entity(
                id=str(uuid.uuid4()),
                manuscript_id=manuscript.id,
                name=entity_data["name"],
                type=entity_data["type"],
                description=entity_data["description"]
            )
            db.add(entity)

        db.commit()

        return {
            "status": "success",
            "manuscript_id": manuscript.id,
            "chapters_imported": len(maxwell_data["chapters"]),
            "entities_imported": len(maxwell_data["entities"])
        }

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

### 3.3 Dependencies

Add to `backend/requirements.txt`:
```
striprtf==0.0.26
```

---

## SHORT-TERM PRIORITY (1-3 Months)

---

## Feature 4: Character Voice Consistency Analyzer

**Objective:** Analyze dialogue patterns per character to detect voice inconsistencies.

**Effort:** 10-12 days

### 4.1 Database Model

**`backend/app/models/voice_profile.py`**
```python
"""Character voice profile models"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer, ForeignKey, Text
from app.database import Base


class CharacterVoiceProfile(Base):
    """Stored voice profile for a character"""
    __tablename__ = "character_voice_profiles"

    id = Column(String, primary_key=True)
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Cached profile data
    profile_data = Column(JSON, default=dict)
    # {
    #   "avg_sentence_length": float,
    #   "vocabulary_complexity": float,
    #   "contraction_rate": float,
    #   "question_rate": float,
    #   "exclamation_rate": float,
    #   "common_phrases": [["phrase", count], ...],
    #   "top_words": ["word1", "word2", ...],
    #   "dialogue_count": int
    # }

    calculated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoiceInconsistency(Base):
    """Detected voice inconsistency"""
    __tablename__ = "voice_inconsistencies"

    id = Column(String, primary_key=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=False)

    inconsistency_type = Column(String)  # VOCABULARY, SENTENCE_LENGTH, FORMALITY
    severity = Column(String)  # HIGH, MEDIUM, LOW

    description = Column(Text)
    dialogue_excerpt = Column(Text)
    expected_value = Column(String)  # What the profile says
    actual_value = Column(String)    # What was found

    suggestion = Column(Text)
    teaching_point = Column(Text)

    is_resolved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 Backend Service

See Plan agent output for full `VoiceAnalysisService` implementation.

### 4.3 API Endpoints

**`backend/app/api/routes/voice_analysis.py`** - Create new file with endpoints for:
- `GET /api/voice-analysis/profile/{character_id}` - Get voice profile
- `POST /api/voice-analysis/analyze/{manuscript_id}` - Run analysis
- `GET /api/voice-analysis/compare/{char_a_id}/{char_b_id}` - Compare voices
- `GET /api/voice-analysis/inconsistencies/{manuscript_id}` - Get issues

---

## Feature 5: Visual Timeline Enhancement

**Objective:** Make timeline visually compelling with character swimlanes and conflict visualization.

**Effort:** 8-10 days

See Plan agent output for component specifications.

---

## Feature 6: Foreshadowing Tracker Expansion

**Objective:** Add auto-detection of setups/payoffs and visual threading.

**Effort:** 7-9 days

See Plan agent output for service and component specifications.

---

## Risk Assessment

| Feature | Risk Level | Primary Risk | Mitigation |
|---------|------------|--------------|------------|
| LanguageTool | Low | Performance on large text | Chunk text, cache results |
| Fast Coach Expansion | Low | False positives | Configurable thresholds |
| Scrivener Import | Medium | Format variations | Test with Scrivener 2 & 3 |
| Voice Consistency | Medium | Dialogue attribution | Use entity linking, allow override |
| Timeline Enhancement | Low | Rendering performance | Virtualization |
| Foreshadowing Detection | Medium | Detection accuracy | Start conservative |

---

## Success Metrics

| Feature | Metric | Target |
|---------|--------|--------|
| LanguageTool | User satisfaction | >80% find it helpful |
| Fast Coach | Issues detected | 30% more than current |
| Scrivener Import | Successful imports | >95% completion rate |
| Voice Consistency | Accuracy | >85% agreement with manual review |
| Timeline | User engagement | 50% of timeline users use enhanced views |
| Foreshadowing | Auto-detection precision | >70% (prioritize precision over recall) |

---

**Document Prepared:** February 3, 2026
**Next Review:** After Week 4 checkpoint
