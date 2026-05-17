from __future__ import annotations

import asyncio
from collections import Counter, defaultdict
from email.utils import parseaddr
from statistics import median
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.contract import Contract
from app.models.email import Email
from app.models.processing_job import ProcessingJob
from app.models.stakeholder import Stakeholder
from app.services.ai_service import get_ai_service
from app.services.processing_job_service import mark_completed, mark_failed, mark_progress, mark_running

_tasks: dict[UUID, asyncio.Task] = {}


def _domain(address: str) -> str:
    return address.split("@", 1)[-1].lower() if "@" in address else ""


async def run_stakeholder_extraction_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    ai_service = get_ai_service()
    async with session_factory() as db:
        job = await db.get(ProcessingJob, job_id)
        if job is None:
            return
        await mark_running(db, job)

        try:
            emails = list((await db.execute(select(Email).order_by(Email.date.asc()))).scalars().all())
            counts = Counter()
            hour_dist: dict[str, Counter] = defaultdict(Counter)
            response_minutes: dict[str, list[float]] = defaultdict(list)
            internal_domain = _domain(emails[0].from_address) if emails else ""

            for email in emails:
                addresses = [email.from_address, *(email.to_addresses or []), *(email.cc_addresses or []), *(email.bcc_addresses or [])]
                addresses = [a.lower() for a in addresses if a]
                for address in addresses:
                    counts[address] += 1
                    if email.date:
                        hour_dist[address][str(email.date.hour)] += 1

            await mark_progress(db, job, 0, total_items=len(counts))

            ai_payload = []
            for address in counts:
                name = parseaddr(address)[0] or None
                ai_payload.append({"email_address": address, "name": name, "sample": address})
            ai_items = await ai_service.extract_stakeholder_info(ai_payload)
            ai_by_email = {item.get("email_address", "").lower(): item for item in ai_items}

            for idx, (address, total) in enumerate(counts.items(), start=1):
                existing = (
                    await db.execute(select(Stakeholder).where(Stakeholder.email_address == address).limit(1))
                ).scalar_one_or_none()
                ai_item = ai_by_email.get(address, {})

                stakeholder = existing or Stakeholder(email_address=address)
                stakeholder.name = ai_item.get("name") or parseaddr(address)[0] or None
                stakeholder.department = ai_item.get("department") or ("External" if _domain(address) != internal_domain else "Legal")
                stakeholder.role = ai_item.get("role") or ("External Client" if stakeholder.department == "External" else "Manager")
                stakeholder.is_internal = bool(ai_item.get("is_internal", _domain(address) == internal_domain))
                stakeholder.total_emails = total
                stakeholder.total_contracts = int(
                    (await db.execute(select(func.count()).select_from(Contract).where(Contract.counterparty_email == address))).scalar_one()
                )

                values = response_minutes.get(address, [])
                stakeholder.avg_response_time = (sum(values) / len(values)) if values else None
                stakeholder.response_time_distribution = {
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "median": median(values) if values else None,
                    "p90": sorted(values)[int(len(values) * 0.9)] if values else None,
                }
                stakeholder.communication_patterns = {
                    "hour_of_day": dict(hour_dist[address]),
                }
                stakeholder.influence_score = float(ai_item.get("influence_score", min(1.0, total / 100)))
                stakeholder.department_mentions = ai_item.get("department_mentions") or []

                if existing is None:
                    db.add(stakeholder)

                await db.commit()
                await mark_progress(db, job, idx)

            await mark_completed(db, job)
        except Exception as exc:
            await mark_failed(db, job, str(exc))
            raise
        finally:
            _tasks.pop(job_id, None)


async def start_stakeholder_extraction_job(job: ProcessingJob, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if existing := _tasks.get(job.id):
        if not existing.done():
            return
    _tasks[job.id] = asyncio.create_task(run_stakeholder_extraction_job(job.id, session_factory))
