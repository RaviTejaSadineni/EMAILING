import pytest


async def _auth_headers(client, suffix='s1'):
    payload = {'email': f'stake{suffix}@example.com', 'username': f'stake{suffix}', 'password': 'Password123'}
    await client.post('/auth/register', json=payload)
    login = await client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_stakeholder_start_and_status(client, monkeypatch):
    headers = await _auth_headers(client, suffix='start')

    async def _noop_start(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.stakeholders.start_stakeholder_extraction_job', _noop_start)

    start = await client.post('/api/stakeholders/start-extraction', headers=headers)
    assert start.status_code == 202

    status = await client.get('/api/stakeholders/status', headers=headers)
    assert status.status_code == 200


@pytest.mark.asyncio
async def test_stakeholder_list_and_stats(client):
    headers = await _auth_headers(client, suffix='list')
    listing = await client.get('/api/stakeholders', headers=headers)
    assert listing.status_code == 200
    stats = await client.get('/api/stakeholders/stats', headers=headers)
    assert stats.status_code == 200
