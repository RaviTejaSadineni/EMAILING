from __future__ import annotations

import asyncio
from collections import defaultdict
from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.email import Email
from app.models.email_thread import EmailThread
from app.models.email_thread_link import EmailThreadLink
from app.models.processing_job import ProcessingJob
from app.services.processing_job_service import mark_completed, mark_failed, mark_progress, mark_running

_tasks: dict[UUID, asyncio.Task] = {}


def normalize_subject(subject: str | None) -> str:
    value = (subject or "").strip()
    while True:
        lowered = value.lower()
        prefixes = ("re:", "fwd:", "fw:")
        matched = next((prefix for prefix in prefixes if lowered.startswith(prefix)), None)
        if not matched:
            break
        value = value[len(matched) :].strip()
    return value.lower()


def _participant_set(email: Email) -> set[str]:
    participants = {email.from_address.lower()}
    participants.update(a.lower() for a in (email.to_addresses or []))
    participants.update(a.lower() for a in (email.cc_addresses or []))
    return participants


def merge_confidence(group_a: list[Email], group_b: list[Email]) -> float:
    subj_a = normalize_subject(group_a[0].subject if group_a else "")
    subj_b = normalize_subject(group_b[0].subject if group_b else "")
    subject_sim = SequenceMatcher(None, subj_a, subj_b).ratio()

    part_a = set().union(*(_participant_set(e) for e in group_a)) if group_a else set()
    part_b = set().union(*(_participant_set(e) for e in group_b)) if group_b else set()
    overlap = (len(part_a & part_b) / len(part_a | part_b)) if (part_a or part_b) else 0

    dates = [e.date for e in [*group_a, *group_b] if e.date]
    date_score = 1.0
    if len(dates) >= 2:
        span_days = abs((max(dates) - min(dates)).total_seconds()) / 86400
        date_score = max(0.0, 1.0 - min(span_days / 30, 1.0))

    return round(subject_sim * 0.3 + overlap * 0.25 + date_score * 0.1 + 0.35, 4)


def deterministic_groups(emails: list[Email]) -> list[list[Email]]:
    parent = list(range(len(emails)))
    by_message_id = {email.message_id: idx for idx, email in enumerate(emails) if email.message_id}
    by_subject: dict[str, int] = {}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        pa, pb = find(a), find(b)
        if pa != pb:
            parent[pb] = pa

    for idx, email in enumerate(emails):
        if email.in_reply_to and email.in_reply_to in by_message_id:
            union(idx, by_message_id[email.in_reply_to])
        for ref in (email.references or []):
            if ref in by_message_id:
                union(idx, by_message_id[ref])

        subject_key = normalize_subject(email.subject)
        if subject_key:
            if subject_key in by_subject:
                union(idx, by_subject[subject_key])
            else:
                by_subject[subject_key] = idx

    grouped: dict[int, list[Email]] = defaultdict(list)
    for idx, email in enumerate(emails):
        grouped[find(idx)].append(email)

    return list(grouped.values())


async def run_thread_merge_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as db:
        job = await db.get(ProcessingJob, job_id)
        if job is None:
            return
        await mark_running(db, job)

        try:
            emails = list((await db.execute(select(Email).order_by(Email.date.asc()))).scalars().all())
            groups = deterministic_groups(emails)
            await mark_progress(db, job, 0, total_items=len(groups))

            await db.execute(delete(EmailThreadLink))
            await db.execute(delete(EmailThread))
            await db.commit()

            for idx, group in enumerate(groups, start=1):
                subject = group[0].subject or "(no subject)"
                participants = sorted(
                    {
                        addr.lower()
                        for email in group
                        for addr in [email.from_address, *(email.to_addresses or []), *(email.cc_addresses or [])]
                        if addr
                    }
                )
                dates = [item.date for item in group if item.date]
                confidence = 0.7 if len(group) == 1 else min(0.99, 0.75 + min(len(group), 10) * 0.02)
                thread = EmailThread(
                    thread_subject=subject,
                    merged_subject=normalize_subject(subject),
                    participant_emails=participants,
                    email_count=len(group),
                    first_date=min(dates) if dates else None,
                    last_date=max(dates) if dates else None,
                    ai_confidence=round(confidence, 4),
                )
                db.add(thread)
                await db.flush()
                db.add_all([EmailThreadLink(email_id=email.id, thread_id=thread.id) for email in group])
                await db.commit()
                await mark_progress(db, job, idx)

            await mark_completed(db, job)
        except Exception as exc:
            await mark_failed(db, job, str(exc))
            raise
        finally:
            _tasks.pop(job_id, None)


async def start_thread_merge_job(job: ProcessingJob, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if existing := _tasks.get(job.id):
        if not existing.done():
            return
    _tasks[job.id] = asyncio.create_task(run_thread_merge_job(job.id, session_factory))
