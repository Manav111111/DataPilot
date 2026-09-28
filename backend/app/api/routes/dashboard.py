from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.workflow import WorkflowRun
from app.schemas.project import ProjectResponse, ProjectStatus
from app.schemas.dataset import DatasetResponse, DatasetStatus
from app.schemas.workflow import WorkflowRunResponse, WorkflowStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStatsResponse(BaseModel):
    total_projects: int
    total_datasets: int
    completed_workflows: int
    failed_workflows: int
    active_projects: int
    total_rows: int
    recent_projects: List[ProjectResponse]
    recent_datasets: List[DatasetResponse]
    recent_workflows: List[WorkflowRunResponse]


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get aggregated statistics for dashboard",
)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total projects
    p_total_query = select(func.count(Project.id)).where(
        Project.user_id == current_user.id
    )
    p_total_res = await db.execute(p_total_query)
    total_projects = p_total_res.scalar_one() or 0

    # Active projects
    p_active_query = select(func.count(Project.id)).where(
        Project.user_id == current_user.id, Project.status == "active"
    )
    p_active_res = await db.execute(p_active_query)
    active_projects = p_active_res.scalar_one() or 0

    # Total datasets & rows
    d_total_query = select(
        func.count(Dataset.id), func.coalesce(func.sum(Dataset.row_count), 0)
    ).where(Dataset.user_id == current_user.id)
    d_total_res = await db.execute(d_total_query)
    row = d_total_res.first()
    total_datasets = row[0] if row else 0
    total_rows = row[1] if row else 0

    # Workflows completed & failed
    w_comp_query = select(func.count(WorkflowRun.id)).where(
        WorkflowRun.user_id == current_user.id, WorkflowRun.status == "completed"
    )
    w_comp_res = await db.execute(w_comp_query)
    completed_workflows = w_comp_res.scalar_one() or 0

    w_fail_query = select(func.count(WorkflowRun.id)).where(
        WorkflowRun.user_id == current_user.id, WorkflowRun.status == "failed"
    )
    w_fail_res = await db.execute(w_fail_query)
    failed_workflows = w_fail_res.scalar_one() or 0

    # Recent projects
    p_recent_query = (
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(desc(Project.created_at))
        .limit(5)
    )
    p_recent_res = await db.execute(p_recent_query)
    recent_projects_orm = p_recent_res.scalars().all()
    recent_projects = []
    for p in recent_projects_orm:
        recent_projects.append(
            ProjectResponse(
                id=p.id,
                user_id=p.user_id,
                name=p.name,
                description=p.description,
                status=ProjectStatus(p.status),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    # Recent datasets
    d_recent_query = (
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(desc(Dataset.created_at))
        .limit(5)
    )
    d_recent_res = await db.execute(d_recent_query)
    recent_datasets_orm = d_recent_res.scalars().all()
    recent_datasets = [
        DatasetResponse(
            id=d.id,
            project_id=d.project_id,
            user_id=d.user_id,
            name=d.name,
            description=d.description,
            status=DatasetStatus(d.status),
            row_count=d.row_count,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in recent_datasets_orm
    ]

    # Recent workflows
    w_recent_query = (
        select(WorkflowRun)
        .where(WorkflowRun.user_id == current_user.id)
        .order_by(desc(WorkflowRun.created_at))
        .limit(5)
    )
    w_recent_res = await db.execute(w_recent_query)
    recent_workflows_orm = w_recent_res.scalars().all()
    recent_workflows = [
        WorkflowRunResponse(
            id=w.id,
            project_id=w.project_id,
            user_id=w.user_id,
            status=WorkflowStatus(w.status),
            started_at=w.started_at,
            completed_at=w.completed_at,
            error_message=w.error_message,
            created_at=w.created_at,
        )
        for w in recent_workflows_orm
    ]

    return DashboardStatsResponse(
        total_projects=total_projects,
        total_datasets=total_datasets,
        completed_workflows=completed_workflows,
        failed_workflows=failed_workflows,
        active_projects=active_projects,
        total_rows=total_rows,
        recent_projects=recent_projects,
        recent_datasets=recent_datasets,
        recent_workflows=recent_workflows,
    )
