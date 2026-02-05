"""
Foreshadowing Detector Service

Auto-detects potential foreshadowing setups and payoffs in manuscript text.
Uses pattern matching and NLP to identify narrative promises and their resolutions.
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter

from sqlalchemy.orm import Session

from app.models.manuscript import Manuscript
from app.models.chapter import Chapter
from app.models.foreshadowing import ForeshadowingPair


@dataclass
class DetectedSetup:
    """A potential foreshadowing setup detected in the text"""
    text: str
    chapter_id: str
    chapter_title: str
    start_offset: int
    end_offset: int
    setup_type: str  # CHEKHOV_GUN, PROPHECY, SYMBOL, HINT, PARALLEL
    confidence: float  # 0.0 to 1.0
    context: str  # Surrounding text
    keywords: List[str]
    suggestion: str


@dataclass
class DetectedPayoff:
    """A potential payoff for a setup"""
    text: str
    chapter_id: str
    chapter_title: str
    start_offset: int
    end_offset: int
    setup_reference: str  # The text/element being paid off
    confidence: float
    context: str


@dataclass
class SetupPayoffMatch:
    """A matched pair of setup and potential payoff"""
    setup: DetectedSetup
    payoff: DetectedPayoff
    similarity_score: float
    match_type: str  # KEYWORD, SYMBOL, CHARACTER, OBJECT


class ForeshadowingDetectorService:
    """
    Service for auto-detecting foreshadowing patterns in manuscripts.

    Detection strategies:
    1. Chekhov's Gun - Objects/items mentioned prominently that could be used later
    2. Prophecies - Predictions, dreams, visions that hint at future events
    3. Symbols - Recurring imagery or motifs
    4. Hints - Subtle clues about character intentions or plot developments
    5. Parallels - Scene/situation echoes that create narrative resonance
    """

    # Chekhov's Gun patterns - objects introduced with emphasis
    CHEKHOV_PATTERNS = [
        r'\b(noticed|spotted|saw|observed|eyed)\b.{1,50}\b(gun|knife|weapon|sword|dagger|pistol)\b',
        r'\b(the|a|an)\s+(ancient|old|mysterious|strange|peculiar)\s+\w+\s+(lay|sat|hung|rested|stood)',
        r'\b(prominently|carefully|deliberately)\s+(placed|positioned|displayed|arranged)',
        r'\b(couldn\'t help but notice|caught (?:his|her|their) eye|drew (?:his|her|their) attention)',
        r'\b(gift|inheritance|heirloom|keepsake|memento)\b.{1,30}\b(from|of)\b',
        r'\b(loaded|hidden|concealed|tucked away)\s+\w+\s+\w+',
    ]

    # Prophecy patterns - predictions and visions
    PROPHECY_PATTERNS = [
        r'\b(prophecy|prophesied|foretold|destined|fated)\b',
        r'\b(will|shall)\s+\w+\s+(one day|someday|eventually|in time)',
        r'\b(dreamed?|vision|nightmare)\s+(of|about)\b',
        r'\b(fortune teller|oracle|seer|psychic|medium)\b',
        r'\b(warned?|warning)\s+(of|about|that)\b',
        r'"[^"]*\b(mark my words|you\'ll see|remember this)\b[^"]*"',
        r'\b(it was said|legend has it|according to|the old tales)\b',
    ]

    # Symbol patterns - recurring imagery
    SYMBOL_PATTERNS = [
        r'\b(symbol|emblem|sign|omen|portent)\b',
        r'\b(like a|as if|reminded .{1,20} of)\s+(a\s+)?(raven|crow|dove|owl|wolf|lion|snake|serpent)',
        r'\b(shadow|darkness|light|storm|fire|water)\s+(consumed|enveloped|surrounded|filled)',
        r'\b(broken|shattered|cracked)\s+(mirror|glass|window|clock|watch)',
        r'\b(red|black|white|blood)\s+\w+\s+\w+\s+(stained|covered|spread)',
    ]

    # Hint patterns - subtle clues
    HINT_PATTERNS = [
        r'\b(little did .{1,30} know|if only .{1,30} knew|unknown to)',
        r'\b(would later|would come to|would prove to)\b',
        r'\b(for reasons .{1,20} (unclear|unknown|mysterious)|for some reason)',
        r'\b(something about|there was something|couldn\'t shake the feeling)',
        r'\b(a hint of|a trace of|a glimpse of)\b',
        r'\b(momentary|fleeting|brief)\s+(hesitation|pause|look|glance)',
        r'"[^"]*\.\.\.[^"]*"',  # Trailing off in dialogue
    ]

    # Parallel patterns - echoing scenes
    PARALLEL_PATTERNS = [
        r'\b(just as|much like|similar to|echoed|mirrored)\b',
        r'\b(once again|just like before|as .{1,30} had done before)',
        r'\b(history|story|pattern)\s+(repeating|repeats)',
        r'\b(déjà vu|familiar|same .{1,20} (place|spot|position))',
    ]

    # Keywords that often relate to foreshadowing setups
    SETUP_KEYWORDS = [
        'hidden', 'secret', 'buried', 'forgotten', 'ancient', 'mysterious',
        'strange', 'peculiar', 'ominous', 'foreboding', 'unsettling',
        'warning', 'promise', 'vow', 'oath', 'curse', 'blessing',
        'destiny', 'fate', 'doom', 'ruin', 'salvation'
    ]

    # Keywords that often indicate payoffs
    PAYOFF_KEYWORDS = [
        'finally', 'at last', 'remembered', 'realized', 'understood',
        'fulfilled', 'came true', 'prophesied', 'predicted', 'warned',
        'revealed', 'discovered', 'unmasked', 'truth', 'answer'
    ]

    def __init__(self, db: Session):
        self.db = db

    def detect_foreshadowing(
        self,
        manuscript_id: str,
        chapter_ids: Optional[List[str]] = None,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Detect potential foreshadowing in a manuscript.

        Args:
            manuscript_id: The manuscript to analyze
            chapter_ids: Optional list of specific chapters to analyze
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            {
                "setups": List of detected setups,
                "payoffs": List of detected payoffs,
                "matches": List of potential setup-payoff matches,
                "suggestions": Writing advice based on findings
            }
        """
        # Get manuscript
        manuscript = self.db.query(Manuscript).filter(
            Manuscript.id == manuscript_id
        ).first()

        if not manuscript:
            raise ValueError(f"Manuscript {manuscript_id} not found")

        # Get chapters
        query = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id
        )
        if chapter_ids:
            query = query.filter(Chapter.id.in_(chapter_ids))

        chapters = query.order_by(Chapter.order).all()

        all_setups: List[DetectedSetup] = []
        all_payoffs: List[DetectedPayoff] = []

        # Analyze each chapter
        for chapter in chapters:
            if not chapter.content:
                continue

            # Detect setups
            setups = self._detect_setups(chapter)
            all_setups.extend([s for s in setups if s.confidence >= min_confidence])

            # Detect payoffs
            payoffs = self._detect_payoffs(chapter, all_setups)
            all_payoffs.extend([p for p in payoffs if p.confidence >= min_confidence])

        # Match setups with payoffs
        matches = self._match_setups_payoffs(all_setups, all_payoffs)

        # Generate suggestions
        suggestions = self._generate_suggestions(all_setups, all_payoffs, matches)

        return {
            "setups": [self._setup_to_dict(s) for s in all_setups],
            "payoffs": [self._payoff_to_dict(p) for p in all_payoffs],
            "matches": [self._match_to_dict(m) for m in matches],
            "suggestions": suggestions,
            "stats": {
                "total_setups": len(all_setups),
                "total_payoffs": len(all_payoffs),
                "matched_pairs": len(matches),
                "unmatched_setups": len(all_setups) - len(matches),
            }
        }

    def _detect_setups(self, chapter: Chapter) -> List[DetectedSetup]:
        """Detect potential foreshadowing setups in a chapter"""
        setups: List[DetectedSetup] = []
        content = chapter.content or ""

        # Detect Chekhov's Guns
        for pattern in self.CHEKHOV_PATTERNS:
            setups.extend(
                self._find_pattern_matches(
                    content, pattern, chapter, "CHEKHOV_GUN",
                    "This object/item is introduced with emphasis - consider if it needs a payoff later."
                )
            )

        # Detect Prophecies
        for pattern in self.PROPHECY_PATTERNS:
            setups.extend(
                self._find_pattern_matches(
                    content, pattern, chapter, "PROPHECY",
                    "Predictions and visions create reader expectations - ensure they're addressed."
                )
            )

        # Detect Symbols
        for pattern in self.SYMBOL_PATTERNS:
            setups.extend(
                self._find_pattern_matches(
                    content, pattern, chapter, "SYMBOL",
                    "Recurring symbols can add depth - track this imagery for consistency."
                )
            )

        # Detect Hints
        for pattern in self.HINT_PATTERNS:
            setups.extend(
                self._find_pattern_matches(
                    content, pattern, chapter, "HINT",
                    "This subtle clue may set reader expectations - consider its payoff."
                )
            )

        # Detect Parallels
        for pattern in self.PARALLEL_PATTERNS:
            setups.extend(
                self._find_pattern_matches(
                    content, pattern, chapter, "PARALLEL",
                    "Scene echoes create narrative resonance - ensure intentional parallels."
                )
            )

        return setups

    def _find_pattern_matches(
        self,
        content: str,
        pattern: str,
        chapter: Chapter,
        setup_type: str,
        suggestion: str
    ) -> List[DetectedSetup]:
        """Find all matches of a pattern in content"""
        setups: List[DetectedSetup] = []

        try:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                # Get context (surrounding text)
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]

                # Extract keywords from match
                keywords = [w.lower() for w in re.findall(r'\b\w+\b', match.group())
                           if len(w) > 3 and w.lower() in self.SETUP_KEYWORDS]

                # Calculate confidence based on pattern specificity and keywords
                confidence = self._calculate_setup_confidence(
                    match.group(), context, setup_type, keywords
                )

                setups.append(DetectedSetup(
                    text=match.group(),
                    chapter_id=chapter.id,
                    chapter_title=chapter.title or f"Chapter {chapter.order}",
                    start_offset=match.start(),
                    end_offset=match.end(),
                    setup_type=setup_type,
                    confidence=confidence,
                    context=context,
                    keywords=keywords,
                    suggestion=suggestion
                ))
        except re.error:
            # Invalid regex pattern
            pass

        return setups

    def _calculate_setup_confidence(
        self,
        text: str,
        context: str,
        setup_type: str,
        keywords: List[str]
    ) -> float:
        """Calculate confidence score for a detected setup"""
        confidence = 0.5  # Base confidence

        # Boost for matching keywords
        keyword_matches = sum(1 for kw in self.SETUP_KEYWORDS if kw in text.lower())
        confidence += min(keyword_matches * 0.1, 0.3)

        # Boost for context keywords
        context_keywords = sum(1 for kw in self.SETUP_KEYWORDS if kw in context.lower())
        confidence += min(context_keywords * 0.05, 0.15)

        # Boost for specific setup types
        if setup_type == "CHEKHOV_GUN":
            # Chekhov's guns are more reliable detections
            confidence += 0.1
        elif setup_type == "PROPHECY":
            confidence += 0.15

        # Check for dialogue (higher confidence if in dialogue)
        if '"' in text or "'" in text:
            confidence += 0.05

        return min(confidence, 1.0)

    def _detect_payoffs(
        self,
        chapter: Chapter,
        prior_setups: List[DetectedSetup]
    ) -> List[DetectedPayoff]:
        """Detect potential payoffs based on prior setups"""
        payoffs: List[DetectedPayoff] = []
        content = chapter.content or ""

        # Look for payoff keywords
        for match in re.finditer(
            r'\b(' + '|'.join(self.PAYOFF_KEYWORDS) + r')\b.{1,100}',
            content,
            re.IGNORECASE
        ):
            # Check if this might be paying off a prior setup
            context = content[max(0, match.start()-100):min(len(content), match.end()+100)]

            # Look for references to prior setups
            for setup in prior_setups:
                # Check for keyword overlap
                overlap = self._calculate_keyword_overlap(setup.keywords, context)

                if overlap > 0.3:
                    payoffs.append(DetectedPayoff(
                        text=match.group(),
                        chapter_id=chapter.id,
                        chapter_title=chapter.title or f"Chapter {chapter.order}",
                        start_offset=match.start(),
                        end_offset=match.end(),
                        setup_reference=setup.text[:50],
                        confidence=0.5 + overlap * 0.5,
                        context=context
                    ))

        return payoffs

    def _calculate_keyword_overlap(
        self,
        setup_keywords: List[str],
        payoff_context: str
    ) -> float:
        """Calculate keyword overlap between setup and potential payoff"""
        if not setup_keywords:
            return 0.0

        payoff_words = set(w.lower() for w in re.findall(r'\b\w+\b', payoff_context))
        overlap = sum(1 for kw in setup_keywords if kw in payoff_words)

        return overlap / len(setup_keywords)

    def _match_setups_payoffs(
        self,
        setups: List[DetectedSetup],
        payoffs: List[DetectedPayoff]
    ) -> List[SetupPayoffMatch]:
        """Match detected setups with their potential payoffs"""
        matches: List[SetupPayoffMatch] = []

        for setup in setups:
            best_payoff = None
            best_score = 0.0

            for payoff in payoffs:
                # Calculate similarity
                score = self._calculate_match_score(setup, payoff)

                if score > best_score and score > 0.4:
                    best_score = score
                    best_payoff = payoff

            if best_payoff:
                matches.append(SetupPayoffMatch(
                    setup=setup,
                    payoff=best_payoff,
                    similarity_score=best_score,
                    match_type=self._determine_match_type(setup, best_payoff)
                ))

        return matches

    def _calculate_match_score(
        self,
        setup: DetectedSetup,
        payoff: DetectedPayoff
    ) -> float:
        """Calculate how well a payoff matches a setup"""
        score = 0.0

        # Keyword overlap
        setup_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', setup.text + " " + setup.context))
        payoff_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', payoff.text + " " + payoff.context))

        common_words = setup_words & payoff_words
        if setup_words:
            score += len(common_words) / len(setup_words) * 0.4

        # Check if payoff is after setup (chapter-wise)
        # For simplicity, assume chapter order corresponds to story order

        # Type-specific matching
        if setup.setup_type == "CHEKHOV_GUN":
            # Look for object usage
            object_pattern = r'\b(used|wielded|grabbed|pulled|drew|fired|threw)\b'
            if re.search(object_pattern, payoff.context, re.IGNORECASE):
                score += 0.3

        elif setup.setup_type == "PROPHECY":
            # Look for fulfillment language
            fulfillment_pattern = r'\b(came true|fulfilled|proved|as (foretold|predicted))\b'
            if re.search(fulfillment_pattern, payoff.context, re.IGNORECASE):
                score += 0.3

        # Confidence boost
        score += (setup.confidence + payoff.confidence) / 10

        return min(score, 1.0)

    def _determine_match_type(
        self,
        setup: DetectedSetup,
        payoff: DetectedPayoff
    ) -> str:
        """Determine the type of setup-payoff match"""
        if setup.setup_type == "CHEKHOV_GUN":
            return "OBJECT"
        elif setup.setup_type == "PROPHECY":
            return "PROPHECY"
        elif setup.setup_type == "SYMBOL":
            return "SYMBOL"
        elif setup.setup_type == "PARALLEL":
            return "PARALLEL"
        else:
            return "KEYWORD"

    def _generate_suggestions(
        self,
        setups: List[DetectedSetup],
        payoffs: List[DetectedPayoff],
        matches: List[SetupPayoffMatch]
    ) -> List[Dict[str, str]]:
        """Generate writing suggestions based on findings"""
        suggestions: List[Dict[str, str]] = []

        matched_setup_ids = {id(m.setup) for m in matches}
        unmatched_setups = [s for s in setups if id(s) not in matched_setup_ids]

        # Warn about unresolved Chekhov's Guns
        chekhov_unresolved = [s for s in unmatched_setups if s.setup_type == "CHEKHOV_GUN"]
        if chekhov_unresolved:
            suggestions.append({
                "type": "warning",
                "title": "Chekhov's Gun Violation",
                "message": f"Found {len(chekhov_unresolved)} objects introduced with emphasis that may lack payoff. "
                          f"Remember: if you show a gun in Act 1, it should fire by Act 3.",
                "count": len(chekhov_unresolved)
            })

        # Warn about unfulfilled prophecies
        prophecy_unresolved = [s for s in unmatched_setups if s.setup_type == "PROPHECY"]
        if prophecy_unresolved:
            suggestions.append({
                "type": "warning",
                "title": "Unfulfilled Prophecies",
                "message": f"Found {len(prophecy_unresolved)} predictions or visions without clear resolution. "
                          f"Prophecies create strong reader expectations - ensure they're addressed.",
                "count": len(prophecy_unresolved)
            })

        # Positive feedback for good matches
        if len(matches) > 0:
            suggestions.append({
                "type": "success",
                "title": "Well-Connected Narrative",
                "message": f"Found {len(matches)} potential setup-payoff connections. "
                          f"Good foreshadowing creates satisfying narrative echoes.",
                "count": len(matches)
            })

        # Symbol tracking suggestion
        symbol_setups = [s for s in setups if s.setup_type == "SYMBOL"]
        if len(symbol_setups) > 2:
            suggestions.append({
                "type": "info",
                "title": "Symbolic Patterns Detected",
                "message": f"Found {len(symbol_setups)} symbolic elements. "
                          f"Consider tracking these to ensure consistent thematic resonance.",
                "count": len(symbol_setups)
            })

        return suggestions

    def _setup_to_dict(self, setup: DetectedSetup) -> Dict[str, Any]:
        """Convert DetectedSetup to dictionary"""
        return {
            "text": setup.text,
            "chapter_id": setup.chapter_id,
            "chapter_title": setup.chapter_title,
            "start_offset": setup.start_offset,
            "end_offset": setup.end_offset,
            "setup_type": setup.setup_type,
            "confidence": round(setup.confidence, 2),
            "context": setup.context,
            "keywords": setup.keywords,
            "suggestion": setup.suggestion,
        }

    def _payoff_to_dict(self, payoff: DetectedPayoff) -> Dict[str, Any]:
        """Convert DetectedPayoff to dictionary"""
        return {
            "text": payoff.text,
            "chapter_id": payoff.chapter_id,
            "chapter_title": payoff.chapter_title,
            "start_offset": payoff.start_offset,
            "end_offset": payoff.end_offset,
            "setup_reference": payoff.setup_reference,
            "confidence": round(payoff.confidence, 2),
            "context": payoff.context,
        }

    def _match_to_dict(self, match: SetupPayoffMatch) -> Dict[str, Any]:
        """Convert SetupPayoffMatch to dictionary"""
        return {
            "setup": self._setup_to_dict(match.setup),
            "payoff": self._payoff_to_dict(match.payoff),
            "similarity_score": round(match.similarity_score, 2),
            "match_type": match.match_type,
        }

    def create_foreshadowing_from_detection(
        self,
        manuscript_id: str,
        setup_data: Dict[str, Any],
        payoff_data: Optional[Dict[str, Any]] = None
    ) -> ForeshadowingPair:
        """
        Create a ForeshadowingPair from detection results.

        This allows users to confirm auto-detected foreshadowing and
        save it to the database for tracking.
        """
        # Find the event for the setup chapter
        from app.models.timeline_event import TimelineEvent

        # Try to find a related event
        setup_event = self.db.query(TimelineEvent).filter(
            TimelineEvent.manuscript_id == manuscript_id,
            TimelineEvent.chapter_id == setup_data["chapter_id"]
        ).first()

        payoff_event = None
        if payoff_data:
            payoff_event = self.db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == manuscript_id,
                TimelineEvent.chapter_id == payoff_data["chapter_id"]
            ).first()

        pair = ForeshadowingPair(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            foreshadowing_event_id=setup_event.id if setup_event else None,
            payoff_event_id=payoff_event.id if payoff_event else None,
            foreshadowing_type=setup_data.get("setup_type", "HINT"),
            foreshadowing_text=setup_data["text"],
            payoff_text=payoff_data["text"] if payoff_data else None,
            is_resolved=1 if payoff_data else 0,
            confidence=int(setup_data.get("confidence", 0.5) * 10),
            notes=f"Auto-detected: {setup_data.get('suggestion', '')}",
            created_at=datetime.utcnow(),
        )

        self.db.add(pair)
        self.db.commit()

        return pair
