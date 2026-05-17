from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.import_job import ImportStatus


class ImportJobCreate(BaseModel):
    filename: str
    file_size: int


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

    model_config = ConfigDict(from_attributes=True)


class ImportProgress(BaseModel):
    job_id: UUID
    processed_emails: int
    total_emails: int
    total_attachments: int
    status: ImportStatus
