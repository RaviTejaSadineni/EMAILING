from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread_link import EmailThreadLink
from app.models.processing_job import ProcessingJob
from app.services.ai_service import get_ai_service
from app.services.processing_job_service import mark_completed, mark_failed, mark_progress, mark_running

settings = get_settings()
_tasks: dict[UUID, asyncio.Task] = {}

STAGE_DEFINITIONS = [
    {"stage": 1, "name": "Request", "description": "Initial contract request and business need"},
    {"stage": 2, "name": "Legal Review", "description": "Legal draft/review and markup"},
    {"stage": 3, "name": "Finance Review", "description": "Pricing and budget approval"},
    {"stage": 4, "name": "Procurement/Compliance", "description": "Vendor/compliance/security checks"},
    {"stage": 5, "name": "Redline Negotiation", "description": "Back-and-forth clause negotiation"},
    {"stage": 6, "name": "Leadership Sign-off", "description": "Executive authorization"},
    {"stage": 7, "name": "Repository & Obligation Tracking", "description": "Execution and tracking"},
]


def _parse_datetime(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


async def run_lifecycle_detection_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    ai_service = get_ai_service()
    async with session_factory() as db:
        job = await db.get(ProcessingJob, job_id)
        if job is None:
            return
        await mark_running(db, job)

        try:
            contracts = list((await db.execute(select(Contract).order_by(Contract.created_at.asc()))).scalars().all())
            await mark_progress(db, job, 0, total_items=len(contracts))

            for idx, contract in enumerate(contracts, start=1):
                email_rows = await db.execute(
                    select(Email)
                    .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
                    .where(EmailThreadLink.thread_id == contract.thread_id)
                    .order_by(Email.date.asc())
                )
                emails = list(email_rows.scalars().all())
                thread_payload = {
                    "thread_id": str(contract.thread_id),
                    "emails": [
                        {
                            "id": str(email.id),
                            "subject": email.subject,
                            "from": email.from_address,
                            "date": email.date,
                            "body": (email.body_text or "")[:2000],
                        }
                        for email in emails
                    ],
                }
                detected = await ai_service.detect_lifecycle_stage(thread_payload)

                contract.stage_history = detected.get("stage_history") or []
                contract.current_stage = detected.get("current_stage") or "Request"
                contract.predicted_completion = _parse_datetime(detected.get("predicted_completion"))

                if emails and emails[0].date and emails[-1].date:
                    total = emails[-1].date - emails[0].date
                    contract.sla_breached = total > timedelta(days=15)

                    if total.total_seconds() / 60 > settings.slr_yellow_minutes:
                        reasons = contract.delay_reasons or []
                        if not reasons:
                            reasons.append(
                                {
                                    "stage": contract.current_stage,
                                    "reason": "Cycle time exceeded testing threshold",
                                    "internal": True,
                                }
                            )
                        contract.delay_reasons = reasons

                await db.commit()
                await mark_progress(db, job, idx)

            await mark_completed(db, job)
        except Exception as exc:
            await mark_failed(db, job, str(exc))
            raise
        finally:
            _tasks.pop(job_id, None)


async def start_lifecycle_detection_job(job: ProcessingJob, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if existing := _tasks.get(job.id):
        if not existing.done():
            return
    _tasks[job.id] = asyncio.create_task(run_lifecycle_detection_job(job.id, session_factory))
