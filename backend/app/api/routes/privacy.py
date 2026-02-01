"""
Privacy API Routes

Endpoints for managing author privacy preferences and AI training consent.
These ensure writers have full control over how their manuscripts are used.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.privacy import (
    AuthorPrivacyPreferences,
    ConsentRecord,
    AIInteractionAudit,
    ContentSharingLevel,
    ConsentType,
)
from app.services.privacy_config import generate_robots_txt, WEB_PROTECTION_HEADERS


router = APIRouter(prefix="/api/privacy", tags=["privacy"])


# Request/Response models
class PrivacyPreferencesUpdate(BaseModel):
    """Request model for updating privacy preferences"""
    allow_ai_assistance: Optional[bool] = None
    allow_training_data: Optional[bool] = None
    allow_style_analysis: Optional[bool] = None
    allow_plot_suggestions: Optional[bool] = None
    allow_character_development: Optional[bool] = None
    allow_grammar_check: Optional[bool] = None
    allow_continuity_check: Optional[bool] = None
    content_sharing_level: Optional[str] = None
    ai_context_retention_days: Optional[int] = None


class ConsentUpdate(BaseModel):
    """Request model for recording consent changes"""
    consent_type: str  # ai_assistance, training_data, analytics
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@router.get("/preferences/{manuscript_id}")
async def get_privacy_preferences(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    Get privacy preferences for a manuscript.

    Creates default preferences (maximum protection) if none exist.
    """
    try:
        preferences = db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == manuscript_id
        ).first()

        if not preferences:
            # Create default preferences with maximum protection
            preferences = AuthorPrivacyPreferences(
                manuscript_id=manuscript_id,
                allow_ai_assistance=True,
                allow_training_data=False,  # CRITICAL: default to FALSE
                content_sharing_level=ContentSharingLevel.AI_ASSIST_ONLY.value,
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)

        return {
            "success": True,
            "data": {
                "id": preferences.id,
                "manuscript_id": preferences.manuscript_id,
                "allow_ai_assistance": preferences.allow_ai_assistance,
                "allow_training_data": preferences.allow_training_data,
                "allow_style_analysis": preferences.allow_style_analysis,
                "allow_plot_suggestions": preferences.allow_plot_suggestions,
                "allow_character_development": preferences.allow_character_development,
                "allow_grammar_check": preferences.allow_grammar_check,
                "allow_continuity_check": preferences.allow_continuity_check,
                "content_sharing_level": preferences.content_sharing_level,
                "ai_context_retention_days": preferences.ai_context_retention_days,
                "created_at": preferences.created_at.isoformat() if preferences.created_at else None,
                "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@router.put("/preferences/{manuscript_id}")
async def update_privacy_preferences(
    manuscript_id: str,
    updates: PrivacyPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """
    Update privacy preferences for a manuscript.

    Only updates fields that are explicitly provided.
    """
    try:
        preferences = db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == manuscript_id
        ).first()

        if not preferences:
            # Create with provided values
            preferences = AuthorPrivacyPreferences(
                manuscript_id=manuscript_id,
                allow_training_data=False,  # Always default to FALSE
            )
            db.add(preferences)

        # Update only provided fields
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(preferences, field) and value is not None:
                setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)

        # Record consent changes for audit
        if updates.allow_training_data is not None:
            consent = ConsentRecord(
                manuscript_id=manuscript_id,
                consent_type=ConsentType.TRAINING_DATA.value,
                granted=updates.allow_training_data,
            )
            db.add(consent)
            db.commit()

        if updates.allow_ai_assistance is not None:
            consent = ConsentRecord(
                manuscript_id=manuscript_id,
                consent_type=ConsentType.AI_ASSISTANCE.value,
                granted=updates.allow_ai_assistance,
            )
            db.add(consent)
            db.commit()

        return {
            "success": True,
            "data": {
                "id": preferences.id,
                "manuscript_id": preferences.manuscript_id,
                "allow_ai_assistance": preferences.allow_ai_assistance,
                "allow_training_data": preferences.allow_training_data,
                "allow_style_analysis": preferences.allow_style_analysis,
                "allow_plot_suggestions": preferences.allow_plot_suggestions,
                "allow_character_development": preferences.allow_character_development,
                "allow_grammar_check": preferences.allow_grammar_check,
                "allow_continuity_check": preferences.allow_continuity_check,
                "content_sharing_level": preferences.content_sharing_level,
                "ai_context_retention_days": preferences.ai_context_retention_days,
                "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None,
            },
            "message": "Privacy preferences updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.post("/consent/{manuscript_id}")
async def record_consent(
    manuscript_id: str,
    consent: ConsentUpdate,
    db: Session = Depends(get_db)
):
    """
    Record a consent decision for audit purposes.

    This creates an immutable audit trail of consent changes.
    """
    try:
        # Validate consent type
        valid_types = [ct.value for ct in ConsentType]
        if consent.consent_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid consent type. Must be one of: {valid_types}"
            )

        record = ConsentRecord(
            manuscript_id=manuscript_id,
            consent_type=consent.consent_type,
            granted=consent.granted,
            ip_address=consent.ip_address,
            user_agent=consent.user_agent,
        )
        db.add(record)
        db.commit()

        # Also update the preferences table
        preferences = db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == manuscript_id
        ).first()

        if preferences:
            if consent.consent_type == ConsentType.TRAINING_DATA.value:
                preferences.allow_training_data = consent.granted
            elif consent.consent_type == ConsentType.AI_ASSISTANCE.value:
                preferences.allow_ai_assistance = consent.granted
            preferences.updated_at = datetime.utcnow()
            db.commit()

        return {
            "success": True,
            "data": {
                "id": record.id,
                "consent_type": record.consent_type,
                "granted": record.granted,
                "created_at": record.created_at.isoformat(),
            },
            "message": "Consent recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record consent: {str(e)}")


@router.get("/consent-history/{manuscript_id}")
async def get_consent_history(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    Get consent history for a manuscript (for compliance/audit).
    """
    try:
        records = db.query(ConsentRecord).filter(
            ConsentRecord.manuscript_id == manuscript_id
        ).order_by(ConsentRecord.created_at.desc()).all()

        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "consent_type": r.consent_type,
                    "granted": r.granted,
                    "version": r.version,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consent history: {str(e)}")


@router.get("/ai-interactions/{manuscript_id}")
async def get_ai_interaction_audit(
    manuscript_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get AI interaction audit log for a manuscript.

    This shows what AI operations have been performed, without
    exposing the actual content.
    """
    try:
        interactions = db.query(AIInteractionAudit).filter(
            AIInteractionAudit.manuscript_id == manuscript_id
        ).order_by(AIInteractionAudit.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "data": [
                {
                    "id": i.id,
                    "interaction_type": i.interaction_type,
                    "provider": i.provider,
                    "model": i.model,
                    "tokens_sent": i.tokens_sent,
                    "tokens_received": i.tokens_received,
                    "training_opted_out": i.training_opted_out,
                    "estimated_cost_usd": i.estimated_cost_usd / 1_000_000 if i.estimated_cost_usd else 0,
                    "created_at": i.created_at.isoformat(),
                }
                for i in interactions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI interactions: {str(e)}")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    """
    Generate robots.txt that blocks AI crawlers from manuscript content.

    This should be served at the root of any web-exposed manuscript URLs.
    """
    return generate_robots_txt()


@router.get("/protection-headers")
async def get_protection_headers():
    """
    Get the HTTP headers that should be added to manuscript responses.

    These headers tell AI crawlers not to use the content for training.
    """
    return {
        "success": True,
        "data": {
            "headers": WEB_PROTECTION_HEADERS,
            "description": "Add these headers to any HTTP response containing manuscript content"
        }
    }


@router.get("/data-export/{manuscript_id}")
async def export_author_data(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    Export all data for a manuscript (for GDPR/CCPA compliance).

    Returns all stored data related to the manuscript including
    preferences, consent history, and AI interaction audit.
    """
    try:
        preferences = db.query(AuthorPrivacyPreferences).filter(
            AuthorPrivacyPreferences.manuscript_id == manuscript_id
        ).first()

        consent_records = db.query(ConsentRecord).filter(
            ConsentRecord.manuscript_id == manuscript_id
        ).all()

        ai_interactions = db.query(AIInteractionAudit).filter(
            AIInteractionAudit.manuscript_id == manuscript_id
        ).all()

        return {
            "success": True,
            "data": {
                "manuscript_id": manuscript_id,
                "export_date": datetime.utcnow().isoformat(),
                "preferences": {
                    "allow_ai_assistance": preferences.allow_ai_assistance if preferences else True,
                    "allow_training_data": preferences.allow_training_data if preferences else False,
                    "content_sharing_level": preferences.content_sharing_level if preferences else "ai_assist_only",
                } if preferences else None,
                "consent_history": [
                    {
                        "consent_type": r.consent_type,
                        "granted": r.granted,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in consent_records
                ],
                "ai_interactions_summary": {
                    "total_interactions": len(ai_interactions),
                    "total_tokens_sent": sum(i.tokens_sent for i in ai_interactions),
                    "total_tokens_received": sum(i.tokens_received for i in ai_interactions),
                    "all_training_opted_out": all(i.training_opted_out for i in ai_interactions),
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
