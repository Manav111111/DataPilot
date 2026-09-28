import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_dataset(client: AsyncClient, test_user_a):
    # First create a project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Real Estate Platform"},
        headers=test_user_a["headers"],
    )
    proj_id = proj_resp.json()["id"]

    # Create dataset
    ds_resp = await client.post(
        "/api/v1/datasets",
        json={
            "project_id": proj_id,
            "name": "NYC Listings Table",
            "description": "5000 cleaned real estate records",
            "status": "completed",
            "row_count": 5000,
        },
        headers=test_user_a["headers"],
    )
    assert ds_resp.status_code == 201
    ds_data = ds_resp.json()
    assert ds_data["name"] == "NYC Listings Table"
    assert ds_data["row_count"] == 5000
    dataset_id = ds_data["id"]

    # Get dataset
    get_resp = await client.get(
        f"/api/v1/datasets/{dataset_id}", headers=test_user_a["headers"]
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == dataset_id


@pytest.mark.asyncio
async def test_list_datasets_by_project(client: AsyncClient, test_user_a):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Health Data Project"},
        headers=test_user_a["headers"],
    )
    proj_id = proj_resp.json()["id"]

    for i in range(2):
        await client.post(
            "/api/v1/datasets",
            json={
                "project_id": proj_id,
                "name": f"Hospitals Dataset {i}",
                "row_count": 100 * (i + 1),
            },
            headers=test_user_a["headers"],
        )

    list_resp = await client.get(
        f"/api/v1/datasets?project_id={proj_id}", headers=test_user_a["headers"]
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_dataset_user_isolation(client: AsyncClient, test_user_a, test_user_b):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Private Project"},
        headers=test_user_a["headers"],
    )
    proj_id = proj_resp.json()["id"]

    ds_resp = await client.post(
        "/api/v1/datasets",
        json={
            "project_id": proj_id,
            "name": "Alice Private Dataset",
            "row_count": 100,
        },
        headers=test_user_a["headers"],
    )
    dataset_id = ds_resp.json()["id"]

    # User B tries to read Alice's dataset
    get_resp = await client.get(
        f"/api/v1/datasets/{dataset_id}", headers=test_user_b["headers"]
    )
    assert get_resp.status_code == 404

    # User B tries to create a dataset inside Alice's project
    foreign_create_resp = await client.post(
        "/api/v1/datasets",
        json={
            "project_id": proj_id,
            "name": "Bob Intruder Dataset",
        },
        headers=test_user_b["headers"],
    )
    assert foreign_create_resp.status_code == 404
