from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.collection_service import CollectionService
from app.schemas.collection import (
    StartCollectionRequest,
    StartCollectionResponse,
    CollectionJobResponse,
    CollectionJobListResponse,
    CollectionJobEventListResponse,
    DataSourceListResponse,
    RecordSourceResponse,
    DatasetRecordListResponse,
    DatasetOverviewStats,
)

router = APIRouter(tags=["data-collection"])


# 1. Collection Job Lifecycle
@router.post(
    "/plans/{plan_id}/collect",
    response_model=StartCollectionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start data collection for an approved plan",
)
async def start_collection(
    plan_id: str,
    request: StartCollectionRequest = StartCollectionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.start_collection(
        plan_id=plan_id, user_id=current_user.id, request=request
    )


@router.get(
    "/collection-jobs/{job_id}",
    response_model=CollectionJobResponse,
    summary="Get collection job status and progress",
)
async def get_collection_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.get_job(job_id=job_id, user_id=current_user.id)


@router.get(
    "/projects/{project_id}/collection-jobs",
    response_model=CollectionJobListResponse,
    summary="List collection jobs for a project",
)
async def list_project_collection_jobs(
    project_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.list_project_jobs(
        project_id=project_id,
        user_id=current_user.id,
        page=page,
        size=size,
        status_filter=status,
    )


@router.post(
    "/collection-jobs/{job_id}/cancel",
    response_model=CollectionJobResponse,
    summary="Cancel an active collection job",
)
async def cancel_collection_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.cancel_job(job_id=job_id, user_id=current_user.id)


@router.post(
    "/collection-jobs/{job_id}/retry",
    response_model=CollectionJobResponse,
    summary="Retry a failed or cancelled collection job",
)
async def retry_collection_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.retry_job(job_id=job_id, user_id=current_user.id)


@router.get(
    "/collection-jobs/{job_id}/events",
    response_model=CollectionJobEventListResponse,
    summary="Get chronological activity log of a collection job",
)
async def get_collection_job_events(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.get_job_events(job_id=job_id, user_id=current_user.id)


# 2. Dataset Records & Provenance
@router.get(
    "/datasets/{dataset_id}/records",
    response_model=DatasetRecordListResponse,
    summary="Get paginated structured records of a dataset",
)
async def list_dataset_records(
    dataset_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.list_dataset_records(
        dataset_id=dataset_id,
        user_id=current_user.id,
        page=page,
        size=size,
        search=search,
        validation_status=validation_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/dataset-records/{record_id}/sources",
    response_model=List[RecordSourceResponse],
    summary="Get source provenance and field evidence for a record",
)
async def get_record_provenance(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.get_record_provenance(
        record_id=record_id, user_id=current_user.id
    )


@router.get(
    "/datasets/{dataset_id}/sources",
    response_model=DataSourceListResponse,
    summary="Get discovered sources for a dataset",
)
async def list_dataset_sources(
    dataset_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    domain: Optional[str] = Query(None),
    retrieval_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.list_dataset_sources(
        dataset_id=dataset_id,
        user_id=current_user.id,
        page=page,
        size=size,
        domain=domain,
        retrieval_status=retrieval_status,
    )


@router.get(
    "/datasets/{dataset_id}/overview",
    response_model=DatasetOverviewStats,
    summary="Get dataset quality and collection metrics overview",
)
async def get_dataset_overview_stats(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    return await service.get_dataset_overview_stats(
        dataset_id=dataset_id, user_id=current_user.id
    )


@router.get(
    "/datasets/{dataset_id}/export",
    summary="Export dataset records to CSV or JSON",
)
async def export_dataset(
    dataset_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CollectionService(db)
    content, media_type, filename = await service.export_dataset(
        dataset_id=dataset_id, user_id=current_user.id, export_format=format
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
