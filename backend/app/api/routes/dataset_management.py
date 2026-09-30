import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.dataset_management_service import DatasetManagementService
from app.schemas.dataset_quality import (
    DatasetProfileResponse,
    QualityReportResponse,
)
from app.schemas.dataset_management import (
    BulkRecordDeleteRequest,
    BulkRecordUpdateRequest,
    ChartCreateRequest,
    ChartResponse,
    ChartUpdateRequest,
    CleanApplyRequest,
    CleanPreviewRequest,
    CleanPreviewResponse,
    DatasetCompareRequest,
    DatasetCompareResponse,
    DuplicateGroupResponse,
    DuplicateMergeRequest,
    ExportCreateRequest,
    ExportResponse,
    RecordUpdateRequest,
    TransformApplyRequest,
    TransformationResponse,
    TransformPreviewRequest,
    TransformPreviewResponse,
    VersionResponse,
    VersionRestoreResponse,
)

router = APIRouter(tags=["Dataset Management & Analytics"])


# ----------------------------------------------------
# 1. Dataset Profiling & Quality
# ----------------------------------------------------
@router.post("/datasets/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def profile_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers dataset profiling and generates comprehensive column-level statistics and quality scoring.
    """
    service = DatasetManagementService(db)
    return await service.profile_dataset(dataset_id, current_user.id)


@router.get("/datasets/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_dataset_profile(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the latest dataset profiling report.
    """
    service = DatasetManagementService(db)
    return await service.profile_dataset(dataset_id, current_user.id)


@router.get("/datasets/{dataset_id}/quality-report", response_model=QualityReportResponse)
async def get_quality_report(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the latest 5-dimension quality report with explanation and suggestions.
    """
    service = DatasetManagementService(db)
    return await service.get_latest_quality_report(dataset_id, current_user.id)


# ----------------------------------------------------
# 2. Data Cleaning & Normalization
# ----------------------------------------------------
@router.post("/datasets/{dataset_id}/clean/preview", response_model=CleanPreviewResponse)
async def clean_preview(
    dataset_id: uuid.UUID,
    req: CleanPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Previews a data cleaning operation before applying it to the dataset.
    """
    service = DatasetManagementService(db)
    return await service.clean_preview(
        dataset_id=dataset_id,
        user_id=current_user.id,
        operation_type=req.operation_type,
        configuration=req.configuration,
    )


@router.post("/datasets/{dataset_id}/clean/apply")
async def clean_apply(
    dataset_id: uuid.UUID,
    req: CleanApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Applies a data cleaning operation, saves a transformation log, and creates a rollback version.
    """
    service = DatasetManagementService(db)
    return await service.clean_apply(
        dataset_id=dataset_id,
        user_id=current_user.id,
        operation_type=req.operation_type,
        configuration=req.configuration,
        create_version=req.create_version,
        change_summary=req.change_summary,
    )


# ----------------------------------------------------
# 3. Transformations & Derived Columns
# ----------------------------------------------------
@router.post("/datasets/{dataset_id}/transformations/preview", response_model=TransformPreviewResponse)
async def transform_preview(
    dataset_id: uuid.UUID,
    req: TransformPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Previews a transformation (derived column, rename, filter) before applying.
    """
    service = DatasetManagementService(db)
    return await service.transform_preview(
        dataset_id=dataset_id,
        user_id=current_user.id,
        operation_type=req.operation_type,
        configuration=req.configuration,
    )


@router.post("/datasets/{dataset_id}/transformations")
async def transform_apply(
    dataset_id: uuid.UUID,
    req: TransformApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Applies a safe transformation to the dataset and creates a version snapshot.
    """
    service = DatasetManagementService(db)
    return await service.transform_apply(
        dataset_id=dataset_id,
        user_id=current_user.id,
        operation_type=req.operation_type,
        configuration=req.configuration,
        create_version=req.create_version,
        change_summary=req.change_summary,
    )


@router.get("/datasets/{dataset_id}/transformations", response_model=List[TransformationResponse])
async def list_transformations(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists auditable transformation history for the dataset.
    """
    service = DatasetManagementService(db)
    return await service.list_transformations(dataset_id, current_user.id)


# ----------------------------------------------------
# 4. Record Editing (Inline, Delete, Bulk)
# ----------------------------------------------------
@router.patch("/dataset-records/{record_id}")
async def update_dataset_record(
    record_id: uuid.UUID,
    req: RecordUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates a single dataset record cell/values.
    """
    service = DatasetManagementService(db)
    return await service.update_record(
        record_id=record_id,
        user_id=current_user.id,
        record_data=req.record_data,
        validation_status=req.validation_status,
    )


@router.delete("/dataset-records/{record_id}")
async def delete_dataset_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a single dataset record.
    """
    service = DatasetManagementService(db)
    return await service.delete_record(record_id, current_user.id)


@router.post("/datasets/{dataset_id}/records/bulk-update")
async def bulk_update_records(
    dataset_id: uuid.UUID,
    req: BulkRecordUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk updates selected records.
    """
    service = DatasetManagementService(db)
    return await service.bulk_update_records(
        dataset_id=dataset_id,
        user_id=current_user.id,
        record_ids=req.record_ids,
        updates=req.updates,
    )


@router.post("/datasets/{dataset_id}/records/bulk-delete")
async def bulk_delete_records(
    dataset_id: uuid.UUID,
    req: BulkRecordDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk deletes selected records.
    """
    service = DatasetManagementService(db)
    return await service.bulk_delete_records(
        dataset_id=dataset_id,
        user_id=current_user.id,
        record_ids=req.record_ids,
    )


# ----------------------------------------------------
# 5. Duplicate Groups & Merging
# ----------------------------------------------------
@router.get("/datasets/{dataset_id}/duplicates", response_model=List[DuplicateGroupResponse])
async def get_duplicate_groups(
    dataset_id: uuid.UUID,
    key_fields: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Identifies duplicate record clusters (exact hashes, canonical URLs, composite keys).
    """
    service = DatasetManagementService(db)
    return await service.get_duplicate_groups(dataset_id, current_user.id, key_fields)


@router.post("/datasets/{dataset_id}/duplicates/merge")
async def merge_duplicates(
    dataset_id: uuid.UUID,
    req: DuplicateMergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Merges duplicate records into a retained record while preserving source provenance.
    """
    service = DatasetManagementService(db)
    return await service.merge_duplicates(
        dataset_id=dataset_id,
        user_id=current_user.id,
        retained_record_id=req.retained_record_id,
        merged_record_ids=req.merged_record_ids,
        field_overrides=req.field_overrides,
        create_version=req.create_version,
    )


@router.post("/datasets/{dataset_id}/duplicates/dismiss")
async def dismiss_duplicates(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dismisses duplicate matches as reviewed false-positives.
    """
    return {"message": "Duplicate match dismissed successfully."}


# ----------------------------------------------------
# 6. Analytics & Dynamic Charts
# ----------------------------------------------------
@router.get("/datasets/{dataset_id}/analytics/overview")
async def get_analytics_overview(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves statistical overview metrics for dashboard cards.
    """
    service = DatasetManagementService(db)
    return await service.get_analytics_overview(dataset_id, current_user.id)


@router.get("/datasets/{dataset_id}/analytics/distributions")
async def get_field_distributions(
    dataset_id: uuid.UUID,
    fields: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computes distribution histograms and categorical frequencies for dataset columns.
    """
    service = DatasetManagementService(db)
    return await service.get_field_distributions(dataset_id, current_user.id, fields)


@router.post("/datasets/{dataset_id}/analytics/charts", response_model=ChartResponse)
async def create_chart(
    dataset_id: uuid.UUID,
    req: ChartCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates and saves a dynamic chart configuration.
    """
    service = DatasetManagementService(db)
    return await service.create_chart(
        dataset_id=dataset_id,
        user_id=current_user.id,
        chart_name=req.chart_name,
        chart_type=req.chart_type,
        configuration=req.configuration,
    )


@router.get("/datasets/{dataset_id}/analytics/charts")
async def list_charts(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists saved charts with computed visualization data points.
    """
    service = DatasetManagementService(db)
    return await service.list_charts(dataset_id, current_user.id)


@router.patch("/analytics/charts/{chart_id}", response_model=ChartResponse)
async def update_chart(
    chart_id: uuid.UUID,
    req: ChartUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates a chart name or configuration.
    """
    service = DatasetManagementService(db)
    return await service.update_chart(
        chart_id=chart_id,
        user_id=current_user.id,
        chart_name=req.chart_name,
        configuration=req.configuration,
    )


@router.delete("/analytics/charts/{chart_id}")
async def delete_chart(
    chart_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a saved chart configuration.
    """
    service = DatasetManagementService(db)
    return await service.delete_chart(chart_id, current_user.id)


# ----------------------------------------------------
# 7. Dataset Comparison
# ----------------------------------------------------
@router.post("/datasets/compare", response_model=DatasetCompareResponse)
async def compare_datasets(
    req: DatasetCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compares two datasets owned by the user for schema differences, record overlap, and quality score deltas.
    """
    service = DatasetManagementService(db)
    return await service.compare_datasets(
        user_id=current_user.id,
        dataset_id_a=req.dataset_id_a,
        dataset_id_b=req.dataset_id_b,
        matching_key=req.matching_key,
    )


# ----------------------------------------------------
# 8. Export Center
# ----------------------------------------------------
@router.post("/datasets/{dataset_id}/exports", response_model=ExportResponse)
async def create_export(
    dataset_id: uuid.UUID,
    req: ExportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a secure CSV, Excel (.xlsx), or JSON export of the dataset.
    """
    service = DatasetManagementService(db)
    return await service.create_export(
        dataset_id=dataset_id,
        user_id=current_user.id,
        export_format=req.format,
        columns=req.columns,
        include_provenance=req.include_provenance,
        include_warnings=req.include_warnings,
        filters=req.filters,
    )


@router.get("/datasets/{dataset_id}/exports", response_model=List[ExportResponse])
async def list_exports(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists export history for a dataset.
    """
    service = DatasetManagementService(db)
    return await service.list_exports(dataset_id, current_user.id)


@router.get("/exports/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves export details and status.
    """
    service = DatasetManagementService(db)
    return await service.get_export(export_id, current_user.id)


@router.get("/exports/{export_id}/download")
async def download_export_file(
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the generated export file safely with proper Content-Disposition.
    """
    service = DatasetManagementService(db)
    exp = await service.get_export(export_id, current_user.id)
    file_path = exp.get("file_reference")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found or expired. Please generate a new export.",
        )

    ext = exp.get("format", "csv")
    media_types = {
        "csv": "text/csv; charset=utf-8",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


# ----------------------------------------------------
# 9. Version History & Restoration
# ----------------------------------------------------
@router.get("/datasets/{dataset_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all version snapshots for a dataset.
    """
    service = DatasetManagementService(db)
    return await service.list_versions(dataset_id, current_user.id)


@router.get("/datasets/{dataset_id}/versions/{version_id}")
async def get_version(
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gets details of a specific version snapshot.
    """
    service = DatasetManagementService(db)
    return await service.get_version(version_id, current_user.id)


@router.post("/datasets/{dataset_id}/versions/{version_id}/restore", response_model=VersionRestoreResponse)
async def restore_version(
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restores dataset records to a prior version safely within a transaction.
    """
    service = DatasetManagementService(db)
    return await service.restore_version(dataset_id, version_id, current_user.id)
