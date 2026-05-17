from __future__ import annotations

from pathlib import Path

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment

ATTACHMENTS_ROOT = Path(__file__).resolve().parents[2] / "data" / "attachments"


class AttachmentStorageService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ATTACHMENTS_ROOT

    async def store_attachment(
        self,
        db: AsyncSession,
        *,
        file_hash: str,
        filename: str,
        content: bytes,
    ) -> str:
        existing = await db.execute(select(Attachment.storage_path).where(Attachment.file_hash == file_hash).limit(1))
        existing_path = existing.scalar_one_or_none()
        if existing_path:
            return existing_path

        safe_name = filename.replace("/", "_").replace("\\", "_")
        relative_path = Path(file_hash[:2]) / file_hash[2:4] / f"{file_hash}_{safe_name}"
        absolute_path = self.root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        if not absolute_path.exists():
            async with aiofiles.open(absolute_path, "wb") as handle:
                await handle.write(content)

        return str(relative_path)
