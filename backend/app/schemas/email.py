from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationParams


class EmailResponse(BaseModel):
    id: UUID
    message_id: str
    subject: str | None
    from_address: str
    to_addresses: list[str]
    cc_addresses: list[str]
    bcc_addresses: list[str]
    date: datetime | None

    model_config = ConfigDict(from_attributes=True)


class EmailListResponse(BaseModel):
    items: list[EmailResponse]
    pagination: PaginationParams


class EmailFilter(BaseModel):
    from_address: str | None = None
    subject_contains: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
