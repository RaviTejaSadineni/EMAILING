from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.import_job import ImportJobCreate, ImportJobResponse

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/upload", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_import_job(
    payload: ImportJobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportJob:
    job = ImportJob(user_id=current_user.id, filename=payload.filename, file_size=payload.file_size)
    db.add(job)
    await db.commit()
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
