import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Doe"
    assert "hashed_password" not in data["user"]


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient, test_user_a):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Duplicate",
            "email": test_user_a["email"],
            "password": "Password123!",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["success"] is False


@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient, test_user_a):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_a["email"],
            "password": "Password123!",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["id"] == test_user_a["id"]


@pytest.mark.asyncio
async def test_user_login_invalid_password(client: AsyncClient, test_user_a):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_a["email"],
            "password": "WrongPassword123!",
        },
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, test_user_a):
    resp = await client.get("/api/v1/auth/me", headers=test_user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user_a["email"]
    assert data["name"] == test_user_a["name"]


@pytest.mark.asyncio
async def test_unauthenticated_access_fails(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, test_user_a):
    resp = await client.patch(
        "/api/v1/auth/me",
        json={"name": "Alice Updated"},
        headers=test_user_a["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice Updated"


@pytest.mark.asyncio
async def test_user_logout(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
