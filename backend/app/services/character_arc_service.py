"""
Character Arc Service - Managing character arcs integrated with Wiki and Outline.

Provides:
- Arc creation from templates
- Arc mapping to outline beats
- Arc detection from manuscript analysis
- Planned vs detected arc comparison
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import re

from app.models.character_arc import CharacterArc, ArcTemplate, ARC_TEMPLATE_DEFINITIONS
from app.models.wiki import WikiEntry, WikiEntryType
from app.models.outline import Outline, PlotBeat


class CharacterArcService:
    """Service for managing character arcs"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Arc CRUD ====================

    def create_arc(
        self,
        wiki_entry_id: str,
        manuscript_id: str,
        arc_template: str = ArcTemplate.CUSTOM.value,
        arc_name: Optional[str] = None,
        planned_arc: Optional[Dict] = None,
        custom_stages: Optional[List[Dict]] = None
    ) -> CharacterArc:
        """Create a new character arc"""
        arc = CharacterArc(
            id=str(uuid.uuid4()),
            wiki_entry_id=wiki_entry_id,
            manuscript_id=manuscript_id,
            arc_template=arc_template,
            arc_name=arc_name,
            planned_arc=planned_arc or {},
            detected_arc={},
            arc_beats=[],
            custom_stages=custom_stages or [],
            arc_completion=0.0,
            arc_health="healthy",
            created_at=datetime.utcnow()
        )
        self.db.add(arc)
        self.db.commit()
        self.db.refresh(arc)
        return arc

    def get_arc(self, arc_id: str) -> Optional[CharacterArc]:
        """Get an arc by ID"""
        return self.db.query(CharacterArc).filter(CharacterArc.id == arc_id).first()

    def get_character_arcs(
        self,
        wiki_entry_id: str,
        manuscript_id: Optional[str] = None
    ) -> List[CharacterArc]:
        """Get all arcs for a character"""
        query = self.db.query(CharacterArc).filter(
            CharacterArc.wiki_entry_id == wiki_entry_id
        )
        if manuscript_id:
            query = query.filter(CharacterArc.manuscript_id == manuscript_id)
        return query.all()

    def get_manuscript_arcs(self, manuscript_id: str) -> List[CharacterArc]:
        """Get all character arcs for a manuscript"""
        return self.db.query(CharacterArc).filter(
            CharacterArc.manuscript_id == manuscript_id
        ).all()

    def update_arc(
        self,
        arc_id: str,
        updates: Dict[str, Any]
    ) -> Optional[CharacterArc]:
        """Update a character arc"""
        arc = self.get_arc(arc_id)
        if not arc:
            return None

        allowed_fields = [
            'arc_template', 'arc_name', 'planned_arc', 'detected_arc',
            'arc_beats', 'custom_stages', 'arc_completion', 'arc_health',
            'arc_deviation_notes'
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(arc, field, value)

        arc.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(arc)
        return arc

    def delete_arc(self, arc_id: str) -> bool:
        """Delete a character arc"""
        arc = self.get_arc(arc_id)
        if not arc:
            return False

        self.db.delete(arc)
        self.db.commit()
        return True

    # ==================== Arc Templates ====================

    def get_arc_templates(self) -> List[Dict]:
        """Get all available arc templates"""
        templates = []
        for template_id, template_data in ARC_TEMPLATE_DEFINITIONS.items():
            templates.append({
                "id": template_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "stages": template_data["stages"],
                "stage_count": len(template_data["stages"])
            })
        return templates

    def get_template_definition(self, template_id: str) -> Optional[Dict]:
        """Get a specific template definition"""
        return ARC_TEMPLATE_DEFINITIONS.get(template_id)

    # ==================== Arc-Beat Mapping ====================

    def map_arc_to_outline(
        self,
        arc_id: str,
        outline_id: str,
        structure_type: str = "three_act"
    ) -> List[Dict]:
        """Map arc stages to outline beats based on structure"""
        arc = self.get_arc(arc_id)
        if not arc:
            return []

        # Get template definition
        template = self.get_template_definition(arc.arc_template)
        if not template:
            return []

        # Get beat mapping for this structure
        beat_mapping = template.get("beat_mapping", {}).get(structure_type, {})
        if not beat_mapping:
            return []

        # Get outline beats
        beats = self.db.query(PlotBeat).filter(
            PlotBeat.outline_id == outline_id
        ).all()

        # Create mapping suggestions
        mappings = []
        for stage in template["stages"]:
            stage_id = stage["id"]
            suggested_beat_type = beat_mapping.get(stage_id)

            matching_beat = None
            if suggested_beat_type:
                # Find a beat matching this type
                for beat in beats:
                    if beat.beat_name.lower().replace(" ", "_") == suggested_beat_type:
                        matching_beat = beat
                        break

            mappings.append({
                "arc_stage": stage_id,
                "stage_name": stage["name"],
                "stage_description": stage["description"],
                "suggested_beat_type": suggested_beat_type,
                "matched_beat_id": matching_beat.id if matching_beat else None,
                "matched_beat_name": matching_beat.beat_name if matching_beat else None
            })

        return mappings

    def link_beat_to_arc_stage(
        self,
        arc_id: str,
        beat_id: str,
        arc_stage: str,
        chapter_id: Optional[str] = None,
        description: Optional[str] = None,
        is_planned: bool = True
    ) -> Optional[CharacterArc]:
        """Link an outline beat to an arc stage"""
        arc = self.get_arc(arc_id)
        if not arc:
            return None

        # Get current beats
        current_beats = arc.arc_beats or []

        # Check if this beat is already linked
        for beat in current_beats:
            if beat.get("beat_id") == beat_id and beat.get("arc_stage") == arc_stage:
                # Update existing
                beat["chapter_id"] = chapter_id
                beat["description"] = description
                beat["is_planned"] = is_planned
                arc.arc_beats = current_beats
                self.db.commit()
                return arc

        # Add new beat link
        current_beats.append({
            "beat_id": beat_id,
            "arc_stage": arc_stage,
            "chapter_id": chapter_id,
            "description": description,
            "is_planned": is_planned,
            "is_detected": False,
            "created_at": datetime.utcnow().isoformat()
        })

        arc.arc_beats = current_beats
        arc.arc_completion = arc.calculate_completion()
        arc.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(arc)
        return arc

    def unlink_beat_from_arc(
        self,
        arc_id: str,
        beat_id: str,
        arc_stage: str
    ) -> Optional[CharacterArc]:
        """Remove a beat link from an arc stage"""
        arc = self.get_arc(arc_id)
        if not arc:
            return None

        current_beats = arc.arc_beats or []
        arc.arc_beats = [
            b for b in current_beats
            if not (b.get("beat_id") == beat_id and b.get("arc_stage") == arc_stage)
        ]

        arc.arc_completion = arc.calculate_completion()
        arc.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(arc)
        return arc

    # ==================== Arc Detection ====================

    def detect_arc_from_manuscript(
        self,
        arc_id: str,
        manuscript_text: str,
        character_name: str
    ) -> Dict[str, Any]:
        """
        Analyze manuscript text to detect character arc progression.
        Uses pattern matching to identify arc stages.
        """
        arc = self.get_arc(arc_id)
        if not arc:
            return {"error": "Arc not found"}

        stages = arc.get_stages()
        if not stages:
            return {"error": "No stages defined for this arc"}

        detected = {}
        character_lower = character_name.lower()

        # Arc detection patterns for different types
        stage_patterns = {
            # Redemption arc
            "flawed_state": [
                rf"{character_lower}.*(?:selfish|cruel|cold|bitter|angry|hateful)",
                rf"{character_lower}.*(?:only cared about|didn't care|refused to)",
            ],
            "catalyst": [
                rf"{character_lower}.*(?:realized|understood|saw for the first time)",
                rf"(?:changed|transformed|opened).*{character_lower}",
            ],
            "transformation": [
                rf"{character_lower}.*(?:sacrificed|gave up|chose to help)",
                rf"{character_lower}.*(?:finally|at last).*(?:understood|saw|realized)",
            ],
            "redeemed_state": [
                rf"{character_lower}.*(?:hero|saved|redeemed|forgiven)",
            ],

            # Coming of age
            "innocence": [
                rf"{character_lower}.*(?:naive|innocent|young|sheltered|unknowing)",
                rf"{character_lower}.*(?:didn't understand|never knew|believed that)",
            ],
            "mentor": [
                rf"(?:taught|showed|guided).*{character_lower}",
                rf"{character_lower}.*(?:learned from|studied under|followed)",
            ],
            "maturity": [
                rf"{character_lower}.*(?:grown|mature|wiser|stronger)",
                rf"{character_lower}.*(?:no longer|finally understood|had become)",
            ],

            # Positive change
            "lie_believed": [
                rf"{character_lower}.*(?:believed|thought|was convinced)",
                rf"{character_lower}.*(?:lie|false|wrong|mistaken)",
            ],
            "truth_embraced": [
                rf"{character_lower}.*(?:truth|real|honest|genuine)",
                rf"{character_lower}.*(?:accepted|embraced|understood the truth)",
            ],

            # Fall/Corruption
            "noble_state": [
                rf"{character_lower}.*(?:noble|virtuous|good|honorable|just)",
            ],
            "temptation": [
                rf"{character_lower}.*(?:tempted|lured|drawn to|seduced)",
            ],
            "downfall": [
                rf"{character_lower}.*(?:fell|destroyed|lost|ruined|corrupted)",
            ],
        }

        # Check each stage
        for stage in stages:
            stage_id = stage["id"]
            patterns = stage_patterns.get(stage_id, [])

            for pattern in patterns:
                try:
                    matches = re.findall(pattern, manuscript_text, re.IGNORECASE)
                    if matches:
                        detected[stage_id] = {
                            "found": True,
                            "match_count": len(matches),
                            "sample_match": matches[0][:100] if matches else None,
                            "confidence": min(0.3 + (len(matches) * 0.1), 0.9)
                        }
                        break
                except re.error:
                    continue

            if stage_id not in detected:
                detected[stage_id] = {
                    "found": False,
                    "match_count": 0,
                    "confidence": 0.0
                }

        # Update arc with detected data
        arc.detected_arc = detected
        arc.last_analyzed_at = datetime.utcnow()

        # Calculate analysis confidence
        found_stages = sum(1 for s in detected.values() if s.get("found"))
        arc.analysis_confidence = found_stages / len(stages) if stages else 0

        self.db.commit()
        self.db.refresh(arc)

        return {
            "arc_id": arc.id,
            "stages_detected": found_stages,
            "total_stages": len(stages),
            "detected_arc": detected,
            "analysis_confidence": arc.analysis_confidence
        }

    # ==================== Arc Comparison ====================

    def compare_arcs(self, arc_id: str) -> Dict[str, Any]:
        """Compare planned arc to detected arc"""
        arc = self.get_arc(arc_id)
        if not arc:
            return {"error": "Arc not found"}

        stages = arc.get_stages()
        planned = arc.planned_arc or {}
        detected = arc.detected_arc or {}

        comparison = []
        deviations = []

        for stage in stages:
            stage_id = stage["id"]
            planned_value = planned.get(stage_id)
            detected_value = detected.get(stage_id, {})

            is_planned = bool(planned_value)
            is_detected = detected_value.get("found", False)

            status = "unknown"
            if is_planned and is_detected:
                status = "matched"
            elif is_planned and not is_detected:
                status = "missing"
                deviations.append({
                    "stage": stage_id,
                    "stage_name": stage["name"],
                    "issue": "Planned but not detected in manuscript"
                })
            elif not is_planned and is_detected:
                status = "unexpected"
                deviations.append({
                    "stage": stage_id,
                    "stage_name": stage["name"],
                    "issue": "Detected but not planned"
                })
            else:
                status = "absent"

            comparison.append({
                "stage_id": stage_id,
                "stage_name": stage["name"],
                "planned": planned_value,
                "detected": is_detected,
                "detection_confidence": detected_value.get("confidence", 0),
                "status": status
            })

        # Determine arc health
        matched_count = sum(1 for c in comparison if c["status"] == "matched")
        missing_count = sum(1 for c in comparison if c["status"] == "missing")
        total_planned = sum(1 for c in comparison if c["planned"])

        if total_planned == 0:
            health = "undefined"
        elif missing_count == 0:
            health = "healthy"
        elif missing_count <= total_planned * 0.3:
            health = "at_risk"
        else:
            health = "broken"

        # Update arc health
        arc.arc_health = health
        arc.arc_deviation_notes = "\n".join([d["issue"] for d in deviations]) if deviations else None
        self.db.commit()

        return {
            "arc_id": arc.id,
            "comparison": comparison,
            "deviations": deviations,
            "health": health,
            "matched_stages": matched_count,
            "total_planned_stages": total_planned
        }

    # ==================== Outline Integration ====================

    def get_character_outline_view(
        self,
        outline_id: str,
        wiki_entry_id: str,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """Get outline beats filtered and annotated for a specific character"""
        # Get the character's arc for this manuscript
        arcs = self.get_character_arcs(wiki_entry_id, manuscript_id)
        arc = arcs[0] if arcs else None

        # Get all outline beats
        beats = self.db.query(PlotBeat).filter(
            PlotBeat.outline_id == outline_id
        ).order_by(PlotBeat.order_index).all()

        # Get character wiki entry
        wiki_entry = self.db.query(WikiEntry).filter(
            WikiEntry.id == wiki_entry_id
        ).first()

        character_name = wiki_entry.title if wiki_entry else "Unknown"

        # Build character-centric view
        arc_beats = arc.arc_beats if arc else []
        arc_beat_ids = {b.get("beat_id") for b in arc_beats}

        character_beats = []
        for beat in beats:
            # Check if beat is linked to character's arc
            arc_link = next(
                (b for b in arc_beats if b.get("beat_id") == beat.id),
                None
            )

            character_beats.append({
                "beat_id": beat.id,
                "beat_name": beat.beat_name,
                "beat_label": beat.beat_label,
                "description": beat.beat_description,
                "order_index": beat.order_index,
                "is_arc_beat": beat.id in arc_beat_ids,
                "arc_stage": arc_link.get("arc_stage") if arc_link else None,
                "arc_description": arc_link.get("description") if arc_link else None
            })

        return {
            "character_name": character_name,
            "wiki_entry_id": wiki_entry_id,
            "arc": {
                "id": arc.id if arc else None,
                "template": arc.arc_template if arc else None,
                "completion": arc.arc_completion if arc else 0,
                "health": arc.arc_health if arc else "undefined"
            } if arc else None,
            "beats": character_beats,
            "total_beats": len(character_beats),
            "arc_beats": len([b for b in character_beats if b["is_arc_beat"]])
        }
