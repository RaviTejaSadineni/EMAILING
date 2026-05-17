import pytest

from app.models.email import Email


async def _auth_headers(client, suffix='c1'):
    payload = {'email': f'class{suffix}@example.com', 'username': f'class{suffix}', 'password': 'Password123'}
    await client.post('/auth/register', json=payload)
    login = await client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_classification_start_and_status(client, db_session, monkeypatch):
    headers = await _auth_headers(client, suffix='start')

    email = Email(message_id='<c1@example.com>', subject='Need contract', from_address='a@x.com', to_addresses=['b@x.com'])
    db_session.add(email)
    await db_session.commit()

    async def _noop_start(*_args, **_kwargs):
        return None

    monkeypatch.setattr('app.routers.classification.start_classification_job', _noop_start)

    start = await client.post('/api/classification/start', headers=headers)
    assert start.status_code == 202
    status = await client.get('/api/classification/status', headers=headers)
    assert status.status_code == 200


@pytest.mark.asyncio
async def test_reclassify_endpoint(client, db_session, monkeypatch):
    headers = await _auth_headers(client, suffix='reclass')
    email = Email(message_id='<c2@example.com>', subject='Approval', from_address='a@x.com', to_addresses=['b@x.com'])
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)

    class FakeAI:
        async def classify_emails(self, _emails):
            return [
                {
                    'id': str(email.id),
                    'category': 'Contract',
                    'email_type': 'Approval',
                    'urgency': 'High',
                    'sentiment': 'Positive',
                    'ai_confidence': 0.95,
                }
            ]

    monkeypatch.setattr('app.routers.classification.get_ai_service', lambda: FakeAI())

    response = await client.post(f'/api/classification/reclassify/{email.id}', headers=headers)
    assert response.status_code == 200
    assert response.json()['category'] == 'Contract'
