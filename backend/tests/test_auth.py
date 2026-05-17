import pytest


@pytest.mark.asyncio
async def test_register_login_me_refresh_flow(client):
    register_payload = {"email": "user@example.com", "username": "user1", "password": "Password123"}
    register_response = await client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "user@example.com"

    login_payload = {"email": "user@example.com", "password": "Password123"}
    login_response = await client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "user1"

    refresh_response = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]
