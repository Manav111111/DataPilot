import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_project(client: AsyncClient, test_user_a):
    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "E-Commerce Scraping Project",
            "description": "Scrapes product pricing and catalog data",
            "status": "active",
        },
        headers=test_user_a["headers"],
    )
    assert create_resp.status_code == 201
    proj_data = create_resp.json()
    assert proj_data["name"] == "E-Commerce Scraping Project"
    assert proj_data["status"] == "active"
    project_id = proj_data["id"]

    get_resp = await client.get(
        f"/api/v1/projects/{project_id}", headers=test_user_a["headers"]
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project_id


@pytest.mark.asyncio
async def test_list_projects_with_filtering(client: AsyncClient, test_user_a):
    # Create multiple projects
    for i in range(3):
        await client.post(
            "/api/v1/projects",
            json={"name": f"Finance Project {i}", "description": "Finance data"},
            headers=test_user_a["headers"],
        )

    resp = await client.get("/api/v1/projects", headers=test_user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3

    # Search filter
    search_resp = await client.get(
        "/api/v1/projects?search=Finance", headers=test_user_a["headers"]
    )
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] >= 3


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, test_user_a):
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Initial Name", "description": "Initial desc"},
        headers=test_user_a["headers"],
    )
    proj_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Updated Name", "status": "completed"},
        headers=test_user_a["headers"],
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"
    assert update_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, test_user_a):
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "To Delete"},
        headers=test_user_a["headers"],
    )
    proj_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/projects/{proj_id}", headers=test_user_a["headers"]
    )
    assert del_resp.status_code == 200

    get_resp = await client.get(
        f"/api/v1/projects/{proj_id}", headers=test_user_a["headers"]
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_user_isolation_projects(
    client: AsyncClient, test_user_a, test_user_b
):
    # User A creates a project
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Secret Project"},
        headers=test_user_a["headers"],
    )
    project_id = create_resp.json()["id"]

    # User B attempts to access Alice's project
    get_resp = await client.get(
        f"/api/v1/projects/{project_id}", headers=test_user_b["headers"]
    )
    assert get_resp.status_code == 404

    # User B attempts to update Alice's project
    patch_resp = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Hacked by Bob"},
        headers=test_user_b["headers"],
    )
    assert patch_resp.status_code == 404

    # User B attempts to delete Alice's project
    del_resp = await client.delete(
        f"/api/v1/projects/{project_id}", headers=test_user_b["headers"]
    )
    assert del_resp.status_code == 404
