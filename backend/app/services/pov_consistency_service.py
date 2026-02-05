"""
POV Consistency Service - Detect POV and head-hopping issues.

Analyzes text to identify:
- POV per scene/chapter
- Head-hopping (multiple POVs in a single scene)
- POV-inappropriate knowledge (character knows too much)
- Consistent POV voice markers
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import re
import uuid

from app.models.manuscript import Chapter
from app.models.entity import Entity
from app.services.nlp_service import nlp_service


# ==================== POV Indicators ====================

# First person indicators
FIRST_PERSON_MARKERS = [
    r'\bI\b', r'\bme\b', r'\bmy\b', r'\bmyself\b', r'\bmine\b',
    r'\bwe\b', r'\bus\b', r'\bour\b', r'\bourselves\b'
]

# Third person limited indicators (internal thought markers)
THIRD_PERSON_INTERNAL = [
    r'(he|she)\s+thought', r'(he|she)\s+wondered', r'(he|she)\s+knew',
    r'(he|she)\s+felt', r'(he|she)\s+realized', r'(he|she)\s+remembered',
    r'(his|her)\s+mind', r'(his|her)\s+heart', r'(his|her)\s+gut',
    r'to\s+(himself|herself)', r'(he|she)\s+hoped', r'(he|she)\s+wished'
]

# Omniscient POV indicators
OMNISCIENT_MARKERS = [
    r'little did (he|she|they) know',
    r'unbeknownst to',
    r'meanwhile,?\s+elsewhere',
    r'at that very moment',
    r'what\s+\w+\s+didn\'t know',
    r'had (he|she) known'
]

# POV Type enum-like
POV_TYPES = {
    'first_person': 'First Person',
    'third_limited': 'Third Person Limited',
    'third_omniscient': 'Third Person Omniscient',
    'second_person': 'Second Person',
    'unknown': 'Unknown'
}


class POVConsistencyService:
    """Analyzes POV consistency across scenes and chapters"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== POV Detection ====================

    def detect_pov_type(self, text: str) -> Dict[str, Any]:
        """
        Detect the POV type used in a text passage.

        Returns:
        {
            "pov_type": "first_person" | "third_limited" | "third_omniscient" | "second_person",
            "confidence": float,
            "indicators_found": List[str],
            "pov_character": str | None
        }
        """
        text_lower = text.lower()
        indicators = {
            'first_person': 0,
            'third_limited': 0,
            'third_omniscient': 0,
            'second_person': 0
        }

        found_markers = []

        # Check first person markers
        for pattern in FIRST_PERSON_MARKERS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                indicators['first_person'] += len(matches)
                if pattern in [r'\bI\b', r'\bmy\b', r'\bme\b']:
                    found_markers.append(f"First person pronoun: {pattern}")

        # Check second person
        second_person_count = len(re.findall(r'\byou\b', text, re.IGNORECASE))
        if second_person_count > 5:  # Threshold for second person
            indicators['second_person'] = second_person_count
            found_markers.append("Second person 'you'")

        # Check third person internal thought markers
        for pattern in THIRD_PERSON_INTERNAL:
            if re.search(pattern, text, re.IGNORECASE):
                indicators['third_limited'] += 3  # Weight internal thought higher
                found_markers.append(f"Internal thought: {pattern[:30]}")

        # Check omniscient markers
        for pattern in OMNISCIENT_MARKERS:
            if re.search(pattern, text, re.IGNORECASE):
                indicators['third_omniscient'] += 5  # Weight omniscient markers higher
                found_markers.append(f"Omniscient marker: {pattern[:30]}")

        # Determine dominant POV
        total = sum(indicators.values())
        if total == 0:
            return {
                "pov_type": "unknown",
                "confidence": 0.0,
                "indicators_found": [],
                "pov_character": None
            }

        # Find the max POV type
        dominant_pov = max(indicators.items(), key=lambda x: x[1])
        pov_type = dominant_pov[0]
        confidence = dominant_pov[1] / total if total > 0 else 0

        # Try to identify POV character for third person
        pov_character = None
        if pov_type in ['third_limited', 'third_omniscient']:
            pov_character = self._identify_pov_character(text)

        return {
            "pov_type": pov_type,
            "confidence": round(confidence, 2),
            "indicators_found": found_markers[:10],
            "pov_character": pov_character
        }

    def _identify_pov_character(self, text: str) -> Optional[str]:
        """Try to identify the POV character from internal thought patterns"""
        # Look for patterns like "Sarah thought", "John's mind"
        patterns = [
            r'([A-Z][a-z]+)\s+(?:thought|wondered|knew|felt|realized)',
            r'([A-Z][a-z]+)\'s\s+(?:mind|heart|gut|thoughts)',
            r'to\s+([A-Z][a-z]+)(?:\'s\s+relief|\'s\s+horror|\'s\s+surprise)',
        ]

        candidates = {}
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                candidates[match] = candidates.get(match, 0) + 1

        if candidates:
            # Return most frequent candidate
            return max(candidates.items(), key=lambda x: x[1])[0]

        return None

    # ==================== Head-Hopping Detection ====================

    def detect_head_hopping(
        self,
        text: str,
        scene_break_pattern: str = r'\n\s*\*\s*\*\s*\*\s*\n|\n\s*#\s*#\s*#\s*\n'
    ) -> Dict[str, Any]:
        """
        Detect head-hopping (POV switches within a scene).

        Returns:
        {
            "has_head_hopping": bool,
            "pov_switches": List[{position, from_pov, to_pov}],
            "scenes_analyzed": int,
            "issues": List[str]
        }
        """
        # Split into scenes
        scenes = re.split(scene_break_pattern, text)

        pov_switches = []
        issues = []

        for scene_idx, scene in enumerate(scenes):
            if len(scene.strip()) < 100:  # Skip very short segments
                continue

            # Split scene into paragraphs
            paragraphs = [p.strip() for p in scene.split('\n\n') if p.strip()]

            if len(paragraphs) < 2:
                continue

            # Track POV through paragraphs
            prev_pov = None
            prev_char = None

            for para_idx, para in enumerate(paragraphs):
                if len(para) < 50:  # Skip very short paragraphs
                    continue

                pov_info = self.detect_pov_type(para)

                if pov_info['pov_type'] == 'unknown':
                    continue

                current_pov = pov_info['pov_type']
                current_char = pov_info['pov_character']

                # Check for POV switch
                if prev_pov and current_pov != prev_pov:
                    if current_pov != 'third_omniscient' and prev_pov != 'third_omniscient':
                        pov_switches.append({
                            "scene_index": scene_idx,
                            "paragraph_index": para_idx,
                            "from_pov": prev_pov,
                            "to_pov": current_pov,
                            "excerpt": para[:100]
                        })
                        issues.append(
                            f"Scene {scene_idx + 1}, para {para_idx + 1}: "
                            f"POV switches from {POV_TYPES[prev_pov]} to {POV_TYPES[current_pov]}"
                        )

                # Check for character switch in third limited
                if (current_pov == 'third_limited' and
                    prev_pov == 'third_limited' and
                    current_char and prev_char and
                    current_char != prev_char):
                    pov_switches.append({
                        "scene_index": scene_idx,
                        "paragraph_index": para_idx,
                        "from_character": prev_char,
                        "to_character": current_char,
                        "excerpt": para[:100]
                    })
                    issues.append(
                        f"Scene {scene_idx + 1}, para {para_idx + 1}: "
                        f"POV character switches from {prev_char} to {current_char}"
                    )

                prev_pov = current_pov
                prev_char = current_char

        return {
            "has_head_hopping": len(pov_switches) > 0,
            "pov_switches": pov_switches,
            "scenes_analyzed": len([s for s in scenes if len(s.strip()) >= 100]),
            "issues": issues
        }

    # ==================== POV-Inappropriate Knowledge ====================

    def detect_inappropriate_knowledge(
        self,
        text: str,
        pov_character: str,
        known_characters: List[str],
        world_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect when POV character seems to know things they shouldn't.

        Looks for:
        - Internal thoughts of other characters
        - Information the POV character couldn't know
        - Descriptions of events POV character wasn't present for
        """
        issues = []

        # Look for other characters' internal states being described
        for char in known_characters:
            if char.lower() == pov_character.lower():
                continue

            # Patterns indicating other character's internal state
            thought_patterns = [
                rf'{char}\s+(?:thought|wondered|knew|felt|realized)',
                rf'{char}\'s\s+(?:mind|heart|thoughts)',
                rf'inside\s+{char}',
                rf'{char}\s+secretly',
            ]

            for pattern in thought_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append({
                        "type": "other_character_thoughts",
                        "character": char,
                        "pattern": pattern,
                        "message": f"POV character ({pov_character}) seems to know {char}'s internal thoughts"
                    })

        # Look for "little did X know" patterns (omniscient intrusion)
        omniscient_intrusions = re.findall(
            rf'little\s+did\s+{pov_character}\s+know',
            text,
            re.IGNORECASE
        )
        if omniscient_intrusions:
            issues.append({
                "type": "omniscient_intrusion",
                "message": "Narrator reveals information POV character doesn't know (breaks limited POV)"
            })

        # Look for scene descriptions where POV character isn't present
        meanwhile_patterns = re.findall(r'meanwhile,?\s+.{0,200}', text, re.IGNORECASE)
        for match in meanwhile_patterns:
            if pov_character.lower() not in match.lower():
                issues.append({
                    "type": "scene_without_pov",
                    "excerpt": match[:100],
                    "message": "Scene described that POV character isn't present for"
                })

        return {
            "pov_character": pov_character,
            "issues_found": len(issues),
            "issues": issues,
            "is_clean": len(issues) == 0
        }

    # ==================== Chapter/Manuscript Analysis ====================

    def analyze_chapter(
        self,
        chapter_id: str
    ) -> Dict[str, Any]:
        """Analyze a chapter for POV consistency"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content:
            return {"error": "No content to analyze"}

        text = chapter.content

        # Detect POV type
        pov_info = self.detect_pov_type(text)

        # Detect head-hopping
        head_hopping = self.detect_head_hopping(text)

        # Get characters from entities if available
        characters = []
        if chapter.manuscript_id:
            entities = self.db.query(Entity).filter(
                Entity.manuscript_id == chapter.manuscript_id,
                Entity.entity_type == "CHARACTER"
            ).all()
            characters = [e.name for e in entities]

        # Detect inappropriate knowledge if POV character identified
        knowledge_issues = {}
        if pov_info['pov_character'] and characters:
            knowledge_issues = self.detect_inappropriate_knowledge(
                text,
                pov_info['pov_character'],
                characters
            )

        # Calculate overall health
        total_issues = (
            len(head_hopping.get('pov_switches', [])) +
            knowledge_issues.get('issues_found', 0)
        )

        health = 'healthy'
        if total_issues > 5:
            health = 'poor'
        elif total_issues > 2:
            health = 'fair'
        elif total_issues > 0:
            health = 'good'

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "pov_info": pov_info,
            "head_hopping": head_hopping,
            "knowledge_issues": knowledge_issues,
            "total_issues": total_issues,
            "health": health,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_manuscript(
        self,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """Analyze an entire manuscript for POV consistency"""
        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).order_by(Chapter.order_index).all()

        if not chapters:
            return {"error": "No chapters found"}

        chapter_analyses = []
        pov_types_found = {}
        total_head_hopping = 0
        total_knowledge_issues = 0

        for chapter in chapters:
            analysis = self.analyze_chapter(chapter.id)
            if 'error' not in analysis:
                chapter_analyses.append(analysis)

                # Track POV types across chapters
                pov_type = analysis['pov_info'].get('pov_type', 'unknown')
                pov_types_found[pov_type] = pov_types_found.get(pov_type, 0) + 1

                total_head_hopping += len(analysis.get('head_hopping', {}).get('pov_switches', []))
                total_knowledge_issues += analysis.get('knowledge_issues', {}).get('issues_found', 0)

        # Determine consistency
        dominant_pov = max(pov_types_found.items(), key=lambda x: x[1]) if pov_types_found else (None, 0)
        is_consistent = dominant_pov[1] == len(chapter_analyses) if chapter_analyses else False

        return {
            "manuscript_id": manuscript_id,
            "chapters_analyzed": len(chapter_analyses),
            "dominant_pov": dominant_pov[0],
            "pov_consistency": {
                "is_consistent": is_consistent,
                "pov_types_found": pov_types_found,
                "dominant_percentage": round(dominant_pov[1] / len(chapter_analyses) * 100, 1) if chapter_analyses else 0
            },
            "total_head_hopping_instances": total_head_hopping,
            "total_knowledge_issues": total_knowledge_issues,
            "chapter_analyses": chapter_analyses,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    # ==================== Get POV Suggestions ====================

    def get_fix_suggestions(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate suggestions for fixing POV issues"""
        suggestions = []

        # Head-hopping fixes
        head_hopping = analysis.get('head_hopping', {})
        if head_hopping.get('has_head_hopping'):
            suggestions.append({
                "type": "head_hopping",
                "severity": "high",
                "title": "Head-Hopping Detected",
                "description": "Multiple POV switches detected within scenes",
                "fix": "Add scene breaks (***) before changing POV, or rewrite from a single character's perspective"
            })

            for switch in head_hopping.get('pov_switches', [])[:3]:
                if 'from_character' in switch:
                    suggestions.append({
                        "type": "character_switch",
                        "severity": "medium",
                        "title": f"POV Character Switch",
                        "description": f"Switches from {switch['from_character']} to {switch['to_character']}",
                        "fix": "Rewrite this section from one character's POV, or add a clear scene break"
                    })

        # Knowledge issues
        knowledge = analysis.get('knowledge_issues', {})
        for issue in knowledge.get('issues', [])[:3]:
            if issue['type'] == 'other_character_thoughts':
                suggestions.append({
                    "type": "inappropriate_knowledge",
                    "severity": "medium",
                    "title": f"POV Violation: {issue['character']}'s Thoughts",
                    "description": issue['message'],
                    "fix": f"Show {issue['character']}'s feelings through observable behavior instead of internal narration"
                })
            elif issue['type'] == 'omniscient_intrusion':
                suggestions.append({
                    "type": "omniscient_intrusion",
                    "severity": "low",
                    "title": "Omniscient Narrator Intrusion",
                    "description": issue['message'],
                    "fix": "Remove narrator commentary that reveals information the POV character doesn't know"
                })

        return suggestions
