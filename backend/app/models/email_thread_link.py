from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class EmailThreadLink(Base):
    __tablename__ = "email_thread_links"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("emails.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("email_threads.id", ondelete="CASCADE"), index=True)
