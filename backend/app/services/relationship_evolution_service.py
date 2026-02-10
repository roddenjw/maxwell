"""
Relationship Evolution Service - Track how relationships change over time.

Analyzes:
- Relationship state changes through the story
- Unearned relationship shifts
- Relationship timeline visualization data
- Wiki integration for relationship tracking
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import re
import uuid

from app.models.manuscript import Chapter
from app.models.entity import Entity, Relationship
from app.models.wiki import WikiEntry, WikiEntryType, WikiCrossReference
from app.services.wiki_service import WikiService


# ==================== Relationship States ====================

class RelationshipState:
    """Possible states for a relationship"""
    STRANGERS = "strangers"
    ACQUAINTANCES = "acquaintances"
    FRIENDS = "friends"
    CLOSE_FRIENDS = "close_friends"
    ROMANTIC_INTEREST = "romantic_interest"
    DATING = "dating"
    COMMITTED = "committed"
    MARRIED = "married"
    ESTRANGED = "estranged"
    ENEMIES = "enemies"
    RIVALS = "rivals"
    ALLIES = "allies"
    MENTOR_STUDENT = "mentor_student"
    FAMILY = "family"
    PROFESSIONAL = "professional"
    NEUTRAL = "neutral"


# State progression paths (what can naturally follow what)
STATE_PROGRESSIONS = {
    RelationshipState.STRANGERS: [
        RelationshipState.ACQUAINTANCES,
        RelationshipState.ENEMIES,
        RelationshipState.NEUTRAL
    ],
    RelationshipState.ACQUAINTANCES: [
        RelationshipState.FRIENDS,
        RelationshipState.RIVALS,
        RelationshipState.ROMANTIC_INTEREST,
        RelationshipState.PROFESSIONAL,
        RelationshipState.NEUTRAL
    ],
    RelationshipState.FRIENDS: [
        RelationshipState.CLOSE_FRIENDS,
        RelationshipState.ROMANTIC_INTEREST,
        RelationshipState.ACQUAINTANCES,
        RelationshipState.RIVALS,
        RelationshipState.ALLIES
    ],
    RelationshipState.CLOSE_FRIENDS: [
        RelationshipState.ROMANTIC_INTEREST,
        RelationshipState.FRIENDS,
        RelationshipState.ESTRANGED,
        RelationshipState.ALLIES
    ],
    RelationshipState.ROMANTIC_INTEREST: [
        RelationshipState.DATING,
        RelationshipState.FRIENDS,
        RelationshipState.ESTRANGED,
        RelationshipState.RIVALS
    ],
    RelationshipState.DATING: [
        RelationshipState.COMMITTED,
        RelationshipState.FRIENDS,
        RelationshipState.ESTRANGED,
        RelationshipState.ROMANTIC_INTEREST
    ],
    RelationshipState.COMMITTED: [
        RelationshipState.MARRIED,
        RelationshipState.ESTRANGED,
        RelationshipState.DATING
    ],
    RelationshipState.MARRIED: [
        RelationshipState.ESTRANGED,
        RelationshipState.COMMITTED
    ],
    RelationshipState.ESTRANGED: [
        RelationshipState.ENEMIES,
        RelationshipState.NEUTRAL,
        RelationshipState.ACQUAINTANCES,
        RelationshipState.FRIENDS  # Reconciliation
    ],
    RelationshipState.ENEMIES: [
        RelationshipState.RIVALS,
        RelationshipState.NEUTRAL,
        RelationshipState.ALLIES  # Redemption arc
    ],
    RelationshipState.RIVALS: [
        RelationshipState.ENEMIES,
        RelationshipState.FRIENDS,
        RelationshipState.ALLIES
    ],
    RelationshipState.ALLIES: [
        RelationshipState.FRIENDS,
        RelationshipState.RIVALS,
        RelationshipState.NEUTRAL
    ],
    RelationshipState.MENTOR_STUDENT: [
        RelationshipState.FRIENDS,
        RelationshipState.ALLIES,
        RelationshipState.ESTRANGED
    ],
    RelationshipState.FAMILY: [
        RelationshipState.ESTRANGED,
        RelationshipState.CLOSE_FRIENDS
    ],
    RelationshipState.PROFESSIONAL: [
        RelationshipState.FRIENDS,
        RelationshipState.RIVALS,
        RelationshipState.ALLIES,
        RelationshipState.NEUTRAL
    ],
    RelationshipState.NEUTRAL: [
        RelationshipState.ACQUAINTANCES,
        RelationshipState.ALLIES,
        RelationshipState.RIVALS
    ],
}

# Patterns that indicate relationship states
STATE_PATTERNS = {
    RelationshipState.FRIENDS: [
        r'(?:became|were|are)\s+friends',
        r'friendship',
        r'buddy|buddies|pal|pals',
        r'trusted\s+(?:him|her|them)',
    ],
    RelationshipState.ROMANTIC_INTEREST: [
        r'(?:attracted\s+to|crush\s+on|feelings\s+for)',
        r'couldn\'t\s+stop\s+(?:thinking|looking)',
        r'heart\s+(?:raced|fluttered|skipped)',
        r'butterflies',
    ],
    RelationshipState.DATING: [
        r'(?:started|began)\s+(?:dating|seeing)',
        r'(?:boyfriend|girlfriend)',
        r'(?:first|second|third)\s+date',
        r'going\s+out',
    ],
    RelationshipState.COMMITTED: [
        r'(?:engaged|engagement)',
        r'moved\s+in\s+together',
        r'partner',
        r'committed',
    ],
    RelationshipState.MARRIED: [
        r'(?:married|wedding|wed)',
        r'(?:husband|wife|spouse)',
        r'honeymoon',
    ],
    RelationshipState.ESTRANGED: [
        r'(?:broke\s+up|broken\s+up)',
        r'(?:separated|separation)',
        r'(?:stopped\s+talking|not\s+speaking)',
        r'betrayed?',
        r'couldn\'t\s+forgive',
    ],
    RelationshipState.ENEMIES: [
        r'(?:hated?|despised?)',
        r'(?:enemy|enemies|nemesis)',
        r'(?:sworn\s+to\s+(?:kill|destroy))',
        r'mortal\s+(?:enemy|foe)',
    ],
    RelationshipState.RIVALS: [
        r'(?:rival|rivalry)',
        r'(?:competed|competition)',
        r'(?:one-up|outdo)',
    ],
    RelationshipState.ALLIES: [
        r'(?:allied|alliance)',
        r'(?:joined\s+forces|teamed\s+up)',
        r'(?:common\s+(?:enemy|goal))',
    ],
    RelationshipState.MENTOR_STUDENT: [
        r'(?:mentor|mentored)',
        r'(?:apprentice|student)',
        r'(?:taught|teaching)',
        r'(?:learned\s+from)',
    ],
}


class RelationshipEvolutionService:
    """Tracks relationship evolution through a manuscript"""

    def __init__(self, db: Session):
        self.db = db
        self.wiki_service = WikiService(db)

    # ==================== State Detection ====================

    def detect_relationship_state(
        self,
        text: str,
        char_a: str,
        char_b: str
    ) -> Dict[str, Any]:
        """
        Detect the relationship state between two characters in a text passage.

        Returns:
        {
            "detected_state": str,
            "confidence": float,
            "indicators_found": List[str],
            "context_excerpts": List[str]
        }
        """
        text_lower = text.lower()
        state_scores = {}
        indicators = []
        excerpts = []

        # Check if both characters are mentioned
        char_a_present = char_a.lower() in text_lower
        char_b_present = char_b.lower() in text_lower

        if not (char_a_present and char_b_present):
            return {
                "detected_state": None,
                "confidence": 0.0,
                "indicators_found": [],
                "context_excerpts": [],
                "note": "Both characters not present in text"
            }

        # Score each state based on patterns
        for state, patterns in STATE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches)
                    indicators.append(f"{state}: {pattern[:30]}")

                    # Get context excerpt
                    for match in re.finditer(pattern, text_lower):
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        excerpts.append(text[start:end])

            if score > 0:
                state_scores[state] = score

        if not state_scores:
            return {
                "detected_state": RelationshipState.NEUTRAL,
                "confidence": 0.3,
                "indicators_found": [],
                "context_excerpts": [],
                "note": "No clear relationship indicators found"
            }

        # Find dominant state
        total = sum(state_scores.values())
        sorted_states = sorted(state_scores.items(), key=lambda x: x[1], reverse=True)
        dominant = sorted_states[0]

        return {
            "detected_state": dominant[0],
            "confidence": round(dominant[1] / total, 2) if total > 0 else 0,
            "all_states": {k: round(v / total, 2) for k, v in state_scores.items()},
            "indicators_found": indicators[:5],
            "context_excerpts": excerpts[:3]
        }

    # ==================== Evolution Tracking ====================

    def track_relationship_evolution(
        self,
        manuscript_id: str,
        char_a: str,
        char_b: str
    ) -> Dict[str, Any]:
        """
        Track how a relationship evolves across chapters.

        Returns timeline of relationship states with chapter positions.
        """
        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).order_by(Chapter.order_index).all()

        if not chapters:
            return {"error": "No chapters found"}

        evolution = []
        previous_state = RelationshipState.STRANGERS
        state_changes = []

        for chapter in chapters:
            if not chapter.content:
                continue

            detection = self.detect_relationship_state(
                chapter.content,
                char_a,
                char_b
            )

            current_state = detection.get('detected_state')

            if current_state and current_state != previous_state:
                # Check if this is a natural progression
                is_natural = self._is_natural_progression(previous_state, current_state)

                state_changes.append({
                    "chapter_id": chapter.id,
                    "chapter_title": chapter.title,
                    "chapter_index": chapter.order_index,
                    "from_state": previous_state,
                    "to_state": current_state,
                    "is_natural_progression": is_natural,
                    "confidence": detection.get('confidence', 0),
                    "excerpts": detection.get('context_excerpts', [])[:2]
                })

                previous_state = current_state

            evolution.append({
                "chapter_id": chapter.id,
                "chapter_title": chapter.title,
                "chapter_index": chapter.order_index,
                "state": current_state or previous_state,
                "confidence": detection.get('confidence', 0)
            })

        # Analyze the evolution
        unearned_changes = [c for c in state_changes if not c['is_natural_progression']]

        return {
            "manuscript_id": manuscript_id,
            "character_a": char_a,
            "character_b": char_b,
            "starting_state": evolution[0]['state'] if evolution else RelationshipState.STRANGERS,
            "ending_state": evolution[-1]['state'] if evolution else RelationshipState.STRANGERS,
            "total_state_changes": len(state_changes),
            "unearned_changes": len(unearned_changes),
            "evolution_timeline": evolution,
            "state_changes": state_changes,
            "unearned_change_details": unearned_changes,
            "health": self._calculate_relationship_health(state_changes, unearned_changes)
        }

    def _is_natural_progression(self, from_state: str, to_state: str) -> bool:
        """Check if a state transition is natural/expected"""
        if from_state == to_state:
            return True

        allowed = STATE_PROGRESSIONS.get(from_state, [])
        return to_state in allowed

    def _calculate_relationship_health(
        self,
        state_changes: List[Dict],
        unearned_changes: List[Dict]
    ) -> str:
        """Calculate overall health of relationship development"""
        if not state_changes:
            return "static"  # No changes at all

        unearned_ratio = len(unearned_changes) / len(state_changes) if state_changes else 0

        if unearned_ratio > 0.5:
            return "poor"  # More than half are unearned
        elif unearned_ratio > 0.2:
            return "fair"
        elif len(state_changes) > 0:
            return "healthy"
        else:
            return "static"

    # ==================== Manuscript-Wide Analysis ====================

    def analyze_all_relationships(
        self,
        manuscript_id: str,
        world_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze all character relationships in a manuscript"""
        # Get all characters
        characters = self.db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id,
            Entity.entity_type == "CHARACTER"
        ).all()

        if len(characters) < 2:
            return {"error": "Need at least 2 characters for relationship analysis"}

        character_names = [c.name for c in characters]

        # Get existing relationships from database
        relationships = self.db.query(Relationship).filter(
            Relationship.manuscript_id == manuscript_id
        ).all()

        # Track pairs we've analyzed
        analyzed_pairs = set()
        all_evolutions = []

        # First analyze existing relationships
        for rel in relationships:
            source = self.db.query(Entity).filter(Entity.id == rel.source_entity_id).first()
            target = self.db.query(Entity).filter(Entity.id == rel.target_entity_id).first()

            if source and target:
                pair_key = tuple(sorted([source.name, target.name]))
                if pair_key not in analyzed_pairs:
                    evolution = self.track_relationship_evolution(
                        manuscript_id,
                        source.name,
                        target.name
                    )
                    if 'error' not in evolution:
                        all_evolutions.append(evolution)
                    analyzed_pairs.add(pair_key)

        # Analyze remaining important pairs (main characters)
        main_chars = character_names[:5]  # Limit to top 5 characters
        for i, char_a in enumerate(main_chars):
            for char_b in main_chars[i + 1:]:
                pair_key = tuple(sorted([char_a, char_b]))
                if pair_key not in analyzed_pairs:
                    evolution = self.track_relationship_evolution(
                        manuscript_id,
                        char_a,
                        char_b
                    )
                    if 'error' not in evolution and evolution.get('total_state_changes', 0) > 0:
                        all_evolutions.append(evolution)
                    analyzed_pairs.add(pair_key)

        # Summary statistics
        total_unearned = sum(e.get('unearned_changes', 0) for e in all_evolutions)
        total_changes = sum(e.get('total_state_changes', 0) for e in all_evolutions)

        return {
            "manuscript_id": manuscript_id,
            "relationships_analyzed": len(all_evolutions),
            "total_state_changes": total_changes,
            "total_unearned_changes": total_unearned,
            "unearned_ratio": round(total_unearned / total_changes, 2) if total_changes > 0 else 0,
            "relationships": all_evolutions,
            "health_summary": {
                "healthy": len([e for e in all_evolutions if e.get('health') == 'healthy']),
                "fair": len([e for e in all_evolutions if e.get('health') == 'fair']),
                "poor": len([e for e in all_evolutions if e.get('health') == 'poor']),
                "static": len([e for e in all_evolutions if e.get('health') == 'static']),
            },
            "analyzed_at": datetime.utcnow().isoformat()
        }

    # ==================== Wiki Integration ====================

    def sync_relationship_to_wiki(
        self,
        evolution: Dict[str, Any],
        world_id: str
    ) -> Optional[WikiCrossReference]:
        """Create or update wiki cross-reference for a relationship"""
        char_a = evolution.get('character_a')
        char_b = evolution.get('character_b')

        if not char_a or not char_b:
            return None

        # Find wiki entries for both characters
        entry_a = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title == char_a
        ).first()

        entry_b = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title == char_b
        ).first()

        if not entry_a or not entry_b:
            return None

        # Map ending state to reference type
        ending_state = evolution.get('ending_state', RelationshipState.NEUTRAL)
        ref_type = self._state_to_reference_type(ending_state)

        # Create context from evolution
        context = f"Relationship evolved from {evolution.get('starting_state')} to {ending_state}"
        if evolution.get('total_state_changes', 0) > 0:
            context += f" over {evolution.get('total_state_changes')} changes"

        # Check for existing reference
        existing = self.db.query(WikiCrossReference).filter(
            WikiCrossReference.source_entry_id == entry_a.id,
            WikiCrossReference.target_entry_id == entry_b.id
        ).first()

        if existing:
            # Update existing reference
            existing.reference_type = ref_type
            existing.context = context
            self.db.commit()
            return existing
        else:
            # Create new reference
            return self.wiki_service.create_reference(
                source_entry_id=entry_a.id,
                target_entry_id=entry_b.id,
                reference_type=ref_type,
                context=context,
                bidirectional=True,
                created_by="ai"
            )

    def _state_to_reference_type(self, state: str) -> str:
        """Map relationship state to wiki reference type"""
        mapping = {
            RelationshipState.FRIENDS: "ally_of",
            RelationshipState.CLOSE_FRIENDS: "ally_of",
            RelationshipState.ROMANTIC_INTEREST: "related_to",
            RelationshipState.DATING: "related_to",
            RelationshipState.COMMITTED: "related_to",
            RelationshipState.MARRIED: "related_to",
            RelationshipState.ENEMIES: "enemy_of",
            RelationshipState.RIVALS: "conflicts_with",
            RelationshipState.ALLIES: "ally_of",
            RelationshipState.MENTOR_STUDENT: "related_to",
            RelationshipState.FAMILY: "related_to",
            RelationshipState.ESTRANGED: "conflicts_with",
        }
        return mapping.get(state, "related_to")

    # ==================== Suggestions ====================

    def get_relationship_suggestions(
        self,
        evolution: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate suggestions for improving relationship development"""
        suggestions = []

        # Unearned changes
        unearned = evolution.get('unearned_change_details', [])
        for change in unearned:
            suggestions.append({
                "type": "unearned_change",
                "severity": "high",
                "title": f"Sudden Shift: {change['from_state']} to {change['to_state']}",
                "description": f"In chapter '{change['chapter_title']}', the relationship jumps from {change['from_state']} to {change['to_state']} without clear development",
                "fix": f"Add transitional scenes showing how the characters moved from {change['from_state']} to {change['to_state']}. Consider intermediate states like {', '.join(STATE_PROGRESSIONS.get(change['from_state'], ['...'])[:2])}"
            })

        # Static relationship
        if evolution.get('health') == 'static' and evolution.get('total_state_changes', 0) == 0:
            suggestions.append({
                "type": "static_relationship",
                "severity": "medium",
                "title": "Relationship Never Changes",
                "description": f"The relationship between {evolution.get('character_a')} and {evolution.get('character_b')} remains static throughout",
                "fix": "Consider adding relationship development to make both characters more dynamic and give readers emotional investment in their connection"
            })

        # Too many changes
        if evolution.get('total_state_changes', 0) > 5:
            suggestions.append({
                "type": "too_volatile",
                "severity": "low",
                "title": "Relationship Changes Frequently",
                "description": f"The relationship changes {evolution.get('total_state_changes')} times, which may feel unstable",
                "fix": "Consider consolidating some relationship beats. Readers need time to adjust to each new relationship state."
            })

        return suggestions
