from __future__ import annotations

from collections import Counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.contract import Contract
from app.models.processing_job import ProcessingJobType
from app.models.stakeholder import Stakeholder
from app.models.user import User
from app.schemas.contract import ContractDetail, ContractResponse, ContractStats, ContractTimeline
from app.schemas.stakeholder import StakeholderResponse
from app.services.contract_service import start_contract_extraction_job
from app.services.processing_job_service import create_job, latest_job

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


def _job_to_progress(job) -> dict:
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
    pending = await latest_job(db, current_user.id, ProcessingJobType.contract_extraction)
    if pending and pending.status.value == "in_progress":
        return _job_to_progress(pending)

    job = await create_job(db, current_user.id, ProcessingJobType.contract_extraction)
    await start_contract_extraction_job(job, AsyncSessionLocal)
    return _job_to_progress(job)


@router.get("/status")
async def extraction_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    job = await latest_job(db, current_user.id, ProcessingJobType.contract_extraction)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No contract extraction job found")
    return _job_to_progress(job)


@router.get("", response_model=list[ContractResponse])
async def list_contracts(
    agreement_type: str | None = Query(default=None),
    counterparty: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    min_risk_score: float | None = Query(default=None),
    max_risk_score: float | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Contract]:
    query = select(Contract)
    if agreement_type:
        query = query.where(Contract.agreement_type == agreement_type)
    if counterparty:
        query = query.where(Contract.counterparty_name.ilike(f"%{counterparty}%"))
    if stage:
        query = query.where(Contract.current_stage == stage)
    if min_risk_score is not None:
        query = query.where(Contract.risk_score >= min_risk_score)
    if max_risk_score is not None:
        query = query.where(Contract.risk_score <= max_risk_score)

    result = await db.execute(query.order_by(Contract.updated_at.desc()))
    return list(result.scalars().all())


@router.get("/search", response_model=list[ContractResponse])
async def search_contracts(
    q: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Contract]:
    result = await db.execute(
        select(Contract).where(
            Contract.agreement_name.ilike(f"%{q}%")
            | Contract.counterparty_name.ilike(f"%{q}%")
            | Contract.agreement_type.ilike(f"%{q}%")
        )
    )
    return list(result.scalars().all())


@router.get("/stats", response_model=ContractStats)
async def contract_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ContractStats:
    total = (await db.execute(select(func.count()).select_from(Contract))).scalar_one()
    rows = await db.execute(select(Contract.agreement_type).where(Contract.agreement_type.is_not(None)))
    by_type = dict(Counter(item[0] for item in rows.all()))
    breaches = (await db.execute(select(func.count()).select_from(Contract).where(Contract.sla_breached.is_(True)))).scalar_one()
    return ContractStats(total_contracts=int(total), by_type=by_type, sla_breaches=int(breaches))


@router.get("/{contract_id}", response_model=ContractDetail)
async def contract_detail(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Contract:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract


@router.get("/{contract_id}/timeline", response_model=ContractTimeline)
async def contract_timeline(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ContractTimeline:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return ContractTimeline(stage_history=contract.stage_history or [])


@router.get("/{contract_id}/clauses")
async def contract_clauses(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract.key_clauses or []


@router.get("/{contract_id}/stakeholders", response_model=list[StakeholderResponse])
async def contract_stakeholders(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Stakeholder]:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    result = await db.execute(select(Stakeholder).where(Stakeholder.email_address == contract.counterparty_email))
    return list(result.scalars().all())
