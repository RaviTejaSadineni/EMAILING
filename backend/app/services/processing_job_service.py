from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob, ProcessingJobStatus, ProcessingJobType
from app.websocket_manager import websocket_manager


async def create_job(db: AsyncSession, user_id: UUID, job_type: ProcessingJobType, total_items: int = 0) -> ProcessingJob:
    job = ProcessingJob(
        user_id=user_id,
        job_type=job_type,
        status=ProcessingJobStatus.pending,
        total_items=total_items,
        processed_items=0,
        progress=0.0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def latest_job(db: AsyncSession, user_id: UUID, job_type: ProcessingJobType) -> ProcessingJob | None:
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.user_id == user_id, ProcessingJob.job_type == job_type)
        .order_by(ProcessingJob.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def broadcast_job(job: ProcessingJob, extra: dict | None = None) -> None:
    payload = {
        "job_id": str(job.id),
        "job_type": job.job_type.value,
        "status": job.status.value,
        "progress": job.progress,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "error_message": job.error_message,
    }
    if extra:
        payload.update(extra)
    await websocket_manager.broadcast(job.id, json.dumps(payload, default=str))


async def mark_running(db: AsyncSession, job: ProcessingJob) -> ProcessingJob:
    job.status = ProcessingJobStatus.in_progress
    job.started_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(job)
    await broadcast_job(job)
    return job


async def mark_progress(db: AsyncSession, job: ProcessingJob, processed_items: int, total_items: int | None = None, extra: dict | None = None) -> ProcessingJob:
    job.processed_items = processed_items
    if total_items is not None:
        job.total_items = total_items
    job.progress = round((job.processed_items / job.total_items) * 100, 2) if job.total_items else 0.0
    await db.commit()
    await db.refresh(job)
    await broadcast_job(job, extra=extra)
    return job


async def mark_completed(db: AsyncSession, job: ProcessingJob, extra: dict | None = None) -> ProcessingJob:
    job.status = ProcessingJobStatus.completed
    job.progress = 100.0
    job.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(job)
    await broadcast_job(job, extra=extra)
    return job


async def mark_failed(db: AsyncSession, job: ProcessingJob, error: str) -> ProcessingJob:
    job.status = ProcessingJobStatus.failed
    job.error_message = error
    job.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(job)
    await broadcast_job(job)
    return job
