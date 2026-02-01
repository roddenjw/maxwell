"""
Carbon Tracker Service

Implements Software Carbon Intensity (SCI) methodology from the
Green Software Foundation for tracking and minimizing environmental impact.

SCI = ((E × I) + M) / R
Where:
- E = Energy consumed (kWh)
- I = Carbon intensity of electricity (gCO2eq/kWh)
- R = Functional unit (per user, per request, etc.)
- M = Embodied carbon of hardware (estimated)

Reference: https://sci.greensoftware.foundation/
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.carbon import (
    CarbonMetric,
    CarbonReport,
    CarbonBudget,
    ENERGY_ESTIMATES_MICRO_KWH,
    CARBON_INTENSITY_BY_REGION,
)


class OperationType(str, Enum):
    """Types of operations we track for carbon"""
    AI_REQUEST_SMALL = "ai_request_small"
    AI_REQUEST_MEDIUM = "ai_request_medium"
    AI_REQUEST_LARGE = "ai_request_large"
    DB_READ_SIMPLE = "db_read_simple"
    DB_READ_COMPLEX = "db_read_complex"
    DB_WRITE = "db_write"
    STORAGE_READ = "storage_read_mb"
    STORAGE_WRITE = "storage_write_mb"
    NETWORK_TRANSFER = "network_transfer_mb"
    NLP_ANALYSIS = "nlp_analysis"


# Map AI models to size categories
AI_MODEL_SIZES = {
    # Small/Fast models
    "claude-3-haiku": OperationType.AI_REQUEST_SMALL,
    "gpt-3.5-turbo": OperationType.AI_REQUEST_SMALL,
    "gpt-4o-mini": OperationType.AI_REQUEST_SMALL,

    # Medium models
    "claude-3-sonnet": OperationType.AI_REQUEST_MEDIUM,
    "claude-3-5-sonnet": OperationType.AI_REQUEST_MEDIUM,
    "claude-sonnet-4": OperationType.AI_REQUEST_MEDIUM,
    "gpt-4o": OperationType.AI_REQUEST_MEDIUM,

    # Large models
    "claude-3-opus": OperationType.AI_REQUEST_LARGE,
    "claude-opus-4": OperationType.AI_REQUEST_LARGE,
    "gpt-4-turbo": OperationType.AI_REQUEST_LARGE,
    "gpt-4": OperationType.AI_REQUEST_LARGE,
}


@dataclass
class CarbonMetricResult:
    """Result of a carbon tracking operation"""
    operation_type: str
    energy_micro_kwh: int
    emissions_micro_gco2: int
    region: str
    carbon_intensity: int
    was_optimized: bool = False
    optimization_type: Optional[str] = None  # 'cache', 'batch', 'defer'


@dataclass
class SCIScore:
    """Software Carbon Intensity score"""
    score: float  # gCO2eq per functional unit
    total_energy_kwh: float
    total_emissions_gco2: float
    functional_units: int
    functional_unit_type: str
    embodied_carbon_gco2: float


@dataclass
class CarbonDashboard:
    """Data for carbon dashboard display"""
    sci_score: float
    total_emissions_gco2: float
    period_start: datetime
    period_end: datetime
    breakdown: Dict[str, float]
    trend: str  # 'improving', 'stable', 'worsening'
    cache_hit_rate: float
    recommendations: List[str]
    comparison_to_previous: float  # percentage change


class CarbonTracker:
    """
    Service for tracking and optimizing carbon footprint.

    Usage:
        tracker = CarbonTracker(db)

        # Track an AI operation
        await tracker.track_ai_operation(
            provider="anthropic",
            model="claude-3-haiku",
            tokens=1500,
            manuscript_id="..."
        )

        # Get dashboard data
        dashboard = await tracker.get_dashboard(days=30)
    """

    # Estimated embodied carbon per hour of compute (micro gCO2eq)
    EMBODIED_CARBON_PER_HOUR = 1000  # ~1 gCO2eq/hour

    def __init__(self, db: Session, region: str = "unknown"):
        self.db = db
        self.region = region
        self.carbon_intensity = CARBON_INTENSITY_BY_REGION.get(region, 400)

    async def track_operation(
        self,
        operation_type: OperationType,
        units: float = 1.0,
        manuscript_id: Optional[str] = None,
        subtype: Optional[str] = None,
        cache_hit: bool = False,
        batched: bool = False,
        deferred: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> CarbonMetricResult:
        """
        Track a generic operation and its carbon impact.

        Args:
            operation_type: Type of operation from OperationType enum
            units: Number of units (tokens/1000, MB, operations, etc.)
            manuscript_id: Optional manuscript for per-project tracking
            subtype: More specific operation type
            cache_hit: Was this served from cache?
            batched: Was this part of a batch?
            deferred: Was this carbon-aware scheduled?
            extra_metadata: Additional tracking data

        Returns:
            CarbonMetricResult with emissions data
        """
        # Calculate energy
        base_energy = ENERGY_ESTIMATES_MICRO_KWH.get(operation_type.value, 1)
        energy_micro_kwh = int(base_energy * units)

        # If cached, energy is near zero (just lookup)
        if cache_hit:
            energy_micro_kwh = max(1, energy_micro_kwh // 100)

        # Calculate emissions
        emissions_micro_gco2 = int(energy_micro_kwh * self.carbon_intensity / 1000)

        # Create metric record
        metric = CarbonMetric(
            operation_type=operation_type.value,
            operation_subtype=subtype,
            manuscript_id=manuscript_id,
            energy_micro_kwh=energy_micro_kwh,
            carbon_intensity=self.carbon_intensity,
            region=self.region,
            emissions_micro_gco2=emissions_micro_gco2,
            cache_hit=1 if cache_hit else 0,
            batched=1 if batched else 0,
            deferred=1 if deferred else 0,
        )

        # Add extra metadata
        if extra_metadata:
            if "tokens" in extra_metadata:
                metric.tokens_processed = extra_metadata["tokens"]
            if "bytes" in extra_metadata:
                metric.bytes_transferred = extra_metadata["bytes"]
            if "compute_ms" in extra_metadata:
                metric.compute_ms = extra_metadata["compute_ms"]
            if "provider" in extra_metadata:
                metric.ai_provider = extra_metadata["provider"]
            if "model" in extra_metadata:
                metric.ai_model = extra_metadata["model"]

        self.db.add(metric)
        self.db.commit()

        # Determine optimization type
        optimization_type = None
        if cache_hit:
            optimization_type = "cache"
        elif batched:
            optimization_type = "batch"
        elif deferred:
            optimization_type = "defer"

        return CarbonMetricResult(
            operation_type=operation_type.value,
            energy_micro_kwh=energy_micro_kwh,
            emissions_micro_gco2=emissions_micro_gco2,
            region=self.region,
            carbon_intensity=self.carbon_intensity,
            was_optimized=cache_hit or batched or deferred,
            optimization_type=optimization_type,
        )

    async def track_ai_operation(
        self,
        provider: str,
        model: str,
        tokens: int,
        manuscript_id: Optional[str] = None,
        request_type: Optional[str] = None,
        cache_hit: bool = False,
        batched: bool = False,
    ) -> CarbonMetricResult:
        """
        Track an AI API operation specifically.

        Args:
            provider: AI provider name (anthropic, openai, etc.)
            model: Model name
            tokens: Total tokens (input + output)
            manuscript_id: Optional manuscript ID
            request_type: Type of request (grammar_check, plot_analysis, etc.)
            cache_hit: Was this a cache hit?
            batched: Was this batched with other requests?
        """
        # Determine operation type based on model
        operation_type = OperationType.AI_REQUEST_MEDIUM  # default
        model_lower = model.lower()

        for model_prefix, op_type in AI_MODEL_SIZES.items():
            if model_prefix in model_lower:
                operation_type = op_type
                break

        # Units are per 1K tokens
        units = tokens / 1000.0

        return await self.track_operation(
            operation_type=operation_type,
            units=units,
            manuscript_id=manuscript_id,
            subtype=request_type,
            cache_hit=cache_hit,
            batched=batched,
            extra_metadata={
                "tokens": tokens,
                "provider": provider,
                "model": model,
            }
        )

    async def calculate_sci(
        self,
        start_date: datetime,
        end_date: datetime,
        functional_unit: str = "per_request",
        manuscript_id: Optional[str] = None,
    ) -> SCIScore:
        """
        Calculate Software Carbon Intensity score.

        SCI = ((E × I) + M) / R

        Args:
            start_date: Period start
            end_date: Period end
            functional_unit: What R represents ('per_request', 'per_user', 'per_manuscript')
            manuscript_id: Optional filter by manuscript

        Returns:
            SCIScore with detailed breakdown
        """
        query = self.db.query(CarbonMetric).filter(
            CarbonMetric.created_at >= start_date,
            CarbonMetric.created_at <= end_date,
        )

        if manuscript_id:
            query = query.filter(CarbonMetric.manuscript_id == manuscript_id)

        metrics = query.all()

        if not metrics:
            return SCIScore(
                score=0.0,
                total_energy_kwh=0.0,
                total_emissions_gco2=0.0,
                functional_units=0,
                functional_unit_type=functional_unit,
                embodied_carbon_gco2=0.0,
            )

        # Calculate totals
        total_energy_micro_kwh = sum(m.energy_micro_kwh for m in metrics)
        total_emissions_micro_gco2 = sum(m.emissions_micro_gco2 for m in metrics)

        # Convert to standard units
        total_energy_kwh = total_energy_micro_kwh / 1_000_000
        total_emissions_gco2 = total_emissions_micro_gco2 / 1_000_000

        # Estimate embodied carbon (simplified)
        hours = (end_date - start_date).total_seconds() / 3600
        embodied_carbon_gco2 = (hours * self.EMBODIED_CARBON_PER_HOUR) / 1_000_000

        # Determine R (functional units)
        if functional_unit == "per_request":
            R = len(metrics)
        elif functional_unit == "per_manuscript":
            R = len(set(m.manuscript_id for m in metrics if m.manuscript_id))
            R = max(R, 1)  # Avoid division by zero
        else:  # per_user - in this local-first app, assume 1 user
            R = 1

        # Calculate SCI
        sci_score = (total_emissions_gco2 + embodied_carbon_gco2) / R

        return SCIScore(
            score=round(sci_score, 6),
            total_energy_kwh=round(total_energy_kwh, 6),
            total_emissions_gco2=round(total_emissions_gco2, 6),
            functional_units=R,
            functional_unit_type=functional_unit,
            embodied_carbon_gco2=round(embodied_carbon_gco2, 6),
        )

    async def get_dashboard(
        self,
        days: int = 30,
        manuscript_id: Optional[str] = None,
    ) -> CarbonDashboard:
        """
        Get carbon dashboard data for display.

        Args:
            days: Number of days to include
            manuscript_id: Optional filter by manuscript

        Returns:
            CarbonDashboard with all metrics and recommendations
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        previous_start = start_date - timedelta(days=days)

        # Current period
        sci = await self.calculate_sci(start_date, end_date, "per_request", manuscript_id)

        # Previous period for comparison
        previous_sci = await self.calculate_sci(previous_start, start_date, "per_request", manuscript_id)

        # Calculate trend
        if previous_sci.total_emissions_gco2 > 0:
            change = ((sci.total_emissions_gco2 - previous_sci.total_emissions_gco2)
                     / previous_sci.total_emissions_gco2) * 100
            if change < -5:
                trend = "improving"
            elif change > 5:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            change = 0.0
            trend = "stable"

        # Get breakdown by operation type
        breakdown = await self._get_emissions_breakdown(start_date, end_date, manuscript_id)

        # Calculate cache hit rate
        cache_hit_rate = await self._get_cache_hit_rate(start_date, end_date, manuscript_id)

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            sci, breakdown, cache_hit_rate
        )

        return CarbonDashboard(
            sci_score=sci.score,
            total_emissions_gco2=sci.total_emissions_gco2,
            period_start=start_date,
            period_end=end_date,
            breakdown=breakdown,
            trend=trend,
            cache_hit_rate=cache_hit_rate,
            recommendations=recommendations,
            comparison_to_previous=round(change, 2),
        )

    async def _get_emissions_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
        manuscript_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get emissions breakdown by operation type"""
        query = self.db.query(
            CarbonMetric.operation_type,
            func.sum(CarbonMetric.emissions_micro_gco2).label('total')
        ).filter(
            CarbonMetric.created_at >= start_date,
            CarbonMetric.created_at <= end_date,
        ).group_by(CarbonMetric.operation_type)

        if manuscript_id:
            query = query.filter(CarbonMetric.manuscript_id == manuscript_id)

        results = query.all()

        return {
            row[0]: row[1] / 1_000_000  # Convert to gCO2eq
            for row in results
        }

    async def _get_cache_hit_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        manuscript_id: Optional[str] = None,
    ) -> float:
        """Calculate cache hit rate for the period"""
        query = self.db.query(CarbonMetric).filter(
            CarbonMetric.created_at >= start_date,
            CarbonMetric.created_at <= end_date,
        )

        if manuscript_id:
            query = query.filter(CarbonMetric.manuscript_id == manuscript_id)

        metrics = query.all()

        if not metrics:
            return 0.0

        cache_hits = sum(1 for m in metrics if m.cache_hit)
        return round((cache_hits / len(metrics)) * 100, 2)

    async def _generate_recommendations(
        self,
        sci: SCIScore,
        breakdown: Dict[str, float],
        cache_hit_rate: float,
    ) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []

        # Cache hit rate recommendations
        if cache_hit_rate < 20:
            recommendations.append(
                "Enable AI response caching - current cache hit rate is only "
                f"{cache_hit_rate}%. Caching common grammar and style checks "
                "could reduce emissions by 30-50%."
            )
        elif cache_hit_rate < 50:
            recommendations.append(
                f"Cache hit rate is {cache_hit_rate}%. Consider expanding "
                "cache coverage to include more AI operation types."
            )

        # AI operation recommendations
        ai_emissions = sum(
            v for k, v in breakdown.items()
            if k.startswith("ai_request")
        )
        total_emissions = sum(breakdown.values())

        if total_emissions > 0 and ai_emissions / total_emissions > 0.7:
            recommendations.append(
                "AI operations account for over 70% of emissions. Consider "
                "using smaller models (Haiku/GPT-3.5) for simple tasks like "
                "grammar checking."
            )

        # Model-specific recommendations
        if "ai_request_large" in breakdown and breakdown["ai_request_large"] > 0:
            large_pct = (breakdown["ai_request_large"] / total_emissions * 100) if total_emissions > 0 else 0
            if large_pct > 30:
                recommendations.append(
                    f"Large AI models account for {large_pct:.1f}% of emissions. "
                    "Reserve these for complex tasks; use medium models for "
                    "most analysis."
                )

        # Regional recommendations
        if self.carbon_intensity > 500:
            recommendations.append(
                f"Your region has high carbon intensity ({self.carbon_intensity} gCO2/kWh). "
                "If possible, schedule heavy AI tasks during off-peak hours or "
                "consider a cloud region with cleaner energy."
            )

        # If doing well, acknowledge it
        if not recommendations:
            recommendations.append(
                "Your carbon footprint is well-optimized. Keep using caching "
                "and appropriate model sizes."
            )

        return recommendations

    async def check_budget(
        self,
        manuscript_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if there's a carbon budget and current usage status.

        Returns None if no budget is set, otherwise returns budget status.
        """
        query = self.db.query(CarbonBudget).filter(
            CarbonBudget.is_active == 1
        )

        if manuscript_id:
            query = query.filter(
                (CarbonBudget.manuscript_id == manuscript_id) |
                (CarbonBudget.manuscript_id.is_(None))
            )
        else:
            query = query.filter(CarbonBudget.manuscript_id.is_(None))

        budget = query.first()

        if not budget:
            return None

        usage_pct = (budget.current_usage_micro_gco2 / budget.budget_micro_gco2 * 100
                    if budget.budget_micro_gco2 > 0 else 0)

        return {
            "budget_gco2": budget.budget_micro_gco2 / 1_000_000,
            "usage_gco2": budget.current_usage_micro_gco2 / 1_000_000,
            "usage_percentage": round(usage_pct, 2),
            "period": budget.budget_period,
            "warn_threshold": budget.warn_threshold,
            "limit_threshold": budget.limit_threshold,
            "limit_action": budget.limit_action,
            "is_over_warn": usage_pct >= budget.warn_threshold,
            "is_over_limit": usage_pct >= budget.limit_threshold,
        }


# Factory function
def get_carbon_tracker(db: Session, region: str = "unknown") -> CarbonTracker:
    """Get a CarbonTracker instance"""
    return CarbonTracker(db, region)
