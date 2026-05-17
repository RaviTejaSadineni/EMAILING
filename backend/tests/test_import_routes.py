import mailbox
from email.message import EmailMessage

import pytest


async def _auth_headers(client, suffix='1'):
    payload = {
        'email': f'import{suffix}@example.com',
        'username': f'importer{suffix}',
        'password': 'Password123',
    }
    await client.post('/auth/register', json=payload)
    login = await client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def _build_mbox_bytes(tmp_path):
    path = tmp_path / 'upload.mbox'
    mbox = mailbox.mbox(path)
    msg = EmailMessage()
    msg['Message-ID'] = '<u1@example.com>'
    msg['Subject'] = 'Upload Test'
    msg['From'] = 'x@example.com'
    msg['To'] = 'y@example.com'
    msg.set_content('hello')
    mbox.add(msg)
    mbox.flush()
    return path.read_bytes()


@pytest.mark.asyncio
async def test_import_upload_and_job_routes(client, tmp_path, monkeypatch):
    async def _noop_start_import(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.imports.start_import_job', _noop_start_import)

    headers = await _auth_headers(client, suffix='11')
    data = _build_mbox_bytes(tmp_path)

    upload = await client.post(
        '/imports/upload',
        files={'file': ('upload.mbox', data, 'application/mbox')},
        headers=headers,
    )
    assert upload.status_code == 201
    job = upload.json()
    assert job['filename'] == 'upload.mbox'

    jobs = await client.get('/imports/jobs', headers=headers)
    assert jobs.status_code == 200
    assert len(jobs.json()) == 1

    detail = await client.get(f"/imports/jobs/{job['id']}", headers=headers)
    assert detail.status_code == 200


@pytest.mark.asyncio
async def test_import_retry_validation(client, tmp_path, monkeypatch):
    async def _noop_start_import(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.imports.start_import_job', _noop_start_import)

    headers = await _auth_headers(client, suffix='22')
    data = _build_mbox_bytes(tmp_path)

    upload = await client.post('/imports/upload', files={'file': ('upload.mbox', data, 'application/mbox')}, headers=headers)
    job_id = upload.json()['id']

    retry = await client.post(f'/imports/jobs/{job_id}/retry', headers=headers)
    assert retry.status_code == 400
