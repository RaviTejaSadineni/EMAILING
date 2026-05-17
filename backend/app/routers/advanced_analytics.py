from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.advanced_analytics import (
    AnomalyList,
    BottleneckPrediction,
    CompletionPrediction,
    ContractInsights,
    EscalationPattern,
    ProcessImprovement,
    RiskAlert,
    RiskFactors,
    RiskMatrix,
    RiskTrend,
    SentimentByEntity,
    SentimentTimeline,
    WeeklyInsights,
    WhatIfResult,
    WorkloadForecast,
)
from app.services import advanced_analytics_service as svc

router = APIRouter(prefix="/api/analytics/advanced", tags=["advanced-analytics"])


# ── Sentiment ────────────────────────────────────────────────────────────────

@router.get("/sentiment/timeline/{contract_id}", response_model=SentimentTimeline)
async def sentiment_timeline(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SentimentTimeline:
    return await svc.get_sentiment_timeline(db, contract_id)


@router.get("/sentiment/by-stakeholder", response_model=list[SentimentByEntity])
async def sentiment_by_stakeholder(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[SentimentByEntity]:
    return await svc.get_sentiment_by_stakeholder(db)


@router.get("/sentiment/by-stage", response_model=list[SentimentByEntity])
async def sentiment_by_stage(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[SentimentByEntity]:
    return await svc.get_sentiment_by_stage(db)


@router.get("/sentiment/escalation-patterns", response_model=list[EscalationPattern])
async def escalation_patterns(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[EscalationPattern]:
    return await svc.get_escalation_patterns(db)


@router.get("/sentiment/correlation")
async def sentiment_correlation(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> dict:
    return await svc.get_sentiment_correlation(db)


# ── Risk ─────────────────────────────────────────────────────────────────────

@router.get("/risk/matrix", response_model=RiskMatrix)
async def risk_matrix(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> RiskMatrix:
    return await svc.get_risk_matrix(db)


@router.get("/risk/factors/{contract_id}", response_model=RiskFactors)
async def risk_factors(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> RiskFactors:
    return await svc.get_risk_factors_breakdown(db, contract_id)


@router.get("/risk/trend", response_model=RiskTrend)
async def risk_trend(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> RiskTrend:
    return await svc.get_risk_trend(db)


@router.get("/risk/alerts", response_model=list[RiskAlert])
async def risk_alerts(
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[RiskAlert]:
    return await svc.get_high_risk_alerts(db, threshold=threshold)


# ── Predictions ───────────────────────────────────────────────────────────────

@router.get("/predictions/completion/{contract_id}", response_model=CompletionPrediction)
async def predict_completion(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CompletionPrediction:
    return await svc.predict_contract_completion(db, contract_id)


@router.get("/predictions/bottleneck/{contract_id}", response_model=BottleneckPrediction)
async def predict_bottleneck(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> BottleneckPrediction:
    return await svc.predict_bottleneck(db, contract_id)


@router.get("/predictions/workload", response_model=WorkloadForecast)
async def predict_workload(
    department: str = Query(...),
    period: str = Query(default="month"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> WorkloadForecast:
    return await svc.predict_workload(db, department=department, period=period)


class WhatIfRequest(BaseModel):
    contract_id: UUID
    scenario: str


@router.post("/predictions/what-if", response_model=WhatIfResult)
async def what_if_analysis(
    body: WhatIfRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> WhatIfResult:
    return await svc.get_what_if_analysis(db, body.contract_id, body.scenario)


# ── Anomalies ──────────────────────────────────────────────────────────────────

@router.get("/anomalies", response_model=AnomalyList)
async def anomalies(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> AnomalyList:
    return await svc.detect_anomalies(db)


# ── Insights ──────────────────────────────────────────────────────────────────

@router.get("/insights/weekly", response_model=WeeklyInsights)
async def weekly_insights(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> WeeklyInsights:
    return await svc.generate_weekly_insights(db)


@router.get("/insights/contract/{contract_id}", response_model=ContractInsights)
async def contract_insights(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ContractInsights:
    return await svc.generate_contract_insights(db, contract_id)


@router.get("/insights/process-improvements", response_model=list[ProcessImprovement])
async def process_improvements(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[ProcessImprovement]:
    return await svc.generate_process_improvement_suggestions(db)
