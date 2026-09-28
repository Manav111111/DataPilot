import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.plan import (
    GeneratePlanRequest,
    UpdatePlanRequest,
    RegeneratePlanRequest,
    CollectionPlanResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.plan_service import PlanService

router = APIRouter(tags=["AI Data Planning"])


@router.post(
    "/projects/{project_id}/plans/generate",
    response_model=CollectionPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a structured data collection plan using AI",
)
async def generate_plan(
    project_id: str,
    req: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.generate_plan(current_user.id, project_id, req)


@router.get(
    "/projects/{project_id}/plans",
    response_model=PaginatedResponse[CollectionPlanResponse],
    summary="List collection plans for a project",
)
async def list_project_plans(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * size
    service = PlanService(db)
    items, total = await service.list_project_plans(
        project_id=project_id,
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=size,
    )
    pages = math.ceil(total / size) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/plans/{plan_id}",
    response_model=CollectionPlanResponse,
    summary="Get collection plan by ID",
)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.get_plan(plan_id, current_user.id)


@router.patch(
    "/plans/{plan_id}",
    response_model=CollectionPlanResponse,
    summary="Update an existing collection plan",
)
async def update_plan(
    plan_id: str,
    req: UpdatePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.update_plan(plan_id, current_user.id, req)


@router.post(
    "/plans/{plan_id}/approve",
    response_model=CollectionPlanResponse,
    summary="Approve a collection plan for future execution",
)
async def approve_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.approve_plan(plan_id, current_user.id)


@router.post(
    "/plans/{plan_id}/reject",
    response_model=CollectionPlanResponse,
    summary="Reject a collection plan",
)
async def reject_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.reject_plan(plan_id, current_user.id)


@router.post(
    "/plans/{plan_id}/regenerate",
    response_model=CollectionPlanResponse,
    summary="Regenerate plan using user feedback or clarification answers",
)
async def regenerate_plan(
    plan_id: str,
    req: RegeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    return await service.regenerate_plan(plan_id, current_user.id, req)
