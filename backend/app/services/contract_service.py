from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread import EmailThread
from app.models.email_thread_link import EmailThreadLink
from app.models.processing_job import ProcessingJob
from app.services.ai_service import get_ai_service
from app.services.processing_job_service import mark_completed, mark_failed, mark_progress, mark_running

_tasks: dict[UUID, asyncio.Task] = {}
CONTRACT_CATEGORIES = {"contract", "legal review", "procurement", "finance", "compliance"}


def _parse_datetime(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


async def _contract_related_threads(db: AsyncSession) -> list[EmailThread]:
    result = await db.execute(select(EmailThread).order_by(EmailThread.created_at.desc()))
    threads = list(result.scalars().all())
    if not threads:
        return []

    related: list[EmailThread] = []
    for thread in threads:
        email_rows = await db.execute(
            select(EmailClassification.category)
            .join(EmailThreadLink, EmailThreadLink.email_id == EmailClassification.email_id)
            .where(EmailThreadLink.thread_id == thread.id)
        )
        categories = {str(row[0] or "").lower() for row in email_rows.all()}
        if categories & CONTRACT_CATEGORIES:
            related.append(thread)
    return related


async def run_contract_extraction_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    ai_service = get_ai_service()
    async with session_factory() as db:
        job = await db.get(ProcessingJob, job_id)
        if job is None:
            return
        await mark_running(db, job)

        try:
            threads = await _contract_related_threads(db)
            await mark_progress(db, job, 0, total_items=len(threads))

            for idx, thread in enumerate(threads, start=1):
                email_result = await db.execute(
                    select(Email)
                    .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
                    .where(EmailThreadLink.thread_id == thread.id)
                    .order_by(Email.date.asc())
                )
                emails = list(email_result.scalars().all())
                payload = {
                    "thread_id": str(thread.id),
                    "subject": thread.thread_subject,
                    "emails": [
                        {
                            "id": str(email.id),
                            "subject": email.subject,
                            "from": email.from_address,
                            "to": email.to_addresses,
                            "cc": email.cc_addresses,
                            "date": email.date,
                            "body": (email.body_text or "")[:3000],
                        }
                        for email in emails
                    ],
                }
                ai_data = await ai_service.extract_contract_metadata(payload)

                existing = (
                    await db.execute(select(Contract).where(Contract.thread_id == thread.id).limit(1))
                ).scalar_one_or_none()
                contract = existing or Contract(thread_id=thread.id)
                contract.agreement_name = ai_data.get("agreement_name")
                contract.agreement_type = ai_data.get("agreement_type")
                contract.counterparty_name = ai_data.get("counterparty_name")
                contract.counterparty_email = ai_data.get("counterparty_email")
                contract.key_clauses = ai_data.get("key_clauses") or []
                contract.contract_value = ai_data.get("contract_value")
                contract.effective_date = _parse_datetime(ai_data.get("effective_date"))
                contract.expiry_date = _parse_datetime(ai_data.get("expiry_date"))
                contract.risk_score = ai_data.get("risk_score")
                contract.complexity_score = ai_data.get("complexity_score")
                contract.ai_summary = ai_data.get("ai_summary")
                contract.lifecycle_summary = ai_data.get("ai_summary")
                contract.delay_reasons = ai_data.get("delay_reasons") or []
                if existing is None:
                    db.add(contract)

                await db.commit()
                await mark_progress(db, job, idx)

            await mark_completed(db, job)
        except Exception as exc:
            await mark_failed(db, job, str(exc))
            raise
        finally:
            _tasks.pop(job_id, None)


async def start_contract_extraction_job(job: ProcessingJob, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if existing := _tasks.get(job.id):
        if not existing.done():
            return
    _tasks[job.id] = asyncio.create_task(run_contract_extraction_job(job.id, session_factory))
