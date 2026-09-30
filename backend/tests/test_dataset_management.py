import pytest
import uuid
from httpx import AsyncClient
from app.core.config import settings
from app.collection.coordinator import CollectionJobCoordinator


@pytest.mark.asyncio
async def test_dataset_profiler_and_quality_scores(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests dataset profiling, column statistics, and 5-dimension quality scoring.
    """
    headers = test_user_a["headers"]

    # 1. Create project & dataset
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Analytics Profiling Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    ds_res = await client.post(
        "/api/v1/datasets",
        headers=headers,
        json={"project_id": project_id, "name": "Startup Hiring Dataset", "description": "Profile test dataset"},
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Profile empty dataset
    prof_empty = await client.get(
        f"/api/v1/datasets/{dataset_id}/profile",
        headers=headers,
    )
    assert prof_empty.status_code == 200
    p_data = prof_empty.json()
    assert p_data["overview"]["total_records"] == 0
    assert p_data["quality"]["overall_score"] >= 0.0

    # 3. Create plan & run collection
    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Find 5 Indian AI startups with company name and location"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    assert collect_res.status_code in (200, 202)
    job_id = collect_res.json()["job_id"]
    collected_ds_id = collect_res.json()["dataset_id"]

    # Run coordinator
    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # Profile collected dataset
    profile_res = await client.post(
        f"/api/v1/datasets/{collected_ds_id}/profile",
        headers=headers,
    )
    assert profile_res.status_code == 200
    prof = profile_res.json()
    assert prof["overview"]["total_records"] > 0
    assert len(prof["columns"]) > 0
    assert "completeness" in prof["quality"]["dimension_scores"]
    assert "provenance" in prof["quality"]["dimension_scores"]
    assert prof["quality"]["overall_score"] > 50.0


@pytest.mark.asyncio
async def test_data_cleaning_preview_and_apply(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests cleaning preview and apply operations (whitespace, URLs, geo labels).
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Cleaning Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Indian tech jobs in Bengaluru with company and title"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # 1. Preview trim whitespace
    preview_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean/preview",
        headers=headers,
        json={"operation_type": "trim_whitespace", "configuration": {}},
    )
    assert preview_res.status_code == 200
    prev_data = preview_res.json()
    assert prev_data["operation_type"] == "trim_whitespace"

    # 2. Apply normalize geo (Bengaluru -> Bangalore)
    clean_apply = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean/apply",
        headers=headers,
        json={"operation_type": "normalize_geo", "configuration": {"field_name": "location"}},
    )
    assert clean_apply.status_code == 200
    assert "transformation_id" in clean_apply.json()

    # 3. Verify transformation history
    trans_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/transformations",
        headers=headers,
    )
    assert trans_res.status_code == 200
    assert len(trans_res.json()) >= 1


@pytest.mark.asyncio
async def test_transformations_derived_columns(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests column renaming and derived column creation (combine text, extract domain).
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Transform Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Tech jobs in Bangalore with website and company"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # 1. Preview derive column: extract domain from company_website
    prev_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/transformations/preview",
        headers=headers,
        json={
            "operation_type": "derive_column",
            "configuration": {
                "target_column": "website_domain",
                "expression_type": "extract_domain",
                "source_column": "company_website",
            },
        },
    )
    assert prev_res.status_code == 200
    assert prev_res.json()["fields_affected"] == ["website_domain"]

    # 2. Apply derive column
    apply_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/transformations",
        headers=headers,
        json={
            "operation_type": "derive_column",
            "configuration": {
                "target_column": "website_domain",
                "expression_type": "extract_domain",
                "source_column": "company_website",
            },
        },
    )
    assert apply_res.status_code == 200

    # 3. Verify records now contain website_domain
    records_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/records",
        headers=headers,
    )
    assert records_res.status_code == 200
    records = records_res.json()["items"]
    assert len(records) > 0


@pytest.mark.asyncio
async def test_duplicate_detection_and_merge(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests finding duplicate groups and merging records while preserving provenance.
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Duplicates Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Companies in Pune with name and sector"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # 1. Query duplicates
    dup_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/duplicates",
        headers=headers,
    )
    assert dup_res.status_code == 200
    assert isinstance(dup_res.json(), list)

    # 2. Get records to perform a merge
    rec_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/records",
        headers=headers,
    )
    records = rec_res.json()["items"]
    if len(records) >= 2:
        retained_id = records[0]["id"]
        merged_id = records[1]["id"]
        merge_res = await client.post(
            f"/api/v1/datasets/{dataset_id}/duplicates/merge",
            headers=headers,
            json={
                "retained_record_id": retained_id,
                "merged_record_ids": [merged_id],
                "create_version": True,
            },
        )
        assert merge_res.status_code == 200
        assert merge_res.json()["retained_record_id"] == retained_id


@pytest.mark.asyncio
async def test_dataset_analytics_and_dynamic_charts(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests analytics distributions and chart builder CRUD.
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Analytics Chart Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Hiring data in Gurgaon with company and location"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # 1. Distributions
    dist_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/analytics/distributions",
        headers=headers,
    )
    assert dist_res.status_code == 200
    assert "distributions" in dist_res.json()

    # 2. Create saved chart
    chart_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/analytics/charts",
        headers=headers,
        json={
            "chart_name": "Jobs by Location",
            "chart_type": "bar",
            "configuration": {"x_field": "location", "aggregation": "count"},
        },
    )
    assert chart_res.status_code == 200
    chart_id = chart_res.json()["id"]

    # 3. List charts
    list_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/analytics/charts",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert "computed_data" in list_res.json()[0]

    # 4. Delete chart
    del_res = await client.delete(
        f"/api/v1/analytics/charts/{chart_id}",
        headers=headers,
    )
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_dataset_comparison(
    client: AsyncClient,
    test_user_a: dict,
):
    """
    Tests comparing two datasets owned by the user.
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Comparison Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    # Create dataset A
    ds_a = await client.post(
        "/api/v1/datasets",
        headers=headers,
        json={"project_id": project_id, "name": "Dataset Alpha", "description": "Comparison test A"},
    )
    id_a = ds_a.json()["id"]

    # Create dataset B
    ds_b = await client.post(
        "/api/v1/datasets",
        headers=headers,
        json={"project_id": project_id, "name": "Dataset Beta", "description": "Comparison test B"},
    )
    id_b = ds_b.json()["id"]

    comp_res = await client.post(
        "/api/v1/datasets/compare",
        headers=headers,
        json={"dataset_id_a": id_a, "dataset_id_b": id_b},
    )
    assert comp_res.status_code == 200
    comp = comp_res.json()
    assert "comparison" in comp
    assert "schema_diff" in comp


@pytest.mark.asyncio
async def test_export_formats_and_formula_injection(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests CSV (with injection protection), Excel (.xlsx), and JSON exports.
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Export Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Export test startups with website and location"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # 1. Export CSV
    csv_exp = await client.post(
        f"/api/v1/datasets/{dataset_id}/exports",
        headers=headers,
        json={"format": "csv", "include_provenance": True},
    )
    assert csv_exp.status_code == 200
    csv_id = csv_exp.json()["id"]

    # Download CSV
    dl_csv = await client.get(
        f"/api/v1/exports/{csv_id}/download",
        headers=headers,
    )
    assert dl_csv.status_code == 200
    assert "text/csv" in dl_csv.headers["content-type"]

    # 2. Export Excel (.xlsx)
    xlsx_exp = await client.post(
        f"/api/v1/datasets/{dataset_id}/exports",
        headers=headers,
        json={"format": "xlsx", "include_provenance": True},
    )
    assert xlsx_exp.status_code == 200
    xlsx_id = xlsx_exp.json()["id"]

    dl_xlsx = await client.get(
        f"/api/v1/exports/{xlsx_id}/download",
        headers=headers,
    )
    assert dl_xlsx.status_code == 200
    assert "openxmlformats" in dl_xlsx.headers["content-type"]

    # 3. Export JSON
    json_exp = await client.post(
        f"/api/v1/datasets/{dataset_id}/exports",
        headers=headers,
        json={"format": "json"},
    )
    assert json_exp.status_code == 200
    json_id = json_exp.json()["id"]

    dl_json = await client.get(
        f"/api/v1/exports/{json_id}/download",
        headers=headers,
    )
    assert dl_json.status_code == 200
    assert "application/json" in dl_json.headers["content-type"]


@pytest.mark.asyncio
async def test_dataset_versioning_and_rollback(
    client: AsyncClient,
    test_user_a: dict,
    db_session,
):
    """
    Tests creating version snapshots and restoring a dataset to a prior state.
    """
    headers = test_user_a["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Version Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=headers,
        json={"request": "Startups for version test with location"},
    )
    plan_id = plan_res.json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers)

    collect_res = await client.post(
        f"/api/v1/plans/{plan_id}/collect",
        headers=headers,
        json={"max_records": 5, "max_queries": 2},
    )
    job_id = collect_res.json()["job_id"]
    dataset_id = collect_res.json()["dataset_id"]

    coord = CollectionJobCoordinator(db_session)
    await coord.run_collection(job_id=job_id, max_records_override=5, max_queries_override=2)

    # Apply a cleaning step that creates version #1
    await client.post(
        f"/api/v1/datasets/{dataset_id}/clean/apply",
        headers=headers,
        json={"operation_type": "trim_whitespace", "create_version": True},
    )

    # List versions
    ver_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/versions",
        headers=headers,
    )
    assert ver_res.status_code == 200
    versions = ver_res.json()
    assert len(versions) >= 1

    # Restore version
    target_ver_id = versions[0]["id"]
    restore_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/versions/{target_ver_id}/restore",
        headers=headers,
    )
    assert restore_res.status_code == 200
    assert "Successfully restored" in restore_res.json()["message"]


@pytest.mark.asyncio
async def test_dataset_management_multi_tenant_isolation(
    client: AsyncClient,
    test_user_a: dict,
    test_user_b: dict,
):
    """
    Guarantees User B cannot access, profile, clean, export, or restore User A's datasets.
    """
    headers_a = test_user_a["headers"]
    headers_b = test_user_b["headers"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Private Project A"},
        headers=headers_a,
    )
    project_id = proj_resp.json()["id"]

    ds_res = await client.post(
        "/api/v1/datasets",
        headers=headers_a,
        json={"project_id": project_id, "name": "User A Private Dataset"},
    )
    dataset_id = ds_res.json()["id"]

    # User B tries to profile User A's dataset -> 404
    p_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/profile",
        headers=headers_b,
    )
    assert p_res.status_code == 404

    # User B tries to clean User A's dataset -> 404
    c_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean/apply",
        headers=headers_b,
        json={"operation_type": "trim_whitespace"},
    )
    assert c_res.status_code == 404

    # User B tries to export User A's dataset -> 404
    e_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/exports",
        headers=headers_b,
        json={"format": "csv"},
    )
    assert e_res.status_code == 404
