import pytest


async def _auth_headers(client, suffix='l1'):
    payload = {'email': f'life{suffix}@example.com', 'username': f'life{suffix}', 'password': 'Password123'}
    await client.post('/auth/register', json=payload)
    login = await client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_lifecycle_start_and_status(client, monkeypatch):
    headers = await _auth_headers(client, suffix='start')

    async def _noop_start(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.lifecycle.start_lifecycle_detection_job', _noop_start)

    start = await client.post('/api/lifecycle/start-detection', headers=headers)
    assert start.status_code == 202

    status = await client.get('/api/lifecycle/status', headers=headers)
    assert status.status_code == 200


@pytest.mark.asyncio
async def test_lifecycle_stage_definitions(client):
    headers = await _auth_headers(client, suffix='stages')
    response = await client.get('/api/lifecycle/stages', headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 7
