"""
Carbon Footprint API Routes

Endpoints for tracking and displaying carbon footprint metrics.
Implements Software Carbon Intensity (SCI) methodology from the
Green Software Foundation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.services.carbon_tracker import get_carbon_tracker, OperationType
from app.models.carbon import CarbonMetric, CarbonReport, CarbonBudget


router = APIRouter(prefix="/api/carbon", tags=["carbon"])


# Request models
class CarbonBudgetCreate(BaseModel):
    """Request model for creating a carbon budget"""
    manuscript_id: Optional[str] = None  # null for global budget
    budget_period: str = "monthly"  # daily, weekly, monthly
    budget_gco2: float  # Budget in gCO2eq
    warn_threshold: int = 80  # Warn at this percentage
    limit_threshold: int = 100
    limit_action: str = "warn"  # warn, defer, block


@router.get("/dashboard")
async def get_carbon_dashboard(
    days: int = 30,
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get carbon footprint dashboard data.

    Returns SCI score, emissions breakdown, trends, and recommendations.
    """
    try:
        tracker = get_carbon_tracker(db)
        dashboard = await tracker.get_dashboard(days=days, manuscript_id=manuscript_id)

        return {
            "success": True,
            "data": {
                "sci_score": dashboard.sci_score,
                "sci_unit": "gCO2eq per request",
                "total_emissions_gco2": dashboard.total_emissions_gco2,
                "period": {
                    "start": dashboard.period_start.isoformat(),
                    "end": dashboard.period_end.isoformat(),
                    "days": days,
                },
                "breakdown": dashboard.breakdown,
                "trend": dashboard.trend,
                "comparison_to_previous_percent": dashboard.comparison_to_previous,
                "cache_hit_rate_percent": dashboard.cache_hit_rate,
                "recommendations": dashboard.recommendations,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/sci")
async def get_sci_score(
    days: int = 30,
    functional_unit: str = "per_request",
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get Software Carbon Intensity (SCI) score.

    SCI = ((E × I) + M) / R

    Args:
        days: Number of days to calculate over
        functional_unit: What R represents (per_request, per_user, per_manuscript)
        manuscript_id: Optional filter by manuscript
    """
    try:
        tracker = get_carbon_tracker(db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        sci = await tracker.calculate_sci(
            start_date=start_date,
            end_date=end_date,
            functional_unit=functional_unit,
            manuscript_id=manuscript_id,
        )

        return {
            "success": True,
            "data": {
                "sci_score": sci.score,
                "unit": f"gCO2eq {sci.functional_unit_type}",
                "total_energy_kwh": sci.total_energy_kwh,
                "total_emissions_gco2": sci.total_emissions_gco2,
                "embodied_carbon_gco2": sci.embodied_carbon_gco2,
                "functional_units": sci.functional_units,
                "functional_unit_type": sci.functional_unit_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days,
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate SCI: {str(e)}")


@router.get("/metrics")
async def get_carbon_metrics(
    days: int = 7,
    manuscript_id: Optional[str] = None,
    operation_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get detailed carbon metrics for analysis.

    Returns individual operation records for debugging and optimization.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        query = db.query(CarbonMetric).filter(
            CarbonMetric.created_at >= start_date,
            CarbonMetric.created_at <= end_date,
        )

        if manuscript_id:
            query = query.filter(CarbonMetric.manuscript_id == manuscript_id)

        if operation_type:
            query = query.filter(CarbonMetric.operation_type == operation_type)

        metrics = query.order_by(CarbonMetric.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "data": {
                "metrics": [
                    {
                        "id": m.id,
                        "operation_type": m.operation_type,
                        "operation_subtype": m.operation_subtype,
                        "energy_kwh": m.energy_micro_kwh / 1_000_000,
                        "emissions_gco2": m.emissions_micro_gco2 / 1_000_000,
                        "carbon_intensity": m.carbon_intensity,
                        "region": m.region,
                        "tokens_processed": m.tokens_processed,
                        "ai_provider": m.ai_provider,
                        "ai_model": m.ai_model,
                        "cache_hit": bool(m.cache_hit),
                        "batched": bool(m.batched),
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in metrics
                ],
                "total_count": len(metrics),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/breakdown")
async def get_emissions_breakdown(
    days: int = 30,
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get emissions breakdown by operation type.

    Useful for identifying which operations contribute most to carbon footprint.
    """
    try:
        tracker = get_carbon_tracker(db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        breakdown = await tracker._get_emissions_breakdown(
            start_date=start_date,
            end_date=end_date,
            manuscript_id=manuscript_id,
        )

        total = sum(breakdown.values())

        # Calculate percentages
        breakdown_with_pct = {
            op_type: {
                "emissions_gco2": emissions,
                "percentage": round((emissions / total * 100) if total > 0 else 0, 2)
            }
            for op_type, emissions in breakdown.items()
        }

        return {
            "success": True,
            "data": {
                "breakdown": breakdown_with_pct,
                "total_emissions_gco2": total,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days,
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown: {str(e)}")


@router.post("/budget")
async def create_carbon_budget(
    budget: CarbonBudgetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a carbon budget to track and limit emissions.

    Budgets can be global or per-manuscript.
    """
    try:
        new_budget = CarbonBudget(
            manuscript_id=budget.manuscript_id,
            budget_period=budget.budget_period,
            budget_micro_gco2=int(budget.budget_gco2 * 1_000_000),
            warn_threshold=budget.warn_threshold,
            limit_threshold=budget.limit_threshold,
            limit_action=budget.limit_action,
            period_start=datetime.utcnow(),
            is_active=1,
        )
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)

        return {
            "success": True,
            "data": {
                "id": new_budget.id,
                "budget_gco2": new_budget.budget_micro_gco2 / 1_000_000,
                "budget_period": new_budget.budget_period,
                "warn_threshold": new_budget.warn_threshold,
                "limit_threshold": new_budget.limit_threshold,
            },
            "message": "Carbon budget created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create budget: {str(e)}")


@router.get("/budget")
async def get_carbon_budget_status(
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get current carbon budget status.

    Returns usage vs budget and alert thresholds.
    """
    try:
        tracker = get_carbon_tracker(db)
        budget_status = await tracker.check_budget(manuscript_id=manuscript_id)

        if not budget_status:
            return {
                "success": True,
                "data": None,
                "message": "No active carbon budget found"
            }

        return {
            "success": True,
            "data": budget_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get budget status: {str(e)}")


@router.get("/optimization-tips")
async def get_optimization_tips(
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get personalized tips for reducing carbon footprint.

    Based on actual usage patterns.
    """
    try:
        tracker = get_carbon_tracker(db)
        dashboard = await tracker.get_dashboard(days=30, manuscript_id=manuscript_id)

        # General tips that always apply
        general_tips = [
            {
                "category": "Model Selection",
                "tip": "Use smaller models for simple tasks",
                "detail": "Haiku/GPT-3.5-turbo use ~4x less energy than Opus/GPT-4 for grammar checking",
                "potential_savings": "30-50%"
            },
            {
                "category": "Caching",
                "tip": "Enable response caching",
                "detail": "Repeated queries for similar content can be served from cache",
                "potential_savings": "20-40%"
            },
            {
                "category": "Batching",
                "tip": "Batch related requests",
                "detail": "Combine multiple small requests into fewer larger ones",
                "potential_savings": "10-20%"
            },
        ]

        return {
            "success": True,
            "data": {
                "personalized_recommendations": dashboard.recommendations,
                "general_tips": general_tips,
                "current_metrics": {
                    "sci_score": dashboard.sci_score,
                    "cache_hit_rate": dashboard.cache_hit_rate,
                    "trend": dashboard.trend,
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tips: {str(e)}")


@router.get("/compare")
async def compare_carbon_periods(
    manuscript_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare carbon metrics across different time periods.

    Useful for tracking improvement over time.
    """
    try:
        tracker = get_carbon_tracker(db)

        now = datetime.utcnow()
        periods = {
            "last_7_days": (now - timedelta(days=7), now),
            "previous_7_days": (now - timedelta(days=14), now - timedelta(days=7)),
            "last_30_days": (now - timedelta(days=30), now),
            "previous_30_days": (now - timedelta(days=60), now - timedelta(days=30)),
        }

        results = {}
        for period_name, (start, end) in periods.items():
            sci = await tracker.calculate_sci(start, end, "per_request", manuscript_id)
            results[period_name] = {
                "sci_score": sci.score,
                "total_emissions_gco2": sci.total_emissions_gco2,
                "functional_units": sci.functional_units,
            }

        # Calculate improvement percentages
        week_improvement = 0
        if results["previous_7_days"]["total_emissions_gco2"] > 0:
            week_improvement = (
                (results["previous_7_days"]["total_emissions_gco2"] -
                 results["last_7_days"]["total_emissions_gco2"]) /
                results["previous_7_days"]["total_emissions_gco2"] * 100
            )

        month_improvement = 0
        if results["previous_30_days"]["total_emissions_gco2"] > 0:
            month_improvement = (
                (results["previous_30_days"]["total_emissions_gco2"] -
                 results["last_30_days"]["total_emissions_gco2"]) /
                results["previous_30_days"]["total_emissions_gco2"] * 100
            )

        return {
            "success": True,
            "data": {
                "periods": results,
                "improvement": {
                    "week_over_week_percent": round(week_improvement, 2),
                    "month_over_month_percent": round(month_improvement, 2),
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare periods: {str(e)}")
