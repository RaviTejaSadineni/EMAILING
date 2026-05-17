from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.contract import Contract
from app.models.processing_job import ProcessingJobType
from app.models.user import User
from app.schemas.lifecycle import (
    BottleneckAnalysis,
    LifecycleOverview,
    NegotiationAnalysis,
    SLABreachReport,
    StageDefinition,
    StageMetrics,
)
from app.services.lifecycle_service import STAGE_DEFINITIONS, start_lifecycle_detection_job
from app.services.processing_job_service import create_job, latest_job

router = APIRouter(prefix="/api/lifecycle", tags=["lifecycle"])


def _job_payload(job) -> dict:
    return {
        "job_id": job.id,
        "status": job.status.value,
        "progress": job.progress,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "error_message": job.error_message,
    }


@router.post("/start-detection", status_code=status.HTTP_202_ACCEPTED)
async def start_detection(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    pending = await latest_job(db, current_user.id, ProcessingJobType.lifecycle_detection)
    if pending and pending.status.value == "in_progress":
        return _job_payload(pending)

    job = await create_job(db, current_user.id, ProcessingJobType.lifecycle_detection)
    await start_lifecycle_detection_job(job, AsyncSessionLocal)
    return _job_payload(job)


@router.get("/status")
async def detection_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    job = await latest_job(db, current_user.id, ProcessingJobType.lifecycle_detection)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No lifecycle job found")
    return _job_payload(job)


@router.get("/stages", response_model=list[StageDefinition])
async def stage_definitions(current_user: User = Depends(get_current_user)) -> list[StageDefinition]:
    return [StageDefinition(**stage) for stage in STAGE_DEFINITIONS]


@router.get("/overview", response_model=LifecycleOverview)
async def lifecycle_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> LifecycleOverview:
    rows = await db.execute(select(Contract.current_stage))
    counts = Counter(item[0] or "Unknown" for item in rows.all())
    return LifecycleOverview(contracts_per_stage=dict(counts), avg_time_per_stage={stage["name"]: 0 for stage in STAGE_DEFINITIONS})


@router.get("/bottlenecks", response_model=BottleneckAnalysis)
async def bottlenecks(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BottleneckAnalysis:
    rows = await db.execute(select(Contract).where(Contract.sla_breached.is_(True)))
    return BottleneckAnalysis(
        bottlenecks=[
            {"contract_id": str(contract.id), "stage": contract.current_stage, "reasons": contract.delay_reasons or []}
            for contract in rows.scalars().all()
        ]
    )


@router.get("/sla-breaches", response_model=SLABreachReport)
async def sla_breaches(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SLABreachReport:
    rows = await db.execute(select(Contract).where(Contract.sla_breached.is_(True)))
    return SLABreachReport(
        items=[
            {"contract_id": str(contract.id), "agreement_name": contract.agreement_name, "delay_reasons": contract.delay_reasons}
            for contract in rows.scalars().all()
        ]
    )


@router.get("/stage-metrics", response_model=StageMetrics)
async def stage_metrics(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StageMetrics:
    return StageMetrics(metrics={stage["name"]: {"avg": 0, "min": 0, "max": 0, "p90": 0} for stage in STAGE_DEFINITIONS})


@router.get("/negotiation-analysis", response_model=NegotiationAnalysis)
async def negotiation_analysis(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NegotiationAnalysis:
    rows = await db.execute(select(Contract.key_clauses))
    clause_counter = Counter()
    for row in rows.all():
        for clause in row[0] or []:
            clause_counter[clause.get("type", "Unknown")] += 1
    return NegotiationAnalysis(
        average_rounds=0,
        most_negotiated_clauses=[{"type": key, "count": value} for key, value in clause_counter.most_common(5)],
    )
