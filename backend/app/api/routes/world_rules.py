"""
World Rules API Routes - Custom validation rules for fantasy/sci-fi worlds.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.world_rule_service import WorldRuleService
from app.models.world_rule import RuleType, RuleSeverity


router = APIRouter(prefix="/world-rules", tags=["world-rules"])


# ==================== Pydantic Models ====================

class RuleCreate(BaseModel):
    world_id: str
    rule_name: str
    rule_type: str = RuleType.CUSTOM.value
    rule_description: Optional[str] = None
    condition: Optional[str] = None
    requirement: Optional[str] = None
    validation_keywords: Optional[List[str]] = None
    validation_pattern: Optional[str] = None
    exception_keywords: Optional[List[str]] = None
    exception_pattern: Optional[str] = None
    valid_examples: Optional[List[str]] = None
    violation_examples: Optional[List[str]] = None
    violation_message: Optional[str] = None
    severity: str = RuleSeverity.WARNING.value
    wiki_entry_id: Optional[str] = None


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    rule_description: Optional[str] = None
    condition: Optional[str] = None
    requirement: Optional[str] = None
    validation_keywords: Optional[List[str]] = None
    validation_pattern: Optional[str] = None
    exception_keywords: Optional[List[str]] = None
    exception_pattern: Optional[str] = None
    valid_examples: Optional[List[str]] = None
    violation_examples: Optional[List[str]] = None
    violation_message: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[int] = None


class RuleResponse(BaseModel):
    id: str
    world_id: str
    wiki_entry_id: Optional[str] = None
    rule_type: str
    rule_name: str
    rule_description: Optional[str] = None
    condition: Optional[str] = None
    requirement: Optional[str] = None
    validation_keywords: List[str] = []
    validation_pattern: Optional[str] = None
    exception_keywords: List[str] = []
    exception_pattern: Optional[str] = None
    valid_examples: List[str] = []
    violation_examples: List[str] = []
    violation_message: Optional[str] = None
    severity: str
    is_active: int
    violation_count: int = 0
    last_violation_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RuleFromTemplateRequest(BaseModel):
    world_id: str
    template_id: str
    customizations: Optional[Dict[str, Any]] = None


class ValidationRequest(BaseModel):
    text: str
    rule_types: Optional[List[str]] = None


class ViolationResponse(BaseModel):
    id: str
    rule_id: str
    manuscript_id: str
    chapter_id: Optional[str] = None
    text_excerpt: str
    surrounding_text: Optional[str] = None
    status: str
    dismissed_reason: Optional[str] = None
    confidence: float
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DismissRequest(BaseModel):
    reason: Optional[str] = None


# ==================== Rule CRUD Endpoints ====================

@router.post("", response_model=RuleResponse)
def create_rule(
    data: RuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new world rule"""
    service = WorldRuleService(db)

    rule = service.create_rule(
        world_id=data.world_id,
        rule_name=data.rule_name,
        rule_type=data.rule_type,
        rule_description=data.rule_description,
        condition=data.condition,
        requirement=data.requirement,
        validation_keywords=data.validation_keywords,
        validation_pattern=data.validation_pattern,
        exception_keywords=data.exception_keywords,
        exception_pattern=data.exception_pattern,
        valid_examples=data.valid_examples,
        violation_examples=data.violation_examples,
        violation_message=data.violation_message,
        severity=data.severity,
        wiki_entry_id=data.wiki_entry_id
    )

    return rule


@router.post("/from-template", response_model=RuleResponse)
def create_rule_from_template(
    data: RuleFromTemplateRequest,
    db: Session = Depends(get_db)
):
    """Create a rule from a pre-defined template"""
    service = WorldRuleService(db)

    rule = service.create_rule_from_template(
        world_id=data.world_id,
        template_id=data.template_id,
        customizations=data.customizations
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Template not found")

    return rule


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Get a rule by ID"""
    service = WorldRuleService(db)
    rule = service.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule


@router.get("/world/{world_id}", response_model=List[RuleResponse])
def get_world_rules(
    world_id: str,
    rule_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get all rules for a world"""
    service = WorldRuleService(db)
    rules = service.get_world_rules(world_id, rule_type, active_only)
    return rules


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: str,
    updates: RuleUpdate,
    db: Session = Depends(get_db)
):
    """Update a rule"""
    service = WorldRuleService(db)

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    rule = service.update_rule(rule_id, update_dict)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Delete a rule"""
    service = WorldRuleService(db)

    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"status": "deleted", "id": rule_id}


@router.post("/{rule_id}/toggle", response_model=RuleResponse)
def toggle_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Toggle a rule's active status"""
    service = WorldRuleService(db)

    rule = service.toggle_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule


# ==================== Validation Endpoints ====================

@router.post("/validate/text/{world_id}")
def validate_text(
    world_id: str,
    data: ValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate text against world rules"""
    service = WorldRuleService(db)

    violations = service.validate_text(
        text=data.text,
        world_id=world_id,
        rule_types=data.rule_types
    )

    return {
        "world_id": world_id,
        "violations": violations,
        "count": len(violations)
    }


@router.post("/validate/chapter/{world_id}/{chapter_id}")
def validate_chapter(
    world_id: str,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Validate a chapter against world rules"""
    service = WorldRuleService(db)

    violations = service.validate_chapter(chapter_id, world_id)

    return {
        "world_id": world_id,
        "chapter_id": chapter_id,
        "violations": violations,
        "count": len(violations)
    }


@router.post("/validate/manuscript/{world_id}/{manuscript_id}")
def validate_manuscript(
    world_id: str,
    manuscript_id: str,
    record_violations: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Validate entire manuscript against world rules"""
    service = WorldRuleService(db)

    result = service.validate_manuscript(
        manuscript_id=manuscript_id,
        world_id=world_id,
        record_violations=record_violations
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


# ==================== Violation Endpoints ====================

@router.get("/violations/manuscript/{manuscript_id}", response_model=List[ViolationResponse])
def get_violations(
    manuscript_id: str,
    rule_id: Optional[str] = Query(None),
    status: str = Query("active"),
    db: Session = Depends(get_db)
):
    """Get violations for a manuscript"""
    service = WorldRuleService(db)
    violations = service.get_violations(manuscript_id, rule_id, status)
    return violations


@router.post("/violations/{violation_id}/dismiss", response_model=ViolationResponse)
def dismiss_violation(
    violation_id: str,
    data: DismissRequest,
    db: Session = Depends(get_db)
):
    """Dismiss a violation"""
    service = WorldRuleService(db)

    violation = service.dismiss_violation(violation_id, data.reason)

    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    return violation


@router.post("/violations/{violation_id}/resolve", response_model=ViolationResponse)
def resolve_violation(
    violation_id: str,
    db: Session = Depends(get_db)
):
    """Mark a violation as fixed"""
    service = WorldRuleService(db)

    violation = service.resolve_violation(violation_id)

    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    return violation


# ==================== Template Endpoints ====================

@router.get("/templates/all")
def get_rule_templates(
    db: Session = Depends(get_db)
):
    """Get available rule templates"""
    service = WorldRuleService(db)
    return service.get_rule_templates()


@router.get("/types/all")
def get_rule_types(
    db: Session = Depends(get_db)
):
    """Get available rule types"""
    service = WorldRuleService(db)
    return service.get_rule_types()
