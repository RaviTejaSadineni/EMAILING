import pytest


async def _auth_headers(client, suffix='k1'):
    payload = {'email': f'contract{suffix}@example.com', 'username': f'contract{suffix}', 'password': 'Password123'}
    await client.post('/auth/register', json=payload)
    login = await client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_contract_start_and_status(client, monkeypatch):
    headers = await _auth_headers(client, suffix='start')

    async def _noop_start(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.contracts.start_contract_extraction_job', _noop_start)

    start = await client.post('/api/contracts/start-extraction', headers=headers)
    assert start.status_code == 202

    status = await client.get('/api/contracts/status', headers=headers)
    assert status.status_code == 200


@pytest.mark.asyncio
async def test_contract_listing_endpoint(client):
    headers = await _auth_headers(client, suffix='list')
    response = await client.get('/api/contracts', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
