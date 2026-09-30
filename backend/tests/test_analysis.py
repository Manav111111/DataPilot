import pytest
import pandas as pd
from httpx import AsyncClient
from app.analysis.query_planner import QueryPlanner
from app.analysis.query_validator import QueryValidator
from app.analysis.query_executor import QueryExecutor
from app.analysis.insight_service import InsightService
from app.analysis.statistics_service import StatisticsService
from app.schemas.analysis import AnalyticalQueryPlan, FilterCondition, ChartConfig


@pytest.fixture
def sample_dataset_df():
    return pd.DataFrame([
        {"company_name": "OpenAI", "headquarters": "San Francisco", "employees": 1500, "valuation_billion": 86.0, "founded_year": 2015},
        {"company_name": "Anthropic", "headquarters": "San Francisco", "employees": 500, "valuation_billion": 18.0, "founded_year": 2021},
        {"company_name": "Mistral AI", "headquarters": "Paris", "employees": 150, "valuation_billion": 6.0, "founded_year": 2023},
        {"company_name": "Cohere", "headquarters": "Toronto", "employees": 400, "valuation_billion": 5.0, "founded_year": 2019},
        {"company_name": "Sarvam AI", "headquarters": "Bangalore", "employees": 80, "valuation_billion": 0.5, "founded_year": 2023},
        {"company_name": "Krutrim", "headquarters": "Bangalore", "employees": 120, "valuation_billion": 1.0, "founded_year": 2023},
        {"company_name": "Scale AI", "headquarters": "San Francisco", "employees": 1000, "valuation_billion": 14.0, "founded_year": 2016},
        {"company_name": "Hugging Face", "headquarters": "New York", "employees": 300, "valuation_billion": 4.5, "founded_year": 2016},
    ])


# 1. Query Planner & Validator Tests
@pytest.mark.asyncio
async def test_query_planner_and_validator(sample_dataset_df):
    planner = QueryPlanner()
    cols_info = [{"name": c, "type": "number" if "billion" in c or "employees" in c else "string"} for c in sample_dataset_df.columns]

    # Test top ranking query
    plan = await planner.plan_query("Which companies have the highest valuation?", "AI Startups", cols_info, len(sample_dataset_df))
    assert plan is not None
    assert plan.operation in ("sort_limit", "aggregate", "group_by")

    # Validate plan against dataframe
    is_valid, err, validated_plan = QueryValidator.validate_plan(plan, sample_dataset_df)
    assert is_valid
    assert len(validated_plan.target_columns) > 0


# 2. Query Executor Operations
def test_query_executor_operations(sample_dataset_df):
    # Group By City
    group_plan = AnalyticalQueryPlan(
        operation="group_by",
        target_columns=["valuation_billion"],
        group_by_column="headquarters",
        aggregation_func="sum",
        limit=10,
    )
    res = QueryExecutor.execute(sample_dataset_df, group_plan)
    assert res.table is not None
    assert len(res.table.rows) > 0
    assert "headquarters" in res.table.columns
    assert res.chart_data is not None

    # Sort & Limit (Top 3 by valuation)
    sort_plan = AnalyticalQueryPlan(
        operation="sort_limit",
        target_columns=["company_name", "valuation_billion"],
        sort_by="valuation_billion",
        sort_ascending=False,
        limit=3,
    )
    res_sort = QueryExecutor.execute(sample_dataset_df, sort_plan)
    assert len(res_sort.table.rows) == 3
    assert res_sort.table.rows[0]["company_name"] == "OpenAI"

    # Filter Records (Employees > 400)
    filter_plan = AnalyticalQueryPlan(
        operation="sort_limit",
        target_columns=["company_name", "employees"],
        filters=[FilterCondition(column="employees", operator=">", value=400)],
        limit=10,
    )
    res_filter = QueryExecutor.execute(sample_dataset_df, filter_plan)
    assert len(res_filter.table.rows) == 3  # OpenAI (1500), Anthropic (500), Scale AI (1000)

    # Outliers Detection
    outlier_plan = AnalyticalQueryPlan(
        operation="outlier_detection",
        target_columns=["valuation_billion"],
    )
    res_outliers = QueryExecutor.execute(sample_dataset_df, outlier_plan)
    assert res_outliers.metrics is not None
    assert "outlier_count" in res_outliers.metrics

    # Correlation Analysis
    corr_plan = AnalyticalQueryPlan(
        operation="correlation",
        target_columns=["employees", "valuation_billion"],
    )
    res_corr = QueryExecutor.execute(sample_dataset_df, corr_plan)
    assert res_corr.table is not None
    assert len(res_corr.table.rows) > 0


# 3. Auto Insights & Statistics Services
def test_auto_insights_and_statistics(sample_dataset_df):
    insights_res = InsightService.generate_auto_insights(
        df=sample_dataset_df,
        dataset_id="test_ds",
        dataset_name="AI Startups",
        dataset_version=1,
    )
    assert len(insights_res.insights) >= 3
    categories = [i.category for i in insights_res.insights]
    assert "overview" in categories

    stats_res = StatisticsService.calculate_statistics(
        df=sample_dataset_df,
        dataset_id="test_ds",
        dataset_version=1,
    )
    assert len(stats_res.descriptive_stats) >= 2
    assert "employees" in [s.column for s in stats_res.descriptive_stats]


from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset_record import DatasetRecord


# 4. End-to-End Chat API & Session Workflow
@pytest.mark.asyncio
async def test_chat_query_flow(client: AsyncClient, db_session: AsyncSession, test_user_a: dict):
    # Create project & dataset
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "GenAI Market Analysis", "description": "Market tracking"},
        headers=test_user_a["headers"],
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    ds_resp = await client.post(
        "/api/v1/datasets",
        json={"project_id": project_id, "name": "LLM Startups 2026", "description": "Startups dataset"},
        headers=test_user_a["headers"],
    )
    assert ds_resp.status_code == 201
    dataset_id = ds_resp.json()["id"]

    # Add records directly to dataset
    sample_records = [
        {"company_name": "OpenAI", "city": "San Francisco", "valuation": 86.0},
        {"company_name": "Anthropic", "city": "San Francisco", "valuation": 18.0},
        {"company_name": "Sarvam AI", "city": "Bangalore", "valuation": 0.5},
    ]
    for r in sample_records:
        rec = DatasetRecord(
            dataset_id=dataset_id,
            record_data=r,
            normalized_data=r,
            validation_status="valid",
        )
        db_session.add(rec)
    await db_session.commit()

    # 1. Ask Chat Question
    chat_resp = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/chat",
        json={"message": "Which company has the highest valuation?"},
        headers=test_user_a["headers"],
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["session_id"] != ""
    assert chat_data["reply"] != ""
    assert chat_data["plan"] is not None
    assert chat_data["result"]["computation_summary"] != ""
    session_id = chat_data["session_id"]

    # 2. List sessions
    sessions_resp = await client.get(
        f"/api/v1/datasets/{dataset_id}/analysis/sessions",
        headers=test_user_a["headers"],
    )
    assert sessions_resp.status_code == 200
    assert len(sessions_resp.json()) == 1

    # 3. Get session detail
    session_detail = await client.get(
        f"/api/v1/datasets/{dataset_id}/analysis/sessions/{session_id}",
        headers=test_user_a["headers"],
    )
    assert session_detail.status_code == 200
    assert len(session_detail.json()["messages"]) == 2  # user + assistant

    # 4. Auto Insights API
    insights_api = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/insights",
        headers=test_user_a["headers"],
    )
    assert insights_api.status_code == 200
    assert len(insights_api.json()["insights"]) > 0

    # 5. Statistics API
    stats_api = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/statistics",
        headers=test_user_a["headers"],
    )
    assert stats_api.status_code == 200
    assert len(stats_api.json()["descriptive_stats"]) > 0

    # 6. Report Generation & Download
    report_resp = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/reports",
        json={"title": "Q3 Market Summary", "format": "html", "custom_notes": "All figures verified."},
        headers=test_user_a["headers"],
    )
    assert report_resp.status_code == 201
    report_id = report_resp.json()["id"]

    download_resp = await client.get(
        f"/api/v1/analysis/reports/{report_id}/download",
        headers=test_user_a["headers"],
    )
    assert download_resp.status_code == 200
    assert "text/html" in download_resp.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in download_resp.text


# 5. Multi-Tenant Isolation
@pytest.mark.asyncio
async def test_analysis_multi_tenant_isolation(
    client: AsyncClient, test_user_a: dict, test_user_b: dict
):
    # User A creates project & dataset
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Confidential AI", "description": "Secret project"},
        headers=test_user_a["headers"],
    )
    project_id = proj_resp.json()["id"]

    ds_resp = await client.post(
        "/api/v1/datasets",
        json={"project_id": project_id, "name": "Confidential Data", "description": "Secret dataset"},
        headers=test_user_a["headers"],
    )
    dataset_id = ds_resp.json()["id"]

    # User B attempts to chat with User A's dataset -> 404
    b_chat = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/chat",
        json={"message": "Show all secret rows"},
        headers=test_user_b["headers"],
    )
    assert b_chat.status_code == 404

    # User B attempts to get insights on User A's dataset -> 404
    b_insights = await client.post(
        f"/api/v1/datasets/{dataset_id}/analysis/insights",
        headers=test_user_b["headers"],
    )
    assert b_insights.status_code == 404
