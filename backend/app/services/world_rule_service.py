"""
World Rule Service - Custom validation rules for fantasy/sci-fi worlds.

Provides:
- Rule CRUD operations
- Pattern-based validation against manuscript text
- Violation tracking and resolution
- Integration with TimelineValidator and consistency checkers
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import re

from app.models.world_rule import (
    WorldRule, RuleViolation,
    RuleType, RuleSeverity, RULE_TEMPLATES
)
from app.models.manuscript import Manuscript, Chapter


class WorldRuleService:
    """Service for managing world rules and validation"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Rule CRUD ====================

    def create_rule(
        self,
        world_id: str,
        rule_name: str,
        rule_type: str = RuleType.CUSTOM.value,
        rule_description: Optional[str] = None,
        condition: Optional[str] = None,
        requirement: Optional[str] = None,
        validation_keywords: Optional[List[str]] = None,
        validation_pattern: Optional[str] = None,
        exception_keywords: Optional[List[str]] = None,
        exception_pattern: Optional[str] = None,
        valid_examples: Optional[List[str]] = None,
        violation_examples: Optional[List[str]] = None,
        violation_message: Optional[str] = None,
        severity: str = RuleSeverity.WARNING.value,
        wiki_entry_id: Optional[str] = None
    ) -> WorldRule:
        """Create a new world rule"""
        rule = WorldRule(
            id=str(uuid.uuid4()),
            world_id=world_id,
            wiki_entry_id=wiki_entry_id,
            rule_type=rule_type,
            rule_name=rule_name,
            rule_description=rule_description,
            condition=condition,
            requirement=requirement,
            validation_keywords=validation_keywords or [],
            validation_pattern=validation_pattern,
            exception_keywords=exception_keywords or [],
            exception_pattern=exception_pattern,
            valid_examples=valid_examples or [],
            violation_examples=violation_examples or [],
            violation_message=violation_message,
            severity=severity,
            is_active=1,
            created_at=datetime.utcnow()
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def create_rule_from_template(
        self,
        world_id: str,
        template_id: str,
        customizations: Optional[Dict] = None
    ) -> Optional[WorldRule]:
        """Create a rule from a pre-defined template"""
        template = RULE_TEMPLATES.get(template_id)
        if not template:
            return None

        # Merge template with customizations
        data = {**template}
        if customizations:
            data.update(customizations)

        return self.create_rule(
            world_id=world_id,
            rule_name=data.get("rule_name", "Unnamed Rule"),
            rule_type=data.get("rule_type", RuleType.CUSTOM.value),
            rule_description=data.get("rule_description"),
            validation_keywords=data.get("validation_keywords", []),
            exception_keywords=data.get("exception_keywords", []),
            violation_message=data.get("violation_message"),
            valid_examples=data.get("valid_examples", []),
            violation_examples=data.get("violation_examples", []),
            severity=data.get("severity", RuleSeverity.WARNING.value)
        )

    def get_rule(self, rule_id: str) -> Optional[WorldRule]:
        """Get a rule by ID"""
        return self.db.query(WorldRule).filter(WorldRule.id == rule_id).first()

    def get_world_rules(
        self,
        world_id: str,
        rule_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[WorldRule]:
        """Get all rules for a world"""
        query = self.db.query(WorldRule).filter(WorldRule.world_id == world_id)

        if rule_type:
            query = query.filter(WorldRule.rule_type == rule_type)
        if active_only:
            query = query.filter(WorldRule.is_active == 1)

        return query.order_by(WorldRule.rule_name).all()

    def update_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WorldRule]:
        """Update a rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        allowed_fields = [
            'rule_name', 'rule_type', 'rule_description', 'condition',
            'requirement', 'validation_keywords', 'validation_pattern',
            'exception_keywords', 'exception_pattern', 'valid_examples',
            'violation_examples', 'violation_message', 'severity', 'is_active',
            'check_scope'
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(rule, field, value)

        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        self.db.delete(rule)
        self.db.commit()
        return True

    def toggle_rule(self, rule_id: str) -> Optional[WorldRule]:
        """Toggle a rule's active status"""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        rule.is_active = 0 if rule.is_active == 1 else 1
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        return rule

    # ==================== Validation ====================

    def validate_text(
        self,
        text: str,
        world_id: str,
        rule_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Validate text against all active world rules"""
        rules = self.get_world_rules(world_id)
        violations = []

        for rule in rules:
            if rule_types and rule.rule_type not in rule_types:
                continue

            violation = self._check_rule(rule, text)
            if violation:
                violations.append(violation)

        return violations

    def validate_chapter(
        self,
        chapter_id: str,
        world_id: str
    ) -> List[Dict[str, Any]]:
        """Validate a chapter against world rules"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return []

        # Get chapter content
        content = ""
        for scene in chapter.scenes:
            content += f"\n{scene.content or ''}"

        violations = self.validate_text(content, world_id)

        # Annotate violations with chapter info
        for v in violations:
            v["chapter_id"] = chapter_id
            v["chapter_title"] = chapter.title

        return violations

    def validate_manuscript(
        self,
        manuscript_id: str,
        world_id: str,
        record_violations: bool = True
    ) -> Dict[str, Any]:
        """Validate entire manuscript against world rules"""
        manuscript = self.db.query(Manuscript).filter(
            Manuscript.id == manuscript_id
        ).first()

        if not manuscript:
            return {"error": "Manuscript not found"}

        all_violations = []
        chapters_checked = 0

        for chapter in manuscript.chapters:
            chapter_violations = self.validate_chapter(chapter.id, world_id)
            all_violations.extend(chapter_violations)
            chapters_checked += 1

        # Record violations if requested
        if record_violations:
            for v in all_violations:
                self._record_violation(
                    rule_id=v["rule_id"],
                    manuscript_id=manuscript_id,
                    chapter_id=v.get("chapter_id"),
                    text_excerpt=v.get("text_excerpt", ""),
                    confidence=v.get("confidence", 0.8)
                )

        # Group by rule
        by_rule = {}
        for v in all_violations:
            rule_id = v["rule_id"]
            if rule_id not in by_rule:
                by_rule[rule_id] = {
                    "rule_name": v["rule_name"],
                    "rule_type": v["rule_type"],
                    "severity": v["severity"],
                    "count": 0,
                    "chapters": []
                }
            by_rule[rule_id]["count"] += 1
            if v.get("chapter_title") not in by_rule[rule_id]["chapters"]:
                by_rule[rule_id]["chapters"].append(v.get("chapter_title"))

        return {
            "manuscript_id": manuscript_id,
            "chapters_checked": chapters_checked,
            "total_violations": len(all_violations),
            "violations_by_rule": by_rule,
            "violations": all_violations
        }

    def _check_rule(self, rule: WorldRule, text: str) -> Optional[Dict[str, Any]]:
        """Check a single rule against text"""
        text_lower = text.lower()

        # Check if any validation keywords are present
        keywords = rule.validation_keywords or []
        keyword_found = any(kw.lower() in text_lower for kw in keywords)

        if not keyword_found and not rule.validation_pattern:
            return None  # No trigger

        # Check if exception keywords exempt this text
        exception_keywords = rule.exception_keywords or []
        if any(ex.lower() in text_lower for ex in exception_keywords):
            return None  # Exempted

        # Check exception pattern
        if rule.exception_pattern:
            try:
                if re.search(rule.exception_pattern, text, re.IGNORECASE):
                    return None  # Exempted by pattern
            except re.error:
                pass

        # Check validation pattern
        violation_found = False
        match_text = ""

        if rule.validation_pattern:
            try:
                # Pattern should match valid text
                # If pattern doesn't match, it's a violation
                match = re.search(rule.validation_pattern, text, re.IGNORECASE)
                if not match:
                    violation_found = True
                    # Find the keyword that triggered this check
                    for kw in keywords:
                        if kw.lower() in text_lower:
                            idx = text_lower.find(kw.lower())
                            match_text = text[max(0, idx-30):idx+len(kw)+50]
                            break
            except re.error:
                pass
        elif keyword_found:
            # Simple keyword match without pattern = potential violation
            violation_found = True
            for kw in keywords:
                if kw.lower() in text_lower:
                    idx = text_lower.find(kw.lower())
                    match_text = text[max(0, idx-30):idx+len(kw)+50]
                    break

        if violation_found:
            return {
                "rule_id": rule.id,
                "rule_name": rule.rule_name,
                "rule_type": rule.rule_type,
                "severity": rule.severity,
                "message": rule.violation_message or f"Possible violation of: {rule.rule_name}",
                "text_excerpt": match_text[:200] if match_text else "",
                "confidence": 0.7 if rule.validation_pattern else 0.5
            }

        return None

    def _record_violation(
        self,
        rule_id: str,
        manuscript_id: str,
        chapter_id: Optional[str],
        text_excerpt: str,
        confidence: float = 0.8
    ) -> RuleViolation:
        """Record a violation"""
        violation = RuleViolation(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            text_excerpt=text_excerpt,
            status="active",
            confidence=confidence,
            detected_at=datetime.utcnow()
        )
        self.db.add(violation)

        # Update rule stats
        rule = self.get_rule(rule_id)
        if rule:
            rule.violation_count = (rule.violation_count or 0) + 1
            rule.last_violation_at = datetime.utcnow()

        self.db.commit()
        return violation

    # ==================== Violation Management ====================

    def get_violations(
        self,
        manuscript_id: str,
        rule_id: Optional[str] = None,
        status: str = "active"
    ) -> List[RuleViolation]:
        """Get violations for a manuscript"""
        query = self.db.query(RuleViolation).filter(
            RuleViolation.manuscript_id == manuscript_id
        )

        if rule_id:
            query = query.filter(RuleViolation.rule_id == rule_id)
        if status:
            query = query.filter(RuleViolation.status == status)

        return query.order_by(RuleViolation.detected_at.desc()).all()

    def dismiss_violation(
        self,
        violation_id: str,
        reason: Optional[str] = None
    ) -> Optional[RuleViolation]:
        """Dismiss a violation"""
        violation = self.db.query(RuleViolation).filter(
            RuleViolation.id == violation_id
        ).first()

        if not violation:
            return None

        violation.status = "dismissed"
        violation.dismissed_reason = reason
        violation.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(violation)
        return violation

    def resolve_violation(self, violation_id: str) -> Optional[RuleViolation]:
        """Mark a violation as fixed"""
        violation = self.db.query(RuleViolation).filter(
            RuleViolation.id == violation_id
        ).first()

        if not violation:
            return None

        violation.status = "fixed"
        violation.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(violation)
        return violation

    # ==================== Templates ====================

    def get_rule_templates(self) -> List[Dict[str, Any]]:
        """Get available rule templates"""
        templates = []
        for template_id, template_data in RULE_TEMPLATES.items():
            templates.append({
                "id": template_id,
                "rule_name": template_data.get("rule_name"),
                "rule_type": template_data.get("rule_type"),
                "rule_description": template_data.get("rule_description"),
                "validation_keywords": template_data.get("validation_keywords", []),
                "valid_examples": template_data.get("valid_examples", []),
                "violation_examples": template_data.get("violation_examples", [])
            })
        return templates

    def get_rule_types(self) -> List[Dict[str, str]]:
        """Get available rule types"""
        return [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in RuleType
        ]
