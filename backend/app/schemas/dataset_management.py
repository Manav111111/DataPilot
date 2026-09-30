import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------
# Cleaning Schemas
# ----------------------------------------------------
class CleanPreviewRequest(BaseModel):
    operation_type: str
    configuration: Dict[str, Any] = Field(default_factory=dict)


class CleanPreviewResponse(BaseModel):
    operation_type: str
    configuration: Dict[str, Any]
    records_affected: int
    fields_affected: List[str]
    samples: List[Dict[str, Any]]
    potential_info_loss: bool
    warnings: List[str]


class CleanApplyRequest(BaseModel):
    operation_type: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    create_version: bool = True
    change_summary: Optional[str] = None


# ----------------------------------------------------
# Transformation Schemas
# ----------------------------------------------------
class TransformPreviewRequest(BaseModel):
    operation_type: str
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TransformPreviewResponse(BaseModel):
    operation_type: str
    configuration: Dict[str, Any]
    records_affected: int
    fields_affected: List[str]
    samples: List[Dict[str, Any]]
    warnings: List[str]


class TransformApplyRequest(BaseModel):
    operation_type: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    create_version: bool = True
    change_summary: Optional[str] = None


class TransformationResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    operation_type: str
    configuration: Dict[str, Any]
    status: str
    records_affected: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Record Editing Schemas
# ----------------------------------------------------
class RecordUpdateRequest(BaseModel):
    record_data: Dict[str, Any]
    validation_status: Optional[str] = None


class BulkRecordUpdateRequest(BaseModel):
    record_ids: List[uuid.UUID]
    updates: Dict[str, Any]


class BulkRecordDeleteRequest(BaseModel):
    record_ids: List[uuid.UUID]


# ----------------------------------------------------
# Duplicate Management Schemas
# ----------------------------------------------------
class DuplicateGroupResponse(BaseModel):
    group_id: str
    rule_type: str
    match_field: str
    match_value: str
    confidence: float
    record_count: int
    records: List[Dict[str, Any]]


class DuplicateMergeRequest(BaseModel):
    retained_record_id: uuid.UUID
    merged_record_ids: List[uuid.UUID]
    field_overrides: Optional[Dict[str, Any]] = None
    create_version: bool = True


class DuplicateDismissRequest(BaseModel):
    group_id: str
    record_ids: List[uuid.UUID] = Field(default_factory=list)


# ----------------------------------------------------
# Analytics & Chart Schemas
# ----------------------------------------------------
class ChartCreateRequest(BaseModel):
    chart_name: str
    chart_type: str
    configuration: Dict[str, Any] = Field(default_factory=dict)


class ChartUpdateRequest(BaseModel):
    chart_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class ChartResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    chart_name: str
    chart_type: str
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Dataset Comparison Schemas
# ----------------------------------------------------
class DatasetCompareRequest(BaseModel):
    dataset_id_a: uuid.UUID
    dataset_id_b: uuid.UUID
    matching_key: Optional[str] = None


class DatasetCompareResponse(BaseModel):
    dataset_a: Dict[str, Any]
    dataset_b: Dict[str, Any]
    comparison: Dict[str, Any]
    schema_diff: Dict[str, Any]
    field_comparisons: Dict[str, Any]


# ----------------------------------------------------
# Export Schemas
# ----------------------------------------------------
class ExportCreateRequest(BaseModel):
    format: str = "csv"  # csv, xlsx, json
    columns: Optional[List[str]] = None
    include_provenance: bool = True
    include_warnings: bool = False
    filters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    format: str
    export_configuration: Dict[str, Any]
    status: str
    file_reference: Optional[str] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Versioning Schemas
# ----------------------------------------------------
class VersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    change_type: str
    change_summary: str
    record_count: int
    schema_snapshot: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VersionRestoreResponse(BaseModel):
    message: str
    restored_version_number: int
    record_count: int
    new_version_id: uuid.UUID
