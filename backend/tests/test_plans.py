import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_plan_success(client: AsyncClient, test_user_a):
    # 1. Create a project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "AI Hiring Intel Project", "description": "Tracking AI startup hiring"},
        headers=test_user_a["headers"],
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Generate plan
    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={
            "request": "Find 100 Indian startups that are hiring AI/ML engineers. Include company name, job title, location, salary if available, job posting URL, company website, and source.",
            "target_record_count": 100,
        },
        headers=test_user_a["headers"],
    )
    assert plan_resp.status_code == 201
    plan = plan_resp.json()

    assert plan["status"] == "ready_for_review"
    assert plan["project_id"] == project_id
    assert len(plan["plan_data"]["fields"]) >= 4
    assert len(plan["plan_data"]["search_queries"]) >= 1
    assert len(plan["plan_data"]["source_recommendations"]) >= 1
    assert len(plan["plan_data"]["quality_rules"]) >= 1
    assert plan["plan_data"]["target_record_count"] == 100


@pytest.mark.asyncio
async def test_generate_plan_ambiguous_triggers_clarification(
    client: AsyncClient, test_user_a
):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Ambiguous Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={"request": "find data"},
        headers=test_user_a["headers"],
    )
    assert plan_resp.status_code == 201
    plan = plan_resp.json()

    assert plan["status"] == "needs_clarification"
    assert len(plan["plan_data"]["clarification_questions"]) > 0


@pytest.mark.asyncio
async def test_update_plan_fields_and_queries(client: AsyncClient, test_user_a):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Edit Plan Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={"request": "Find 50 fintech companies in Mumbai"},
        headers=test_user_a["headers"],
    )
    plan_id = plan_resp.json()["id"]

    # Update fields and target count
    updated_fields = [
        {
            "name": "company_name",
            "label": "Company Name",
            "type": "string",
            "required": True,
            "description": "Legal entity name",
        },
        {
            "name": "valuation_usd",
            "label": "Estimated Valuation (USD)",
            "type": "number",
            "required": False,
            "description": "Latest round valuation",
        },
    ]

    patch_resp = await client.patch(
        f"/api/v1/plans/{plan_id}",
        json={
            "target_record_count": 250,
            "goal": "Refined fintech intelligence goal",
            "fields": updated_fields,
        },
        headers=test_user_a["headers"],
    )
    assert patch_resp.status_code == 200
    updated_plan = patch_resp.json()
    assert updated_plan["plan_data"]["target_record_count"] == 250
    assert updated_plan["plan_data"]["goal"] == "Refined fintech intelligence goal"
    assert len(updated_plan["plan_data"]["fields"]) == 2


@pytest.mark.asyncio
async def test_approve_and_reject_plan(client: AsyncClient, test_user_a):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Approval Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={"request": "Find 100 Indian startups hiring AI engineers"},
        headers=test_user_a["headers"],
    )
    plan_id = plan_resp.json()["id"]

    # Approve
    approve_resp = await client.post(
        f"/api/v1/plans/{plan_id}/approve", headers=test_user_a["headers"]
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Reject
    reject_resp = await client.post(
        f"/api/v1/plans/{plan_id}/reject", headers=test_user_a["headers"]
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_approve_blocked_on_unresolved_clarification(
    client: AsyncClient, test_user_a
):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Blocked Approval Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={"request": "find data"},
        headers=test_user_a["headers"],
    )
    plan_id = plan_resp.json()["id"]
    assert plan_resp.json()["status"] == "needs_clarification"

    # Try to approve directly
    approve_resp = await client.post(
        f"/api/v1/plans/{plan_id}/approve", headers=test_user_a["headers"]
    )
    assert approve_resp.status_code == 400
    assert "clarification" in approve_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_regenerate_plan_with_feedback(client: AsyncClient, test_user_a):
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Regenerate Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        json={"request": "Find 50 tech startups in Bangalore"},
        headers=test_user_a["headers"],
    )
    plan_id = plan_resp.json()["id"]

    regen_resp = await client.post(
        f"/api/v1/plans/{plan_id}/regenerate",
        json={"feedback": "Focus specifically on AI/ML companies with at least series A funding"},
        headers=test_user_a["headers"],
    )
    assert regen_resp.status_code == 200
    regen_plan = regen_resp.json()
    assert regen_plan["id"] == plan_id


@pytest.mark.asyncio
async def test_plan_user_isolation(client: AsyncClient, test_user_a, test_user_b):
    # User A creates project and plan
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Secret Intelligence Project"},
        headers=test_user_a["headers"],
    )
    proj_id = proj_resp.json()["id"]

    plan_resp = await client.post(
        f"/api/v1/projects/{proj_id}/plans/generate",
        json={"request": "Find 100 Indian startups hiring AI engineers"},
        headers=test_user_a["headers"],
    )
    plan_id = plan_resp.json()["id"]

    # User B tries to view Alice's plan
    get_resp = await client.get(
        f"/api/v1/plans/{plan_id}", headers=test_user_b["headers"]
    )
    assert get_resp.status_code == 404

    # User B tries to approve Alice's plan
    approve_resp = await client.post(
        f"/api/v1/plans/{plan_id}/approve", headers=test_user_b["headers"]
    )
    assert approve_resp.status_code == 404

    # User B tries to generate a plan inside Alice's project
    gen_foreign_resp = await client.post(
        f"/api/v1/projects/{proj_id}/plans/generate",
        json={"request": "Bob intruder request"},
        headers=test_user_b["headers"],
    )
    assert gen_foreign_resp.status_code == 404
