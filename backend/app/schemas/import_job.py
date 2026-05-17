from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.import_job import ImportStatus


class ImportJobResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_size: int
    total_emails: int
    processed_emails: int
    total_attachments: int
    status: ImportStatus
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    resume_offset: int
    upload_path: str | None

    model_config = ConfigDict(from_attributes=True)


class ImportProgress(BaseModel):
    job_id: UUID
    status: ImportStatus
    phase: str
    processed_emails: int
    total_emails: int
    total_attachments: int
    processed_attachments: int
    current_batch: int | None = None
    emails_per_second: float = 0
    estimated_remaining_seconds: int | None = None
    current_subject: str | None = None


class ChunkUploadRequest(BaseModel):
    job_id: UUID
    chunk_number: int
    total_chunks: int


class ImportStats(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_emails: int
    total_attachments: int
