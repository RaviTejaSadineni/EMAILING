from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
