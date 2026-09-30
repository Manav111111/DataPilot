from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StartCollectionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_name: Optional[str] = Field(None, max_length=255, description="Optional custom name for created dataset")
    max_records: Optional[int] = Field(None, ge=1, le=5000, description="Override max records for this job")
    max_queries: Optional[int] = Field(None, ge=1, le=50, description="Override max queries for this job")


class StartCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    dataset_id: str
    status: str
    message: str


class CollectionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    plan_id: str
    dataset_id: str
    status: str
    current_stage: str
    progress_percentage: int
    total_queries: int
    completed_queries: int
    total_sources: int
    processed_sources: int
    records_extracted: int
    records_saved: int
    records_rejected: int
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CollectionJobListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[CollectionJobResponse]
    total: int
    page: int
    size: int
    pages: int


class CollectionJobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_job_id: str
    event_type: str
    message: str
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class CollectionJobEventListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[CollectionJobEventResponse]
    total: int


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    collection_job_id: str
    source_url: str
    canonical_url: Optional[str] = None
    domain: Optional[str] = None
    page_title: Optional[str] = None
    source_type: str
    retrieval_status: str
    retrieved_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    error_message: Optional[str] = None
    search_query: Optional[str] = None
    created_at: datetime


class DataSourceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[DataSourceResponse]
    total: int
    page: int
    size: int
    pages: int


class RecordSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_record_id: str
    data_source_id: str
    evidence_excerpt: Optional[str] = None
    evidence_field: Optional[str] = None
    source_url: Optional[str] = None
    domain: Optional[str] = None
    page_title: Optional[str] = None
    created_at: datetime


class DatasetRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_id: str
    record_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    record_hash: Optional[str] = None
    validation_status: str
    validation_errors: Optional[List[Dict[str, Any]]] = None
    source_count: int
    created_at: datetime
    updated_at: datetime
    sources: Optional[List[RecordSourceResponse]] = None


class DatasetRecordListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[DatasetRecordResponse]
    total: int
    page: int
    size: int
    pages: int


class DatasetOverviewStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_records: int
    valid_records: int
    records_with_warnings: int
    rejected_records: int
    duplicate_count: int
    source_count: int
    latest_job_status: Optional[str] = None
