from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.dashboard import (
    ActivityFeedItem,
    DashboardFilters,
    DashboardKPIs,
    DistributionResponse,
    TopContract,
    TopStakeholder,
    TrendResponse,
)
from app.services import dashboard_service as svc
from app.services.cache_service import invalidate_all_analytics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=DashboardKPIs)
async def dashboard_kpis(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    contract_type: str | None = Query(default=None),
    department: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DashboardKPIs:
    filters = DashboardFilters(
        date_from=date_from, date_to=date_to,
        contract_type=contract_type, department=department,
    )
    return await svc.get_dashboard_kpis(db, filters)


@router.get("/trends/emails", response_model=TrendResponse)
async def email_volume_trend(
    period: str = Query(default="day"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TrendResponse:
    return await svc.get_email_volume_trend(db, period=period, date_from=date_from, date_to=date_to)


@router.get("/trends/contracts", response_model=TrendResponse)
async def contract_creation_trend(
    period: str = Query(default="month"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TrendResponse:
    return await svc.get_contract_creation_trend(db, period=period, date_from=date_from, date_to=date_to)


@router.get("/trends/sla", response_model=TrendResponse)
async def sla_breach_trend(
    period: str = Query(default="month"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TrendResponse:
    return await svc.get_sla_breach_trend(db, period=period, date_from=date_from, date_to=date_to)


@router.get("/trends/cycle-time", response_model=TrendResponse)
async def avg_cycle_time_trend(
    period: str = Query(default="month"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TrendResponse:
    return await svc.get_avg_cycle_time_trend(db, period=period, date_from=date_from, date_to=date_to)


@router.get("/distributions/contract-types", response_model=DistributionResponse)
async def contract_type_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_contract_type_distribution(db)


@router.get("/distributions/stages", response_model=DistributionResponse)
async def stage_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_contract_stage_distribution(db)


@router.get("/distributions/categories", response_model=DistributionResponse)
async def email_category_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_email_category_distribution(db)


@router.get("/distributions/urgency", response_model=DistributionResponse)
async def urgency_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_email_urgency_distribution(db)


@router.get("/distributions/sentiment", response_model=DistributionResponse)
async def sentiment_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_email_sentiment_distribution(db)


@router.get("/distributions/departments", response_model=DistributionResponse)
async def department_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_department_distribution(db)


@router.get("/distributions/risk-scores", response_model=DistributionResponse)
async def risk_score_distribution(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_risk_score_distribution(db)


@router.get("/distributions/clauses", response_model=DistributionResponse)
async def clause_frequency(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DistributionResponse:
    return await svc.get_clause_frequency_distribution(db)


@router.get("/top/bottlenecks", response_model=list[TopContract])
async def top_bottleneck_contracts(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[TopContract]:
    return await svc.get_top_bottleneck_contracts(db, limit=limit)


@router.get("/top/risks", response_model=list[TopContract])
async def top_risk_contracts(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[TopContract]:
    return await svc.get_top_risk_contracts(db, limit=limit)


@router.get("/top/stakeholders", response_model=list[TopStakeholder])
async def top_active_stakeholders(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[TopStakeholder]:
    return await svc.get_top_active_stakeholders(db, limit=limit)


@router.get("/recent-activity", response_model=list[ActivityFeedItem])
async def recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[ActivityFeedItem]:
    return await svc.get_recent_activity(db, limit=limit)


@router.post("/cache/invalidate")
async def invalidate_cache(_: User = Depends(get_current_user)) -> dict:
    deleted = await invalidate_all_analytics()
    return {"deleted_keys": deleted, "status": "ok"}
