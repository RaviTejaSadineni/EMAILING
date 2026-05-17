import hashlib

import pytest

from app.services.attachment_storage import AttachmentStorageService


@pytest.mark.asyncio
async def test_attachment_storage_deduplicates_by_hash(tmp_path, db_session):
    service = AttachmentStorageService(root=tmp_path)
    content = b'same-content'
    file_hash = hashlib.sha256(content).hexdigest()

    first = await service.store_attachment(db_session, file_hash=file_hash, filename='file.pdf', content=content)
    second = await service.store_attachment(db_session, file_hash=file_hash, filename='file.pdf', content=content)

    assert first == second
    assert (tmp_path / first).exists()
    assert first.startswith(f"{file_hash[:2]}/{file_hash[2:4]}/")
