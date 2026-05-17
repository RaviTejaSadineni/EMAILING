from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.classification import EmailClassification
from app.models.email import Email
from app.models.processing_job import ProcessingJob, ProcessingJobType
from app.services.ai_service import get_ai_service
from app.services.processing_job_service import mark_completed, mark_failed, mark_progress, mark_running

_tasks: dict[UUID, asyncio.Task] = {}


async def _unclassified_emails(db: AsyncSession) -> list[Email]:
    result = await db.execute(
        select(Email)
        .outerjoin(EmailClassification, EmailClassification.email_id == Email.id)
        .where(EmailClassification.id.is_(None))
        .order_by(Email.date.asc())
    )
    return list(result.scalars().all())


async def run_classification_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession], batch_size: int = 25) -> None:
    ai_service = get_ai_service()
    async with session_factory() as db:
        job = await db.get(ProcessingJob, job_id)
        if job is None:
            return
        await mark_running(db, job)

        try:
            emails = await _unclassified_emails(db)
            await mark_progress(db, job, processed_items=0, total_items=len(emails))

            for i in range(0, len(emails), batch_size):
                batch = emails[i : i + batch_size]
                payload = [
                    {
                        "id": str(email.id),
                        "subject": email.subject,
                        "from_address": email.from_address,
                        "to_addresses": email.to_addresses,
                        "cc_addresses": email.cc_addresses,
                        "body_text": (email.body_text or "")[:4000],
                        "date": email.date,
                    }
                    for email in batch
                ]
                ai_results = await ai_service.classify_emails(payload)
                by_id = {item.get("id"): item for item in ai_results if item.get("id")}

                for email in batch:
                    item = by_id.get(str(email.id), {})
                    db.add(
                        EmailClassification(
                            email_id=email.id,
                            category=item.get("category", "General"),
                            email_type=item.get("email_type", "FYI/Information"),
                            urgency=item.get("urgency", "Low"),
                            sentiment=item.get("sentiment", "Neutral"),
                            ai_confidence=float(item.get("ai_confidence", 0.5) or 0.5),
                        )
                    )

                await db.commit()
                await mark_progress(db, job, processed_items=min(i + len(batch), len(emails)))

            await mark_completed(db, job)
        except Exception as exc:
            await mark_failed(db, job, str(exc))
            raise
        finally:
            _tasks.pop(job_id, None)


async def start_classification_job(job: ProcessingJob, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if existing := _tasks.get(job.id):
        if not existing.done():
            return
    _tasks[job.id] = asyncio.create_task(run_classification_job(job.id, session_factory))


async def classification_stats(db: AsyncSession) -> dict:
    category_rows = await db.execute(select(EmailClassification.category, func.count()).group_by(EmailClassification.category))
    type_rows = await db.execute(select(EmailClassification.email_type, func.count()).group_by(EmailClassification.email_type))
    urgency_rows = await db.execute(select(EmailClassification.urgency, func.count()).group_by(EmailClassification.urgency))
    return {
        "by_category": {k or "Unknown": v for k, v in category_rows.all()},
        "by_type": {k or "Unknown": v for k, v in type_rows.all()},
        "by_urgency": {k or "Unknown": v for k, v in urgency_rows.all()},
    }
