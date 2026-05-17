import mailbox
from email.message import EmailMessage

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.attachment import Attachment
from app.models.import_job import ImportJob, ImportStatus
from app.models.user import User
from app.services.import_service import run_import_job


def _write_test_mbox(path):
    mbox = mailbox.mbox(path)
    for idx in range(3):
        msg = EmailMessage()
        msg['Message-ID'] = f'<m{idx}@example.com>'
        msg['Subject'] = f'Subject {idx}'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'receiver@example.com'
        msg.set_content(f'body {idx}')
        if idx == 1:
            msg.add_attachment(b'hello', maintype='application', subtype='octet-stream', filename='a.bin')
        mbox.add(msg)
    mbox.flush()


@pytest.mark.asyncio
async def test_import_service_processes_batches(engine, tmp_path):
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as db:
        user = User(email='import-user@example.com', username='import-user', hashed_password='hashed')
        db.add(user)
        await db.commit()
        await db.refresh(user)

        mbox_path = tmp_path / 'service.mbox'
        _write_test_mbox(mbox_path)

        job = ImportJob(user_id=user.id, filename='service.mbox', upload_path=str(mbox_path), status=ImportStatus.pending)
        db.add(job)
        await db.commit()
        await db.refresh(job)

    await run_import_job(job.id, session_factory)

    async with session_factory() as db:
        saved_job = await db.get(ImportJob, job.id)
        assert saved_job is not None
        assert saved_job.status == ImportStatus.completed
        assert saved_job.processed_emails == 3

        attachments = (await db.execute(select(Attachment).limit(10))).scalars().all()
        assert len(attachments) == 1
