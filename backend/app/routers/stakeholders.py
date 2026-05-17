from __future__ import annotations

from collections import Counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.contract import Contract
from app.models.email import Email
from app.models.processing_job import ProcessingJobType
from app.models.stakeholder import Stakeholder
from app.models.user import User
from app.schemas.contract import ContractResponse
from app.schemas.stakeholder import DepartmentStats, StakeholderAnalytics, StakeholderComparison, StakeholderDetail, StakeholderResponse
from app.services.processing_job_service import create_job, latest_job
from app.services.stakeholder_service import start_stakeholder_extraction_job

router = APIRouter(prefix="/api/stakeholders", tags=["stakeholders"])


def _job_payload(job) -> dict:
    return {
        "job_id": job.id,
        "status": job.status.value,
        "progress": job.progress,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "error_message": job.error_message,
    }


@router.post("/start-extraction", status_code=status.HTTP_202_ACCEPTED)
async def start_extraction(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    pending = await latest_job(db, current_user.id, ProcessingJobType.stakeholder_extraction)
    if pending and pending.status.value == "in_progress":
        return _job_payload(pending)

    job = await create_job(db, current_user.id, ProcessingJobType.stakeholder_extraction)
    await start_stakeholder_extraction_job(job, AsyncSessionLocal)
    return _job_payload(job)


@router.get("/status")
async def extraction_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    job = await latest_job(db, current_user.id, ProcessingJobType.stakeholder_extraction)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stakeholder extraction job found")
    return _job_payload(job)


@router.get("", response_model=list[StakeholderResponse])
async def list_stakeholders(
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    is_internal: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Stakeholder]:
    query = select(Stakeholder)
    if department:
        query = query.where(Stakeholder.department == department)
    if role:
        query = query.where(Stakeholder.role == role)
    if is_internal is not None:
        query = query.where(Stakeholder.is_internal.is_(is_internal))

    result = await db.execute(query.order_by(Stakeholder.total_emails.desc()))
    return list(result.scalars().all())


@router.get("/comparison", response_model=StakeholderComparison)
async def compare_stakeholders(
    ids: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StakeholderComparison:
    parsed_ids = [UUID(item.strip()) for item in ids.split(",") if item.strip()]
    result = await db.execute(select(Stakeholder).where(Stakeholder.id.in_(parsed_ids)))
    return StakeholderComparison(items=[StakeholderResponse.model_validate(item) for item in result.scalars().all()])


@router.get("/stats")
async def stakeholder_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    rows = await db.execute(select(Stakeholder.department))
    counts = Counter(item[0] or "Unknown" for item in rows.all())
    return {"total": sum(counts.values()), "by_department": dict(counts)}


@router.get("/departments", response_model=list[DepartmentStats])
async def department_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[DepartmentStats]:
    rows = await db.execute(select(Stakeholder.department))
    counts = Counter(item[0] or "Unknown" for item in rows.all())
    return [DepartmentStats(department=dep, count=count) for dep, count in counts.items()]


@router.get("/{stakeholder_id}", response_model=StakeholderDetail)
async def stakeholder_detail(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Stakeholder:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stakeholder not found")
    return stakeholder


@router.get("/{stakeholder_id}/contracts", response_model=list[ContractResponse])
async def stakeholder_contracts(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Contract]:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stakeholder not found")
    rows = await db.execute(select(Contract).where(Contract.counterparty_email == stakeholder.email_address))
    return list(rows.scalars().all())


@router.get("/{stakeholder_id}/emails")
async def stakeholder_emails(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stakeholder not found")
    rows = await db.execute(select(Email).where(Email.from_address == stakeholder.email_address).order_by(Email.date.desc()))
    return [{"id": str(email.id), "subject": email.subject, "date": email.date} for email in rows.scalars().all()]


@router.get("/{stakeholder_id}/analytics", response_model=StakeholderAnalytics)
async def stakeholder_analytics(
    stakeholder_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StakeholderAnalytics:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stakeholder not found")
    return StakeholderAnalytics(
        response_time_distribution=stakeholder.response_time_distribution,
        communication_patterns=stakeholder.communication_patterns,
        influence_score=stakeholder.influence_score,
    )
