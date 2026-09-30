import pytest
from httpx import AsyncClient
from app.collection.security.url_validator import validate_and_sanitize_url
from app.collection.search.tavily_client import TavilySearchClient
from app.collection.extraction.firecrawl_client import FirecrawlExtractionClient, ExtractedPage
from app.collection.extraction.structured_extractor import StructuredExtractor
from app.collection.processing.validator import RecordValidator
from app.collection.processing.deduplicator import DeduplicationEngine
from app.schemas.plan import CollectionPlanData, FieldDefinition, SearchQuery, QualityRule, RuleType
from app.collection.coordinator import CollectionJobCoordinator


# 1. URL Safety & SSRF Tests
def test_url_safety_and_ssrf_blocking():
    # Blocked URLs
    assert not validate_and_sanitize_url("http://127.0.0.1:8000")[0]
    assert not validate_and_sanitize_url("http://localhost/admin")[0]
    assert not validate_and_sanitize_url("http://169.254.169.254/latest/meta-data/")[0]
    assert not validate_and_sanitize_url("ftp://example.com/file.txt")[0]
    assert not validate_and_sanitize_url("file:///etc/passwd")[0]
    assert not validate_and_sanitize_url("http://internal-service.local/api")[0]

    # Allowed safe public URLs
    is_valid, safe_url, err = validate_and_sanitize_url("https://www.techcrunch.com/article/ai-startups")
    assert is_valid
    assert safe_url == "https://www.techcrunch.com/article/ai-startups"
    assert err is None


# 2. Tavily Search Adapter Test
@pytest.mark.asyncio
async def test_tavily_search_adapter():
    client = TavilySearchClient()
    results = await client.search(
        query="Indian AI ML startups hiring",
        max_results=5,
        source_category="job_board",
    )
    assert len(results) > 0
    assert results[0].url.startswith("http")
    assert results[0].domain != ""
    assert results[0].search_query == "Indian AI ML startups hiring"
    assert results[0].source_category == "job_board"


# 3. Firecrawl Extraction Adapter Test
@pytest.mark.asyncio
async def test_firecrawl_extraction_adapter():
    client = FirecrawlExtractionClient()
    page = await client.extract_url(
        url="https://www.sarvam.ai/careers/senior-ml-engineer",
        fallback_title="Sarvam AI Careers",
    )
    assert page.status == "retrieved"
    assert "Sarvam AI" in page.content
    assert page.content_hash is not None
    assert len(page.content_hash) == 64


# 4. Structured Extractor & Validator Test
@pytest.mark.asyncio
async def test_structured_extractor_and_validation():
    plan_data = CollectionPlanData(
        goal="Collect AI startups hiring engineers",
        entity_type="Startup Job Listing",
        geography="India",
        target_record_count=50,
        fields=[
            FieldDefinition(name="company_name", type="string", required=True, description="Name of company"),
            FieldDefinition(name="job_title", type="string", required=True, description="Title of role"),
            FieldDefinition(name="salary", type="string", required=False, description="Salary range"),
            FieldDefinition(name="website", type="url", required=False, description="Company website URL"),
        ],
        search_queries=[SearchQuery(query="Indian AI startups hiring", priority="high", category="broad")],
    )

    page = ExtractedPage(
        url="https://www.sarvam.ai/careers",
        title="Sarvam AI Careers",
        content="""# Sarvam AI Careers
        Sarvam AI is developing foundational AI models in Bangalore, India.
        Role: Senior AI/ML Engineer.
        Compensation: ₹45,00,000 per annum.
        Website: https://www.sarvam.ai
        """,
    )

    extractor = StructuredExtractor()
    extracted_records = await extractor.extract_records_from_page(page, plan_data)
    assert len(extracted_records) > 0

    validator = RecordValidator(plan_data)
    validated = validator.validate_and_normalize(extracted_records[0])
    assert validated.validation_status in ("valid", "valid_with_warnings")
    assert validated.normalized_data["company_name"] is not None
    assert len(validated.field_evidences) > 0


# 5. Deduplication Engine Test
def test_deduplication_engine():
    plan_data = CollectionPlanData(
        goal="Test Dedup",
        entity_type="Company",
        geography="India",
        fields=[
            FieldDefinition(name="company_name", type="string", required=True, description="Company"),
            FieldDefinition(name="job_title", type="string", required=True, description="Job"),
            FieldDefinition(name="website", type="url", required=False, description="URL"),
        ],
        quality_rules=[
            QualityRule(
                name="Duplicate Check",
                rule_type=RuleType.DUPLICATE_CHECK,
                target_fields=["company_name", "job_title"],
                description="Exact duplicate check on company and job title",
            )
        ],
    )

    validator = RecordValidator(plan_data)
    raw1 = ExtractedPage(
        url="https://site1.com/job1",
        title="Page 1",
        content="Company: Sarvam AI. Role: ML Engineer.",
    )
    raw2 = ExtractedPage(
        url="https://site2.com/job2",
        title="Page 2",
        content="Company: Sarvam AI. Role: ML Engineer. Website: https://sarvam.ai",
    )

    rec1 = validator.validate_and_normalize(
        StructuredExtractor()._fallback_extraction(raw1, plan_data)[0]
    )
    rec2 = validator.validate_and_normalize(
        StructuredExtractor()._fallback_extraction(raw2, plan_data)[0]
    )

    deduplicator = DeduplicationEngine(plan_data)
    unique_recs, dup_count, merged_sources = deduplicator.process_records([rec1, rec2])

    assert len(unique_recs) == 1
    assert dup_count == 1


# 6. Start Collection Requires Approved Plan
@pytest.mark.asyncio
async def test_start_collection_requires_approved_plan(
    client: AsyncClient, test_user_a
):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "SaaS Intel Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    # 2. Create draft plan
    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=test_user_a["headers"],
        json={"request": "Find 50 B2B SaaS startups in Mumbai with company name and funding"},
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    assert plan["status"] == "ready_for_review"

    # 3. Attempt to start collection before approval -> Expect 400 Bad Request
    collect_res = await client.post(
        f"/api/v1/plans/{plan['id']}/collect",
        headers=test_user_a["headers"],
        json={"dataset_name": "Unapproved Collection"},
    )
    assert collect_res.status_code == 400
    assert "Only approved plans" in collect_res.json()["detail"]

    # 4. Now approve the plan
    approve_res = await client.post(
        f"/api/v1/plans/{plan['id']}/approve",
        headers=test_user_a["headers"],
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # 5. Now start collection -> Expect 202 Accepted
    collect_res = await client.post(
        f"/api/v1/plans/{plan['id']}/collect",
        headers=test_user_a["headers"],
        json={"dataset_name": "Approved SaaS Collection", "max_records": 10},
    )
    assert collect_res.status_code == 202
    data = collect_res.json()
    assert "job_id" in data
    assert "dataset_id" in data
    assert data["status"] == "queued"


# 7. Full Collection Pipeline Execution & Record Provenance
@pytest.mark.asyncio
async def test_full_collection_job_pipeline_and_provenance(
    client: AsyncClient, test_user_a, db_session
):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "AI Hiring Intel Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    # 2. Generate & approve plan
    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=test_user_a["headers"],
        json={"request": "Find 20 AI/ML startups hiring in Bangalore with company name, job title, and website"},
    )
    plan = plan_res.json()
    await client.post(f"/api/v1/plans/{plan['id']}/approve", headers=test_user_a["headers"])

    # 3. Start collection job
    start_res = await client.post(
        f"/api/v1/plans/{plan['id']}/collect",
        headers=test_user_a["headers"],
        json={"max_records": 5, "max_queries": 2},
    )
    job_info = start_res.json()
    job_id = job_info["job_id"]
    dataset_id = job_info["dataset_id"]

    # 4. Execute collection coordinator directly
    coordinator = CollectionJobCoordinator(db_session)
    completed_job = await coordinator.run_collection(
        job_id=job_id, max_records_override=5, max_queries_override=2
    )
    assert completed_job.status in ("completed", "completed_with_errors")
    assert completed_job.progress_percentage == 100
    assert completed_job.records_saved > 0

    # 5. Query Job status via API
    job_status_res = await client.get(
        f"/api/v1/collection-jobs/{job_id}",
        headers=test_user_a["headers"],
    )
    assert job_status_res.status_code == 200
    job_data = job_status_res.json()
    assert job_data["status"] in ("completed", "completed_with_errors")
    assert job_data["records_saved"] > 0
    assert job_data["completed_queries"] > 0

    # 6. Query Dataset records via API
    records_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/records",
        headers=test_user_a["headers"],
    )
    assert records_res.status_code == 200
    records_data = records_res.json()
    assert len(records_data["items"]) > 0
    first_record = records_data["items"][0]
    assert "company_name" in first_record["record_data"] or "company_name" in first_record["normalized_data"]

    # 7. Query Record Provenance
    prov_res = await client.get(
        f"/api/v1/dataset-records/{first_record['id']}/sources",
        headers=test_user_a["headers"],
    )
    assert prov_res.status_code == 200
    provenance_list = prov_res.json()
    assert len(provenance_list) > 0
    assert provenance_list[0]["source_url"].startswith("http")
    assert provenance_list[0]["evidence_excerpt"] is not None

    # 8. Query Dataset Sources
    sources_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/sources",
        headers=test_user_a["headers"],
    )
    assert sources_res.status_code == 200
    assert len(sources_res.json()["items"]) > 0

    # 9. Query Dataset Overview Stats
    overview_res = await client.get(
        f"/api/v1/datasets/{dataset_id}/overview",
        headers=test_user_a["headers"],
    )
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["total_records"] > 0
    assert overview["source_count"] > 0

    # 10. Query Export (JSON and CSV)
    json_export = await client.get(
        f"/api/v1/datasets/{dataset_id}/export?format=json",
        headers=test_user_a["headers"],
    )
    assert json_export.status_code == 200
    assert "attachment" in json_export.headers.get("content-disposition", "")

    csv_export = await client.get(
        f"/api/v1/datasets/{dataset_id}/export?format=csv",
        headers=test_user_a["headers"],
    )
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers.get("content-type", "")


# 8. Cancel and Retry Job Tests
@pytest.mark.asyncio
async def test_cancel_and_retry_collection_job(
    client: AsyncClient, test_user_a
):
    # Setup project & approved plan
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Delhi AI Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=test_user_a["headers"],
        json={"request": "Find 20 AI startups in Delhi with company name and location"},
    )
    plan = plan_res.json()
    await client.post(f"/api/v1/plans/{plan['id']}/approve", headers=test_user_a["headers"])

    start_res = await client.post(
        f"/api/v1/plans/{plan['id']}/collect",
        headers=test_user_a["headers"],
    )
    job_id = start_res.json()["job_id"]

    # Cancel job
    cancel_res = await client.post(
        f"/api/v1/collection-jobs/{job_id}/cancel",
        headers=test_user_a["headers"],
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Retry cancelled job
    retry_res = await client.post(
        f"/api/v1/collection-jobs/{job_id}/retry",
        headers=test_user_a["headers"],
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "queued"
    assert retry_res.json()["retry_count"] == 1


# 9. Multi-Tenant Isolation for Collection Jobs & Records
@pytest.mark.asyncio
async def test_collection_multi_tenant_isolation(
    client: AsyncClient, test_user_a, test_user_b
):
    # User A creates project, plan, and starts job
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "User A Fintech Project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    plan_res = await client.post(
        f"/api/v1/projects/{project_id}/plans/generate",
        headers=test_user_a["headers"],
        json={"request": "Find 10 Fintech startups in Bangalore with company name and website"},
    )
    plan = plan_res.json()
    await client.post(f"/api/v1/plans/{plan['id']}/approve", headers=test_user_a["headers"])

    start_res = await client.post(
        f"/api/v1/plans/{plan['id']}/collect",
        headers=test_user_a["headers"],
    )
    job_id = start_res.json()["job_id"]
    dataset_id = start_res.json()["dataset_id"]

    # User B attempts to access User A's job -> 404
    job_b_res = await client.get(f"/api/v1/collection-jobs/{job_id}", headers=test_user_b["headers"])
    assert job_b_res.status_code == 404

    # User B attempts to cancel User A's job -> 404
    cancel_b_res = await client.post(f"/api/v1/collection-jobs/{job_id}/cancel", headers=test_user_b["headers"])
    assert cancel_b_res.status_code == 404

    # User B attempts to list User A's project jobs -> empty/404
    proj_jobs_b = await client.get(
        f"/api/v1/projects/{project_id}/collection-jobs", headers=test_user_b["headers"]
    )
    assert proj_jobs_b.status_code == 200
    assert len(proj_jobs_b.json()["items"]) == 0

    # User B attempts to access User A's dataset records -> empty list
    rec_b = await client.get(f"/api/v1/datasets/{dataset_id}/records", headers=test_user_b["headers"])
    assert rec_b.status_code == 200
    assert len(rec_b.json()["items"]) == 0
