import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dataset for a project",
)
async def create_dataset(
    data: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    return await service.create_dataset(current_user.id, data)


@router.get(
    "",
    response_model=PaginatedResponse[DatasetResponse],
    summary="List datasets with filtering and pagination",
)
async def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * size
    service = DatasetService(db)
    items, total = await service.list_datasets(
        user_id=current_user.id,
        project_id=project_id,
        skip=skip,
        limit=size,
        search=search,
        status=status,
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
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset by ID",
)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    return await service.get_dataset(dataset_id, current_user.id)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update dataset",
)
async def update_dataset(
    dataset_id: str,
    data: DatasetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    return await service.update_dataset(dataset_id, current_user.id, data)


@router.delete(
    "/{dataset_id}",
    response_model=MessageResponse,
    summary="Delete dataset by ID",
)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)
    await service.delete_dataset(dataset_id, current_user.id)
    return MessageResponse(message="Dataset deleted successfully")
