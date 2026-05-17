from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.contract_analytics import (
    BottleneckReport,
    ContractTimeline,
    CycleTimeDistribution,
    LifecycleStory,
    NegotiationAnalysis,
    SLABreachReport,
    SLAComplianceTrend,
    StageDuration,
    StageDurationStats,
    StageHealth,
    StageTransition,
    VelocityTrend,
)
from app.services import contract_analytics_service as svc

router = APIRouter(prefix="/api/analytics/contracts", tags=["contract-analytics"])


@router.get("/timeline/{contract_id}", response_model=ContractTimeline)
async def contract_timeline(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ContractTimeline:
    return await svc.get_contract_timeline(db, contract_id)


@router.get("/stage-durations/{contract_id}", response_model=list[StageDuration])
async def contract_stage_durations(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[StageDuration]:
    return await svc.get_contract_stage_durations(db, contract_id)


@router.get("/lifecycle-story/{contract_id}", response_model=LifecycleStory)
async def lifecycle_story(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> LifecycleStory:
    return await svc.get_lifecycle_story(db, contract_id)


@router.get("/stage-duration-stats", response_model=list[StageDurationStats])
async def stage_duration_stats(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[StageDurationStats]:
    return await svc.get_stage_duration_stats(db)


@router.get("/bottlenecks", response_model=list[BottleneckReport])
async def bottleneck_analysis(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[BottleneckReport]:
    return await svc.get_bottleneck_analysis(db)


@router.get("/sla-breaches", response_model=SLABreachReport)
async def sla_breach_report(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SLABreachReport:
    return await svc.get_sla_breach_report(db, date_from=date_from, date_to=date_to)


@router.get("/sla-compliance", response_model=SLAComplianceTrend)
async def sla_compliance(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    period: str = Query(default="month"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SLAComplianceTrend:
    return await svc.get_sla_compliance_rate(db, date_from=date_from, date_to=date_to, period=period)


@router.get("/stage-transitions", response_model=list[StageTransition])
async def stage_transitions(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[StageTransition]:
    return await svc.get_stage_transition_matrix(db)


@router.get("/negotiation-analysis", response_model=NegotiationAnalysis)
async def negotiation_analysis(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> NegotiationAnalysis:
    return await svc.get_negotiation_loop_analysis(db)


@router.get("/cycle-time-distribution", response_model=CycleTimeDistribution)
async def cycle_time_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CycleTimeDistribution:
    return await svc.get_cycle_time_distribution(db)


@router.get("/velocity-trend", response_model=VelocityTrend)
async def velocity_trend(
    period: str = Query(default="week"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> VelocityTrend:
    return await svc.get_contract_velocity_trend(db, period=period)


@router.get("/stage-health", response_model=StageHealth)
async def stage_health(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> StageHealth:
    return await svc.get_stage_health_overview(db)
