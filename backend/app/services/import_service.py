from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.models.attachment import Attachment
from app.models.email import Email
from app.models.import_job import ImportJob, ImportStatus
from app.redis_client import get_redis_client
from app.services.attachment_storage import AttachmentStorageService
from app.services.mbox_counter import quick_count_mbox
from app.services.mbox_parser import MboxParser
from app.websocket_manager import websocket_manager

settings = get_settings()
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "data" / "uploads"

_import_tasks: dict[UUID, asyncio.Task] = {}
_cancelled_jobs: set[UUID] = set()


async def _broadcast_progress(job_id: UUID, progress: dict) -> None:
    message = json.dumps(progress, default=str)
    await websocket_manager.broadcast(job_id, message)
    try:
        redis = await get_redis_client()
        await redis.publish(f"import_progress:{job_id}", message)
    except Exception:
        pass


async def run_import_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    start = time.perf_counter()
    attachment_storage = AttachmentStorageService()
    processed_attachments = 0

    async with session_factory() as db:
        result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None or not job.upload_path:
            return

        job.status = ImportStatus.processing
        await db.commit()

        try:
            total_emails, _ = quick_count_mbox(job.upload_path)
            job.total_emails = total_emails
            await db.commit()

            parser = MboxParser(job.upload_path)
            batch_size = max(settings.max_emails_per_poll, 1)
            email_batch = []
            attachment_batch = []
            processed = job.resume_offset
            batch_number = 0

            def flush_batches():
                nonlocal processed, processed_attachments, batch_number
                if not email_batch:
                    return None
                batch_number += 1
                return batch_number

            for parsed in parser.iter_emails(start_index=job.resume_offset):
                if job.id in _cancelled_jobs:
                    job.status = ImportStatus.cancelled
                    job.completed_at = datetime.now(UTC)
                    await db.commit()
                    _cancelled_jobs.discard(job.id)
                    return

                email_batch.append(
                    {
                        "message_id": parsed.message_id,
                        "subject": parsed.subject,
                        "from_address": parsed.from_address,
                        "to_addresses": parsed.to_addresses,
                        "cc_addresses": parsed.cc_addresses,
                        "bcc_addresses": parsed.bcc_addresses,
                        "date": parsed.date,
                        "body_text": parsed.body_text,
                        "body_html": parsed.body_html,
                        "in_reply_to": parsed.in_reply_to,
                        "references": parsed.references,
                        "headers": parsed.headers,
                        "raw_size": parsed.raw_size,
                    }
                )
                attachment_batch.append(parsed.attachments)

                if len(email_batch) < batch_size:
                    continue

                current_batch = flush_batches()
                if current_batch is None:
                    continue

                email_insert = insert(Email).returning(Email.id, Email.subject).values(email_batch)
                insert_result = await db.execute(email_insert)
                inserted_rows = insert_result.all()

                attachment_rows = []
                write_tasks = []
                for (email_id, _), parsed_attachments in zip(inserted_rows, attachment_batch):
                    for attachment in parsed_attachments:
                        write_tasks.append(
                            attachment_storage.store_attachment(
                                db,
                                file_hash=attachment.file_hash,
                                filename=attachment.filename,
                                content=attachment.content,
                            )
                        )
                        attachment_rows.append(
                            {
                                "email_id": email_id,
                                "filename": attachment.filename,
                                "content_type": attachment.content_type,
                                "size": attachment.size,
                                "file_hash": attachment.file_hash,
                            }
                        )

                storage_paths = await asyncio.gather(*write_tasks) if write_tasks else []
                for row, storage_path in zip(attachment_rows, storage_paths):
                    row["storage_path"] = storage_path

                if attachment_rows:
                    await db.execute(insert(Attachment).values(attachment_rows))

                processed += len(email_batch)
                processed_attachments += len(attachment_rows)
                job.processed_emails = processed
                job.total_attachments = processed_attachments
                job.resume_offset = processed
                await db.commit()

                elapsed = max(time.perf_counter() - start, 0.001)
                rate = processed / elapsed
                eta = int(max((total_emails - processed) / rate, 0)) if rate else None
                progress = {
                    "job_id": str(job.id),
                    "status": job.status.value,
                    "total_emails": total_emails,
                    "processed_emails": processed,
                    "total_attachments": processed_attachments,
                    "processed_attachments": processed_attachments,
                    "current_batch": current_batch,
                    "emails_per_second": round(rate, 2),
                    "estimated_remaining_seconds": eta,
                    "current_subject": inserted_rows[-1][1] if inserted_rows else None,
                    "phase": "parsing",
                }
                await _broadcast_progress(job.id, progress)

                email_batch = []
                attachment_batch = []

            if email_batch:
                current_batch = flush_batches()
                if current_batch is not None:
                    email_insert = insert(Email).returning(Email.id, Email.subject).values(email_batch)
                    insert_result = await db.execute(email_insert)
                    inserted_rows = insert_result.all()

                    attachment_rows = []
                    write_tasks = []
                    for (email_id, _), parsed_attachments in zip(inserted_rows, attachment_batch):
                        for attachment in parsed_attachments:
                            write_tasks.append(
                                attachment_storage.store_attachment(
                                    db,
                                    file_hash=attachment.file_hash,
                                    filename=attachment.filename,
                                    content=attachment.content,
                                )
                            )
                            attachment_rows.append(
                                {
                                    "email_id": email_id,
                                    "filename": attachment.filename,
                                    "content_type": attachment.content_type,
                                    "size": attachment.size,
                                    "file_hash": attachment.file_hash,
                                }
                            )

                    storage_paths = await asyncio.gather(*write_tasks) if write_tasks else []
                    for row, storage_path in zip(attachment_rows, storage_paths):
                        row["storage_path"] = storage_path

                    if attachment_rows:
                        await db.execute(insert(Attachment).values(attachment_rows))

                    processed += len(email_batch)
                    processed_attachments += len(attachment_rows)
                    job.processed_emails = processed
                    job.total_attachments = processed_attachments
                    job.resume_offset = processed
                    await db.commit()

            job.status = ImportStatus.completed
            job.completed_at = datetime.now(UTC)
            await db.commit()

            await _broadcast_progress(
                job.id,
                {
                    "job_id": str(job.id),
                    "status": job.status.value,
                    "total_emails": job.total_emails,
                    "processed_emails": job.processed_emails,
                    "total_attachments": job.total_attachments,
                    "processed_attachments": job.total_attachments,
                    "current_batch": None,
                    "emails_per_second": 0,
                    "estimated_remaining_seconds": 0,
                    "current_subject": None,
                    "phase": "complete",
                },
            )
        except Exception as exc:
            job.status = ImportStatus.failed
            job.error_message = str(exc)
            job.completed_at = datetime.now(UTC)
            await db.commit()
            await _broadcast_progress(
                job.id,
                {
                    "job_id": str(job.id),
                    "status": job.status.value,
                    "total_emails": job.total_emails,
                    "processed_emails": job.processed_emails,
                    "total_attachments": job.total_attachments,
                    "processed_attachments": job.total_attachments,
                    "current_batch": None,
                    "emails_per_second": 0,
                    "estimated_remaining_seconds": 0,
                    "current_subject": None,
                    "phase": "failed",
                },
            )
        finally:
            _import_tasks.pop(job_id, None)


async def start_import_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if job_id in _import_tasks and not _import_tasks[job_id].done():
        return
    _import_tasks[job_id] = asyncio.create_task(run_import_job(job_id, session_factory))


def cancel_import_job(job_id: UUID) -> None:
    _cancelled_jobs.add(job_id)


def get_upload_path(job_id: UUID) -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT / f"{job_id}.mbox"
