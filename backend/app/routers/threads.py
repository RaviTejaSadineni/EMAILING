from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.email import Email
from app.models.email_thread import EmailThread
from app.models.email_thread_link import EmailThreadLink
from app.models.processing_job import ProcessingJobType
from app.models.user import User
from app.schemas.thread import MergeProgress, ThreadDetail, ThreadListResponse, ThreadResponse, ThreadStats
from app.services.processing_job_service import create_job, latest_job
from app.services.thread_merge_service import start_thread_merge_job

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _job_to_progress(job) -> MergeProgress:
    return MergeProgress(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        total_items=job.total_items,
        processed_items=job.processed_items,
        error_message=job.error_message,
    )


@router.post("/start-merge", response_model=MergeProgress, status_code=status.HTTP_202_ACCEPTED)
async def start_merge(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> MergeProgress:
    pending = await latest_job(db, current_user.id, ProcessingJobType.thread_merge)
    if pending and pending.status.value == "in_progress":
        return _job_to_progress(pending)

    job = await create_job(db, current_user.id, ProcessingJobType.thread_merge)
    await start_thread_merge_job(job, AsyncSessionLocal)
    return _job_to_progress(job)


@router.get("/status", response_model=MergeProgress)
async def merge_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> MergeProgress:
    job = await latest_job(db, current_user.id, ProcessingJobType.thread_merge)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No thread merge job found")
    return _job_to_progress(job)


@router.get("", response_model=ThreadListResponse)
async def list_threads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ThreadListResponse:
    total = (await db.execute(select(func.count()).select_from(EmailThread))).scalar_one()
    result = await db.execute(select(EmailThread).offset((page - 1) * page_size).limit(page_size).order_by(EmailThread.last_date.desc()))
    return ThreadListResponse(items=[ThreadResponse.model_validate(item) for item in result.scalars().all()], total=total)


@router.get("/stats", response_model=ThreadStats)
async def thread_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ThreadStats:
    total = (await db.execute(select(func.count()).select_from(EmailThread))).scalar_one()
    avg = (await db.execute(select(func.avg(EmailThread.email_count)))).scalar_one() or 0.0
    return ThreadStats(total_threads=int(total), avg_emails_per_thread=float(avg))


@router.get("/{thread_id}", response_model=ThreadDetail)
async def thread_detail(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ThreadDetail:
    thread = await db.get(EmailThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    email_rows = await db.execute(
        select(Email)
        .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
        .where(EmailThreadLink.thread_id == thread_id)
        .order_by(Email.date.asc())
    )
    emails = [
        {
            "id": str(email.id),
            "subject": email.subject,
            "from_address": email.from_address,
            "to_addresses": email.to_addresses,
            "cc_addresses": email.cc_addresses,
            "date": email.date,
        }
        for email in email_rows.scalars().all()
    ]
    return ThreadDetail(**ThreadResponse.model_validate(thread).model_dump(), emails=emails)


@router.get("/{thread_id}/emails")
async def thread_emails(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    email_rows = await db.execute(
        select(Email)
        .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
        .where(EmailThreadLink.thread_id == thread_id)
        .order_by(Email.date.asc())
    )
    return [
        {
            "id": str(email.id),
            "subject": email.subject,
            "from_address": email.from_address,
            "to_addresses": email.to_addresses,
            "cc_addresses": email.cc_addresses,
            "date": email.date,
        }
        for email in email_rows.scalars().all()
    ]


@router.post("/{thread_id}/split")
async def split_thread(thread_id: UUID, current_user: User = Depends(get_current_user)) -> dict:
    return {"status": "ok", "message": f"Manual split placeholder for thread {thread_id}"}


@router.post("/merge")
async def manual_merge_threads(source_thread_id: UUID, target_thread_id: UUID, current_user: User = Depends(get_current_user)) -> dict:
    return {"status": "ok", "message": f"Manual merge placeholder {source_thread_id} -> {target_thread_id}"}
