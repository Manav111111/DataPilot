import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workflows_returns_empty_initially(client: AsyncClient, test_user_a):
    resp = await client.get("/api/v1/workflows", headers=test_user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_workflow_not_found(client: AsyncClient, test_user_a):
    resp = await client.get(
        "/api/v1/workflows/non-existent-id", headers=test_user_a["headers"]
    )
    assert resp.status_code == 404
