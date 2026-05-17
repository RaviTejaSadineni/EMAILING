from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    message_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    from_address: Mapped[str] = mapped_column(String(255), index=True)
    to_addresses: Mapped[list[str]] = mapped_column(JSON, default=list)
    cc_addresses: Mapped[list[str]] = mapped_column(JSON, default=list)
    bcc_addresses: Mapped[list[str]] = mapped_column(JSON, default=list)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    in_reply_to: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    references: Mapped[list[str]] = mapped_column(JSON, default=list)
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_size: Mapped[int] = mapped_column(default=0)
    import_batch_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
