from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.stakeholder_analytics import (
    AIRecommendation,
    CommunicationNetwork,
    ContractInvolvement,
    DepartmentAnalytics,
    DepartmentComparison,
    ResponseTimeTrend,
    StakeholderComparison,
    StakeholderPerformance,
    StakeholderRanking,
    WorkloadBalance,
    WorkloadTimeline,
)
from app.services import stakeholder_analytics_service as svc

router = APIRouter(prefix="/api/analytics/stakeholders", tags=["stakeholder-analytics"])


@router.get("/{stakeholder_id}/performance", response_model=StakeholderPerformance)
async def stakeholder_performance(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> StakeholderPerformance:
    result = await svc.get_stakeholder_performance(db, stakeholder_id)
    if result is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stakeholder not found")
    return result


@router.get("/{stakeholder_id}/response-time-trend", response_model=ResponseTimeTrend)
async def response_time_trend(
    stakeholder_id: UUID,
    period: str = Query(default="week"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ResponseTimeTrend:
    return await svc.get_stakeholder_response_time_trend(db, stakeholder_id, period=period)


@router.get("/{stakeholder_id}/workload", response_model=WorkloadTimeline)
async def workload_timeline(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> WorkloadTimeline:
    return await svc.get_stakeholder_workload_timeline(db, stakeholder_id)


@router.get("/{stakeholder_id}/contracts", response_model=list[ContractInvolvement])
async def stakeholder_contracts(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[ContractInvolvement]:
    return await svc.get_stakeholder_contracts_detail(db, stakeholder_id)


@router.get("/{stakeholder_id}/network", response_model=CommunicationNetwork)
async def communication_network(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CommunicationNetwork:
    return await svc.get_stakeholder_communication_network(db, stakeholder_id)


@router.get("/{stakeholder_id}/recommendations", response_model=AIRecommendation)
async def ai_recommendations(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> AIRecommendation:
    return await svc.get_ai_recommendations(db, stakeholder_id)


@router.get("/comparison", response_model=StakeholderComparison)
async def compare_stakeholders(
    ids: str = Query(..., description="Comma-separated stakeholder IDs"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> StakeholderComparison:
    stakeholder_ids = [i.strip() for i in ids.split(",") if i.strip()]
    return await svc.get_stakeholder_comparison(db, stakeholder_ids)


@router.get("/departments", response_model=DepartmentAnalytics)
async def department_analytics(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DepartmentAnalytics:
    return await svc.get_department_analytics(db)


@router.get("/departments/comparison", response_model=DepartmentComparison)
async def department_comparison(
    dept1: str = Query(...),
    dept2: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> DepartmentComparison:
    return await svc.get_department_comparison(db, dept1, dept2)


@router.get("/rankings", response_model=list[StakeholderRanking])
async def stakeholder_rankings(
    metric: str = Query(default="response_time"),
    order: str = Query(default="asc"),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[StakeholderRanking]:
    return await svc.get_stakeholder_rankings(db, metric=metric, order=order, limit=limit)


@router.get("/workload-balance", response_model=WorkloadBalance)
async def workload_balance(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> WorkloadBalance:
    return await svc.get_workload_balance(db)


@router.get("/communication-network", response_model=CommunicationNetwork)
async def full_communication_network(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CommunicationNetwork:
    return await svc.get_communication_network(db)
