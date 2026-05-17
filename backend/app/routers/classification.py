from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.dependencies import get_current_user, get_db_session
from app.models.classification import EmailClassification
from app.models.email import Email
from app.models.processing_job import ProcessingJobType
from app.models.user import User
from app.schemas.classification import ClassificationProgress, ClassificationResponse, ClassificationStats
from app.services.ai_service import get_ai_service
from app.services.classification_service import classification_stats, start_classification_job
from app.services.processing_job_service import create_job, latest_job

router = APIRouter(prefix="/api/classification", tags=["classification"])


def _job_to_progress(job) -> ClassificationProgress:
    return ClassificationProgress(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        total_items=job.total_items,
        processed_items=job.processed_items,
        error_message=job.error_message,
    )


@router.post("/start", response_model=ClassificationProgress, status_code=status.HTTP_202_ACCEPTED)
async def start_classification(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ClassificationProgress:
    pending = await latest_job(db, current_user.id, ProcessingJobType.classification)
    if pending and pending.status.value == "in_progress":
        return _job_to_progress(pending)

    job = await create_job(db, current_user.id, ProcessingJobType.classification)
    await start_classification_job(job, AsyncSessionLocal)
    return _job_to_progress(job)


@router.get("/status", response_model=ClassificationProgress)
async def get_classification_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ClassificationProgress:
    job = await latest_job(db, current_user.id, ProcessingJobType.classification)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No classification job found")
    return _job_to_progress(job)


@router.get("/results", response_model=list[ClassificationResponse])
async def get_classification_results(
    category: str | None = Query(default=None),
    email_type: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[EmailClassification]:
    query = select(EmailClassification)
    if category:
        query = query.where(EmailClassification.category == category)
    if email_type:
        query = query.where(EmailClassification.email_type == email_type)
    if urgency:
        query = query.where(EmailClassification.urgency == urgency)
    result = await db.execute(query.order_by(EmailClassification.created_at.desc()))
    return list(result.scalars().all())


@router.get("/stats", response_model=ClassificationStats)
async def get_classification_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ClassificationStats:
    return ClassificationStats(**(await classification_stats(db)))


@router.post("/reclassify/{email_id}", response_model=ClassificationResponse)
async def reclassify_email(
    email_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> EmailClassification:
    email = await db.get(Email, email_id)
    if email is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    ai_service = get_ai_service()
    result = await ai_service.classify_emails(
        [
            {
                "id": str(email.id),
                "subject": email.subject,
                "from_address": email.from_address,
                "to_addresses": email.to_addresses,
                "cc_addresses": email.cc_addresses,
                "body_text": (email.body_text or "")[:4000],
                "date": email.date,
            }
        ]
    )
    item = result[0] if result else {}

    existing = (
        await db.execute(select(EmailClassification).where(EmailClassification.email_id == email_id).limit(1))
    ).scalar_one_or_none()
    classification = existing or EmailClassification(email_id=email_id)
    classification.category = item.get("category", "General")
    classification.email_type = item.get("email_type", "FYI/Information")
    classification.urgency = item.get("urgency", "Low")
    classification.sentiment = item.get("sentiment", "Neutral")
    classification.ai_confidence = float(item.get("ai_confidence", 0.5) or 0.5)
    if existing is None:
        db.add(classification)

    await db.commit()
    await db.refresh(classification)
    return classification
