from __future__ import annotations

from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.import_job import ImportJob, ImportStatus
from app.models.user import User
from app.schemas.import_job import ChunkUploadRequest, ImportJobResponse, ImportStats
from app.services.import_service import cancel_import_job, get_upload_path, start_import_job

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/upload", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
async def upload_mbox(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    if not file.filename or not file.filename.lower().endswith(".mbox"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .mbox files are supported")

    job = ImportJob(
        user_id=current_user.id,
        filename=file.filename,
        file_size=0,
        status=ImportStatus.pending,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    upload_path = get_upload_path(job.id)
    file_size = 0
    async with aiofiles.open(upload_path, "wb") as out:
        while chunk := await file.read(10 * 1024 * 1024):
            file_size += len(chunk)
            await out.write(chunk)

    job.file_size = file_size
    job.upload_path = str(upload_path)
    await db.commit()
    await db.refresh(job)

    await start_import_job(job.id, AsyncSessionLocal)
    return job


@router.post("/upload/chunk", response_model=ImportJobResponse)
async def upload_chunk(
    file: UploadFile = File(...),
    job_id: UUID = Form(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    _ = ChunkUploadRequest(job_id=job_id, chunk_number=chunk_number, total_chunks=total_chunks)

    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if job is None and chunk_number == 0:
        job = ImportJob(
            id=job_id,
            user_id=current_user.id,
            filename=file.filename or f"{job_id}.mbox",
            file_size=0,
            status=ImportStatus.pending,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
    elif job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    upload_path = get_upload_path(job.id)
    async with aiofiles.open(upload_path, "ab") as out:
        while chunk := await file.read(10 * 1024 * 1024):
            await out.write(chunk)
            job.file_size += len(chunk)

    job.upload_path = str(upload_path)
    await db.commit()

    if chunk_number == total_chunks - 1:
        await start_import_job(job.id, AsyncSessionLocal)

    await db.refresh(job)
    return job


@router.get("/jobs", response_model=list[ImportJobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[ImportJob]:
    result = await db.execute(select(ImportJob).where(ImportJob.user_id == current_user.id).order_by(ImportJob.started_at.desc()))
    return list(result.scalars().all())


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=ImportJobResponse)
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    if job.status == ImportStatus.processing:
        cancel_import_job(job.id)
    else:
        job.status = ImportStatus.cancelled
        await db.commit()

    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/retry", response_model=ImportJobResponse)
async def retry_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    if job.status not in {ImportStatus.failed, ImportStatus.cancelled}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only failed/cancelled jobs can be retried")

    job.status = ImportStatus.pending
    job.error_message = None
    await db.commit()
    await start_import_job(job.id, AsyncSessionLocal)
    await db.refresh(job)
    return job


@router.get("/stats", response_model=ImportStats)
async def get_import_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportStats:
    total_jobs = await db.scalar(select(func.count(ImportJob.id)).where(ImportJob.user_id == current_user.id))
    completed_jobs = await db.scalar(
        select(func.count(ImportJob.id)).where(ImportJob.user_id == current_user.id, ImportJob.status == ImportStatus.completed)
    )
    failed_jobs = await db.scalar(
        select(func.count(ImportJob.id)).where(ImportJob.user_id == current_user.id, ImportJob.status == ImportStatus.failed)
    )
    totals = await db.execute(
        select(
            func.coalesce(func.sum(ImportJob.processed_emails), 0),
            func.coalesce(func.sum(ImportJob.total_attachments), 0),
        ).where(ImportJob.user_id == current_user.id)
    )
    total_emails, total_attachments = totals.one()

    return ImportStats(
        total_jobs=total_jobs or 0,
        completed_jobs=completed_jobs or 0,
        failed_jobs=failed_jobs or 0,
        total_emails=total_emails or 0,
        total_attachments=total_attachments or 0,
    )
